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
        #'model': 'gpt-3.5-turbo',
        #'model': 'gpt-3.5-turbo-0613', # function calls introduced
        #'model_token_limit': 4096, # ~16,384 chars
        'model': 'gpt-3.5-turbo-16k', # Extended context length
        'model_token_limit': 16384, # ~65k chars
        #'model': 'gpt-4',
        #'model_token_limit': 8000, # ~32k chars
        'embedding_model': 'text-embedding-ada-002', # 1,536 length vector
        'embedding_model_token_limit': 8191, # ~32,764 chars
        },
    
    'azure_openai': {
        # Refer to your Azure configuration to create/check the endpoint and deployment names
        # Microsoft Azure: https://portal.azure.com/#home.
        # Azure OpenAI Studio: https://oai.azure.com/portal/
        'api_key': '******************************** ',
        'endpoint': 'https://*****.openai.azure.com/',
        'deployment_name': '********',
        'model': 'gpt-35-turbo-16k',
        'model_token_limit': 16384, # ~65k chars
        #'model': 'gpt-4',
        #'model_token_limit': 128000, # ~512k chars
        'embedding_deployment_name': '********',
        'embedding_model': 'text-embedding-ada-002', # 1,536 length vector
        'embedding_model_token_limit': 8191, # ~32k chars
        },
        
    
    'anthropic': {
        'api_key': 'sk-ant-api03-***********************************************************************************************'
        #'model': 'claude-instant-1',
        'model': 'claude-1',
        'model_token_limit': 9000, # ~36,000 chars
        #'model': 'claude-1-100k',
        #'model_token_limit': 100000, # ~400,000 chars
        'max_tokens_to_sample': 1000,
        },    
    
    'doc_database': {
        'host': 'localhost',
        'database': 'SciBot_DocumentStore',
        'user': 'scibot',
        'password': '********',
        }        
        
    
    }
