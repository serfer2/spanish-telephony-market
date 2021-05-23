import os
from datetime import (
    datetime,
    timedelta
)
from unittest import (
    TestCase
)
from unittest import mock

from expects import (
    have_keys,
    equal,
    expect
)

from backend.preprocess_data import (
    run,
    _load_file,
    _read_csv_lines,
)

db_is_up_to_date = mock.MagicMock(return_value=False)
file_reader_mock = mock.MagicMock()


class BaseTestCase(TestCase):

    def tearDown(self) -> None:
        try:
            os.unlink('backend/data/mobile_data.json')
        except Exception:
            pass
        try:
            os.unlink('backend/data/landline_data.json')
        except Exception:
            pass
        return super().tearDown()


class PreprocessDataDownloadDbTestCase(BaseTestCase):

    def setUp(self):
        self.bd_url = 'https://numeracionyoperadores.cnmc.es/bd-num.zip'

    @mock.patch('backend.preprocess_data.requests')
    @mock.patch('backend.preprocess_data._db_creation_date')
    def test_it_downloads_bd_when_outdated(self, db_creation_date, http_client):
        db_creation_date.return_value = (datetime.now() - timedelta(days=1)).date()

        run()

        http_client.get.assert_called_with(self.bd_url)

    @mock.patch('backend.preprocess_data.requests')
    @mock.patch('backend.preprocess_data._db_is_outdated')
    def test_it_doesnt_download_bd_when_not_outdated(self, is_outdated, http_client):
        is_outdated.return_value = False

        run()

        http_client.get.assert_not_called()


@mock.patch('backend.preprocess_data._db_is_outdated', db_is_up_to_date)
class PreprocessDataLoadTestCase(BaseTestCase):

    def test_it_reads_landline_and_mobile_files(self):
        with mock.patch('backend.preprocess_data.open', mock.mock_open()) as open_file:

            run()

            open_file.assert_any_call(
                'data/bd-num/geograficos.txt',
                encoding='iso-8859-15'
            )
            open_file.assert_any_call(
                'data/bd-num/moviles.txt',
                encoding='iso-8859-15'
            )

    @mock.patch('backend.preprocess_data._load_file')
    def test_it_returns_error_code_when_no_data_readed(self, load_file):
        load_file.side_effect = ([], [])

        return_code = run()

        expect(return_code).to(equal(1))

    def test_it_loads_csv_lines_with_correct_encoding(self):
        file_content = (
            '815#00#Madrid#Asignado#AVATEL MÓVIL, S.L. UNIPERSONAL#30/04/2021\n'
            '822#00#Santa Cruz de Tenerife#Asignado#DUOCOM#23/11/2000\n'
            '822#01#Alicante#Compartido#VODAFONE ESPAÑA, S.A. UNIPERSONAL#21/12/2016'
        )
        with open('/tmp/test.csv', encoding='iso-8859-15', mode='w') as f:
            f.write(file_content)

        lines = _read_csv_lines(filepath='/tmp/test.csv')

        expect(lines).to(equal([
            '815#00#Madrid#Asignado#AVATEL MÓVIL, S.L. UNIPERSONAL#30/04/2021',
            '822#00#Santa Cruz de Tenerife#Asignado#DUOCOM#23/11/2000',
            '822#01#Alicante#Compartido#VODAFONE ESPAÑA, S.A. UNIPERSONAL#21/12/2016'
        ]))

    def test_it_loads_file_content_into_objects(self):
        file_content = (
            '815#00#Madrid#Asignado#AVATEL MÓVIL#30/04/2021\n'
            '822#01#Cuenca#Asignado#VODAFONE ONO#10/07/2003\n'
            '822#01#Cuenca#Compartido#VODAFONE ESPAÑA#21/12/2016\n'
            '822#24#Cuenca#Asignado#AIRE NETWORKS DEL MEDITERRÁNEO, S.L. UNIPERSONAL#09/07/2013\n'
            '822#24#Cuenca#Subasignado 03#WIFI CANARIAS#15/05/2018\n'
        )
        with open('/tmp/test.csv', encoding='iso-8859-15', mode='w') as f:
            f.write(file_content)

        registries = _load_file('/tmp/test.csv')

        expect(len(registries)).to(equal(5))
        expect(registries[0]).to(have_keys({
            'operator': 'AVATEL MÓVIL',
            'wholesaler': '',
            'date': '2021-04-30',
            'index': '815',
            'block': '00',
            'sub_block': '',
            'nmin': 815000000,
            'nmax': 815009999,
            'volume': 10000,
            'type': 'asignado',
        }))
        expect(registries[1]).to(have_keys({
            'operator': 'VODAFONE ONO',
            'wholesaler': '',
            'date': '2003-07-10',
            'index': '822',
            'block': '01',
            'sub_block': '',
            'nmin': 822010000,
            'nmax': 822019999,
            'volume': 5000,
            'type': 'asignado',
        }))
        expect(registries[2]).to(have_keys({
            'operator': 'VODAFONE ESPAÑA',
            'wholesaler': '',
            'date': '2016-12-21',
            'index': '822',
            'block': '01',
            'sub_block': '',
            'nmin': 822010000,
            'nmax': 822019999,
            'volume': 5000,
            'type': 'compartido',
        }))
        expect(registries[3]).to(have_keys({
            'operator': 'AIRE NETWORKS DEL MEDITERRÁNEO, S.L. UNIPERSONAL',
            'wholesaler': '',
            'date': '2013-07-09',
            'index': '822',
            'block': '24',
            'sub_block': '',
            'nmin': 822240000,
            'nmax': 822249999,
            'volume': 10000,
            'type': 'asignado',
        }))
        expect(registries[4]).to(have_keys({
            'operator': 'WIFI CANARIAS',
            'wholesaler': 'AIRE NETWORKS DEL MEDITERRÁNEO, S.L. UNIPERSONAL',
            'date': '2018-05-15',
            'index': '822',
            'block': '24',
            'sub_block': '03',
            'nmin': 822240300,
            'nmax': 822240399,
            'volume': 100,
            'type': 'subasignado',
        }))
