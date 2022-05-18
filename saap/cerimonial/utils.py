from datetime import date, datetime, timedelta
from calendar import Calendar, LocaleHTMLCalendar

import calendar

class Calendar(LocaleHTMLCalendar):

    eventos = None

    def __init__(self, year=None, month=None, events=None, locale='pt_BR.UTF-8'):
        self.year = year
        self.month = month
        super(Calendar, self).__init__()
        self.setfirstweekday(6)
        self.events = events

    # formats a day as a td
    # filter events by day
    def formatday(self, day, events):
        events_per_day = events.filter(inicio__day=day)
        d = ''
        for event in events_per_day:
            d += f'{event.get_html_url}<br>'

        if day != 0:
            return f"<td><span class='data'>{day}</span><br>{d}</td>"
        return '<td></td>'

    # formats a week as a tr 
    def formatweek(self, theweek, events):
        week = ''
        for d, weekday in theweek:
            week += self.formatday(d, events)
        return f'<tr> {week} </tr>'

    # formats a month as a table
    # filter events by year and month
    def formatmonth(self, withyear=True):
	
        cal = f'<table border="0" cellpadding="0" cellspacing="0" class="calendario">\n'
        cal += f'{self.formatmonthname(self.year, self.month, withyear=withyear)}\n'
        cal += f'{self.formatweekheader()}\n'
        for week in self.monthdays2calendar(self.year, self.month):
            cal += f'{self.formatweek(week, self.events)}\n'
        cal += f'</table>'
        return cal

def get_date(req_day):
    if req_day:
        year, month = (int(x) for x in req_day.split('-'))
        return date(year, month, day=1)
    return datetime.today()

def prev_month(d):
    first = d.replace(day=1)
    prev_month = first - timedelta(days=1)
    month = 'mes=' + str(prev_month.year) + '-' + str(prev_month.month)
    return month

def next_month(d):
    days_in_month = calendar.monthrange(d.year, d.month)[1]
    last = d.replace(day=days_in_month)
    next_month = last + timedelta(days=1)
    month = 'mes=' + str(next_month.year) + '-' + str(next_month.month)
    return month

def this_month():
    d= date.today()
    month = 'mes=' + str(d.year) + '-' + str(d.month)
    return month

def prev_year(d):
    prev_year = d.year - 1
    month = 'mes=' + str(prev_year) + '-' + str(d.month)
    return month

def next_year(d):
    next_year = d.year + 1
    month = 'mes=' + str(next_year) + '-' + str(d.month)
    return month

