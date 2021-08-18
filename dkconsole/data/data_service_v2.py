import errno
import json
import logging
import os
import shutil
import subprocess
import tarfile
import tempfile
import uuid
from datetime import datetime
from pathlib import Path

import requests
from PIL import Image
from django.conf import settings
from django.utils.timezone import make_aware
from donkeycar.parts.tub_v2 import Tub as DKTubV2
from requests_toolbelt import MultipartEncoder
from rest_framework import status

from dkconsole.data.models import Meta, Tub, TubImage
from dkconsole.service_factory import factory
from dkconsole.vehicle.vehicle_service import VehicleService

logger = logging.getLogger(__name__)


class TubServiceV2:
    """
    This tub service works with the new datastore v2 on donkeycar
    """
    REFRESH_TUB_STATUS_URL = f'{settings.HQ_BASE_URL}/data/refresh_tub_statuses'
    UPLOAD_TUB_URL = f'{settings.HQ_BASE_URL}/data/upload_tub'

    vehicle_service: VehicleService = factory.create('vehicle_service')

    @classmethod
    def data_dir(cls):
        return settings.DATA_DIR

    @classmethod
    def get_tub_path_by_name(cls, tub_name):
        tub_path = Path(cls.data_dir()) / tub_name
        return tub_path

    @classmethod
    def get_image_path(cls, tub_name, image_name):
        return cls.get_tub_path_by_name(tub_name) / "images" / image_name

    @classmethod
    def get_meta_json_path(cls, tub_path):
        """
        tub_path is a POSIXPATH
        """
        path = tub_path / 'meta.json'
        logger.debug(f"get_meta_json_path path: {path}")
        # print(path)
        if not Path(path).exists():
            with open(path, "w") as f:
                json.dump({"last_update": datetime.now().strftime("%m/%d/%Y, %H:%M:%S")}, f)
        return path

    @classmethod
    def get_tub(cls, tub_path):
        if not (type(tub_path) is Path):
            tub_path = Path(tub_path)

        tub = DKTubV2(tub_path)

        meta_json_path = cls.get_meta_json_path(tub_path)
        first_jpg_name = cls.get_thumbnail_name(tub)
        width, height = cls.get_image_resolution(tub)

        created_at = make_aware(datetime.fromtimestamp(tub.manifest.manifest_metadata['created_at']))

        with open(meta_json_path) as f:
            meta = json.load(f)
            print(meta)

        if 'size' in meta.keys():
            size = meta['size']
            print("have 'size'")
        else:
            size = cls.get_size(tub_path)
            cls.update_meta(tub_path.name, {"size": size})
            print("dont have 'size'")
        # TODO: fix this file size by fstat

        no_of_images = len(tub)

        previews = []

        if no_of_images > 0:
            it = iter(tub)
            for i in range(5):
                previews.append(next(it)['cam/image_array'])

        if 'rating' in tub.manifest.metadata:
            rating = tub.manifest.metadata['rating']
        else:
            rating = 0

        tub_image = TubImage(first_jpg_name, width, height)

        uuid = None
        if 'uuid' in meta.keys():
            uuid = meta['uuid']

        return Tub(tub_path.name, tub_path, created_at, no_of_images, tub_image, size, rating, previews,
                   uuid=uuid or None)

    @classmethod
    def get_size(cls, tub_path):
        # initialize the size
        total_size = 0
        # use the walk() method to navigate through directory tree
        for dirpath, dirnames, filenames in os.walk(tub_path):
            for i in filenames:
                # use join to concatenate all the components of path
                f = os.path.join(dirpath, i)
                # use getsize to generate size in bytes and add it to the total size
                total_size += os.path.getsize(f)
        total_size = total_size / 1024 / 1024
        return round(total_size, 2)

    @classmethod
    def get_tubs(cls):
        tubs = []

        for child in Path(cls.data_dir()).iterdir():
            if child.is_dir():
                try:
                    tub = cls.get_tub(child)
                    tubs.append(tub)
                except Exception as e:
                    print(e)

        tubs.sort(key=lambda x: x.created_at, reverse=True)

        return tubs

    @classmethod
    def get_jpg_file_count_on_disk(cls, tub_path):
        logger.debug(f"get_jpg_file_count_on_disk {tub_path}")
        return len([f for f in os.listdir(tub_path) if f.endswith('.jpg')])

    @classmethod
    def generate_tub_archive(cls, tub_paths, add_config_file=True):
        print("generating tub archive")
        f = tempfile.NamedTemporaryFile(mode='w+b', suffix='.tar.gz', delete=False)

        with tarfile.open(fileobj=f, mode='w:gz') as tar:
            for tub_path in tub_paths:
                p = Path(tub_path)
                tar.add(p, arcname=p.name)
            if add_config_file:
                tar.add(f"{settings.CARAPP_PATH}/myconfig.py", arcname="myconfig.py")

        f.close()

        return f.name

    @classmethod
    def delete_tub(cls, tub_path):
        if os.path.exists(tub_path):
            shutil.rmtree(tub_path)
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), tub_path)

    @classmethod
    def get_thumbnail_name(cls, tub: DKTubV2):
        if len(tub) == 0:
            return None
        else:
            return next(iter(tub))['cam/image_array']

    @classmethod
    def get_image_resolution(cls, tub: DKTubV2):
        if cls.get_thumbnail_name(tub) is not None:

            image = Image.open(Path(tub.images_base_path) / cls.get_thumbnail_name(tub))
            return image.size
        else:
            width = 0
            heigh = 0
            return width, heigh

    @classmethod
    def delete_tubs(cls, min_image=0):
        tubs = cls.get_tubs()
        for tub in cls.get_tubs():
            if tub.no_of_images <= min_image:
                shutil.rmtree(tub.path)

    @classmethod
    def gen_movie(cls, tub_name):
        tub_path = Path(settings.DATA_DIR) / tub_name

        # Create movie directory if not exists
        if not os.path.exists(settings.MOVIE_DIR):
            os.mkdir(settings.MOVIE_DIR)

        videoPath = Path(settings.MOVIE_DIR) / f"{tub_name}.mp4"
        if not os.path.exists(videoPath):
            command = [f'{settings.VENV_PATH}/donkey', 'makemovie', f'--tub={tub_path}', f'--out={videoPath}']
            print(" ".join(command))
            subprocess.check_output(command, cwd=settings.CARAPP_PATH)
            return videoPath
        return videoPath

    @classmethod
    def gen_histogram(cls, tub_path):
        print("bing bing")
        tub = DKTubV2(tub_path)

        if len(tub) == 0:
            raise Exception("empty tub")

        histogram_name = os.path.basename(tub_path) + "_hist.png"
        histogram_path = tub_path / histogram_name

        if not os.path.exists(histogram_path):
            command = [f'{settings.VENV_PATH}/donkey', 'tubhist', f'--tub={tub_path}', f'--out={histogram_path}']
            logger.debug(f"command  = {''.join(command)}")

            subprocess.check_output(command, cwd=settings.CARAPP_PATH)

            return histogram_path
        return histogram_path

    @classmethod
    def get_tub_by_name(cls, tub_name):
        tub_path = Path(cls.data_dir()) / tub_name

        return cls.get_tub(tub_path)
        # if tub_path.is_dir():
        #     tub = cls.get_tub(tub_path)
        # else:
        #     return None
        # return tub

    @classmethod
    def get_latest(cls):
        all_file = []
        for tub in Path(cls.data_dir()).iterdir():
            if os.path.isdir(tub):
                all_file.append(tub)
        latest = max(all_file, key=os.path.getmtime)
        tub = cls.get_tub(latest)
        return tub

    @classmethod
    def get_meta(cls, tub_name):
        tub_path = Path(cls.data_dir()) / tub_name
        # meta_json_path = cls.get_meta_json_path(tub_path)
        tub = DKTubV2(tub_path)

        no_of_images = len(tub)
        location_lat = tub.manifest.metadata.get('lat')
        location_lon = tub.manifest.metadata.get('lon')
        remark = tub.manifest.metadata.get('remark')
        rating = tub.manifest.metadata.get('rating')

        return Meta(no_of_images, location_lat, location_lon, remark, rating)

    @classmethod
    def update_meta(cls, tub_name, update_parms):
        # tub_path = Path(cls.data_dir()) / tub_name
        # logger.debug(f"update_meta() tub_path:{tub_path}")
        # tub = DKTubV2(tub_path)
        # tub.manifest.update_metadata(update_parms)
        # return tub.manifest.metadata

        tub_path = Path(cls.data_dir()) / tub_name
        meta_json_path = cls.get_meta_json_path(tub_path)
        with open(meta_json_path, "r+") as jsonfile:
            meta = json.load(jsonfile)
            update = {**meta, **update_parms}  # Merge the dict
            meta["last_update"] = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
            jsonfile.seek(0)
            json.dump(update, jsonfile)
            jsonfile.truncate()
        return update

    @classmethod
    def check_uuid_exist(cls, tub_name):
        tub_path = Path(cls.data_dir()) / tub_name
        meta_json_path = cls.get_meta_json_path(Path(tub_path))
        with open(meta_json_path) as f:
            meta = json.load(f)
            return 'uuid' in meta

    @classmethod
    def upload_to_hq(cls, data):
        device_id = cls.vehicle_service.get_wlan_mac_address()
        hostname = cls.vehicle_service.get_hostname()
        fail = []
        success = []
        transaction_uuid = str(uuid.uuid4())
        for tub_name in data['tub_names']:
            tub_path = Path(cls.data_dir()) / tub_name
            if not cls.check_uuid_exist(tub_path):
                try:
                    filename = cls.generate_tub_archive(tub_paths=[tub_path], add_config_file=False)
                    mp_encoder = MultipartEncoder(
                        fields={
                            'tub_name': tub_name,
                            'device_id': device_id,
                            'hostname': hostname,
                            'tub_archive_file': ('file.tar.gz', open(filename, 'rb'), 'application/gzip'),
                            'transaction_uuid': transaction_uuid
                        }
                    )

                    logger.debug('Posting tub to HQ')
                    r = requests.post(
                        cls.UPLOAD_TUB_URL,
                        data=mp_encoder,  # The MultipartEncoder is posted as data, don't use files=...!
                        # The MultipartEncoder provides the content-type header with the boundary:
                        headers={'Content-Type': mp_encoder.content_type}
                    )

                    if r.status_code == status.HTTP_200_OK and r.json()['uuid']:
                        cls.update_meta(tub_name, {'uuid': r.json()['uuid']})
                        success.append(tub_name)
                    else:
                        fail.append(tub_name)
                except Exception as e:
                    logger.error(e)
                    fail.append(tub_name)
            else:
                success.append(tub_name)
        return fail, success
