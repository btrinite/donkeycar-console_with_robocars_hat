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
from django.conf import settings

from dkconsole.model.services import MLModelService
from .vehicle_service import VehicleService

logger = logging.getLogger(__name__)


class PiVehicle(VehicleService):
    def no_op(self):
        pass
