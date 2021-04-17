from abc import ABC, abstractmethod


class IotMqtt(ABC):

    @abstractmethod
    def connect(self):
        raise NotImplementedError

    @abstractmethod
    def disconnect(self):
        raise NotImplementedError

    @abstractmethod
    def subscribe(self, topic, qos, callback):
        raise NotImplementedError

    @abstractmethod
    def publish(self, topic, payload, qos):
        raise NotImplementedError
