#!/usr/bin/python3




import sys, os
# If SciBot is not "installed" (pip install SciToolsSciBot), then you can point to the code on your computer here:
#SciBot_PATH = '/home/user/SciBot/'
#SciBot_PATH  in sys.path or sys.path.append(SciBot_PATH)

from SciBot.bots import AnswerBot




# We presume there is a local file called "config.py" that stores your configuration
config_PATH = SciBot_PATH + 'scripts/'
config_PATH  in sys.path or sys.path.append(config_PATH )

import config 






if __name__=='__main__':

    with open('query.txt') as fin:
        message = fin.read().strip()
    
    #response = "You said [{}]".format(message) # For testing
        
        
    bot = AnswerBot(name='bot', configuration=config.SciBot_configuration, verbosity=5)
    infile = config_PATH + '/chunk_lookup.npy'
    bot.load_embedding_lookup_file(infile=infile)
    response = bot.query(message, use_context=True, doc_name=True)
        
        
    with open('response.txt', 'w') as fout:
        fout.write(response)

