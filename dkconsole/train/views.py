import logging

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from dkconsole.train.models import Job
from dkconsole.util import *
from .serializers import JobSerializer
from .serializers import SubmitJobSerializer
from .services import TrainService

logger = logging.getLogger(__name__)


# Create your views here.


@api_view(['GET'])
def index(request):
    jobs = TrainService.get_jobs()

    serializer = JobSerializer(jobs, many=True)
    return Response(serializer.data)


@api_view(['POST'])
def submit_job(request):
    try:
        print(request.data)
        serializer = SubmitJobSerializer(data=request.data)

        if serializer.is_valid():
            tub_paths = request.data['tub_paths']

            try:
                if not request.data['v2']:
                    TrainService.submit_job(tub_paths)
                else:
                    TrainService.submit_job_v2(tub_paths)
            except KeyError:
                TrainService.submit_job(tub_paths)

            return Response({"success": True})
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(e)
        return Response(status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def refresh_job_status(request):
    '''
    This is supposed to be called by scheduled job per minute
    '''
    count = TrainService.refresh_all_job_status()

    return Response({"count": count})


@api_view(['POST'])
def download_model(request):
    print(request.data)
    job_id = request.data['job_id']
    job = Job.objects.get(pk=job_id)
    TrainService.download_model(job)
    return Response({"success": False})


@api_view(['POST'])
def delete_jobs(request):
    job_ids = request.data['job_ids']
    TrainService.delete_jobs(job_ids)
    return Response({"success": True})


def stream_video(request, job_id):
    path = (TrainService.get_model_movie_path(job_id))

    resp = video_stream(request, path)
    return resp
