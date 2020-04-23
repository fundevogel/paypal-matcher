#! /usr/bin/python
# ~*~ coding=utf-8 ~*~

from os import makedirs, path
from hashlib import md5
from datetime import datetime

from yaml import safe_load, YAMLError


def load_config(config_file):
    with open('config.yml', 'r') as file:
        try:
            config = safe_load(file)
        except YAMLError:
            pass

    return config


def create_path(file_path):
    if not path.exists(path.dirname(file_path)):
        try:
            makedirs(path.dirname(file_path))

        # Guard against race condition
        except OSError as e:
            if e.errno != errno.EEXIST:
                raise

    return True


def dedupe(duped_data, encoding='utf-8'):
    deduped_data = []
    codes = set()

    for item in duped_data:
        hash_digest = md5(str(item).encode(encoding)).hexdigest()

        if hash_digest not in codes:
            codes.add(hash_digest)
            deduped_data.append(item)

    return deduped_data


def group_data(ungrouped_data):
    grouped_data = {}

    for item in ungrouped_data:
        try:
            if 'Datum' in item:
                _, month, year = item['Datum'].split('.')
            else:
                if 'Creation Date' in item:
                    date = item['Creation Date']

                if 'timeplaced' in item:
                    date = item['timeplaced']

                year, month = str(date)[:7].split('-')

        except ValueError:
            # EOF
            pass

        code = '-'.join([str(year), str(month)])

        if code not in grouped_data.keys():
            grouped_data[code] = []

        grouped_data[code].append(item)

    return grouped_data
