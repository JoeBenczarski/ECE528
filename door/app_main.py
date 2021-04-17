import logging
import cv2
import queue
import threading
import time
import concurrent.futures
import sys
import os
import json
from awscrt import mqtt

import face_detector
import iot_comm_aws
import lock
import lock_physical


# Globals
aws_pipeline = queue.Queue()
iot_pipeline = queue.Queue()
stop_cap_event = threading.Event()

phys_lock = lock_physical.LockPhysical()
vir_lock = lock.Lock(phys_lock)


# Mqtt Dispatcher
def mqtt_dispatch(topic: str, payload: dict):
    topic_levels = topic.split("/")
    if topic_levels[0] == "cmd":
        # Handle incoming command
        if topic_levels[1] == "lock":
            if topic_levels[2] == "state":
                if payload["state"] == "lock":
                    logging.info(vir_lock.lock())
                    mqtt_send_state("lock")
                elif payload["state"] == "unlock":
                    logging.info(vir_lock.unlock())
                    mqtt_send_state("unlock")
                else:
                    raise NotImplementedError
    elif topic_levels[0] == "dt":
        # Handle incoming data
        pass
    else:
        raise NotImplementedError


def mqtt_send_state(state: str):
    topic = "dt/lock/state"
    payload = json.dumps({"state": state})
    aws_iot.publish(topic=topic, payload=payload, qos=mqtt.QoS.AT_LEAST_ONCE)


# IoT callbacks
def on_connection_interrupted(connection, error, **kwargs):
    logging.info(f"Connection interrupted: {connection} {error}")


def on_connection_resumed(connection, return_code, session_present, **kwargs):
    logging.info(f"Connection resumed. return_code: {return_code} session_present: {session_present}")
    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        logging.info("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()
        # Cannot synchronously wait for resubscribe result because we're on the connection's event-loop thread,
        # evaluate result with a callback instead.
        resubscribe_future.add_done_callback(on_resubscribe_complete)


def on_resubscribe_complete(resubscribe_future):
    resubscribe_results = resubscribe_future.result()
    logging.info(f"Resubscribe results: {resubscribe_results}")
    for topic, qos in resubscribe_results['topics']:
        if qos is None:
            sys.exit("Server rejected resubscribe to topic: {}".format(topic))


def on_message_received(topic, payload, dup, qos, retain, **kwargs):
    iot_pipeline.put({"topic": topic, "payload": payload})
    logging.debug(f"Received: {topic} : {payload}")


# Thread for video handling
def video_thread(pipeline: queue.Queue):
    past = time.time()
    video = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not video.isOpened():
        stop_cap_event.set()
    while True:
        if stop_cap_event.is_set():
            logging.info(f"vid thread detected stop capture")
            break
        _, frame = video.read()
        cv2.imshow('Video Feed', frame)
        elapsed = time.time() - past
        if elapsed > 2:
            past = time.time()
            try:
                pipeline.put(frame, timeout=2)
            except queue.Full:
                logging.debug(f"video queue full")
        # must call wait key for cv2.imshow to work
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_cap_event.set()
    video.release()
    cv2.destroyAllWindows()


# Thread for AWS Rekognition
def rekognition_thread(pipeline: queue.Queue):
    detector = face_detector.FaceDetector()
    while True:
        if stop_cap_event.is_set():
            logging.info(f"rekog thread detected stop capture")
            break
        try:
            frame = pipeline.get(block=True, timeout=2)
            _, frame_png = cv2.imencode('.png', frame)
            frame_bytes = frame_png.tobytes()
            if vir_lock.get_state() is lock.Locked:
                prob = detector.detect_face_from_bytes(frame_bytes)
                if prob > 0.75:
                    logging.info(f'Probability: {prob}  Face detected')
                    # check if this is an authorized person
                    try:
                        with open('images/Joe-Benczarski.jpg', 'rb') as tgt:
                            compare_bytes = tgt.read()
                    except OSError:
                        logging.error(f"cannot open image")
                    auth = detector.compare_face_from_bytes(frame_bytes, compare_bytes, 99.5)
                    if auth:
                        logging.info(f"Detected authorized person")
                        # Unlock the door
                        logging.info(vir_lock.unlock())
                        mqtt_send_state("unlock")
                else:
                    logging.info(f'Probability: {prob}  No face detected')
        except queue.Empty:
            logging.debug(f"rekognition queue empty")


# Thread for AWS IoT
def iot_thread(pipeline: queue.Queue):
    while True:
        if stop_cap_event.is_set():
            logging.info(f"iot thread detected stop capture")
            break
        try:
            info = pipeline.get(block=True, timeout=2)
            topic = info["topic"]
            payload = json.loads(info["payload"].decode("utf-8"))
            logging.debug(f"Dispatching: {topic} : {payload}")
            try:
                mqtt_dispatch(topic, payload)
                logging.debug(f"Dispatched: {topic} : {payload}")
            except NotImplementedError:
                logging.warning(f"NotImplementedError: {topic} : {payload}")
        except queue.Empty:
            logging.debug(f"iot queue timeout")


# Setup AWS IoT Core
cert_path = os.path.abspath('./certs/5b35693745-certificate.pem.crt')
key_path = os.path.abspath('./certs/5b35693745-private.pem.key')
root_ca_path = os.path.abspath('./certs/AmazonRootCA1.pem')
endpoint = "aeuwkvsf1rv59-ats.iot.us-east-1.amazonaws.com"
client = "door-lock"
aws_iot = iot_comm_aws.IotCommAws(client_id=client, endpoint=endpoint,
                                  cert=cert_path, key=key_path, root_ca=root_ca_path,
                                  conn_int=on_connection_interrupted, conn_res=on_connection_resumed)


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')

    subscribe_topic = "cmd/lock/state"
    connect_future = aws_iot.connect()
    connect_future.result()
    subscribe_future, packet_id = aws_iot.subscribe(subscribe_topic, mqtt.QoS.AT_LEAST_ONCE, on_message_received)
    subscribe_result = subscribe_future.result()
    logging.info(f"Subscribed with {str(subscribe_result['qos'])}")
    mqtt_send_state("lock")
    # Start threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        logging.info("submitting threads")
        executor.submit(video_thread, aws_pipeline)
        executor.submit(rekognition_thread, aws_pipeline)
        executor.submit(iot_thread, iot_pipeline)
    logging.info(f'Shutting down')
    # Shutdown AWS IoT Core
    disconnect_future = aws_iot.disconnect()
    disconnect_future.result()
