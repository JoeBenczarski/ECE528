import concurrent.futures
from awscrt import io, mqtt
from awsiot import mqtt_connection_builder
from iot_mqtt.iot_mqtt import IotMqtt


class MqttAws(IotMqtt):

    _instance = None
    event_loop_group = None
    host_resolver = None
    client_bootstrap = None
    connection = None

    def __init__(self):
        raise RuntimeError('Call instance() instead')

    @classmethod
    def create_instance(cls, client_id, endpoint, cert, key, root_ca, conn_int, conn_res):
        if cls._instance is None:
            cls._instance = cls.__new__(cls)
            cls.event_loop_group = io.EventLoopGroup(1)
            cls.host_resolver = io.DefaultHostResolver(cls.event_loop_group)
            cls.client_bootstrap = io.ClientBootstrap(cls.event_loop_group, cls.host_resolver)
            cls.connection = mqtt_connection_builder.mtls_from_path(
                endpoint=endpoint,
                cert_filepath=cert,
                pri_key_filepath=key,
                client_bootstrap=cls.client_bootstrap,
                ca_filepath=root_ca,
                on_connection_interrupted=conn_int,
                on_connection_resumed=conn_res,
                client_id=client_id,
                clean_session=False,
                keep_alive_secs=6)
        return cls._instance

    @classmethod
    def get_instance(cls):
        return cls._instance

    def connect(self) -> concurrent.futures.Future:
        return self.connection.connect()

    def disconnect(self) -> concurrent.futures.Future:
        return self.connection.disconnect()

    def subscribe(self, topic: str, qos: mqtt.QoS, on_receive=None) -> (concurrent.futures.Future, int):
        return self.connection.subscribe(topic=topic, qos=qos, callback=on_receive)

    def publish(self, topic, payload, qos) -> (concurrent.futures.Future, int):
        return self.connection.publish(topic=topic, payload=payload, qos=qos)
