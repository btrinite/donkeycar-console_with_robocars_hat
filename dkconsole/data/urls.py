from django.urls import path

from . import views

app_name = 'data'
urlpatterns = [
    path('', views.index, name='index'),
    path('upload_tub', views.upload_tubs, name='upload_tub'),
    path('<str:tub_name>/tub_archive.tar.gz', views.tub_archive, name='tub_archive'),
    path('delete', views.delete, name='delete'),
    path('latest', views.latest, name='latest'),
    path('latest/hist.png', views.latest_histogram, name='latest_histogram'),
    path('<str:tub_name>/tub_movie.mp4', views.stream_video, name='stream_video'),
    path('<str:tub_name>/hist.png', views.histogram, name='histogram'),
    path('<str:tub_name>/meta', views.show_meta, name='meta'),
    path('<str:tub_name>/update_meta', views.update_meta, name='update_meta'),
    path('<str:tub_name>/<str:filename>', views.jpg, name='jpg'),
    path('delete_tubs', views.delete_tubs, name='delete_tubs'),
    path('<str:tub_name>', views.detail, name='detail'),

]
