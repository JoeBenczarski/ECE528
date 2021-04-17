import threading


Unlocked = 0
Locked = 1


class Lock(object):

    def __init__(self, device_ctrl):
        self.state = Locked
        self.device_controller_ = device_ctrl
        self.locker = threading.Lock()

    def lock(self):
        with self.locker:
            response = self.device_controller_.lock()
            self.state = Locked
        return response

    def unlock(self):
        with self.locker:
            response = self.device_controller_.unlock()
            self.state = Unlocked
        return response

    def get_state(self):
        with self.locker:
            state = self.state
        return state
