import re
import logging
import requests
from typing import Optional
import streamlit as st
from youtube_transcript_api import YouTubeTranscriptApi

# LaaS API 키 설정
LAAS_API_KEY = st.secrets["LAAS_API_KEY"]
LAAS_API_URL = "https://api-laas.wanted.co.kr/api/preset/v2/chat/completions"
LAAS_PROJECT = "JEONGSK"
LAAS_HASH = "7840a8aedaca519d09fb85ecca6b5d270584c56f24437889e30d4b169e1ced19"

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 페이지 설정
st.set_page_config(page_title="Youtube Summary", page_icon="", layout="centered")
st.markdown("# 📺 Youtube Summary")


def extract_video_id(url):
    """YouTube URL에서 video ID를 추출합니다."""
    video_id = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", url)
    return video_id.group(1) if video_id else None


def get_youtube_transcript(video_id):
    """YouTube 비디오의 자막을 가져옵니다."""
    try:
        transcript = YouTubeTranscriptApi.get_transcript(
            video_id, languages=("ko", "en")
        )
        return " ".join([entry["text"] for entry in transcript])
    except Exception as e:
        logger.error(f"자막을 가져오는 데 실패했습니다: {str(e)}")
        st.error(f"자막을 가져오는 데 실패했습니다: {str(e)}")
        return None


def make_laas_api_request(text: str) -> Optional[str]:
    """LaaS API에 요청을 보내고 응답을 받습니다."""
    try:
        response = requests.post(
            LAAS_API_URL,
            headers={"project": LAAS_PROJECT, "apikey": LAAS_API_KEY},
            json={"hash": LAAS_HASH, "params": {"youtube_transcript": text}},
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.RequestException as e:
        logger.error(f"API 요청 중 오류 발생: {str(e)}")
        st.error(f"요약하는 데 실패했습니다: {str(e)}")
        return None


def summarize_youtube_video(url: str) -> None:
    """YouTube 비디오 URL을 받아 요약을 생성합니다."""
    video_id = extract_video_id(url)
    if not video_id:
        st.error("올바른 YouTube URL을 입력해주세요.")
        return

    with st.spinner("자막을 다운로드하고 요약하는 중..."):
        transcript = get_youtube_transcript(video_id)
        if transcript:
            summary = make_laas_api_request(transcript)
            if summary:
                st.subheader("요약:")
                st.write(summary)


# 메인 로직
def main():
    youtube_url = st.text_input(
        "YouTube URL을 입력하세요:",
        placeholder="https://www.youtube.com/watch?v=hEKcdsrdV8M",
        help="YouTube 영상의 전체 URL을 입력해주세요.",
    )

    if st.button("요약하기"):
        if youtube_url:
            summarize_youtube_video(youtube_url)
        else:
            st.warning("YouTube URL을 입력해주세요.")


if __name__ == "__main__":
    main()
