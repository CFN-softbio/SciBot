#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: visualize.py
Author: Kevin G. Yager, Brookhaven National Laboratory
Email: kyager@bnl.gov
Date created: 2023-04-03
Description:
 Visualize SciBot data.
"""

from .Base import Base
from pathlib import Path
import numpy as np

import matplotlib as mpl
mpl.rcParams['mathtext.fontset'] = 'cm'
import matplotlib.pyplot as plt


class Visualize(Base):
    
    def __init__(self, configuration, name='vis', **kwargs):
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


    # Data
    ##################################################

    def load_embedding_lookup_file(self, infile='./chunk_lookup.npy'):
        '''Load the quick lookup file.'''
        
        data = np.load(infile, allow_pickle=True).item()
        self.embeddings = data
        #self.embeddings = { 'doc_ids': data['doc_ids'], 'chunk_nums': data['chunk_nums'], 'vectors': data['vectors'] }


    def generate_tSNE(self):
        from sklearn.manifold import TSNE
        tsne = TSNE(n_components=2, verbose=1, perplexity=40, n_iter=300, random_state=123)
        
        X = self.embeddings['vectors']
        
        self.msg(f'Computing tSNE for {len(X):,d} vectors of {X.shape[1]:,d} dimensions', 3, 0)
        self.timing_start()
        t_positions = tsne.fit_transform(X)
        self.timing_end_msg('tSNE', threshold=3, indent=1)
        
        self.embeddings['tSNE'] = t_positions
        
        
    def save_embedding_lookup_file(self, outfile='./chunk_lookup.npy'):
        np.save(outfile, self.embeddings, allow_pickle=True)
        
        
    # Plotting
    ##################################################
    def plot_tSNE(self, save=None, show=False, plot_range=[None,None,None,None], plot_buffers=[0.05,0.0,0.05,0.0], dpi=300, transparent=False):
        
        self.fig = plt.figure( figsize=(10,10), facecolor='white' )
        left_buf, right_buf, bottom_buf, top_buf = plot_buffers
        fig_width = 1.0-right_buf-left_buf
        fig_height = 1.0-top_buf-bottom_buf
        self.ax = self.fig.add_axes( [left_buf, bottom_buf, fig_width, fig_height] )
        
        x, y = self.embeddings['tSNE'][:,0], self.embeddings['tSNE'][:,1]
        z = self.embeddings['doc_ids']
        self.ax.scatter(x, y, c=z, cmap='jet')
        
        
        if save:
            plt.savefig(save, dpi=dpi, transparent=transparent)
        
        if show:
            plt.show()
            
        plt.close(self.fig.number)
        
    
