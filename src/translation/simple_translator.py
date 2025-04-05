#!/usr/bin/env python3
"""
Simple Translation Module using Transformers

This module provides basic translation functionality using pre-trained models
from the Hugging Face hub, focusing on compatibility and simplicity.
"""

import logging
from typing import Dict, List
import traceback

# For fallback
import requests

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class SimpleTranslator:
    """Translation service using pre-trained models or API fallback"""
    
    def __init__(self, language_code_map: Dict[str, str] = None):
        """
        Initialize the translation service.
        
        Args:
            language_code_map: Map of language codes to ISO codes
        """
        self.language_code_map = language_code_map or {
            "en-US": "en",
            "ru-RU": "ru", 
            "es-CO": "es"
        }
        
        # Track if we're using transformers or fallback
        self.using_transformers = False
        self.using_fallback = False
        
        # Log initialization info
        logger.info("Initializing Simple Translator")
        
        # Try to initialize transformers
        try:
            import torch
            from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer
            
            # Initialize model and tokenizer for English to Spanish
            logger.info("Loading English to Spanish translation model...")
            model_name = "Helsinki-NLP/opus-mt-en-es"
            model_en_es = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            tokenizer_en_es = AutoTokenizer.from_pretrained(model_name)
            
            # Create pipeline for English to Spanish
            self.en_es_pipeline = pipeline(
                "translation", 
                model=model_en_es,
                tokenizer=tokenizer_en_es,
                device="cpu"
            )
            logger.info("English to Spanish model loaded successfully")
            
            # Initialize model and tokenizer for Spanish to English
            logger.info("Loading Spanish to English translation model...")
            model_name = "Helsinki-NLP/opus-mt-es-en"
            model_es_en = AutoModelForSeq2SeqLM.from_pretrained(model_name)
            tokenizer_es_en = AutoTokenizer.from_pretrained(model_name)
            
            # Create pipeline for Spanish to English
            self.es_en_pipeline = pipeline(
                "translation", 
                model=model_es_en,
                tokenizer=tokenizer_es_en,
                device="cpu"
            )
            logger.info("Spanish to English model loaded successfully")
            
            # Test the pipelines
            test_en = "Hello, this is a test."
            test_es = "Hola, esto es una prueba."
            
            logger.info(f"Testing EN->ES: '{test_en}'")
            result_es = self.en_es_pipeline(test_en)
            logger.info(f"Result: {result_es}")
            
            logger.info(f"Testing ES->EN: '{test_es}'")
            result_en = self.es_en_pipeline(test_es)
            logger.info(f"Result: {result_en}")
            
            # Track that we're using transformers
            self.using_transformers = True
            logger.info("Using transformers pipelines for translation")
            
        except Exception as e:
            logger.warning(f"Failed to initialize transformers pipelines: {e}")
            logger.warning(traceback.format_exc())
            logger.warning("Will use fallback translation method")
            self.using_fallback = True
    
    def _get_language_code(self, lang_code: str) -> str:
        """Get the ISO language code from a locale code"""
        return self.language_code_map.get(lang_code, lang_code.split('-')[0].lower())
    
    def translate_with_fallback(self, text: str, source_lang: str, target_lang: str) -> str:
        """Use mock translation as a basic fallback"""
        try:
            # First try LibreTranslate API
            url = "https://libretranslate.com/translate"
            
            # Convert language codes
            src = self._get_language_code(source_lang)
            tgt = self._get_language_code(target_lang)
            
            # Prepare request data
            data = {
                "q": text,
                "source": src,
                "target": tgt,
                "format": "text"
            }
            
            # Send request
            logger.info(f"Using API fallback for {src} to {tgt}")
            response = requests.post(url, json=data, timeout=10)
            
            # Parse response
            if response.status_code == 200:
                result = response.json()
                translation = result.get("translatedText", text)
                logger.info(f"API translation: {translation[:50]}...")
                return translation
            else:
                logger.warning(f"API fallback error: {response.status_code}")
                # Continue to mock fallback
                
        except Exception as e:
            logger.error(f"API fallback error: {e}")
            # Continue to mock fallback
        
        # If API fallback didn't work, use mock translation
        logger.info("Using mock translation as final fallback")
        lang_code = self._get_language_code(target_lang)
        return f"[{lang_code}] {text}"
    
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
            # If we're using transformers, try to translate with pipelines
            if self.using_transformers:
                # Check language pair
                if src_lang == "en" and tgt_lang == "es":
                    logger.info(f"Using transformers EN->ES for: {text[:50]}...")
                    result = self.en_es_pipeline(text, max_length=512)
                    if result and len(result) > 0 and 'translation_text' in result[0]:
                        translated = result[0]['translation_text']
                        logger.info(f"Transformers translation: {translated[:50]}...")
                        return translated
                    else:
                        logger.warning(f"EN->ES pipeline returned unexpected result: {result}")
                
                elif src_lang == "es" and tgt_lang == "en":
                    logger.info(f"Using transformers ES->EN for: {text[:50]}...")
                    result = self.es_en_pipeline(text, max_length=512)
                    if result and len(result) > 0 and 'translation_text' in result[0]:
                        translated = result[0]['translation_text']
                        logger.info(f"Transformers translation: {translated[:50]}...")
                        return translated
                    else:
                        logger.warning(f"ES->EN pipeline returned unexpected result: {result}")
                else:
                    logger.warning(f"No transformer pipeline for {src_lang} to {tgt_lang}")
            
            # If transformers failed or isn't available, use fallback
            return self.translate_with_fallback(text, source_lang, target_lang)
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            logger.error(traceback.format_exc())
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
        print("Usage: python simple_translator.py <text> <source_lang> <target_lang>")
        sys.exit(1)
    
    text = sys.argv[1]
    source_lang = sys.argv[2]
    target_lang = sys.argv[3]
    
    try:
        translator = SimpleTranslator()
        translation = translator.translate(text, source_lang, target_lang)
        print(f"Original: {text}")
        print(f"Translation: {translation}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1) 