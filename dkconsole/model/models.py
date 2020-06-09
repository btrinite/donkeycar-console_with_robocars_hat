from django.db import models


# Create your models here.
class MLModel():
    def __init__(self, name, path, created, rating):
        self.name = name
        self.path = path
        self.created = created
        self.rating = rating
