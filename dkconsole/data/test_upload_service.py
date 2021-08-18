from unittest.mock import patch
from uuid import uuid4

from django.test import TestCase

from .data_service_v2 import TubServiceV2


class TestUploadService(TestCase):
    def setUp(self):
        self.data = dict()
        self.data['tub_names'] = ['tub_26_21-07-02', 'tub_27_21-07-02']
        self.upload_service = TubServiceV2

    def test_upload(self):
        with patch('requests.post') as r:
            r.return_value.status_code = 200
            r.return_value.json.return_value = {"uuid": str(uuid4())}
            result = self.upload_service.upload_to_hq(self.data)
            assert result is not None
            print(result)
