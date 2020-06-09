from django.test import TestCase
from .services import MLModelService
from django.conf import settings
from pathlib import Path
from unittest.mock import patch


# Create your tests here.
class TestTubService(TestCase):

    def test_get_models(self):
        models = MLModelService.get_mlmodels()
        assert len(models) == 32

    def test_delete_model(self):
        model_dir = Path(settings.MODEL_DIR)
        with patch('os.remove') as mock_method:
            MLModelService.delete_model(model_dir / "job_118")

        mock_method.assert_called_once_with(model_dir / "job_118")

        with self.assertRaises(FileNotFoundError) as context:
            MLModelService.delete_model("non-exist-model.h5")

    def test_update_meta(self):
        update = MLModelService.update_meta("job_120", ['rating:1'])
        assert update['rating'] == '1'


