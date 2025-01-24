from slth import endpoints
from ..models import WhatsappNotification


class WhatsappNotifications(endpoints.ListEndpoint[WhatsappNotification]):
    def get(self):
        return super().get().actions('whatsappnotification.send')
    def check_permission(self):
        return self.check_role()


class Add(endpoints.AddEndpoint[WhatsappNotification]):
    class Meta:
        modal = True
        icon = 'message'
    
    def check_permission(self):
        return self.check_role()
    
    def get_verbose_name(self):
        return 'Enviar Whatsapp'


class Edit(endpoints.EditEndpoint[WhatsappNotification]):
    def check_permission(self):
        return self.check_role()


class Delete(endpoints.DeleteEndpoint[WhatsappNotification]):
    def check_permission(self):
        return self.check_role()


class View(endpoints.ViewEndpoint[WhatsappNotification]):
    def check_permission(self):
        return self.check_role()


class Send(endpoints.InstanceEndpoint[WhatsappNotification]):
    class Meta:
        icon = "chevron-right"
        verbose_name = "Send"

    def check_permission(self):
        return self.check_role()
    
    def get(self):
        return self.formfactory().fields()
    
    def post(self):
        self.instance.send()
        return super().post()