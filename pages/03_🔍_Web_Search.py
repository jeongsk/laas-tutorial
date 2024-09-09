import os
import logging
import requests
import json
from typing import Dict, List, Optional
import streamlit as st
from datetime import datetime
from tavily import TavilyClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MAX_MESSAGES = 100
LAAS_API_URL = "https://api-laas.wanted.co.kr/api/preset/v2/chat/completions"
LAAS_API_KEY = st.secrets["LAAS_API_KEY"]
TAVILY_API_KEY = st.secrets["TAVILY_API_KEY"]
LAAS_PROJECT = "JEONGSK"
LAAS_HASH = "03e28d0f8fcb9184b37cc5132bff67c3c74b8387bc84002649917d2cf6b131bc"
tavily_client = TavilyClient(api_key=TAVILY_API_KEY)


def make_api_request(url: str, headers: Dict, json_data: Dict) -> Optional[Dict]:
    try:
        response = requests.post(url, headers=headers, json=json_data)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logger.error(f"API 요청 중 오류 발생: {str(e)}")
        st.error(f"API 요청 실패: {str(e)}")
        return None


def make_laas_api_request(messages: List[Dict]) -> Optional[Dict]:
    logger.info(f"API 요청 메시지: {messages}")
    json_response = make_api_request(
        LAAS_API_URL,
        {"project": LAAS_PROJECT, "apikey": LAAS_API_KEY},
        {
            "hash": LAAS_HASH,
            "params": {"date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
            "messages": messages,
        },
    )
    if json_response:
        logger.info(f"API 응답: {json_response}")
    return json_response


def add_message(
    messages: List[Dict[str, str]],
    role: str,
    content: str,
    tool_call_id: Optional[str] = None,
):
    messages.append({"role": role, "content": content,
                    "tool_call_id": tool_call_id})
    if len(messages) > MAX_MESSAGES:
        messages.pop(0)


def tavily_search(query: str) -> str:
    try:
        results = tavily_client.search(query=query, search_depth="basic")
        logger.info(f"Tavily API 응답: {results}")
        top_results = results.get("results", [])[:3]

        return "\n\n".join(
            [
                f"제목: {result['title']}\n링크: {
                    result['url']}\n내용: {result['content']}"
                for result in top_results
            ]
        )
    except Exception as e:
        logger.error(f"Tavily API 요청 중 오류 발생: {str(e)}")
        return f"검색 중 오류가 발생했습니다: {str(e)}"


def handle_tool_calls(tool_calls, info_placeholder):
    results = []
    for call in tool_calls:
        if call["function"]["name"] == "search":
            arguments = json.loads(call["function"]["arguments"])
            query = arguments.get("query", "")
            info_placeholder.info(f"🔍 '{query}' 검색 중...")
            search_result = tavily_search(query)
            results.append((call["id"], search_result))
    return results


def process_user_input(user_input: str, messages: List[Dict]):
    add_message(messages, "user", user_input)
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        container = st.empty()
        info_placeholder = st.empty()
        with st.spinner("AI가 응답을 생성 중..."):
            response = make_laas_api_request(messages)
            if response:
                message = response["choices"][0]["message"]
                if message.get("tool_calls"):
                    tool_messages = [
                        {"role": "user", "content": user_input},
                        message
                    ]
                    tool_results = handle_tool_calls(
                        message["tool_calls"], info_placeholder
                    )
                    for tool_call_id, tool_result in tool_results:
                        tool_messages.append({
                            "role": "tool",
                            "content": tool_result,
                            "tool_call_id": tool_call_id
                        })
                    response = make_laas_api_request(tool_messages)
                    content = response["choices"][0]["message"].get("content")
                    container.markdown(content)
                    add_message(messages, "assistant", content)
                elif message.get("content"):
                    container.markdown(message["content"])
                    add_message(messages, "assistant", message["content"])
                else:
                    st.error("유효한 응답을 받지 못했습니다.")
            else:
                st.error("챗봇 응답을 받지 못했습니다.")
        info_placeholder.empty()


def get_page_name():
    try:
        return os.path.basename(st.get_script_run_ctx().script_path)
    except:
        return "main"


def main():
    st.set_page_config(page_title="🤖 AI 지식 도우미", page_icon="🤖")
    st.title("🤖 AI 지식 도우미")
    st.write(
        "궁금한 점을 물어보세요. 필요하다면 최신 정보를 검색해 답변해 드리겠습니다!"
    )

    # 현재 페이지 이름을 기반으로 고유한 세션 상태 키 생성
    page_name = get_page_name()
    messages_key = f"messages_{page_name}"

    if messages_key not in st.session_state:
        st.session_state[messages_key] = []

    messages = st.session_state[messages_key]

    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    user_input = st.chat_input("질문을 입력하세요:")

    if user_input:
        process_user_input(user_input, messages)


if __name__ == "__main__":
    main()
