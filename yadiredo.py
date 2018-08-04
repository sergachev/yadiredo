#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil
import pathlib
import os
import argparse
import hashlib
import requests
from logzero import logger as log


API_ENDPOINT = 'https://cloud-api.yandex.net/v1/disk/public/resources/?public_key={}&path=/{}&offset={}'
dry = False


def md5sum(file_path):
    md5 = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(128 * md5.block_size), b''):
            md5.update(chunk)
    return md5.hexdigest()


def check_and_download_file(target_path, url, size, checksum):
    if os.path.isfile(target_path):
        if size == os.path.getsize(target_path):
            if checksum == md5sum(target_path):
                log.info('skipping correct {}'.format(target_path))
                return
    if not dry:
        log.info('downloading {}'.format(target_path))
        r = requests.get(url, stream=True)
        with open(target_path, 'wb') as f:
            shutil.copyfileobj(r.raw, f)


def download_path(target_path, public_key, source_path, offset=0):
    log.info('getting "{}" at offset {}'.format(source_path, offset))
    current_path = os.path.join(target_path, source_path)
    pathlib.Path(current_path).mkdir(parents=True, exist_ok=True)
    jsn = requests.get(API_ENDPOINT.format(public_key, source_path, offset)).json()

    def try_as_file(j):
        if 'file' in j:
            file_save_path = os.path.join(current_path, j['name'])
            check_and_download_file(file_save_path, j['file'], j['size'], j['md5'])
            return True
        return False

    # first try to treat the actual json as a single file description
    if try_as_file(jsn):
        return

    # otherwise treat it as a directory
    emb = jsn['_embedded']
    items = emb['items']
    for i in items:
        # each item can be a file...
        if try_as_file(i):
            continue
        # ... or a directory
        else:
            subdir_path = os.path.join(source_path, i['name'])
            download_path(target_path, public_key, subdir_path)

    # check if current directory has more items
    last = offset + emb['limit']
    if last < emb['total']:
        download_path(target_path, public_key, source_path, last)


parser = argparse.ArgumentParser(description='Yandex.Disk downloader.')
parser.add_argument('url')
parser.add_argument('-o', dest='output_path', default='output')
parser.add_argument('--dry', action='store_const', const=True, default=False)
parser.add_argument('-r', dest='retries', default=None)
args = parser.parse_args()
dry = args.dry
if args.retries:
    requests.adapters.DEFAULT_RETRIES = args.retries

download_path(args.output_path, args.url, '')
