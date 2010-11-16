#!/bin/bash

python ../manage.py dumpdata auth \
		--format=xml \
		--settings=abe.settings_localhost \
		--pythonpath=/var/www \
		> ../fixtures/auth/initial_data.xml

python ../manage.py dumpdata tagging \
		--format=xml \
		--settings=abe.settings_localhost \
		--pythonpath=/var/www \
		> ../fixtures/tagging/initial_data.xml
		
python ../manage.py dumpdata posts \
		--format=xml \
		--settings=abe.settings_localhost \
		--pythonpath=/var/www \
		> ../fixtures/posts/initial_data.xml

python ../manage.py dumpdata bugs \
		--format=xml \
		--settings=abe.settings_localhost \
		--pythonpath=/var/www \
		> ../fixtures/bugs/initial_data.xml
		
python ../manage.py dumpdata comments \
		--format=xml \
		--settings=abe.settings_localhost \
		--pythonpath=/var/www \
		> ../fixtures/comments/initial_data.xml


