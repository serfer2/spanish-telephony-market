import json
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
OUTPUT_DIR = 'ui/data'
LANDLINE_OPERATORS_FILE = 'landline_operators.js'
MOBILE_OPERATORS_FILE = 'mobile_operators.js'
DATASET_FILE = 'dataset.js'


def run():

    if _db_is_outdated(filepath=f'{TMP_DIR}/{LANDLINE_FILE}'):
        _download_bd(BD_URL)

    landline_registries = _load_file(f'{TMP_DIR}/{LANDLINE_FILE}')
    mobile_registries = _load_file(f'{TMP_DIR}/{MOBILE_FILE}')
    print(f'Readed {len(landline_registries)} landline registries')
    print(f'Readed {len(mobile_registries)} mobile registries')

    if not landline_registries or not mobile_registries:
        return 1

    landline_operators = _get_operators(registries=landline_registries)
    mobile_operators = _get_operators(registries=mobile_registries)
    _export_operators(
        'landlineOperators',
        f'{OUTPUT_DIR}/{LANDLINE_OPERATORS_FILE}',
        landline_operators
    )
    _export_operators(
        'mobileOperators',
        f'{OUTPUT_DIR}/{MOBILE_OPERATORS_FILE}',
        mobile_operators
    )

    landline_operators_by_name = {}
    for _id, operator in landline_operators.items():
        landline_operators_by_name[operator['name']] = _id

    mobile_operators_by_name = {}
    for _id, operator in mobile_operators.items():
        mobile_operators_by_name[operator['name']] = _id

    landline_dataset = _build_dataset(landline_registries, landline_operators_by_name)
    mobile_dataset = _build_dataset(mobile_registries, mobile_operators_by_name)
    _export(landline_dataset, mobile_dataset)

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


def _read_csv_lines(filepath: str) -> List[str]:
    lines = []
    try:
        with open(filepath, encoding='iso-8859-15') as f:
            lines = [line.strip() for line in f.readlines()]
    except Exception:
        pass
    return lines


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


def _get_operators(registries: List[Dict]) -> List[Dict]:
    id = 0
    operators = {}
    operators_id = {}
    for registry in registries:
        if registry['operator'] not in operators:
            id += 1
            operators[registry['operator']] = {
                'id': str(id),
                'name': registry['operator'],
                'date_added': registry['date'],
            }
            operators_id[str(id)] = registry['operator']
        elif operators[registry['operator']]['date_added'] > registry['date']:
            operators[registry['operator']]['date_added'] = registry['date']
    operators_dict = {}
    for i in range(1, len(operators) + 1):
        operators_dict[str(i)] = operators[operators_id[str(i)]]

    return operators_dict


def _export_operators(var_name: str, filepath: str, operators: Dict):
    with open(filepath, mode='w', encoding='utf-8') as f:
        content = f'{var_name} = ' + json.dumps(operators, )
        f.write(content)


def _unique_ordered_years(registries: List[Dict]) -> List:
    years = []
    for registy in registries:
        year = registy['date'].split('-')[0]
        if year not in years:
            years.append(year)
    years.sort()
    return years


def _operators_status_by_year(year_filter: str, registries: List[Dict], operators_by_name: Dict) -> List[Dict]:
    operators = {}

    for reg in registries:
        year = reg['date'].split('-')[0]
        if year > year_filter:
            continue

        _id = operators_by_name[reg['operator']]
        if _id not in operators:
            operators[_id] = {'id': _id, 'volume': 0, 'links': []}

        links = operators[_id]['links']
        links.append(operators_by_name[reg['wholesaler']] if reg['wholesaler'] else '0')
        links = list(set(links))
        links.sort()

        operators[_id]['volume'] += reg['volume']
        operators[_id]['links'] = links

    return sorted([op for _, op in operators.items()], key=lambda x: sum([int(i) for i in x['links']]))


def _build_dataset(registries: List[Dict], operators_by_name: Dict) -> Dict:
    dataset = {}
    years = [int(y) for y in _unique_ordered_years(registries)]
    _from = min(years)
    _to = max(years)

    for year in range(_from, _to + 1):
        _y = str(year)
        dataset[_y] = {
            'year': _y,
            'operators': _operators_status_by_year(_y, registries, operators_by_name)
        }

    return dataset


def _export(landline_dataset, mobile_dataset):
    with open(f'{OUTPUT_DIR}/{DATASET_FILE}', 'w', encoding='utf-8') as f:
        sep = (',', ':')
        f.write(f'landlineData = {json.dumps(landline_dataset, separators=sep)}; ')
        f.write(f'mobileData = {json.dumps(mobile_dataset, separators=sep)};')


if __name__ == '__main__':
    sys.exit(run())
