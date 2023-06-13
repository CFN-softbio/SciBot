#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: LLMAnthropic.py
Author: Kevin Yager
Date created: 2023-06-13
Description:
 Manages connections to Anthropic Claude model.
"""


from .Base import Base
import anthropic


# Conversion factors (for Anthropic Claude LLM):
##################################################
#              |  words  |  tokens  |   chars  |
#  words       |   1     |    1.33  |    5.33  |
#  tokens      |   0.75  |    1     |    4.00  |
#  characters  |   0.19  |    0.25  |    1     |
##################################################
#              |  words  |  tokens  |   chars  |
#  words       |  1,000  |   1,333  |   5,333  |
#  tokens      |    750  |   1,000  |   4,000  |
#  characters  |    187  |     250  |   1,000  |
##################################################
#  limit       |  3,072  |   4,096  |  16,384  |
#  limit       | 75,000  | 100,000  | 400,000  |
##################################################

class Anthropic_LLM(Base):
    
    
    def __init__(self, api_key, model='claude-1', token_limit=4096, max_tokens_to_sample=1000, name='LLM', **kwargs):
        
        super().__init__(name=name, **kwargs)
        
        self.client = anthropic.Client(api_key=api_key)
        
        self.model = model
        self.token_limit = token_limit
        self.word_limit = int(self.token_limit*0.75)
        self.char_limit = int(self.token_limit*4.00)
        
        self.max_tokens_to_sample = max_tokens_to_sample
        
        #self.paragraph_limit = int(self.word_limit/250)
        #self.page_limit = self.char_limit/1800
        
        
    def chat_completion(self, messages, model=None):
        
        if model is None:
            model = self.model
            
        # Messages to prompt
        #prompt = f"{anthropic.HUMAN_PROMPT} How many toes do Egyptian Maus have?{anthropic.AI_PROMPT}"
        prompt = ""
        for message in messages:
            if message['role']=='system':
                prompt += f"{anthropic.HUMAN_PROMPT} Here are some instructions and background information: {message['content']}"
                
            elif message['role']=='user':
                prompt += f"{anthropic.HUMAN_PROMPT} {message['content']}"
                
            elif message['role']=='assistant':
                prompt += f"{anthropic.AI_PROMPT} {message['content']}"
                
            else:
                self.msg_error('Role for message not handled: {}'.format(message['role']))
        
        prompt += f"{anthropic.AI_PROMPT}"
 
        response = self.client.completion(
            prompt=prompt,
            model=model,
            max_tokens_to_sample=self.max_tokens_to_sample,
        )        
        
        return response['completion']
    
    
