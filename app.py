import streamlit as st
import os
import sys

# generator 모듈 임포트 경로 방어
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from generator import safe_extract_meta, generate_threads_posts, generate_reply_templates, clean_url

# -------------------------------------------------------------
# 0. Streamlit Config
# -------------------------------------------------------------
st.set_page_config(
    page_title="스레드 제휴마케팅 썰 글 & 댓글 생성기 Pro",
    page_icon="🧵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 모바일 및 데스크톱 고대비 반응형 스타일
st.markdown("""
<style>
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 3rem;
        max-width: 960px;
    }
    .badge-tag {
        display: inline-block;
        background-color: #111827;
        color: #F9FAFB;
        font-size: 0.8rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 6px;
        margin-bottom: 8px;
        letter-spacing: 0.5px;
    }
    .main-title {
        font-size: 1.8rem;
        font-weight: 800;
        color: #0F172A;
        margin-bottom: 0.3rem;
        line-height: 1.3;
    }
    .sub-title {
        font-size: 0.95rem;
        color: #475569;
        margin-bottom: 1.2rem;
        line-height: 1.5;
    }
    .stButton>button {
        width: 100%;
        min-height: 48px;
        font-size: 1.05rem;
        font-weight: 700;
        border-radius: 8px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 8px 16px;
        font-weight: 600;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# 1. Session State 초기화 (Single Source of Truth)
# -------------------------------------------------------------
if "url_input" not in st.session_state:
    st.session_state["url_input"] = "https://link.coupang.com/a/sample_cleaner"
if "name_input" not in st.session_state:
    st.session_state["name_input"] = "샤오미 미니 무선 핸디 청소기"
if "points_input" not in st.session_state:
    st.session_state["points_input"] = "책상 위 지우개 가루랑 키보드 머리카락 1초 만에 흡입, 500g 초경량이라 손목 전혀 안 아픔"
if "plat_input" not in st.session_state:
    st.session_state["plat_input"] = "쿠팡 파트너스"
if "posts_data" not in st.session_state:
    st.session_state["posts_data"] = None
if "replies_data" not in st.session_state:
    st.session_state["replies_data"] = None
if "meta_notice" not in st.session_state:
    st.session_state["meta_notice"] = None

# -------------------------------------------------------------
# 2. Callbacks (위젯 인스턴스화 전에 실행되어 에러 원천 방지)
# -------------------------------------------------------------
def cb_load_preset(url, name, points, plat, notice):
    st.session_state["url_input"] = url
    st.session_state["name_input"] = name
    st.session_state["points_input"] = points
    st.session_state["plat_input"] = plat
    st.session_state["meta_notice"] = notice

def cb_parse_link():
    url = st.session_state.get("url_input", "").strip()
    if url:
        meta = safe_extract_meta(url)
        st.session_state["url_input"] = meta["url"]
        if meta["platform"] == "coupang":
            st.session_state["plat_input"] = "쿠팡 파트너스"
        elif meta["platform"] == "naver":
            st.session_state["plat_input"] = "네이버 브랜드 커넥트/쇼핑"
        
        if meta["title"]:
            st.session_state["name_input"] = meta["title"]
        if meta["desc"]:
            st.session_state["points_input"] = meta["desc"]
            
        st.session_state["meta_notice"] = meta["message"]
    else:
        st.session_state["meta_notice"] = "⚠️ 분석할 링크를 먼저 입력해주세요!"

# -------------------------------------------------------------
# 3. Header
# -------------------------------------------------------------
st.markdown('<div class="badge-tag">THREADS AUTO MARKETING PRO</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">🧵 스레드 제휴마케팅 썰 글 & 댓글/답글 생성기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">제휴 링크와 키워드만 넣으면, <b>1) 스레드 도달률 5배 썰 글 4종</b>, <b>2) 공정위 첫 댓글</b>, <b>3) 독자 댓글용 자동 답글 5종</b>까지 한 방에 뽑아드립니다.</div>', unsafe_allow_html=True)

st.divider()

# -------------------------------------------------------------
# 4. 프리셋 샘플 버튼 (원클릭 로드)
# -------------------------------------------------------------
st.markdown("##### ⚡ 빠른 샘플 불러오기 (원클릭)")
p_col1, p_col2, p_col3 = st.columns(3)

p_col1.button(
    "🧹 무선청소기",
    key="btn_sample1",
    on_click=cb_load_preset,
    args=(
        "https://link.coupang.com/a/sample_cleaner",
        "샤오미 미니 무선 핸디 청소기",
        "책상 위 지우개 가루랑 키보드 머리카락 1초 흡입, 가벼워서 손목 안 아픔",
        "쿠팡 파트너스",
        "청소기 샘플이 로드되었습니다."
    )
)

p_col2.button(
    "🖱️ 버티컬 마우스",
    key="btn_sample2",
    on_click=cb_load_preset,
    args=(
        "https://link.coupang.com/a/sample_mouse",
        "로지텍 무선 인체공학 버티컬 마우스",
        "손목터널증후군 찌릿하던 거 3일 만에 사라짐, 클릭감 부드럽고 가성비 최고",
        "쿠팡 파트너스",
        "버티컬 마우스 샘플이 로드되었습니다."
    )
)

p_col3.button(
    "🍫 단백질 쉐이크",
    key="btn_sample3",
    on_click=cb_load_preset,
    args=(
        "https://smartstore.naver.com/sample_protein",
        "비린내 없는 초코맛 프로틴 단백질 쉐이크",
        "특유의 비린내 0%, 그냥 시원한 초코우유 맛이라 아침 대용으로 거부감 없이 원샷",
        "네이버 브랜드 커넥트/쇼핑",
        "단백질 쉐이크 샘플이 로드되었습니다."
    )
)

st.write("")

# -------------------------------------------------------------
# 5. 입력 섹션
# -------------------------------------------------------------
with st.container():
    st.markdown("##### 📋 상품 및 제휴 정보 입력")
    
    c_url, c_btn = st.columns([4, 1])
    with c_url:
        st.text_input(
            "1. 제휴 링크 또는 상품 URL (쿠팡, 스마트스토어 등)",
            placeholder="예: https://link.coupang.com/a/... 또는 https://smartstore.naver.com/...",
            key="url_input"
        )
    with c_btn:
        st.write("")
        st.write("")
        st.button("🔍 링크 분석", key="btn_parse_link", on_click=cb_parse_link)

    if st.session_state.get("meta_notice"):
        st.info(f"💡 {st.session_state['meta_notice']}")

    col_in1, col_in2 = st.columns([1, 1])
    with col_in1:
        st.text_input(
            "2. 상품명 (필수)",
            placeholder="예: 샤오미 미니 무선 청소기",
            key="name_input"
        )
        
        plat_options = ["쿠팡 파트너스", "네이버 브랜드 커넥트/쇼핑", "기타 제휴마케팅"]
        st.selectbox(
            "3. 제휴 플랫폼 (공정위 문구 자동 분기)",
            plat_options,
            key="plat_input"
        )

    with col_in2:
        st.text_area(
            "4. 핵심 장점 / 실구매 체감 후기 (선택)",
            placeholder="예: 가볍고 흡입력 짱, 소음 적고 디자인 깔끔",
            height=122,
            key="points_input"
        )

# 현재 입력값 추출
curr_url = st.session_state["url_input"]
curr_name = st.session_state["name_input"]
curr_plat = st.session_state["plat_input"]
curr_points = st.session_state["points_input"]

plat_code = "coupang" if curr_plat == "쿠팡 파트너스" else ("naver" if "네이버" in curr_plat else "etc")

st.write("")
generate_btn = st.button("🚀 스레드 썰 글 4종 + 댓글/답글 일괄 생성하기", type="primary", use_container_width=True)

# -------------------------------------------------------------
# 6. 생성 및 결과 출력 섹션
# -------------------------------------------------------------
if generate_btn:
    if not curr_name.strip():
        st.error("⚠️ 상품명을 꼭 입력해주세요! (상품명만 있으면 즉시 생성됩니다)")
    else:
        with st.spinner("스레드 알고리즘 맞춤 썰 글과 독자 답글을 생성하고 있습니다..."):
            posts = generate_threads_posts(
                product_name=curr_name,
                key_points=curr_points,
                affiliate_link=curr_url,
                platform_type=plat_code
            )
            replies = generate_reply_templates(
                product_name=curr_name,
                affiliate_link=curr_url,
                platform_type=plat_code
            )
            st.session_state["posts_data"] = posts
            st.session_state["replies_data"] = replies

# 결과가 세션에 존재할 때 화면 렌더링
if st.session_state.get("posts_data"):
    posts = st.session_state["posts_data"]
    replies = st.session_state["replies_data"]

    st.write("")
    st.markdown("### 🎯 생성 결과 리포트")
    st.success("✅ **생성 완료**: 모바일에서 아래 박스 우측 상단의 **[📋 복사]** 아이콘을 누르면 터치 한 번으로 복사됩니다!")

    tabs = st.tabs([
        "🔥 [A] 찐후기 썰",
        "💡 [B] 호구방지 썰",
        "☕ [C] 일상공감 썰",
        "🎯 [D] 단점솔직 썰",
        "💬 [NEW] 독자 댓글 답글 5종",
        "🛡️ 떡상 운영 꿀팁"
    ])

    def render_post_tab(post_item):
        st.markdown(f"#### {post_item['title']}")
        st.caption(post_item['subtitle'])
        
        c1, c2 = st.columns([1, 1])
        with c1:
            st.markdown("##### 1️⃣ 스레드 본문용 (오른쪽 위 📋 복사)")
            st.code(post_item["body"], language=None)
            with st.expander("✏️ 텍스트로 직접 수정해서 복사하기"):
                st.text_area("본문 수정", value=post_item["body"], height=200, key=f"edit_body_{post_item['title']}")

        with c2:
            st.markdown("##### 2️⃣ 첫 댓글용 (등록 후 내 글에 바로 댓글 달기)")
            st.code(post_item["comment"], language=None)
            with st.expander("✏️ 첫 댓글 직접 수정해서 복사하기"):
                st.text_area("댓글 수정", value=post_item["comment"], height=200, key=f"edit_comm_{post_item['title']}")

        with st.expander("📌 본문+링크 일체형 전체 복사 (스레드 외 블로그/카페용)"):
            st.code(post_item["full"], language=None)

    with tabs[0]:
        render_post_tab(posts["type_a"])

    with tabs[1]:
        render_post_tab(posts["type_b"])

    with tabs[2]:
        render_post_tab(posts["type_c"])

    with tabs[3]:
        render_post_tab(posts["type_d"])

    with tabs[4]:
        st.markdown("#### 💬 독자 반응 대응용 실전 답글(대댓글) 5종 세트")
        st.info("💡 **댓글 대응 팁**: 독자가 질문을 남겼을 때 30분 이내에 답글을 달아주면, 스레드 알고리즘이 '반응 좋은 대화방'으로 인식해 수천 명의 피드에 추가 추천 노출합니다!")
        
        for idx, rep in enumerate(replies, start=1):
            with st.container():
                st.markdown(f"**Q{idx}. {rep['category']}** `({rep['trigger']})`")
                st.code(rep["reply"], language=None)
                st.write("")

    with tabs[5]:
        st.markdown("#### 🛡️ 스레드 제휴마케팅 3대 컴플라이언스 & 계정보호 수칙")
        st.markdown("""
        1. **본문에 링크 금지 (첫 댓글 고정)**
           - 스레드는 외부 링크가 포함된 본문의 노출을 90% 이상 차단합니다. 썰만 풀고 **"링크는 첫 댓글에 고정해 둘게요"**가 공식입니다.
        2. **공정위 경제적 이해관계 필수 고지**
           - 쿠팡 파트너스 링크 게시 시 공정위 문구가 빠지면 적립금 환수 및 계정 영구 정지 처분을 받을 수 있습니다. (첫 댓글에 자동 포함됨)
        3. **일상 7 : 홍보 3 황금 비율 유지**
           - 매일 제휴 링크 글만 올리면 스팸 봇으로 찍혀 섀도우밴(도달 제한)을 당합니다. 하루에 3개를 올린다면 2개는 일상·공감 썰, 1개만 제휴 썰로 운영하세요.
        """)

# -------------------------------------------------------------
# 7. Footer
# -------------------------------------------------------------
st.divider()
st.caption("Threads Affiliate Marketing Pro v2.0 · 무결점 실전 배포 엔진")
