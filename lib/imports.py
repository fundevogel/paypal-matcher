#! /usr/bin/python
# ~*~ coding=utf-8 ~*~

import sys

from glob import glob
from os.path import join as knot

from lib.helpers import load_config


# Load configuration
config = load_config('config.yml')


def import_files():
    # Import payment files
    payment_files_old = glob(knot(config['payment_dir'], '*.csv'))
    payment_files_new = glob(knot(config['import_dir'], 'Download*.CSV'))
    import_csv(payment_files_old + payment_files_new, 'payments')

    # Import order files
    order_files_old = glob(knot(config['order_dir'], '*.csv'))
    order_files_new = glob(knot(config['import_dir'], 'Orders_*.csv'))
    import_csv(order_files_old + order_files_new, 'orders')

    # Import info files
    info_files_old = glob(knot(config['info_dir'], '*.csv'))
    info_files_new = glob(knot(config['import_dir'], 'OrdersInfo_*.csv'))
    import_csv(info_files_old + info_files_new, 'infos')

    for pdf_file in glob(knot(config['import_dir'], '*.pdf')):
        move(pdf_file, config['invoice_dir'])

    return True


def import_payments():
    # Ask for year
    year = input('Year: ')

    if '--all' in sys.argv:
        return glob(knot(config['payment_dir'], str(year) + '-*.csv'))
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

        return [knot(config['payment_dir'], '-'.join([str(year), str(month).zfill(2) + '.csv'])) for month in months]
