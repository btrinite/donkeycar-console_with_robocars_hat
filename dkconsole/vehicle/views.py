from django.shortcuts import render
from django.http import HttpResponse, HttpResponseServerError
from rest_framework.response import Response
from rest_framework.decorators import api_view

from dkconsole.service_factory import factory

from django.conf import settings
from rest_framework import status
import time
import logging
from .vehicle_service import VehicleService

logger = logging.getLogger(__name__)
vehicle_service: VehicleService = factory.create('vehicle_service')


# Create your views here.
def index(request):
    return HttpResponse("Hello, world")

@api_view(['POST'])
def start_driving(request):
    '''
    tub_meta - a list of key:value
    ["x:y", "a:b"]
    '''
    use_joystick = request.data.get('use_joystick', False)
    tub_meta = request.data.get('tub_meta', None)

    vehicle_service.start_driving(use_joystick, tub_meta)
    return Response({"status": True})


@api_view(['POST'])
def start_autopilot(request):
    model_path = request.data['model_path']
    use_joystick = request.data['use_joystick']

    pid = vehicle_service.start_autopilot(use_joystick, model_path)

    return Response({"status": True})


@api_view(['POST'])
def stop_driving(request):
    vehicle_service.stop_driving()
    return Response({"status": True})


@api_view(['GET'])
def status(request):
    hostname = vehicle_service.get_hostname()
    carapp_path = vehicle_service.carapp_path

    return Response({"hostname": hostname,
                     "carapp_path": carapp_path,
                     "wlan_ip_address": vehicle_service.get_wlan_ip_address(),
                     "wlan_mac_address": vehicle_service.get_wlan_mac_address(),
                     "is_wlan_connected": vehicle_service.is_wlan_connected(),
                     "is_hotspot_on": vehicle_service.is_hotspot_on(),
                     "hotspot_ip_address": vehicle_service.get_hotspot_ip_address(),
                     "isFirstTime": vehicle_service.first_time(),
                     "current_ssid": vehicle_service.get_current_ssid(),
                     "battery_level": vehicle_service.battery_level_in_percentage(),
                     "web_controller_port": vehicle_service.get_web_controller_port(),
                     "donkeycar_version": str(vehicle_service.get_donkeycar_version())
                     })


@api_view(['POST'])
def update_console_software(request):
    try:
        return Response({"Output": vehicle_service.update_console_software(), "status": True})
    except:
        return HttpResponseServerError()

@api_view(['POST'])
def update_donkey_software(request):
    try:
        return Response({"Output": vehicle_service.update_donkey_software(), "status": True})
    except:
        return HttpResponseServerError()


@api_view(['POST'])
def add_network(request):
    ssid = request.data['ssid']
    password = request.data['password']
    try:
        return Response({"status": vehicle_service.add_network(ssid, password)})
    except:
        return Response({"status": "fail"})


@api_view(['POST'])
def reset_network(request):
    try:
        vehicle_service.remove_all_network()
        return Response({"status": "success"})
    except:
        return Response({"status": "fail"})


@api_view(['POST'])
def set_hostname(request):
    hostname = request.data['hostname']
    try:
        vehicle_service.set_hostname(hostname)
        vehicle_service.reboot()
        return Response({"status": "success"})
    except:
        return Response({"status": "fail"})


@api_view(['POST'])
def finish_first_time(request):
    hostname = request.data['hostname']
    ssid = request.data['ssid']
    psk = request.data['psk']
    controller = request.data['controller']
    country_code = request.data['country']

    logger.debug(f"{request.data}")

    try:
        vehicle_service.first_time_finish(hostname, ssid, psk, controller, country_code)
        logger.info("finished first time setup")
        if vehicle_service.reboot_required:
            vehicle_service.reboot()
            logger.info("sending response - reboot true")
            return Response({"reboot": True})
        else:
            logger.info("sending response - reboot false")
            return Response({"reboot": False})

    except Exception as e:
        logger.error(e)
        from rest_framework import status
        return Response({"error_msg": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def scan_network(request):
    try:
        return Response({"ssid": vehicle_service.scan_network()})
    except Exception as e:
        print(e)
        return Response({"status": "fail"})


@api_view(['POST'])
def change_password(request):
    current = request.data['current']
    password = request.data['password']
    try:
        vehicle_service.changePasswd(current, password)
        return Response({"status": "success"})
    except:
        return Response({"status": "fail"})


@api_view(['POST'])
def update_config(request):
    try:
        config_data = request.data
        vehicle_service.update_config(config_data)
        return Response({"status": "success"})
    except:
        return Response({"status": "fail"})

@api_view(['POST'])
def update_env(request):
    try:
        config_data = request.data
        vehicle_service.update_env(config_data)
        return Response({"status": "success"})
    except:
        return Response({"status": "fail"})


@api_view(['POST'])
def sync_time(request):
    try:
        currentTime = request.data['current']
        vehicle_service.sync_time(currentTime)
        return Response({"status": "success"})
    except:
        return Response({"status": "fail"})


@api_view(['GET'])
def config(request):
    data = vehicle_service.config()
    return Response(data)

@api_view(['POST'])
def start_calibrate(request):
    try:
        vehicle_service.start_calibrate()
        return Response()
    except Exception as e:
        print(e)
        from rest_framework import status
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def stop_calibrate(request):
    try:
        vehicle_service.stop_calibrate()
        return Response()
    except Exception as e:
        print(e)
        from rest_framework import status
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def reset_config(request):
    try:
        vehicle_service.reset_config()
        return Response({"status": "success"})
    except Exception as e:
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def power_off(request):
    vehicle_service.power_off()

@api_view(['POST'])
def reboot(request):
    vehicle_service.reboot()

@api_view(['POST'])
def factory_reset(request):
    try:
        vehicle_service.factory_reset()
        return Response({"status": "success"})
    except Exception as e:
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

