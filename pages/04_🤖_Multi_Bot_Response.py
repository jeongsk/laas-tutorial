import os
import asyncio
import aiohttp
import streamlit as st
from helpers.laas_chat_api import LaasChatAPI

# 환경 변수 설정
os.environ["LAAS_PROJECT"] = "JEONGSK"
os.environ["LAAS_API_KEY"] = st.secrets["LAAS_API_KEY"]
LAAS_HASH = "87be5acd71e58fdbb7a76df49726403d18d175b7b45ce5d2dd37faadb1c02694"


# 모델 인스턴스 생성
openai_gpt4o_api = LaasChatAPI(
    hash=LAAS_HASH,
    service_type="OPENAI",
    model="gpt-4o",
)
anthropic_claude_api = LaasChatAPI(
    hash=LAAS_HASH,
    service_type="AWS",
    model="claude-3.5-sonnet",
)
google_gemini_api = LaasChatAPI(
    hash=LAAS_HASH,
    service_type="GOOGLE",
    model="gemini-1.5-pro",
)

# 페이지 설정
st.set_page_config(
    page_title="🤖 3개의 AI 모델 응답 비교", page_icon="🤖", layout="wide"
)
st.title("3개의 AI 모델 응답 비교")


async def get_responses(user_input):
    tasks = [
        openai_gpt4o_api.send_message_request_async(user_input),
        anthropic_claude_api.send_message_request_async(user_input),
        google_gemini_api.send_message_request_async(user_input),
    ]
    return await asyncio.gather(*tasks)


def on_input_change():
    st.session_state.input_submitted = True


user_input = st.text_input(
    "질문:",
    key="user_input",
    on_change=on_input_change,
    placeholder="질문을 입력하세요...",
)

if "input_submitted" not in st.session_state:
    st.session_state.input_submitted = False

if st.session_state.input_submitted:

    if user_input:
        col1, col2, col3 = st.columns(3)
        with st.spinner("응답 작성 중..."):

            # 비동기 요청 실행
            responses = asyncio.run(get_responses(user_input))

            with col1:
                st.markdown("##### 🤖 GPT-4o")
                st.markdown(responses[0])

            with col2:
                st.markdown("##### 🤖 Claude-3.5-Sonnet")
                st.markdown(responses[1])

            with col3:
                st.markdown("##### 🤖 Gemini-1.5-Pro")
                st.markdown(responses[2])
    else:
        st.warning("질문을 입력해주세요.")
