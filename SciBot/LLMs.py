#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: LLMs.py
Author: Kevin Yager
Date created: 2023-03-25
Description:
 Manages connections to AI large language models (LLM), which
could be local or running in the cloud.
For instance, OpenAI's GPT-3 model.
"""


from .Base import Base
import openai


# Conversion factors (for GPT-3 LLM):
##################################################
#              |  words  |  tokens  |  chars  |
#  words       |   1     |    1.33  |   5.33  |
#  tokens      |   0.75  |    1     |   4.00  |
#  characters  |   0.19  |    0.25  |   1     |
##################################################
#              |  words  |  tokens  |  chars  |
#  words       |  1,000  |   1,333  |  5,333  |
#  tokens      |    750  |   1,000  |  4,000  |
#  characters  |    187  |     250  |  1,000  |
##################################################
#  limit       |  3,072  |   4,096  | 16,384  |
##################################################

class OpenAI_LLM(Base):
    
    
    def __init__(self, api_key, model='gpt-3.5-turbo', token_limit=4096, name='LLM', **kwargs):
        
        super().__init__(name=name, **kwargs)
        
        openai.api_key = api_key
        self.model = model
        self.token_limit = token_limit
        self.word_limit = int(self.token_limit*0.75)
        self.char_limit = int(self.token_limit*4.00)
        
        #self.paragraph_limit = int(self.word_limit/250)
        #self.page_limit = self.char_limit/1800
        
        
    def chat_completion(self, messages, model=None):
        
        if model is None:
            model = self.model
        
        completion = openai.ChatCompletion.create(
            model=model, 
            messages=messages,
        )
        
        response = completion['choices'][0]['message']
        if response['role']=="assistant":
            response = response['content']
        else:
            response = self.msg_error("No response matching 'assistant'.")
            
        return response


    def embedding(self, text, model=None):
        '''Lookup this text block in OpenAI, and determine the embedding for it.'''
        
        # https://platform.openai.com/docs/guides/embeddings/what-are-embeddings
        
        if model is None:
            model = self.model
            
        result = openai.Embedding.create(
            model=model,
            input=text,
        )
        
        return result['data'][0]['embedding']
    
        
            
