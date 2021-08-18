from django.test import TestCase
from .services import TubService
import pytest
import os
from .models import Tub
from unittest.mock import patch, mock_open

from pathlib import Path
from django.conf import settings
import tarfile
from datetime import datetime
from django.utils.timezone import make_aware


# Create your tests here.


class TestTubService(TestCase):

    def setUp(self):
        self.data_dir = settings.DATA_DIR
        self.tub_path = self.data_dir / "tub_18_19-04-06"

        self.tub_service = TubService

        print(f"self.data_dir = ${self.data_dir}")

    def test_get_tubs(self):
        tubs = self.tub_service.get_tubs()
        assert len(tubs) == 14
        for tub in tubs:
            if tub.name == "tub_18_19-04-06":
                assert tub.no_of_images == 5336
                assert tub.created_at == make_aware(datetime.fromtimestamp(1554525538.338533))

    def test_get_jpg_file_count_on_disk(self):
        assert self.tub_service.get_jpg_file_count_on_disk(self.tub_path) == 5336

    def test_data_dir(self):
        assert Path(self.tub_service.data_dir()) == self.data_dir

    def test_generate_tub_archive(self):
        tub_paths = [self.tub_path]

        archive_path = self.tub_service.generate_tub_archive(tub_paths)

        tar = tarfile.open(archive_path, mode="r:gz")

        # +2 because myconfig.py and current directory
        # assert 10675 + 2 == len(tar.getmembers())
        tar.close()

    def test_delete_tub(self):
        tub_dir = Path(settings.DATA_DIR)
        with patch('shutil.rmtree') as mock_method:
            self.tub_service.delete_tub(tub_dir / "tub_1_20-03-30")

        mock_method.assert_called_once_with(tub_dir / "tub_1_20-03-30")

    def test_get_thumbnails(self):
        assert self.tub_service.get_thumbnail_name(self.tub_path) == '1_cam-image_array_.jpg'

    def test_get_image_resolution(self):
        assert self.tub_service.get_image_resolution(self.tub_path) == (160, 120)

    def test_delete_tubs(self):
        with patch('shutil.rmtree') as mock_method:
            self.tub_service.delete_tubs(0)

            assert mock_method.call_count == 12

        with patch('shutil.rmtree') as mock_method:
            self.tub_service.delete_tubs(99999)

            assert mock_method.call_count == 14

    def test_gen_movie(self):
        tub_name = "tub_2_20-03-30"
        videoPath = self.tub_service.gen_movie(tub_name)
        assert videoPath == settings.MOVIE_DIR / f"{tub_name}.mp4"
        assert os.path.exists(videoPath) is True

    def test_get_detail(self):
        tub_name = "tub_18_19-04-06"
        tub = self.tub_service.get_detail(tub_name)
        if tub.name == "tub_18_19-04-06":
            assert tub.no_of_images == 5336
            assert tub.created_at == make_aware(datetime.fromtimestamp(1554525538.338533))

    def test_get_latest(self):
        latest = self.tub_service.get_latest()
        assert latest.name == "tub_18_19-04-06"

    def test_get_size(self):
        tub_name = "tub_18_19-04-06"
        path = self.data_dir / tub_name
        total_size = self.tub_service.get_size(path)
        assert total_size == 18.58

    def test_gen_histogram(self):
        tub_name = "tub_18_19-04-06"
        path = self.data_dir / tub_name
        filename = self.tub_service.gen_histogram(path)
        assert str(filename) == str(path / tub_name) + "_hist.png"

    def test_get_meta(self):
        tub_name = "tub_18_19-04-06"
        meta = self.tub_service.get_meta(tub_name)
        assert meta.no_of_images == 5336

    def test_update_meta(self):
        data = '{"a": 1, "b": 2}'

        with patch("builtins.open", mock_open(read_data=data)) as mock_file:
            meta = self.tub_service.update_meta("some_tub", {"b": 4, 'c': "asdfa", "d": 5})
            assert meta == {'a': 1, 'b': 4, 'c': 'asdfa', 'd': 5}

