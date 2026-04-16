import streamlit as st

st.set_page_config(page_title="FAQ 만족도", layout="centered")

col1, col2 = st.columns(2)

with col1:
    if st.button("😊 만족스러워요", use_container_width=True):
        st.toast("✅ 만족스러웠군요, 좋습니다!", icon="✅")

with col2:
    if st.button("😢 만족스럽지 않아요", use_container_width=True):
        st.markdown("[💬 채널톡으로 바로 문의하기](여기에_채널톡_링크)")
