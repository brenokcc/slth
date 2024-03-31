

def absolute_url(request, *querystrings):
    url = ''
    if request:
        url = "{}://{}{}".format(request.META.get('X-Forwarded-Proto', request.scheme), request.get_host(), request.path)
        if 'QUERY_STRING' in request.META and request.META['QUERY_STRING']:
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
