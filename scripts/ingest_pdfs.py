#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: ingest_pdfs.py
Author: Kevin G. Yager, Brookhaven National Laboratory
Email: kyager@bnl.gov
Date created: 2023-04-03
Description:
 Simple example of putting documents into the database.
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
    
    
    
    docs = ingest.DocumentIngester(name='docs', configuration=config.SciBot_configuration, verbosity=5)
    
    pdf_dir = config.base_dir / 'documents/input_documents/A/'
    
    #docs.create_tables(documents=False, chunks=False, embeddings=True, close=True)
    #docs.create_tables(documents=False, chunks=True, embeddings=True, table_suffix='_summary', close=True)
    
    #docs.ingest_pdfs(pdf_dir, step_initial=1, force=False)
    
    #docs.ingest_pdfs(pdf_dir, step_initial=3, step_final=3, make_summaries=True, force=False)
    
    #docs.ingest_pdfs(pdf_dir, step_initial=7, step_final=7, make_summaries=True, force=False)
    #docs.ingest_pdfs(pdf_dir, step_initial=9, step_final=9, make_summaries=True, force=False)
    
    #docs.ingest_pdfs(pdf_dir, step_initial=20, step_final=20, make_summaries=True, force=True) # Generate rapid lookup file
    
    
