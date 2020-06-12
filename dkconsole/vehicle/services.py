import errno
import fileinput
import json
import os
import re
import signal
import socket
import subprocess
import time
from pathlib import Path

import netifaces
from django.conf import settings

from dkconsole.model.services import MLModelService


class Vehicle(object):
    # def __init__(self, **kwargs):
    #     for field in ('id', 'name', 'owner', 'status'):
    #         setattr(self, field, kwargs.get(field, None))

    pid = None
    carapp_path = settings.CARAPP_PATH
    venv_path = settings.VENV_PATH
    proc = None
    calibrate_proc = None
    reboot_required = False



    @classmethod
    def build_calibrate_command(cls):
        command = [f"{cls.venv_path}/python", f"{cls.carapp_path}/calibrate.py".format(cls.carapp_path), "drive"]

        print(" ".join(command))

        return command


    @classmethod
    def build_drive_command(cls, use_joystick, model_path, tub_meta=None):
        command = [f"{cls.venv_path}/python", f"{cls.carapp_path}/manage.py".format(cls.carapp_path), "drive"]

        if use_joystick:
            command.append("--js")

        if model_path:
            command.append(f"--model={model_path}")

        if tub_meta is not None:
            for i in tub_meta:
                command.append(f"--meta={i}")
                # ["x:y", "s:z"] => --meta=x:y --meta=s:z

        print(" ".join(command))

        return command

    @classmethod
    def drive_log(cls):
        data = ""
        with open(cls.carapp_path + "/drive.log", 'r') as log:
            data = log.read()

        return data

    @classmethod
    def start_calibrate(cls):
        if cls.calibrate_proc is not None:
            cls.stop_calibrate()

        print("start calibrate")
        command = cls.build_calibrate_command()

        cls.calibrate_proc = subprocess.Popen(command)

        return cls.calibrate_proc

    @classmethod
    def stop_calibrate(cls):
        if cls.calibrate_proc is not None:
            print("stop calibrate: sending SIGINT")
            cls.calibrate_proc.send_signal(signal.SIGINT)
            cls.calibrate_proc = None
        else:
            print("stop calibrate: No proc found. Cannot send stop driving signal")

    @classmethod
    def start_driving(cls, use_joystick, tub_meta=None):
        if cls.proc is not None:
            cls.stop_driving()

        print("start driving")
        command = cls.build_drive_command(use_joystick, None, tub_meta)

        with open(cls.carapp_path + "/drive.log", 'w') as log:
            cls.proc = subprocess.Popen(command, stdout=log)
            print(f"cls.proc = {cls.proc}")

        return cls.proc.pid

    @classmethod
    def stop_driving(cls):
        if cls.proc is not None:
            print("stop driving: sending SIGINT")
            cls.proc.send_signal(signal.SIGINT)
            cls.proc = None
        else:
            print("stop driving: No proc found. Cannot send stop driving signal")

    @classmethod
    def start_autopilot(cls, use_joystick, model_path, tub_meta=None):
        if cls.proc is not None:
            cls.stop_driving()

        if MLModelService.model_exists(model_path):
            command = cls.build_drive_command(use_joystick, model_path, tub_meta)

            cls.proc = subprocess.Popen(command)
            return cls.proc.pid
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), model_path)

    @classmethod
    def get_hostname(cls):
        return socket.gethostname()

    @classmethod
    def get_current_ssid(cls):
        try:
            output = str(subprocess.check_output(['/sbin/iwconfig', settings.WLAN]))
            m = re.search('ESSID:"(.*)"', output)

            if m is None:
                return None
            else:
                return m.group(1)
        except:
            return "OS not support"

    @classmethod
    def get_wlan_ip_address(cls):
        addrs = cls.get_addrs(settings.WLAN)

        if (netifaces.AF_INET in addrs) and (len(addrs[netifaces.AF_INET]) == 1):
            return addrs[netifaces.AF_INET][0]['addr']
        else:
            return None

    @classmethod
    def get_wlan_mac_address(cls):
        addrs = cls.get_addrs(settings.WLAN)

        if (netifaces.AF_LINK in addrs) and (len(addrs[netifaces.AF_LINK]) == 1):
            return addrs[netifaces.AF_LINK][0]['addr']
        else:
            return None

    @classmethod
    def is_wlan_connected(cls):
        addrs = cls.get_addrs(settings.WLAN)

        if netifaces.AF_INET in addrs:
            return True
        else:
            return False

    @classmethod
    def is_hotspot_on(cls):
        addrs = cls.get_addrs(settings.HOTSPOT_IF_NAME)

        if netifaces.AF_INET in addrs:
            return True
        else:
            return False

    @classmethod
    def get_hotspot_ip_address(cls):
        addrs = cls.get_addrs(settings.HOTSPOT_IF_NAME)

        if (netifaces.AF_INET in addrs) and (len(addrs[netifaces.AF_INET]) == 1):
            return addrs[netifaces.AF_INET][0]['addr']
        else:
            return None

    @classmethod
    def get_addrs(cls, interface):
        interfaces = netifaces.interfaces()

        if interface not in interfaces:
            raise Exception(f"Network interface is not properly configured. {interface} does not exists.")

        return netifaces.ifaddresses(interface)

    @classmethod
    def update_donkey_software(cls):
        verbose = subprocess.check_output(['git', 'pull'], cwd=settings.DONKEYCAR_DIR)
        command = [f"{cls.venv_path}/donkey createcar --path {settings.CARAPP_PATH} --overwrite"]
        verbose = subprocess.check_output(command, shell=True)
        output = verbose.decode('utf-8')
        return output

    @classmethod
    def update_console_software(cls):
        verbose = subprocess.check_output(['git', 'pull'], cwd=settings.CONSOLE_DIR)
        subprocess.Popen(['sleep 2 ; sudo service gunicorn restart'], shell=True)
        output = verbose.decode('utf-8')
        return output

    @classmethod
    def add_network(cls, ssid, password):
        try:
            print(f"adding network {ssid} {password}")
            cls.remove_network(ssid)

            existing_networks = cls.list_network()
            for network in existing_networks:
                subprocess.check_output(['wpa_cli', 'set_network', network['network'], 'priority', '1'])

            test = subprocess.check_output(['wpa_cli', 'add_network'])
            id = test.decode('utf-8')
            id = id.splitlines()[1]

            # Add network to wpa_supplicant
            output = subprocess.check_output(['wpa_cli', 'set_network', f'{id}', 'ssid', f'"{ssid}"'])
            output = subprocess.check_output(['wpa_cli', 'set_network', f'{id}', 'psk', f'"{password}"'])
            output = subprocess.check_output(['wpa_cli', 'set_network', f'{id}', 'priority', '2'])

            # Enable and save the config to file
            output = subprocess.check_output(['wpa_cli', 'enable_network', f'{id}'])
            output = subprocess.check_output(['wpa_cli', 'save_config'])

            # Ask wpa client to force reconnect based on the config file
            output = subprocess.check_output(['wpa_cli', 'reconfigure', '-i', 'wlan0'])

            for i in range(5):
                subprocess.check_output(['sleep', '2'])
                current_ssid = cls.get_current_ssid()
                if (ssid == current_ssid):
                    output = subprocess.Popen(['sleep 2 ; sudo systemctl stop hostapd.service'], shell=True)
                    return True
                else:
                    print(f"current ssid = {current_ssid}")
            cls.remove_network(ssid)
            return False
        except Exception as e:
            print(e)

    # TODO: Deprecated, to be deleted
    # @classmethod
    # def reset_network(cls, wipe):
    #     try:
    #         if (wipe is True):
    #             subprocess.check_output(
    #                 ['sudo', 'cp', '/home/pi/donkeycar-images/resources/wpa_supplicant.empty.conf', '/boot/wpa_supplicant.conf'])
    #             subprocess.Popen(['sleep 3 ; sudo reboot'], shell=True)
    #         else:
    #             subprocess.check_output(
    #                 ['sudo', 'cp', '/home/pi/donkeycar-images/resources/wpa_supplicant.test.conf', '/boot/wpa_supplicant.conf'])
    #             subprocess.Popen(['sleep 3 ; sudo reboot'], shell=True)
    #     except Exception as e:
    #         print(e)

    @classmethod
    def list_network(cls):
        '''
        Return list of network
        [{"network": 0, id:"ssid1"}, {"network": 1, id:"ssid2"}]
        '''
        import csv
        output = subprocess.check_output(['wpa_cli list_network | tail +3 '], shell=True)   # First two lines are header, tail to skip them

        networks = csv.DictReader(output.decode('ascii').splitlines(),
                        delimiter='\t', skipinitialspace=True,
                        fieldnames=['network', 'id',
                                    '/'])

        return networks


    @classmethod
    def remove_network(cls, ssid):
        networks = cls.list_network()

        for network in networks:
            print(f"{network} , network = {network['network']} \t, id = {network['id']}")
            if network['id'] == ssid:
                print(f"removing network {network['network']}")
                subprocess.check_output(['wpa_cli', 'remove_network', network['network']])


    @classmethod
    def remove_all_network(cls):
        subprocess.check_output(['wpa_cli', 'remove_network', 'all'])
        subprocess.check_output(['wpa_cli', 'save_config'])
        subprocess.check_output(['wpa_cli', 'reconfigure', '-i', 'wlan0'])

        subprocess.Popen(['sudo /etc/raspap/hostapd/servicestart.sh --interface uap0 --seconds 3'], shell=True)


    @classmethod
    def reboot(cls):
        subprocess.Popen(['sleep 3 ; sudo reboot'], shell=True)

    @classmethod
    def edit_hostname(cls, hostname, path):
        if (os.path.exists(path)):
            with open(path, 'r') as f:
                newHostname = re.sub(f"(127\.0\.1\.1)\s*.*\n*", f"127.0.1.1 {hostname}", f.read())
                f.close
                output = open(path, 'w')
                output.seek(0)
                output.write(newHostname)
                output.close

    @classmethod
    def set_hostname(cls, hostname):
        subprocess.check_output(['sudo', 'hostnamectl', 'set-hostname', f'{hostname}'])
        hosts = "/etc/hosts"
        cls.edit_hostname(hostname, hosts)

    @classmethod
    def first_time(cls):
        path = cls.carapp_path + "/setup.json"
        if (os.path.exists(path)):
            with open(path, 'r') as f:
                data = json.load(f)
                return data['isFirstTime']
        else:
            with open(path, 'w+') as f:
                output = {}
                output['isFirstTime'] = True
                json.dump(output, f)
                return True

    @classmethod
    def write_setup_file_to_disk(cls):
        path = cls.carapp_path + "/setup.json"
        with open(path, 'w+') as f:
            output = {}
            output['isFirstTime'] = False
            json.dump(output, f)

    @classmethod
    def first_time_finish(cls, hostname, ssid, psk, controller):
        if controller is not None:
            cls.update_config(controller)

        if ssid is not None:
            wifi = cls.add_network(ssid, psk)
            if wifi is not True:
                raise Exception("Cannot connect to wifi")
            cls.reboot_required = True

        if hostname is not None:
            cls.set_hostname(hostname)
            cls.reboot_required = True

        cls.write_setup_file_to_disk()

        return True

    @classmethod
    def scan_network(cls):
        print("Scanning network")
        subprocess.check_output(['wpa_cli', 'scan', '-i', 'wlan0'])
        results = subprocess.check_output(
            ["sleep 2 ; wpa_cli -i wlan0 scan_results | awk '{ print $5 }'"], shell=True)
        print(results)

        available_networks = set()

        i = 0
        for line_bytes in results.splitlines():
            try:
                line_str = line_bytes.decode("ascii").replace(' ', '')

                if line_str and "\\" not in line_str and i != 0:       # Skip first, non-alphanumeric and empty string
                    available_networks.add(line_str)

                i += 1
            except Exception as e:
                print(e)
                pass

        return sorted(available_networks)

    @classmethod
    def changePasswd(cls, current, password):
        proc = subprocess.check_output(f'echo -n "{current}\n{password}\n{password}\n" | passwd pi', shell=True)
        print(proc)
        return proc

    @classmethod
    def replace_key_in_lines(cls, lines, key, replacement_line):
        replaced = False
        for idx, line in enumerate(lines):
            search = re.search(rf'^#*\s*{key}\s*=\s*(.*)$', line)

            if search is not None:
                lines[idx] = replacement_line
                replaced = True

        if replaced is False:
            lines.append(replacement_line)

        print(len(lines))
        return lines

    @classmethod
    def file_readlines(cls, f):
        ''' convenient method for unit testing patching '''
        lines = f.readlines()
        return lines

    @classmethod
    def file_writelines(cls, f, lines):
        ''' convenient method for unit testing patching '''
        f.writelines(lines)
        # f.writ


    @classmethod
    def replace_all_keys_in_lines(cls, lines, config_data, flattened_map):
        for key in config_data:
            if flattened_map[key]['dtype'] == "str" or flattened_map[key]['dtype'] == "mc":
                replacement_line = f'{key} = "{config_data[key]}"\n'
            else:
                replacement_line = f'{key} = {config_data[key]}\n'

            lines = cls.replace_key_in_lines(lines, key, replacement_line)

        return lines

    @classmethod
    def update_config(cls, config_data):
        path = cls.carapp_path + "/myconfig.py"
        with open(path, 'r') as f:
            lines = cls.file_readlines(f)
            flattened_map = cls.flatten_config_map()
            lines = cls.replace_all_keys_in_lines(lines, config_data, flattened_map)

        with open(path, 'w') as f:
            cls.file_writelines(f, lines)

    @classmethod
    def sync_time(cls, currentTime):
        result = subprocess.check_output(f"sudo date -s '{currentTime}'", shell=True)
        return result

    @classmethod
    def edit_env(cls, path, config_data):
        for key in config_data:
            with open(path, 'r') as f:
                if (not re.search(rf'(?m)^#*\s*({key}*)\s*=\s*(.*)\n', f.read())):
                    output = open(path, "a")
                    output.write(f'{key}={config_data[key]}\n')
                    output.close
                else:
                    f.seek(0)
                    newline = re.sub(rf'(?m)^#*\s*({key}*)\s*=\s*(.*)\n', f'{key}={config_data[key]}\n', f.read())
                    output = open(path, "w")
                    output.seek(0)
                    output.write(newline)
                    output.close

    @classmethod
    def update_env(cls, config_data):
        path = settings.CONSOLE_DIR + "/.env_pi4"
        cls.edit_env(path, config_data)
        subprocess.check_output(['sudo', 'service', 'gunicorn', 'restart'])

    @classmethod
    def config(cls):
        data = {
            "Controller": {
                "DRIVE_TRAIN_TYPE": {"value": "SERVO_ESC", "dtype": "mc", "choices": ['SERVO_ESC', 'MM1']}
            },
            "section 2": {
                    "STEERING_LEFT_PWM": {"value": 460, "dtype": "int", "default": 460},
                    "STEERING_RIGHT_PWM": {"value": 290, "dtype": "int", "default": 290},
                    "THROTTLE_FORWARD_PWM": {"value": 500, "dtype": "int", "default": 500},
                    "THROTTLE_REVERSE_PWM": {"value": 220, "dtype": "int", "default": 220},
                    "MM1_STEERING_MID": {"value": 1500, "dtype": "int", "default": 1500},
                    "MM1_MAX_FORWARD": {"value": 2000, "dtype": "int", "default": 2000},
                    "MM1_MAX_REVERSE": {"value": 1000, "dtype": "int", "default": 1000},
            }
        }

        data = cls.read_value_from_config(data)

        return data


    @classmethod
    def is_number(cls, s):
        try:
            float(s)
            return True
        except ValueError:
            return False

    @classmethod
    def to_num(cls, s):
        try:
            return int(s)
        except ValueError:
            return float(s)

    @classmethod
    def extract_value_from_config_line(cls, lines, key):
        value = None

        for line in lines:
            search = re.search(rf'^#*\s*{key}\s*=\s*([^#]*)#*.*$', line)

            if search and search.groups():
                value_str = re.sub(r'["\s]', "", search.groups()[0])
                if cls.is_number(value_str):
                    value = cls.to_num(value_str)
                else:
                    value = value_str

        return value


    @classmethod
    def read_value_from_config(cls, config):
        config_path = cls.carapp_path + "/config.py"
        myconfig_path = cls.carapp_path + "/myconfig.py"

        with open(config_path, 'r') as f_config:
            with open(myconfig_path, 'r') as f_myconfig:
                config_content = f_config.readlines()
                myconfig_content = f_myconfig.readlines()

                for section_name in config.keys():
                    for config_name in config[section_name].keys():
                        value = cls.extract_value_from_config_line(myconfig_content, config_name)

                        if value is None:
                            value = cls.extract_value_from_config_line(config_content, config_name)
                            if value is None:
                                raise Exception(f"Cannot find default value for {config_name} ")

                        else:
                            config[section_name][config_name]['value'] = value

        return config

    @classmethod
    def flatten_config_map(cls):
        first_level_keys = list()
        second_level_keys = list()
        data = cls.config()
        result = dict()
        for first_level_key in data.keys():
            for key in data[first_level_key].keys():
                item = data[first_level_key][key]
                result[key] = item
        return result

    @classmethod
    def reset_config(cls):
        subprocess.check_output(
                    ['sudo', 'cp', '/opt/donkeycar-images/resources/myconfig.py', f'{cls.carapp_path}/myconfig.py'])
        return True

    @classmethod
    def power_off(cls):
        subprocess.check_output(['sudo', 'shutdown', '-h', 'now'])
