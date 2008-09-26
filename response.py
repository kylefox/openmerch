class Response(object):
    def __init__(self, success, message, params={}, options={}):
        self.success = success
        self.message = message
        self.params = params
        self.test = options.setdefault('test', False)
        self.authorization = options['authorization']
        self.fraud_review = options['fraud_review']
