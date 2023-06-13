#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: query_question.py
Author: Kevin G. Yager, Brookhaven National Laboratory
Email: kyager@bnl.gov
Date created: 2023-04-03
Description:
 Simple example of asking the bot a question, using existing
documents defined in the database.
"""

# Imports
########################################

import sys, os
# If SciBot is not "installed" (pip install SciToolsSciBot), then you can point to the code on your computer here:
SciBot_PATH = '/home/user/SciBot/'
SciBot_PATH  in sys.path or sys.path.append(SciBot_PATH)

from SciBot.bots import AnswerBot
#from SciBot.bots import AnswerBot_Claude as AnswerBot

# We presume there is a local file called "config.py" that stores your configuration
import config 


# Run
########################################
if __name__ == "__main__":
    
    bot = AnswerBot(name='bot', configuration=config.SciBot_configuration, verbosity=5)
    bot.load_embedding_lookup_file(infile='./chunk_lookup.npy')
    
    question = 'What sweep velocity is typically used in shear-aligning of BCPs using the SS-LZA method? What is the optimal speed?'
    
    #bot.mock_query(question, use_context=True, doc_name=True)
    
    response = bot.query(question, use_context=True, doc_name=True)
    print(f"{bot.name} responded with: {response}")


