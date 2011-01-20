#!/bin/bash

python ../manage.py runserver --settings=abe.settings_localhost --pythonpath=/var/www 8000 --adminmedia=/home/cedric/Developpement/Dev/libs/aesia/django/abe/Abe-Python-Lib/abe_media/admin/
