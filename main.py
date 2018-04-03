import requests
import shutil
import pathlib
import os.path
# import pprint

API_ENDPOINT = 'https://cloud-api.yandex.net/v1/disk/public/resources/{}?public_key={}'


def save_file(url, save_path):
    r = requests.get(url, stream=True)
    # TODO: verify size, checksum and re-download in necessary
    with open(save_path, 'wb') as f:
        shutil.copyfileobj(r.raw, f)


def recurse(url, save_path):
    pathlib.Path(save_path).mkdir(parents=True, exist_ok=True)
    items = requests.get(API_ENDPOINT.format('', url)).json()['_embedded']['items']
    ret = []
    for i in items:
        new_path = os.path.join(save_path, i['name'])
        if 'file' in i:
            print('file {}'.format(new_path))
            save_file(i['file'], new_path)
        else:
            print('folder {}'.format(new_path))


target_root = 'https://yadi.sk/d/AhgSCPivmcMff'
recurse(target_root, 'dl')
