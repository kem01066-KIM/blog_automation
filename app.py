"""
Place Insight Pro - 네이버 스마트플레이스 운영 진단 & 새소식 스튜디오 (확장 업그레이드 버전)
"""

import streamlit as st
import json
from engine import calculate_place_audit
from news_studio import generate_news_post
from presets import PRESETS

# 1. 페이지 설정
st.set_page_config(
    page_title="Place Insight Pro — 플레이스 운영 진단",
    page_icon="📍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 2. 커스텀 CSS (성수동 감성의 올리브 그린 & 웜 베이지 테마)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Pretendard', sans-serif;
    }
    
    .main {
        background-color: #F8F9F5;
    }
    
    /* 헤더 카드 */
    .hero-card {
        background: linear-gradient(135deg, #173C34 0%, #204C42 100%);
        border-radius: 1.5rem;
        padding: 2.2rem 2.5rem;
        color: white;
        box-shadow: 0 16px 36px rgba(23, 60, 52, 0.15);
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    
    .hero-badge {
        display: inline-block;
        background-color: rgba(230, 190, 122, 0.2);
        color: #E6BE7A;
        padding: 0.35rem 0.85rem;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.1em;
        margin-bottom: 0.8rem;
    }
    
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        line-height: 1.3;
        margin-bottom: 0.5rem;
    }
    
    .hero-sub {
        font-size: 0.95rem;
        color: #C1D5CB;
    }
    
    /* 점수 카드 */
    .score-box {
        background: white;
        border: 1px solid #DCE3D9;
        border-radius: 1.25rem;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03);
    }
    
    .score-num {
        font-size: 3.2rem;
        font-weight: 800;
        color: #173C34;
        line-height: 1;
    }
    
    .score-total {
        font-size: 1.1rem;
        color: #8C9C95;
        font-weight: 600;
    }
    
    /* 섹션 카드 */
    .insight-card {
        background: white;
        border: 1px solid #E2E8DF;
        border-radius: 1.25rem;
        padding: 1.5rem 1.8rem;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.03);
    }
    
    .field-note-card {
        background: #FFFBF2;
        border: 1.5px solid #F1DFBD;
        border-radius: 1.25rem;
        padding: 1.6rem 1.8rem;
        margin-bottom: 1.5rem;
    }
    
    /* 배지 스타일 */
    .status-badge-good {
        background-color: #E8F5E9;
        color: #2E7D32;
        padding: 0.25rem 0.7rem;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
    }
    
    .status-badge-warn {
        background-color: #FFF3E0;
        color: #E65100;
        padding: 0.25rem 0.7rem;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
    }
    
    .status-badge-bad {
        background-color: #FFEBEE;
        color: #C62828;
        padding: 0.25rem 0.7rem;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
    }
    
    /* 과제 카드 */
    .task-card {
        background: white;
        border: 1px solid #EAE0CE;
        border-left: 5px solid #75835B;
        border-radius: 1rem;
        padding: 1.2rem 1.4rem;
        margin-bottom: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# 3. 사이드바 - 매장 선택 및 입력
st.sidebar.markdown("## 📍 Place Insight Pro")
st.sidebar.caption("네이버 스마트플레이스 정밀 진단 시스템 (v2.0 확장)")

RUBRIC_VERSION = "2.3"
if st.session_state.get("rubric_version") != RUBRIC_VERSION:
    st.session_state.current_data = None
    st.session_state.rubric_version = RUBRIC_VERSION

preset_options = list(PRESETS.keys()) + ["➕ 직접 매장 정보 입력"]
selected_preset_name = st.sidebar.selectbox("🎯 진단할 매장 선택", preset_options, index=0)

# 세션 스테이트 초기화
if "current_data" not in st.session_state or st.session_state.get("last_preset") != selected_preset_name:
    if selected_preset_name in PRESETS:
        st.session_state.current_data = json.loads(json.dumps(PRESETS[selected_preset_name]))
    else:
        st.session_state.current_data = {
            "name": "",
            "category": "일반 음식점",
            "region": "대구",
            "address": "",
            "tel": "",
            "hours": "매일 11:00 ~ 21:00",
            "directions": "",
            "parking": "주차 가능",
            "intro": "",
            "selected_strengths": [
                {"label": "단체 가능", "icon": "👥", "synonyms": ["단체석", "모임", "회식"]},
                {"label": "주차 편리", "icon": "🚗", "synonyms": ["전용 주차장", "무료 주차"]},
                {"label": "가족 외식", "icon": "👨‍👩‍👧‍👦", "synonyms": ["아기의자", "아이동반"]}
            ],
            "keywords": ["대구맛집", "단체모임", "주차편한식당"],
            "photo_count": 10,
            "has_signature_menu": True,
            "menu_photo_ratio": "일부 등록",
            "has_menu_desc": True,
            "has_menu_price": True,
            "menu_items": [
                {"name": "대표 메뉴 A", "price": "15,000원", "desc": "신선한 재료로 만든 시그니처 메뉴"},
                {"name": "인기 메뉴 B", "price": "12,000원", "desc": "남녀노소 좋아하는 추천 메뉴"}
            ],
            "amenities": ["단체석", "주차", "예약"],
            "has_reservation": False,
            "has_smart_call": False,
            "has_alert_benefit": False,
            "has_coupon": False,
            "has_talktalk": False,
            "photo_review_level": "보통",
            "reply_rate": "거의 안 함",
            "reply_quality": "복붙 매크로",
            "has_recent_news": False,
            "news_has_photo_link": False
        }
    st.session_state.last_preset = selected_preset_name

# 매장 정보 수정 아코디언
with st.sidebar.expander("⚙️ 매장 세부 진단 요소 수정", expanded=False):
    cur = st.session_state.current_data
    cur["name"] = st.text_input("상호명", value=cur.get("name", ""))
    cur["region"] = st.text_input("지역/위치", value=cur.get("region", ""))
    cur["category"] = st.text_input("업종 카테고리", value=cur.get("category", ""))
    cur["address"] = st.text_input("도로명 주소", value=cur.get("address", ""))
    cur["tel"] = st.text_input("대표 전화번호", value=cur.get("tel", ""))
    cur["hours"] = st.text_input("영업시간 및 휴무일", value=cur.get("hours", ""))
    cur["parking"] = st.text_input("주차 안내", value=cur.get("parking", ""))
    cur["directions"] = st.text_area("찾아오는 길", value=cur.get("directions", ""))
    cur["intro"] = st.text_area("플레이스 소개글", value=cur.get("intro", ""), height=100)
    cur["photo_count"] = st.number_input("등록 사진 개수", value=cur.get("photo_count", 15), min_value=0, max_value=200)
    
    st.markdown("---")
    st.markdown("🍳 **메뉴명 & 메뉴사진 설정**")
    cur["menu_photo_ratio"] = st.selectbox("메뉴 사진 등록 비율", ["전체 등록", "일부 등록", "없음"], 
                                           index=["전체 등록", "일부 등록", "없음"].index(cur.get("menu_photo_ratio", "일부 등록")))
    cur["has_signature_menu"] = st.checkbox("대표/시그니처 메뉴 지정", value=cur.get("has_signature_menu", True))
    cur["has_menu_desc"] = st.checkbox("메뉴별 매력적인 한 줄 설명", value=cur.get("has_menu_desc", True))
    cur["has_menu_price"] = st.checkbox("전 메뉴 가격 투명 공개", value=cur.get("has_menu_price", True))
    
    st.markdown("---")
    st.markdown("⚡ **각종 핵심 기능 연동**")
    cur["has_reservation"] = st.checkbox("네이버 예약 연동 (당일/시간)", value=cur.get("has_reservation", False))
    cur["has_smart_call"] = st.checkbox("스마트콜(050 번호) 및 통화연결음", value=cur.get("has_smart_call", False))
    cur["has_alert_benefit"] = st.checkbox("플레이스 '알림받기' 동의 혜택", value=cur.get("has_alert_benefit", False))
    cur["has_coupon"] = st.checkbox("플레이스 쿠폰 발행 중 (웰컴/할인)", value=cur.get("has_coupon", False))
    cur["has_talktalk"] = st.checkbox("네이버 톡톡 1:1 상담 연결", value=cur.get("has_talktalk", False))
    
    st.markdown("---")
    st.markdown("💬 **리뷰 & 사장님 답글 설정**")
    cur["reply_rate"] = st.selectbox("사장님 답글 작성률", ["80% 이상", "50% 수준", "거의 안 함"],
                                     index=["80% 이상", "50% 수준", "거의 안 함"].index(cur.get("reply_rate", "거의 안 함")))
    cur["reply_quality"] = st.selectbox("답글 스타일", ["정성 답글", "복붙 매크로"],
                                        index=["정성 답글", "복붙 매크로"].index(cur.get("reply_quality", "복붙 매크로")))
    cur["photo_review_level"] = st.selectbox("포토 리뷰 비중", ["높음", "보통", "낮음"],
                                            index=["높음", "보통", "낮음"].index(cur.get("photo_review_level", "보통")))
    
    st.markdown("---")
    st.markdown("📢 **새소식 활성도**")
    cur["has_recent_news"] = st.checkbox("최근 30일 내 새소식 발행", value=cur.get("has_recent_news", False))

data = st.session_state.current_data
audit = calculate_place_audit(data)

# 4. 상단 히어로 헤더
st.markdown(f"""
<div class="hero-card">
    <div class="hero-badge">PLACE / DIAGNOSTIC NOTE 2.0</div>
    <div class="hero-title">{data.get('name', '매장')} 플레이스 정밀 진단</div>
    <div class="hero-sub">{data.get('region', '')} · {data.get('category', '')} · 6대 핵심 영역 (기능·메뉴·리뷰·특장점) 정밀 진단 기준</div>
</div>
""", unsafe_allow_html=True)

# 5. 메인 탭 레이아웃 (확장 7개 탭)
tabs = st.tabs([
    "📊 종합 진단 대시보드",
    "⚡ 핵심 기능 진단 (예약·스마트콜·쿠폰·알림)",
    "🍳 메뉴 디테일 (메뉴명·가격·사진)",
    "💬 리뷰 & 사장님 답글 관리",
    "🎯 강점 vs 실제 반영도",
    "📋 이번 주 15분 실행 과제",
    "⚔️ 경쟁업체 비교 & 노출 관측",
    "✍️ 새소식 스튜디오",
    "📄 카톡 전송용 요약본"
])

# -------------------------------------------------------------
# TAB 1: 📊 종합 진단 대시보드
# -------------------------------------------------------------
with tabs[0]:
    col1, col2 = st.columns([1, 2.2])
    
    with col1:
        st.markdown(f"""
        <div class="score-box">
            <div style="font-size: 0.9rem; font-weight: 700; color: #75835B; margin-bottom: 0.5rem;">종합 운영 준비도</div>
            <div class="score-num">{audit['total_score']} <span class="score-total">/ 100</span></div>
            <div style="margin-top: 0.8rem;">
                <span class="status-badge-{'good' if audit['grade'] in ['S', 'A'] else 'warn'}" style="font-size: 0.95rem; padding: 0.4rem 1rem;">
                    {audit['grade']} 등급
                </span>
            </div>
            <div style="margin-top: 1.2rem; font-size: 0.88rem; color: #556B60; line-height: 1.5; font-weight: 600;">
                {audit['grade_desc']}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    with col2:
        st.markdown("""<div class="insight-card">
            <div style="font-size: 0.95rem; font-weight: 800; color: #173C34; margin-bottom: 1rem;">6대 핵심 영역 진단 점수</div>
        """, unsafe_allow_html=True)
        
        scores = audit['scores']
        
        # 6개 영역 메트릭
        r1_cols = st.columns(3)
        with r1_cols[0]:
            st.metric("기본 정보", f"{scores['info']} / 15")
            st.progress(min(1.0, max(0.0, float(scores['info']) / 15)))
        with r1_cols[1]:
            st.metric("특장점 키워드", f"{scores['strengths']} / 15")
            st.progress(min(1.0, max(0.0, float(scores['strengths']) / 15)))
        with r1_cols[2]:
            st.metric("메뉴 디테일", f"{scores['menu']} / 20")
            st.progress(min(1.0, max(0.0, float(scores['menu']) / 20)))
            
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        
        r2_cols = st.columns(3)
        with r2_cols[0]:
            st.metric("각종 기능(예약/콜/쿠폰)", f"{scores['features']} / 25")
            st.progress(min(1.0, max(0.0, float(scores['features']) / 25)))
        with r2_cols[1]:
            st.metric("리뷰 & 답글 관리", f"{scores['reviews']} / 15")
            st.progress(min(1.0, max(0.0, float(scores['reviews']) / 15)))
        with r2_cols[2]:
            st.metric("새소식 활성도", f"{scores['news']} / 10")
            st.progress(min(1.0, max(0.0, float(scores['news']) / 10)))
            
        st.markdown("</div>", unsafe_allow_html=True)

    # 핵심 발견 (Field Note)
    fn = audit['field_note']
    st.markdown(f"""
    <div class="field-note-card">
        <div style="font-size: 0.8rem; font-weight: 800; color: #A56C32; letter-spacing: 0.08em; margin-bottom: 0.4rem;">{fn['tag']}</div>
        <div style="font-size: 1.35rem; font-weight: 800; color: #234A40; margin-bottom: 0.6rem;">{fn['title']}</div>
        <div style="font-size: 0.95rem; color: #556B60; line-height: 1.6;">{fn['description']}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # 세부 관찰 사항
    st.markdown("### 🔍 주요 진단 관찰")
    if audit['evidences']:
        for ev in audit['evidences']:
            st.markdown(f"- ⚠️ {ev}")
    else:
        st.success("모든 주요 운영 지표가 완벽하게 세팅되어 있습니다!")

# -------------------------------------------------------------
# TAB 2: ⚡ 핵심 기능 진단 (예약·스마트콜·알림받기·쿠폰·톡톡)
# -------------------------------------------------------------
with tabs[1]:
    st.markdown("### 네이버 플레이스 5대 핵심 기능 연동 진단 ⚡")
    st.caption("플레이스 방문자를 실제 예약 손님과 '저장하기' 단골로 전환시키는 네이버 공식 무료 기능입니다. (25점 만점)")
    
    f_cols = st.columns(5)
    features_list = [
        {"name": "네이버 예약", "val": data.get("has_reservation"), "max": 6, "desc": "24시간 자동 예약 접수 및 노출 가산점"},
        {"name": "스마트콜(050)", "val": data.get("has_smart_call"), "max": 5, "desc": "통화연결음 안내 및 종료 후 위치 자동문자"},
        {"name": "알림받기 혜택", "val": data.get("has_alert_benefit"), "max": 5, "desc": "소식 알림 동의 고객에게 전용 혜택 제공"},
        {"name": "플레이스 쿠폰", "val": data.get("has_coupon"), "max": 5, "desc": "‘저장하기’ 수를 폭발시키는 웰컴 혜택"},
        {"name": "네이버 톡톡", "val": data.get("has_talktalk"), "max": 4, "desc": "통화 부담 없는 1:1 실시간 채팅 문의"}
    ]
    
    for idx, f in enumerate(features_list):
        with f_cols[idx]:
            is_on = f["val"]
            badge_class = "good" if is_on else "bad"
            badge_text = "연동 완료" if is_on else "미연동 (0점)"
            st.markdown(f"""
            <div class="insight-card" style="text-align: center; height: 210px;">
                <div style="font-size: 1.05rem; font-weight: 800; color: #173C34; margin-bottom: 0.4rem;">{f['name']}</div>
                <div><span class="status-badge-{badge_class}">{badge_text}</span></div>
                <div style="font-size: 0.82rem; color: #6E7F74; margin-top: 0.8rem; line-height: 1.4;">
                    {f['desc']}
                </div>
            </div>
            """, unsafe_allow_html=True)
            
    st.info("💡 **전환 극대화 팁**: 특히 '알림받기 혜택'과 '플레이스 쿠폰'은 사장님이 비용을 들이지 않고도 고객의 [저장하기] 수를 단기간에 3배 이상 끌어올릴 수 있는 핵심 무기입니다.")

# -------------------------------------------------------------
# TAB 3: 🍳 메뉴 디테일 (메뉴명·가격·사진)
# -------------------------------------------------------------
with tabs[2]:
    st.markdown("### 메뉴판 디테일 & 비주얼 진단 🍳")
    st.caption("손님이 플레이스를 켜고 가장 먼저 확인하는 것은 '음식 사진'과 '가격'입니다. (20점 만점)")
    
    m_cols = st.columns(4)
    with m_cols[0]:
        st.markdown(f"""
        <div class="insight-card">
            <div style="font-weight: 700; color: #75835B;">메뉴 사진 등록 비율</div>
            <div style="font-size: 1.3rem; font-weight: 800; color: #173C34; margin: 0.3rem 0;">{data.get('menu_photo_ratio')}</div>
            <div style="font-size: 0.8rem; color: #666;">{'전체 메뉴 고화질 사진 완비' if data.get('menu_photo_ratio') == '전체 등록' else '사진 미등록 메뉴 보강 필요'}</div>
        </div>
        """, unsafe_allow_html=True)
    with m_cols[1]:
        st.markdown(f"""
        <div class="insight-card">
            <div style="font-weight: 700; color: #75835B;">시그니처 메뉴 지정</div>
            <div style="font-size: 1.3rem; font-weight: 800; color: #173C34; margin: 0.3rem 0;">{'지정 완료 (대표)' if data.get('has_signature_menu') else '미지정'}</div>
            <div style="font-size: 0.8rem; color: #666;">첫 방문 고객에게 시그니처 뱃지 노출</div>
        </div>
        """, unsafe_allow_html=True)
    with m_cols[2]:
        st.markdown(f"""
        <div class="insight-card">
            <div style="font-weight: 700; color: #75835B;">메뉴별 스토리 설명</div>
            <div style="font-size: 1.3rem; font-weight: 800; color: #173C34; margin: 0.3rem 0;">{'등록됨' if data.get('has_menu_desc') else '미등록'}</div>
            <div style="font-size: 0.8rem; color: #666;">원산지, 조리 비법, 맛 포인트 한 줄 설명</div>
        </div>
        """, unsafe_allow_html=True)
    with m_cols[3]:
        st.markdown(f"""
        <div class="insight-card">
            <div style="font-weight: 700; color: #75835B;">전 메뉴 가격 투명성</div>
            <div style="font-size: 1.3rem; font-weight: 800; color: #173C34; margin: 0.3rem 0;">{'100% 공개' if data.get('has_menu_price') else '일부 누락'}</div>
            <div style="font-size: 0.8rem; color: #666;">가격 미표기(변동/시가) 최소화</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("#### 📋 현재 등록된 메뉴 현황")
    for m in data.get("menu_items", []):
        st.markdown(f"- **{m['name']}** ({m['price']}) : {m.get('desc', '설명 없음')}")

# -------------------------------------------------------------
# TAB 4: 💬 리뷰 & 사장님 답글 관리
# -------------------------------------------------------------
with tabs[3]:
    st.markdown("### 영수증 리뷰 & 사장님 정성 답글 관리 💬")
    st.caption("손님의 리뷰는 매장의 신뢰를 증명하고, 사장님의 답글은 단골을 만듭니다. (15점 만점)")
    
    r_cols = st.columns(3)
    with r_cols[0]:
        r_rate = data.get("reply_rate")
        b_class = "good" if r_rate == "80% 이상" else "warn" if r_rate == "50% 수준" else "bad"
        st.markdown(f"""
        <div class="insight-card">
            <div style="font-weight: 700; color: #75835B;">사장님 답글 작성률</div>
            <div style="font-size: 1.4rem; font-weight: 800; color: #173C34; margin: 0.3rem 0;">
                <span class="status-badge-{b_class}">{r_rate}</span>
            </div>
            <div style="font-size: 0.82rem; color: #666; margin-top: 0.5rem;">
                {'리뷰 10개 중 8개 이상 정성 답글 작성' if r_rate == '80% 이상' else '방치된 리뷰가 많아 고객 소통 단절'}
            </div>
        </div>
        """, unsafe_allow_html=True)
    with r_cols[1]:
        r_qual = data.get("reply_quality")
        b_class2 = "good" if r_qual == "정성 답글" else "warn"
        st.markdown(f"""
        <div class="insight-card">
            <div style="font-weight: 700; color: #75835B;">답글 스타일 및 품질</div>
            <div style="font-size: 1.4rem; font-weight: 800; color: #173C34; margin: 0.3rem 0;">
                <span class="status-badge-{b_class2}">{r_qual}</span>
            </div>
            <div style="font-size: 0.82rem; color: #666; margin-top: 0.5rem;">
                {'손님 닉네임과 주문 메뉴를 언급하는 감동 답글' if r_qual == '정성 답글' else '복붙 매크로성 답변은 감동 저하'}
            </div>
        </div>
        """, unsafe_allow_html=True)
    with r_cols[2]:
        p_level = data.get("photo_review_level")
        b_class3 = "good" if p_level == "높음" else "warn"
        st.markdown(f"""
        <div class="insight-card">
            <div style="font-weight: 700; color: #75835B;">포토 리뷰 비율</div>
            <div style="font-size: 1.4rem; font-weight: 800; color: #173C34; margin: 0.3rem 0;">
                <span class="status-badge-{b_class3}">{p_level}</span>
            </div>
            <div style="font-size: 0.82rem; color: #666; margin-top: 0.5rem;">
                네이버 검색 상위 노출에 가장 강력한 가산점 요소
            </div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("#### 💌 사장님 감동 답글 황금 공식")
    st.markdown("""
    1. **고객 닉네임 + 방문 감사 인사**: "○○님, 소중한 주말 가족 식사로 찾아주셔서 진심으로 감사드립니다."
    2. **고객이 칭찬한 포인트 맞장구**: "남겨주신 사진 속 능이백숙을 너무 맛있게 드셔주셔서 주방 이모님들도 뿌듯해하셨어요!"
    3. **다음 방문 추천 메뉴 안내**: "다음 번 방문 때는 참숯에 바삭하게 구워내는 생오리구이도 꼭 한번 맛보시길 추천드립니다."
    """)

# -------------------------------------------------------------
# TAB 5: 🎯 사장님 강점 vs 실제 반영도
# -------------------------------------------------------------
with tabs[4]:
    st.markdown("### 사장님이 말한 강점, 손님 눈에도 보이나요? 👀")
    st.caption("사장님은 '우리 집은 단체도 되고 주차도 편하다'고 생각하지만, 실제 플레이스 화면에는 손님이 믿고 예약할 증거가 빠져 있는 경우가 많습니다. (15점 만점)")
    
    eval_cols = st.columns(len(audit['strength_evals']))
    for idx, se in enumerate(audit['strength_evals']):
        with eval_cols[idx]:
            b_class = "good" if se['status'] == "반영 양호" else "warn" if se['status'] == "부분 반영" else "bad"
            st.markdown(f"""
            <div class="insight-card" style="text-align: center;">
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">{se['icon']}</div>
                <div style="font-size: 1.15rem; font-weight: 800; color: #173C34; margin-bottom: 0.5rem;">{se['label']}</div>
                <div><span class="status-badge-{b_class}">{se['status']} ({se['score']}점)</span></div>
                <div style="font-size: 0.85rem; color: #6E7F74; margin-top: 0.8rem; line-height: 1.5;">
                    {se['evidence']}
                </div>
            </div>
            """, unsafe_allow_html=True)

# -------------------------------------------------------------
# TAB 6: 📋 이번 주 15분 실행 과제
# -------------------------------------------------------------
with tabs[5]:
    st.markdown("### 이번 주, 가장 먼저 고칠 15분 과제 TOP 3 ⚡")
    st.caption("점수만 보고 끝내지 마세요. 스마트플레이스 센터 모바일 앱에서 15분 만에 바꿀 수 있는 우선순위 과제입니다.")
    
    for task in audit['priority_tasks']:
        st.markdown(f"""
        <div class="task-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-weight: 800; font-size: 1.1rem; color: #244A40;">#{task['id']} {task['title']}</span>
                <div>
                    <span class="status-badge-warn" style="margin-right: 0.4rem;">{task['time']}</span>
                    <span class="status-badge-good">영향도 {task['impact']}</span>
                </div>
            </div>
            <div style="font-size: 0.9rem; color: #405F54; line-height: 1.6; border-left: 2px solid #D9AF70; padding-left: 0.8rem; margin-top: 0.5rem;">
                👉 <b>실행 가이드</b>: {task['action']}
            </div>
        </div>
        """, unsafe_allow_html=True)

# -------------------------------------------------------------
# TAB 7: ⚔️ 경쟁업체 비교 & 노출 관측
# -------------------------------------------------------------
with tabs[6]:
    st.markdown("### 같은 검색어에서, 무엇이 다를까요? ⚔️")
    st.caption("고객이 검색창에서 매장을 고를 때 비교하는 핵심 정보의 공백을 발견합니다.")
    
    comps = data.get("competitors", [])
    if comps:
        st.markdown("""
        | 업체명 | 단체 수용 인원 | 메뉴 & 사진 | 핵심 기능 세팅 | 사장님 답글 | 새소식 |
        | :--- | :--- | :--- | :--- | :--- | :--- |
        """ + "\n".join([f"| **{c['name']}** | {c['capacity']} | {c['menu']} | {c['features']} | {c['reply']} | {c['news']} |" for c in comps]))
        
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📡 타겟 키워드 노출 관측 시뮬레이션")
    kw_cols = st.columns(3)
    with kw_cols[0]:
        st.markdown("""
        <div class="insight-card">
            <div style="font-size: 0.8rem; font-weight: 700; color: #75835B;">모바일 · 1km 기준</div>
            <div style="font-size: 1.1rem; font-weight: 800; color: #173C34; margin: 0.3rem 0;">‘팔공산 오리백숙’</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #2E7D32;">12위 <span style="font-size: 0.85rem; color: #2E7D32;">▲ 3</span></div>
            <div style="font-size: 0.78rem; color: #888;">상위 노출 유지 중</div>
        </div>
        """, unsafe_allow_html=True)
    with kw_cols[1]:
        st.markdown("""
        <div class="insight-card">
            <div style="font-size: 0.8rem; font-weight: 700; color: #75835B;">모바일 · 1km 기준</div>
            <div style="font-size: 1.1rem; font-weight: 800; color: #173C34; margin: 0.3rem 0;">‘팔공산 단체 모임’</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #E65100;">28위 <span style="font-size: 0.85rem; color: #C62828;">▼ 5</span></div>
            <div style="font-size: 0.78rem; color: #888;">특장점 보강 시 진입 가능</div>
        </div>
        """, unsafe_allow_html=True)
    with kw_cols[2]:
        st.markdown("""
        <div class="insight-card">
            <div style="font-size: 0.8rem; font-weight: 700; color: #75835B;">모바일 · 1km 기준</div>
            <div style="font-size: 1.1rem; font-weight: 800; color: #173C34; margin: 0.3rem 0;">‘팔공산 주차편한 식당’</div>
            <div style="font-size: 1.8rem; font-weight: 800; color: #C62828;">100위 밖 <span style="font-size: 0.85rem; color: #888;">—</span></div>
            <div style="font-size: 0.78rem; color: #888;">주차 키워드 새소식 발행 시급</div>
        </div>
        """, unsafe_allow_html=True)

# -------------------------------------------------------------
# TAB 8: ✍️ 새소식 스튜디오
# -------------------------------------------------------------
with tabs[7]:
    st.markdown("### 강점을, 고객이 이해하는 이야기로. ✍️")
    st.caption("특장점과 부족한 증거를 연결해 네이버 스마트플레이스에 바로 올릴 수 있는 맞춤형 새소식을 생성합니다. (10점 만점)")
    
    theme_choice = st.radio(
        "발행할 새소식 주제 선택",
        ["단체 모임", "주차 및 찾아오는 길", "시그니처 메뉴", "단골 쿠폰 이벤트", "아이 놀이방/가족 편의"],
        horizontal=True
    )
    
    news = generate_news_post(theme_choice, data)
    
    st.markdown(f"""
    <div class="insight-card" style="border-top: 4px solid #173C34;">
        <div style="font-size: 0.85rem; font-weight: 700; color: #A56C32; margin-bottom: 0.4rem;">DRAFT PREVIEW / {news['theme']}</div>
        <div style="font-size: 1.3rem; font-weight: 800; color: #173C34; margin-bottom: 1rem;">{news['title']}</div>
        <div style="background-color: #F8FAF6; padding: 1rem; border-radius: 0.75rem; font-size: 0.88rem; color: #556B60; margin-bottom: 1rem;">
            📸 <b>권장 첨부 사진</b>: {news['photo_tip']}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("**복붙용 본문 텍스트**")
    full_text = f"{news['title']}\n\n{news['body']}\n\n" + " ".join(news['tags'])
    st.text_area("새소식 본문", value=full_text, height=260)
    
    st.success("위 본문을 복사해서 [네이버 스마트플레이스 센터 > 새소식 등록]에 그대로 붙여넣으시면 3분 만에 최신화가 완료됩니다!")

# -------------------------------------------------------------
# TAB 9: 📄 카톡 전송용 요약본
# -------------------------------------------------------------
with tabs[8]:
    st.markdown("### 사장님 카톡 전송용 브리핑 요약문 📱")
    st.caption("미팅 전이나 컨설팅 후 사장님 카톡으로 1초 만에 전송할 수 있는 텍스트 브리핑입니다.")
    
    tasks_summary_lines = "\n".join([f"{idx+1}. {t['title']} ({t['time']})" for idx, t in enumerate(audit.get('priority_tasks', []))])
    summary_text = f"""[📍 {data.get('name')} 플레이스 6대 영역 정밀 진단 리포트]

■ 종합 점수: {audit['total_score']}점 / 100점 ({audit['grade']}등급)
■ 진단 요약: {audit['grade_desc']}

▶ 6대 세부 영역별 점수
- 1. 기본 정보 정확성: {audit['scores']['info']}/15점
- 2. 특장점 키워드: {audit['scores']['strengths']}/15점
- 3. 메뉴 디테일(사진/설명): {audit['scores']['menu']}/20점
- 4. 핵심 기능(예약·콜·쿠폰·알림): {audit['scores']['features']}/25점
- 5. 리뷰 관리 & 사장님 답글: {audit['scores']['reviews']}/15점
- 6. 새소식 활성도: {audit['scores']['news']}/10점

▶ 핵심 발견
"{audit['field_note']['title']}"
{audit['field_note']['description']}

▶ 이번 주 15분 실전 과제
{tasks_summary_lines}

※ 상세 진단 및 새소식 초안 생성은 Place Insight Pro 시스템에서 실시간으로 확인하실 수 있습니다."""

    st.text_area("카톡 복붙용 리포트", value=summary_text, height=360)
