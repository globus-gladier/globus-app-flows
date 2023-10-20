import logging

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
                user=collector_model.user, flow=batch.flow, status="READY", batch=batch
            )
            run_input = collector.get_run_input(item, batch.form)
            run.run_input = item
            run.save()
            log.debug(f"Saved run {run} in batch {batch}, is now {run.status}")

        collector_model.status = "COMPLTED"
        collector_model.save()
        log.debug(f"Worker tick: Finished searching for batches.")
