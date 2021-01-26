"""
With these settings, tests run faster.
"""

from .base import *  # noqa
from .base import env


if (donkeycar_version.major == 3):
    DATA_DIR = ROOT_DIR / "dkconsole/mycar_test/data"
elif (donkeycar_version.major == 4):
    DATA_DIR = ROOT_DIR / "dkconsole/mycar4_test/data"


# DATA_DIR = ROOT_DIR / "dkconsole/mycar_test/data"
MOVIE_DIR = ROOT_DIR / "dkconsole/mycar_test/movies"

MODEL_DIR = ROOT_DIR / "dkconsole/mycar_test/models"
# CARAPP_PATH = str(ROOT_DIR / "dkconsole/mycar_test")
