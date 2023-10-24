import threading
import logging
import time

log = logging.getLogger(__name__)


class SingleThreadedWorker:
    workers = []
    max_workers = 2

    def start(self):
        if len(self.workers) >= self.max_workers:
            log.debug(f"{self}: Additional worker attempted to start, aborting!")
            return
        log.info(f"{self}: Starting worker with 1 thread")
        self.workers.append(self)
        threading.Thread(target=self._run_thread, daemon=True, args=()).start()

    def _run_thread(self):
        time.sleep(5)
        while True:
            self.do_work()
            log.debug(f"{self} tick...")
            time.sleep(5)
        log.info(f"{self}: Shutdown successful")

    def do_work(self):
        raise NotImplemented(f"{self} has not implemented do_work!")
