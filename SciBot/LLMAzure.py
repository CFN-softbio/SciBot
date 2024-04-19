#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: LLMAzure.py
Author: Terry Healy / thealy@bnl.gov
Date created: 2024-01-25
Description:
 Manages connections to Azure OpenAI's GPT-3 model.
 Based on "LLMOpenAI.py" by Kevin Yager
"""

from .Base import Base
from openai import AzureOpenAI


# Conversion factors (for GPT-3 LLM):
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
##################################################

class Azure_OpenAI_LLM(Base):

    def __init__(self, api_key, model='gpt-35-turbo-16k', 
                 token_limit:int = 4096, 
                 endpoint: str = 'https://*****.openai.azure.com/',
                 deployment: str = 'gpt35', name='LLM', **kwargs):

        super().__init__(name=name, **kwargs)
        self.model = model
        self.token_limit = token_limit
        self.word_limit = int(self.token_limit * 0.75)
        self.char_limit = int(self.token_limit * 4.00)
        self.endpoint = endpoint,
        self.api_key = api_key
        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version="2023-05-15",
            azure_endpoint=endpoint,    # For some reason, self.endpoint is a tuple. Default value?
            azure_deployment=deployment # The configured service in our Azure portal
        )

    def chat_completion(self, messages, model=None):
        if model is None:
            model = self.model

        completion = self.client.chat.completions.create(model=model, messages=messages)
        response = completion.choices[0].message
        if response.role == "assistant":
            response = response.content
        else:
            response = self.msg_error("No response matching 'assistant'.")

        return response

class Azure_OpenAI_embedding(Base):
    
    def __init__(self, api_key, model='text-embedding-ada-002',
                 token_limit:int = 8192,
                 endpoint: str = 'https://*****.openai.azure.com/',
                 deployment: str = 'ada002', name='embed', **kwargs):

        super().__init__(name=name, **kwargs)
        self.model = model
        self.token_limit = token_limit
        self.word_limit = int(self.token_limit * 0.75)
        self.char_limit = int(self.token_limit * 4.00)
        self.endpoint = endpoint,
        self.api_key = api_key
        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version="2023-05-15",
            azure_endpoint=endpoint,    # For some reason, self.endpoint is a tuple. Default value?
            azure_deployment=deployment # The configured service in our Azure portal
        )
    
    
    def embedding(self, text, model=None):
        """Lookup this text block in OpenAI, and determine the embedding for it."""

        # https://platform.openai.com/docs/guides/embeddings/what-are-embeddings
        if model is None:
            model = self.model

        result = self.client.embeddings.create(model=model, input=text)
        return result.data[0].embedding
