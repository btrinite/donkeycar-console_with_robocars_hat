from django.urls import path

from . import views

app_name = 'vehicle'
urlpatterns = [
    path('', views.index, name='index'),
    path('start_driving', views.start_driving, name='start_driving'),
    path('stop_driving', views.stop_driving, name='stop_driving'),
    path('start_autopilot', views.start_autopilot, name='start_autopilot'),
    path('status', views.status, name='status'),
    path('update', views.update_console_software, name='update'),
    path('update_donkey', views.update_donkey_software, name='update_donkey'),
    path('add_network', views.add_network, name='add_network'),
    path('reset_network', views.reset_network, name='reset_network'),
    path('set_hostname', views.set_hostname, name='set_hostname'),
    path('finish_first_time', views.finish_first_time, name='finish_first_time'),
    path('scan_network', views.scan_network, name='scan_network'),
    path('change_password', views.change_password, name='change_password'),
    path('update_config', views.update_config, name='update_config'),
    path('update_myconfig', views.update_config, name='update_config'), # legacy
    path('sync_time', views.sync_time, name='sync_time'),
    path('config', views.config, name='config'),
    path('update_env', views.update_env, name='update_env'),
    path('start_calibrate', views.start_calibrate, name='start_calibrate'),
    path('stop_calibrate', views.stop_calibrate, name='stop_calibrate'),
    path('reset_config', views.reset_config, name='reset_config'),
    path('power_off', views.power_off, name='power_off'),
    path('reboot', views.reboot, name='reboot'),
    path('factory_reset', views.factory_reset, name='factory_reset'),

]
