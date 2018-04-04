#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil
import pathlib
import os
import argparse
import hashlib
import pprint
import requests

API_ENDPOINT = 'https://cloud-api.yandex.net/v1/disk/public/resources/{}?public_key={}'


def md5sum(filename):
    md5 = hashlib.md5()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(128 * md5.block_size), b''):
            md5.update(chunk)
    return md5.hexdigest()


def check_and_download_file(url, path, size, checksum, dry):
    if os.path.isfile(path):
        if size == os.path.getsize(path):
            if checksum == md5sum(path):
                print('skipping correctly downloaded file {}'.format(path))
                return
    if not dry:
        print('downloading {}'.format(path))
        r = requests.get(url, stream=True)
        with open(path, 'wb') as f:
            shutil.copyfileobj(r.raw, f)


def download_directory(url, save_path, dry):
    pathlib.Path(save_path).mkdir(parents=True, exist_ok=True)
    items = requests.get(API_ENDPOINT.format('', url)).json()['_embedded']['items']
    for i in items:
        # pprint.pprint(i)
        new_path = os.path.join(save_path, i['name'])
        if 'file' in i:
            check_and_download_file(i['file'], new_path, i['size'], i['md5'], dry)
        else:
            print('entering folder {}'.format(new_path))
            download_directory(i['public_url'], new_path, dry)


parser = argparse.ArgumentParser(description='Yandex.Disk downloader.')
parser.add_argument('url')
parser.add_argument('-o', dest='output_path', default='output')
parser.add_argument('--dry', action='store_const', const=True, default=False)
args = parser.parse_args()

download_directory(args.url, args.output_path, args.dry)
