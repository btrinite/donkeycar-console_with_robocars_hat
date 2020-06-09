rm db.sqlite3

sudo service gunicorn stop

find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
find . -path "*/migrations/*.pyc"  -delete
python manage.py makemigrations
python manage.py migrate


sudo service gunicorn start

