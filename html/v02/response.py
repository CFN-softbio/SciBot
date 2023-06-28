#!/usr/bin/python3




import sys, os
# If SciBot is not "installed" (pip install SciToolsSciBot), then you can point to the code on your computer here:
SciBot_PATH = '/home/user/SciBot/'
SciBot_PATH  in sys.path or sys.path.append(SciBot_PATH)

from SciBot.bots import AnswerBot




# We presume there is a local file called "config.py" that stores your configuration
config_PATH = SciBot_PATH + 'scripts/'
config_PATH  in sys.path or sys.path.append(config_PATH )

import config 






if __name__=='__main__':

    thread_id = sys.argv[1]

    bot = AnswerBot(name='bot', configuration=config.SciBot_configuration, verbosity=5)
    infile = config_PATH + '/chunk_lookup.npy'
    bot.load_embedding_lookup_file(infile=infile)
    response = bot.query_via_db(thread_id, use_context=True, doc_name=True)

