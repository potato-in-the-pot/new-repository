import streamlit as st
import pandas as pd
import numpy as np
import requests
import io
from sentence_transformers import SentenceTransformer

# ── 설정 ──────────────────────────────────────────────────────────────
SHEET_ID = "1uay8nvcFYFIJ6VPS1ZcQyrtqOB9AeK6gyumNbMy1r7c"
FAQ_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv"
CHANNELTALK_URL = "https://codeit.channel.io/home"
FEEDBACK_URL = "https://script.google.com/macros/s/AKfycbxMqX287NH-8cim1l2OTB5cPNcUqU0LM_2-MWf0wWf6vewPsW_wmY-bx_p_J86v42V2/exec"
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
SIMILARITY_THRESHOLD = 0.35  # 이 점수 이하면 "관련 FAQ 없음" 처리


# ── 데이터 / 모델 로드 ─────────────────────────────────────────────────
@st.cache_data(ttl=300)  # 5분마다 최신 데이터 반영
def load_faq():
    response = requests.get(FAQ_URL)
    response.encoding = "utf-8"
    df = pd.read_csv(io.StringIO(response.text))
    df.columns = [c.strip().lower() for c in df.columns]
    df = df.fillna("")
    return df


@st.cache_resource
def load_model():
    return SentenceTransformer(MODEL_NAME)


@st.cache_data
def compute_faq_embeddings(texts: tuple):
    model = load_model()
    return model.encode(list(texts))  # numpy array


def log_feedback(query: str, faq_title: str, category: str, result: str):
    try:
        requests.post(FEEDBACK_URL, json={
            "query": query,
            "faq_title": faq_title,
            "category": category,
            "result": result,
        }, timeout=3)
    except Exception:
        pass  # 로깅 실패해도 앱은 정상 동작


def keyword_score(query: str, row) -> float:
    q = query.strip()
    keywords = [k.strip() for k in str(row.get("keywords", "")).split(",") if k.strip()]
    score = 0.0
    for kw in keywords:
        if kw == q:             # 키워드와 완전 일치
            score += 0.5
        elif q in kw:           # 키워드 안에 쿼리 포함 ("환급" in "자비부담금 환급")
            score += 0.3
        elif kw in q:           # 쿼리 안에 키워드 포함
            score += 0.2
    return min(score, 0.6)


def search(query: str, df: pd.DataFrame, top_n: int = 3):
    texts = tuple(
        f"{row['question']} {row['keywords']}" for _, row in df.iterrows()
    )
    faq_emb = compute_faq_embeddings(texts)

    model = load_model()
    query_emb = model.encode(query)

    semantic_scores = np.dot(faq_emb, query_emb) / (
        np.linalg.norm(faq_emb, axis=1) * np.linalg.norm(query_emb) + 1e-9
    )

    final_scores = [
        float(semantic_scores[i]) + keyword_score(query, df.iloc[i])
        for i in range(len(df))
    ]

    top_idx = np.array(final_scores).argsort()[::-1][:top_n]
    results = [(df.iloc[i], final_scores[i]) for i in top_idx]
    return [(row, score) for row, score in results if score >= SIMILARITY_THRESHOLD]


# ── 앱 시작 ────────────────────────────────────────────────────────────
st.set_page_config(page_title="코드잇 국비지원과정 FAQ", page_icon="💬", layout="centered")

st.markdown("""
<style>
    /* 전체 배경 */
    .stApp { background-color: #FFFFFF; }

    /* 버튼 — 아웃라인 스타일 */
    .stButton > button {
        background-color: white !important;
        color: #333236 !important;
        border: 1.5px solid #D0D0D0 !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        padding: 8px 16px !important;
    }
    .stButton > button:hover {
        border-color: #6500C3 !important;
        color: #6500C3 !important;
    }

    /* 채널톡 링크 버튼 */
    .stLinkButton > a {
        background-color: white !important;
        color: #333236 !important;
        border: 1.5px solid #D0D0D0 !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
    }
    .stLinkButton > a:hover {
        border-color: #6500C3 !important;
        color: #6500C3 !important;
    }

    /* expander 박스 */
    .stExpander {
        border: 1.5px solid #E8E8E8 !important;
        border-radius: 8px !important;
        margin-bottom: 8px !important;
    }

    /* 추천 답변 박스 */
    .stAlert { border-left: 4px solid #6500C3 !important; }

    /* 입력창 */
    .stTextInput > div > div > input {
        border-radius: 8px !important;
        border: 1.5px solid #E8E8E8 !important;
    }
</style>
""", unsafe_allow_html=True)

# 로고 + 타이틀
st.title("💬 코드잇 국비지원과정 자주 묻는 질문")
st.markdown("---")

for key, default in [("step", "search"), ("last_query", ""), ("last_faq", ""), ("last_category", "")]:
    if key not in st.session_state:
        st.session_state[key] = default

try:
    df = load_faq()
except Exception as e:
    st.error(f"FAQ 데이터를 불러오지 못했어요. Google Sheets 공유 설정을 확인해주세요.\n\n{e}")
    st.stop()


# ── 1단계: 검색 ────────────────────────────────────────────────────────
if st.session_state.step == "search":
    query = st.text_input(
        "궁금한 점을 입력해주세요",
        placeholder="예: 내일배움카드 없이 수강할 수 있나요?",
    )

    if query:
        with st.spinner("찾는 중..."):
            results = search(query, df)

        if not results:
            st.warning("관련 FAQ를 찾지 못했어요.")
            st.link_button("채널톡으로 문의하기 →", CHANNELTALK_URL)
        else:
            top_row, _ = results[0]
            st.session_state.last_query = query
            st.session_state.last_faq = top_row["question"]
            st.session_state.last_category = top_row["category"]

            st.markdown("---")
            st.markdown("**추천 답변**")
            st.info(f"**Q. {top_row['question']}**\n\n{top_row['answer']}")

            if top_row.get("link"):
                st.markdown(f"🔗 [관련 링크]({top_row['link']})")

            if len(results) > 1:
                with st.expander("다른 관련 질문 보기"):
                    for row, _ in results[1:]:
                        st.markdown(f"**Q. {row['question']}**")
                        st.markdown(row["answer"])
                        if row.get("link"):
                            st.markdown(f"🔗 [관련 링크]({row['link']})")
                        st.markdown("---")

            st.markdown("---")
            st.markdown("**도움이 되셨나요?**")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("👍 네, 해결됐어요", use_container_width=True):
                    log_feedback(query, top_row["question"], top_row["category"], "해결")
                    st.session_state.step = "resolved"
                    st.rerun()
            with col2:
                if st.button("👎 아니오, 다른 내용 찾아볼게요", use_container_width=True):
                    log_feedback(query, top_row["question"], top_row["category"], "미해결")
                    st.session_state.step = "browse"
                    st.rerun()


# ── 2단계: 해결 ────────────────────────────────────────────────────────
elif st.session_state.step == "resolved":
    st.success("도움이 되었다니 다행이에요! 😊")
    if st.button("← 처음으로"):
        st.session_state.step = "search"
        st.rerun()


# ── 3단계: 카테고리 탐색 → 채널톡 ────────────────────────────────────
elif st.session_state.step == "browse":
    st.markdown("### 카테고리로 찾아보기")

    categories = sorted([c for c in df["category"].unique() if c])
    selected = st.selectbox("카테고리를 선택하세요", ["선택하세요"] + categories)

    if selected != "선택하세요":
        for _, row in df[df["category"] == selected].iterrows():
            with st.expander(row["question"]):
                st.write(row["answer"])
                if row.get("link"):
                    st.markdown(f"🔗 [관련 링크]({row['link']})")

    st.markdown("---")
    st.markdown("그래도 원하는 답변이 없다면 직접 문의해주세요.")
    st.link_button("채널톡으로 문의하기 →", CHANNELTALK_URL)

    if st.button("← 처음으로"):
        st.session_state.step = "search"
        st.rerun()
