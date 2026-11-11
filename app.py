import streamlit as st
import os
from generator import extract_meta_info, generate_threads_posts

# -------------------------------------------------------------
# 0. Streamlit Config
# -------------------------------------------------------------
st.set_page_config(
    page_title="스레드 제휴마케팅 썰 글 생성기",
    page_icon="🧵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for clean mobile and desktop experience
st.markdown("""
<style>
    .main-title {
        font-size: 1.8rem;
        font-weight: 800;
        color: #111827;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: 0.95rem;
        color: #4B5563;
        margin-bottom: 1.2rem;
        line-height: 1.5;
    }
    .badge-tag {
        display: inline-block;
        background-color: #EEF2FF;
        color: #4F46E5;
        font-size: 0.8rem;
        font-weight: bold;
        padding: 3px 8px;
        border-radius: 4px;
        margin-bottom: 8px;
    }
    .stButton>button {
        width: 100%;
        background-color: #000000;
        color: #FFFFFF;
        font-weight: bold;
        padding: 0.75rem;
        border-radius: 8px;
        border: none;
        font-size: 1.05rem;
    }
    .stButton>button:hover {
        background-color: #374151;
        color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. Header
# -------------------------------------------------------------
st.markdown('<div class="badge-tag">THREADS AUTO PRO</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">🧵 스레드 제휴마케팅 썰 글 생성기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">쿠팡 파트너스·네이버 제휴 링크와 키워드만 넣으면, 스레드에서 떡상하는 1인칭 썰 글 3종과 공정위 문구를 3초 만에 뽑아드립니다.</div>', unsafe_allow_html=True)

st.divider()

# -------------------------------------------------------------
# 2. Input Section
# -------------------------------------------------------------
col_in1, col_in2 = st.columns([1, 1])

# Preset examples
st.markdown("##### ⚡ 빠른 테스트 예시 클릭")
c_ex1, c_ex2, c_ex3 = st.columns(3)

default_url = "https://link.coupang.com/a/sample999"
default_name = "샤오미 미니 무선청소기"
default_points = "흡입력 세고 틈새 먼지 머리카락 1초 컷, 가벼워서 손목 전혀 안 아픔"
default_plat = "coupang"

if c_ex1.button("청소기 예시"):
    st.session_state["p_name"] = "샤오미 미니 무선 핸디 청소기"
    st.session_state["p_link"] = "https://link.coupang.com/a/sample_cleaner"
    st.session_state["p_points"] = "책상 위 지우개 가루랑 키보드 머리카락 1초 만에 흡입, 차 청소할 때도 꿀템"
    st.session_state["p_plat"] = "쿠팡 파트너스"

if c_ex2.button("버티컬 마우스 예시"):
    st.session_state["p_name"] = "로지텍 인체공학 무선 버티컬 마우스"
    st.session_state["p_link"] = "https://link.coupang.com/a/sample_mouse"
    st.session_state["p_points"] = "손목터널증후군 찌릿하던 거 3일 만에 싹 사라짐, 그립감 편안함"
    st.session_state["p_plat"] = "쿠팡 파트너스"

if c_ex3.button("단백질 쉐이크 예시"):
    st.session_state["p_name"] = "비린내 없는 초코맛 프로틴 단백질 쉐이크"
    st.session_state["p_link"] = "https://link.coupang.com/a/sample_protein"
    st.session_state["p_points"] = "특유의 비린내 0%, 그냥 제티 초코우유 맛이라 매일 아침 거부감 없이 원샷"
    st.session_state["p_plat"] = "쿠팡 파트너스"

with col_in1:
    affiliate_url = st.text_input(
        "1. 제휴 링크 또는 상품 링크 (필수)",
        value=st.session_state.get("p_link", default_url),
        placeholder="https://link.coupang.com/... 또는 coupang.com/..."
    )
    
    platform_label = st.selectbox(
        "2. 제휴 플랫폼 선택",
        ["쿠팡 파트너스", "네이버 브랜드 커넥트/쇼핑", "기타 제휴마케팅"],
        index=0 if st.session_state.get("p_plat", "쿠팡 파트너스") == "쿠팡 파트너스" else 1
    )

with col_in2:
    prod_name = st.text_input(
        "3. 상품명 (필수)",
        value=st.session_state.get("p_name", default_name),
        placeholder="예: 샤오미 미니 무선청소기"
    )
    
    prod_points = st.text_area(
        "4. 실구매 후기 / 핵심 장점 (선택)",
        value=st.session_state.get("p_points", default_points),
        placeholder="예: 가볍고 흡입력 짱, 소음 적고 디자인 깔끔",
        height=68
    )

plat_code = "coupang" if platform_label == "쿠팡 파트너스" else ("naver" if "네이버" in platform_label else "etc")

generate_btn = st.button("🚀 스레드 썰 글 3종 생성하기", use_container_width=True)

# -------------------------------------------------------------
# 3. Output Section
# -------------------------------------------------------------
if generate_btn or "results" in st.session_state:
    if generate_btn:
        if not prod_name.strip():
            st.error("상품명을 입력해주세요!")
            st.stop()
        
        posts = generate_threads_posts(
            product_name=prod_name,
            key_points=prod_points,
            affiliate_link=affiliate_url,
            platform_type=plat_code
        )
        st.session_state["results"] = posts

    posts = st.session_state["results"]

    st.markdown("### 📝 생성된 스레드 썰 글 3선")
    st.info("💡 **스레드 꿀팁**: 본문에 링크를 직접 달면 메타 알고리즘이 도달률을 깎습니다. **[본문 글]을 먼저 올리고, 내 링크는 [첫 댓글]에 다는 방식**이 노출이 5배 이상 잘 나옵니다!")

    tab1, tab2, tab3 = st.tabs([
        "🔥 [A타입] 내돈내산 찐후기형",
        "💡 [B타입] 호구방지 비교분석형",
        "☕ [C타입] 일상공감 삶의질형"
    ])

    def render_tab_content(data):
        c1, c2 = st.columns([3, 2])
        with c1:
            st.markdown("#### 1️⃣ 스레드 본문용 (복사해서 스레드 등록)")
            st.text_area("스레드 본문", value=data["body"], height=240, label_visibility="collapsed")
        with c2:
            st.markdown("#### 2️⃣ 첫 댓글용 (등록 후 내 글에 바로 댓글 달기)")
            st.text_area("첫 댓글 (링크+공정위 문구)", value=data["comment"], height=240, label_visibility="collapsed")
        
        with st.expander("📌 본문에 링크까지 한 번에 넣고 싶다면? (본문 일체형 전체 복사)"):
            st.text_area("본문 일체형", value=data["full"], height=280)

    with tab1:
        render_tab_content(posts["type_a"])

    with tab2:
        render_tab_content(posts["type_b"])

    with tab3:
        render_tab_content(posts["type_c"])

# -------------------------------------------------------------
# 4. Footer & Tips
# -------------------------------------------------------------
st.divider()
st.markdown("""
<div style="background-color: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 8px; padding: 16px;">
    <h4 style="margin-top: 0; color: #1E293B;">🛡️ 스레드 제휴마케팅 3대 컴플라이언스 & 떡상 원칙</h4>
    <ul style="color: #475569; font-size: 0.9rem; line-height: 1.6; margin-bottom: 0;">
        <li><b>공정위 문구 필수</b>: 쿠팡 파트너스 링크 게시 시 공정위 문구를 누락하면 제휴 계정이 영구 정지될 수 있습니다. (생성기에 자동 포함됨)</li>
        <li><b>도달률 방어 (댓글 링크)</b>: 본문에 링크를 넣으면 봇으로 오인받기 쉽습니다. 본문은 흥미진진한 썰로 채우고 링크는 첫 댓글에 고정하세요.</li>
        <li><b>일상 7 : 홍보 3 황금 비율</b>: 제휴 링크 글만 100% 올리면 계정이 죽습니다. 하루 3개 올린다면 2개는 일상/공감 글, 1개는 핫딜 추천 글로 섞어주세요.</li>
    </ul>
</div>
""", unsafe_allow_html=True)
