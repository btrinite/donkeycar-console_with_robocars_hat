from django.test import TestCase
from django.test import Client
from django.urls import reverse
import json
from rest_framework import status
from pathlib import Path
import io
import tarfile
import re
from unittest.mock import patch, ANY
from django.core import serializers


# from .views import *

# Create your tests here.


class TestDataView(TestCase):

    def setUp(self):
        self.data_dir = Path(__file__).parent.absolute() / "test_data"

    def test_index(self):
        client = Client()
        data = dict()

        response = client.get(
            reverse('data:index'),
            content_type='application/json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 14

    def test_tub_archive(self):
        client = Client()
        data = dict()
        data["tub_paths"] = [str(self.data_dir / "tub_7_20-03-31"),
                             str(self.data_dir / "tub_6_20-03-31")]

        response = client.post(
            reverse('data:tub_archive'),
            data=json.dumps(data),
            content_type='application/json'
        )

        assert response.status_code, status.HTTP_200_OK
        assert re.match(r"inline; filename=tmp\w+.tar.gz", response.get('Content-Disposition'))

        f = io.BytesIO(response.content)
        tar = tarfile.open(fileobj=f, mode="r:gz")
        assert 4 == len(tar.getmembers())
        tar.close()

    @patch('dkconsole.data.services.TubService.delete_tub')
    def test_delete(self, mock_delete_tub):
        client = Client()
        data = dict()
        data["tub_path"] = str(self.data_dir / "tub_1_20-03-30")

        response = client.post(
            reverse('data:delete'),
            data=json.dumps(data),
            content_type='application/json'
        )

        mock_delete_tub.assert_called_once()

        assert response.status_code, status.HTTP_200_OK
        assert response.data['success'] is True

    def test_delete_non_exist_tub_file(self):
        client = Client()
        data = dict()
        data["tub_path"] = str(self.data_dir / "non-exist")

        response = client.post(
            reverse('data:delete'),
            data=json.dumps(data),
            content_type='application/json'
        )

        assert response.status_code, status.HTTP_200_OK
        assert response.data['success'] is False

    def test_jpg(self):
        client = Client()

        response = client.get(
            reverse('data:jpg', kwargs={'tub_name': 'tub_18_19-04-06', 'filename': '1_cam-image_array_.jpg'})
        )

        assert response.status_code, status.HTTP_200_OK
        assert re.match(r"image/jpeg", response.get('Content-Type'))
        assert re.match(r"3953", response.get('Content-Length'))

    def test_jpg_not_exist(self):
        client = Client()
        response = client.get(
            reverse('data:jpg', kwargs={'tub_name': 'tub_18_19-04-06', 'filename': '0_cam-image_array_.jpg'})
        )

        assert response.status_code, status.HTTP_200_OK
        # assert response.data['success'] is False
        assert re.match(r"image/png", response.get('Content-Type'))
        assert re.match(r"16973", response.get('Content-Length'))

    def test_delete_tubs(self):
        client = Client()
        data = dict()
        data["number_of_images"] = str(self.data_dir / "tub_1_20-03-30")

        response = client.post(
            reverse('data:delete_tubs'),
            data=json.dumps(data),
            content_type='application/json'
        )

        assert response.status_code, status.HTTP_200_OK
        assert response.data['success'] is True

    def test_get_detail(self):
        client = Client()
        data = dict()

        response = client.get(
            reverse('data:detail'),
            content_type='application/json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 14

    def test_get_latest(self):
        client = Client()
        data = dict()

        response = client.get(
            reverse('data:latest'),
            content_type='application/json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 5

    def test_show_meta(self):
        client = Client()
        data = dict()

        response = client.get(
            reverse('data:meta', kwargs={'tub_name': 'tub_18_19-04-06'}),
            content_type='application/json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 5

    def test_update_meta(self):
        client = Client()
        data = dict()
        data["update_parms"] = ["123: test"]

        response = client.post(
            reverse('data:update_meta', kwargs={'tub_name': 'tub_18_19-04-06'}),
            data=json.dumps(data),
            content_type='application/json'
        )

        assert response.status_code, status.HTTP_200_OK
        assert response.data['success'] is True

    def test_upload(self):
        # with patch('dkconsole.data.data_service_v2.TubServiceV2.upload') as mock_method:
        # mock_method.return_value = {'done': True, 'successful': ['tub_26_21-07-02', 'tub_27_21-07-02']}
        client = Client()
        data = dict()
        data["tub_names"] = ['tub_26_21-07-02', 'tub_27_21-07-02']

        # r.return_value.status_code = 200
        response = client.post(
            reverse('data:upload_tub'),
            data=json.dumps(data),
            content_type='application/json'
        )
        print(response.data)
        assert response.status_code, status.HTTP_200_OK
        assert response.data['done'] is True
