from django.apps import AppConfig
from .service_factory import factory
from packaging import version
import donkeycar

class MyAppConfig(AppConfig):
    name='dkconsole'

    def ready(self):

        donkeycar_version = version.parse(donkeycar.__version__)
        if (donkeycar_version.major == 3):
            print("3")
        else:
            print("4")

        from dkconsole.vehicle.pi_vehicle_service import PiVehicle
        # from dkconsole.vehicle.vehicle_service import VehicleService
        factory.register('vehicle_service', PiVehicle)


