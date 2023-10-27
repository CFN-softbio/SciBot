#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: tool_scores_pairwise.py
Author: Kevin G. Yager, Brookhaven National Laboratory
Email: kyager@bnl.gov
Date created: 2023-07-07
Description:
 Defines methods for ranking documents.
"""

from .Base import Base
from .tool_bots import *

import numpy as np
import time

class Classifier(Base):
    
    def __init__(self, configuration, name='Classifier', **kwargs):
        super().__init__(name=name, **kwargs)
        
        self.configuration = configuration
        self.db = None
        
        
    # Database interaction
    ##################################################
    def start_database(self, force=False):
        
        if force or self.db is None:
            from .dbase import DocumentDatabase
            self.db = DocumentDatabase(config=self.configuration['doc_database'], verbosity=self.verbosity)
        
    def close_database(self):
        self.db.close()
        
        
        
    # Protocols/workflows
    ##################################################
    
    def classify_document(self, doc):
        
        exists, row = self.db.tool_classify_exists(doc['doc_id'], retrows=True)
        if exists:
            self.msg("{}: Already exists (result: {}).".format(doc['doc_id'], row['result']), 4, 2)
            
            return row['result']
            
        else:
            self.msg("{}: Doing classification.".format(doc['doc_id']), 4, 2)
            
            m = self.path_re.match(doc['file_path'])
            
            if m:
                p = m.groups()[0] + '/txt/' + m.groups()[2] + '.tei.txt'
                
                txt = open(p).read()

                try:
                    response, result = self.bot.query(txt)
                
                    self.db.add_tool_classify(doc['doc_id'], result, response, title=doc['title'])
                
                except Exception as e:
                    self.msg_error('Python exception: ' + type(e).__name__)
                    result = -2


            else:
                self.msg_error("RE failure for {} and/or {}.".format(selected[0], selected[1]))
                result = -3
                
            self.msg(f"result: {result}", 4, 3)
            time.sleep(5)
                
            return result


       


    def classify_documents(self, wait=5):
        
        import re
        self.path_re = re.compile('(^\/.+)(\/xml\/)(.+)(\.tei\.xml)$')
        
        categories = """self-assembly: This category is for publications related to self-assembling materials, especially block copolymer thin films (which form nanoscale morphologies due to phase separation), nanoparticle superlattices, and DNA self-assembly (particle assembly, DNA origami, etc.).\n\n
        machine-learning: This category is for papers related to artificial intelligence (AI), machine-learning (ML), data analytics, and associated concepts such as autonomous experimenation (AE).\n\n
        scattering: This category is for method and technique development associated with x-ray scattering and/or neutron scattering. This includes new techniques for measurement, or for the analysis of data related to transmission small-angle x-ray scattering (SAXS) or wide-angle scattering (WAXS), grazing-incidence methods (GISAXS or GIWAXS), reflectivity (x-ray reflectivity or neutron reflectivity), and so on. This category includes methods, data analysis, and sample cells. However, papers that merely use these techniques to study some other material do not belong in this category.\n\n
        photo-responsive materials: This category is for papers discussing photo-responsive materials, such as azobenzene materials that exhibit photo-induced cis-trans isomerization (azo-polymers) and associated phenomena such as formation of surface relief gratings (SRG).\n\n
        materials: This category serves as a general category for material science studies that do not fit into one of the above categories. Thus, it may include papers related to organic photovoltaics, battery materials, membrane materials, and so on.\n\n
        other: This category is for only the small number of papers that do not fit into any of the other categories. For instance, papers focused on education or art would belong in this category.\n\n
        """
        
        self.bot = ClassifyBot(self.configuration, categories)
        
        self.start_database()
        
        docs = self.db.get_docs()
        
        start_time = time.time()
        for i, doc in enumerate(docs):
            self.classify_document(doc)
            #print('Completed {} classifications in {} seconds ({} s/call)'.format(i+1, time.time()-start_time, (time.time()-start_time)/(i+1)))
            
            
        
        
        
        
        
        
        
