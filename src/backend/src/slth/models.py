import os
import binascii
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _


class Photo(models.Model):
    
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    photo = models.ImageField(verbose_name=_("Photo"))

    class Meta:
        verbose_name = _("Photo")
        verbose_name_plural = _("Photos")


class Token(models.Model):
    key = models.CharField(_("Key"), max_length=40, primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created = models.DateTimeField(_("Created"), auto_now_add=True)

    class Meta:
        verbose_name = _("Token")
        verbose_name_plural = _("Tokens")

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = binascii.hexlify(os.urandom(20)).decode()
        return super().save(*args, **kwargs)

    def __str__(self):
        return self.key
