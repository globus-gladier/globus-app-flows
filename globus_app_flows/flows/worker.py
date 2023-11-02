import logging
import time
import traceback

from django.conf import settings
from django.utils import timezone

from globus_app_flows.worker import SingleThreadedWorker
from globus_app_flows.models import Batch, Run
from globus_app_flows.collectors import get_collector
from globus_app_flows.flows.auth import get_specific_flow_client, get_flows_client


log = logging.getLogger(__name__)

DGAF_SETTINGS = getattr(settings, "GLOBUS_APP_FLOWS", {})


class RunWorkerQueue(SingleThreadedWorker):
    FLOW_TERMINATED = ["SUCCEEDED", "FAILED"]
    CONCURRENT_RUNS = DGAF_SETTINGS.get("concurrent_runs", 10)

    def do_work(self):
        active_runs = self.check_runs()
        if active_runs:
            log.info(f"Run queue {active_runs}/{self.CONCURRENT_RUNS}")

        if active_runs < self.CONCURRENT_RUNS:
            to_start = self.CONCURRENT_RUNS - active_runs
            self.start_runs(to_start)
        else:
            time.sleep(5)

    def start_runs(self, limit: int):
        runs = Run.objects.filter(status="READY")[:limit]
        for run in runs:
            sfc = get_specific_flow_client(run.flow, run.authorization, run.user)
            try:
                run.started = timezone.now()
                run.status = "ACTIVE"
                response = sfc.run_flow(
                    body=run.payload, label=run.label, **run.start_kwargs
                )
                run.run_id = response["run_id"]
            except Exception as e:
                run.error_data = str(e)
                run.status = "FAILED"
                run.completed = timezone.now()
            finally:
                run.save()

    def check_runs(self):
        runs = Run.objects.filter(status="ACTIVE")
        for run in runs:
            try:
                fc = get_flows_client(run.authorization, run.user)
                response = fc.get_run(run.run_id)
                run.status = response["status"]
                if run.status in self.FLOW_TERMINATED:
                    if run.status == "FALIED":
                        run.error_data = "Run failed during execution. More details in the flows service"
                        run.completed = timezone.now()
                run.save()
            except Exception as e:
                run.error_data = str(e)
                run.status = "FAILED"
                run.save()
                log.info(f"Run by user {run.user} FAILED.")
                if settings.DEBUG:
                    log.exception(e)
        return Run.objects.filter(status="ACTIVE").count()
