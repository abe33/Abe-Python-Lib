#!/bin/bash

options="--settings=abe.settings_localhost --pythonpath=/var/www"

#load fixtures
python ../manage.py loaddata auth/initial_data.xml $options 
#python ../manage.py loaddata tagging/initial_data.xml $options 
python ../manage.py loaddata posts/initial_data.xml $options 
python ../manage.py loaddata comments/initial_data.xml $options 
python ../manage.py loaddata bugs/initial_data.xml $options 
