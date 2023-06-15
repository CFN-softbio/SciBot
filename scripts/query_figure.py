#!/usr/bin/env python3

"""
Filename: query_figure.py
Author: Kevin G. Yager, Brookhaven National Laboratory
Email: kyager@bnl.gov
Date created: 2023-05-08
Description:
 Simple example of finding figures similar to a target figure.
"""

# Imports
########################################

import sys, os
# If SciBot is not "installed" (pip install SciToolsSciBot), then you can point to the code on your computer here:
SciBot_PATH = '/home/user/SciBot/'
SciBot_PATH  in sys.path or sys.path.append(SciBot_PATH)

from pathlib import Path

from SciBot.bots import FigureBot

# We presume there is a local file called "config.py" that stores your configuration
import config 


# Run
########################################
if __name__ == "__main__":
    
    bot = FigureBot(configuration=config.SciBot_configuration, verbosity=5)
    bot.load_embedding_lookup_file(infile='./figure_lookup.npy')
    
    
    file_name = 'image.png'
    query_image = Path('/home/user/data/') / file_name
    
    #similar_images = bot.query(query_image)
    html = bot.query_html(query_image, 'response_query_figure.html', mode='cosine')
    
