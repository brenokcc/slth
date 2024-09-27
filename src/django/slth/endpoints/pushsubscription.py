import json
from slth import endpoints
from ..models import PushSubscription
from ..components import Response


class PushSubscriptions(endpoints.ListEndpoint[PushSubscription]):
    def check_permission(self):
        return self.check_role()


class Add(endpoints.AddEndpoint[PushSubscription]):
    def check_permission(self):
        return self.check_role()


class Edit(endpoints.EditEndpoint[PushSubscription]):
    def check_permission(self):
        return self.check_role()


class Delete(endpoints.DeleteEndpoint[PushSubscription]):
    def check_permission(self):
        return self.check_role()


class View(endpoints.ViewEndpoint[PushSubscription]):
    def check_permission(self):
        return self.check_role()


class Subscribe(endpoints.Endpoint):

    class Meta:
        verbose_name = "Subscrever para Notificações"

    def post(self):
        data = json.loads(self.request.POST.get("subscription"))
        device = self.request.META.get("HTTP_USER_AGENT", "")
        qs = PushSubscription.objects.filter(user=self.request.user, device=device)
        if qs.exists():
            qs.update(data=data)
        else:
            PushSubscription.objects.create(user=self.request.user, data=data, device=device)
        return Response()

    def check_permission(self):
        return True
