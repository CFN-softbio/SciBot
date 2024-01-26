#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Filename: image_embedding.py
Author: Kevin G. Yager, Brookhaven National Laboratory
Email: kyager@bnl.gov
Date created: 2023-05-08
Description:
 Compute an embedding vector for an image input.
"""

from .Base import Base

import torch
import torchvision.transforms as transforms
from PIL import Image
from clip import clip

class Image_Embedding(Base):
    
    def __init__(self, name='img', **kwargs):
        super().__init__(name=name, **kwargs)
        
        # Load the pretrained CLIP model
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.msg(f'Using device: {self.device}', 3, 2)
        self.model, self.preprocess = clip.load("ViT-B/32", device=self.device)
        
        
    def get_model_name(self):
        
        return 'CLIP_ViT-B/32'
    
        
    def image_to_embedding(self, image_path):
        
        image = Image.open(image_path)
        
        return self.image_data_to_embedding(image)


    def image_data_to_embedding(self, image):
        
        # Load and preprocess an image
        image_input = self.preprocess(image).unsqueeze(0).to(self.device)
        
        # Calculate the image embeddings
        with torch.no_grad():
            image_features = self.model.encode_image(image_input)

        image_features = image_features.cpu().numpy()
        vector = image_features[0]

        self.msg(f'Computed embedding vector: {vector}', 7, 3)
        
        return vector
    

    def image_class_probabilities(self, image_path, categories):

        # Load and preprocess an image
        image = Image.open(image_path)
        image_input = self.preprocess(image).unsqueeze(0).to(self.device)
        
        
        text = clip.tokenize(categories).to(self.device)
        
        with torch.no_grad():
            image_features = self.model.encode_image(image_input)
            text_features = self.model.encode_text(text)
            
            logits_per_image, logits_per_text = self.model(image_input, text)
            probs = logits_per_image.softmax(dim=-1).cpu().numpy()


        results = [f'{category}: {100*prob:.1f}%' for category, prob in zip(categories, probs[0])]
        results_str = '; '.join(results)
        self.msg(f'class probabilities: {results_str}', 4, 2)
            
        return probs
        
