
class LockPhysical(object):

    def __init__(self):
        pass

    def lock(self):
        return "{}: Locked".format(self.__module__)

    def unlock(self):
        return "{}: Unlocked".format(self.__module__)
