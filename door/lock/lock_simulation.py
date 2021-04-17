from lock.lock_abstract import LockAbstract
from lock.lock_state import LockState
import time


DEVICE_DELAY = 0
LOCK_MSG = "LockSimulation: Locked"
UNLOCK_MSG = "LockSimulation: Unlocked"


class LockSimulation(LockAbstract):

    def lock(self) -> LockState:
        time.sleep(DEVICE_DELAY)
        self.state = LockState.LOCKED
        return self.state

    def unlock(self) -> LockState:
        time.sleep(DEVICE_DELAY)
        self.state = LockState.UNLOCKED
        return self.state
