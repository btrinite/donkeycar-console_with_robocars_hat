from django.shortcuts import render
from dkconsole.data.models import Tub
from rest_framework.response import Response
from django.http import HttpResponse, JsonResponse, Http404, FileResponse

from .services import TubService
from .serializers import TubSerializer, TubImageSerializer, MetaSerializer
from rest_framework.decorators import api_view
import os
from pathlib import Path
from django.conf import settings
from PIL import Image
from wsgiref.util import FileWrapper

from django.http.response import StreamingHttpResponse
import os
import re
import mimetypes
from wsgiref.util import FileWrapper

# Create your views here.


@api_view(['GET'])
def index(request):

    # for name in os.listdir(tub_path()):
    #     print(name)
    tubs = TubService.get_tubs()

    serializer = TubSerializer(tubs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
def tub_archive(request, tub_name):
    tub_paths = [Path(settings.DATA_DIR) / tub_name]
    archive_path = TubService.generate_tub_archive(tub_paths)

    if os.path.exists(archive_path):
        with open(archive_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type="application/gzip")
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(archive_path)
            return response
    raise Http404


@api_view(['POST'])
def delete(request):
    try:
        tub_path = request.data['tub_path']

        TubService.delete_tub(tub_path)

        return Response({"success": True})
    except Exception as e:
        print(e)
        return Response({"success": False})


@api_view(['GET'])
def jpg(request, tub_name, filename):
    '''
    http://localhost:8000/data/tub_9_20-01-10/1_cam-image_array_.jpg
    '''
    try:
        image_file_path = Path(settings.DATA_DIR) / tub_name / filename

        # 192.168.0.76

        return FileResponse(open(image_file_path, 'rb'))

        # with open(image_file_path, "rb") as f:
        #     return HttpResponse(f.read(), content_type="image/jpeg")
    except IOError:
        # with open(get_no_image_path(), "rb") as f:
        #     return HttpResponse(f.read(), content_type="image/png")

        return FileResponse(open(get_no_image_path(), 'rb'))


def get_no_image_path():
    return os.path.dirname(__file__) + "/static/no_image.png"


@api_view(['POST'])
def delete_tubs(request):
    try:
        number_of_images = request.data['number_of_images']

        TubService.delete_tubs(number_of_images)

        return Response({"success": True})
    except Exception as e:
        print(e)
        return Response({"success": False})


@api_view(['GET'])
def get_sample_video(request, tub_name):
    path = os.path.dirname(__file__) + "/static/tub_80.mp4"
    path = Path(settings.DATA_DIR) / tub_name / "tub_movie.mp4"
    print(path)
    # return FileResponse(open(path, 'rb'))

    file = FileWrapper(open(path, 'rb'))
    response = StreamingHttpResponse(file, content_type='video/mp4')
    # response['Content-Disposition'] = 'attachment; filename=my_video.mp4'
    return response


range_re = re.compile(r'bytes\s*=\s*(\d+)\s*-\s*(\d*)', re.I)


class RangeFileWrapper(object):
    def __init__(self, filelike, blksize=8192, offset=0, length=None):
        self.filelike = filelike
        self.filelike.seek(offset, os.SEEK_SET)
        self.remaining = length
        self.blksize = blksize

    def close(self):
        if hasattr(self.filelike, 'close'):
            self.filelike.close()

    def __iter__(self):
        return self

    def __next__(self):
        if self.remaining is None:
            # If remaining is None, we're reading the entire file.
            data = self.filelike.read(self.blksize)
            if data:
                return data
            raise StopIteration()
        else:
            if self.remaining <= 0:
                raise StopIteration()
            data = self.filelike.read(min(self.remaining, self.blksize))
            if not data:
                raise StopIteration()
            self.remaining -= len(data)
            return data


def stream_video(request, tub_name):
    path = str(TubService.gen_movie(tub_name))
    range_header = request.META.get('HTTP_RANGE', '').strip()
    range_match = range_re.match(range_header)
    size = os.path.getsize(path)
    content_type, encoding = mimetypes.guess_type(path)
    content_type = content_type or 'application/octet-stream'
    if range_match:
        first_byte, last_byte = range_match.groups()
        first_byte = int(first_byte) if first_byte else 0
        last_byte = int(last_byte) if last_byte else size - 1
        if last_byte >= size:
            last_byte = size - 1
        length = last_byte - first_byte + 1
        resp = StreamingHttpResponse(RangeFileWrapper(open(path, 'rb'), offset=first_byte, length=length), status=206, content_type=content_type)
        resp['Content-Length'] = str(length)
        resp['Content-Range'] = 'bytes %s-%s/%s' % (first_byte, last_byte, size)
    else:
        resp = StreamingHttpResponse(FileWrapper(open(path, 'rb')), content_type=content_type)
        resp['Content-Length'] = str(size)
    resp['Accept-Ranges'] = 'bytes'
    return resp


@api_view(['GET'])
def detail(requst, tub_name):
    tub = TubService.get_detail(tub_name)
    serializer = TubSerializer(tub)
    return Response(serializer.data)


@api_view(['GET'])
def latest(requst):
    latest = TubService.get_latest()
    # tub = TubService.get_detail(TubService.get_latest())
    print(latest)
    serializer = TubSerializer(latest)
    return Response(serializer.data)


@api_view(['GET'])
def histogram(requst, tub_name):
    '''
    http://localhost:8000/data/tub_9_20-01-10/tub_9_20-01-10_hist.png
    '''
    try:
        TubService.gen_histogram(Path(settings.DATA_DIR) / tub_name)
        histogram_name = tub_name + "_hist.png"
        image_file_path = Path(settings.DATA_DIR) / tub_name / histogram_name
        return FileResponse(open(image_file_path, 'rb'))
    except:
        return FileResponse(open(get_no_image_path(), 'rb'))


@api_view(['GET'])
def latest_histogram(requst):
    '''
    http://localhost:8000/data/tub_9_20-01-10/tub_9_20-01-10_hist.png
    '''
    try:
        latest = TubService.get_latest()
        TubService.gen_histogram(Path(settings.DATA_DIR) / latest.name)
        histogram_name = latest.name + "_hist.png"
        image_file_path = Path(settings.DATA_DIR) / latest.name / histogram_name
        return FileResponse(open(image_file_path, 'rb'))
    except:
        return FileResponse(open(get_no_image_path(), 'rb'))


@api_view(['GET'])
def show_meta(request, tub_name):
    meta = TubService.get_meta(tub_name)
    serializer = MetaSerializer(meta)
    return Response(serializer.data)


@api_view(['POST'])
def update_meta(request, tub_name):
    '''
    {"update_parms":["123: 123"]}
    '''
    update_parms = request.data["update_parms"]
    TubService.update_meta(tub_name, update_parms)
    return Response({"success": True})
