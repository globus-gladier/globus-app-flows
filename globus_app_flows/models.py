import json
from django.db import models
from django.contrib.auth.models import User


class Flow(models.Model):
    flow_id = models.CharField(max_length=128, primary_key=True)
    flow_scope = models.CharField(max_length=128)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class Run(models.Model):
    # TODO: These need to be verified
    STATUSES = ["IDLE", "READY", "STARTED", "RUNING", "COMPLETED", "FAILED"]
    AUTHORIZATION_TYPES = ["USER", "CONFIDENTIAL_CLIENT", "CONFIDENTIAL_TOKEN"]

    run_id = models.CharField(max_length=128)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    flow = models.ForeignKey(Flow, on_delete=models.CASCADE)
    batch = models.ForeignKey("Batch", on_delete=models.CASCADE)
    authorization_type = models.CharField(
        max_length=128, choices=[(c, c) for c in AUTHORIZATION_TYPES], default="USER"
    )
    authorization_key = models.CharField(max_length=128, null=True, blank=True)
    status = models.CharField(
        max_length=128, choices=[(c, c) for c in STATUSES], default="IDLE"
    )
    started = models.DateTimeField(null=True, blank=True)
    completed = models.DateTimeField(null=True, blank=True)
    payload = models.TextField()
    error_data = models.TextField()

    @property
    def run_input(self):
        return json.loads(self.payload or "{}")

    @run_input.setter
    def run_input(self, value: dict):
        self.payload = json.dumps(value)


class Deployment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payload = models.TextField()


class Batch(models.Model):
    STATUSES = ["IDLE", "READY", "COLLECTING", "RUNNING", "COMPLETED", "FAILED"]

    name = models.CharField(max_length=128)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    flow = models.ForeignKey(Flow, on_delete=models.CASCADE)
    collector = models.ForeignKey("Collector", on_delete=models.CASCADE)
    form_data = models.TextField()
    status = models.CharField(
        max_length=128, choices=[(c, c) for c in STATUSES], default="IDLE"
    )
    started = models.DateTimeField(null=True, blank=True)
    completed = models.DateTimeField(null=True, blank=True)

    @property
    def form(self):
        return json.loads(self.form_data or "{}")

    @form.setter
    def form(self, value: dict):
        self.form_data = json.dumps(value)


class Collector(models.Model):
    STATUSES = ["IDLE", "READY", "COLLECTING", "COMPLETED", "FAILED"]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    collector_type = models.CharField(max_length=128)
    status = models.CharField(
        max_length=128, choices=[(c, c) for c in STATUSES], default="IDLE"
    )
    collector_data = models.TextField()

    @property
    def data(self):
        return json.loads(self.collector_data or "{}")

    @data.setter
    def data(self, value: dict):
        self.collector_data = json.dumps(value)
