from gateways.authorizenet import AuthorizeNet
from creditcard import CreditCard
from datetime import datetime

LOGIN = ''
PASSWORD = ''

def setup_subscribe():
    interval = {
        'length': '1',
        'unit': 'months'
    }
    duration = {
        'start_date': datetime.now().strftime("%Y-%m-%d"),
        'occurrences': '2'
    }
    billing_address = {
        'first_name': 'Mal',
        'last_name': 'Reynolds'
    }

    options = {
        'interval': interval,
        'duration': duration,
        'billing_address': billing_address,
        'login': LOGIN,
        'password': PASSWORD
    }

    cc = CreditCard('4111111111111111', 6, 2010, 'visa', '', '')

    return cc, options

def setup_update():
    duration = {
        'start_date': datetime.now().strftime("%Y-%m-%d"),
        'occurrences': '3'
    }
    billing_address = {
        'first_name': 'Mal',
        'last_name': 'Reynolds'
    }

    options = {
        'duration': duration,
        'billing_address': billing_address,
        'login': LOGIN,
        'password': PASSWORD
    }

    cc = CreditCard('4111111111111111', 6, 2010, 'visa', '', '')

    return cc, options

#integration tests
def subscribe():
    cc, options = setup_subscribe()
    gateway = AuthorizeNet(options, gateway_mode='test')
    result = gateway.recurring('100', cc, **options)

    print unicode(result)
    return result['subscriptionId']

def update_subscription(sub_id=None):
    cc, options = setup_update()
    options['subscription_id'] = sub_id
    gateway = AuthorizeNet(options, gateway_mode='test')
    result = gateway.update_recurring('100', cc, **options)

    print unicode(result)

def cancel_subscription(sub_id=None):
    cc, options = setup_subscribe()
    gateway = AuthorizeNet(options, gateway_mode='test')
    result = gateway.cancel_recurring(sub_id)
    
    print unicode(result)

if __name__ == '__main__':
    sub_id = subscribe()
    update_subscription(sub_id)
    cancel_subscription(sub_id)
