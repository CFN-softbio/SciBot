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

class RankSorter(Base):
    def __init__(self, configuration, name='Ranker', **kwargs):
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
    
    def compare_documents(self, doc_A, doc_B):
        
        exists, row = self.db.scores_pairwise_exists(doc_A['doc_id'], doc_B['doc_id'], retrows=True)
        if exists:
            self.msg("{} vs. {}: Comparison already exists ({} won).".format(doc_A['doc_id'], doc_B['doc_id'], row['winner']), 4, 2)
            
            return row['winner']
            
        else:
            self.msg("{} vs. {}: Doing comparison.".format(doc_A['doc_id'], doc_B['doc_id']), 4, 2)
            
            mA = self.path_re.match(doc_A['file_path'])
            mB = self.path_re.match(doc_B['file_path'])
            
            if mA and mB:
                pA = mA.groups()[0] + '/txt/' + mA.groups()[2] + '.tei.txt'
                pB = mB.groups()[0] + '/txt/' + mB.groups()[2] + '.tei.txt'
                
                txtA = open(pA).read()
                txtB = open(pB).read()

                try:
                    response, winner = self.bot.query(txtA, txtB)
                
                    if winner=='A':
                        winner = doc_A['doc_id']
                    elif winner=='B':
                        winner = doc_B['doc_id']
                    else:
                        winner = -1
                    
                    self.db.add_scores_pairwise(doc_A['doc_id'], doc_B['doc_id'], winner, response)
                
                except Exception as e:
                    self.msg_error('Python exception: ' + type(e).__name__)
                    winner = -2


            else:
                self.msg_error("RE failure for {} and/or {}.".format(selected[0], selected[1]))
                winner = -3
                
            self.msg(f"winner: {winner}", 4, 3)
                
            return winner


    def try_sort(self, docs, max_rounds=None, wait=10):
        '''This is a crude/simple sort (effectively BubbleSort).
        Normally, BubbleSort is ineficient. However, it is not so bad for
        nearlyed-sorted lists, and it allows us to simply 'ignore' the
        occassional failed comparisons. (This mostly works since sorting 
        operations are local.)'''
        
        n = len(docs)
    
        count = 0
        for i in range(n):
            for j in range(0, n - i - 1):
                
                if max_rounds is None or count<max_rounds:
                
                    count += 1
                    self.msg(f'try_sort {count} (i,j = {i},{j}): ', 4, 1)
                    
                    winner = self.compare_documents(docs[j], docs[j+1])

                    if winner<0:
                        # The comparison failed.
                        # For now, we do nothing.
                        pass
                    
                    elif winner==docs[j]['doc_id']: # doc_A is considered 'better'
                        # Already in the right order; no need to swap.
                        pass
                    
                    elif winner==docs[j+1]['doc_id']: # doc_B is considered 'better'
                        # Put doc_B at the lower index, since it is 'better'
                        docs[j], docs[j+1] = docs[j+1], docs[j] # Swap items
                        
                    else:
                        # It should be impossible to reach here!
                        self.msg_error('Impossible comparison outcome!')
                        
                    time.sleep(wait) # Don't overload API
                    
        return docs
        
   
        
        
    def score_sort(self, docs, num_iterations=5):
        '''Use the available scores to guess at ordering of docs.'''
        
        # First, compute some stats based on the scores.
        scores = self.db.get_scores_pairwise()
        
        docs = self.score_stats(docs, scores)
        
        # We can brutely sort by "win ratio".
        #docs = sorted(docs, key=lambda item: item['scoring_win_ratio'], reverse=True)


        # We can run some rounds of pairwise sorting, which forces pairs to be in the right order relative to each other
        #for i in range(num_iterations):
            #docs = self.apply_scores_pairwise(docs)
            
        
        
        outward, inward = self.determine_connections(docs, scores)
        
        # We can go through docs, and for each one try swapping with a neighbor
        # to decrease the number of bad/wrong connections.
        #docs = self.adjust_positions_connection_wise(docs, outward, inward, rounds=10)


        for i in range(num_iterations):
            # We can try random swaps (to avoid getting stuck in local minima).
            docs = self.consider_swaps_random(docs, outward, inward, rounds=200)
            
            # We can iterate through the list, checking whether local swaps
            # decrease the number of bad/wrong connections.
            docs = self.consider_swaps_connection_wise(docs, outward, inward, rounds=50)
        
        
        
        return docs

    
    
    def consider_swaps_connection_wise(self, docs, outward, inward, rounds=10):
        '''We go through the doc list, and for each pair consider whether swapping
        will improve things (decrease the number of bad/wrong connections that point
        the wrong way). This is slow and inefficient. However, because the graph of 
        pairwise score-connections is not well-behaved (the graph is inconsistent, 
        i.e. intransitive since it violates strict pairwise ordering consistency),
        this is as good as we can do.'''
        
        import random
        
        for trial in range(rounds):
        
            bad_out, bad_in, bad_total = self.count_bad_connections(docs, outward, inward)
            self.msg('Adjusting round {}/{} = {:.1f}%; {}+{} = {} bad connections'.format(trial, rounds, 100*trial/rounds, bad_out, bad_in,bad_total), 4, 1)
        
        
            for i in range(len(docs)-1):
                
                # Consider swapping the i and i+1 docs
                idx1, idx2 = i, i+1
                badness = self.calculate_badness(idx1, idx2, docs, outward, inward)
                
                # Do the swap
                docs[i], docs[i+1] = docs[i+1], docs[i]
                
                badness_after = self.calculate_badness(idx1, idx2, docs, outward, inward)
                
                if badness_after==badness:
                    # The badness didn't change; so randomly swap (or not)
                    # to create a random-walk effect
                    if random.random()>0.5:
                        # Undo the swap
                        docs[i+1], docs[i] = docs[i], docs[i+1]
                        
                elif badness_after>badness:
                    # Undo the swap
                    docs[i+1], docs[i] = docs[i], docs[i+1]
                    
                else: # badness_after<badness
                    pass # Keep the swap
            
            
            bad_out, bad_in, bad_total = self.count_bad_connections(docs, outward, inward)
            self.msg('Done round {}/{} = {:.1f}%; {}+{} = {} bad connections'.format(trial, rounds, 100*trial/rounds, bad_out, bad_in,bad_total), 6, 2)
            
            
        return docs
            
            
    def consider_swaps_random(self, docs, outward, inward, rounds=10):
        '''We go through the doc list, and consider random swaps.'''
        
        import random
        
        for trial in range(rounds):
        
            bad_out, bad_in, bad_total = self.count_bad_connections(docs, outward, inward)
            self.msg('Trial swap {}/{} = {:.1f}%; {}+{} = {} bad connections'.format(trial, rounds, 100*trial/rounds, bad_out, bad_in,bad_total), 4, 1)
        
        
            idx1, idx2 = random.randint(0, len(docs)-1), random.randint(0, len(docs)-1)
            if idx1!=idx2:
                badness = self.calculate_badness(idx1, idx2, docs, outward, inward)
                
                # Do the swap
                docs[idx1], docs[idx2] = docs[idx2], docs[idx1]
                
                badness_after = self.calculate_badness(idx1, idx2, docs, outward, inward)
                
                if badness_after==badness:
                    # The badness didn't change; so randomly swap (or not)
                    # to create a random-walk effect
                    if random.random()>0.5:
                        # Undo the swap
                        docs[idx1], docs[idx2] = docs[idx2], docs[idx1]
                        
                elif badness_after>badness:
                    # Undo the swap
                    docs[idx1], docs[idx2] = docs[idx2], docs[idx1]
                    
                else: # badness_after<badness
                    pass # Keep the swap
            
            
            bad_out, bad_in, bad_total = self.count_bad_connections(docs, outward, inward)
            self.msg('done trial {}/{} = {:.1f}%; {}+{} = {} bad connections'.format(trial, rounds, 100*trial/rounds, bad_out, bad_in,bad_total), 6, 2)
            
            
        return docs
                        
            
    def calculate_badness(self, idx1, idx2, docs, outward, inward):
        doc_id1, doc_id2 = docs[idx1]['doc_id'], docs[idx2]['doc_id']
        badness = 0
        
        # Before candidate swap:
        doc_ids = [doc['doc_id'] for doc in docs]
        
        # Figure out how many of the connections are 'bad'
        # (pointing the wrong way).
        badness += np.sum( [doc_ids.index(c)<idx1 for c in outward[doc_id1] ], dtype=int )
        badness += np.sum( [doc_ids.index(c)>idx1 for c in inward[doc_id1] ], dtype=int )
        badness += np.sum( [doc_ids.index(c)<idx2 for c in outward[doc_id2] ], dtype=int )
        badness += np.sum( [doc_ids.index(c)>idx2 for c in inward[doc_id2] ], dtype=int )
        
        return badness
            
    
    def adjust_positions_connection_wise(self, docs, outward, inward, rounds=10):
        '''We try to move the documents in the (semi-sorted) list to
        improve sorting. We are trying to minimize the number of 'wrong-
        way' connections.'''
        
        import random
        
        for i in range(rounds):
            
            bad_out, bad_in, bad_total = self.count_bad_connections(docs, outward, inward)
            self.msg('Adjusting round {}/{} = {:.1f}%; {}+{} = {} bad connections'.format(i, rounds, 100*i/rounds, bad_out, bad_in,bad_total))
            
            doc_ids = [doc['doc_id'] for doc in docs]
            random.shuffle(doc_ids)
            
            for doc_id in doc_ids:
                docs = self.consider_position_doc(doc_id, docs, outward, inward)

            bad_out, bad_in, bad_total = self.count_bad_connections(docs, outward, inward)
            self.msg('Done round {}/{} = {:.1f}%; {}+{} = {} bad connections'.format(i, rounds, 100*i/rounds, bad_out, bad_in,bad_total))
            
        return docs
                
                
    def count_bad_connections(self, docs, outward, inward):
        
        doc_ids = [doc['doc_id'] for doc in docs]
        bad_out, bad_in = 0, 0
        
        for doc in docs:
            doc_id = doc['doc_id']
            idx = doc_ids.index(doc_id)
            bad_out += np.sum( [doc_ids.index(c)<idx for c in outward[doc_id] ], dtype=int )
            bad_in += np.sum( [doc_ids.index(c)>idx for c in inward[doc_id] ], dtype=int )
            
        return bad_out, bad_in, bad_out+bad_in
    
                
    def consider_position_doc(self, doc_id, docs, outward, inward):
    
        # Current ordering of docs:
        doc_ids = [doc['doc_id'] for doc in docs]
        idx = doc_ids.index(doc_id)
        doc = docs[idx]
        
        num_out = len(outward[doc_id])
        num_in = len(inward[doc_id])
        self.msg('doc_id={}: {} connections (beats {}, is beat by {})'.format(doc_id, num_out+num_in, num_out, num_in), 6, 1)

        # This is an explicit way to keep track of connections
        # (but this is slow/redundant)
        #n, good, bad = 0, 0, 0
        #for connection in outward[doc_id]:
            #n += 1
            #idxc = doc_ids.index(connection)
            #if idxc>idx:
                #good += 1
            #else:
                #bad += 1
        #for connection in inward[doc_id]:
            #n += 1
            #idxc = doc_ids.index(connection)
            #if idxc<idx:
                #good += 1
            #else:
                #bad += 1                
        
        # Figure out how many of the connections from/to this doc are 'bad'
        # (pointing the wrong way).
        bad_out = np.sum( [doc_ids.index(c)<idx for c in outward[doc_id] ], dtype=int )
        bad_in = np.sum( [doc_ids.index(c)>idx for c in inward[doc_id] ], dtype=int )
        
        self.msg(f'{bad_out}+{bad_in} = {bad_out+bad_in} bad connections', 6, 2)
        
        if bad_out+bad_in>0:
        
            if bad_out>bad_in:
                # We should move this doc to lower index on the list
                docs[idx], docs[idx-1] = docs[idx-1], docs[idx]
                self.msg(f'moved {doc_id} left', 6, 2)
            
            if bad_in>bad_out:
                # We should move this doc to higher index on the list
                docs[idx], docs[idx+1] = docs[idx+1], docs[idx]
                self.msg(f'moved {doc_id} right', 6, 2)

            else: # bad_out==bad_in
                # Don't bother moving it
                # TODO: Maybe move in a random direction?
                pass
        

        
        return docs
    
    
    
    def determine_connections(self, docs, scores):
        '''Get a list of all the pairwise connections between docs.
        outward connections point from doc A to B, where A "wins" over B.
        inward connections point from various docs towards A; i.e. those
        docs all beat A.'''
        
        from collections import defaultdict

        # Convert the data into an adjacency list
        outward = defaultdict(list)
        inward = defaultdict(list)
        for score in scores:
            if score['winner']>0:
                if score['winner']==score['doc_id_A']:
                    outward[ score['doc_id_A'] ].append( score['doc_id_B'] )
                    inward[ score['doc_id_B'] ].append( score['doc_id_A'] )
                    
                elif score['winner']==score['doc_id_B']:
                    outward[ score['doc_id_B'] ].append( score['doc_id_A'] )
                    inward[ score['doc_id_A'] ].append( score['doc_id_B'] )
                
                else:
                    # This is not possible
                    self.msg_error('winner recorded in db is impossible')
                
        return outward, inward
    
    
    def score_stats(self, docs, scores):
        
        unpaired = 0
        for i, doc in enumerate(docs):
            t = doc['title'][:64] if doc['title'] else ''
            e = '...' if doc['title'] and len(doc['title'])>64 else ''
            self.msg('{}: doc_id={} {}{}'.format(i+1, doc['doc_id'], t, e))
            
            doc['index'] = i
            
            # How many times was this doc analyzed?
            doc['scoring_count'] = np.sum([ 1 for score in scores if score['doc_id_A']==doc['doc_id'] or score['doc_id_B']==doc['doc_id'] ])
            
            # How many times did it win?
            doc['scoring_wins'] = np.sum([ 1 for score in scores if score['winner']==doc['doc_id'] ])
            
            if doc['scoring_count']>0:
                doc['scoring_win_ratio'] = doc['scoring_wins'] / doc['scoring_count']
            else:
                unpaired += 1
                doc['scoring_win_ratio'] = 0.50
            
            self.msg('    wins: {}/{} = {:.1f}%'.format(doc['scoring_wins'], doc['scoring_count'], 100.*doc['scoring_win_ratio']))
            
            doc['x'], doc['y'] = doc['index'], 100.*doc['scoring_win_ratio']
            
            
        self.msg(f'{unpaired} docs were never paired')            
        
        return docs
    
        
    def apply_scores_pairwise(self, docs):
        '''We sort the list of docs, using the scores_pairwise from the database.
        Since this pairwise scores are not necessarily exhaustive, this operation
        is not guaranteed to result in a perfect sort.'''
        
        scores = self.db.get_scores_pairwise()
        
        self.msg('Applying {:,d} scores for {:,d} docs ({:.1f}%)'.format(len(scores), len(docs), 100.*len(scores)/len(docs)), 3, 0)
        
        num_swaps = 0
        for score in scores:
            if score['winner']>0:
                doc_ids = [ doc['doc_id'] for doc in docs ]
                idx_A = doc_ids.index( score['doc_id_A'] )
                idx_B = doc_ids.index( score['doc_id_B'] )
                
                if score['winner']==score['doc_id_A']:
                    if idx_A>idx_B: # A should be lower idx but isn't
                        docs[idx_B], docs[idx_A] = docs[idx_A], docs[idx_B] # Swap
                        num_swaps += 1
                
                elif score['winner']==score['doc_id_B']:
                    if idx_B>idx_A: # B should be lower idx
                        docs[idx_A], docs[idx_B] = docs[idx_B], docs[idx_A] # Swap
                        num_swaps += 1
                
                else:
                    # This is not possible
                    self.msg_error('winner recorded in db is impossible')
                    
                    
        self.msg('swapped {}/{} = {:.1f}%'.format(num_swaps, len(scores), 100.*num_swaps/len(scores)), 4, 1)
            
        return docs
                
                    
                
        
        
        
    
    def random_comparisons(self, rounds=10, wait=10):
        '''Pick two docs at random, and compare them to each other.'''
        
        import random
        import re
        
        self.path_re = re.compile('(^\/.+)(\/xml\/)(.+)(\.tei\.xml)$')
        
        self.bot = CompareBot(self.configuration)
        
        self.start_database()
        
        docs = self.db.get_docs()
        
        doc_ids = [ doc['doc_id'] for doc in docs ]
        
        for i in range(rounds):
            # Pick two documents
            selected = random.sample(doc_ids, 2)
            self.msg("Round {}/{} ({:.1f}%): Comparing doc {} and {}.".format(i+1, rounds, 100.*(i+1)/rounds, selected[0], selected[1]), 3)


            doc_A = docs[ doc_ids.index(selected[0]) ]
            doc_B = docs[ doc_ids.index(selected[1]) ]
            
            winner = self.compare_documents(doc_A, doc_B)
                    
            time.sleep(wait) # Don't overload API


    def semi_random_comparisons(self, rounds=10, wait=10):
        
        import random
        import re
        
        self.path_re = re.compile('(^\/.+)(\/xml\/)(.+)(\.tei\.xml)$')
        
        self.bot = CompareBot(self.configuration)
        
        self.start_database()
        
        docs = self.db.get_docs()
        
        doc_ids = [ doc['doc_id'] for doc in docs ]
        
        for i in range(rounds):
            for j, doc in enumerate(docs):
                # Pick one document
                selected = random.sample(doc_ids, 1)
                if selected[0]!=doc['doc_id']:
                    self.msg("Round {}/{} ({:.1f}%), doc {}/{} ({:.1f}%): Comparing doc {} and {}.".format(i+1, rounds, 100.*(i+1)/rounds, j, len(docs), 100.*(j+1)/len(docs), doc['doc_id'], selected[0]), 3)


                    doc_A = docs[ doc_ids.index(doc['doc_id']) ]
                    doc_B = docs[ doc_ids.index(selected[0]) ]
                    
                    winner = self.compare_documents(doc_A, doc_B)
                            
                    time.sleep(wait) # Don't overload API                


    def rank_documents(self, wait=5):
        
        #import random
        import re
        
        
        self.path_re = re.compile('(^\/.+)(\/xml\/)(.+)(\.tei\.xml)$')
        
        self.bot = CompareBot(self.configuration)
        
        self.start_database()
        
        #self.random_comparisons(rounds=50)
        #self.semi_random_comparisons(rounds=1, wait=wait)
        
        #docs = self.db.get_docs()
        docs = np.load('documents_sorted.npy', allow_pickle=True)
        
        #docs = self.try_sort(docs, max_rounds=20, wait=wait)
        docs = self.score_sort(docs, num_iterations=20)
        
        
        
        
        np.save('documents_sorted.npy', docs, allow_pickle=True)
        
        if True:
            for i, doc in enumerate(docs):
                t = doc['title'][:64] if doc['title'] else ''
                e = '...' if doc['title'] and len(doc['title'])>64 else ''
                print('{}: doc_id={} {}{}'.format(i+1, doc['doc_id'], t, e))
        
        
        
        
