# Donkeycar Console

This is a management software of the donkey car software that provides
rest-based API to support Donkey Car mobile app. This software currenly supports
RPI 4B only. We welcome any contribution to make it work with Jetson Nano /
Xavier NX.

# How to deploy this app

## On Rpi4

1. clone the repo under ~
2. Go into that folder

3. Create a new virtutal environment

```
python3 -m virtualenv -p python3 ~/env_dc --system-site-packages
source ~/env_dc/bin/activate
```

4. Install dependencies

```
pip install -r requirements/production.txt
```

5. Test the installation by running the server directly

```
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

6. Add the app as systemd service

```
sudo ln -s gunicorn.service /etc/systemd/system/gunicorn.service
```

## Developer Guide

### Setup environment

#### Setup conda

```
conda create -n dconsole python=3.7
conda activate dconsole
pip install -r requirements/production.txt
```
#### Install donkeycar
```
git clone git@github.com:robocarstore/donkeycar.git
cd donkeycar
pip install -e .[pc]
cd ../
```

#### Checkout

This project use git LFS to manage testing data. If you don't want to download the testing data(which is kind of big), you can skip them by doing

`GIT_LFS_SKIP_SMUDGE=1 git clone git@github.com:robocarstore/donkeycar-console.git`

#### Modify .env file(s)
Modify .env_pc_v4 and .env_pc_v3 files if neccessary

#### Run server

```
python manage.py runserver 0.0.0.0:8000
```

1. Change .env_pc according to your PC.

#### Run test case

```
pytest -s -v dkconsole/data/test_service.py -k test_xxx
```

## Changes

2/11/2020

- return device id as "docker" if running in docker mode

# Commercial Use

If you intend to use this project for making money, you must obtain our consent before you do so. Contact us at sales@robocarstore.com
