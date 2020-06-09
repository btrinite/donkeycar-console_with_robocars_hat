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
sudo ln -s gunicorn.service /etc/systemd/system/gunicorn.service
```

## Developer Guide

1. Change .env_pc according to your PC.