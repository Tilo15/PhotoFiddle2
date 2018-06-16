import threading
import time

class Debouncer:
    def __init__(self, callback, complete=False, interval=0.5):
        self.callback = callback
        self.complete_callback = complete
        self.interval = interval
        self.called_while_running = False
        self.called_during_timeout = False
        self.timeout_set = False
        self.running = False
        self.latest_args = []

    def call(self, *args):
        self.latest_args = args

        if(self.timeout_set):
            self.called_during_timeout = True

        elif(self.running):
            self.called_while_running = True

        else:
            threading.Thread(target=self._timeout).start()

    def _timeout(self):
        self.timeout_set = True
        time.sleep(self.interval)
        self.timeout_set = False

        if(self.called_during_timeout):
            self.called_during_timeout = False
            self._timeout()
            return

        self.running = True
        res = self.callback(*self.latest_args)
        self.running = False

        if(self.called_while_running):
            self.called_while_running = False
            self._timeout()
        
        elif(self.complete_callback):
            self.complete_callback(res)
