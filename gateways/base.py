class Gateway(object):
    DEBIT_CARDS = ('switch', 'solo')
    money_format = 'dollars'
    supported_cardtypes = []
    options = {}

    def __init__(self, gateway_mode='live'):
        self.gateway_mode = gateway_mode

    def supports(self, card_type):
        return (card_type in self.supported_cardtypes)

    def card_brand(self, source):
        try:
            result = source.brand
        except AttributeError:
            result = type(source)
        return str(result).lower()
    
    def is_test(self):
        return self.gateway_mode == 'test'

    def amount(self, money):
        if money is None:
            return None
        try:
            cents = money.cents
        except AttributeError:
            cents = money

        if type(money) == '' or int(cents) < 0:
            raise TypeError, 'money amount must be either a Money ojbect or a positive integer in cents.'

        if self.money_format == 'cents':
            return str(cents)
        return ("%.2f" % (float(cents) / 100))

    def currency(money):
        try:
            return money.currency
        except AttributeError:
            return self.default_currency

    def requires_start_data_or_issue_number(credit_card):
        if self.card_brand(credit_card).strip() == '':
            return False
        if card_brand(credit_card) in self.DEBIT_CARDS:
            return True
        return False

    def purchase(self, money, creditcard, **kwargs):
        raise NotImplementedError

    def authorize(self, money, creditcard, **kwargs):
        raise NotImplementedError

    def capture(self, money, authorization, **kwargs):
        raise NotImplementedError

    def void(self, identification, **kwargs):
        raise NotImplementedError

    def credit(self, money, identification, **kwargs):
        raise NotImplementedError

    def recurring(self, money, creditcard, **kwargs):
        raise NotImplementedError
        
    def store(self, creditcard, **kwargs):
        raise NotImplementedError

    def unstore(self, indentification, **kwargs):
        raise NotImplementedError

    def require(self, kwargs_hash, *args):
        for arg in args:
            assert(kwargs_hash.has_key[arg])


