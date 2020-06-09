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

# Create your tests here.


class TestModelView(TestCase):

    def setUp(self):
        self.data_dir = Path(__file__).parent.absolute() / "test_data"

    @patch('dkconsole.model.services.MLModelService.delete_model')
    def test_delete(self, mock_delete_model):
        client = Client()
        data = dict()
        data["model_path"] = str(self.data_dir / "job_118")

        response = client.post(
            reverse('model:delete'),
            data=json.dumps(data),
            content_type='application/json'
        )

        mock_delete_model.assert_called_once()

        assert response.status_code, status.HTTP_200_OK
        assert response.data['success'] is True

    def test_delete_non_exist_model_file(self):
        client = Client()
        data = dict()
        data["model_path"] = str(self.data_dir / "non-exist.h5")

        response = client.post(
            reverse('model:delete'),
            data=json.dumps(data),
            content_type='application/json'
        )

        assert response.status_code, status.HTTP_200_OK
        assert response.data['success'] is False
