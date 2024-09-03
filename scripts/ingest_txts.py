#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: ingest_txts.py
Author: Kevin G. Yager, Brookhaven National Laboratory
Email: kyager@bnl.gov
Date created: 2024-09-03
Description:
 Simple example of putting raw text files into the database.
"""

# Imports
########################################

import sys, os
# If SciBot is not "installed" (pip install SciToolsSciBot), then you can point to the code on your computer here:
SciBot_PATH ='/home/user/SciBot/'
SciBot_PATH  in sys.path or sys.path.append(SciBot_PATH )

from SciBot import ingest
from pathlib import Path

# We presume there is a local file called "config.py" that stores your configuration
import config 




# Run
########################################
if __name__ == "__main__":
    
    docs = ingest.DocumentIngester(name='docs', configuration=config.SciBot_configuration, verbosity=6)
    
    txt_dir = config.base_dir / 'documents/input_documents/A/'
    
    filename = 'input.md'
    title = 'Title'
    authors = 'author'

    chunk_length, overlap_length = 5000, 300
    
    infile = Path(txt_dir + filename)
    
    docs.ingest_single_txt(infile, title, authors, step_initial=3, step_final=20, chunk_length=chunk_length, overlap_length=overlap_length, make_summaries=True, force=False)
