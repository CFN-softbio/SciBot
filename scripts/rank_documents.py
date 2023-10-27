#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: rank_documents.py
Author: Kevin G. Yager, Brookhaven National Laboratory
Email: kyager@bnl.gov
Date created: 2023-07-07
Description:
 Rank/sort documents according to a criteria.
"""

# Imports
########################################

import sys, os
# If SciBot is not "installed" (pip install SciToolsSciBot), then you can point to the code on your computer here:
SciBot_PATH = '/home/user/SciBot/'
SciBot_PATH  in sys.path or sys.path.append(SciBot_PATH)

from SciBot.tool_scores_pairwise import *

# We presume there is a local file called "config.py" that stores your configuration
import config


# Run
########################################
if __name__ == "__main__":
    
    
    ranker = RankSorter(configuration=config.SciBot_configuration, verbosity=5)
    #ranker.random_comparisons()
    ranker.rank_documents()
    
