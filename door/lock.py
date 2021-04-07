
Unlocked = 0
Locked = 1


class Lock(object):

    def __init__(self, device_ctrl):
        self.state = Unlocked
        self.device_controller_ = device_ctrl

    def lock(self):
        response = self.device_controller_.lock()
        self.state = Locked
        return response

    def unlock(self):
        response = self.device_controller_.unlock()
        self.state = Unlocked
        return response
