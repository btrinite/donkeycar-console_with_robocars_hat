from django.db import models
from pathlib import Path


class Tub():
    def __init__(self, name, path, created_at, no_of_images, thumbnail, size, rating, previews, uuid=None):
        '''
        name - str
        path - POSIXPATH
        created_at - DateTime
        no_of_images - int
        '''

        self.name = name
        self.path = path
        self.created_at = created_at
        self.no_of_images = no_of_images
        self.thumbnail = thumbnail
        self.size = size
        self.rating = rating
        self.previews = previews
        self.uuid = uuid


class TubImage():
    def __init__(self, name, width, height):
        self.name = name
        self.width = width
        self.height = height


class Meta():
    def __init__(self, no_of_images, lat, lon, remark, rating):
        self.no_of_images = no_of_images
        self.lat = lat
        self.lon = lon
        self.remark = remark
        self.rating = rating
