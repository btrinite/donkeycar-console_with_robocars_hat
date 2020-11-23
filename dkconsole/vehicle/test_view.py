import io
import json
import re
import tarfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from django.conf import settings
from django.test import Client, TestCase
from django.urls import reverse
from rest_framework import status
from unittest import mock

from .vehicle_service import VehicleService

# Create your tests here.


class TestVehicleView(TestCase):

    def test_start_driving(self):
        client = Client()
        data = dict()
        data["use_joystick"] = True

        with patch('dkconsole.vehicle.vehicle_service.VehicleService.start_driving') as mock_method:
            response = client.post(
                reverse('vehicle:start_driving'),
                data=json.dumps(data),
                content_type='application/json'
            )
            mock_method.assert_called_once()

        assert response.status_code, status.HTTP_200_OK

    def test_stop_driving(self):
        client = Client()
        data = dict()
        data["use_joystick"] = True

        with patch('dkconsole.vehicle.vehicle_service.VehicleService.stop_driving') as mock_method:
            response = client.post(
                reverse('vehicle:stop_driving'),
                content_type='application/json'
            )
            mock_method.assert_called_once()

        assert response.status_code, status.HTTP_200_OK

    def test_start_autopilot_with_invalid_model_path(self):
        client = Client()
        data = dict()
        data["use_joystick"] = True
        data["model_path"] = str(Path(settings.MODEL_DIR) / "job_120.h5")

        with patch('dkconsole.vehicle.vehicle_service.VehicleService.start_autopilot') as mock_method:
            response = client.post(
                reverse('vehicle:start_autopilot'),
                data=json.dumps(data),
                content_type='application/json'
            )
            # mock_method.assert_called_once()

        assert response.status_code, status.HTTP_200_OK

    @pytest.mark.slow
    def test_start_driving_with_meta(self):
        client = Client()
        data = dict()
        data["use_joystick"] = True
        data["tub_meta"] = ["aaaa:bbbb", "x:1", "y:2"]

        response = client.post(
            reverse('vehicle:start_driving'),
            data=json.dumps(data),
            content_type='application/json'
        )

        time.sleep(3)
        response = client.post(
            reverse('vehicle:stop_driving'),
            content_type='application/json'
        )

    def test_update(self):
        client = Client()

        with patch('dkconsole.vehicle.vehicle_service.VehicleService.update_donkey_software') as mock_method:
            response = client.post(
                reverse('vehicle:update'),
            )
            mock_method.assert_called_once()

        assert response.status_code, status.HTTP_200_OK

    def test_add_network(self):
        client = Client()

        with patch('dkconsole.vehicle.vehicle_service.VehicleService.add_network') as mock_method:
            response = client.post(
                reverse('vehicle:add_network'),
            )
            mock_method.assert_called_once()

        assert response.status_code == status.HTTP_200_OK

    def test_finish_first_time_1(self):
        client = Client()
        data = dict()
        data["hostname"] = "some-hostname"
        data["ssid"] = "some-ssid"
        data["psk"] = "some-psk"

        with patch('dkconsole.vehicle.vehicle_service.VehicleService.first_time_finish') as mock_method:
            mock_method.side_effect = Exception('Boom!')
            response = client.post(
                reverse('vehicle:finish_first_time'),
                data=json.dumps(data),
                content_type='application/json'
            )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data['error_msg'] == "Boom!"

    def test_finish_first_time_2(self):

        client = Client()
        data = dict()
        data["hostname"] = "some-hostname"
        data["ssid"] = "some-ssid"
        data["psk"] = "some-psk"

        with patch('dkconsole.vehicle.vehicle_service.VehicleService.first_time_finish') as mock_method:
            Vehicle.reboot_required = True
            response = client.post(
                reverse('vehicle:finish_first_time'),
                data=json.dumps(data),
                content_type='application/json'
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['reboot'] == True

        with patch('dkconsole.vehicle.vehicle_service.VehicleService.first_time_finish') as mock_method:
            VehicleService.reboot_required = False
            response = client.post(
                reverse('vehicle:finish_first_time'),
                data=json.dumps(data),
                content_type='application/json'
            )

        assert response.status_code == status.HTTP_200_OK
        assert response.data['reboot'] == False
