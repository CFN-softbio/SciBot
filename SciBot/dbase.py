#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: dbase.py
Author: Kevin G. Yager, Brookhaven National Laboratory
Email: kyager@bnl.gov
Date created: 2023-04-03
Description:
 Manages connections to databases, where document chunks can be
stored.
"""

from .Base import Base
import mysql.connector
import numpy as np

class DocumentDatabase(Base):

    # Basic MySQL interaction
    ##################################################
    
    def __init__(self, config, name='dbase', **kwargs):
        
        super().__init__(name=name, **kwargs)
        
        self.config = config
        
        self.msg(f"Connecting to MySQL database: {self.config['database']}")
        
        # Establish the connection
        self.connection = mysql.connector.connect(**config)
        # Create a cursor object to interact with the database
        self.cursor = self.connection.cursor(dictionary=True)
        
        self.embeddings = None


    
    def query(self, sql):
        
        # Execute a query
        self.cursor.execute(sql)

        # Fetch the results
        rows = self.cursor.fetchall()
            
        return rows


    def query_values(self, sql, values):
        
        # Execute a query
        self.cursor.execute(sql, values)

        # Fetch the results
        rows = self.cursor.fetchall()
            
        return rows


    def close(self):
        self.cursor.close()
        self.connection.close()
        
    def __del__(self):
        self.close()



    # Create tables within database
    ##################################################

    def create_table_documents(self):
        sql = """
CREATE TABLE `documents` (
  `doc_id` int NOT NULL,
  `file_path` text NOT NULL,
  `file_name` text NOT NULL,
  `len_chars` int NOT NULL,
  `title` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `authors` text CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci,
  `doc_name` text NOT NULL,
  `datetime_added` datetime NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
ALTER TABLE `documents`
  ADD PRIMARY KEY (`doc_id`);
ALTER TABLE `documents`
  MODIFY `doc_id` int NOT NULL AUTO_INCREMENT;
COMMIT;
"""

        self.cursor.execute(sql)

    def create_table_chunks(self, table_suffix=''):
        sql = f"""
CREATE TABLE `chunks{table_suffix}` (
  `chunk_num` int NOT NULL,
  `doc_id` int NOT NULL,
  `content` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;"""

        self.cursor.execute(sql)

    def create_table_embeddings(self, table_suffix=''):
        sql = f"""
CREATE TABLE `embeddings{table_suffix}` (
  `doc_id` int NOT NULL,
  `chunk_num` int NOT NULL,
  `model` text NOT NULL,
  `vector` blob NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;"""

        self.cursor.execute(sql)

    def create_table_images(self, table_suffix=''):
        sql = f"""
CREATE TABLE `images{table_suffix}` (
  `image_id` int NOT NULL,
  `file_path` text NOT NULL,
  `file_name` text NOT NULL,
  `embedding_model` text NOT NULL,
  `embedding_vector` blob
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;"""

        self.cursor.execute(sql)
        

    # Documents
    ##################################################
    def get_doc(self, doc_id, table_suffix=''):
        
        sql = f"""SELECT * FROM documents{table_suffix} WHERE doc_id='{doc_id}' ;"""
        
        rows = self.query(sql)
        
        if len(rows)!=1:
            self.msg_warning(f"{len(rows)} documents{table_suffix} matches for doc_id={doc_id}")
            
        return rows[0]

    
    def doc_exists(self, infile):
        
        sql = f"""SELECT doc_id FROM documents WHERE file_name like '{infile.name}';"""
        
        rows = self.query(sql)
        
        return len(rows)>0
    

    def make_doc_name(self, md):
        
        first = md['first_author']
        last = md['last_author']
        if first==last:
            doc_name = '''{} et al. "{}"'''.format(first, md['title'])
        else:
            doc_name = '''{}, {}, et al. "{}"'''.format(first, last, md['title'])
            
        return doc_name
        

    def add_doc(self, infile, md):
        
        sql = "INSERT INTO documents (file_path, file_name, len_chars, title, authors, doc_name, datetime_added) VALUES (%s, %s, %s, %s, %s, %s, now())"
        doc_name = self.make_doc_name(md)
        values = (infile, infile.name, md['len_xml_chars'], md['title'], md['authors'], doc_name)
        self.cursor.execute(sql, values)
        self.connection.commit()
        
        # Get the id
        doc_id = self.cursor.lastrowid
        
        self.msg(f"Inserted new document (doc_id={doc_id})", 5, 2)
        
        return doc_id
        
        
    def get_doc_id(self, name):
        
        sql = f"""SELECT doc_id FROM documents WHERE file_name like '{name}';"""
        
        rows = self.query(sql)
        
        if len(rows)!=1:
            self.msg_warning(f"{len(rows)} document matches for name={name}")
        
        return int(rows[0]['doc_id'])
        
        
    def get_pdf_path(self, doc_id):
        
        sql = f"""SELECT pdf_file FROM documents WHERE doc_id={doc_id};"""
        
        rows = self.query(sql)
        
        if len(rows)!=1:
            self.msg_warning(f"{len(rows)} document matches for doc_id={doc_id}")
        
        return rows[0]['pdf_file']
    
    def set_pdf_path(self, doc_id, pdf_file):
        
        sql = """UPDATE documents SET pdf_file = %s WHERE doc_id = %s ;"""
        values = (pdf_file, doc_id)
        
        self.cursor.execute(sql, values)
        self.connection.commit()
    
    
        
    # Chunks
    ##################################################
        
    def chunk_exists(self, doc_id, chunk_num, table_suffix=''):
        
        sql = f"""SELECT doc_id FROM chunks{table_suffix} WHERE doc_id='{doc_id}' AND chunk_num='{chunk_num}' ;"""
        
        rows = self.query(sql)
        
        return len(rows)>0
    
        
    def add_chunk(self, doc_id, chunk_num, chunk, table_suffix=''):
        
        sql = "INSERT INTO chunks{} (chunk_num, doc_id, content) VALUES (%s, %s, %s)".format(table_suffix)
        values = (chunk_num, doc_id, chunk)

        self.cursor.execute(sql, values)
        
        
        
    def add_chunks(self, doc_id, chunks, table_suffix='', md={}):
        
        for i, chunk in enumerate(chunks):
            self.add_chunk(doc_id, i+1, chunk, table_suffix=table_suffix)
            
        self.connection.commit()
        
        self.msg(f"Added {len(chunks):,d} chunks (doc_id={doc_id})", 5, 2)
            
        
    def get_chunks_list(self, table_suffix=''):
        
        sql = f"""SELECT doc_id, chunk_num FROM chunks{table_suffix} ;"""
        
        rows = self.query(sql)
        
        return rows
        
        
    def get_chunk_only(self, doc_id, chunk_num, table_suffix=''):
        sql = f"""SELECT * FROM chunks{table_suffix} WHERE doc_id='{doc_id}' AND chunk_num='{chunk_num}' ;"""
        
        rows = self.query(sql)
        
        if len(rows)!=1:
            self.msg_warning(f"{len(rows)} chunk{table_suffix} matches for doc_id={doc_id} chunk #{chunk_num:,d}")
            
        return rows[0]
        
        
    def get_chunk(self, doc_id, chunk_num, table_suffix=''):
        sql = f"""
SELECT c.doc_id, c.chunk_num, c.content, d.doc_name FROM chunks{table_suffix} AS c
INNER JOIN documents AS d
ON c.doc_id = d.doc_id
WHERE c.doc_id='{doc_id}' AND c.chunk_num='{chunk_num}' 
ORDER BY c.doc_id, c.chunk_num ASC;"""

        rows = self.query(sql)
        
        if len(rows)!=1:
            self.msg_warning(f"{len(rows)} chunk{table_suffix} matches for doc_id={doc_id} chunk #{chunk_num:,d}")
            
        return rows[0]
        
        
        
    # Embeddings (text)
    ##################################################
        
    def embedding_exists(self, doc_id, chunk_num, table_suffix=''):
        
        sql = f"""SELECT doc_id FROM embeddings{table_suffix} WHERE doc_id='{doc_id}' AND chunk_num='{chunk_num}' ;"""
        
        rows = self.query(sql)
        
        return len(rows)>0        
        
        
    def add_embedding(self, doc_id, chunk_num, model, vector, table_suffix=''):
        
        byte_array = np.asarray(vector).tobytes()
        
        sql = "INSERT INTO embeddings{} (doc_id, chunk_num, model, vector) VALUES (%s, %s, %s, %s)".format(table_suffix)
        values = (doc_id, chunk_num, model, byte_array)
        self.cursor.execute(sql, values)
        
        self.connection.commit()
                
        
    def get_embedding(self, doc_id, chunk_num, table_suffix=''):
        
        sql = f"""SELECT * FROM embeddings{table_suffix} WHERE doc_id='{doc_id}' AND chunk_num='{chunk_num}' ;"""
        
        rows = self.query(sql)
        
        if len(rows)!=1:
            self.msg_warning(f"{len(rows)} embedding{table_suffix} matches for doc_id={doc_id} chunk #{chunk_num:,d}")
        
        byte_array = rows[0]['vector']
        vector = np.frombuffer(byte_array)

        return vector

    
    def generate_embedding_lookup_table(self, model='text-embedding-ada-002', table_suffix=''):
        
        sql = f"""SELECT * FROM embeddings{table_suffix} WHERE model='{model}' ORDER BY doc_id, chunk_num ASC"""
        
        rows = self.query(sql)

        doc_ids = []
        chunk_nums = []
        vectors = []
        for row in rows:
            byte_array = row['vector']
            vector = np.frombuffer(byte_array)
            
            doc_ids.append(row['doc_id'])
            chunk_nums.append(row['chunk_num'])
            vectors.append(vector)
            
        doc_ids = np.asarray(doc_ids)
        chunk_nums = np.asarray(chunk_nums)
        vectors = np.asarray(vectors)
        
        table_suffix = np.repeat(table_suffix, len(doc_ids))
        
        results = { 'table_suffix':table_suffix, 'doc_ids': doc_ids, 'chunk_nums': chunk_nums, 'vectors': vectors }
        self.embeddings = results
        
        return results


    def generate_embedding_lookup(self, table_suffixes, model='text-embedding-ada-002'):
        
        results = None

        for suffix in table_suffixes:
            
            result_current = self.generate_embedding_lookup_table(model=model, table_suffix=suffix)
            
            if results is None:
                results = result_current
            else:
                for key, value in results.items():
                    results[key] = np.concatenate( (value, result_current[key]) )
            
        return results
        
            
    def save_embedding_lookup_file(self, table_suffixes, outfile='./chunk_lookup.npy', model='text-embedding-ada-002'):
        '''Grab embeddings from MySQL database, and save them to a npy file for easier lookup.'''
        
        results = self.generate_embedding_lookup(table_suffixes=table_suffixes, model=model)
        
        np.save(outfile, results, allow_pickle=True)
        
        
    def load_embedding_lookup_file(self, infile='./chunk_lookup.npy'):
        '''Load the quick lookup file.'''
        
        data = np.load(infile, allow_pickle=True).item()
        self.embeddings = data
        #self.embeddings = { 'table_suffix': data['table_suffix'], 'doc_ids': data['doc_ids'], 'chunk_nums': data['chunk_nums'], 'vectors': data['vectors'] }
        


    # Find relevant chunks using embeddings
    ##################################################
    # c.f. tutorials:
    #https://platform.openai.com/docs/guides/embeddings
    #https://blog.bitsrc.io/customizing-an-openai-chatbot-with-embeddings-fdc9ec859bbb
    #https://github.com/openai/openai-cookbook/blob/main/examples/Question_answering_using_embeddings.ipynb
    #https://www.mlq.ai/fine-tuning-gpt-3-question-answer-bot/
    #https://dev.to/manumaan/use-chatgpt-to-query-your-internal-website-5e2a

    def vector_similarity(self, x, y):
        """
        Returns the similarity between two vectors.

        Because OpenAI Embeddings are normalized to length 1, the cosine similarity is the same as the dot product.
        """
        return np.dot(np.array(x), np.array(y))


    def vector_distance(self, x, y):
        """
        Returns the Euclidian distance between two points.
        """
        return np.linalg.norm(x - y)


    def order_chunks_by_similarity(self, vector):
        """
        Return the list of document chunks, sorted by relevance in descending order.
        """
        
        #contexts: dict[(str, str), np.array]
        contexts = zip( self.embeddings['table_suffix'], self.embeddings['doc_ids'], self.embeddings['chunk_nums'], self.embeddings['vectors'] )

        similarities = sorted([
                (self.vector_similarity(vector, chunk_embedding), table_suffix, doc_id, chunk_num) for table_suffix, doc_id, chunk_num, chunk_embedding in contexts
            ], reverse=True)
        
        return similarities



    # Figures and Embeddings (image)
    ##################################################
    def get_figure(self, fig_id, table_suffix=''):
        
        sql = f"""SELECT * FROM figures{table_suffix} WHERE fig_id='{fig_id}' ;"""
        
        rows = self.query(sql)
        
        if len(rows)!=1:
            self.msg_warning(f"{len(rows)} figure{table_suffix} matches for fig_id={fig_id}")
            
        row = rows[0]
        byte_array = row['embedding_vector']
        row['vector'] = np.frombuffer(byte_array)
            
        return row
        
        
    def add_figure(self, doc_id, fig_num, fig_caption, file_path, file_name, table_suffix=''):
        
        sql = "INSERT INTO figures{} (doc_id, fig_num, fig_caption, file_path, file_name) VALUES (%s, %s, %s, %s, %s)".format(table_suffix)
        values = (doc_id, fig_num, fig_caption, file_path, file_name)

        self.cursor.execute(sql, values)
        self.connection.commit()


    def add_figure_w_embedding(self, doc_id, fig_num, fig_caption, file_path, file_name, model, vector, table_suffix=''):
        
        byte_array = np.asarray(vector).tobytes()
        
        sql = "INSERT INTO figures{} (doc_id, fig_num, fig_caption, file_path, file_name, embedding_model, embedding_vector) VALUES (%s, %s, %s, %s, %s, %s, %s)".format(table_suffix)
        values = (doc_id, fig_num, fig_caption, file_path, file_name, model, byte_array)

        self.cursor.execute(sql, values)
        self.connection.commit()
        
        
    def get_figure_embedding(self, file_name, table_suffix=''):
        
        sql = f"""SELECT * FROM figures{table_suffix} WHERE file_name='{file_name}' ;"""
        
        rows = self.query(sql)
        
        if len(rows)!=1:
            self.msg_warning(f"{len(rows)} figures{table_suffix} matches for file_name={file_name}")
        
        byte_array = rows[0]['embedding_vector']
        vector = np.frombuffer(byte_array)

        return vector
    

    def generate_figure_embedding_lookup_table(self, model='CLIP_ViT-B/32', table_suffix=''):
        
        sql = f"""SELECT * FROM figures{table_suffix} WHERE embedding_model='{model}' ORDER BY fig_id ASC"""
        
        rows = self.query(sql)

        doc_ids = []
        fig_ids = []
        file_names = []
        vectors = []
        for row in rows:
            byte_array = row['embedding_vector']
            vector = np.frombuffer(byte_array)
            
            doc_ids.append(row['doc_id'])
            fig_ids.append(row['fig_id'])
            file_names.append(row['file_name'])
            vectors.append(vector)
            
        doc_ids = np.asarray(doc_ids)
        fig_ids = np.asarray(fig_ids)
        file_names = np.asarray(file_names)
        vectors = np.asarray(vectors)
        
        table_suffix = np.repeat(table_suffix, len(fig_ids))
        
        results = { 'table_suffix':table_suffix, 'doc_ids': doc_ids, 'fig_ids': fig_ids, 'file_names': file_names, 'vectors': vectors }
        self.figure_embeddings = results
        
        return results    
    
    
    def generate_figure_embedding_lookup(self, table_suffixes, model='CLIP_ViT-B/32'):
        
        results = None

        for suffix in table_suffixes:
            
            result_current = self.generate_figure_embedding_lookup_table(model=model, table_suffix=suffix)
            
            if results is None:
                results = result_current
            else:
                for key, value in results.items():
                    results[key] = np.concatenate( (value, result_current[key]) )
            
        return results    
    
    
    def save_figure_embedding_lookup_file(self, table_suffixes, outfile='./figure_lookup.npy', model='CLIP_ViT-B/32'):
        '''Grab image embeddings from MySQL database, and save them to a npy file for easier lookup.'''
        
        results = self.generate_figure_embedding_lookup(table_suffixes=table_suffixes, model=model)
        
        np.save(outfile, results, allow_pickle=True)
        
        
    def load_figure_embedding_lookup_file(self, infile='./figure_lookup.npy'):
        '''Load the quick lookup file.'''
        
        data = np.load(infile, allow_pickle=True).item()
        self.figure_embeddings = data
    
    
    def order_figures_by_similarity(self, vector):
        """
        Return the list of figures/images, sorted by relevance in descending order.
        """
        
        contexts = zip( self.figure_embeddings['table_suffix'], self.figure_embeddings['doc_ids'], self.figure_embeddings['fig_ids'], self.figure_embeddings['file_names'], self.figure_embeddings['vectors'] )

        similarities = sorted([
                (self.vector_similarity(vector, image_embedding), table_suffix, doc_id, fig_id, file_name) for table_suffix, doc_id, fig_id, file_name, image_embedding in contexts
            ], reverse=True)
        
        return similarities
    
    
    def order_figures_by_distance(self, vector):
        """
        Return the list of figures/images, sorted by relevance in descending order.
        """
        
        contexts = zip( self.figure_embeddings['table_suffix'], self.figure_embeddings['doc_ids'], self.figure_embeddings['fig_ids'], self.figure_embeddings['file_names'], self.figure_embeddings['vectors'] )

        similarities = sorted([
                (self.vector_distance(vector, image_embedding), table_suffix, doc_id, fig_id, file_name) for table_suffix, doc_id, fig_id, file_name, image_embedding in contexts
            ], reverse=False)
        
        return similarities
    
    
    
    # Images
    ##################################################
    def image_exists(self, infile, table_suffix=''):
        
        sql = f"""SELECT image_id FROM images{table_suffix} WHERE file_path like %s;"""
        values = (infile, )
        
        rows = self.query_values(sql, values)
        
        return len(rows)>0
    
    def get_image(self, image_id, table_suffix=''):
        
        sql = f"""SELECT * FROM images{table_suffix} WHERE image_id='{image_id}' ;"""
        
        rows = self.query(sql)
        
        if len(rows)!=1:
            self.msg_warning(f"{len(rows)} images{table_suffix} matches for image_id={image_id}")
            
        row = rows[0]
        byte_array = row['embedding_vector']
        row['vector'] = np.frombuffer(byte_array)
            
        return row    
    
    def add_image_w_embedding(self, file_path, file_name, model, vector, table_suffix=''):
        
        byte_array = np.asarray(vector).tobytes()
        
        sql = "INSERT INTO images{} (file_path, file_name, embedding_model, embedding_vector) VALUES (%s, %s, %s, %s)".format(table_suffix)
        values = (file_path, file_name, model, byte_array)
        
        self.cursor.execute(sql, values)
        self.connection.commit()
        
        
    def get_image_embedding(self, file_name, table_suffix=''):
        
        sql = f"""SELECT * FROM images{table_suffix} WHERE file_name=%s ;"""
        values = (file_name, )
        
        rows = self.query_values(sql, values)
        
        if len(rows)!=1:
            self.msg_warning(f"{len(rows)} images{table_suffix} matches for file_name={file_name}")
        
        byte_array = rows[0]['embedding_vector']
        vector = np.frombuffer(byte_array)

        return vector
    
    
    
    def generate_image_embedding_lookup_table(self, model='CLIP_ViT-B/32', table_suffix=''):
        
        sql = f"""SELECT * FROM images{table_suffix} WHERE embedding_model='{model}' ORDER BY image_id ASC"""
        
        rows = self.query(sql)

        image_ids = []
        file_names = []
        vectors = []
        for row in rows:
            byte_array = row['embedding_vector']
            vector = np.frombuffer(byte_array)
            
            image_ids.append(row['image_id'])
            file_names.append(row['file_name'])
            vectors.append(vector)
            
        image_ids = np.asarray(image_ids)
        file_names = np.asarray(file_names)
        vectors = np.asarray(vectors)
        
        table_suffix = np.repeat(table_suffix, len(image_ids))
        
        results = { 'table_suffix':table_suffix, 'image_ids': image_ids, 'file_names': file_names, 'vectors': vectors }
        self.image_embeddings = results
        
        return results    
    
    
    def generate_image_embedding_lookup(self, table_suffixes, model='CLIP_ViT-B/32'):
        
        results = None

        for suffix in table_suffixes:
            
            result_current = self.generate_image_embedding_lookup_table(model=model, table_suffix=suffix)
            
            if results is None:
                results = result_current
            else:
                for key, value in results.items():
                    results[key] = np.concatenate( (value, result_current[key]) )
            
        return results    
    
    
    def save_image_embedding_lookup_file(self, table_suffixes, outfile='./image_lookup.npy', model='CLIP_ViT-B/32'):
        '''Grab image embeddings from MySQL database, and save them to a npy file for easier lookup.'''
        
        results = self.generate_image_embedding_lookup(table_suffixes=table_suffixes, model=model)
        
        np.save(outfile, results, allow_pickle=True)
        
        
    def load_image_embedding_lookup_file(self, infile='./image_lookup.npy'):
        '''Load the quick lookup file.'''
        
        data = np.load(infile, allow_pickle=True).item()
        self.image_embeddings = data
    
    
    def order_images_by_similarity(self, vector):
        """
        Return the list of figures/images, sorted by relevance in descending order.
        """
        
        contexts = zip( self.image_embeddings['table_suffix'], self.image_embeddings['image_ids'], self.image_embeddings['file_names'], self.image_embeddings['vectors'] )

        similarities = sorted([
                (self.vector_similarity(vector, image_embedding), table_suffix, image_id, file_name) for table_suffix, image_id, file_name, image_embedding in contexts
            ], reverse=True)
        
        return similarities
    
    
    def order_images_by_distance(self, vector):
        """
        Return the list of figures/images, sorted by Euclidian distance, in descending order.
        """
        
        contexts = zip( self.image_embeddings['table_suffix'], self.image_embeddings['image_ids'], self.image_embeddings['file_names'], self.image_embeddings['vectors'] )

        similarities = sorted([
                (self.vector_distance(vector, image_embedding), table_suffix, image_id, file_name) for table_suffix, image_id, file_name, image_embedding in contexts
            ], reverse=False)
        
        return similarities    



    # Messages (a.k.a. conversation threads)
    ##################################################
    def add_thread_message(self, thread_id, who, message_content):

        sql = "INSERT INTO messages (thread_id, date_time, who, message_content) VALUES (%s, NOW(), %s, %s)"
        values = (thread_id, who, message_content)
        
        self.cursor.execute(sql, values)
        self.connection.commit()
        
        
    def get_last_thread_message(self, thread_id):
        
        sql = f"""SELECT * FROM messages WHERE thread_id=%s ORDER BY date_time DESC LIMIT 1;"""
        values = (thread_id, )
        
        rows = self.query_values(sql, values)

        if len(rows)!=1:
            self.msg_warning(f"{len(rows)} messages returned for thread_id={thread_id}")
        
        return rows[0]
        
        
    def get_thread_messages(self, thread_id, cutoff=100):
        
        sql = f"""SELECT * FROM ( SELECT * FROM messages WHERE thread_id=%s ORDER BY date_time DESC LIMIT %s ) sub ORDER BY date_time ASC;"""
        values = (thread_id, cutoff)
        
        rows = self.query_values(sql, values)

        if len(rows)==0:
            self.msg_warning(f"{len(rows)} messages returned for thread_id={thread_id}")
        
        return rows       
        
        
        
