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
    # have_keys,
    equal,
    expect
)

from backend.preprocess_data import run

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
