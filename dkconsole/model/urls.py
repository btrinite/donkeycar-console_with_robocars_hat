from django.urls import path

from . import views

app_name = 'model'
urlpatterns = [
    path('', views.index, name='index'),
    path('delete', views.delete, name='delete'),
    path('<str:model_name>/update_meta', views.update_meta, name='update_meta')

]
