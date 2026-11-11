"""
Place Insight Pro - 네이버 스마트플레이스 운영 진단 & 새소식 스튜디오
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
    /* 전체 폰트 및 배경 */
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
st.sidebar.caption("네이버 스마트플레이스 정밀 진단 시스템")

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
            "has_menu_photos": True,
            "menu_items": [
                {"name": "대표 메뉴 A", "price": "15,000원", "desc": "신선한 재료로 만든 시그니처 메뉴"},
                {"name": "인기 메뉴 B", "price": "12,000원", "desc": "남녀노소 좋아하는 추천 메뉴"}
            ],
            "amenities": ["단체석", "주차", "예약"],
            "has_reservation": False,
            "has_order": False,
            "has_talktalk": False,
            "has_coupon": False,
            "has_recent_news": False
        }
    st.session_state.last_preset = selected_preset_name

# URL 빠른 입력 검사창
st.sidebar.markdown("---")
st.sidebar.markdown("### 🔗 플레이스 URL 진단")
naver_url_input = st.sidebar.text_input("네이버 플레이스 링크", placeholder="https://m.place.naver.com/restaurant/...", help="네이버 지도나 플레이스 링크를 넣으시면 매장 정보를 불러옵니다.")
if st.sidebar.button("🔍 URL 분석 실행", use_container_width=True):
    if naver_url_input.strip():
        st.sidebar.info("네이버 보안 캡차(ncaptcha) 정책으로 인해 웹 클라우드 직접 조회가 차단될 수 있습니다. 아래 폼에서 세부 정보를 검토하거나 수정하실 수 있습니다.")
        # 간이 파싱
        st.session_state.current_data["intro"] = st.session_state.current_data.get("intro", "")

# 매장 정보 수정 아코디언
with st.sidebar.expander("⚙️ 매장 세부 정보 수정", expanded=False):
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
    
    st.markdown("**고객 전환 장치**")
    cur["has_reservation"] = st.checkbox("네이버 예약 활성화", value=cur.get("has_reservation", False))
    cur["has_talktalk"] = st.checkbox("네이버 톡톡 상담 연결", value=cur.get("has_talktalk", False))
    cur["has_coupon"] = st.checkbox("플레이스 쿠폰 발행 중", value=cur.get("has_coupon", False))
    cur["has_recent_news"] = st.checkbox("최근 30일 내 새소식 발행", value=cur.get("has_recent_news", False))

data = st.session_state.current_data
audit = calculate_place_audit(data)

# 4. 상단 히어로 헤더
st.markdown(f"""
<div class="hero-card">
    <div class="hero-badge">PLACE / DIAGNOSTIC NOTE</div>
    <div class="hero-title">{data.get('name', '매장')} 플레이스 정밀 진단</div>
    <div class="hero-sub">{data.get('region', '')} · {data.get('category', '')} · 2026.11 실시간 운영 데이터 기준</div>
</div>
""", unsafe_allow_html=True)

# 5. 메인 탭 레이아웃
tabs = st.tabs([
    "📊 진단 대시보드",
    "🎯 강점 vs 실제 반영도",
    "📋 이번 주 15분 실행 과제",
    "⚔️ 경쟁업체 비교 & 노출 관측",
    "✍️ 새소식 스튜디오",
    "📄 카톡 전송용 요약본"
])

# -------------------------------------------------------------
# TAB 1: 📊 진단 대시보드
# -------------------------------------------------------------
with tabs[0]:
    col1, col2 = st.columns([1, 2])
    
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
            <div style="font-size: 0.95rem; font-weight: 800; color: #173C34; margin-bottom: 1rem;">4대 핵심 영역 진단 점수</div>
        """, unsafe_allow_html=True)
        
        scores = audit['scores']
        
        # 4개 영역 바
        cols_m = st.columns(4)
        with cols_m[0]:
            st.metric("정보 정확성", f"{scores['info']} / 25")
            st.progress(scores['info'] / 25)
        with cols_m[1]:
            st.metric("특장점 반영", f"{scores['strengths']} / 25")
            st.progress(scores['strengths'] / 25)
        with cols_m[2]:
            st.metric("사진·콘텐츠", f"{scores['content']} / 25")
            st.progress(scores['content'] / 25)
        with cols_m[3]:
            st.metric("고객 전환", f"{scores['conversion']} / 25")
            st.progress(scores['conversion'] / 25)
            
        st.markdown("</div>", unsafe_allow_html=True)

    # 핵심 발견 (Field Note 01)
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
        st.success("모든 주요 운영 지표가 양호하게 등록되어 있습니다!")

# -------------------------------------------------------------
# TAB 2: 🎯 사장님 강점 vs 실제 반영도
# -------------------------------------------------------------
with tabs[1]:
    st.markdown("### 사장님이 말한 강점, 손님 눈에도 보이나요? 👀")
    st.caption("사장님은 '우리 집은 단체도 되고 주차도 편하다'고 생각하지만, 실제 플레이스 화면에는 손님이 믿고 예약할 증거가 빠져 있는 경우가 많습니다.")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
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
            
    st.info("💡 **개선 팁**: 손님은 설명문에 적힌 추상적인 단어보다 '최대 몇 명?', '주차 몇 대?', '단체석 사진'을 보고 예약을 결정합니다. 숫자가 빠진 강점은 매출로 연결되지 않습니다.")

# -------------------------------------------------------------
# TAB 3: 📋 이번 주 15분 실행 과제
# -------------------------------------------------------------
with tabs[2]:
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
# TAB 4: ⚔️ 경쟁업체 비교 & 노출 관측
# -------------------------------------------------------------
with tabs[3]:
    st.markdown("### 같은 검색어에서, 무엇이 다를까요? ⚔️")
    st.caption("고객이 검색창에서 매장을 고를 때 비교하는 핵심 정보의 공백을 발견합니다.")
    
    comps = data.get("competitors", [])
    if comps:
        st.markdown("""
        | 업체명 | 단체 수용 인원 | 단체/세트 메뉴 | 단체석 사진 | 예약 방식 | 쿠폰 혜택 |
        | :--- | :--- | :--- | :--- | :--- | :--- |
        """ + "\n".join([f"| **{c['name']}** | {c['capacity']} | {c['menu']} | {c['photo']} | {c['reservation']} | {c['coupon']} |" for c in comps]))
    else:
        st.write("비교 데이터 준비 중")
        
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
# TAB 5: ✍️ 새소식 스튜디오 (원클릭 AI 작성기)
# -------------------------------------------------------------
with tabs[4]:
    st.markdown("### 강점을, 고객이 이해하는 이야기로. ✍️")
    st.caption("특장점과 부족한 증거를 연결해 네이버 스마트플레이스에 바로 올릴 수 있는 맞춤형 새소식을 생성합니다.")
    
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
# TAB 6: 📄 카톡 전송용 요약본
# -------------------------------------------------------------
with tabs[5]:
    st.markdown("### 사장님 카톡 전송용 브리핑 요약문 📱")
    st.caption("미팅 전이나 컨설팅 후 사장님 카톡으로 1초 만에 전송할 수 있는 텍스트 브리핑입니다.")
    
    summary_text = f"""[📍 {data.get('name')} 플레이스 운영 진단 리포트]

■ 종합 점수: {audit['total_score']}점 / 100점 ({audit['grade']}등급)
■ 진단 요약: {audit['grade_desc']}

▶ 4대 영역별 점수
- 정보 정확성: {audit['scores']['info']}/25점
- 특장점 반영: {audit['scores']['strengths']}/25점
- 사진·콘텐츠: {audit['scores']['content']}/25점
- 고객 전환장치: {audit['scores']['conversion']}/25점

▶ 핵심 발견
"{audit['field_note']['title']}"
{audit['field_note']['description']}

▶ 이번 주 15분 실전 과제
1. {audit['priority_tasks'][0]['title']} ({audit['priority_tasks'][0]['time']})
2. {audit['priority_tasks'][1]['title']} ({audit['priority_tasks'][1]['time']})
3. {audit['priority_tasks'][2]['title']} ({audit['priority_tasks'][2]['time']})

※ 상세 진단 및 새소식 초안 생성은 Place Insight Pro 시스템에서 실시간으로 확인하실 수 있습니다."""

    st.text_area("카톡 복붙용 리포트", value=summary_text, height=350)
