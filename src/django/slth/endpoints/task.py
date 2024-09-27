from django.core.cache import cache
from .. import endpoints


class TaskProgress(endpoints.PublicEndpoint):

    def __init__(self, key):
        self.key = key
        super().__init__()

    def get(self):
        return cache.get(self.key)
