from datetime import date, datetime, timedelta
from calendar import Calendar, LocaleHTMLCalendar
from pytz import timezone as pytz_timezone
from django.db.models import Q

import calendar

class Calendar(LocaleHTMLCalendar):

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

class CalendarAgenda(Calendar):

    def __init__(self, year=None, month=None, events=None, locale='pt_BR.UTF-8'):
        self.year = year
        self.month = month
        super(Calendar, self).__init__()
        self.setfirstweekday(6)
        self.events = events

    # formats a day as a td
    # filter events by day
    def formatday(self, day, events):

        hoje = date.today()

        if(self.year < hoje.year):
            estilo_passado = 'passado'
        elif(self.year == hoje.year and self.month < hoje.month):
            estilo_passado = 'passado'
        elif(self.year == hoje.year and self.month == hoje.month and day < hoje.day):
            estilo_passado = 'passado'
        else:
            estilo_passado = ''
   
        if(hoje.day == day and hoje.month == self.month and hoje.year == self.year):
            estilo_hoje = 'hoje'
        else:
            estilo_hoje = ''

        events_per_day = events.filter(inicio__day=day)
        d = ''
        for event in events_per_day:

            inicio_concomitante = events.filter(inicio__lte=event.inicio, termino__gte=event.inicio)
            inicio_concomitante = inicio_concomitante.filter(~Q(pk=event.pk))

            termino_concomitante = events.filter(inicio__lte=event.termino, termino__gte=event.termino)
            termino_concomitante = termino_concomitante.filter(~Q(pk=event.pk))       

            concomitante = ''
            if (inicio_concomitante.count() > 0 or termino_concomitante.count() > 0):
                concomitante = 'evento-concomitante'

            url = "/eventos/" + str(event.pk)
            fmt = "%d/%m/%Y às %H:%M"
            event.inicio = event.inicio.astimezone(pytz_timezone('America/Sao_Paulo'))
            event.termino = event.termino.astimezone(pytz_timezone('America/Sao_Paulo'))

            longo = ''
            qtde_dias = 0
            if (event.termino.day != event.inicio.day):
                longo = 'evento-longo' 
                qtde_dias = (event.termino.day - event.inicio.day) 
    
            if(event.bairro != None):
                str_bairro = event.bairro.nome
            else:
                str_bairro = ''
    
            if(event.municipio != None):
                str_municipio = event.municipio.nome
            else:
                str_municipio = ''
    
            text = "Descrição: " + event.descricao + "\n\n" + \
                   "Local: " + event.localizacao + "\n" + \
                   "Bairro: " + str_bairro + "\n" + \
                   "Município: " + str_municipio + "\n\n" + \
                   "Início: " + event.inicio.strftime(fmt) + "\n" + \
                   "Término: " + event.termino.strftime(fmt) 
            hora_inicio = event.inicio.strftime("%H:%M")
            hora_termino = event.termino.strftime("%H:%M")

            dias_duracao = ""
            if(qtde_dias > 0):
                dias_duracao = "(+" + str(qtde_dias) + ")"

            evento_formatado = f'&nbsp;<span class="{concomitante}"><b>{hora_inicio}-{hora_termino}</b></span><span class="{longo}"><b>{dias_duracao}</b></span>&nbsp;<a href="{url}" title="{text}">{event.titulo}</a>'
            d += f'{evento_formatado}<br>'

        if day != 0:
            return f"<td class='{estilo_hoje} {estilo_passado}'><span class='data'>{day}</span><br>{d}</td>"
        return '<td></td>'

class CalendarAniversarios(Calendar):

    def __init__(self, year=None, month=None, birthdays=None, locale='pt_BR.UTF-8'):
        self.year = year
        self.month = month
        super(Calendar, self).__init__()
        self.setfirstweekday(6)
        self.events = birthdays

    # formats a day as a td
    # filter birthdays by day
    def formatday(self, day, events):

        hoje = date.today()

        if(self.year < hoje.year):
            estilo_passado = 'passado'
        elif(self.year == hoje.year and self.month < hoje.month):
            estilo_passado = 'passado'
        elif(self.year == hoje.year and self.month == hoje.month and day < hoje.day):
            estilo_passado = 'passado'
        else:
            estilo_passado = ''
   
        if(hoje.day == day and hoje.month == self.month and hoje.year == self.year):
            estilo_hoje = 'hoje'
        else:
            estilo_hoje = ''

        #birthdays_per_day = events.filter(data_nascimento__day=day)
        d = ''
        for birthday in events: 
            if(birthday.data_nascimento != None):
                if(birthday.data_nascimento.day == day):
                    url = "/contatos/" + str(birthday.pk)
                    idade = self.year - birthday.data_nascimento.year
        
                    nascimento = str(birthday.data_nascimento.strftime("%d/%m/%Y")) 
         
                    enderecos = birthday.endereco_set.all()
                    endereco_texto = ''
                    municipio_texto = ''
                    for endereco in enderecos:
                        if(endereco.permite_contato == True):
                            endereco_texto = endereco.endereco
                            if(endereco.numero == None):
                                endereco_texto += ", S/N"
                            else: 
                                if(endereco.numero > 0):
                                    endereco_texto += ", " + str(endereco.numero)
                                else:
                                    endereco_texto += ", S/N"
                            
                            if(endereco.complemento != '' and endereco.complemento != None):
                                endereco_texto += " - " + endereco.complemento
                  
                            endereco_texto += ' - %s' % endereco.bairro.nome if endereco.bairro else ''
                           
                            municipio_texto = '%s/%s' % (endereco.municipio.nome, endereco.estado.sigla)
                            
                            break
                
                    telefones = birthday.telefone_set.all()
                    telefone_texto = ''
                    for telefone in telefones:
                        if(telefone.permite_contato == True):
                            telefone_texto += telefone.telefone
                            break
 
                    emails = birthday.email_set.all()
                    email_texto = ''
                    for email in emails:
                        if(email.permite_contato == True):
                            email_texto += email.email
                            break
        
                    text = "Nome: " + birthday.nome + "\n" \
                           "Data de nascimento: " + nascimento + "\n\n" \
                           "Endereço: " + endereco_texto + "\n" \
                           "Município: " + municipio_texto + "\n\n" \
                           "Telefone: " + telefone_texto + "\n\n" \
                           "E-mail: " + email_texto
        
                    birthday_formatted = f'&nbsp;<b>{idade}</b> - <a href="{url}" title="{text}">{birthday.nome}</a>'
                    d += f'{birthday_formatted}<br>'
        
        if day != 0:
            return f"<td class='{estilo_hoje} {estilo_passado}'><span class='data'>{day}</span><br>{d}</td>"
        return '<td></td>'


def get_date(req_day):
    if req_day:
        year, month = (int(x) for x in req_day.split('-'))
        return date(year, month, day=1)
    return date.today()

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

