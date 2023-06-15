#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Filename: ingest_pdfs.py
Author: Kevin G. Yager, Brookhaven National Laboratory
Email: kyager@bnl.gov
Date created: 2023-04-03
Description:
 Defines various LLM chatbots.
"""

from .Base import Base
from .LLMs import *

class SummarizeBot(Base):
    '''Takes a paragraph of text and summarizes it.'''
    
    def __init__(self, configuration, name='SummarizeBot', **kwargs):
        super().__init__(name=name, **kwargs)
        
        
        self.configuration = configuration
        api_key = self.configuration['openai']['api_key']
        self.model = self.configuration['openai']['model']
        self.token_limit = self.configuration['openai']['model_token_limit']
        self.LLM = OpenAI_LLM(api_key=api_key, model=self.model, token_limit=self.token_limit, name='OpenAI')
        
        
        instruction = "Your task is to take blocks of text from scientific journal articles, and summarize them in a concise way. Capture as much information as possible, whiel avoiding repetition. Omit details very specific to the particular paper. Emphasize insights that are generalizable. Do not make things up."

        self.request_template = "Summarize this (from the paper {}):\n\n{}"
        
        # Reserve this space in the message
        self.header_len = len(instruction) + len(self.request_template) + 100 
        
        self.background = [
            {"role": "system", "content" : instruction}
            ]
        
        
    def get_request_window(self, ratio=0.6):
        '''Returns an estimate for a reasonable size of the input text.'''
        
        return int( (self.LLM.char_limit - self.header_len)*ratio )
        
        
    def summarize(self, text, doc_name='<UNKNOWN>', msg_cutoff=35):
        
        request = self.request_template.format(doc_name, text)
        
        messages = self.background.copy()
        messages.append({"role": "user", "content": request})
        
        
        self.msg(f'''Asking for text summary ({len(text):,d} chars): "{text[:msg_cutoff]}"...''', 3, 2)
        
        response = self.LLM.chat_completion(messages)
        
        self.msg(f'''Received response ({len(response):,d} chars): "{response[:msg_cutoff]}"...''', 3, 2)
        
        return response
        
        
        
class EmbedBot(Base):
    '''Takes a chunk of text and computed an embedding vector.'''
    
    # https://platform.openai.com/docs/guides/embeddings/what-are-embeddings
    
    def __init__(self, configuration, name='EmbedBot', **kwargs):
        super().__init__(name=name, **kwargs)
        
        
        self.configuration = configuration
        api_key = self.configuration['openai']['api_key']
        self.model = self.configuration['openai']['embedding_model']
        self.token_limit = self.configuration['openai']['embedding_model_token_limit']
        self.LLM = OpenAI_LLM(api_key=api_key, model=self.model, token_limit=self.token_limit, name='OpenAI')
        
        
    def compute_embedding(self, text):
        if len(text)>self.LLM.char_limit:
            self.msg_error(f"Supplied text size ({len(text):,d} chars) greater than limit ({self.LLM.char_limit:,d} chars)")
        result = self.LLM.embedding(text)
        
        self.msg(f'''Received embedding (dimension {len(result):,d})''', 3, 2)
        
        return result



class ImageBot(Base):
    '''Takes an input image, finds similar images.'''

    def __init__(self, configuration, name='ImageBot', **kwargs):
        super().__init__(name=name, **kwargs)

        self.db = None
        self.configuration = configuration
        
        from .image_embedding import Image_Embedding
        self.ImgEmbed = Image_Embedding(verbosity=self.verbosity)


    # Database interaction
    ##################################################
    def start_database(self, force=False):
        if force or self.db is None:
            from .dbase import DocumentDatabase
            self.db = DocumentDatabase(config=self.configuration['doc_database'], verbosity=self.verbosity)
        
    def close_database(self):
        self.db.close()
        
    def load_embedding_lookup_file(self, infile='./image_lookup.npy'):
        self.start_database()
        self.db.load_image_embedding_lookup_file(infile=infile)


    # User interaction with bot
    ##################################################

    def query(self, image_file, mode='cosine'):
        
        vector = self.ImgEmbed.image_to_embedding(image_file)
        
        if mode=='cosine':
            similarities = self.db.order_images_by_similarity(vector)
        elif mode=='euclid':
            similarities = self.db.order_images_by_distance(vector)
        else:
            self.msg_error(f'mode not recognized: {mode}')
        
        return similarities

        
    def query_txt(self, image_file, outfile='response.html', mode='cosine', exclude=None, num_cutoff=50):

        similarities = self.query(image_file, mode=mode)
        txt = self.generate_txt(similarities, image_file, num_cutoff=num_cutoff, exclude=exclude)
        
        if outfile is not None:
            with open(outfile, 'w') as fout:
                fout.write(txt)
            
        return txt

    
    def query_html(self, image_file, outfile='response.html', mode='cosine', exclude=None, num_cutoff=50):
        
        similarities = self.query(image_file, mode=mode)
        html = self.generate_html(similarities, image_file, num_cutoff=num_cutoff, exclude=exclude)
        
        if outfile is not None:
            with open(outfile, 'w') as fout:
                fout.write(html)
            
        return html


    def generate_txt(self, images, image_file, num_cutoff=50, exclude=None):
        
        txt = ''

        txt += f'Images similar to: {image_file}\n'
        
        count = 0
        for image in images:
            if count<num_cutoff:
                similarity, suffix, image_id, file_name = image
                image_info = self.db.get_image(image_id, table_suffix=suffix)
                
                if (exclude is None) or (exclude not in image_info['file_path']):
                    src = image_info['file_path']
                    txt += f'{count+1}\t{src}\n'
                    count += 1
            
            
        return txt
        

    def generate_html(self, images, image_file, num_cutoff=50, exclude=None):
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Images similar to: {image_file.name}</title>\n'''
    
        html += '''
    <style>
        .box {
            width: 800px;
            border: 1px solid #ccc;
            padding: 10px;
            margin: 10px;
            text-align: center;
            background-color: #f9f9f9;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
        }

        .image {
            max-width: 600px;
            height: auto;
            margin-bottom: 10px;
        }

        .caption {
            font-size: 14px;
            text-align: left;
        }
    </style>
</head>
<body>'''

        
        html += f'<div class="title">Images similar to: <a href="{image_file}">{image_file.name}</a></div>\n'
        html += f'<a href="{image_file}"><img src="{image_file}" alt="{image_file.name}"></a>\n'

        count = 0
        for image in images:
            if count<num_cutoff:
                similarity, suffix, image_id, file_name = image
                image_info = self.db.get_image(image_id, table_suffix=suffix)
                
                if (exclude is None) or (exclude not in image_info['file_path']):
                    
                    html += '<div class="box">\n'
                    name = image_info['file_name']
                    src = image_info['file_path']
                    html += f'<div class="caption"><a href="{src}">{src}</a></div>\n'
                    html += f'<a href="{src}"><img class="image" src="{src}" alt="{name}"></a>\n'
                    html += '</div>\n'
                    
                    count += 1
            
            
        html += '</body>\n</html>\n'
        
        return html
    
    
        
class FigureBot(ImageBot):
    '''Takes an input image, finds similar images.'''

    def __init__(self, configuration, name='FigureBot', **kwargs):
        super().__init__(configuration, name=name, **kwargs)

        

    # Database interaction
    ##################################################
    def load_embedding_lookup_file(self, infile='./figure_lookup.npy'):
        self.start_database()
        self.db.load_figure_embedding_lookup_file(infile=infile)



        
    # User interaction with bot
    ##################################################

    def query(self, image_file, mode='cosine'):
        
        vector = self.ImgEmbed.image_to_embedding(image_file)
        
        if mode=='cosine':
            similarities = self.db.order_figures_by_similarity(vector)
        elif mode=='euclid':
            similarities = self.db.order_figures_by_distance(vector)
        else:
            self.msg_error(f'mode not recognized: {mode}')
        
        return similarities
    

    def generate_html(self, figures, image_file, mode='cosine', exclude=None, num_cutoff=50):
        
        html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Images similar to: {image_file.name}</title>\n'''
    
        html += '''
    <style>
        .box {
            width: 800px;
            border: 1px solid #ccc;
            padding: 10px;
            margin: 10px;
            text-align: center;
            background-color: #f9f9f9;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }

        .title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
        }

        .image {
            max-width: 600px;
            height: auto;
            margin-bottom: 10px;
        }

        .caption {
            font-size: 14px;
            text-align: left;
        }
    </style>
</head>
<body>'''

        
        html += f'<div class="title">Figures similar to: <a href="{image_file}">{image_file.name}</a></div>\n'
        html += f'<a href="{image_file}"><img src="{image_file}" alt="{image_file.name}"></a>\n'

        
        for i, figure in enumerate(figures):
            if i<num_cutoff:
                similarity, suffix, doc_id, fig_id, file_name = figure
                figure_info = self.db.get_figure(fig_id, table_suffix=suffix)
                doc = self.db.get_doc(doc_id=figure_info['doc_id'])
                
                name = f'Figure {figure_info["fig_num"]} from {figure_info["file_name"]}'
                
                html += '<div class="box">\n'
                html += f'<div class="title">{name}</div>\n'
                html += f'<div class="caption">{doc["doc_name"]}</a></div>\n'
                src = doc['pdf_file']
                if src is None:
                    src = doc['file_path']
                html += f'<div class="caption"><a href="{src}">{src}</a></div>\n'
                src = figure_info['file_path']
                html += f'<a href="{src}"><img class="image" src="{src}" alt="{name}"></a>\n'
                html += f'<div class="caption">{figure_info["fig_caption"]}</div>\n'
                html += '</div>\n'
            
            
        html += '</body>\n</html>\n'
        
        return html
            



        
class AnswerBot(Base):
    '''Answers questions, using the provided messages for context.'''
    
    def __init__(self, configuration, name='AnswerBot', max_response_len=3600, **kwargs):
        super().__init__(name=name, **kwargs)

        self.db = None        
        
        self.configuration = configuration
        api_key = self.configuration['openai']['api_key']

        # For embedding lookup
        self.embedding_model = self.configuration['openai']['embedding_model']
        self.embedding_token_limit = self.configuration['openai']['embedding_model_token_limit']
        
        # For chat responses
        self.model = self.configuration['openai']['model']
        self.token_limit = self.configuration['openai']['model_token_limit']
        self.LLM_chat = OpenAI_LLM(api_key=api_key, model=self.model, token_limit=self.token_limit, name='OpenAI')
        
        self.LLM_embed = self.LLM_chat
        
        instruction = "You are a chatbot that answers questions, especially about scientific research. You are given snippets from relevant published journal articles. You should provide a meaningful response to the user question, based on your general knowledge and the information in the provided snippets. Do not make things up. Quote and refer to the sources where appropriate."

        # Reserve this space in the message
        self.header_len = len(instruction)
        
        self.background = [
            {"role": "system", "content" : instruction}
            ] 
        
        
        self.max_response_len = max_response_len # chars
        self.max_context_len = self.LLM_chat.char_limit - self.header_len - self.max_response_len
        
        self.print_window()
        
        
        
    def print_window(self):
        
        total = self.header_len + self.max_context_len + self.max_response_len
        
        w, t, c = 0.187, 0.25, 1
        self.msg('----------------------------------------------')
        self.msg('|              |  words  |  tokens |  chars  |')
        self.msg('| WINDOW       | {:7,d} | {:7,d} | {:7,d} |'.format(int(self.LLM_chat.word_limit), int(self.token_limit), int(self.LLM_chat.char_limit)))
        self.msg('| Instructions | {:7,d} | {:7,d} | {:7,d} |'.format(int(self.header_len*w), int(self.header_len*t), int(self.header_len*c)))
        self.msg('| Context      | {:7,d} | {:7,d} | {:7,d} |'.format(int(self.max_context_len*w), int(self.max_context_len*t), int(self.max_context_len*c)))
        self.msg('| Response     | {:7,d} | {:7,d} | {:7,d} |'.format(int(self.max_response_len*w), int(self.max_response_len*t), int(self.max_response_len*c)))
        self.msg('| TOTAL        | {:7,d} | {:7,d} | {:7,d} |'.format(int(total*w), int(total*t), int(total*c)))
        self.msg('----------------------------------------------')
        
        
        
        
        
    # Database interaction
    ##################################################
    def start_database(self, force=False):
        
        if force or self.db is None:
            from .dbase import DocumentDatabase
            self.db = DocumentDatabase(config=self.configuration['doc_database'], verbosity=self.verbosity)
        
    def close_database(self):
        self.db.close()
        
    def load_embedding_lookup_file(self, infile='./chunk_lookup.npy'):
        self.start_database()
        self.db.load_embedding_lookup_file(infile=infile)


    # LLM
    ##################################################
    def get_embedding(self, text):
        
        vector = self.LLM_embed.embedding(text, model=self.embedding_model)
        
        return vector
        

    def construct_prompt(self, question, separator="\n*", doc_name=True):
        '''Generate the text preample that we feed in for a question.'''
        
        vector = self.get_embedding(question)
        
        most_relevant_chunks = self.db.order_chunks_by_similarity(vector)
        
        separator_len = len(separator)
        
        chosen_sections = []
        chosen_sections_len = 0
        chosen_sections_text = []

        for similarity, table_suffix, doc_id, chunk_num in most_relevant_chunks:
            
            # Add contexts until we run out of space.        
            chunk = self.db.get_chunk(doc_id, chunk_num, table_suffix=table_suffix)
            content = chunk['content']
            
            if doc_name:
                content = "From [{}]: {}".format(chunk['doc_name'], content)
                #content = "From ts=_{}_ [{}]: {}".format(table_suffix, chunk['doc_name'], content)
                
            
            chosen_sections_len += len(content) + separator_len
            if chosen_sections_len > self.max_context_len:
                break

            chosen_sections.append(separator + content.replace("\n", " "))
            chosen_sections_text.append(str(content))


        prompt = """Context:\n""" + "".join(chosen_sections)

        # Useful diagnostic information
        self.msg(f"Selected {len(chosen_sections):,d} document sections (prompt {len(prompt):,d} chars)", 3, 1)
        #self.msg("\n".join(chosen_sections_text), 4, 2)

        #print(prompt)
        
        return prompt


        
    # User interaction with bot
    ##################################################
        
    def query(self, question, use_context=True, doc_name=True, msg_cutoff=35):
        '''Answer user question by retrieving chunks, and doing a call
        to the LLM API.'''
        
        messages = self.background.copy()
        
        if use_context:
            context_content = self.construct_prompt(question, doc_name=doc_name)
            messages.append({"role": "system", "content" : context_content})
        
        messages.append({"role": "user", "content" : question})


        self.msg(f'''Asking question ({len(question):,d} chars): "{question[:msg_cutoff]}"...''', 3, 2)
        
        response = self.LLM_chat.chat_completion(messages)
        
        self.msg(f'''Received response ({len(response):,d} chars): "{response[:msg_cutoff]}"...''', 3, 2)
        
        return response


    def mock_query(self, question, use_context=True, doc_name=True, savefile='./mock_query.txt', msg_cutoff=35):
        '''Prepare to query the LLM, but don't actually send the request.
        Instead, just save the preparred query to disk.'''
        
        messages = self.background.copy()
        
        if use_context:
            context_content = self.construct_prompt(question, doc_name=doc_name)
            messages.append({"role": "system", "content" : context_content})
        
        messages.append({"role": "user", "content" : question})


        self.msg(f'''Saving question ({len(question):,d} chars): "{question[:msg_cutoff]}"...''', 3, 2)
        with open(savefile, 'w') as fout:
            for message in messages:
                fout.write(message['content']+'\n\n')
        
     
        


class AnswerBot_Claude(AnswerBot):
    
    def __init__(self, configuration, name='AnswerBot', **kwargs):
        Base.__init__(self, name=name, **kwargs)

        self.db = None        
        
        self.configuration = configuration
        

        # For embedding lookup
        api_key = self.configuration['openai']['api_key']
        self.embedding_model = self.configuration['openai']['embedding_model']
        self.embedding_token_limit = self.configuration['openai']['embedding_model_token_limit']
        self.LLM_embed = OpenAI_LLM(api_key=api_key, model=self.embedding_model, token_limit=self.embedding_token_limit, name='OpenAI')        
        
        # For chat responses
        api_key = self.configuration['anthropic']['api_key']
        self.model = self.configuration['anthropic']['model']
        self.token_limit = self.configuration['anthropic']['model_token_limit']
        self.max_tokens_to_sample = self.configuration['anthropic']['max_tokens_to_sample']
        self.LLM_chat = Anthropic_LLM(api_key=api_key, model=self.model, token_limit=self.token_limit, max_tokens_to_sample=self.max_tokens_to_sample, name='Claude')
        
        instruction = "You are a chatbot that answers questions, especially about scientific research. You are given snippets from relevant published journal articles. You should provide a meaningful response to the user question, based on your general knowledge and the information in the provided snippets. Do not make things up. Quote and refer to the sources where appropriate."

        # Reserve this space in the message
        self.header_len = len(instruction)
        
        self.background = [
            {"role": "system", "content" : instruction}
            ] 
        
        
        self.max_response_len = self.max_tokens_to_sample # chars
        self.max_context_len = self.LLM_chat.char_limit - self.header_len - self.max_response_len
        
        self.print_window()
        
          
      
