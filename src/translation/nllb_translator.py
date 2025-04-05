#!/usr/bin/env python3
"""
Translation module using MarianMT instead of NLLB

This module provides functionality to translate text between languages
using MarianMT models which are better supported and more reliable.
"""

import os
import logging
from typing import Dict, List, Optional, Union
from pathlib import Path

import torch
from transformers import MarianMTModel, MarianTokenizer

# Set up logging
logger = logging.getLogger(__name__)

class NLLBTranslator:
    """Translation service using MarianMT models"""
    
    # Mapping of language pairs to model names
    MODEL_MAP = {
        ("en", "es"): "Helsinki-NLP/opus-mt-en-es",
        ("es", "en"): "Helsinki-NLP/opus-mt-es-en",
        ("en", "ru"): "Helsinki-NLP/opus-mt-en-ru",
        ("ru", "en"): "Helsinki-NLP/opus-mt-ru-en",
    }
    
    def __init__(self, model_path: str, language_code_map: Dict[str, str] = None):
        """
        Initialize the translation models.
        
        Args:
            model_path: Not used for MarianMT as we load from Hugging Face
            language_code_map: Map of language codes to ISO codes
        """
        self.language_code_map = language_code_map or {
            "en-US": "en",
            "ru-RU": "ru", 
            "es-CO": "es"
        }
        
        # Log initialization info
        logger.info("Initializing MarianMT translator")
        
        try:
            # Determine device
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            logger.info(f"Using device: {self.device}")
            
            # We'll load models on demand instead of pre-loading all
            self.models = {}
            self.tokenizers = {}
            
            # Pre-load English-Spanish model
            key = ("en", "es")
            self._load_model(key)
            
            logger.info("MarianMT translator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize translator: {e}")
            raise
    
    def _load_model(self, key):
        """Load a model for the language pair"""
        if key not in self.MODEL_MAP:
            raise ValueError(f"No translation model available for {key[0]} to {key[1]}")
            
        model_name = self.MODEL_MAP[key]
        logger.info(f"Loading model {model_name}")
        self.models[key] = MarianMTModel.from_pretrained(model_name).to(self.device)
        self.tokenizers[key] = MarianTokenizer.from_pretrained(model_name)
        
    def _get_language_code(self, lang_code: str) -> str:
        """Get the ISO language code from a locale code"""
        return self.language_code_map.get(lang_code, lang_code.split('-')[0].lower())
    
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """
        Translate text from source language to target language
        
        Args:
            text: Text to translate
            source_lang: Source language code (e.g., "en-US")
            target_lang: Target language code (e.g., "ru-RU")
            
        Returns:
            Translated text
        """
        if not text or not text.strip():
            return text
            
        # Get ISO language codes
        src_lang = self._get_language_code(source_lang)
        tgt_lang = self._get_language_code(target_lang)
        
        # If source and target are the same, return the original text
        if src_lang == tgt_lang:
            return text
        
        try:
            # Check if we have a model for this language pair
            key = (src_lang, tgt_lang)
            if key not in self.MODEL_MAP:
                logger.warning(f"No direct translation model for {src_lang} to {tgt_lang}")
                return f"{text} [Translation unavailable]"
                
            # Load the model if needed
            if key not in self.models:
                self._load_model(key)
            
            # Get the model and tokenizer
            model = self.models[key]
            tokenizer = self.tokenizers[key]
            
            # Tokenize and translate
            inputs = tokenizer(text, return_tensors="pt").to(self.device)
            translated = model.generate(**inputs)
            translation = tokenizer.decode(translated[0], skip_special_tokens=True)
            
            # If translation is empty, return the original text
            if not translation or translation.strip() in [".", ",", "!", "?"]:
                logger.warning(f"Empty translation result for: '{text}'")
                return f"{text} [Translation unavailable]"
                
            return translation
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            # Return original text if translation fails
            return f"{text} [Translation failed: {str(e)}]"
    
    def batch_translate(self, texts: List[str], source_lang: str, target_lang: str) -> List[str]:
        """
        Translate a batch of texts
        
        Args:
            texts: List of texts to translate
            source_lang: Source language code
            target_lang: Target language code
            
        Returns:
            List of translated texts
        """
        return [self.translate(text, source_lang, target_lang) for text in texts]

# For testing
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 4:
        print("Usage: python marian_translator.py <text> <source_lang> <target_lang>")
        sys.exit(1)
    
    text = sys.argv[1]
    source_lang = sys.argv[2]
    target_lang = sys.argv[3]
    
    try:
        translator = NLLBTranslator("")  # Model path is not used
        translation = translator.translate(text, source_lang, target_lang)
        print(f"Translation: {translation}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 