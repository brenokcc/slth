from slth import timezone


class Middleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tz = request.path[0] == '/' and (request.META.get('HTTP_TZ') or request.META.get('TZ'))
        if tz:
            timezone.activate(tz)
        response = self.get_response(request)
        if tz:
            timezone.deactivate()
        return response
