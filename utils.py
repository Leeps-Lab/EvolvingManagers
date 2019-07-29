import threading
import time


# this is almost a copy of otree-redwood's DiscreteEventEmitter
# redwood's doesn't allow multiple emitters to exist per group for some reason
# I didn't want to deal with making that change to redwood and having to update everything
# so there's just a copy of it here
class DiscreteEventEmitter():

    def __init__(self, interval, period_length, group, callback, start_immediate=False):
        self.interval = float(interval)
        self.period_length = period_length
        self.group = group
        self.intervals = self.period_length / self.interval
        self.callback = callback
        self.current_interval = 0
        self.timer = threading.Timer(0 if start_immediate else self.interval, self._tick)

    def _tick(self):
        start = time.time()
        self.callback(self.current_interval, self.intervals)
        self.current_interval += 1
        if self.current_interval < self.intervals:
            self.timer = threading.Timer(self._time, self._tick)
            self.timer.start()
    
    @property
    def _time(self):
        return self.interval - ((time.time() - self.start_time) % self.interval)

    def start(self):
        if self.timer:
            self.start_time = time.time()
            self.timer.start()

    def stop(self):
        del self.timer
