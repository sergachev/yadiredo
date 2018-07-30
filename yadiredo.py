#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil
import pathlib
import os
import argparse
import hashlib
import pprint
import requests
from logzero import logger as log


API_ENDPOINT = 'https://cloud-api.yandex.net/v1/disk/public/resources/?public_key={}&path=/{}&offset={}'
dry = False


def md5sum(filename):
    md5 = hashlib.md5()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(128 * md5.block_size), b''):
            md5.update(chunk)
    return md5.hexdigest()


def check_and_download_file(url, path, size, checksum):
    if os.path.isfile(path):
        if size == os.path.getsize(path):
            if checksum == md5sum(path):
                log.info('skipping correct {}'.format(path))
                return
    if not dry:
        log.info('downloading {}'.format(path))
        r = requests.get(url, stream=True)
        with open(path, 'wb') as f:
            shutil.copyfileobj(r.raw, f)


def download_directory(dl_root_path, public_key, src_path, offset=0):
    log.info('getting folder "{}" at offset {}'.format(src_path, offset))
    cur_path = os.path.join(dl_root_path, src_path)
    pathlib.Path(cur_path).mkdir(parents=True, exist_ok=True)
    jsn = requests.get(API_ENDPOINT.format(public_key, src_path, offset)).json()
    emb = jsn['_embedded']
    items = emb['items']
    for i in items:
        if 'file' in i:
            file_save_path = os.path.join(cur_path, i['name'])
            check_and_download_file(i['file'], file_save_path, i['size'], i['md5'])
        else:
            subdir_path = os.path.join(src_path, i['name'])
            download_directory(dl_root_path, public_key, subdir_path)
    last = offset + emb['limit']
    if last < emb['total']:
        download_directory(dl_root_path, public_key, src_path, last)

parser = argparse.ArgumentParser(description='Yandex.Disk downloader.')
parser.add_argument('url')
parser.add_argument('-o', dest='output_path', default='output')
parser.add_argument('--dry', action='store_const', const=True, default=False)
parser.add_argument('-r', dest='retries', default=None)
args = parser.parse_args()
dry = args.dry
if args.retries:
    requests.adapters.DEFAULT_RETRIES = args.retries

download_directory(args.output_path, args.url, '')
