#! /usr/bin/python
# ~*~ coding=utf-8 ~*~

import os
import csv
import sys
import json

from glob import glob
from datetime import datetime
from shutil import copy, move

from PyPDF2 import PdfFileReader


def init():
    # PDF files
    for pdf_file in glob('new/*.pdf'):
        basename = os.path.basename(pdf_file)
        date_string = basename.split('-')[1]
        year = date_string[0:4]
        month = date_string[4:6]
        destination = 'src/' + year + '/' + month + '/' + basename

        create_path(destination)
        move(pdf_file, destination)

    # CSV files
    categories = {}

    for year in range(2010, 2030):
        year = str(year)
        categories[year] = {}

        for month in range(0, 13):
            month = str(month)

            # Add leading zero
            if int(month) < 10:
                month = '0' + month

            categories[year][month] = []

    csv_input = 'Download.CSV'

    try:
        with open(csv_input, 'r') as file:
            payment_data = csv.DictReader(file)

            for item in payment_data:
                date = list(item.items())[0][1]
                date_list = date.split('.')

                payment_year = date_list[2]
                payment_month = date_list[1]
                categories[payment_year][payment_month].append(item)

        for year, months in categories.items():
            for month, data in months.items():

                if len(data):
                    csv_file = 'src/' + year + '/' + month + '/payments.csv'
                    create_path(csv_file)

                    keys, values = [], []
                    for key, value in data[0].items():
                        keys.append(key)
                        values.append(value)

                    with open(csv_file, 'w') as file:
                        csvwriter = csv.writer(file)
                        csvwriter.writerow(keys)
                        csvwriter.writerow(values)

    except FileNotFoundError as e:
        print('No CSV file found: ' + csv_file)
        sys.exit()

    os.remove(csv_input)


def collect_pdf_data(pdf_files):
    pdf_data = {}

    for pdf_file in pdf_files:
        with open(pdf_file, 'rb') as file:
            pdf_name = os.path.basename(file.name)
            pdf_file = PdfFileReader(file)
            pdf_page = pdf_file.getPage(0)
            pdf_text = pdf_page.extractText()

        pdf_content = pdf_text.split('\n')
        pdf_data[pdf_name] = pdf_content

    return pdf_data


def create_path(file_path):
    if not os.path.exists(os.path.dirname(file_path)):
        try:
            os.makedirs(os.path.dirname(file_path))

        # Guard against race condition
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise


def print_csv(data, file):
    csv_file = csv.writer(file, quoting=csv.QUOTE_NONNUMERIC)

    csv_file.writerow(data[0].keys())

    for item in data:
        csv_file.writerow(item.values())


def write_data(data):
    # Write JSON
    with open(dist + 'paid.json', 'w') as file:
        json.dump(data, file, ensure_ascii=False, indent=4)

    # Print CSV
    with open(dist + 'paid.csv', 'w') as file:
        print_csv(data, file)

if __name__ == "__main__":
    if '--setup' in sys.argv:
        init()
        sys.exit()

    # Declare variables
    year = input('Year: ')
    month = input('Month: ')

    src = 'src/' + year + '/' + month + '/'
    dist = 'dist/' + year + '/' + month + '/'


    # Load payment CSV
    csv_file = src + 'payments.csv'

    try:
        with open(csv_file, 'r') as file:
            paypal_data = list(csv.DictReader(file))

    except FileNotFoundError as e:
        print('No CSV file found: ' + csv_file)
        sys.exit()

    # Create PDF data
    pdf_files = glob(src + '*.pdf')
    pdf_data = collect_pdf_data(pdf_files)


    # Rock 'n' roll
    report = []
    json_data = []

    for item in paypal_data:
        paypal_date = list(item.items())[0][1]
        paypal_name = item['Name']
        paypal_before_tax = item['Brutto']
        paypal_fee = item[u'Gebühr']
        paypal_after_tax = item['Netto']

        # Skip withdrawals
        if paypal_before_tax[:1] == '-':
            continue

        matches = []

        for pdf_name, pdf_content in pdf_data.items():
            date_string = pdf_name.split('-')[1]
            date_object = datetime.strptime(date_string, '%Y%m%d')

            invoice_date = date_object.strftime('%d.%m.%Y')
            invoice_price = [item[12:-4] for item in pdf_content if item[:12] == 'Gesamtbetrag'][0]

            case_number = pdf_name[:-4].split('-')[2]
            output_name = date_object.strftime('%Y-%m-%d') + '_' + case_number + '.pdf'

            hits = 0

            if invoice_date == paypal_date:
                hits += 1

            if invoice_price == paypal_before_tax:
                hits += 1

            for line in pdf_content:
                if paypal_name.lower() == line.lower():
                    hits += 1

            if hits >= 2:
                match = {}

                match['Vorgang'] = case_number
                match['Datum'] = paypal_date
                match['Name'] = paypal_name
                match['Brutto'] = paypal_before_tax
                match['Gebühr'] = paypal_fee
                match['Netto'] = paypal_after_tax

                match['metadata'] = tuple([hits, pdf_name, output_name])

                matches.append(match)

        # If more than one match, only keep highest scoring ones
        if len(matches) > 1:
            matches = [match for match in matches if match['metadata'][0] == 3]

        # Create directory if it doesn't exist
        create_path(dist)

        # Coppy invoices for all matches
        for match in matches:
            _, pdf_name, output_name = match['metadata']
            copy(src + pdf_name, dist + output_name)
            del match['metadata']

            json_data.append(match)

        # Generate report
        if len(matches) > 0:
            report.append(str(len(matches)) + ' Treffer für ' + paypal_name + ' vom ' + paypal_date)
        else:
            report.append('Kein Treffer für ' + paypal_name + ' vom ' + paypal_date)


    # Write report
    with open(dist + 'report.txt', 'w') as file:
        for item in sorted(report):
            file.write("%s\n" % item)


    # Write payment data
    if len(json_data) > 0:
        write_data(json_data)
