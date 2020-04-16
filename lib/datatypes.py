#! /usr/bin/python
# ~*~ coding=utf-8 ~*~

import sys
import json

from os.path import join as knot
from datetime import datetime
import pandas as pd
from pandas import DataFrame, concat, read_csv
from PyPDF2 import PdfFileReader, PdfFileMerger

from lib.helpers import load_config, create_path, dedupe, group_data


# Load configuration
config = load_config('../config.yml')


def load_pdf(pdf_file):
    try:
        with open(pdf_file, 'rb') as file:
            pdf_name = file.name
            pdf_file = PdfFileReader(file)
            pdf_page = pdf_file.getPage(0)
            pdf_text = pdf_page.extractText()

        pdf_content = pdf_text.split('\n')

        # TODO: Only if PAYPAL payment (doesn't seem readable by PdfFileReader)
        pdf_data = [
            pdf_name,
            pdf_content
        ]

    except FileNotFoundError:
        print('No PDF file found: ' + pdf_file)
        sys.exit()

    return pdf_data


def merge_pdf(invoice_data, output_file):
    for identifier, data in group_data(invoice_data).items():
        pdf_files = [item['Datei'] for item in data if 'Datei' in item]
        invoice_file = knot(config['dist'], identifier, output_file)

        merger = PdfFileMerger()

        for pdf_file in pdf_files:
            with open(pdf_file, 'rb') as file:
                merger.append(PdfFileReader(file))

        create_path(invoice_file)

        merger.write(invoice_file)

    return True


def load_csv(csv_files, delimiter=',', encoding='utf-8'):
    try:
        df = concat(map(lambda file: read_csv(file, sep=delimiter, encoding=encoding), csv_files))

    except FileNotFoundError:
        return {}

    return df.to_dict('records')


def import_csv(csv_files, data_type):
    encoding = 'utf-8' if data_type == 'payments' else 'iso-8859-1'
    delimiter = ',' if data_type == 'payments' else ';'
    file_path = config['payment_dir'] if data_type == 'payments' else config['order_dir']

    if data_type == 'orders':
        encoding = 'iso-8859-1'
        delimiter = ';'
        file_path = config['order_dir']

    csv_data = dedupe(load_csv(csv_files, delimiter, encoding))

    for identifier, data in group_data(csv_data).items():
        csv_file = knot(file_path, identifier + '.csv')
        create_path(csv_file)
        _dump_csv(data, csv_file)

    return True


def _dump_csv(data, csv_file):
    DataFrame(data).to_csv(csv_file, index=False)

    return True


def dump_csv(raw, file_path):
    csv_data = dedupe(raw)

    for identifier, data in group_data(csv_data).items():
        csv_file = knot(file_path, identifier, identifier + '.csv')
        create_path(csv_file)
        _dump_csv(data, csv_file)

    return True


def dump_json(raw, file_path):
    json_data = dedupe(raw)

    for identifier, data in group_data(json_data).items():
        json_file = knot(file_path, identifier, identifier + '.json')
        create_path(json_file)

        with open(json_file, 'w') as file:
            json.dump(data, file, ensure_ascii=False, indent=4)

    return True
