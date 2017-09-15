#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Language Version: 2.7+
# Last Modified: 2016-09-09 08:48:51
from __future__ import unicode_literals, division, absolute_import, print_function

import os
bind = '0.0.0.0:6666'
workers = 4
backlog = 2048
worker_class = "gevent"  # sync, gevent,meinheld
debug = True
# proc_name = 'f01.py'
pidfile = '/tmp/gunicorn-micromsg.pid'
loglevel = 'debug'
daemon = True
errorlog = '/data/log/micromsg/error.log'
accesslog = '/data/log/micromsg/access.log'