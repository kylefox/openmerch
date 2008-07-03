import calendar

class ExpiryDate(object):
    def __init__(self, month, year):
        self.month = month
        self.year = year

    def is_expired(self):
        datetime.now() > self.expiration()

    def expiration(self):
        datestr = "%d/%d/%d 23:59:59" % (month, calendar.monthrange(year,month)[1], year)
        return datetime.strptime(datestr, "%m/%d/%Y %H:%M:%S")

