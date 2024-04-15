

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
        if request and 'QUERY_STRING' in request.META and request.META['QUERY_STRING']:
            url = '{}?{}'.format(url, request.META['QUERY_STRING'])
        for querystring in querystrings:
            if querystring:
                querystring = querystring.replace('?', '')
                url = f'{url}?{querystring}' if '?' not in url else f'{url}&{querystring}'
    return url

def append_url(url, *querystrings):
    for querystring in querystrings:
        if querystring:
            querystring = querystring.replace('?', '')
            url = f'{url}?{querystring}' if '?' not in url else f'{url}&{querystring}'
    return url
