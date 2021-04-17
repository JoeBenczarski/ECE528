from abc import ABC, abstractmethod
from lock.lock_state import LockState


class LockAbstract(ABC):

    def __init__(self):
        self.state = LockState.LOCKED
        super().__init__()

    @abstractmethod
    def lock(self) -> LockState:
        raise NotImplementedError

    @abstractmethod
    def unlock(self) -> LockState:
        raise NotImplementedError
