import concurrent.futures
import logging
from awscrt import mqtt
from configuration.configuration import read_configuration

from iot_mqtt.mqtt_aws import MqttAws
from app_threads import iot_thread, rekognition_thread, video_thread, iot_pipeline, aws_pipeline
from iot_mqtt.mqtt_aws_cb import on_message_received, on_connection_resumed, on_connection_interrupted


# Logging level
LOG_LEVEL = logging.INFO


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=LOG_LEVEL, format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
    # Read config
    config = read_configuration()
    aws_iot = MqttAws.create_instance(client_id=config['client'], endpoint=config['endpoint'],
                                      cert= config['cert_path'], key=config['key_path'],
                                      root_ca=config['root_ca_path'], conn_int=on_connection_interrupted,
                                      conn_res=on_connection_resumed)

    subscribe_topic = "cmd/lock/state"
    connect_future = aws_iot.connect()
    connect_future.result()
    subscribe_future, packet_id = aws_iot.subscribe(subscribe_topic, mqtt.QoS.AT_LEAST_ONCE, on_message_received)
    subscribe_result = subscribe_future.result()
    logging.info(f"Subscribed to {subscribe_topic} with {str(subscribe_result['qos'])}")

    # Start threads
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        logging.info("submitting threads")
        executor.submit(video_thread, aws_pipeline)
        executor.submit(rekognition_thread, aws_pipeline)
        executor.submit(iot_thread, iot_pipeline)

    # Shutdown
    logging.info(f'Shutting down')
    disconnect_future = aws_iot.disconnect()
    disconnect_future.result()

