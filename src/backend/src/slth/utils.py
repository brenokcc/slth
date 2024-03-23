

def absolute_url(request, *querystrings):
    url = request.path if request else ''
    for querystring in querystrings:
        if querystring:
            querystring = querystring.replace('?', '')
            if '?' not in url:
                url = f'{url}?{querystring}'
            else:
                url = f'{url}&{querystring}'
    return url
        