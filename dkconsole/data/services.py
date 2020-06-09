import os
from pathlib import Path

from django.conf import settings
from dkconsole.data.models import Meta, Tub, TubImage
from datetime import datetime
from django.utils.timezone import make_aware
import tarfile
import tempfile
import shutil
import json
import errno
from PIL import Image
import subprocess
import re


class TubService():
    @classmethod
    def data_dir(cls):
        return settings.DATA_DIR

    @classmethod
    def get_meta_json_path(cls, tub_path):
        '''
        tub_path is a POSIXPATH
        '''
        return tub_path / 'meta.json'

    @classmethod
    def get_tub_method(cls, tub_path):
        meta_json_path = cls.get_meta_json_path(tub_path)
        first_jpg_name = cls.get_thumbnail_name(tub_path)
        width, height = cls.get_image_resolution(tub_path)
        size = cls.get_size(tub_path)

        with open(meta_json_path) as f:
            meta = json.load(f)
            # print(meta)
            created_at = make_aware(datetime.fromtimestamp(meta['start']))

            if 'no_of_images' in meta:
                no_of_images = meta['no_of_images']
            else:
                no_of_images = cls.get_jpg_file_count_on_disk(tub_path)
            if 'rating' in meta:
                rating = meta['rating']
            else:
                rating = 0

            tub_image = TubImage(first_jpg_name, width, height)

            return Tub(tub_path.name, tub_path, created_at, no_of_images, tub_image, size, rating)

    @classmethod
    def get_size(cls, tub_path):
        total_size = 0.0
        for filename in Path(tub_path).iterdir():
            total_size += os.path.getsize(filename)
        total_size = total_size / 1024 / 1024
        return round(total_size, 2)

    @classmethod
    def get_tubs(cls):
        tubs = []

        for child in Path(cls.data_dir()).iterdir():
            if child.is_dir():
                try:
                    tub = cls.get_tub_method(child)
                    tubs.append(tub)
                except Exception as e:
                    print(e)
                    pass

        tubs.sort(key=lambda x: x.created_at, reverse=True)

        return tubs

    @classmethod
    def get_jpg_file_count_on_disk(cls, tub_path):
        return len([f for f in os.listdir(tub_path) if f.endswith('.jpg')])

    @classmethod
    def generate_tub_archive(cls, tub_paths):
        print("generating tub archive")
        f = tempfile.NamedTemporaryFile(mode='w+b', suffix='.tar.gz', delete=False)

        with tarfile.open(fileobj=f, mode='w:gz') as tar:
            for tub_path in tub_paths:
                p = Path(tub_path)
                tar.add(p, arcname=p.name)

        f.close()

        return f.name

    @classmethod
    def delete_tub(cls, tub_path):
        if os.path.exists(tub_path):
            shutil.rmtree(tub_path)
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), tub_path)

    @classmethod
    def get_thumbnail_name(cls, tub_path):
        jpgs = []

        for f in os.listdir(tub_path):
            if f.endswith('.jpg'):
                jpgs.append(f)

        jpgs = sorted(jpgs, key=lambda d: int(d.split('_')[0]))

        if (len(jpgs) != 0):
            return jpgs[0]
        else:
            return None

    @classmethod
    def get_image_resolution(cls, tub_path):
        if (cls.get_thumbnail_name(tub_path) is not None):
            image = Image.open(Path(tub_path / cls.get_thumbnail_name(tub_path)))
            return image.size
        else:
            width = 0
            heigh = 0
            return width, heigh

    @classmethod
    def delete_tubs(cls, min_image=0):
        for tub in cls.get_tubs():
            if tub.no_of_images <= min_image:
                shutil.rmtree(tub.path)

    @classmethod
    def gen_movie(cls, tub_name):
        tub_path = Path(settings.DATA_DIR) / tub_name
        videoPath = tub_path / "tub_movie.mp4"
        if (not os.path.exists(videoPath)):
            command = [f'{settings.VENV_PATH}/donkey', 'makemovie', f'--tub={tub_path}', f'--out={videoPath}']
            subprocess.check_output(command, cwd=settings.CARAPP_PATH)
            return videoPath
        return videoPath

    @classmethod
    def gen_histogram(cls, tub_path):
        histogram_name = os.path.basename(tub_path) + "_hist.png"
        histogram_path = tub_path / histogram_name
        if (not os.path.exists(histogram_path)):
            command = [f'{settings.VENV_PATH}/donkey', 'tubhist', f'--tub={tub_path}', f'--out={histogram_path}']
            subprocess.check_output(command, cwd=settings.CARAPP_PATH)
            return histogram_path
        return histogram_path

    @classmethod
    def get_detail(cls, tub_name):
        tub_path = Path(cls.data_dir()) / tub_name
        tub = None

        if tub_path.is_dir():
            tub = cls.get_tub_method(tub_path)
        else:
            return None
        return tub

    @classmethod
    def get_latest(cls):
        all_file = []
        for tub in Path(cls.data_dir()).iterdir():
            if os.path.isdir(tub):
                all_file.append(tub)
        latest = max(all_file, key=os.path.getmtime)
        tub = cls.get_detail(os.path.basename(latest))
        return tub

    @classmethod
    def get_meta(cls, tub_name):
        tub_path = Path(cls.data_dir()) / tub_name
        meta_json_path = cls.get_meta_json_path(tub_path)
        with open(meta_json_path) as f:
            meta = json.load(f)
            if 'no_of_images' in meta:
                no_of_images = meta['no_of_images']
            else:
                no_of_images = cls.get_jpg_file_count_on_disk(tub_path)
            if 'lat' in meta:
                location_lat = meta['lat']
            else:
                location_lat = None
            if 'lon' in meta:
                location_lon = meta['lon']
            else:
                location_lon = None
            if 'remark' in meta:
                remark = meta['remark']
            else:
                remark = None
            if 'rating' in meta:
                rating = meta['rating']
            else:
                rating = None

            return Meta(no_of_images, location_lat, location_lon, remark, rating)

    @classmethod
    def update_meta(cls, tub_name, update_parms):
        update = {}
        tub_path = Path(cls.data_dir()) / tub_name
        meta_json_path = cls.get_meta_json_path(tub_path)
        with open(meta_json_path) as f:
            meta = json.load(f)
            update = meta.copy()
            parms = dict([i.split(':') for i in update_parms])
            dict_parms = dict((k, v) for k, v in parms.items())
            for key in dict_parms:
                for meta_items in meta:
                    if (re.match(key, meta_items)):
                        update[meta_items] = dict_parms[key]
                    else:
                        update[key] = dict_parms[key]
        output = open(meta_json_path, "w+")
        json.dump(update, output)
        output.close

        return update
