"""
With these settings, tests run faster.
"""

from .base import *  # noqa
from .base import env

DATA_DIR = ROOT_DIR / "dkconsole/mycar_test/data"
MOVIE_DIR = ROOT_DIR / "dkconsole/mycar_test/movies"

MODEL_DIR = ROOT_DIR / "dkconsole/mycar_test/models"
CARAPP_PATH = str(ROOT_DIR / "dkconsole/mycar_test")
