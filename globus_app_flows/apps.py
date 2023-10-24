import os
from django.apps import AppConfig


class GlobusAppFlows(AppConfig):
    name = "globus_app_flows"

    def ready(self):
        from globus_app_flows.collectors.worker import CollectionWorker
        from globus_app_flows.flows.worker import RunWorkerQueue

        if os.environ.get("RUN_MAIN"):
            cw = CollectionWorker()
            cw.start()

            rw = RunWorkerQueue()
            rw.start()
