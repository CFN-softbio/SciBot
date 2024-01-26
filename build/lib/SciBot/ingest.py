#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Filename: ingest.py
Author: Kevin G. Yager, Brookhaven National Laboratory
Email: kyager@bnl.gov
Date created: 2023-04-03
Description:
 Basic capabilities for ingesting raw PDF documents, and putting them in the
database.
"""


# Limitations:
# - Ingestion code assumes that each PDF has a distinct filename

from .Base import Base
from pathlib import Path



class Ingester(Base):
    def __init__(self, configuration, name='Ingester', **kwargs):
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
    def do_step(self, this_step, step_initial, step_final=None):
        '''Convenience method for controlling which steps in a protocol get executed.
        By default, we do all the steps. However, one can restrict the steps that are
        run, by controlling where we start (step_initial) and optionally stopping
        at some point (step_final).'''
        
        if step_final is not None and step_initial>step_final:
            self.msg_error(f'No steps will execute since step_initial>step_final ({step_initial}>{step_final})')
        
        return this_step>=step_initial and (step_final is None or this_step<=step_final)



class DocumentIngester(Ingester):

    def __init__(self, configuration, name='docs', **kwargs):
        super().__init__(configuration, name=name, **kwargs)
    

    # Conversions
    ##################################################
        
    def pdfs_to_xmls(self, source_dir, output_dir=None, force=False):
        '''Convert a folder of PDF files into corresponding XML files.
        We use Grobid for this, and thus assume that a valid Grobid
        server is running and available using the parameters specified
        in the grobid config.json file.'''
        
        self.msg(f"Converting PDFs to XML from directory: {source_dir}")
        
        from grobid_client.grobid_client import GrobidClient
        
        config_file = self.configuration['grobid']['config_file']

        client = GrobidClient(config_path=config_file)
        client.process("processFulltextDocument", source_dir, output=output_dir, consolidate_citations=False, force=force, verbose=True)


    def pdfs_to_db(self, source_dir, force=False):
        for infile in source_dir.glob('*.pdf'):
            self.msg(f"Adding PDF path to database: {infile}")
            xml_name = infile.with_suffix('.tei.xml').name
            doc_id = self.db.get_doc_id(xml_name)
            pdf_file = self.db.get_pdf_path(doc_id)
            self.msg(f"Found doc_id: {doc_id}; pdf_file = {pdf_file}", 6, 3)
            if force or pdf_file is None:
                self.db.set_pdf_path(doc_id, str(infile))
                self.msg(f"Updated doc_id={doc_id} with pdf_file: {infile}", 4, 3)
            else:
                self.msg(f"No update for doc_id: {doc_id}", 6, 3)
            

    def xml_to_chunks(self, xml_file, chunk_length=None, overlap_length=None):
        
        self.msg(f"Converting XML to chunks: {xml_file}")
        
        xml_document = self.load_xml_file(xml_file)
        
        text, md = self.xml_to_plaintext(xml_document)
        compression = 100.*len(text)/len(xml_document)
        self.msg(f"Generated plaintext {len(text):,d} chars ({compression:.0f}%)", 3, 2)
        
        if chunk_length is None:
            chunk_length = self.configuration['chunk_length']
        if overlap_length is None:
            overlap_length = self.configuration['chunk_overlap_length']
        
        chunks = self.split_overlapping_chunks(text, chunk_length, overlap_length)
        
        return chunks, md


    def xml_to_paragraphs(self, xml_file):
        
        self.msg(f"Converting XML to paragraphs: {xml_file}")
        
        xml_document = self.load_xml_file(xml_file)
        
        paragraphs, md = self.xml_to_plaintext_paragraphs(xml_document)
        self.msg(f"Generated {len(paragraphs):,d} paragraphs", 3, 2)
        
        return paragraphs, md
        
        
    def load_xml_file(self, xml_file):
        '''Load an xml file from disk.'''
        
        p = Path(xml_file) # Conver to Path() object (if not already)
        
        with open(p, 'r') as fin:
            xml_document = fin.read()
        
        self.msg(f"Loaded XML ({len(xml_document):,d} chars): {p.name} ", 3, 2)        
        
        return xml_document
        
        
    def xml_to_plaintext(self, xml_document):
        '''Remove all the xml tags from a xml document.
        While we're at it, we also extract some useful meta-data.'''
        
        # Parse the XML document using BeautifulSoup
        soup = self.xml_to_soup(xml_document)
        
        # Extract document header/meta-data information
        md = self.xml_metadata(soup)
        md['len_xml_chars'] = len(xml_document)


        # Extract text (removing all HTML/XML tags), 
        # and add a blank line between separated paragraph ("<p>") blocks
        text = ''
        for tag in soup.find_all():
            if tag.name == 'p' and tag.text.strip():
                text += tag.text.strip() + '\n\n'
            elif not tag.find_all() and tag.text.strip():
                text += tag.text.strip() + ' '
                
        return text, md
    
    
    def xml_to_plaintext_paragraphs(self, xml_document):
        '''Remove all the xml tags from a xml document.
        While we're at it, we also extract some useful meta-data.'''
        
        # Parse the XML document using BeautifulSoup
        soup = self.xml_to_soup(xml_document)
        
        # Extract document header/meta-data information
        md = self.xml_metadata(soup)
        md['len_xml_chars'] = len(xml_document)

        # Extract text (removing all HTML/XML tags), 
        # and add a blank line between separated paragraph ("<p>") blocks
        text = ''
        paragraphs = []
        for tag in soup.find_all():
            if tag.name == 'p' and tag.text.strip():
                text += tag.text.strip() + '\n\n'
                paragraphs.append(text)
                text = ''
            elif not tag.find_all() and tag.text.strip():
                text += tag.text.strip() + ' '
                
        return paragraphs, md
    
    
    def xml_to_soup(self, xml_document, clean=True):
        '''Parse xml into a BeautifulSoup object.'''

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(xml_document, 'lxml')

        if clean:
            # Remove the appInfo tag that labels this as a GROBID result
            selects = soup.findAll('appinfo')
            for match in selects:
                match.decompose()

            # Remove bibliography/references sections
            for match in soup.findAll('listbibl'):
                match.decompose()

            soup.smooth()
        
        return soup



    def xml_metadata(self, soup):
        '''Extract some metadata from a xml TEI document.'''
        
        md = {}
        header = soup.find('teiheader')
        md['title'] = header.find('title').find(text=True)
        
        try:
            md['first_author'] = header.find('surname').find(text=True)
        except:
            md['first_author'] = '?'
        
        authors_list = []
        for author_tag in header.find_all('author'):
            pers_name_tag = author_tag.find('persname')
            if pers_name_tag:
                forenames = pers_name_tag.find_all('forename')
                full_forename = ' '.join([forename.text for forename in forenames])
                surname = pers_name_tag.find('surname').text
                authors_list.append(f'{full_forename} {surname}')
                
        try:
            md['last_author'] = surname
        except:
            md['last_author'] = '?'
        md['authors_list'] = authors_list
        md['authors'] = '; '.join(authors_list)
        
        
        return md


    

    def split_overlapping_chunks(self, text, chunk_length, overlap_length):
        '''Takes a text string, and breaks it into chunks.'''
        
        chunks = []
        index = 0
        
        while index < (len(text) - chunk_length + 1):
            chunk = text[index:index + chunk_length]
            chunks.append(chunk)
            index += chunk_length - overlap_length
            
        # Final chunk
        chunk = text[index:]
        if len(chunk) > chunk_length:
            self.msg_error(f"final chunk length {len(chunk):,d} chars is longer than chunk_length={chunk_length:,d}")
        chunks.append(chunk)
        
        return chunks




    def xml_to_summaries(self, xml_file, chunk_length=None, overlap_amount=0.2):
        
        self.msg(f"Summarizing XML: {xml_file}")
        
        xml_document = self.load_xml_file(xml_file)
        
        text, md = self.xml_to_plaintext(xml_document)
        compression = 100.*len(text)/len(xml_document)
        self.msg(f"Generated plaintext {len(text):,d} chars ({compression:.0f}%)", 3, 2)
        

        from .bots import SummarizeBot
        summary_bot = SummarizeBot(configuration=self.configuration, name='sum_bot', verbosity=self.verbosity)
        
        doc_name = '''{} et al. "{}"'''.format(md['first_author'], md['title'])
        
        if chunk_length is None:
            # Estimate reasonable length based on LLM
            chunk_length = summary_bot.get_request_window()
        overlap_length = int(chunk_length*overlap_amount)        
        
        chunks = self.split_overlapping_chunks(text, chunk_length, overlap_length)
        
        summaries = []
        for i, chunk in enumerate(chunks):
            response = self.summarize_chunk(chunk, doc_name, summary_bot)
            summaries.append(response)
        
        return summaries, md
    
    
    def summarize_chunk(self, text, doc_name, bot):
        
        if (len(doc_name) + len(text)) > bot.LLM.char_limit:
            self.msg_warning(f'Supplied text ({len(text):,d} chars) + doc_name ({len(doc_name):,d} chars) are over LLM limit ({bot.LLM.char_limit} chars).')
            
        response = bot.summarize(text, doc_name)
        
        return response


    def document_to_figures(self, xml_file, pdf_dir, fig_dir, force=False):
        
        doc_id = self.db.get_doc_id(xml_file.name)
        xml_document = self.load_xml_file(xml_file)
        
        pdf_file = str(xml_file.name)[:-len('.tei.xml')] + '.pdf'
        pdf_file = pdf_dir / pdf_file
        
        
        from .image_embedding import Image_Embedding
        ImgEmbed = Image_Embedding(verbosity=self.verbosity)
        model = ImgEmbed.get_model_name()
        
        # Parse the XML document using BeautifulSoup
        soup = self.xml_to_soup(xml_document)
        
        # Iterate over all 'figure' tags and extract information from 'graphic' tags
        for i, figure in enumerate(soup.find_all('figure')):
            graphic = figure.find('graphic', coords=True)
            if graphic:
                label = figure.find('label')
                if label:
                    try:
                        fig_num = int(label.get_text())
                    except:
                        self.msg_error(f"Figure label is not a number: {label}")
                        fig_num = 9000+i
                    
                else:
                    self.msg_error("No label tag found for figure.")
                    fig_num = 9000+i
                
                
                outfile = pdf_file.stem + '_fig{:d}.png'.format(fig_num)
                outfile = fig_dir / outfile
                
                if force or not outfile.is_file():
                    
                    # Get figure coordinates
                    coords = graphic['coords'].split(',')
                    coords = [float(coord) for coord in coords]
                    page, x0, y0, xw, yw = coords
                    page = int(page)
                    
                    # Extract pixels for figure
                    pixmap = self.pdf_to_pixmap(pdf_file, page=page, region=(x0, y0, x0+xw, y0+yw) )
                    
                    # Save figure to disk
                    self.msg(f'Saving Figure {fig_num} to: {outfile}', 4, 2)
                    pixmap.save(outfile)

                    # Get figure caption
                    figdesc = figure.find('figdesc')
                    if figdesc:
                        caption = figdesc.get_text()
                    else:
                        caption = '<N/A>'
                        
                    
                    # Compute embedding vector for this image
                    vector = ImgEmbed.image_to_embedding(outfile)
                    self.msg(f'Obtained image embedding vector ({len(vector)} dims)', 4, 2)

                    # Add figure to database
                    #self.db.add_figure(doc_id, fig_num, caption, str(outfile), str(outfile.name))
                    self.db.add_figure_w_embedding(doc_id, fig_num, caption, str(outfile), str(outfile.name), model, vector.tolist())
                    #vector_retrieved = self.db.get_figure_embedding(file_name=str(outfile.name))
                    
                    
                    #categories = ['scientific image', 'graph', 'CAD diagram', 'painting']
                    #probs = ImgEmbed.image_class_probabilities(outfile, categories)
                    
                    
                else:
                    self.msg(f'File for Figure {fig_num} already exists: {outfile}', 4, 2)
                    
                    
                     
    
    def pdf_to_pixmap(self, pdf_file, page, region, zoom=2):
        
        self.msg(f'Extracting region {region} from page {page:d} of: {pdf_file}', 4, 2)
        
        import fitz  # PyMuPDF

        doc = fitz.open(pdf_file) # Open the PDF file
        page = doc[page-1] # Select the page number (0-based)
        
        # Extract the region as a pixmap
        mat = fitz.Matrix(zoom, zoom)  # Zooming matrix
        pixmap = page.get_pixmap(matrix=mat, clip=region)
        
        return pixmap
            
        


    # Iterations through documents
    ##################################################
    def xmls_to_txt(self, xml_dir, txt_dir, force=False):
        '''Converts all the xml files into plaintext equivalents.'''
        
        infiles = xml_dir.glob('./*.xml')

        for infile in infiles:
            outfile = txt_dir / infile.with_suffix('.txt').name
            if force or not outfile.is_file():
                self.msg(f'Converting {infile.name}', 3, 0)
                
                xml_document = self.load_xml_file(infile)
                text, md = self.xml_to_plaintext(xml_document)
                
                with open(outfile, 'w') as fout:
                    fout.write(text)
                
                self.msg(f'Saved {outfile}', 3, 1)

        
    def xmls_to_summaries(self, xml_dir, summary_dir, force=False):
        '''Takes xmls of scientific documents, and generates a shortened
        version of the document, by summarize it block-by-block.'''

        infiles = xml_dir.glob('./*.xml')

        for infile in infiles:
            outfile = summary_dir / infile.with_suffix('.txt').name
            if force or not outfile.is_file():
            
                summaries, md = self.xml_to_summaries(infile, chunk_length=None, overlap_amount=0.2)
                
                self.msg(f'Got {len(summaries):,d} summaries', 3, 1)
                
                text = '\n\n'.join(summaries)
                with open(outfile, 'w') as fout:
                    fout.write(text)

            
    def documents_to_figures(self, pdf_dir, xml_dir, fig_dir, force=False):
        
        infiles = xml_dir.glob('./*.xml')

        for infile in infiles:
            #if infile.name.startswith('24-'): # abla
            self.msg(f'Extracting figures from {infile.name}', 3, 0)
            
            self.document_to_figures(infile, pdf_dir=pdf_dir, fig_dir=fig_dir, force=force)

        
        
    def xmls_to_database(self, xml_dir, force=False, randomize=False):
        
        infiles = xml_dir.glob('./*.xml')
        
        if randomize:
            # For testing purposes
            infiles = [infile for infile in infiles]
            import random
            random.shuffle(infiles)
        
        for infile in infiles:
            if force or not self.db.doc_exists(infile):
                self.msg(f'Ingesting {infile.name}', 3, 0)
                
                chunks, md = self.xml_to_chunks(infile)
                
                # Add document to database
                doc_id = self.db.add_doc(str(infile), md)
                
                # Add chunks
                self.db.add_chunks(doc_id, chunks, table_suffix='', md=md)


    def summaries_to_database(self, summary_dir, table_suffix='_summary', chunk_length=None, overlap_length=None):
        
        if chunk_length is None:
            chunk_length = self.configuration['chunk_length']
        if overlap_length is None:
            overlap_length = self.configuration['chunk_overlap_length']
        
        
        infiles = summary_dir.glob('./*.txt')
        for infile in infiles:
            self.msg(f'Ingesting summary {infile.name}', 3, 0)
            
            with open(infile) as fin:
                text = fin.read()
            
            doc_id = self.db.get_doc_id(infile.with_suffix('.xml').name)
            
            chunks = self.split_overlapping_chunks(text, chunk_length, overlap_length)

            self.db.add_chunks(doc_id, chunks, table_suffix=table_suffix)
        


    def calc_chunk_embeddings(self, force=False, doc_name=True, table_suffix=''):
        
        from .bots import EmbedBot
        embed_bot = EmbedBot(configuration=self.configuration, name='embed')
        model = embed_bot.model
        
        
        chunk_list = self.db.get_chunks_list(table_suffix=table_suffix)
        
        for chunk_item in chunk_list:
            if force or not self.db.embedding_exists(chunk_item['doc_id'], chunk_item['chunk_num'], table_suffix=table_suffix):
                self.msg(f"Calculating embedding for doc_id={chunk_item['doc_id']} chunk #{chunk_item['chunk_num']:,d}", 3, 0)
                
                chunk = self.db.get_chunk(chunk_item['doc_id'], chunk_item['chunk_num'], table_suffix=table_suffix)
                content = chunk['content']
                
                if doc_name:
                    content = "[{}] {}".format(chunk['doc_name'], content)
                    
                vector = embed_bot.compute_embedding(content)
                
                self.db.add_embedding(chunk_item['doc_id'], chunk_item['chunk_num'], model, vector, table_suffix=table_suffix)
                
                
    def save_embedding_lookup_file(self, table_suffixes=[''], outfile='./chunk_lookup.npy'):
        
        self.msg(f'Generating chunk lookup file: {outfile}', 3, 0)
        model = self.configuration['openai']['embedding_model']
        self.db.save_embedding_lookup_file(table_suffixes=table_suffixes, outfile=outfile, model=model)
        
        
    def save_figure_embedding_lookup_file(self, outfile='./figure_lookup.npy', table_suffixes=[''], model='CLIP_ViT-B/32'):

        self.msg(f'Generating figure lookup file: {outfile}', 3, 0)
        self.db.save_figure_embedding_lookup_file(table_suffixes=table_suffixes, outfile=outfile, model=model)



    # Database interaction
    ##################################################
    def create_tables(self, documents=False, chunks=False, embeddings=False, table_suffix='', close=True):
        self.start_database()
        if documents:
            self.db.create_table_documents()
        if chunks:
            self.db.create_table_chunks(table_suffix=table_suffix)
        if embeddings:
            self.db.create_table_embeddings(table_suffix=table_suffix)
        if close:
            self.close_database()
        


    # Protocols/workflows
    ##################################################
    def ingest_pdfs(self, source_dir, step_initial=1, step_final=None, make_txt=True, make_summaries=False, force=False):
        
        # The procedure is broken into steps, allowing the user to only perform certain steps,
        # or to selectively re-do certain steps.
        
        si, sf = step_initial, step_final # Use shorter names to make code below easier to read
        
        xml_dir = self.configuration['document_dir'] / 'xml/'
        Path(xml_dir).mkdir(parents=True, exist_ok=True)
        
        
        if self.do_step(0, si, sf):
            # If this is the first time ingestion is being run, then the database
            # might need to be set-up.
            self.create_tables(documents=True, chunks=True, embeddings=True, close=True)
            self.create_tables(documents=False, chunks=True, embeddings=True, table_suffix='_summary', close=True)
        
        
        if self.do_step(1, si, sf):
            # Convert a directory of PDFs into XMLs (using Grobid)
            self.pdfs_to_xmls(source_dir, xml_dir, force=force)

            
            
        if self.do_step(2, si, sf) and make_txt:
            # This step is optional. We can output plaintext versions of documents.
            # These are not used for any downstream tasks, but could be useful to
            # the user.
            txt_dir = self.configuration['document_dir'] / 'txt/'
            Path(txt_dir).mkdir(parents=True, exist_ok=True)
            self.xmls_to_txt(xml_dir=xml_dir, txt_dir=txt_dir, force=force)
            
                        
        self.start_database()


        if self.do_step(3, si, sf):
            # Update the database with the source PDF paths
            self.pdfs_to_db(source_dir, force=force)

            
        if self.do_step(4, si, sf):
            # Break each XML document into chunks, and put those in the database
            self.xmls_to_database(xml_dir, force=force)
            
        if self.do_step(5, si, sf):
            # Compute embedding for each chunk
            self.calc_chunk_embeddings(force=force)


        if make_summaries:
            # We can generate more concise versions of documents, and
            # break those into a separate set of lookup chunks.
            
            summary_dir = self.configuration['document_dir'] / 'summary/'
            Path(summary_dir).mkdir(parents=True, exist_ok=True)

            
            if self.do_step(10, si, sf):
                self.xmls_to_summaries(xml_dir=xml_dir, summary_dir=summary_dir, force=force)
                
            if self.do_step(11, si, sf):
                self.summaries_to_database(summary_dir, table_suffix='_summary')
                
            if self.do_step(12, si, sf):
                self.calc_chunk_embeddings(force=force, table_suffix='_summary')


        if self.do_step(15, si, sf):
            # Extract figures from PDFs
            fig_dir = self.configuration['document_dir'] / 'figures/'
            self.documents_to_figures(pdf_dir=source_dir, xml_dir=xml_dir, fig_dir=fig_dir, force=force)
            
        if self.do_step(16, si, sf):
            outfile = './figure_lookup.npy'
            self.save_figure_embedding_lookup_file(outfile=outfile)



            
        if self.do_step(20, si, sf):
            # Generate rapid lookup file
            outfile = './chunk_lookup.npy'
            model = self.configuration['openai']['embedding_model']
            table_suffixes = ['']
            if make_summaries:
                table_suffixes.append('_summary')
                
            self.save_embedding_lookup_file(table_suffixes=table_suffixes, outfile=outfile)
            
        self.close_database()
        
        
            
            
        
            
        
            
class ImageIngester(Ingester):
    
    def __init__(self, configuration, name='docs', **kwargs):
        super().__init__(configuration, name=name, **kwargs)


    # Iterations through files
    ##################################################
    def add_images(self, image_dir, recursive=True, force=False):
        
        from .image_embedding import Image_Embedding
        ImgEmbed = Image_Embedding(verbosity=self.verbosity)
        model = ImgEmbed.get_model_name()
        
        self.add_images_directory(image_dir, ImgEmbed, recursive=recursive, force=force)
        
        
    def add_images_directory(self, image_dir, ImgEmbed, recursive=True, force=False):
        
        model = ImgEmbed.get_model_name()
        
        for infile in image_dir.glob('*'):
            
            if infile.is_dir():
                if recursive:
                    self.add_images_directory(infile, ImgEmbed, recursive=recursive, force=force)
            
            elif infile.suffix in ['.tiff', '.tif', '.png', '.jpg', '.jpeg']:
                
                if self.db.image_exists(str(infile)) and not force:
                    self.msg(f'Skipping (already in db): {infile}')
                
                else:
                    self.msg(f'Ingesting: {infile}')
                    
                    vector = ImgEmbed.image_to_embedding(infile)
                    self.msg(f'Obtained image embedding vector ({len(vector)} dims)', 4, 2)
                    
                    self.db.add_image_w_embedding(str(infile), infile.name, model, vector.tolist(), table_suffix='')
                    
            

    # Operations
    ##################################################
    def save_image_embedding_lookup_file(self, outfile='./image_lookup.npy', table_suffixes=[''], model='CLIP_ViT-B/32'):

        self.msg(f'Generating image lookup file: {outfile}', 3, 0)
        self.db.save_image_embedding_lookup_file(table_suffixes=table_suffixes, outfile=outfile, model=model)
    
    
    # Database interaction
    ##################################################
    def create_tables(self, table_suffix='', close=True):
        self.start_database()
        self.db.create_table_images(table_suffix=table_suffix)
        if close:
            self.close_database()


    # Protocols/workflows
    ##################################################
    def ingest_images(self, img_dir, step_initial=1, step_final=None, force=False):

        # The procedure is broken into steps, allowing the user to only perform certain steps,
        # or to selectively re-do certain steps.
        si, sf = step_initial, step_final # Use shorter names to make code below easier to read

        if self.do_step(0, si, sf):
            # If this is the first time ingestion is being run, then the database
            # might need to be set-up.
            self.create_tables(close=True)


        self.start_database()

        if self.do_step(3, si, sf):
            # Update the database with the source PDF paths
            self.add_images(img_dir, recursive=True, force=force)


        if self.do_step(20, si, sf):
            # Generate rapid lookup file
            outfile = './image_lookup.npy'
            self.save_image_embedding_lookup_file(outfile=outfile)
            
            
        self.close_database()

