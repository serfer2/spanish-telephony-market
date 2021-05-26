import os
import json
from datetime import (
    datetime,
    timedelta
)
from unittest import (
    TestCase
)
from unittest import mock
from unittest.case import expectedFailure

from expects import (
    have_keys,
    equal,
    expect
)

from backend.preprocess_data import (
    run,
    _build_dataset,
    _load_file,
    _operators_status_by_year,
    _read_csv_lines,
    _unique_ordered_years,
)

db_is_up_to_date = mock.MagicMock(return_value=False)


class BaseTestCase(TestCase):

    def tearDown(self) -> None:
        files_to_delete = (
            '/tmp/geograficos.txt',
            '/tmp/moviles.txt',
            '/tmp/landline_operators.json',
            '/tmp/mobile_operators.json',
            '/tmp/landline_data.json',
            '/tmp/mobile_data.json',
        )
        for filepath in files_to_delete:
            try:
                os.unlink(filepath)
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

        http_client.get.assert_called_with(
            self.bd_url,
            headers={'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:88.0) Gecko/20100101 Firefox/88.0'},
            allow_redirects=True
        )

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

            open_file.assert_any_call('/tmp/geograficos.txt', encoding='iso-8859-15')
            open_file.assert_any_call('/tmp/moviles.txt', encoding='iso-8859-15')

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


@mock.patch('backend.preprocess_data._db_is_outdated', db_is_up_to_date)
class PreprocessDataExportOperatorsTestCase(BaseTestCase):

    @mock.patch('backend.preprocess_data.OUTPUT_DIR', '/tmp')
    @mock.patch('backend.preprocess_data._read_csv_lines')
    def test_it_exports_landline_operators(self, read_csv_lines):
        file_content = (
            '815#00#Madrid#Asignado#AVATEL MÓVIL#30/04/2021',
            '822#01#Cuenca#Asignado#VODAFONE ONO#10/07/2003',
            '822#02#Cuenca#Asignado#VODAFONE ONO#20/08/2003',
            '822#01#Cuenca#Compartido#VODAFONE ESPAÑA#21/12/2016',
            '822#24#Cuenca#Asignado#AIRE NETWORKS DEL MEDITERRÁNEO, S.L. UNIPERSONAL#09/07/2013',
            '822#24#Cuenca#Subasignado 03#WIFI CANARIAS#15/05/2018'
        )
        read_csv_lines.return_value = file_content

        run()

        operators = u"""{
            "1": {
                "id": "1",
                "name": "AVATEL MÓVIL",
                "date_added": "2021-04-30"
            },
            "2": {
                "id": "2",
                "name": "VODAFONE ONO",
                "date_added": "2003-07-10"
            },
            "3": {
                "id": "3",
                "name": "VODAFONE ESPAÑA",
                "date_added": "2016-12-21"
            },
            "4": {
                "id": "4",
                "name": "AIRE NETWORKS DEL MEDITERRÁNEO, S.L. UNIPERSONAL",
                "date_added": "2013-07-09"
            },
            "5": {
                "id": "5",
                "name": "WIFI CANARIAS",
                "date_added": "2018-05-15"
            }
        }"""
        expected_content = 'landlineOperators = ' + json.dumps(json.loads(operators))
        with open('/tmp/landline_operators.json', 'r', encoding='iso-8859-15') as f:
            file_content = f.read()

            expect(file_content).to(equal(expected_content))

    @mock.patch('backend.preprocess_data.OUTPUT_DIR', '/tmp')
    @mock.patch('backend.preprocess_data._read_csv_lines')
    def test_it_exports_mobile_operators(self, read_csv_lines):
        file_content = (
            '600###Asignado#VODAFONE ESPAÑA, S.A. UNIPERSONAL#19/11/1998',
            '601#0##Asignado#VODAFONE ESPAÑA, S.A. UNIPERSONAL#01/11/2016',
            '601#5# #Asignado#XFERA MÓVILES, S.A. UNIPERSONAL#02/02/2021',
        )
        read_csv_lines.return_value = file_content

        run()

        operators = u"""{
            "1": {
                "id": "1",
                "name": "VODAFONE ESPAÑA, S.A. UNIPERSONAL",
                "date_added": "1998-11-19"
            },
            "2": {
                "id": "2",
                "name": "XFERA MÓVILES, S.A. UNIPERSONAL",
                "date_added": "2021-02-02"
            }
        }"""
        expected_content = 'mobileOperators = ' + json.dumps(json.loads(operators))
        with open('/tmp/mobile_operators.json', 'r', encoding='iso-8859-15') as f:
            file_content = f.read()

            expect(file_content).to(equal(expected_content))


@mock.patch('backend.preprocess_data._db_is_outdated', db_is_up_to_date)
class PreprocessDataBuildBaseGraphDatasetTestCase(BaseTestCase):

    def test_it_gets_sorted_unique_dates(self):
        registries = [
            {
                'operator': 'operator 1',
                'wholesaler': '',
                'date': '2020-01-30',
                'index': '815',
                'block': '00',
                'sub_block': '',
                'nmin': 815000000,
                'nmax': 815009999,
                'volume': 10000,
                'type': 'asignado',
            }, {
                'operator': 'operator 2',
                'wholesaler': 'operator1',
                'date': '2021-02-30',
                'index': '815',
                'block': '00',
                'sub_block': '01',
                'nmin': 815000100,
                'nmax': 815000199,
                'volume': 100,
                'type': 'subasignado',
            }, {
                'operator': 'operator 3',
                'wholesaler': '',
                'date': '2021-02-30',
                'index': '966',
                'block': '55',
                'sub_block': '',
                'nmin': 966550000,
                'nmax': 966559999,
                'volume': 10000,
                'type': 'asignado',
            }
        ]

        years = _unique_ordered_years(registries)

        expect(years).to(equal(['2020', '2021']))

    # def test_it_gets_operators_status_by_year(self):
    #     registries = [
    #         {
    #             #  Links Operator 1 with ER
    #             'operator': 'operator 1',
    #             'wholesaler': '',
    #             'date': '1999-01-30',
    #             'volume': 10000,
    #             'type': 'asignado',
    #         }, {
    #             'operator': 'operator 1',
    #             'wholesaler': '',
    #             'date': '2018-12-31',
    #             'volume': 10000,
    #             'type': 'asignado',
    #         }, {
    #             #  Not to be shown, filtered by date
    #             'operator': 'operator 2',
    #             'wholesaler': 'operator 1',
    #             'date': '2021-02-30',
    #             'volume': 100,
    #             'type': 'subasignado',
    #         }, {
    #             #  Will produce link between operator 3 and operator 1
    #             'operator': 'operator 3',
    #             'wholesaler': 'operator 1',
    #             'date': '2010-02-30',
    #             'volume': 100,
    #             'type': 'subasignado',
    #         }, {
    #             #  Links this operator 3 with ER
    #             'operator': 'operator 3',
    #             'wholesaler': '',
    #             'date': '2019-12-01',
    #             'volume': 10000,
    #             'type': 'asignado',
    #         }
    #     ]

    #     operators_by_name = {'operator 1': '1', 'operator 2': '2', 'operator 3': '3'}
    #     operators = _operators_status_by_year('2020-01-30', registries, operators_by_name)

    #     expected_operators = [
    #         {
    #             'id': '1',
    #             'volume': 20000,
    #             'links': ['0', ]
    #         }, {
    #             'id': '3',
    #             'volume': 10100,
    #             'links': ['0', '1']
    #         }
    #     ]
    #     expect(len(operators)).to(equal(2))
    #     expect(operators[0]).to(equal(expected_operators[0]))
    #     expect(operators[1]).to(equal(expected_operators[1]))

    # def test_it_builds_dataset_with_ordered_dates_and_associated_operators_status(self):
    #     registries = [
    #         {
    #             'operator': 'operator 1',
    #             'wholesaler': '',
    #             'date': '1999-01-30',
    #             'volume': 10000,
    #             'type': 'asignado',
    #         }, {
    #             'operator': 'operator 1',
    #             'wholesaler': '',
    #             'date': '2018-12-31',
    #             'volume': 10000,
    #             'type': 'asignado',
    #         }, {
    #             'operator': 'operator 2',
    #             'wholesaler': 'operator 1',
    #             'date': '2018-12-31',
    #             'index': '815',
    #             'volume': 100,
    #             'type': 'subasignado',
    #         }, {
    #             'operator': 'operator 3',
    #             'wholesaler': 'operator 1',
    #             'date': '2010-02-30',
    #             'volume': 100,
    #             'type': 'subasignado',
    #         }, {
    #             'operator': 'operator 3',
    #             'wholesaler': '',
    #             'date': '2019-12-01',
    #             'volume': 10000,
    #             'type': 'asignado',
    #         }
    #     ]
    #     operators_by_name = {'operator 1': '1', 'operator 2': '2', 'operator 3': '3'}

    #     dataset = _build_dataset(registries, operators_by_name)

    #     expect(len(dataset)).to(equal(4))
    #     expect(dataset['1999-01-30']).to(have_keys({
    #         'date': '1999-01-30',
    #         'operators': [
    #             {'id': '1', 'volume': 10000, 'links': ['0', ]}
    #         ]
    #     }))
    #     expect(dataset['2010-02-30']).to(have_keys({
    #         'date': '2010-02-30',
    #         'operators': [
    #             {'id': '1', 'volume': 10000, 'links': ['0', ]},
    #             {'id': '3', 'volume': 100, 'links': ['1', ]}
    #         ]
    #     }))
    #     expect(dataset['2018-12-31']).to(have_keys({
    #         'date': '2018-12-31',
    #         'operators': [
    #             {'id': '1', 'volume': 20000, 'links': ['0', ]},
    #             {'id': '2', 'volume': 100, 'links': ['1', ]},
    #             {'id': '3', 'volume': 100, 'links': ['1', ]}
    #         ]
    #     }))
    #     expect(dataset['2019-12-01']).to(have_keys({
    #         'date': '2019-12-01',
    #         'operators': [
    #             {'id': '1', 'volume': 20000, 'links': ['0', ]},
    #             {'id': '2', 'volume': 100, 'links': ['1', ]},
    #             {'id': '3', 'volume': 10100, 'links': ['0', '1']}
    #         ]
    #     }))
