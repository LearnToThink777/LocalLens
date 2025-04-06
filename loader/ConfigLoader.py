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


class ConfigLoader:
    @staticmethod
    def load_config(config_file="config.json") -> dict:
        logger.debug("[load_config] 설정 파일 경로: %s", config_file)
        try:
            # 파일 존재 여부 확인
            if not os.path.exists(config_file):
                logger.error("[load_config] 설정 파일이 존재하지 않음: %s", config_file)
                raise FileNotFoundError(f"설정 파일 '{config_file}'을 찾을 수 없습니다.")

            # 파일 열기 시도
            logger.debug("[load_config] 설정 파일 열기 시도...")
            with open(config_file, "r", encoding="utf-8") as file:
                config_raw = file.read()
                logger.debug("[load_config] 설정 파일 원본 내용: %s", config_raw)
                config = json.loads(config_raw)

            # 필수 키 존재 여부 확인
            required_keys = ["gemini_api_key", "huggingface_api_token"]
            logger.debug("[load_config] 필수 키 확인: %s", required_keys)
            for key in required_keys:
                if key not in config:
                    logger.error("[load_config] 누락된 키: %s", key)
                    raise KeyError(f"config.json에 '{key}'가 없습니다.")

            # 로드 완료
            logger.info("[load_config] 설정 로드 성공")
            logger.debug("[load_config] 로드된 설정 데이터: %s", config)
            return config

        except Exception as e:
            logger.exception("[load_config] 설정 로드 중 예외 발생: %s", e)

            raise

