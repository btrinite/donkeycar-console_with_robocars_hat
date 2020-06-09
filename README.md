# How to deploy this app

## On Rpi4


1. clone the repo under ~
2. Go into that folder

3. Create a new virtutal environment
```
python3 -m virtualenv -p python3 dc2env --system-site-packages
```

4. Install dependencies

```
pip install -r requirements/production.txt
```

5. Test the installation by running the server directly

```
python manage.py runserver 0.0.0.0:8000
```

6. Add the app as systemd service

```
sudo vi /etc/systemd/system/gunicorn.service
```

```
[Unit]
Description = DKConsole v2
After = network.target

[Service]
PermissionsStartOnly = true
PIDFile = /run/dkconsole/dkconsole.pid
User = pi
Group = pi
WorkingDirectory = /home/pi/donkeycar-console-v2
ExecStartPre = /bin/mkdir /run/dkconsole
ExecStartPre = /bin/chown -R  pi:pi /run/dkconsole
ExecStart = /home/pi/donkeycar-console-v2/dc2env/bin/gunicorn dkconsole.wsgi -b 0.0.0.0:8000 --pid /run/dkconsole/dkconsole.pid
ExecReload = /bin/kill -s HUP $MAINPID
ExecStop = /bin/kill -s TERM $MAINPID
ExecStopPost = /bin/rm -rf /run/dkconsole
PrivateTmp = true

[Install]
WantedBy = multi-user.target
```

## Developer Guide

1. Change .env_pc according to your PC.