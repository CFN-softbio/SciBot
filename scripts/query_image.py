#!/usr/bin/env python3

"""
Filename: query_image.py
Author: Kevin G. Yager, Brookhaven National Laboratory
Email: kyager@bnl.gov
Date created: 2023-05-08
Description:
 Simple example of finding images similar to a target image.
"""

# Imports
########################################

import sys, os
# If SciBot is not "installed" (pip install SciToolsSciBot), then you can point to the code on your computer here:
SciBot_PATH = '/home/user/SciBot/'
SciBot_PATH  in sys.path or sys.path.append(SciBot_PATH)

from pathlib import Path

from SciBot.bots import ImageBot

# We presume there is a local file called "config.py" that stores your configuration
import config 


# Run
########################################
if __name__ == "__main__":
    
    bot = ImageBot(configuration=config.SciBot_configuration, verbosity=5)
    bot.load_embedding_lookup_file(infile='./image_lookup.npy')
    
    

    query_image = Path('/home/user/data/image_q22.tif')
    
    
    #similar_images = bot.query(query_image)
    html = bot.query_txt(query_image, 'response_query_image.txt', mode='euclid', exclude=None)
    
