

def build_url(request, path=None):
    url = ''
    if request:
        port = request.META.get('HTTP_X_FORWARDED_PORT', request.get_port())
        port = '' if port in (80, 443) else f':{port}'
        url = "{}://{}{}{}".format(
            request.META.get('HTTP_X_FORWARDED_PROTO', request.scheme),
            request.get_host().split(':')[0], port, path or request.path
        )
    return url

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
