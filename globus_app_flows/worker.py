import threading
import logging
import time

log = logging.getLogger(__name__)


class SingleThreadedWorker:
    workers = []
    max_workers = 1

    def start(self):
        if len(self.workers) > self.max_workers:
            log.debug(f"Additional worker attempted to start, aborting!")
        log.info(f"{self}: Starting worker with 1 thread")
        self.workers.append(self)
        threading.Thread(target=self._run_thread, daemon=True, args=()).start()

    def _run_thread(self):
        time.sleep(20)
        while True:
            self.do_work()
            # log.debug(f'Work tick...')
            time.sleep(5)
        log.info(f"{self}: Shutdown successful")

    def do_work(self):
        raise NotImplemented(f"{self} has not implemented do_work!")
