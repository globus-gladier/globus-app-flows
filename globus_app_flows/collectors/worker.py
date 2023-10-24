import logging

from django.conf import settings
from globus_app_flows.worker import SingleThreadedWorker
from globus_app_flows.models import Batch, Run
from globus_app_flows.collectors import get_collector


log = logging.getLogger(__name__)


class CollectionWorker(SingleThreadedWorker):
    def do_work(self):
        batches = Batch.objects.filter(status="IDLE")
        for batch in batches:
            try:
                self.collect_batch(batch)
                log.info(f"Successfully collected items for batch {batch}")
                batch.status = "READY"
                batch.save()
            except Exception as e:
                raise
                log.exception(e)
                log.error(f"Failed to collect for batch {batch}")

    def collect_batch(self, batch):
        collector_model = batch.collector
        collector_class = get_collector(collector_model.collector_type)
        collector = collector_class(user=collector_model.user, **collector_model.data)
        collector_model.save()

        log.debug(f"Started collection for batch {batch}")
        for item in collector:
            run = Run(
                user=collector_model.user,
                flow=batch.flow,
                status="READY",
                batch=batch,
                authorization=batch.authorization,
            )
            try:
                run.run_input = collector.get_run_input(item, batch.form)
                start_kwargs = collector.get_run_start_kwargs(item, batch.form)
                if "label" in start_kwargs:
                    run.label = start_kwargs.pop("label")
                run.start_kwargs = start_kwargs
            except Exception as e:
                run.error_data = str(e)
                run.status = "FAILED"
                log.debug(
                    f"Run {run} failed to collect payload data. Debug:{settings.DEBUG}"
                )
                if settings.DEBUG:
                    log.exception(e)
            finally:
                run.save()
                log.debug(f"Saved run {run} in batch {batch}, is now {run.status}")

        collector_model.status = "COMPLTED"
        collector_model.save()
        log.debug(f"Worker tick: Finished searching for batches.")
