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

import ConfigLoader
import CSVHandler
import GeminiLLM
import ReviewAnalyzer
import Translator

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
# 메인 실행 영역
# ---------------------------
if __name__ == "__main__":
    # 설정 로드
    config = ConfigLoader.load_config()

    # GeminiLLM 인스턴스 생성
    try:
        gemini_llm = GeminiLLM(api_key=config["gemini_api_key"])
        logger.debug("Gemini LLM 인스턴스 생성 성공")
    except Exception as e:
        logger.exception("Gemini LLM 인스턴스 생성 실패: %s", e)
        raise

    # Translator 인스턴스 생성
    translator = Translator(hf_api_token=config["huggingface_api_token"])

    # CSVHandler 인스턴스 생성
    csv_handler = CSVHandler()

    # ReviewAnalyzer 인스턴스 생성
    analyzer = ReviewAnalyzer(gemini_llm, translator, csv_handler)

    # 예시 리뷰 분석
    korean_review = "방문했을 때 위치와 서비스는 좋았지만, 청결 상태가 실망스러웠습니다."
    result = analyzer.analyze_and_save(korean_review)
    logger.info("최종 분석 결과: %s", result)


