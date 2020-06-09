from pathlib import Path

from django.conf import settings
from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .serializers import JobSerializer
from .services import TrainService
from .serializers import SubmitJobSerializer
from rest_framework import status
from dkconsole.train.models import Job, JobStatus

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

            TrainService.submit_job(tub_paths)

            return Response({"success": True})
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(e)
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

