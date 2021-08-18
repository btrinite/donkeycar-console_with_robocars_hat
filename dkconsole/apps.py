from django.apps import AppConfig
from .service_factory import factory
from packaging import version
import donkeycar
import logging
from dkconsole.vehicle.vehicle_service import VehicleService
from django.conf import settings

logger = logging.getLogger(__name__)


class MyAppConfig(AppConfig):

    name = 'dkconsole'

    def ready(self):
        '''
        We inject dependency based on donkey car version or OS

        e.g. for v3 donkey car, we inject the data v3 service
        for jetson nano, we inject a vehicle service compatible with Jetson Nano
        '''
        from dkconsole.vehicle.pi_vehicle_service import PiVehicle
        factory.register('vehicle_service', PiVehicle)

        donkeycar_major_version = VehicleService.get_donkeycar_major_version()

        if (donkeycar_major_version == 3):
            from dkconsole.data.services import TubService
            factory.register('tub_service', TubService)
        elif (donkeycar_major_version == 4):
            from dkconsole.data.data_service_v2 import TubServiceV2
            factory.register('tub_service', TubServiceV2)
        else:
            raise Exception("Donkey car version not supported")

        logger.info(f"CARAPP_PATH = {settings.CARAPP_PATH}")
