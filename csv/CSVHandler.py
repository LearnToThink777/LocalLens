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
# CSVHandler 클래스 (CSV 저장 기능)
# ---------------------------
class CSVHandler:
    def __init__(self, filename="review_analysis.csv"):
        self.filename = filename

    def save(self, data: dict) -> None:
        try:
            headers = ["Review", "Topic", "Sentiment"]
            file_exists = os.path.exists(self.filename)
            write_header = not file_exists or os.path.getsize(self.filename) == 0
            with open(self.filename, mode="a", newline="", encoding="utf-8") as csvfile:
                writer = csv.writer(csvfile)
                if write_header:
                    writer.writerow(headers)
                writer.writerow([data["review"], data["topic"], data["sentiment"]])
            logger.debug("CSV 파일 저장 완료: %s", self.filename)
        except Exception as e:
            logger.exception("CSV 파일 저장 실패: %s", e)

