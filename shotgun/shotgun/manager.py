from shotgun.driver import Driver

class Manager(object):
    def __init__(self, conf):
        self.conf = conf

    def snapshot(self):
        for obj_data in self.conf.objects:
            driver = Driver.getDriver(obj_data, self.conf)
            driver.snapshot()

