
import time
from slth.tasks import Task

class FazerAlgumaCoisa(Task):

    def run(self):
        for i in self.iterate(range(1, 10)):
            print(i)
            time.sleep(1)
