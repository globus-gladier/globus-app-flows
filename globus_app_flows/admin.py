from django.contrib import admin
from globus_app_flows.models import (
    Batch,
    Collector,
    Flow,
    Run,
    Deployment,
    FlowAuthorization,
)

admin.site.register(FlowAuthorization)
admin.site.register(Batch)
admin.site.register(Collector)
admin.site.register(Flow)
admin.site.register(Run)
admin.site.register(Deployment)
