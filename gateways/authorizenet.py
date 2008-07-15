from base import Gateway
from StringIO import StringIO
import xml.etree.ElementTree as ET

from post import post

class AuthorizeNet(Gateway):
    API_VERSION = '3.1'

    APPROVED, DECLINED, ERROR, FRAUD_REVIEW = 1, 2, 3, 4
    RESPONSE_CODE, RESPONSE_REASON_CODE, RESPONSE_REASON_TEXT = 0, 2, 3
    AVS_RESULT_CODE, TRANSACTION_ID, CARD_CODE_RESPONSE_CODE = 5, 6, 38
    RECURRING_ACTIONS = {
      u'create': 'ARBCreateSubscription',
      u'update': 'ARBUpdateSubscription',
      u'cancel': 'ARBCancelSubscription'
    }
    test_url = "https://test.authorize.net/gateway/transact.dll"
    live_url = "https://secure.authorize.net/gateway/transact.dll"
 
    arb_test_url = 'https://apitest.authorize.net/xml/v1/request.api'
    arb_live_url = 'https://api.authorize.net/xml/v1/request.api'

    supported_countries = ['US']
    supported_cardtypes = ['visa', 'master', 'american_express', 'discover']
    homepage_url = 'http://www.authorize.net/'
    display_name = u'Authorize.Net'
 
    CARD_CODE_ERRORS = ('N', 'S')
    AVS_ERRORS = ('A', 'E', 'N', 'R', 'W', 'Z')
 
    AUTHORIZE_NET_ARB_NAMESPACE = 'AnetApi/xml/v1/schema/AnetApiSchema.xsd'

    def __init__(self, options, gateway_mode='live'):
        assert(options.has_key('login'))
        assert(options.has_key('password'))
        self.options = options
        super(AuthorizeNet, self).__init__(gateway_mode=gateway_mode)

    def recurring(self, money, creditcard, **kwargs):
        assert(kwargs.has_key('interval') and
               kwargs.has_key('duration') and
               kwargs.has_key('billing_address'))
        assert(kwargs['interval'].has_key('length') and
               kwargs['interval'].has_key('unit'))
        assert(kwargs['interval']['unit'] == 'days' or 
               kwargs['interval']['unit'] == 'months')
        assert(kwargs['duration'].has_key('start_date') or
               kwargs['duration'].has_key('occurrences'))
        assert(kwargs['billing_address'].has_key('first_name') or
               kwargs['billing_address'].has_key('last_name'))

        #Create a copy of kwargs and call it options. This is not 
        #intended to be self.options. ARB has different options
        #than the standard Authorize.Net payment gateway
        options = kwargs.copy()
        options['credit_card'] = creditcard
        options['amount'] = money

        request = self.build_recurring_request(u'create', options)
        return self.recurring_commit(u'create', request)

    def update_recurring(self, money, creditcard, **kwargs):
        assert(kwargs.has_key('subscription_id'))

        #Create a copy of kwargs and call it options. This is not 
        #intended to be self.options. ARB has different options
        #than the standard Authorize.Net payment gateway
        options = kwargs.copy()
        options['credit_card'] = creditcard
        options['amount'] = money

        request = self.build_recurring_request(u'update', options)
        return self.recurring_commit(u'update', request)

    def cancel_recurring(self, subscription_id):
        request = self.build_recurring_request('cancel', {'subscription_id': subscription_id})
        return self.recurring_commit(u'cancel', request)
        
        
    def build_recurring_request(self, action, options):
        if not self.RECURRING_ACTIONS.has_key(action):
            raise StandardError, u"Invalid Automated Recurring Billing Action: " + unicode(action)

        requestbuff = StringIO()

        requestbuff.write('<?xml version="1.0" encoding="utf-8"?>')
        root = ET.Element(self.RECURRING_ACTIONS[action] + 'Request',
                          attrib={'xmlns': self.AUTHORIZE_NET_ARB_NAMESPACE})
        self.add_arb_merchant_authentication(root)
        if options.has_key('ref_id'):
            refId = ET.SubElement(root, 'refId')
            refId.text = options['ref_id']
        {'create': self.build_arb_create_subscription_request,
         'update': self.build_arb_update_subscription_request,
         'cancel': self.build_arb_cancel_subscription_request
        }[action](root, options)

        tree = ET.ElementTree(root)
        tree.write(requestbuff)
        
        return requestbuff.getvalue()

    def add_se(self, node, name, text):
        subnode = ET.SubElement(node, name)
        subnode.text = text
        return subnode

    def add_arb_merchant_authentication(self, root):
        merch_auth = ET.SubElement(root, 'merchantAuthentication')
        self.add_se(merch_auth, 'name', self.options['login'])
        self.add_se(merch_auth, 'transactionKey', self.options['password'])

    def build_arb_create_subscription_request(self, root, options):
        self.add_arb_subscription(root, options)
    
    def build_arb_update_subscription_request(self, root, options):
        subscription_id = self.add_se(root, 'subscriptionId', options['subscription_id'])
        self.add_arb_subscription(root, options)

    def build_arb_cancel_subscription_request(self, root, options):
        self.add_se(root, 'subscriptionId', options['subscription_id'])

    def add_arb_subscription(self, root, options):
        subscription = ET.SubElement(root, 'subscription')
        if options.has_key('subscription_name'):
            self.add_se(subscription, 'name', options['subscription_name'])
        self.add_arb_payment_schedule(subscription, options)
        if options.has_key('amount'):
            self.add_se(subscription, 'amount', self.amount(options['amount']))
        if options.setdefault('trial', None) and options['trial'].setdefault('amount', 0):
            self.add_se(subscription, 'trailAmount', options['trial']['amount'])
        self.add_arb_payment(subscription, options)
        self.add_arb_order(subscription, options)
        self.add_arb_customer(subscription, options)
        self.add_arb_address(subscription, 'billTo', options['billing_address'])
        if 'shipping_address' in options.keys():
            self.add_arb_address(subscription, 'shipTo', options['shipping_address'])

    def add_arb_interval(self, payment_schedule, options):
        if not 'interval' in options.keys() or not options['interval']:
            return
        interval = ET.SubElement(payment_schedule, 'interval')
        self.add_se(interval, 'length', options['interval']['length'])
        self.add_se(interval, 'unit', options['interval']['unit'])

    def add_arb_duration(self, payment_schedule, options):
        if not 'duration' in options.keys() or not options['duration']:
            return
        self.add_se(payment_schedule, 'startDate', options['duration']['start_date'])
        self.add_se(payment_schedule, 'totalOccurrences', options['duration']['occurrences'])
            
    def add_arb_payment_schedule(self, subscription, options):
        if 'interval' in options.keys() or 'duration' in options.keys():
            payment_schedule = ET.SubElement(subscription, 'paymentSchedule')
            self.add_arb_interval(payment_schedule, options)
            self.add_arb_duration(payment_schedule, options)
            if 'trial' in options.keys() and options['trial']:
                self.add_se(payment_schedule, 'trialOccurrences', options['trial']['occurrences'])

    def add_arb_payment(self, subscription, options):
        #if not 'credit_card' in options.keys() or 'bank_account' in options.keys():
        #    return
        payment = ET.SubElement(subscription, 'payment')
        self.add_arb_credit_card(payment, options)
        self.add_arb_bank_account(payment, options)

    def add_arb_credit_card(self, payment, options):
        if not 'credit_card' in options.keys() or not options['credit_card']:
            return
        credit_card = ET.SubElement(payment, 'creditCard')
        self.add_se(credit_card, 'cardNumber', options['credit_card'].number)
        self.add_se(credit_card, 'expirationDate', self.arb_expdate(options['credit_card']))

    def add_arb_bank_account(self, payment, options):
        if not 'bank_account' in options.keys() or not options['bank_account']:
            return
        bank_account = ET.SubElement(payment, 'bankAccount')
        self.add_se(bank_account, 'accountType', options['bank_account']['account_type'])
        self.add_se(bank_account, 'routingNumber', options['bank_account']['routing_number'])
        self.add_se(bank_account, 'accountNumber', options['bank_account']['account_number'])
        self.add_se(bank_account, 'nameOfAccount', options['bank_account']['name_of_account'])
        if 'bank_name' in options['bank_account'].keys():
            self.add_se(bank_account, 'bankName', options['bank_account']['bank_name'])
        self.add_se(bank_account, 'echeckType', options['bank_account']['echeck_type'])

    def add_arb_order(self, root, options):
        if not 'order' in options.keys() or not options['order']:
            return
        order = ET.SubElement(root, 'order')
        self.add_se(order, 'invoiceNumber', options['order']['invoice_number'])
        self.add_se(order, 'description', options['order']['description'])

    def add_arb_customer(self, root, options):
        if not 'customer' in options.keys() or not options['customer']:
            return
        customer = ET.SubElement(root, 'customer')
        if 'type' in options['customer'].keys():
            self.add_se(customer, 'type', options['customer']['type'])
        if 'id' in options['customer'].keys():
            self.add_se(customer, 'id', options['customer']['id'])
        if 'email' in options['customer'].keys():
            self.add_se(customer, 'email', options['customer']['email'])
        if 'phone_number' in options['customer'].keys():
            self.add_se(customer, 'phoneNumber', options['customer']['phone_number'])
        if 'fax_number' in options['customer'].keys():
            self.add_se(customer, 'faxNumber', options['customer']['fax_number'])
        self.add_arb_drivers_license(customer, options)
        if 'tax_id' in options['customer'].keys():
            self.add_se(customer, 'taxId', options['customer']['tax_id'])

    def add_arb_drivers_license(self, customer, options):
        if not 'customer' in options.keys() or not options['customer']:
            return
        if not 'drivers_license' in options['customer'].keys() or not options['customer']['drivers_license']:
            return
        drivers_license = ET.SubElement(customer, 'driversLicense')
        self.add_se(drivers_license, 'number', options['drivers_license']['number'])
        self.add_se(drivers_license, 'state', options['drivers_license']['state'])
        self.add_se(drivers_license, 'dateOfBirth', options['drivers_license']['date_of_birth'])

    def add_arb_address(self, root, container_name, address):
        if not address.keys():
            return
        container = ET.SubElement(root, container_name)
        self.add_se(container, 'firstName', address['first_name'])
        self.add_se(container, 'lastName', address['last_name'])

        if 'company' in address.keys():
            self.add_se(container, 'company', address['company'])
        if 'address1' in address.keys():
            self.add_se(container, 'address', address['address1'])
        if 'city' in address.keys():
            self.add_se(container, 'city', address['city'])
        if 'state' in address.keys():
            self.add_se(container, 'state', address['state'])
        if 'zip' in address.keys():
            self.add_se(container, 'zip', address['zip'])
        if 'country' in address.keys():
            self.add_se(container, 'country', address['country'])

    def arb_expdate(self, credit_card):
        return "%04d-%02d" % (credit_card.year, credit_card.month)

    def recurring_commit(self, action, request):
        if self.is_test():
            url = self.arb_test_url
        else:
            url = self.arb_live_url
        xml = post(url, request, {"Content-Type": "text/xml"})
        print 'RESPONSE: ', xml
        response = self.recurring_parse('create', xml.decode('utf-8-sig'))
        return response

    def normalize(self, name):
        if name[0] == "{":
            uri, tag = name[1:].split("}")
            return tag
        else:
            return name

    def recurring_parse(self, action, xml):
        response = {}
        xml = ET.parse(StringIO(xml))
        root = xml.getroot()
        root_tag = self.normalize(root.tag)
        print "ROOT TAG: ", self.normalize(root_tag)

        if root_tag == "%sResponse"%(self.RECURRING_ACTIONS[action]) or root_tag == "ErrorResponse":
            response[root_tag] = True
            for child in root.getchildren():
                self.recurring_parse_element(response, child)
        return response

    def recurring_parse_element(self, response, node):
        if node.getchildren():
            for child in node.getchildren():
                self.recurring_parse_element(response, child)
        else:
            response[self.normalize(node.tag)] = node.text
