from django.shortcuts import render
from django.http import HttpResponse, HttpResponseServerError
from rest_framework.response import Response
from rest_framework.decorators import api_view

from .services import Vehicle

from django.conf import settings
from rest_framework import status
import time


# Create your views here.
def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")


@api_view(['GET'])
def block(request):
    # This function does nothing but block the thread. For testing gunicorn worker setting
    time.sleep(60)
    return Response({"status": "blocked 1 seconds"})


@api_view(['POST'])
def start_driving(request):
    '''
    tub_meta - a list of key:value
    ["x:y", "a:b"]
    '''
    use_joystick = request.data.get('use_joystick', False)
    tub_meta = request.data.get('tub_meta', None)

    Vehicle.start_driving(use_joystick, tub_meta)
    return Response({"status": True})


@api_view(['POST'])
def start_autopilot(request):
    model_path = request.data['model_path']
    use_joystick = request.data['use_joystick']

    pid = Vehicle.start_autopilot(use_joystick, model_path)

    return Response({"status": True})


@api_view(['POST'])
def stop_driving(request):
    Vehicle.stop_driving()
    return Response({"status": True})


@api_view(['GET'])
def status(request):
    hostname = Vehicle.get_hostname()
    carapp_path = Vehicle.carapp_path
    return Response({"hostname": hostname,
                     "carapp_path": carapp_path,
                     "wlan_ip_address": Vehicle.get_wlan_ip_address(),
                     "wlan_mac_address": Vehicle.get_wlan_mac_address(),
                     "is_wlan_connected": Vehicle.is_wlan_connected(),
                     "is_hotspot_on": Vehicle.is_hotspot_on(),
                     "hotspot_ip_address": Vehicle.get_hotspot_ip_address(),
                     "isFirstTime": Vehicle.first_time(),
                     "current_ssid": Vehicle.get_current_ssid()
                     })


@api_view(['POST'])
def update_console_software(request):
    try:
        return Response({"Output": Vehicle.update_console_software(), "status": True})
    except:
        return HttpResponseServerError()

@api_view(['POST'])
def update_donkey_software(request):
    try:
        return Response({"Output": Vehicle.update_donkey_software(), "status": True})
    except:
        return HttpResponseServerError()


@api_view(['POST'])
def add_network(request):
    ssid = request.data['ssid']
    password = request.data['password']
    try:
        return Response({"status": Vehicle.add_network(ssid, password)})
    except:
        return Response({"status": "fail"})


@api_view(['POST'])
def reset_network(request):
    try:
        Vehicle.remove_all_network()
        return Response({"status": "success"})
    except:
        return Response({"status": "fail"})


@api_view(['POST'])
def set_hostname(request):
    hostname = request.data['hostname']
    try:
        Vehicle.set_hostname(hostname)
        Vehicle.reboot()
        return Response({"status": "success"})
    except:
        return Response({"status": "fail"})


@api_view(['POST'])
def finish_first_time(request):
    hostname = request.data['hostname']
    ssid = request.data['ssid']
    psk = request.data['psk']
    controller = request.data['controller']

    print(f"{hostname} {ssid} {psk} {controller}")

    try:
        Vehicle.first_time_finish(hostname, ssid, psk, controller)
        if Vehicle.reboot_required:
            Vehicle.reboot()
            return Response({"reboot": True})
        else:
            return Response({"reboot": False})

    except Exception as e:
        from rest_framework import status
        return Response({"error_msg": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def scan_network(request):
    try:
        return Response({"ssid": Vehicle.scan_network()})
    except Exception as e:
        print(e)
        return Response({"status": "fail"})


@api_view(['POST'])
def change_password(request):
    current = request.data['current']
    password = request.data['password']
    try:
        Vehicle.changePasswd(current, password)
        return Response({"status": "success"})
    except:
        return Response({"status": "fail"})


@api_view(['POST'])
def update_config(request):
    try:
        config_data = request.data
        Vehicle.update_config(config_data)
        return Response({"status": "success"})
    except:
        return Response({"status": "fail"})

@api_view(['POST'])
def update_env(request):
    try:
        config_data = request.data
        Vehicle.update_env(config_data)
        return Response({"status": "success"})
    except:
        return Response({"status": "fail"})


@api_view(['POST'])
def sync_time(request):
    try:
        currentTime = request.data['current']
        Vehicle.sync_time(currentTime)
        return Response({"status": "success"})
    except:
        return Response({"status": "fail"})


@api_view(['GET'])
def config(request):
    data = Vehicle.config()
    return Response(data)

@api_view(['POST'])
def start_calibrate(request):
    try:
        Vehicle.start_calibrate()
        return Response()
    except Exception as e:
        print(e)
        from rest_framework import status
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def stop_calibrate(request):
    try:
        Vehicle.stop_calibrate()
        return Response()
    except Exception as e:
        print(e)
        from rest_framework import status
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def reset_config(request):
    try:
        Vehicle.reset_config()
        return Response({"status": "success"})
    except Exception as e:
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def power_off(request):
    Vehicle.power_off()

@api_view(['POST'])
def factory_reset(request):
    try:
        Vehicle.factory_reset()
        return Response({"status": "success"})
    except Exception as e:
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

