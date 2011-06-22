#!/bin/bash

options="--settings=abe.settings_localhost --pythonpath=/var/www"

# flush the db
#python ../manage.py flush $options

# sync the db with django models
python ../manage.py syncdb $options 

#load fixtures
#python ../manage.py loaddata auth/initial_data.xml $options 
#python ../manage.py loaddata tagging/initial_data.xml $options 
#python ../manage.py loaddata posts/initial_data.xml $options 


