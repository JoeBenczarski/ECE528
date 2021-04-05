import device
import iot_comm


class IotDevice(device.Device):

    def __init__(self, name: str, comm: iot_comm.IotComm):
        super(IotDevice, self).__init__(name)
        self.comm = comm

    def send(self, message):
        self.comm.publish()
