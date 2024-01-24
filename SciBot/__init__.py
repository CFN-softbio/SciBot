#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: __init__.py
Author: Kevin G. Yager, Brookhaven National Laboratory
Email: kyager@bnl.gov
Date created: 2023-04-03
Description:
 This file allows the directory to act as a package.
"""

from ._version import get_versions
__version__ = get_versions()['version']
del get_versions


