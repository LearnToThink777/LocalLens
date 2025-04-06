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
# GeminiLLM 클래스 (Gemini API 호출)
# ---------------------------
class GeminiLLM(LLM):
    api_url: str = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    api_key: str

    def __init__(self, api_key: str):
      super().__init__(api_key=api_key)
      self.api_key = api_key
      # API 키 로드 확인 (실제 키 전체를 노출하지 않고 일부만 보여주거나 존재 여부만 체크)
      if self.api_key:
          logger.debug("[GeminiLLM.__init__] API key successfully loaded: %s", self.api_key[:4] + "****")
      else:
          logger.error("[GeminiLLM.__init__] API key가 로드되지 않음")

    def _call(self, prompt: str, **kwargs) -> str:
        # API 호출 직전에 API 키가 올바르게 로드되었는지 확인
        if self.api_key:
            logger.debug("[GeminiLLM._call] API key is present: %s", self.api_key[:4] + "****")
        else:
            logger.error("[GeminiLLM._call] API key is missing!")
            return json.dumps({"topic": "Error", "sentiment": "API key is missing"})
        
        logger.info("[GeminiLLM._call] API 호출 시작")
        logger.debug("[GeminiLLM._call] 입력된 prompt: %s", prompt)
        logger.debug("[GeminiLLM._call] 추가 파라미터: %s", kwargs)
        
        headers = {"Content-Type": "application/json"}
        data = {
          "contents": [{"parts": [{"text": prompt}]}],
          "generationConfig": {
              "temperature": 0.5,
              "maxOutputTokens": 100
          }
        }
        logger.debug("[GeminiLLM._call] 요청 URL: %s", self.api_url)
        logger.debug("[GeminiLLM._call] 요청 JSON Body:\n%s", json.dumps(data, indent=2, ensure_ascii=False))
        
        try:
            response = requests.post(
                f"{self.api_url}?key={self.api_key}",
                headers=headers,
                json=data,
                timeout=10
            )
            logger.debug("[GeminiLLM._call] 응답 상태 코드: %s", response.status_code)
            logger.debug("[GeminiLLM._call] 응답 헤더: %s", response.headers)
            logger.debug("[GeminiLLM._call] 응답 본문(raw text):\n%s", response.text)

            if response.status_code == 200:
                result = response.json()
                logger.debug("[GeminiLLM._call] 응답 JSON 파싱 성공:\n%s", json.dumps(result, indent=2, ensure_ascii=False))

                # 후보 중 첫 번째 candidate 추출
                if "candidates" in result and result["candidates"]:
                    candidate = result["candidates"][0]
                    logger.debug("[GeminiLLM._call] 추출된 candidate: %s", candidate)

                    # 여러 응답 포맷에 대한 분기 처리
                    if "output" in candidate:
                        output = candidate["output"]
                        logger.debug("[GeminiLLM._call] 'output' 필드에서 텍스트 추출: %s", output)
                    elif "content" in candidate and "parts" in candidate["content"] and candidate["content"]["parts"]:
                        output = candidate["content"]["parts"][0].get("text", "")
                        logger.debug("[GeminiLLM._call] 'content.parts[0].text'에서 텍스트 추출: %s", output)
                    else:
                        output = ""
                        logger.warning("[GeminiLLM._call] 응답 구조는 유효하지만 텍스트 추출 실패")

                    return output.strip()
                else:
                    err_msg = "응답 형식이 올바르지 않음 (candidates 없음)"
                    logger.error("[GeminiLLM._call] %s", err_msg)
                    return json.dumps({"topic": "Error", "sentiment": err_msg})
            else:
                err_msg = f"API 응답 실패 - HTTP {response.status_code}"
                logger.error("[GeminiLLM._call] %s", err_msg)
                return json.dumps({"topic": "Error", "sentiment": err_msg})

        except Exception as e:
            logger.exception("[GeminiLLM._call] 예외 발생: %s", e)
            return json.dumps({"topic": "Error", "sentiment": str(e)})

    def _llm_type(self) -> str:
        return "custom_gemini_llm"

    def invoke(self, prompt: str, **kwargs) -> str:
        logger.debug("[GeminiLLM.invoke] 호출됨")
        return self._call(prompt, **kwargs)

