import urllib2

def post(url, data, headers={}):
    print data
    request = urllib2.Request(url=url, data=data, headers=headers)
    response = urllib2.urlopen(request)
    return response.read()
