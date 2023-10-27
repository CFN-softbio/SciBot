#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: tool_bots.py
Author: Kevin G. Yager, Brookhaven National Laboratory
Email: kyager@bnl.gov
Date created: 2023-07-07
Description:
 Defines LLM tools.
"""

from .Base import Base
from .LLMs import *
import re


class CompareBot(Base):
    '''Compares two documents.'''
    
    def __init__(self, configuration, name='CompareBot', max_response_len=3600, **kwargs):
        super().__init__(name=name, **kwargs)

        self.db = None        
        
        self.configuration = configuration
        api_key = self.configuration['openai']['api_key']

        # For LLM responses
        self.model = self.configuration['openai']['model']
        self.token_limit = self.configuration['openai']['model_token_limit']
        self.LLM_chat = OpenAI_LLM(api_key=api_key, model=self.model, token_limit=self.token_limit, name='OpenAI')
        
        instruction = """Analyze the two extracts given below, which were taken from PUBLICATION_A and PUBLICATION_B (scientific publications). I want you to decide which one is more likely to be "high impact", meaning that it becomes influential in terms of creating community excitement, driving follow-on work, and changin perspectives in the field. Please compose a reply that provides a very brief impact analysis of PUBLICATION_A and PUBLICATION_B, then compares the two, and finishes off with a clear statement that strictly follows this format: "The higher-impact publication is: PUBLICATION_X" (where X is A or B)."""

        # Reserve this space in the message
        self.header_len = len(instruction)
        
        self.background = [
            {"role": "system", "content" : instruction}
            ] 
        
        
        self.max_response_len = max_response_len # chars
        self.max_context_len = self.LLM_chat.char_limit - self.header_len - self.max_response_len
        
        #self.print_window()
        
        self.answer_re = re.compile('higher-impact publication is:? PUBLICATION_([AB])', re.IGNORECASE)
        
        
        
    # Call the LLM
    ##################################################
        
    def query(self, txtA, txtB, msg_cutoff=35):
        
        txt_size = int(self.max_context_len/2)
        
        messages = self.background.copy()
        
        question = """PUBLICATION_A:\n\n{}\n\nPUBLICATION_B:\n\n{}\n""".format(txtA[:txt_size], txtB[:txt_size])
        
        messages.append({"role": "user", "content" : question})


        msg = question[:msg_cutoff].replace('\n', '')
        self.msg(f'''Asking question ({len(question):,d} chars): "{msg}"...''', 3, 2)
        
        response = self.LLM_chat.chat_completion(messages)
        
        self.msg(f'''Received response ({len(response):,d} chars): "{response[:msg_cutoff]}"...''', 3, 2)
        
        m = self.answer_re.search(response)
        if m:
            winner = m.groups()[0]
            
        else:
            winner = '?'
        
        
        return response, winner
        


class ClassifyBot(Base):
    '''Puts a document into one of the specified categories/bins.'''
    
    def __init__(self, configuration, categories, name='ClassifyBot', max_response_len=3600, **kwargs):
        super().__init__(name=name, **kwargs)

        self.db = None        
        
        self.configuration = configuration
        api_key = self.configuration['openai']['api_key']

        # For LLM responses
        self.model = self.configuration['openai']['model']
        self.token_limit = self.configuration['openai']['model_token_limit']
        self.LLM_chat = OpenAI_LLM(api_key=api_key, model=self.model, token_limit=self.token_limit, name='OpenAI')
        
        instruction = f"""Analyze the two text provided below, which is taken from a scientific publication. Identify the most appropriate category for this publication (list provided below). Provide a brief response that analyzes the content of the publication, and then finish off your reply with a clear classification statement that strictly follows this format: "The publication should be in category: CATEGORY" (where CATEGORY is one of the ones listed below).\n\nThe valid categories for consideration are:\n{categories}"""

        # Reserve this space in the message
        self.header_len = len(instruction)
        
        self.background = [
            {"role": "system", "content" : instruction}
            ] 
        
        
        self.max_response_len = max_response_len # chars
        self.max_context_len = self.LLM_chat.char_limit - self.header_len - self.max_response_len
        
        #self.print_window()
        
        self.answer_re = re.compile('should be in category:? ([a-zA-Z-]+)', re.IGNORECASE)
        
        
        
    # Call the LLM
    ##################################################
        
    def query(self, txt, msg_cutoff=35):
        
        txt_size = int(self.max_context_len)
        
        messages = self.background.copy()
        
        question = """Publication text:\n\n{}""".format(txt[:txt_size])
        
        messages.append({"role": "user", "content" : question})


        msg = question[:msg_cutoff].replace('\n', '')
        self.msg(f'''Asking question ({len(question):,d} chars): "{msg}"...''', 3, 2)
        
        response = self.LLM_chat.chat_completion(messages)
        
        self.msg(f'''Received response ({len(response):,d} chars): "{response[:msg_cutoff]}"...''', 3, 2)
        
        m = self.answer_re.search(response)
        if m:
            result = m.groups()[0]
            
        else:
            result = '?'
        
        
        return response, result
    
    
    
