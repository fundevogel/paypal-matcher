#! /usr/bin/python
# ~*~ coding=utf-8 ~*~

import sys

from glob import glob
from shutil import move
from os.path import join as knot

from lib.helpers import load_config
from lib.datatypes import load_pdf, merge_pdf, load_csv, import_csv, dump_csv, dump_json
from lib.processing import process_payments, process_orders, process_invoices
from lib.matching import match_payment, match_invoices, extract_best_match


if __name__ == "__main__":
    # Load configuration
    config = load_config('config.yml')

    if '--import' in sys.argv:
        # Import payments
        # payment_files = glob(knot(config['import_dir'], 'Download*.CSV')) + glob(knot(config['payment_dir'], '*.csv'))
        # import_csv(payment_files, 'payments')

        # # Import orders
        order_files = glob(knot(config['import_dir'], 'Orders*.csv')) + glob(knot(config['order_dir'], '*.csv'))
        import_csv(order_files, 'orders')

        for pdf_file in glob(knot(config['import_dir'], '*.pdf')):
            move(pdf_file, config['invoice_dir'])

        # Close
        sys.exit('Import done!')

    # Ask for year
    year = input('Year: ')

    if '--all' in sys.argv:
        payment_files = glob(knot(config['payment_dir'], str(year) + '-*.csv'))
    else:
        quarter = None

        while quarter == None:
            try:
                answer = input('Quarter (1-4): ')

                if 1 <= int(answer) <= 4:
                    quarter = int(answer)
                else:
                    print('Quarter must be between 1 and 4.')

            except ValueError:
                print('Quarter must be an integer,', str(answer) + ' given.')

        # Compute months for given quarter
        months = [month + 3 * (quarter - 1) for month in [1, 2, 3]]

        # Show time
        payment_files = [knot(config['payment_dir'], '-'.join([str(year), str(month).zfill(2) + '.csv'])) for month in months]

    # Payments
    payment_data = load_csv(payment_files)
    payments = process_payments(payment_data)

    # # Orders
    order_files = glob(knot(config['order_dir'], '*.csv'))
    order_data = load_csv(order_files)
    orders = process_orders(order_data)

    # # Invoices
    invoice_data = [load_pdf(file) for file in glob(knot(config['invoice_dir'], '*.pdf'))]
    invoices = process_invoices(invoice_data)

    results = []

    for payment in payments:
        # Assign payment
        # (1) Match each payment with orders
        # (2) Match each payment with invoices
        # (3) Assign invoice to each order
        matching_orders = match_payment(payment, orders)
        matching_invoices = match_payment(payment, invoices)
        candidates = match_invoices(payment, matching_orders, matching_invoices, config['order_invoice_range'], config['payment_invoice_range'])

        # Skip if no results
        if not candidates:
            results.append(payment)
            continue

        # Extract best match by ..
        # (1) .. removing duplicates
        # (2) .. sorting by number of hits
        # (3) .. choosing the first tuple's item
        match = extract_best_match(candidates)

        # Store data
        # (1) Add match's information to payment data
        # (2) Save payment & match as tuple
        payment['Vorgang'] = match['Vorgang']
        payment['Datei'] = match['Datei']
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
