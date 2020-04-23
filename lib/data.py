#! /usr/bin/python
# ~*~ coding=utf-8 ~*~

import os
import json
from glob import glob
from shutil import move
from sys import argv as cli_args

from pandas import DataFrame, concat, read_csv
from PyPDF2 import PdfFileReader, PdfFileMerger

from lib.utils import load_config, create_path, dedupe, group_data


# Load configuration
config = load_config('../config.yml')


# Load data

def load_data():
    # Ask for year
    year = input('Year: ')

    # Mode: per year or per quarter
    if '--all' in cli_args:
        payment_files = glob(os.path.join(config['payment_dir'], str(year) + '-*.csv'))
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

        payment_files = [os.path.join(config['payment_dir'], '-'.join([str(year), str(month).zfill(2) + '.json'])) for month in months]

    # Generating ..
    # (1) .. payment data
    payment_data = load_json(payment_files)
    # (2) .. order data
    order_files = glob(os.path.join(config['order_dir'], '*.json'))
    order_data = load_json(order_files)
    # (3) .. info data
    info_files = glob(os.path.join(config['info_dir'], '*.json'))
    info_data = load_json(info_files)

    return (payment_data, order_data, info_data)


# JSON tasks

def load_json(json_files):
    data = []

    for json_file in json_files:
        try:
            with open(json_file, 'r') as file:
                data.extend(json.load(file))

        except FileNotFoundError:
            pass

    return data


def dump_json(data, json_file):
    with open(json_file, 'w') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)


# CSV tasks

def load_csv(csv_files, data_type):
    delimiter = ';'
    encoding = 'iso-8859-1'

    if data_type == 'payment':
        delimiter = ','
        encoding = 'utf-8'

    try:
        df = concat(map(lambda file: read_csv(file, sep=delimiter, encoding=encoding, low_memory=False), csv_files))

    except FileNotFoundError:
        return {}

    return df.to_dict('records')


def import_csv(json_files, csv_files, data_type):
    base_dir = config[data_type + '_dir']

    json_data = load_json(json_files)
    csv_data = load_csv(csv_files, data_type)

    for code, data in group_data(json_data + csv_data).items():
        dump_json(data, os.path.join(base_dir, code + '.json'))

    return True


def export_csv(raw, base_dir):
    csv_data = dedupe(raw)

    for code, data in group_data(csv_data).items():
        csv_file = os.path.join(base_dir, code, code + '.csv')
        create_path(csv_file)

        DataFrame(data).to_csv(csv_file, index=False)

    return True


# PDF tasks

def import_pdf(pdf_files):
    for pdf_file in pdf_files:
        move(pdf_file, config['invoice_dir'])


def export_pdf(matches, invoice_list):
    # Prepare invoice data
    invoices = {os.path.basename(invoice).split('-')[2][:-4]: invoice for invoice in invoice_list}

    for code, data in group_data(matches).items():
        # Extract matching invoice numbers
        invoice_numbers = []

        for item in data:
            if item['Vorgang'] != 'nicht zugeordnet':
                if ';' in item['Vorgang']:
                    invoice_numbers += [number for number in item['Vorgang'].split(';')]
                else:
                    invoice_numbers.append(item['Vorgang'])

        # Init merger object
        merger = PdfFileMerger()

        # Merge corresponding invoices
        for number in dedupe(invoice_numbers):
            if number in invoices:
                pdf_file = invoices[number]

                with open(pdf_file, 'rb') as file:
                    merger.append(PdfFileReader(file))

        # Write merged PDF to disk
        invoice_file = os.path.join(config['dist'], code, config['invoice_file'])
        create_path(invoice_file)
        merger.write(invoice_file)

    return True
