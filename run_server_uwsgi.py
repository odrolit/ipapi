#!/usr/bin/env python

#uwsgi --http :5000 --wsgi-file run_server_uwsgi.py --master --processes 4 --threads 4 --stats 10.0.0.18:5001

from ipapi import application

