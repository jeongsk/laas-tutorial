import logging
import os
from typing import Dict, List, Optional, Any

import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LaasChatAPI:
    def __init__(
        self,
        project: Optional[str] = os.getenv("LAAS_PROJECT"),
        api_key: Optional[str] = os.getenv("LAAS_API_KEY"),
        hash: Optional[str] = None,
        model: Optional[str] = None,
        service_type: Optional[str] = None,
        temperature: Optional[float] = None,
        api_url: Optional[str] = None,
        params: Optional[Dict] = None,
    ):
        self.project = project
        self.api_key = api_key
        self.hash = hash
        self.model = model
        self.service_type = service_type
        self.temperature = temperature
        self.params = params or {}

        self.api_url = self._get_api_url(api_url)

        if not all([self.project, self.api_key, self.hash]):
            raise ValueError("Project, API key, and hash are required.")

    def _get_api_url(self, url: Optional[str]) -> str:
        if url:
            return url
        return os.getenv(
            "LAAS_API_URL",
            "https://api-laas.wanted.co.kr/api/preset/v2/chat/completions",
        )

    def _send_api_request(
        self, url: str, headers: Dict, json_data: Dict
    ) -> Dict[str, Any]:
        try:
            response = requests.post(url, headers=headers, json=json_data)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"API request error: {str(e)}")
            raise

    def send_chat_request(self, messages: List[Dict]) -> Dict[str, Any]:
        logger.info(f"Chat request messages: {messages}")

        json_data = {
            "hash": self.hash,
            "messages": messages,
        }

        if self.model:
            json_data["model"] = self.model
        if self.service_type:
            json_data["service_type"] = self.service_type
        if self.temperature is not None:
            json_data["temperature"] = self.temperature
        if self.params:
            json_data["params"] = self.params

        print(
            {"project": self.project, "apikey": self.api_key},
            json_data,
        )
        json_response = self._send_api_request(
            self.api_url,
            {"project": self.project, "apikey": self.api_key},
            json_data,
        )
        if json_response:
            logger.info(f"API response: {json_response}")
        return json_response

    def send_message_request(self, query: str, **kwargs) -> str:
        try:
            logger.info(f"Sending message request: {query}")
            response = self.send_chat_request(
                [{"role": "user", "content": query}], **kwargs
            )
            logger.info("Message request sent successfully")
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error in send_message_request: {str(e)}")
            raise
