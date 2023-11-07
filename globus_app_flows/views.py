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
from django import forms

from globus_portal_framework.gsearch import get_template
from globus_portal_framework.gclients import get_user_groups

from globus_app_flows.models import Batch, Collector, Flow, FlowAuthorization

from django.http import HttpResponse
from django.views import View


log = logging.getLogger(__name__)


class BatchCreateView(FormView):
    collector = None
    flow = None
    group = None
    authorization_type = "User"
    authorization_key = None

    def save_temp_collector(self, collector):
        log.debug(f"Saving collector in SESSION")
        self.request.session["collector"] = collector.get_metadata()
        log.debug(self.request.session["collector"])

    def load_collector(self):
        values = self.request.session.get("collector")
        if not values:
            raise ValueError(f"Unable to load collector {self}")
        return values

    def _get_user_group(self, user_groups):
        for group in user_groups:
            if group["id"] == self.group:
                return group

    def ensure_authorized(self):
        if not self.group:
            raise ValueError("'group' must be set on the class {self} in order to authorize flows")

        log.debug(f"Checking if user {self.request.user} authorized to run flow...")
        user_groups = get_user_groups(self.request.user)
        try:
            user_group = self._get_user_group(user_groups)
            assert user_group is not None, f"User is not in group {self.group}"
            assert any(m["status"] == "active" for m in user_group["my_memberships"])
        except (StopIteration, AssertionError):
            raise ValueError(
                f"User {self.request.user} is not authorized to run this flow!"
            )

    def get(self, request, index, *args, **kwargs):
        self.ensure_authorized()
        request = super().get(request, *args, **kwargs)
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

    def get_flow_authorization(
        self, authorization_type: str, authorization_key: str, form: forms.Form = None
    ) -> FlowAuthorization:
        obj, created = FlowAuthorization.objects.get_or_create(
            authorization_type=authorization_type, authorization_key=authorization_key
        )
        return obj

    def get_collector(self):
        ctype = self.get_collector_class().get_import_string()
        collector = Collector(
            data=dict(self.load_collector()),
            user=self.request.user,
            collector_type=ctype,
        )
        return collector

    def get_batch(self, authorization, collector, form):
        batch = Batch(
            name="Reprocessing Batch",
            user=self.request.user,
            authorization=authorization,
            collector=collector,
            started=None,
            completed=None,
            flow=self.get_flow(),
        )
        batch.form = form.cleaned_data
        return batch

    def form_valid(self, form):
        response = super().form_valid(form)
        authorization = self.get_flow_authorization(
            self.authorization_type, self.authorization_key, form=form
        )
        collector = self.get_collector()
        collector.save()
        batch = self.get_batch(authorization, collector, form)
        batch.save()

        messages.success(self.request, f"Processing data in {batch}")
        return response
