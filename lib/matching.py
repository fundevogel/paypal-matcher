#! /usr/bin/python
# ~*~ coding=utf-8 ~*~

import sys
from datetime import datetime, timedelta
from operator import itemgetter

from lib.helpers import dedupe


def match_dates(base_date, test_date, days=3):
    date_objects = [datetime.strptime(date, '%d.%m.%Y') for date in [base_date, test_date]]
    date_range = timedelta(days=days)

    if date_objects[0] <= date_objects[1] <= date_objects[0] + date_range:
        return True

    return False


def match_payment(payment, data):
    matching_data = [item for item in data if item['Betrag'] == payment['Brutto']]

    if not matching_data:
        matching_data = []

    return matching_data


def match_invoices(payment, orders, invoices, order_invoice_range=3, payment_invoice_range=14):
    # Since payments, orders & invoices only share the total cost,
    # we have to match orders & invoices separately
    candidates = []

    for order in orders:
        for invoice in invoices:
            # Only ever compare orders & invoices if their dates are within range
            if match_dates(order['Datum'], invoice['Datum'], order_invoice_range) == True:
                hits = 0

                # Compare payment & invoice date
                if match_dates(payment['Datum'], order['Datum'], payment_invoice_range) == True:
                    hits += 1

                # Compare payment name & order name
                for line in invoice['Inhalt']:
                    # TODO: Levenshtein comparison
                    if order['Name'].lower() == line.lower():
                        hits += 1

                # Compare number of ordered items
                if len(order['Artikel']) == len(invoice['Artikel']):
                        hits += 1

                # Compare ordered items themselves
                product_hits = 0

                for product in order['Artikel']:
                    if str(product) in ' '.join(invoice['Artikel']):
                        product_hits += 1

                if product_hits == len(order['Artikel']):
                    hits += 1

                # Set threshold
                candidates.append(tuple([hits, invoice]))

    return candidates


def extract_best_match(candidates):
    matches = sorted(dedupe(candidates), key=itemgetter(0), reverse=True)

    return matches[0][1]
