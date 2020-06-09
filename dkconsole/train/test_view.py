from django.test import TestCase
from django.test import Client
from django.urls import reverse
import json
from rest_framework import status
from pathlib import Path
import io
import tarfile
import re
from unittest.mock import patch
from dkconsole.train.models import Job

# Create your tests here.


class TestTrainView(TestCase):

    def setUp(self):
        self.data_dir = Path(__file__).parent.absolute() / "test_data"


    def test_submit_job(self):
        client = Client()
        data = dict()
        data["tub_paths"] = [str(self.data_dir / "tub_7_20-03-31"),
                             str(self.data_dir / "tub_6_20-03-31")]

        with patch('dkconsole.train.services.TrainService.submit_job') as mock_method:
            mock_method.return_value = 'mock-spot-request-id'

            response = client.post(
                reverse('train:submit_job'),
                data=json.dumps(data),
                content_type='application/json'
            )

            mock_method.assert_called_with(data["tub_paths"])
            assert response.status_code == status.HTTP_200_OK
            assert response.data['success'] is True

    def test_submit_job_2(self):
        client = Client()
        data = dict()
        data["tub_pathsx"] = []

        with patch('dkconsole.train.services.TrainService.submit_job') as mock_method:

            response = client.post(
                reverse('train:submit_job'),
                # data=json.dumps(data),
                content_type='application/json'
            )

            mock_method.assert_not_called()
            assert response.status_code == status.HTTP_400_BAD_REQUEST

        data["tub_paths"] = []

        with patch('dkconsole.train.services.TrainService.submit_job') as mock_method:

            response = client.post(
                reverse('train:submit_job'),
                data=json.dumps(data),
                content_type='application/json'
            )

            mock_method.assert_not_called()
            assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_index(self):
        job = Job()
        job.status = "Some status"
        job.save()
        client = Client()
        data = dict()

        response = client.get(
            reverse('train:index'),
            content_type='application/json'
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["status"] == "Some status"
