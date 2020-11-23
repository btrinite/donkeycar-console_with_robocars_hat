from django.apps import AppConfig
from .service_factory import factory
from packaging import version
import donkeycar

class MyAppConfig(AppConfig):
    name='dkconsole'

    def ready(self):
        '''
        We inject dependency based on donkey car version or OS

        e.g. for v3 donkey car, we inject the data v3 service
        for jetson nano, we inject a vehicle service compatible with Jetson Nano
        '''

        donkeycar_version = version.parse(donkeycar.__version__)

        if (donkeycar_version.major == 3):
            print("3")
        elif (donkeycar_version.major == 4):
            print("4")
        else:
            raise Exception("Donkey car version not supported")

        from dkconsole.vehicle.pi_vehicle_service import PiVehicle
        factory.register('vehicle_service', PiVehicle)


        from dkconsole.data.services import TubService
        factory.register('tub_service', TubService)



