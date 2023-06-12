#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: visualize.py
Author: Kevin G. Yager, Brookhaven National Laboratory
Email: kyager@bnl.gov
Date created: 2023-04-03
Description:
 Visualize the distribution of embedding vectors.
"""

# Imports
########################################

import sys, os
# If SciBot is not "installed" (pip install SciToolsSciBot), then you can point to the code on your computer here:
SciBot_PATH ='/home/user/SciBot/'
SciBot_PATH  in sys.path or sys.path.append(SciBot_PATH )

from SciBot import visualize

# We presume there is a local file called "config.py" that stores your configuration
import config



# Run
########################################
if __name__ == "__main__":
    
    vis = visualize.Visualize(name='vis', configuration=config.SciBot_configuration, verbosity=5)
    
    
    dtype = 'raw'
    dtype = 'doc_names'
    
    infile = './hold-{}-chunk_lookup.npy'.format(dtype)
    outfile = infile.replace('hold-', 'tSNE-')
    
    if True:
        vis.load_embedding_lookup_file(infile)
        vis.generate_tSNE()
        vis.save_embedding_lookup_file(outfile)
        
    else:
        vis.load_embedding_lookup_file(outfile)

    outfile = 'tSNE-{}.png'.format(dtype)
    vis.plot_tSNE(save=outfile)
