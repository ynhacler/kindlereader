#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup  
import py2exe
from kindlereader import __version__

options = {"py2exe":  
            {   "compressed": 1,
                "optimize": 2,
                "includes":"os,sys,sgmllib",
                "bundle_files": 1
            }
          }
setup(
    version = __version__,
    description = "Push RSS to your kindle",
    name = "kindlereader",
    options = options,
    zipfile=None,
    console=[{"script": "kindlereader.py"}],
 )