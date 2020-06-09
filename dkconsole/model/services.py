import os
import errno
from pathlib import Path

from django.conf import settings
from .models import MLModel
from datetime import datetime
import json
import fnmatch
import re


class MLModelService():
    @classmethod
    def model_dir(cls):
        return settings.MODEL_DIR

    @classmethod
    def get_meta_json(cls, model_name):
        model_dir = cls.model_dir()
        return Path(model_dir) / f"{model_name}.json"

    @classmethod
    def get_mlmodels(cls):
        models = []
        model_dir = cls.model_dir()
        modelFile = None

        paths = sorted(Path(model_dir).iterdir(), key=os.path.getmtime, reverse=True)

        for path in paths:
            if path.is_file() and path.name.endswith(".h5"):
                modelFile = path
                model_meta_path = cls.get_meta_json(os.path.splitext(modelFile)[0])
                if os.path.exists(model_meta_path):
                    with open(model_meta_path) as f:
                        meta = json.load(f)
                        if "rating" in meta:
                            rating = meta['rating']
                        else:
                            rating = None

                    if modelFile is not None:
                        model = MLModel(modelFile.name, modelFile, datetime.fromtimestamp(
                            modelFile.stat().st_mtime), rating)
                        models.append(model)
                else:
                    if modelFile is not None:
                        model = MLModel(modelFile.name, modelFile, datetime.fromtimestamp(modelFile.stat().st_mtime), 0)
                        models.append(model)

        return models

    @classmethod
    def delete_model(cls, model_path):
        models = []

        if os.path.exists(model_path):
            os.remove(model_path)
        else:
            raise FileNotFoundError(errno.ENOENT, os.strerror(errno.ENOENT), model_path)

    @classmethod
    def model_exists(cls, model_path):
        if os.path.exists(model_path):
            return True
        else:
            return False

    @classmethod
    def update_meta(cls, model_name, update_parms):
        update = {}
        model_dir = cls.model_dir()
        model = os.path.splitext(model_name)[0]
        target_json = Path(model_dir) / f"{model}.json"
        parms = dict([i.split(':') for i in update_parms])
        dict_parms = dict((k, v) for k, v in parms.items())
        if (os.path.exists(target_json)):
            with open(target_json) as f:
                meta = json.load(f)
                update = meta.copy()
                for key in dict_parms:
                    for meta_items in meta:
                        if (re.match(key, meta_items)):
                            update[meta_items] = dict_parms[key]
                        else:
                            update[key] = dict_parms[key]
        else:
            for key in dict_parms:
                update[key] = dict_parms[key]

        output = open(target_json, "w+")
        json.dump(update, output)
        output.close

        return update
