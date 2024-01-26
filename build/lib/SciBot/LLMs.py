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
from .LLMOpenAI import *
from .LLMAnthropic import *


