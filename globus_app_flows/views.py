from typing import Any, Dict
import logging
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from django.utils.timezone import timezone

from globus_portal_framework.gsearch import get_template

from globus_app_flows.models import Batch, Collector, Flow

from django.http import HttpResponse
from django.views import View


log = logging.getLogger(__name__)


class BatchCreateView(FormView):
    collector = None
    flow = None
    group = None

    def save_temp_collector(self, collector):
        log.debug(f"Saving collector in SESSION")
        self.request.session["collector"] = collector.get_metadata()
        log.debug(self.request.session["collector"])

    def load_collector(self):
        values = self.request.session.get("collector")
        if not values:
            raise ValueError(f"Unable to load collector {self}")
        return values

    def ensure_authorized(self):
        log.debug(f"Checking if user {self.request.user} authorized to run flow...")
        user_groups = get_user_groups(self.request.user)
        try:
            az_group = next(filter(lambda g: g["id"] == self.group, user_groups))
            assert any(m["status"] == "active" for m in az_group["my_memberships"])
        except (StopIteration, AssertionError):
            raise ValueError(
                f"User {self.request.user} is not authorized to run this flow!"
            )

    def get(self, request, index, *args, **kwargs):
        self.ensure_authorized
        request = super().get(request, *args, **kwargs)
        log.debug((request, index, args, kwargs))
        col_inst = self.get_collector_class().from_get_request(
            self.request, index, *args, **kwargs
        )
        self.save_temp_collector(col_inst)
        return request

    def get_collector_class(self):
        if self.collector is None:
            raise ValueError(f"You need to set collector on {self}")
        return self.collector

    def get_flow(self):
        if self.flow is None:
            raise ValueError(
                "Need to set 'flow' to a valid flow uuid as class attribute"
            )
        return Flow.objects.get(flow_id=self.flow)

    def form_valid(self, form):
        response = super().form_valid(form)
        ctype = self.get_collector_class().get_import_string()
        collector = Collector(
            data=dict(self.load_collector()),
            user=self.request.user,
            collector_type=ctype,
        )
        collector.save()
        batch = Batch(
            name="hello batch",
            user=self.request.user,
            collector=collector,
            started=None,
            completed=None,
            flow=self.get_flow(),
        )
        batch.form = form.cleaned_data
        batch.save()

        messages.success(self.request, f"Processing data in {batch}")
        return response
