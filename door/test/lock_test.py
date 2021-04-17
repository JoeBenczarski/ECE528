import unittest
import logging
import lock
from lock.lock_state import LockState
from lock.lock_virtual import LockVirtual
from lock.lock_simulation import LockSimulation

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s', datefmt='%d-%b-%y %H:%M:%S')
ls = LockSimulation()
lv = LockVirtual(ls)


class LockTestCase(unittest.TestCase):

    def test_init(self):
        self.assertEqual(lv.get_state() == LockState.LOCKED, True)
        
    def test_unlock(self):
        unlock_future = lv.unlock_device()
        self.assertEqual(unlock_future.result() == LockState.UNLOCKED, True)
        self.assertEqual(lv.get_state() == LockState.UNLOCKED, True)

    def test_lock(self):
        lock_future = lv.lock_device()
        self.assertEqual(lock_future.result() == LockState.LOCKED, True)
        self.assertEqual(lv.get_state() == LockState.LOCKED, True)


if __name__ == '__main__':
    unittest.main()
