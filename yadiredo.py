#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import shutil
import pathlib
import os
import argparse
import hashlib
import pprint
import requests

API_ENDPOINT = 'https://cloud-api.yandex.net/v1/disk/public/resources/?public_key={}&path=/{}'


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


def download_directory(dl_root_path, public_key, src_path, dry):
    cur_path = os.path.join(dl_root_path, src_path)
    pathlib.Path(cur_path).mkdir(parents=True, exist_ok=True)
    jsn = requests.get(API_ENDPOINT.format(public_key, src_path)).json()
    try:
        items = jsn['_embedded']['items']
    except KeyError:
        pprint.pprint(jsn)
        return
    for i in items:
        if 'file' in i:
            file_save_path = os.path.join(cur_path, i['name'])
            check_and_download_file(i['file'], file_save_path, i['size'], i['md5'], dry)
        else:
            subdir_path = os.path.join(src_path, i['name'])
            print('entering folder {}'.format(subdir_path))
            download_directory(dl_root_path, public_key, subdir_path, dry)


parser = argparse.ArgumentParser(description='Yandex.Disk downloader.')
parser.add_argument('url')
parser.add_argument('-o', dest='output_path', default='output')
parser.add_argument('--dry', action='store_const', const=True, default=False)
args = parser.parse_args()

download_directory(args.output_path, args.url, '', args.dry)
