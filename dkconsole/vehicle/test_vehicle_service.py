import pytest
import subprocess
import netifaces
import re

from .vehicle_service import VehicleService
from django.conf import settings


from unittest.mock import MagicMock
from unittest.mock import patch, ANY
from django.test import TestCase
import time
import datetime
import os


class MockProc():
    pid = None


class TestVehicleServiceUnit(TestCase):
    def setUp(self):
        self.vehicle_service = VehicleService

        self.vehicle_service.proc = None
        self.mock_proc = MockProc()
        self.mock_proc.pid = 999
        self.test_data_dir = settings.ROOT_DIR / "dkconsole" / "mycar_test"

    def test_settings(self):
        assert self.vehicle_service.carapp_path == str(self.test_data_dir)
        assert type(self.vehicle_service.carapp_path) is str
        assert self.vehicle_service.venv_path is not None

    @patch('subprocess.Popen')
    def test_start_driving_without_js(self, popen):
        popen.return_value = self.mock_proc

        val = self.vehicle_service.start_driving(False)
        popen.assert_called_with([f"{self.vehicle_service.venv_path}/python", self.vehicle_service.carapp_path +
                                  "/manage.py", "drive"], stdout=ANY)
        assert val == 999

    def test_drive_log(self):
        assert self.vehicle_service.drive_log() is not None

    @patch('subprocess.Popen')
    def test_start_driving_with_js(self, popen):
        popen.return_value = self.mock_proc

        val = self.vehicle_service.start_driving(True)

        popen.assert_called_with([f"{self.vehicle_service.venv_path}/python", self.vehicle_service.carapp_path +
                                  "/manage.py", "drive", "--js"], stdout=ANY)
        assert val == 999

    @patch('subprocess.Popen')
    def test_start_autopilot(self, popen):
        with self.assertRaises(FileNotFoundError) as context:
            val = self.vehicle_service.start_autopilot(True, "some_non_exist_model_path")

        model_path = settings.MODEL_DIR / "job_118"

        val = self.vehicle_service.start_autopilot(True, model_path)
        popen.assert_called_with([f"{self.vehicle_service.venv_path}/python", self.vehicle_service.carapp_path + "/manage.py",
                                  "drive", "--js", f"--model={model_path}"])

    @patch('subprocess.check_output')
    def test_get_current_ssid(self, check_output):
        check_output.side_effect = [
            'wlo1      IEEE 802.11  ESSID:"DONKEY01"',
            'wlo1      No such device'
        ]

        ssid = self.vehicle_service.get_current_ssid()
        assert ssid == "DONKEY01"

        ssid = self.vehicle_service.get_current_ssid()
        assert ssid is None

    @patch('netifaces.interfaces')
    @patch('netifaces.ifaddresses')
    def test_get_ip_address(self, ifaddresses, interfaces):
        netifaces.interfaces.side_effect = [['wlo1'], ['wlo1'], ['wlo1']]
        ifaddresses.side_effect = [
            {},
            {
                netifaces.AF_LINK: [{'addr': 'a0:51:0b:61:de:e2', 'broadcast': 'ff:ff:ff:ff:ff:ff'}]
            },
            {
                netifaces.AF_LINK: [{'addr': 'a0:51:0b:61:de:e2', 'broadcast': 'ff:ff:ff:ff:ff:ff'}],
                netifaces.AF_INET: [{'addr': '192.168.3.2', 'netmask': '255.255.255.0', 'broadcast': '192.168.3.255'}]
            }
        ]

        ip_address = self.vehicle_service.get_wlan_ip_address()
        assert ip_address is None

        ip_address = self.vehicle_service.get_wlan_ip_address()
        assert ip_address is None

        ip_address = self.vehicle_service.get_wlan_ip_address()
        assert ip_address == "192.168.3.2"

    @patch('netifaces.interfaces')
    @patch('netifaces.ifaddresses')
    def test_get_mac_address(self, ifaddresses, interfaces):
        netifaces.interfaces.side_effect = [['wlo1'], ['wlo1']]
        ifaddresses.side_effect = [
            {},
            {
                netifaces.AF_LINK: [{'addr': 'a0:51:0b:61:de:e2', 'broadcast': 'ff:ff:ff:ff:ff:ff'}]
            }
        ]

        mac_address = self.vehicle_service.get_wlan_mac_address()
        assert mac_address is None

        mac_address = self.vehicle_service.get_wlan_mac_address()
        assert mac_address == "a0:51:0b:61:de:e2"

    @patch('netifaces.interfaces')
    @patch('netifaces.ifaddresses')
    def test_is_wlan_connected(self, ifaddresses, interfaces):
        netifaces.interfaces.side_effect = [['wlo1'], ['wlo1'], ['wlo1']]
        ifaddresses.side_effect = [
            {},
            {
                netifaces.AF_LINK: [{'addr': 'a0:51:0b:61:de:e2', 'broadcast': 'ff:ff:ff:ff:ff:ff'}]
            },
            {
                netifaces.AF_LINK: [{'addr': 'a0:51:0b:61:de:e2', 'broadcast': 'ff:ff:ff:ff:ff:ff'}],
                netifaces.AF_INET: [{'addr': '192.168.3.2', 'netmask': '255.255.255.0', 'broadcast': '192.168.3.255'}]
            }

        ]

        # Empty address returned
        assert self.vehicle_service.is_wlan_connected() is False

        # IP address missing
        assert self.vehicle_service.is_wlan_connected() is False

        # IP address present
        assert self.vehicle_service.is_wlan_connected() is True

    # def test_is_wlan_connected(self):

    #     assert self.vehicle_service.is_wlan_connected() == True
    #     # assert self.vehicle_service.is_wlan_connected() == True

    @patch('subprocess.Popen')
    def test_update_console_software(self, mock_check_output):
        self.vehicle_service.update_console_software()

    def test_remove_all_network(self):
        with patch('subprocess.Popen') as mock_popen:
            with patch('subprocess.check_output') as mock_check_output:
                self.vehicle_service.remove_all_network()

                mock_popen.assert_called_once()
                assert mock_check_output.call_count == 3

    # TODO: Fix mock

    def test_sync_time(self):
        current = datetime.datetime.now()
        print(current)
        with patch('subprocess.check_output', return_value=current) as mock_method:
            result = self.vehicle_service.sync_time(current)
            mock_method.assert_called_once()
            assert result == current

    def test_first_time_finish(self):
        hostname = None
        ssid = None
        psk = None

        with patch('dkconsole.vehicle.vehicle_service.VehicleService.write_setup_file_to_disk') as mock_write_setup_file_to_disk:
            self.vehicle_service.first_time_finish(hostname, ssid, psk, None, None)
            mock_write_setup_file_to_disk.assert_called_once()
            assert self.vehicle_service.reboot_required is False

        hostname = "abcd1234"
        ssid = None
        psk = None

        with patch('dkconsole.vehicle.vehicle_service.VehicleService.set_hostname') as mock_set_hostname:
            with patch('dkconsole.vehicle.vehicle_service.VehicleService.write_setup_file_to_disk') as mock_write_setup_file_to_disk:
                self.vehicle_service.first_time_finish(hostname, ssid, psk, None, None)
                mock_set_hostname.assert_called_once()
                mock_write_setup_file_to_disk.assert_called_once()
                assert self.vehicle_service.reboot_required is True

        hostname = None
        ssid = "ssid1234"
        psk = "psk1234"

        with patch('dkconsole.vehicle.vehicle_service.VehicleService.add_network', return_value=True) as mock_add_network:
            with patch('dkconsole.vehicle.vehicle_service.VehicleService.write_setup_file_to_disk') as mock_write_setup_file_to_disk:
                self.vehicle_service.first_time_finish(hostname, ssid, psk, None, None)
                mock_add_network.assert_called_once()
                mock_write_setup_file_to_disk.assert_called_once()
                assert self.vehicle_service.reboot_required is True

    def test_update_host_table(self):
        path = self.test_data_dir / "hosts"
        sudo_required = False
        return_value = path, sudo_required

        with patch('dkconsole.vehicle.vehicle_service.VehicleService.host_table_path', return_value=return_value):
            self.vehicle_service.update_host_table("testing123")
            with open(path, 'r') as f:
                output = f.readlines()
                assert "127.0.1.1\ttesting123\n" in output

    def test_update_env(self):
        config_data = {"CARAPP_PATH": "/home/pi/mycar_mm1"}
        path = settings.CONSOLE_DIR + "/.env_pi4"
        self.vehicle_service.edit_env(path, config_data)
        with open(path, 'r') as f:
            check = re.search('CARAPP_PATH=/home/pi/mycar_mm1', f.read())
            assert check.group() == 'CARAPP_PATH=/home/pi/mycar_mm1'

    def test_flatten_config_map(self):
        result = self.vehicle_service.flatten_config_map()
        assert result['STEERING_LEFT_PWM']['dtype'] == "int" or result['STEERING_LEFT_PWM']['dtype'] == "mc"

    def test_scan_network(self):
        with patch('subprocess.check_output') as mock_method:
            mock_method.return_value = b'signal\nWLAN01\nWLAN02\nWLAN03\n'

            networks = self.vehicle_service.scan_network()
            assert networks == ['WLAN01', 'WLAN02', 'WLAN03']

    def test_list_network(self):
        output = b"0\tProactive_JBB_Guest\tany\t\n1\tPROACTIVE_JBB_5G\tany\t\n2\tPROACTIVE_JBB_5G\tany\t\n3\trobocar\tany\t\n4\trobocar\tany\t\n"

    def test_remove_network(self):
        output = []
        output.append({'id': 'ssid1', 'network': '0'})
        output.append({'id': 'ssid2', 'network': '1'})
        output.append({'id': 'robocar', 'network': '2'})
        output.append({'id': 'robocar', 'network': '3'})

        with patch('dkconsole.vehicle.vehicle_service.VehicleService.list_network', return_value=output) as mock_add_network:
            with patch('subprocess.check_output') as mock_method:
                self.vehicle_service.remove_network("robocar")
                assert mock_method.call_count == 2

    @patch('subprocess.check_output')
    def test_reset_config(self, mock_check_output):
        self.vehicle_service.reset_config()

        mock_check_output.assert_called_with(['sudo', 'cp', ANY, ANY])

    def test_get_config(self):
        self.vehicle_service.read_value_from_config(self.vehicle_service.config())

    def test_extract_value_from_config_line(self):
        config_path = self.vehicle_service.carapp_path + "/config.py"
        myconfig_path = self.vehicle_service.carapp_path + "/myconfig.py"

        with open(myconfig_path, 'r') as f_config:
            with open(myconfig_path, 'r') as f_myconfig:
                config_content = f_config.readlines()
                myconfig_content = f_myconfig.readlines()

                assert self.vehicle_service.extract_value_from_config_line(
                    config_content, 'MM1_STEERING_MID') is not None

                assert self.vehicle_service.extract_value_from_config_line(
                    myconfig_content, 'MM1_STEERING_MID') is not None

    def test_replace_key_in_lines(self):
        content = '''#DRIVE_TRAIN_TYPE = "MM1"
# DRIVE_TRAIN_TYPE = "MM1"
DRIVE_TRAIN_TYPE = "MM1"
'''

        assert self.vehicle_service.replace_key_in_lines(content.splitlines(), 'DRIVE_TRAIN_TYPE', 'DRIVE_TRAIN_TYPE = "ABC"') == [
            'DRIVE_TRAIN_TYPE = "ABC"',
            'DRIVE_TRAIN_TYPE = "ABC"',
            'DRIVE_TRAIN_TYPE = "ABC"'
        ]

        content = '#DRIVE_TRAIN_TYPE = "MM1"'
        assert self.vehicle_service.replace_key_in_lines(content.splitlines(), 'DRIVE_TRAIN_TYPE', 'DRIVE_TRAIN_TYPE = "ABC"') == [
            'DRIVE_TRAIN_TYPE = "ABC"'
        ]

        content = '#DRIVE_TRAIN_TYPE = "MM1"'
        assert self.vehicle_service.replace_key_in_lines(content.splitlines(), 'STEERING_RIGHT_PWM', 'STEERING_RIGHT_PWM = 123') == [
            '#DRIVE_TRAIN_TYPE = "MM1"',
            'STEERING_RIGHT_PWM = 123',
        ]

    def test_replace_all_keys_in_lines(self):
        content = '''#DRIVE_TRAIN_TYPE = "MM1"
# DRIVE_TRAIN_TYPE = "MM1"
DRIVE_TRAIN_TYPE = "MM1"'''

        config_data = {'DRIVE_TRAIN_TYPE': 'hahah', 'STEERING_RIGHT_PWM': 'hahah2'}
        flattened_map = self.vehicle_service.flatten_config_map()
        assert self.vehicle_service.replace_all_keys_in_lines(content.splitlines(), config_data, flattened_map) == [
            'DRIVE_TRAIN_TYPE = "hahah"\n',
            'DRIVE_TRAIN_TYPE = "hahah"\n',
            'DRIVE_TRAIN_TYPE = "hahah"\n',
            'STEERING_RIGHT_PWM = hahah2\n',
        ]

    def test_update_config(self):
        path = self.test_data_dir / "myconfig.py"

        with open(path, 'r') as f:
            content = self.vehicle_service.file_readlines(f)
            print(content)

        config_data = {"DRIVE_TRAIN_TYPE": "SERVO_ESC"}

        with patch("builtins.open") as mock_file:
            with patch('dkconsole.vehicle.vehicle_service.VehicleService.file_readlines', return_value=content) as mock_file_readlines:
                with patch('dkconsole.vehicle.vehicle_service.VehicleService.file_writelines') as mock_file_writelines:
                    with patch('dkconsole.vehicle.vehicle_service.VehicleService.flatten_config_map') as mock_flatten_config_map:

                        mock_flatten_config_map.return_value = {
                            "DRIVE_TRAIN_TYPE": {"dtype": "mc", "choices": ['SERVO_ESC', 'MM1']}
                        }

                        test = self.vehicle_service.flatten_config_map()

                        self.vehicle_service.update_config(config_data)
                        mock_file_readlines.assert_called_once()
                        mock_file_writelines.assert_called_once()
                        found = False

                        for line in mock_file_writelines.call_args_list[0][0][1]:
                            if 'DRIVE_TRAIN_TYPE = "SERVO_ESC"' in line:
                                found = True

                        assert found

    def test_battery_level_in_percentage(self):
        # TODO: Should test this
        # Need to solve how to mock import because adafruit_ina219 isn't available on pc
        # assert None == self.vehicle_service.battery_level_in_percentage()
        pass

    def test_calculate_battery_percentage(self):
        assert 100 == self.vehicle_service.calculate_battery_percentage(8.4)
        assert 50 == self.vehicle_service.calculate_battery_percentage(7.7)
        assert 0 == self.vehicle_service.calculate_battery_percentage(7)
        assert -7 == self.vehicle_service.calculate_battery_percentage(6.9)
