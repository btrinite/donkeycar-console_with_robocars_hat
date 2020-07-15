from django.test import TestCase
from .services import TubService
import pytest
import os
from .models import Tub
from unittest.mock import patch
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

    def test_get_tubs(self):
        tubs = TubService.get_tubs()
        assert len(tubs) == 14
        for tub in tubs:
            if tub.name == "tub_18_19-04-06":
                assert tub.no_of_images == 5336
                assert tub.created_at == make_aware(datetime.fromtimestamp(1554525538.338533))

    def test_get_jpg_file_count_on_disk(self):
        assert TubService.get_jpg_file_count_on_disk(self.tub_path) == 5336

    def test_data_dir(self):
        assert Path(TubService.data_dir()) == self.data_dir

    def test_generate_tub_archive(self):
        tub_paths = [self.tub_path]

        archive_path = TubService.generate_tub_archive(tub_paths)

        tar = tarfile.open(archive_path, mode="r:gz")
        assert 10675 == len(tar.getmembers())
        tar.close()

    def test_delete_tub(self):
        tub_dir = Path(settings.DATA_DIR)
        with patch('shutil.rmtree') as mock_method:
            TubService.delete_tub(tub_dir / "tub_1_20-03-30")

        mock_method.assert_called_once_with(tub_dir / "tub_1_20-03-30")

    def test_get_thumbnails(self):
        assert TubService.get_thumbnail_name(self.tub_path) == self.tub_path / '1_cam-image_array_.jpg'

    def test_get_image_resolution(self):
        assert TubService.get_image_resolution(self.tub_path) == (160, 120)

    def test_delete_tubs(self):
        # with patch('shutil.rmtree') as mock_method:
        #     TubService.delete_tubs(0)

        #     assert mock_method.call_count == 12

        with patch('shutil.rmtree') as mock_method:
            TubService.delete_tubs(99999)

            assert mock_method.call_count == 12

        # with self.assertRaises(FileNotFoundError) as context:
        #     MLModelService.delete_model("non-exist-model.h5")

    # def test_add_new_tubs(self):
    #     TubService.add_new_tubs()

    # def test_read_meta_file():
    #     meta_data = MetaFileService().read_console_meta_file(tub_path)
    #     assert meta_data['name'] == 'tub_18_19-04-06'
    #     assert meta_data['no'] == 5336

    def test_gen_movie(self):
        tub_name = "tub_2_20-03-30"
        videoPath = TubService.gen_movie(tub_name)
        assert videoPath == settings.MOVIE_DIR / f"{tub_name}.mp4"
        assert os.path.exists(videoPath) is True

    def test_get_detail(self):
        tub_name = "tub_18_19-04-06"
        tub = TubService.get_detail(tub_name)
        if tub.name == "tub_18_19-04-06":
            assert tub.no_of_images == 5336
            assert tub.created_at == make_aware(datetime.fromtimestamp(1554525538.338533))

    def test_get_latest(self):
        latest = TubService.get_latest()
        assert latest.name == "tub_2_20-03-30"

    def test_get_size(self):
        tub_name = "tub_18_19-04-06"
        path = self.data_dir / tub_name
        total_size = TubService.get_size(path)
        assert total_size == 0

    def test_gen_histogram(self):
        tub_name = "tub_18_19-04-06"
        path = self.data_dir / tub_name
        filename = TubService.gen_histogram(path)
        assert str(filename) == str(path / tub_name) + "_hist.png"

    def test_get_meta(self):
        tub_name = "tub_18_19-04-06"
        meta = TubService.get_meta(tub_name)
        assert meta.no_of_images == 5336

    def test_update_meta(self):
        tub_name = "tub_18_19-04-06"
        update = TubService.update_meta(tub_name, ['123: test'])
        assert update['123'] == "test"
