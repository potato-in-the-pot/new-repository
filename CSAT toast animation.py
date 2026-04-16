Python 3.14.4 (v3.14.4:23116f998f6, Apr  7 2026, 09:45:22) [Clang 17.0.0 (clang-1700.6.4.2)] on darwin
Enter "help" below or click "Help" above for more information.
>>> import streamlit as st
... import time
... 
... st.set_page_config(page_title="FAQ 만족도", layout="centered")
... 
... # 버튼 두 개 나란히 배치
... col1, col2 = st.columns(2)
... 
... with col1:
...     if st.button("😊 만족스러워요", use_container_width=True):
...         st.toast("✅ 만족스러웠군요, 좋습니다!", icon="✅")
... 
... with col2:
...     if st.button("😢 만족스럽지 않아요", use_container_width=True):
...         # 텍스트 입력창 표시
...         feedback = st.text_area(
...             "어떤 내용이 부실하게 느껴지셨나요?",
...             placeholder="내용을 입력해주세요."
...         )
...         if st.button("제출하기"):
...             if feedback:
...                 st.toast("피드백이 접수됐어요. 빠르게 확인하겠습니다!", icon="📩")
...                 time.sleep(2)
...                 # 채널톡 링크로 이동
