from django.apps import AppConfig


class GlobusAppFlows(AppConfig):
    name = "globus_app_flows"

    def ready(self):
        from globus_app_flows.collectors.worker import CollectionWorker

        cw = CollectionWorker()
        cw.start()
