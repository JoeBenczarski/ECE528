import iot_comm
import concurrent.futures
from awscrt import io, mqtt
from awsiot import mqtt_connection_builder


class IotCommAws(iot_comm.IotComm):

    def __init__(self, client_id, endpoint, cert, key, root_ca, conn_int, conn_res):
        self.event_loop_group = io.EventLoopGroup(1)
        self.host_resolver = io.DefaultHostResolver(self.event_loop_group)
        self.client_bootstrap = io.ClientBootstrap(self.event_loop_group, self.host_resolver)
        self.connection = mqtt_connection_builder.mtls_from_path(
            endpoint=endpoint,
            cert_filepath=cert,
            pri_key_filepath=key,
            client_bootstrap=self.client_bootstrap,
            ca_filepath=root_ca,
            on_connection_interrupted=conn_int,
            on_connection_resumed=conn_res,
            client_id=client_id,
            clean_session=False,
            keep_alive_secs=6)

    def connect(self) -> concurrent.futures.Future:
        return self.connection.connect()

    def disconnect(self) -> concurrent.futures.Future:
        return self.connection.disconnect()

    def subscribe(self, topic: str, qos: mqtt.QoS, on_receive=None) -> (concurrent.futures.Future, int):
        return self.connection.subscribe(topic=topic, qos=qos, callback=on_receive)

    def publish(self, topic, payload, qos) -> (concurrent.futures.Future, int):
        return self.connection.publish(topic=topic, payload=payload, qos=qos)
