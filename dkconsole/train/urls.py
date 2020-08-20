from django.urls import path

from . import views

app_name = 'train'
urlpatterns = [
    path('', views.index, name='index'),
    path('submit_job', views.submit_job, name='submit_job'),
    path('refresh_job_status', views.refresh_job_status, name='refresh_job_status'),
    path('download_model', views.download_model, name='download_model'),
    path('delete_jobs', views.delete_jobs, name='delete_jobs'),
    path('<int:job_id>/model_movie.mp4', views.stream_video, name='stream_video')
]
