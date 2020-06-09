from django.test import TestCase
from .services import TrainService
from django.conf import settings
from pathlib import Path
import pytest
from unittest import skip
from unittest.mock import patch, ANY
from .models import Job, JobStatus
from datetime import timedelta
from django.utils import timezone
import time
import uuid


# Create your tests here.
class TestTrainService(TestCase):

    def setUp(self):
        self.data_dir = Path(settings.DATA_DIR)
        self.tub_paths = [str(self.data_dir / "tub_18_19-04-06"),
                          str(self.data_dir / "tub_6_20-03-31")]

        self.tub_archive_path = Path(__file__).parent.absolute() / "test_data" / "test_archive.tar.gz"

    def test_create_job(self):
        job = TrainService.create_job(self.tub_paths)

        assert job is not None
        assert job.id is not None
        assert job.tub_paths is not None
        assert job.model_size is None

    def test_submit_job(self):
        with patch('dkconsole.train.services.TrainService.create_job') as mock_create_job:
            with patch('dkconsole.data.services.TubService.generate_tub_archive', return_value=self.tub_archive_path) as mock_generate_tub_archive:
                with patch('requests.post') as mock_post:
                    # type(mock_post.return_value).status_code =
                    # PropertyMock(return_value=200)
                    mock_post.return_value.status_code = 200
                    mock_post.return_value.json.return_value = {'job_uuid': str(uuid.uuid4())}

                    TrainService.submit_job(self.tub_paths)
                    mock_create_job.assert_called_once_with(self.tub_paths)
                    mock_generate_tub_archive.assert_called_once()

                    mock_post.assert_called_once()

    @patch('dkconsole.train.services.TrainService.refresh_job_status')
    def test_refresh_all_job_status(self, mock_refresh_job_status):

        for i in range(0, 10):
            Job(status=JobStatus.SCHEDULED).save()
            Job(status=JobStatus.TRAINING).save()
            Job(status=JobStatus.TIMEOUT).save()

        TrainService.refresh_all_job_status()
        assert mock_refresh_job_status.call_count == 20

    def test_refresh_job_status(self):
        # TrainService.submit_job(self.tub_paths)
        # jobs = Job.objects.all()
        job_uuids = ["19460b57-27fa-4e7d-8a79-9434af0f9629"]

        # Build up test data
        for uuid in job_uuids:
            Job(uuid=uuid, status=JobStatus.SCHEDULED).save()

        # exception case, uuid is none
        Job(uuid=None, status=JobStatus.SCHEDULED).save()

        with patch('dkconsole.train.services.TrainService.get_latest_job_status_from_hq') as mock_get_latest_job_status_from_hq:
            with patch('dkconsole.train.services.TrainService.download_file') as mock_download_file:
                mock_return_value = [{"uuid": uuid, "status": JobStatus.COMPLETED, "model_url": "some-url", "model_accuracy_url": "some-url"} for uuid in job_uuids]
                mock_get_latest_job_status_from_hq.return_value = mock_return_value

                TrainService.refresh_all_job_status()
                mock_get_latest_job_status_from_hq.assert_called_once_with(job_uuids)
                assert mock_download_file.call_count == 2

                mock_get_latest_job_status_from_hq.return_value = []
                TrainService.refresh_all_job_status()
                assert mock_download_file.call_count == 2

        jobs = Job.objects.filter(uuid__in=job_uuids)
        for job in jobs:
            assert job.status == JobStatus.COMPLETED

    def test_refresh_job_status_lock(self):
        TrainService.refresh_lock = True

        with patch('dkconsole.train.services.TrainService.get_latest_job_status_from_hq') as mock_get_latest_job_status_from_hq:
            TrainService.refresh_all_job_status()
            mock_get_latest_job_status_from_hq.assert_not_called() # when refresh is locked, do not send request again

        TrainService.refresh_lock = False

    def test_download_file(self):
        url = "https://www.google.com/robots.txt"
        target_path = "some_download_file_for_test.txt"
        TrainService.download_file(url, target_path)

        time.sleep(1)

        my_file = Path(target_path)
        assert my_file.is_file() is True

    def test_delete_jobs(self):
        job_ids = []
        self.test_create_job()
        assert Job.objects.all().exists() is True
        job_ids.append(Job.objects.all()[0].id)
        TrainService.delete_jobs(job_ids)
        assert Job.objects.all().exists() is False






