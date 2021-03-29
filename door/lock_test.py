import unittest
import lock
import lock_physical


class LockTestCase(unittest.TestCase):

    def test_init(self):
        phys_lock = lock_physical.LockPhysical()
        virt_lock = lock.Lock(phys_lock)
        self.assertEqual(virt_lock.state == lock.Unlocked, True)

    def test_lock(self):
        phys_lock = lock_physical.LockPhysical()
        virt_lock = lock.Lock(phys_lock)
        self.assertEqual(virt_lock.state == lock.Unlocked, True)
        virt_lock.lock()
        self.assertEqual(virt_lock.state == lock.Locked, True)

    def test_unlock(self):
        phys_lock = lock_physical.LockPhysical()
        virt_lock = lock.Lock(phys_lock)
        self.assertEqual(virt_lock.state == lock.Unlocked, True)
        virt_lock.lock()
        self.assertEqual(virt_lock.state == lock.Locked, True)
        virt_lock.unlock()
        self.assertEqual(virt_lock.state == lock.Unlocked, True)


if __name__ == '__main__':
    unittest.main()
