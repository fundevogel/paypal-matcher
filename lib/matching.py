#! /usr/bin/python
# ~*~ coding=utf-8 ~*~

import sys
from datetime import datetime, timedelta
from operator import itemgetter

from lib.helpers import load_config, dedupe


# Load configuration
config = load_config('../config.yml')


def match_dates(base_date, test_date, days=3):
    date_objects = [datetime.strptime(date, '%d.%m.%Y') for date in [base_date, test_date]]
    date_range = timedelta(days=days)

    if date_objects[0] <= date_objects[1] <= date_objects[0] + date_range:
        return True

    return False


def match_payment(payment, orders):
    candidates = []

    for item in orders:
        costs_match = payment['Brutto'] == item['Betrag']
        dates_match = match_dates(payment['Datum'], item['Datum'], config['payment_order_range']) == True

        if costs_match and dates_match:
            hits = 0

            # TODO: Levenshtein
            candidates.append(tuple([hits, item]))

    matches = sorted(candidates, key=itemgetter(0), reverse=True)

    return matches[0][1]


def match_infos(order, infos):
    info = []

    for order_id, numbers in infos.items():
        if order_id == order['ID']:
            info = numbers

    return info


def match_invoices(infos, invoices):
    return [invoice for invoice in invoices for info in infos if info in invoice]
