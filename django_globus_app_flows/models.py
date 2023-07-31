from django.db import models
from django.contrib.auth.models import User


class Flow(models.Model):
    id = models.CharField(max_length=128, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class Run(models.Model):
    id = models.CharField(max_length=128, primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    flow = models.ForeignKey(Flow, on_delete=models.CASCADE)
    status = models.CharField(max_length=128)


class Deployment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payload = models.TextField()


class Batch(models.Model):
    name = models.CharField(max_length=128)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    index = models.CharField(max_length=128)
    query = models.CharField(max_length=512)
    date_created = models.DateTimeField(auto_now_add=True)
    flows = models.ManyToManyField(Flow)
