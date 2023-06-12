#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: ingest_images.py
Author: Kevin G. Yager, Brookhaven National Laboratory
Email: kyager@bnl.gov
Date created: 2023-05-18
Description:
 Simple example of putting images into the database.
"""

# Imports
########################################

import sys, os
# If SciBot is not "installed" (pip install SciToolsSciBot), then you can point to the code on your computer here:
SciBot_PATH ='/home/user/SciBot/'
SciBot_PATH  in sys.path or sys.path.append(SciBot_PATH )

from SciBot import ingest

# We presume there is a local file called "config.py" that stores your configuration
import config 




# Run
########################################
if __name__ == "__main__":
    
    
    
    imgs = ingest.ImageIngester(name='imgs', configuration=config.SciBot_configuration, verbosity=5)
    
    img_dir = config.Path('/home/user/data/')
    
    imgs.ingest_images(img_dir)
    
    #imgs.ingest_images(img_dir, step_initial=3, step_final=3, force=False)
    #imgs.ingest_images(img_dir, step_initial=20, step_final=20, force=False)
    
    
    
    
