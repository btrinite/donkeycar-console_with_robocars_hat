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
import logging
import donkeycar
from packaging import version

from django.conf import settings

from dkconsole.model.services import MLModelService

logger = logging.getLogger(__name__)


class VehicleService():

    '''
    This is a base class of all vehicle service. Strictly speaking, this is not an interface, it is ok to put
    implementation here for reusability.

    1. Reusable method should be put in this class
    2. Concrete class should implement their specific implementation in their own class

    If we don't have this class, we can't:
    1. Code cannot auto-complete in IDE
    2. Cannot re-use method that all concrete shall same implementation

    '''

    MODE_DOCKER = "docker"

    pid = None
    carapp_path: str = settings.CARAPP_PATH
    venv_path = settings.VENV_PATH
    proc = None
    calibrate_proc = None
    reboot_required = False
    mode = settings.MODE
    web_controller_port = 8887

    @classmethod
    def get_donkeycar_version(cls):
        donkeycar_version = version.parse(donkeycar.__version__)
        logger.debug(f"donkeycar_version = {donkeycar_version}")

        return donkeycar_version

    @classmethod
    def get_donkeycar_major_version(cls):
        donkeycar_version = cls.get_donkeycar_version()
        return donkeycar_version.major

    @classmethod
    def build_calibrate_command(cls):
        command = [f"{cls.venv_path}/python", f"{cls.carapp_path}/calibrate.py", "drive"]

        logger.debug(" ".join(command))

        return command

    @classmethod
    def build_drive_command(cls, use_joystick, model_path, tub_meta=None):
        command = [f"{cls.venv_path}/python", f"{cls.carapp_path}/manage.py", "drive"]

        if (cls.get_donkeycar_major_version() == 3):
            if tub_meta is not None:
                for i in tub_meta:
                    command.append(f"--meta={i}")
                    # ["x:y", "s:z"] => --meta=x:y --meta=s:z

        if use_joystick:
            command.append("--js")

        if model_path:
            command.append(f"--model={model_path}")

        logger.debug(" ".join(command))

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

        if cls.mode == cls.MODE_DOCKER:
            cls.proc = subprocess.Popen(command)
        else:
            with open(cls.carapp_path + "/drive.log", 'w') as log:
                cls.proc = subprocess.Popen(command, stdout=log)

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

        if addrs is None:
            return None

        if (netifaces.AF_INET in addrs) and (len(addrs[netifaces.AF_INET]) == 1):
            return addrs[netifaces.AF_INET][0]['addr']
        else:
            return None

    @classmethod
    def get_wlan_mac_address(cls):
        if (cls.mode == cls.MODE_DOCKER):
            return "docker"

        addrs = cls.get_addrs(settings.WLAN)

        if addrs is None:
            return None

        if (netifaces.AF_LINK in addrs) and (len(addrs[netifaces.AF_LINK]) == 1):
            return addrs[netifaces.AF_LINK][0]['addr']
        else:
            return None

    @classmethod
    def is_wlan_connected(cls):
        addrs = cls.get_addrs(settings.WLAN)

        if addrs is None:
            return False

        if netifaces.AF_INET in addrs:
            return True
        else:
            return False

    @classmethod
    def is_hotspot_on(cls):
        addrs = cls.get_addrs(settings.HOTSPOT_IF_NAME)

        if addrs is None:
            return False

        if netifaces.AF_INET in addrs:
            return True
        else:
            return False

    @classmethod
    def get_hotspot_ip_address(cls):
        addrs = cls.get_addrs(settings.HOTSPOT_IF_NAME)

        if addrs is None:
            return None

        if (netifaces.AF_INET in addrs) and (len(addrs[netifaces.AF_INET]) == 1):
            return addrs[netifaces.AF_INET][0]['addr']
        else:
            return None

    @classmethod
    def get_addrs(cls, interface):
        interfaces = netifaces.interfaces()

        if interface not in interfaces:
            # logger.error(f"Network interface is not properly configured. {interface} does not exists.")
            return None

        return netifaces.ifaddresses(interface)

    @classmethod
    def update_donkey_software(cls):
        try:
            verbose = subprocess.check_output(['git', 'pull'], cwd=settings.DONKEYCAR_DIR)
        except Exception as e:
            logging.exception(e)
        command = [f"{cls.venv_path}/donkey createcar --path {settings.CARAPP_PATH} --overwrite"]
        verbose = subprocess.check_output(command, shell=True)
        output = verbose.decode('utf-8')
        return output

    @classmethod
    def update_console_software(cls):
        try:
            # gunicorn service runs git pull upon restart
            output = subprocess.Popen(['sleep 2 ; sudo service gunicorn restart'], shell=True, stdout=subprocess.PIPE)
            stdout = output.communicate()[0].decode('utf-8')
        except Exception as e:
            print(e)
        return stdout

    @classmethod
    def set_wpa_country(cls, country_code):
        try:
            subprocess.check_output(['wpa_cli', 'set', f'country={country_code}'])
            output = subprocess.check_output(['wpa_cli', 'save_config'])
        except Exception as e:
            logger.error("Cannot set wpa_cli country", e)

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
                subprocess.check_output(['sleep', '3'])
                current_ssid = cls.get_current_ssid()
                if (ssid == current_ssid):
                    logger.info("Wifi connected. Shutting down hotstop")
                    # Delay shutting down the hotspot so that mobile client can receive the http response
                    output = subprocess.Popen(['sleep 10 ; sudo systemctl stop hostapd.service'], shell=True)
                    return True
                else:
                    logger.info(f"current ssid = {current_ssid}")
            cls.remove_network(ssid)
            return False
        except Exception as e:
            logger.info(e)

    @classmethod
    def list_network(cls):
        '''
        Return list of network
        [{"network": 0, id:"ssid1"}, {"network": 1, id:"ssid2"}]
        '''
        import csv
        # First two lines are header, tail to skip them
        output = subprocess.check_output(['wpa_cli list_network | tail +3 '], shell=True)

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
        print("rebooting in 3 seconds")
        subprocess.Popen(['sleep 3 ; sudo reboot'], shell=True)

    @classmethod
    def host_table_path(cls):
        sudo_required = True
        return "/etc/hosts", sudo_required

    @classmethod
    def update_host_table(cls, hostname):
        try:
            host_table_path, sudo_required = cls.host_table_path()
            command = f'sed -i "s/127.0.1.1.*/127.0.1.1\t{hostname}/g" {host_table_path}'

            if sudo_required:
                command = 'sudo ' + command

            subprocess.check_output(command, shell=True)
        except Exception as e:
            print(f"failed to update host table. Reason: {e}")

    @classmethod
    def set_hostname(cls, hostname):
        subprocess.check_output(['sudo', 'hostnamectl', 'set-hostname', f'{hostname}'])
        cls.update_host_table(hostname)

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
    def first_time_finish(cls, hostname, ssid, psk, controller, country_code):
        if controller is not None:
            cls.update_config(controller)

        if country_code:
            logger.info("Setting wpa_country ${country_code}")
            cls.set_wpa_country(country_code)

        if ssid is not None:
            wifi = cls.add_network(ssid, psk)
            if wifi is not True:
                raise Exception("Cannot connect to wifi")

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
            ["sleep 5 ; wpa_cli -i wlan0 scan_results | awk '{ print $5 }'"], shell=True)
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

            print(f"flattedmap = {flattened_map}")
            lines = cls.replace_all_keys_in_lines(lines, config_data, flattened_map)

        with open(path, 'w') as f:
            cls.file_writelines(f, lines)

    @classmethod
    def sync_time(cls, currentTime):
        logger.debug("sync time")
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
        logger.debug("update_env")
        path = settings.CONSOLE_DIR + "/.env_pi4"
        cls.edit_env(path, config_data)
        subprocess.check_output(['sudo', 'service', 'gunicorn', 'restart'])

    @classmethod
    def config(cls):
        data = {
            "Basic": {
                "DRIVE_LOOP_HZ": {"dtype": "int", "default": 20},
                "AI_THROTTLE_MULT": {"value": 1.0, "dtype": "int", "default": 1.0},
            },
            "Controller": {
                "DRIVE_TRAIN_TYPE": {"dtype": "mc", "choices": ['SERVO_ESC', 'MM1']},
                "STEERING_LEFT_PWM": {"dtype": "int", "default": 460},
                "STEERING_RIGHT_PWM": {"dtype": "int", "default": 290},
                "THROTTLE_FORWARD_PWM": {"dtype": "int", "default": 500},
                "THROTTLE_REVERSE_PWM": {"dtype": "int", "default": 220},
                "MM1_STEERING_MID": {"dtype": "int", "default": 1500},
                "MM1_MAX_FORWARD": {"dtype": "int", "default": 2000},
                "MM1_MAX_REVERSE": {"dtype": "int", "default": 1000},
                "MM1_STOPPED_PWM": {"dtype": "int", "default": 1500}
            },
            "Camera": {
                "CAMERA_TYPE":  {
                    "dtype": "mc",
                    "choices": ['PICAM', 'WEBCAM', 'CSIC', 'MOCK']
                },
                "IMAGE_W": {"dtype": "int", "default": 160},
                "IMAGE_H": {"dtype": "int", "default": 120},
            },
            "Training": {
                "ROI_CROP_TOP": {"dtype": "int", "default": 0},
                "ROI_CROP_BOTTOM": {"dtype": "int", "default": 0},
                "DEFAULT_MODEL_TYPE": {
                    "dtype": "mc",
                    "choices": ['linear', 'categorical', 'rnn', 'imu', 'behavior', '3d', 'localizer', 'latent','tflite_linear']
                },
                "BATCH_SIZE": {"dtype": "int", "default": 128}
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
            ['sudo', 'cp', '/opt/donkeycar-console/dkconsole/vehicle/myconfig.py', f'{cls.carapp_path}/myconfig.py'])
        return True

    @classmethod
    def power_off(cls):
        subprocess.check_output(['sudo', 'shutdown', '-h', 'now'])

    @classmethod
    def reboot(cls):
        subprocess.check_output(['sudo', 'reboot', '-h', 'now'])

    @classmethod
    def factory_reset(cls):
        return True

    @classmethod
    def battery_level_in_percentage(cls):
        '''
        return int, perecentage of battery
        assume it is a 2 cell 8.4v lipo
        '''

        try:
            import board
            import busio
            import adafruit_ina219
            i2c = busio.I2C(board.SCL, board.SDA)
            ina219 = adafruit_ina219.INA219(i2c, 0x41)
            return cls.calculate_battery_percentage(ina219.bus_voltage)
        except Exception as e:
            print(e)
            return 0

    @classmethod
    def calculate_battery_percentage(cls, current_voltage):
        max_voltage = 8.4
        min_voltage = 7

        battery_level = int((current_voltage - min_voltage) / (max_voltage - min_voltage) * 100)

        return battery_level
        # print("Bus Voltage:   {} V".format())
        # print("Shunt Voltage: {} mV".format(ina219.shunt_voltage / 1000))
        # print("Current:       {} mA".format(ina219.current))

    @classmethod
    def get_web_controller_port(cls):
        try:
            config_path = f"{cls.carapp_path}/config.py"
            cfg = donkeycar.load_config(config_path=config_path)
            cls.web_controller_port = cfg.WEB_CONTROL_PORT
        except:
            pass

        return cls.web_controller_port
