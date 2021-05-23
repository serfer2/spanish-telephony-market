import os
import requests
import sys
from datetime import (
    date,
    datetime,
)
from typing import (
    Dict,
    Iterable,
    List,
)
from zipfile import ZipFile

BD_URL = 'https://numeracionyoperadores.cnmc.es/bd-num.zip'
USER_AGENT = 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0'
TMP_DIR = '/tmp'
BD_FILE = 'bd-num.zip'
LANDLINE_FILE = 'geograficos.txt'
MOBILE_FILE = 'moviles.txt'


def run():

    if _db_is_outdated(filepath=f'{TMP_DIR}/{LANDLINE_FILE}'):
        _download_bd(BD_URL)

    landline_registries = _load_file(f'{TMP_DIR}/{LANDLINE_FILE}')
    mobile_registries = _load_file(f'{TMP_DIR}/{MOBILE_FILE}')
    print(f'Readed {len(landline_registries)} landline registries')
    print(f'Readed {len(mobile_registries)} mobile registries')

    if not landline_registries or not mobile_registries:
        return 1

    return 0


def _download_bd(url: str):
    print(f'Dowloading (with {str(requests)}): {url}')
    response = requests.get(
        url,
        headers={'User-Agent': USER_AGENT},
        allow_redirects=True
    )
    try:
        zip_tmp_path = f'{TMP_DIR}/{BD_FILE}'
        with open(zip_tmp_path, 'wb') as f:
            f.write(response.content)
        with ZipFile(zip_tmp_path, 'r') as zipObj:
            zipObj.extractall(path=TMP_DIR, members=(LANDLINE_FILE, MOBILE_FILE))
    except Exception:
        print('_download_bd() - Can\'t extract DB files')
    try:
        os.unlink(zip_tmp_path)
    except Exception:
        pass


def _db_is_outdated(filepath: str) -> bool:
    cdate = _db_creation_date(filepath)
    if cdate is not None:
        return cdate < datetime.now().date()
    return True


def _db_creation_date(filepath: str) -> date:
    if os.path.exists(filepath) and os.path.isfile(filepath):
        return datetime.fromtimestamp(os.path.getctime(filepath)).date()
    return None


def _read_csv_lines(filepath: str) -> List[str]:
    lines = []
    try:
        with open(filepath, encoding='iso-8859-15') as f:
            lines = [line.strip() for line in f.readlines()]
    except Exception:
        pass
    return lines


def _numbers_from_line(fields: List) -> Iterable:
    index = fields[0]
    block = fields[1]
    sub_block = fields[3].split(' ')
    sub_block = sub_block[1].strip() if len(sub_block) > 1 else ''
    nmin = int(f'{index}{block}{sub_block}'.ljust(9, '0'))
    nmax = int(f'{index}{block}{sub_block}'.ljust(9, '9'))

    return (index, block, sub_block, nmin, nmax)


def _date_to_iso(spanish_str_date: str) -> str:
    dd, mm, yyyy = spanish_str_date.split('/')
    return f'{yyyy}-{mm}-{dd}'


def _set_volumes_and_wholesaler(registries: List[Dict]):
    block_owners = {}
    block_shares = {}

    # Volume: Count quantity of operators that shares number blocks.
    # Wholesaler: Get owner of every number block.
    for registry in registries:
        _key = f'{registry["index"]}{registry["block"]}'
        if _key not in block_owners and registry['type'] == 'asignado':
            block_owners[_key] = registry['operator']
        if _key not in block_shares:
            block_shares[_key] = 0
        block_shares[_key] += 1 if registry['type'] != 'subasignado' else 0

    # Adjust volume for shared blocks and set wholesaler when sub-assigned range
    for registry in registries:
        _key = f'{registry["index"]}{registry["block"]}'
        registry['volume'] = int(registry['volume'] / block_shares[_key])
        if registry['type'] == 'subasignado':
            registry['wholesaler'] = block_owners[_key]


def _load_file(filepath: str) -> List[Dict]:
    registries = []
    lines = _read_csv_lines(filepath)

    for line in lines:
        fields = line.split('#')
        if len(fields) != 6:
            continue
        if fields[3].startswith('Libre'):
            continue
        index, block, sub_block, nmin, nmax = _numbers_from_line(fields)
        registries.append({
            'operator': fields[4],
            'wholesaler': '',
            'date': _date_to_iso(fields[5]),
            'index': index,
            'block': block,
            'sub_block': sub_block,
            'nmin': nmin,
            'nmax': nmax,
            'volume': (nmax - nmin) + 1,
            'type': fields[3].split(' ')[0].lower()
        })

    _set_volumes_and_wholesaler(registries)

    return registries


if __name__ == '__main__':
    sys.exit(run())
