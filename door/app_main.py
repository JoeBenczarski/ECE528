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


# Globals
aws_pipeline = queue.Queue()
iot_pipeline = queue.Queue()
capturing = threading.Event()


# IoT callbacks
def on_connection_interrupted(connection, error, **kwargs):
    logging.info(f"Connection interrupted. error: {error}")


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


# Thread for video handling
def video_thread(pipeline: queue.Queue):
    past = time.time()
    video = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not video.isOpened():
        capturing.clear()
    while capturing.is_set():
        _, frame = video.read()
        cv2.imshow('Video Feed', frame)
        elapsed = time.time() - past
        if elapsed > 2:
            pipeline.put(frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            capturing.clear()
            break
    video.release()
    cv2.destroyAllWindows()


# Thread for AWS Rekognition
def rekognition_thread(pipeline: queue.Queue):
    detector = face_detector.FaceDetector()
    while capturing.is_set():
        frame = pipeline.get(block=True)
        _, frame_png = cv2.imencode('.png', frame)
        frame_bytes = frame_png.tobytes()
        prob = detector.detect_face_from_bytes(frame_bytes)
        if prob > 0.90:
            logging.debug(f'Probability: {prob}  Face detected')
        else:
            logging.debug(f'Probability: {prob}  No face detected')


# Thread for AWS IoT
def iot_thread(pipeline: queue.Queue):
    while capturing.is_set():
        info = iot_pipeline.get(block=True)
        topic = info['topic']
        message = json.loads(info['payload'].decode("utf-8"))
        logging.debug(f"Topic: {topic}  Message: {message}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    capturing.set()
    logging.info(f'Starting video feed')

    cert_path = os.path.abspath('./certs/5b35693745-certificate.pem.crt')
    key_path = os.path.abspath('./certs/5b35693745-private.pem.key')
    root_ca_path = os.path.abspath('./certs/AmazonRootCA1.pem')
    endpoint = "aeuwkvsf1rv59-ats.iot.us-east-1.amazonaws.com"
    client = "door-lock"
    subscribe_topic = "cmd/lock/state"
    aws_iot = iot_comm_aws.IotCommAws(client_id=client, endpoint=endpoint,
                                      cert=cert_path, key=key_path, root_ca=root_ca_path,
                                      conn_int=on_connection_interrupted, conn_res=on_connection_resumed)
    connect_future = aws_iot.connect()
    connect_future.result()
    subscribe_future, packet_id = aws_iot.subscribe(subscribe_topic, mqtt.QoS.AT_LEAST_ONCE, on_message_received)
    subscribe_result = subscribe_future.result()
    logging.info(f"Subscribed with {str(subscribe_result['qos'])}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        executor.submit(video_thread, aws_pipeline)
        executor.submit(rekognition_thread, aws_pipeline)
        executor.submit(iot_thread, iot_pipeline)

    disconnect_future = aws_iot.disconnect()
    disconnect_future.result()
    logging.info(f'Shutting down')