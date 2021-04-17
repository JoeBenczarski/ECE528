from lock.lock_abstract import LockAbstract
from concurrent.futures import ThreadPoolExecutor, Future


class LockVirtual(object):

    def __init__(self, lock_device: LockAbstract):
        super().__init__()
        self.device_ = lock_device
        self.future_ = self.lock_device()

    def lock_device(self) -> Future:
        with ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(self.device_.lock)

    def unlock_device(self) -> Future:
        with ThreadPoolExecutor(max_workers=1) as executor:
            return executor.submit(self.device_.unlock)

    def get_state(self):
        return self.device_.state
