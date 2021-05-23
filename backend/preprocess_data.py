import os
import requests
import sys
from datetime import (
    date,
    datetime,
)
from typing import (
    Dict,
    List,
)

BD_URL = 'https://numeracionyoperadores.cnmc.es/bd-num.zip'
LANDLINE_FILE = 'data/bd-num/geograficos.txt'
MOBILE_FILE = 'data/bd-num/moviles.txt'


def run():

    if _db_is_outdated(filepath=LANDLINE_FILE):
        _download_bd(BD_URL)

    landline_registries = _load_file(_read_csv_lines(LANDLINE_FILE))
    mobile_registries = _load_file(_read_csv_lines(MOBILE_FILE))

    if not landline_registries or not mobile_registries:
        return 1

    print(f'Readed {landline_registries} landline registries')
    print(f'Readed {mobile_registries} mobile registries')

    return 0


def _download_bd(url: str):
    print(f'Dowloading (with {str(requests)}): {url}')
    requests.get(url)


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


def _load_file(lines: List) -> List[Dict]:
    return lines


def _landline_output_filepath():
    return 'data/landline_data.json'


def _mobile_output_filepath():
    return 'data/mobile_data.json'


if __name__ == '__main__':
    sys.exit(run())
