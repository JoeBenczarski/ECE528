import threading
import queue
import logging
import time
import cv2
import json
from lock import lock_simulation, lock_virtual
from lock.lock_state import LockState
from detection.face_detector import FaceDetector
from iot_mqtt.mqtt_aws import MqttAws
from awsiot import mqtt


aws_pipeline = queue.Queue()
iot_pipeline = queue.Queue()
stop_capture = threading.Event()
deadbolt = lock_virtual.LockVirtual(lock_simulation.LockSimulation())
aws_iot = MqttAws.get_instance()


# Mqtt Dispatcher
def mqtt_dispatch(topic: str, payload: dict):
    topic_levels = topic.split("/")
    if topic_levels[0] == "cmd":
        logging.debug("Received command")
        # Handle incoming command
        if topic_levels[1] == "lock":
            if topic_levels[2] == "state":
                if payload["state"] == "lock":
                    state = deadbolt.lock_device().result()
                    mqtt_send_state(state)
                    logging.info(state)
                elif payload["state"] == "unlock":
                    state = deadbolt.unlock_device().result()
                    mqtt_send_state(state)
                    logging.info(state)
                else:
                    raise NotImplementedError
    elif topic_levels[0] == "dt":
        # Handle incoming data
        pass
    else:
        raise NotImplementedError


def mqtt_send_state(state: LockState):
    topic = "dt/lock/state"
    lookup = {LockState.LOCKED: "lock", LockState.UNLOCKED: "unlock"}
    payload = json.dumps({"state": lookup[state]})
    aws_iot.publish(topic=topic, payload=payload, qos=mqtt.QoS.AT_LEAST_ONCE)


# Thread for video handling
def video_thread(pipeline: queue.Queue):
    past = time.time()
    video = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    if not video.isOpened():
        stop_capture.set()
    while True:
        if stop_capture.is_set():
            logging.info(f"video thread detected stop capture")
            break
        _, frame = video.read()
        cv2.imshow('Video Feed', frame)
        elapsed = time.time() - past
        if elapsed > 2:
            past = time.time()
            if deadbolt.get_state() is LockState.LOCKED:
                try:
                    pipeline.put(frame, timeout=1)
                except queue.Empty:
                    logging.debug(f"video queue full")
        # must call wait key for cv2.imshow to work
        if cv2.waitKey(1) & 0xFF == ord('q'):
            stop_capture.set()
    video.release()
    cv2.destroyAllWindows()


# Thread for AWS Rekognition
def rekognition_thread(pipeline: queue.Queue):
    detector = FaceDetector()
    while True:
        if stop_capture.is_set():
            logging.info(f"rekognition thread detected stop capture")
            break
        try:
            frame = pipeline.get(block=True, timeout=1)
            _, frame_png = cv2.imencode('.png', frame)
            frame_bytes = frame_png.tobytes()
            if deadbolt.get_state() is LockState.LOCKED:
                prob = detector.detect_face_from_bytes(frame_bytes)
                if prob > 0.75:
                    logging.info(f'Probability: {prob}  Face detected')
                    # check if this is an authorized person
                    with open('images/Joe-Benczarski.jpg', 'rb') as tgt:
                        auth = detector.compare_face_from_bytes(frame_bytes, tgt.read(), 99.5)
                        if auth:
                            logging.info(f"Detected authorized person")
                            # Unlock the door
                            unlock_future = deadbolt.unlock_device()
                            mqtt_send_state(unlock_future.result())
                        else:
                            logging.info(f"Detected a Guest")
                else:
                    logging.info(f'Probability: {prob}  No face detected')
        except queue.Empty:
            logging.debug(f"rekognition queue timeout")


# Thread for AWS IoT
def iot_thread(pipeline: queue.Queue):
    mqtt_send_state(LockState.LOCKED)
    while True:
        if stop_capture.is_set():
            logging.info(f"iot thread detected stop capture")
            break
        try:
            info = pipeline.get(block=True, timeout=1)
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
