#! /usr/bin/python
# ~*~ coding=utf-8 ~*~

from datetime import datetime, timedelta
from itertools import groupby
from operator import itemgetter


def convert_cost(string):
    string = float(string.replace(',', '.'))

    integer = f'{string:.2f}'

    return str(integer)


def process_payments(data):
    payments = []

    for item in data:
        # Skip withdrawals
        if item['Brutto'][:1] == '-':
            continue

        payment = {}

        try:
            payment['Datum'] = item['Datum']
            payment['Vorgang'] = 'nicht zugeordnet'
            payment['Name'] = item['Name']
            payment['Brutto']  = convert_cost(item['Brutto'])
            payment['Gebühr'] = item['Gebühr']
            payment['Netto'] = item['Netto']

            payments.append(payment)

        except AttributeError:
            pass

    payments.sort(key=lambda x: datetime.strptime(x['Datum'], '%d.%m.%Y'))

    return payments


def group_orders(data):
    groups = []

    for key, items in groupby(data, itemgetter('ID')):
        groups.append(list(items))

    orders = []

    for group in groups:
        order = group[0]
        order['Artikel'] = [part['Artikel'] for part in group]

        orders.append(order)

    return orders


def process_orders(data):
    orders = []

    for item in data:
        # TODO: Skip alternative payment methods
        if 'paymenttype' in item and item['paymenttype'] != 'PAYPAL':
            continue

        order = {}

        order['ID'] = item['ormorderid']

        date_object = datetime.strptime(item['timeplaced'][:10], '%Y-%m-%d')
        order['Datum'] = date_object.strftime('%d.%m.%Y')
        order['Name'] = ' '.join([item['rechnungaddressfirstname'], item['rechnungaddresslastname']])
        order['Betrag'] = convert_cost(item['totalordercost'])  # totalordercost = + shipping?
        order['Artikel'] = item['isbn']
        order['Straße'] = ' '.join([item['rechnungaddressstreet'], item['rechnungaddresshousenumber']])
        order['PLZ'] = item['rechnungaddresszipcode']
        order['Ort'] = item['rechnungaddresscity']
        # TODO: nan
        order['Fon'] = item['rechnungaddressphonenumber']
        order['Mail'] = item['rechnungaddressemail']

        orders.append(order)

    return group_orders(orders)


def process_invoices(invoice_data):
    invoices = []

    for item in invoice_data:
        invoice = {}

        pdf_name = item[0]
        _, reverse_date, invoice_number = pdf_name.split('-')

        date_object = datetime.strptime(reverse_date, '%Y%m%d')
        invoice['Datum'] = date_object.strftime('%d.%m.%Y')

        invoice['Vorgang'] = invoice_number[:-4]

        invoice_contents = item[1]
        invoice['Inhalt'] = invoice_contents

        # TODO: Mehrseitige PDFs!
        try:
            invoice_cost = [item[12:-4] for item in invoice_contents if item[:12] == 'Gesamtbetrag'][0]
            invoice['Betrag'] = convert_cost(invoice_cost)

        except IndexError:
            print(invoice['Vorgang'])


        start, stop = 0, 0

        for line in invoice_contents:
            if 'Bitte bei Zahlung oder Rückfragen angeben' in line:
                start = invoice_contents.index(line) + 1

            if 'Gemäß Ihrer Internetbestellung' in line:
                start = invoice_contents.index(line) + 1

            if 'Nettobetrag 7%:' in line:
                stop = invoice_contents.index(line)

        # TODO: ISBN regex, eg r'978(?:-?\d){10}'
        products = [product for product in invoice_contents[start:stop] if product != '']
        invoice['Artikel'] = products

        invoice['Datei'] = pdf_name

        invoices.append(invoice)

    return invoices
