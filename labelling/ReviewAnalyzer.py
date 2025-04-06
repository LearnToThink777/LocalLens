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
# ReviewAnalyzer 클래스 (리뷰 분석 파이프라인)
# ---------------------------
class ReviewAnalyzer:
    def __init__(self, gemini_llm: GeminiLLM, translator: Translator, csv_handler: CSVHandler):
        self.gemini_llm = gemini_llm
        self.translator = translator
        self.csv_handler = csv_handler

        # Few-shot 예시와 템플릿 초기화
        self.topics_list = ["Location", "Service", "Price", "Cleanliness", "Facilities"]
        topics_str = ", ".join(self.topics_list)
        self.few_shot_examples = (
            "예시 1: 리뷰: \"위치는 정말 좋았어요. 서비스도 훌륭했습니다.\" -> [\n"
            "    {\"topic\": \"Location\", \"sentiment\": \"Positive\"},\n"
            "    {\"topic\": \"Service\", \"sentiment\": \"Positive\"},\n"
            "    {\"topic\": \"Price\", \"sentiment\": \"Neutral\"},\n"
            "    {\"topic\": \"Cleanliness\", \"sentiment\": \"Neutral\"},\n"
            "    {\"topic\": \"Facilities\", \"sentiment\": \"Neutral\"}\n"
            "]\n"
            "예시 2: 리뷰: \"청결 상태가 너무 안 좋고 불쾌했어요.\" -> [\n"
            "    {\"topic\": \"Location\", \"sentiment\": \"Neutral\"},\n"
            "    {\"topic\": \"Service\", \"sentiment\": \"Neutral\"},\n"
            "    {\"topic\": \"Price\", \"sentiment\": \"Neutral\"},\n"
            "    {\"topic\": \"Cleanliness\", \"sentiment\": \"Negative\"},\n"
            "    {\"topic\": \"Facilities\", \"sentiment\": \"Neutral\"}\n"
            "]\n"
            "예시 3: 리뷰: \"음식은 괜찮았지만 가격이 너무 비쌌어요.\" -> [\n"
            "    {\"topic\": \"Location\", \"sentiment\": \"Neutral\"},\n"
            "    {\"topic\": \"Service\", \"sentiment\": \"Neutral\"},\n"
            "    {\"topic\": \"Price\", \"sentiment\": \"Negative\"},\n"
            "    {\"topic\": \"Cleanliness\", \"sentiment\": \"Neutral\"},\n"
            "    {\"topic\": \"Facilities\", \"sentiment\": \"Neutral\"}\n"
            "]\n"
            "※ 리뷰 내에서 명확하게 긍정 또는 부정의 표현이 없는 주제는 'Neutral'로 분류한다.\n"
        )
        self.template = PromptTemplate(
            input_variables=["review", "topics", "few_shot"],
            template=(
                "{few_shot}\n"
                "다음 리뷰에 대해 {topics}에 명시된 모든 주제에 대해 감정(sentiment)을 추출하라. "
                "리뷰 내에서 각 주제가 명확하게 긍정(Positive)이나 부정(Negative)으로 표현되면 해당 감정을, "
                "그렇지 않으면 'Neutral'로 분류한다. "
                "출력은 JSON 배열 형식으로 작성하며, 각 객체는 'topic'과 'sentiment' 필드를 포함해야 한다. "
                "리뷰: \"{review}\""
            )
        )
        self.topics_str = topics_str

        # LLMChain 구성
        self.chain = LLMChain(llm=self.gemini_llm, prompt=self.template)


    @staticmethod
    def extract_json(response: str) -> str:
        logger.debug("[extract_json] 호출됨")
        logger.debug("[extract_json] 입력된 응답 문자열:\n%s", response)

        # 코드 블록 구분자와 "json" 키워드를 제거
        cleaned = re.sub(r"```\s*json\s*", "", response, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```", "", cleaned)
        cleaned = cleaned.strip()

        logger.debug("[extract_json] 정리된 응답 문자열:\n%s", cleaned)
        return cleaned



    def build_prompt(self, english_review: str) -> str:
        prompt = self.template.format(
            review=english_review,
            topics=self.topics_str,
            few_shot=self.few_shot_examples
        )
        logger.debug("생성된 프롬프트 (PromptTemplate 사용): %s", prompt)
        return prompt

    def analyze_review(self, korean_review: str) -> dict:
          logger.info("리뷰 분석 시작: %s", korean_review)

          # 1. 한국어 리뷰 -> 영어 번역
          english_review = self.translator.translate_to_english(korean_review)
          logger.debug("번역된 영어 리뷰: %s", english_review)

          # 2. 프롬프트 생성
          prompt = self.build_prompt(english_review)
          logger.debug("최종 프롬프트: %s", prompt)

          # 3. Gemini API 호출
          gemini_response = self.gemini_llm.invoke(prompt)
          logger.debug("Gemini API 원본 응답: %s", gemini_response)
          logger.debug("Gemini API 응답 문자열 길이: %d", len(gemini_response))

          # 4. JSON 추출
          cleaned_response = self.extract_json(gemini_response)
          logger.debug("전처리 후 추출된 응답: %s", cleaned_response)

          # 5. JSON 파싱
          try:
              result_data = json.loads(cleaned_response)
              logger.debug("파싱된 JSON 데이터: %s", result_data)
          except Exception as e:
              logger.exception("JSON 파싱 실패: %s", e)
              result_data = {"topic": "Unknown", "sentiment": "Unknown"}

          # 6. 결과가 리스트인 경우 모든 요소에 대해 한국어 번역 적용
          if isinstance(result_data, list):
              translated_results = []
              for item in result_data:
                  if isinstance(item, dict):
                      if item.get("topic") not in ["Unknown", "Error"]:
                          item["topic"] = self.translator.translate_to_korean(item["topic"])
                          item["sentiment"] = self.translator.translate_to_korean(item["sentiment"])
                      translated_results.append(item)
              result_data = translated_results
          # 딕셔너리 형태인 경우 바로 번역 적용
          elif isinstance(result_data, dict):
              if result_data.get("topic") not in ["Unknown", "Error"]:
                  result_data["topic"] = self.translator.translate_to_korean(result_data["topic"])
                  result_data["sentiment"] = self.translator.translate_to_korean(result_data["sentiment"])
          else:
              result_data = {"topic": "Unknown", "sentiment": "Unknown"}

          logger.debug("번역 후 JSON 데이터 (한국어 라벨): %s", result_data)
          return result_data
    def analyze_and_save(self, korean_review: str) -> dict:
        result = self.analyze_review(korean_review)
        # 결과가 리스트인 경우 JSON 문자열로 변환하여 저장
        if isinstance(result, list):
            topic = json.dumps(result, ensure_ascii=False)
            sentiment = ""
        else:
            topic = result.get("topic", "Unknown")
            sentiment = result.get("sentiment", "Unknown")
        csv_data = {
            "review": korean_review,
            "topic": topic,
            "sentiment": sentiment
        }
        self.csv_handler.save(csv_data)
        return result
