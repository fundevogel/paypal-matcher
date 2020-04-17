#! /usr/bin/python
# ~*~ coding=utf-8 ~*~

import sys

from glob import glob
from shutil import move
from os.path import join as knot

from lib.helpers import load_config
from lib.imports import import_files, import_payments
from lib.datatypes import merge_pdf, load_csv, import_csv, dump_csv, dump_json
from lib.processing import process_payments, process_orders, process_infos
from lib.matching import match_payment, match_infos, match_invoices


if __name__ == "__main__":
    # Load configuration
    config = load_config('config.yml')

    # On '--import', import all files from config['import_dir]
    if '--import' in sys.argv:
        if import_files() == True:
            sys.exit('Import done!')
        else:
            sys.exit('Import failed!')

    # Payments
    payment_files = import_payments()
    payment_data = load_csv(payment_files)
    payments = process_payments(payment_data)

    # Orders
    order_files = glob(knot(config['order_dir'], '*.csv'))
    order_data = load_csv(order_files)
    orders = process_orders(order_data)

    # Orders
    info_files = glob(knot(config['info_dir'], '*.csv'))
    info_data = load_csv(info_files)
    infos = process_infos(info_data)

    # Invoices
    invoices = glob(knot(config['invoice_dir'], '*.pdf'))

    results = []

    for payment in payments:
        # Assign payment to matching invoice
        # (1) Find matching order for payment
        # (2) Find matching info for matching order
        # (3) Find matching invoice for matching info
        matching_order = match_payment(payment, orders)
        matching_infos = match_infos(matching_order, infos)
        matching_invoices = match_invoices(matching_infos, invoices)

        # Skip if no matching invoices
        if not matching_invoices:
            results.append(payment)
            continue

        # Store data
        # (1) Add match's information to payment data
        # (2) Save payment & match as tuple
        payment['Vorgang'] = ', '.join(matching_infos)
        payment['Datei'] = matching_invoices
        results.append(payment)

    # Generate PDF for matches by
    # (1) .. merging matched invoices
    merge_pdf(results, config['invoice_file'])

    # (2) .. removing their reference from payment data
    for result in results:
        if 'Datei' in result:
            del(result['Datei'])

    # Write JSON & CSV files
    # (1) Build base directory
    # (2) Write CSV
    # (3) Write JSON
    dump_csv(results, config['dist'])
    dump_json(results, config['dist'])
