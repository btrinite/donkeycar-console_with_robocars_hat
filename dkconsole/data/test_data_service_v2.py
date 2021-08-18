from django.test import TestCase
from .services import TubService
import pytest
import os
from .models import Tub
from unittest.mock import patch, mock_open
import tempfile

from pathlib import Path
from django.conf import settings
import tarfile
from datetime import datetime
from django.utils.timezone import make_aware
from donkeycar.parts.tub_v2 import Tub
from dkconsole.data.data_service_v2 import TubServiceV2

import shutil


# Create your tests here.


class TestDataService(TestCase):

    def setUp(self):
        self.data_dir = settings.DATA_DIR
        self.tub_name = "tub_26_21-07-02"
        self.tub_path = self.data_dir / self.tub_name

        self.tub = Tub(self.tub_path)

        self.temp_path = tempfile.mkdtemp()
        self.temp_tub = Tub(self.temp_path)

        self.tub_service = TubServiceV2

        # print(f"self.data_dir = ${self.data_dir}")

    def test_tub_path(self):
        assert settings.DATA_DIR == settings.ROOT_DIR / "dkconsole" / "mycar4_test" / "data"

    def test_read_existing_tub(self):

        assert len(self.tub.manifest.metadata) == 1

        assert self.tub.manifest.metadata['test1'] == "great"
        tub_iter = iter(self.tub)
        record = next(tub_iter)
        assert record["_index"] == 5

    def test_get_tub(self):
        tub = self.tub_service.get_tub(self.tub_path)
        assert tub.name == "tub_26_21-07-02"
        print(tub.uuid)

    def test_get_tubs(self):
        tubs = self.tub_service.get_tubs()
        assert len(tubs) == 4

    def test_delete_tub(self):

        with patch('shutil.rmtree') as mock_method:
            self.tub_service.delete_tubs(0)

            assert mock_method.call_count == 1

    def test_get_thumbnail_name(self):

        assert self.tub_service.get_thumbnail_name(self.tub) == "5_cam_image_array_.jpg"

        assert self.tub_service.get_thumbnail_name(self.temp_tub) is None

    def test_get_image_resolution(self):
        tub = Tub(self.tub_path)

        assert self.tub_service.get_image_resolution(tub) == (160, 120)

    def test_tub_length(self):
        tub = Tub(self.tub_path)
        assert len(tub) == 313

    def test_gen_movie(self):
        os.environ["IMAGEIO_FFMPEG_EXE"] = "/usr/bin/ffmpeg"
        self.tub_service.gen_movie(self.tub_name)

    def test_gen_histogram(self):
        self.tub_service.gen_histogram(self.tub_path)

    def test_get_tub_by_name(self):
        tub = self.tub_service.get_tub_by_name(self.tub_name)
        assert tub.name == self.tub_name

    def test_get_latest(self):
        tub = self.tub_service.get_latest()
        assert tub.name == "empty_tub"  # Note: empty tub is the latest created tub in the tseting folder

    def test_get_meta(self):
        meta = self.tub_service.get_meta(self.tub_name)
        # assert tub.name == "empty_tub"  # Note: empty tub is the latest created tub in the tseting folder
        assert meta.no_of_images == 313
        assert meta.remark is None

    def test_update_metadata(self):
        update_meta = {"test1": "great2", "new_meta": "meta2"}

        with patch('donkeycar.parts.datastore_v2.Manifest.update_metadata') as mock_method:
            self.tub_service.update_meta(self.tub_name, update_meta)
            assert mock_method.call_count == 0

    def tearDown(self):
        shutil.rmtree(self.temp_path)
        pass