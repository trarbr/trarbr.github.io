#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

# The settings in this file are applied on top of the settings in pelicanconf.py

import os
import sys
sys.path.append(os.curdir)
from pelicanconf import *

SITEURL = 'https://tr.arbr.dk'
OUTPUT_PATH = 'output'
DELETE_OUTPUT_DIRECTORY = True

FEED_ALL_ATOM = 'feeds/all.atom.xml'
CATEGORY_FEED_ATOM = 'feeds/{slug}.atom.xml'

RELATIVE_URLS = False

# Following items are often useful when publishing

#GOOGLE_ANALYTICS = ""

STATIC_PATHS = [
    'CNAME',
]

DISQUS_SITENAME = 'trarbr'
