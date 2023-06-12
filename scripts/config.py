#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: config.py
Description:
 This file stores configuration variables for the SciBot to run. 
Your SciBot code can import this so that required parameters are set.
"""




from pathlib import Path
base_dir = Path('/home/user/SciBot/')


SciBot_configuration = {
    
    'document_dir': base_dir / 'documents/',
    
    'chunk_length': 1400, # chars
    'chunk_overlap_length': 280, # chars
    
    'grobid': {
        'config_file': base_dir / 'Grobid/client/config.json',
        },
    
    'openai': {
        'api_key': 'sk-************************************************',
        'model': 'gpt-3.5-turbo',
        'model_token_limit': 4096, # ~16,384 chars
        'embedding_model': 'text-embedding-ada-002', # 1,536 length vector
        'embedding_model_token_limit': 8191, # ~32,764 chars
        },
    
    'doc_database': {
        'host': 'localhost',
        'database': 'SciBot_DocumentStore',
        'user': 'scibot',
        'password': '********',
        }        
        
    
    }
