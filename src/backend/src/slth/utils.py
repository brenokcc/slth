

def absolute_url(request, *querystrings):
    url = ''
    if request:
        url = "{}://{}{}".format(request.META.get('X-Forwarded-Proto', request.scheme), request.get_host(), request.path)
        if 'QUERY_STRING' in request.META:
            url = '{}?{}'.format(url, request.META['QUERY_STRING'])
    for querystring in querystrings:
        if querystring:
            querystring = querystring.replace('?', '')
            if '?' not in url:
                url = f'{url}?{querystring}'
            else:
                url = f'{url}&{querystring}'
    return url
        