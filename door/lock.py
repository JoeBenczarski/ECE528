
Unlocked = 0
Locked = 1


class Lock(object):

    def __init__(self, device_ctrl):
        self.state = Unlocked
        self.device_controller_ = device_ctrl

    def lock(self):
        result = self.device_controller_.lock()
        self.state = Locked

    def unlock(self):
        result = self.device_controller_.unlock()
        self.state = Unlocked
