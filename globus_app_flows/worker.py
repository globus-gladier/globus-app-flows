import threading
import logging
import time
import signal

log = logging.getLogger(__name__)


class SingleThreadedWorker:
    shutdown_flag = False
    workers = []
    max_workers = 2

    def shutdown(self, *args):
        log.debug(f"Shutdown initiated for {self}")
        self.shutdown_flag = True

    def start(self):
        signal.signal(signal.SIGINT, self.shutdown)
        if len(self.workers) >= self.max_workers:
            log.debug(f"{self}: Additional worker attempted to start, aborting!")
            return
        log.info(f"{self}: Starting worker with 1 thread")
        self.workers.append(self)
        threading.Thread(target=self._run_thread, daemon=True, args=()).start()

    def _run_thread(self):
        time.sleep(5)
        while self.shutdown_flag is False:
            self.do_work()
            time.sleep(5)
        log.info(f"{self}: Shutdown successful")

    def do_work(self):
        raise NotImplemented(f"{self} has not implemented do_work!")
