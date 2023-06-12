#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: Base.py
Author: Kevin G. Yager, Brookhaven National Laboratory
Email: kyager@bnl.gov
Date created: 2023-04-03
Description:
 The Base() class provides simple methods for printing messages in a pretty way,
and optionally storing these messages in a log file. This is based on the code at:
https://github.com/CFN-softbio/SciAnalysis/blob/master/SciAnalysis/Base.py
"""

from pathlib import Path
import time, datetime

import numpy as np

# Base
########################################
class Base():
    
    def __init__(self, name='-', common=None, verbosity=3, log_verbosity=None):
        
        self.name = name
        self._common = common
        self.verbosity = verbosity
        self.log_verbosity = log_verbosity # None means we use the msg/print verbosity
        
        self.indent_depth = 0


    # Verbosity meaning
    ################################################################################
    # verbosity=0 : Output nothing
    # verbosity=1 : Output only most important messages (e.g. errors)
    # verbosity=2 : Output 'regular' amounts of information/data
    # verbosity=3 : Output all useful results
    # verbosity=4 : Output marginally useful things (e.g. essentially redundant/obvious things)
    # verbosity=5 : Output everything (e.g. for testing)


    # Messages (print and log)
    ########################################
    def indent(self, indent=1):
        self.indent_depth += indent
    def dedent(self, dedent=1):
        self.indent_depth -= dedent
        
    def date_stamp(self, threshold=1, indent=0, verbosity=None, **kwargs):
        date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.msg(date_str, threshold=threshold, indent=indent, verbosity=verbosity, **kwargs)
        
        
    def msg(self, txt, threshold=3, indent=0, indent_txt='  ', verbosity=None, empty_lines=0, raw=False, **kwargs):
        '''Outputs a status line indicating the current state of execution.'''
        if verbosity is None:
            verbosity = self.verbosity

        indent = np.clip(indent+self.indent_depth, 0, 10)
        indent = indent_txt*indent
        if raw:
            message = txt
        else:
            message = '{}> {}{}'.format(self.name, indent, txt)
            
        if verbosity>=threshold:
            for i in range(empty_lines):
                print('')
            print(message)
            if self.log_verbosity is None and self._common:
                for i in range(empty_lines):
                    self._common.log('')
                self._common.log(message, threshold=threshold)
            
        if self.log_verbosity is not None and self.log_verbosity>=threshold and self._common:
            for i in range(empty_lines):
                self._common.log('')
            self._common.log(message, threshold=threshold)
            

    def msgm(self, txt=None, threshold=1, indent=0, verbosity=None, mark='=', nmark=40, empty_lines=1, **kwargs):
        '''Outputs a very noticeable message, demarcated by lines.'''
        
        self.msg(txt=mark*nmark, threshold=threshold, indent=indent, verbosity=verbosity, empty_lines=empty_lines, **kwargs)
        if txt is not None:
            self.msg(txt=txt, threshold=threshold, indent=indent, verbosity=verbosity, **kwargs)
            self.msg(txt=mark*nmark, threshold=threshold, indent=indent, verbosity=verbosity, **kwargs)


    def msg_warning(self, txt, threshold=2, indent=0, verbosity=None, empty_lines=1, **kwargs):
        txt = 'WARNING: {}'.format(txt)
        self.msgm(txt=txt, threshold=threshold, indent=indent, verbosity=verbosity, empty_lines=empty_lines, **kwargs)
            
            
    def msg_error(self, txt, threshold=1, indent=0, verbosity=None, empty_lines=1, **kwargs):
        txt = 'ERROR: {}'.format(txt)
        self.msgm(txt=txt, threshold=threshold, indent=indent, verbosity=verbosity, empty_lines=empty_lines, **kwargs)


    # Messages (timing)
    ########################################
        
    def timing_start(self):
        self.start_time = time.time()

        
    def timing_end(self):
        return time.time() - self.start_time
        
        
    def timing_end_msg(self, txt='', iterations=None, threshold=3, indent=0, indent_txt='  ', verbosity=None, empty_lines=0, **kwargs):
        took = self.timing_end()
        if iterations is None:
            txt = '{} took {:.1f}s'.format(txt, took)
        else:
            txt = '{} took {:.1f}s for {} iterations ({:.3f} s/iteration)'.format(txt, took, iterations, took/iterations)
        self.msg(txt, threshold=threshold, indent=indent, indent_txt=indent_txt, verbosity=verbosity, empty_lines=empty_lines, **kwargs)


    def timing_progress_msg(self, icurrent, itotal, threshold=4, indent=4, indent_txt='  ', every=50, verbosity=None):
        if verbosity is None:
            verbosity = self.verbosity
        if verbosity>=threshold:
            if icurrent%every==0:
                amt = icurrent/itotal
                took = self.timing_end()
                if icurrent>0 and icurrent<itotal:
                    estimate = (itotal-icurrent)*took/icurrent
                    estimate = '; done in ~{}'.format(self.time_diff_str(estimate))
                else:
                    estimate = ''
                txt = "{}{:,d}/{:,d} = {:.1f}% ({}{})".format(indent_txt*indent, icurrent, itotal, 100.*icurrent/itotal, self.time_diff_str(took), estimate)
                self.print(txt)

    def now(self, str_format='%Y-%m-%d %H:%M:%S'):
        #return time.strftime(str_format)
        return datetime.datetime.now().strftime(str_format)

    def time_str(self, timestamp, str_format='%Y-%m-%d %H:%M:%S'):
        #time_tuple = time.gmtime(timestamp)
        #s = time.strftime(str_format, time_tuple)
        s = datetime.datetime.fromtimestamp(timestamp).strftime(str_format)
        return s

    def time_diff_str(self, diff):
        diff = abs(diff)
        if diff>60*60*48:
            diff = '{:.1f} days'.format(diff/(60*60*24))
        elif diff>60*60:
            diff = '{:.1f} hours'.format(diff/(60*60))
        elif diff>60:
            diff = '{:.1f} mins'.format(diff/60)
        elif diff>0.1:
            diff = '{:.1f} s'.format(diff)
        else:
            diff = '{:.4f} s'.format(diff)
            
        return diff

    def time_delta(self, first, second):
        diff = self.time_diff_str(second-first)
        
        if second<first:
            return '{} earlier'.format(diff)
        else:
            return '{} later'.format(diff)
        

    # Messages (data)
    ########################################
    def print(self, txt, **kwargs):
        self.msg(txt, threshold=1, raw=True, **kwargs)
    
    def print_array(self, data, name='array', verbosity=3):
        '''Helper code for inspecting arrays (e.g. for debugging).'''
        span = np.max(data)-np.min(data)
        if verbosity>=3:
            self.print('print_array for: {} (shape: {})'.format(name, data.shape))
        if verbosity>=1:
            self.print('    values: {:.4g} ± {:.4g} (span {:.3g}, from {:.3g} to {:.3g})'.format(np.average(data), np.std(data), span, np.min(data), np.max(data)))
        if verbosity>=4:
            self.print(data)

    def print_d(self, d, i=4):
        '''Simple helper to print a dictionary.'''
        for k, v in d.items():
            if isinstance(v,dict):
                self.print('{}{} : <dict>'.format(' '*i,k))
                self.print_d(v, i=i+4)
            elif isinstance(v,(np.ndarray)):
                self.print('{}{} : Ar{}: {}'.format(' '*i,k,v.shape,v))
            elif isinstance(v,(list,tuple)):
                self.print('{}{} : L{}: {}'.format(' '*i,k,len(v),v))
            else:
                self.print('{}{} : {}'.format(' '*i,k,v))

    def print_results(self, results):
        '''Simple helper to print out a list of dictionaries.'''
        for i, result in enumerate(results):
            self.print(i)
            self.print_d(result)

    def print_n(self, d):
        '''Simple helper to print nested arrays/dicts'''
        if isinstance(d, (list,tuple,np.ndarray)):
            self.print_results(d)
        elif isinstance(d, dict):
            self.print_d(d)
        else:
            self.print(d)

    def val_stats(self, values, name='z', sizing=False):
        span = np.max(values)-np.min(values)
        if sizing:
            sizing = " [{} = {} elements]".format(values.shape, values.size)
        else:
            sizing = ""
        self.print("  {} = {:.2g} ± {:.2g} (span {:.2g}, from {:.3g} to {:.3g}){}".format(name, np.average(values), np.std(values), span, np.min(values), np.max(values), sizing))        
            
            
    # End class Base()
    ########################################
            
            
# Common
########################################
class Common():
    '''A class meant to hold settings and pointers to open files, which many
    different other classes/objects may need to access.'''
    
    def __init__(self, settings=None, logdir='./logs/', log_verbosity=None, prepend_timestamp=True):
        
        self.settings = {} if settings is None else settings
        
        self.logdir = logdir
        self.log_verbosity = log_verbosity
        self._logfile = None
        self.prepend_timestamp = prepend_timestamp

        self._accumulate = False
        self._accumulated_msgs = []


    def log(self, msg, prepend_timestamp=None, threshold=None):
        
        if (threshold is None) or (self.log_verbosity is None) or (self.log_verbosity>=threshold):

            if self._accumulate:
                self._accumulated_msgs.append(msg)
            
            logdir = Path(self.logdir)
            logfile = '{}.log'.format(datetime.datetime.now().strftime("%Y-%m-%d"))
            
            if self._logfile is None:
                # Open new logfile if none exists
                logdir.mkdir(exist_ok=True)
                logfile = Path(logdir, logfile)
                self._logfile = open(logfile, 'a', buffering=1)
                
            else:
                # Check if existing logfile is from yesterday
                cur_logfile = Path(self._logfile.name).name
                if cur_logfile!=logfile:
                    logdir.mkdir(exist_ok=True)
                    logfile = Path(logdir, logfile)
                    self._logfile = open(logfile, 'a', buffering=1)
                
                
            if (prepend_timestamp is None and self.prepend_timestamp) or prepend_timestamp:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d (%a %b %d) %H:%M:%S")
                #timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                msg = '[{}] {}'.format(timestamp, msg)
                
            self._logfile.write('{}\n'.format(msg))
        
    
    
    def accumulate_msgs(self):
        self._accumulate = True
        self._accumulated_msgs = []
        
    def get_accumulated_msgs(self):
        m = self._accumulated_msgs
        self._accumulate = False
        self._accumulated_msgs = []
        return m    
        
    
    def __del__(self):
        if self._logfile is not None:
            self._logfile.close()
        
        
    # End class Common()
    ########################################
        
        
