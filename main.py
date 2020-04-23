#! /usr/bin/python
# ~*~ coding=utf-8 ~*~

import os
import sys
from glob import glob

from knv_pypal import match_data

from lib.utils import load_config
from lib.data import load_data, import_csv, export_csv, import_pdf, export_pdf


if __name__ == "__main__":
    # Load configuration
    config = load_config('config.yml')

    # On '--import', import all files from config['import_dir]
    if '--import' in sys.argv:
        # Import payment files
        payment_files_old = glob(os.path.join(config['payment_dir'], '*.json'))
        payment_files_new = glob(os.path.join(config['import_dir'], 'Download*.CSV'))
        import_csv(payment_files_old, payment_files_new, 'payment')

        # Import order files
        order_files_old = glob(os.path.join(config['order_dir'], '*.json'))
        order_files_new = glob(os.path.join(config['import_dir'], 'Orders_*.csv'))
        import_csv(order_files_old, order_files_new, 'order')

        # Import info files
        info_files_old = glob(os.path.join(config['info_dir'], '*.json'))
        info_files_new = glob(os.path.join(config['import_dir'], 'OrdersInfo_*.csv'))
        import_csv(info_files_old, info_files_new, 'info')

        # Import PDF files
        import_pdf(glob(os.path.join(config['import_dir'], '*.pdf')))

        sys.exit('Import done!')

    # Load CSV data
    # (1) Single sources
    # (2) Matched sources
    payments, orders, infos = load_data()
    matches = match_data(payments, orders, infos)

    # Assign invoices
    invoices = glob(os.path.join(config['invoice_dir'], '*.pdf'))

    # Merge matched invoices
    export_pdf(matches, invoices)

    # Write CSV files
    export_csv(matches, config['dist'])
