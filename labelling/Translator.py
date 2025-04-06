import re
import json
import csv
import requests
import logging
import os
from langchain import PromptTemplate, LLMChain
from langchain.llms.base import LLM
from transformers import MarianMTModel, MarianTokenizer
from transformers import M2M100ForConditionalGeneration, M2M100Tokenizer
from huggingface_hub import login

# ---------------------------
# 로깅 설정
# ---------------------------
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
    force=True
)
logger = logging.getLogger(__name__)


# ---------------------------
# Translator 클래스 (번역 기능 통합)
# ---------------------------
class Translator:
    def __init__(self, hf_api_token: str):
        try:
            # Hugging Face 로그인
            login(token=hf_api_token)
            logger.debug("Hugging Face 로그인 성공")
        except Exception as e:
            logger.exception("Hugging Face 로그인 실패: %s", e)
            raise

        # 한국어 -> 영어 모델 로드
        self.ko_en_model_name = 'Helsinki-NLP/opus-mt-ko-en'
        try:
            self.ko_en_model = MarianMTModel.from_pretrained(
                self.ko_en_model_name,
                use_auth_token=hf_api_token
            )
            self.ko_en_tokenizer = MarianTokenizer.from_pretrained(
                self.ko_en_model_name,
                use_auth_token=hf_api_token
            )
            logger.debug("MarianMT (ko->en) 모델 로드 성공")
        except Exception as e:
            logger.exception("MarianMT (ko->en) 모델 로드 실패: %s", e)
            raise

        # 영어 -> 한국어 모델 로드
        self.en_ko_model_name = "facebook/m2m100_418M"
        try:
            self.en_ko_model = M2M100ForConditionalGeneration.from_pretrained(
                self.en_ko_model_name,
                use_auth_token=hf_api_token
            )
            self.en_ko_tokenizer = M2M100Tokenizer.from_pretrained(
                self.en_ko_model_name,
                use_auth_token=hf_api_token
            )
            self.en_ko_tokenizer.src_lang = "en"
            logger.debug("M2M100 (en->ko) 모델 로드 성공")
        except Exception as e:
            logger.exception("M2M100 (en->ko) 모델 로드 실패: %s", e)
            raise

    def translate_to_english(self, text: str) -> str:
        try:
            logger.debug("한국어 -> 영어 번역 시작, text: %s", text)
            tokens = self.ko_en_tokenizer(text, return_tensors="pt", padding=True)
            translated = self.ko_en_model.generate(**tokens)
            translated_text = self.ko_en_tokenizer.decode(translated[0], skip_special_tokens=True)
            logger.debug("번역 결과 (영어): %s", translated_text)
            return translated_text
        except Exception as e:
            logger.exception("한국어 -> 영어 번역 실패: %s", e)
            return text

    def translate_to_korean(self, text: str) -> str:
        try:
            logger.debug("영어 -> 한국어 번역 시작, text: %s", text)
            tokens = self.en_ko_tokenizer(text, return_tensors="pt", padding=True)
            generated_tokens = self.en_ko_model.generate(**tokens, forced_bos_token_id=self.en_ko_tokenizer.get_lang_id("ko"))
            translated_text = self.en_ko_tokenizer.decode(generated_tokens[0], skip_special_tokens=True)
            logger.debug("번역 결과 (한국어): %s", translated_text)
            return translated_text
        except Exception as e:
            logger.exception("영어 -> 한국어 번역 실패: %s", e)
            return text

