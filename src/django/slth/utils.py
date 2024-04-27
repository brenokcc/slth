from django.conf import settings

def build_url(request, path=None):
    return path or request.path if request else ''

def absolute_url(request, *querystrings):
    url = build_url(request)
    if url:
        querstring = request.META.get('QUERY_STRING')
        url = append_url(url, querstring)
        for querystring in querystrings:
            url = append_url(url, querystring)
    return url

def append_url(url, *querystrings):
    params = {}
    if '?' in url:
        url, querystring = url.split('?')
        if querystring:
            for param in querystring.split('&'):
                k, v = param.split('=')
                params[k] = v
    else:
        url, querystring = url, ''
    for querystring in querystrings:
        if querystring:
            for param in querystring.split('&'):
                k, v = param.split('=')
                params[k] = v
    if params:
        url = '{}?{}'.format(url, '&'.join([f'{k}={v}' for k, v in params.items()]))
    return url
