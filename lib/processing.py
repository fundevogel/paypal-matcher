#! /usr/bin/python
# ~*~ coding=utf-8 ~*~

from datetime import datetime, timedelta
from itertools import groupby
from operator import itemgetter

from lib.helpers import dedupe


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

    payments.sort(key=lambda payment: datetime.strptime(payment['Datum'], '%d.%m.%Y'))

    return payments


def process_orders(order_data):
    orders = []

    for key, data in groupby(order_data, itemgetter('ormorderid')):
        # (1) You know what they say, `'itertools._grouper' object is not subscriptable`
        # (2) Just a silly shorthand since we don't need another loop
        item = list(data)[0]

        # TODO: Skip alternative payment methods
        if 'paymenttype' in item and item['paymenttype'] != 'PAYPAL':
            continue

        order = {}

        order['ID'] = item['ormorderid']
        date_object = datetime.strptime(item['timeplaced'][:10], '%Y-%m-%d')
        order['Datum'] = date_object.strftime('%d.%m.%Y')
        order['Name'] = ' '.join([item['rechnungaddressfirstname'], item['rechnungaddresslastname']])
        order['Betrag'] = convert_cost(item['totalordercost'])

        orders.append(order)

    return orders


def process_infos(info_data):
    infos = {}

    for key, data in groupby(info_data, itemgetter('OrmNumber')):
        numbers = [str(item['Invoice Number'])[:-2] for item in data if str(item['Invoice Number']) != 'nan']
        infos[key] = dedupe(numbers)

    return infos
