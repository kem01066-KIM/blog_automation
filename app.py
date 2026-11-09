import streamlit as st
import pandas as pd
from scraper import search_naver_blog, search_instagram
from database import init_db, save_candidate, get_saved_candidates, update_candidate, delete_candidate, export_candidates_csv

# 모바일 화면에 맞춘 레이아웃 설정
st.set_page_config(
    page_title="Signal Room · 인플루언서 발굴기",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 커스텀 모바일 최적화 CSS
st.markdown("""
<style>
    .stApp {
        max-width: 1000px;
        margin: 0 auto;
    }
    .candidate-card {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 14px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.03);
    }
    .score-badge-high {
        background-color: #ecfdf5;
        color: #059669;
        font-weight: bold;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        display: inline-block;
    }
    .score-badge-mid {
        background-color: #eff6ff;
        color: #2563eb;
        font-weight: bold;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.85rem;
        display: inline-block;
    }
    .tag-chip {
        background-color: #f1f5f9;
        color: #475569;
        padding: 2px 8px;
        border-radius: 6px;
        font-size: 0.78rem;
        margin-right: 4px;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# DB 초기화
init_db()

st.title("🎯 Signal Room · 인플루언서 발굴기")
st.caption("복잡한 API 키 없이 실시간 네이버 블로그 & 인스타그램 공구·체험단 파트너를 발굴합니다.")

# 메인 탭 구성
tab1, tab2, tab3 = st.tabs(["🔍 실시간 인플루언서 발굴", "📁 내 보관함 (영구저장)", "💬 협업 컨택 템플릿"])

# ==========================================
# TAB 1: 실시간 인플루언서 발굴
# ==========================================
with tab1:
    st.subheader("새로운 인플루언서 탐색")
    
    col1, col2 = st.columns([1, 1])
    with col1:
        platform = st.radio("플랫폼 선택", ["인스타그램", "네이버 블로그"], horizontal=True)
    with col2:
        purpose = st.radio("캠페인 목적", ["공구", "체험단"], horizontal=True)

    # 추천 빠른 검색 키워드
    st.write("💡 **인기 카테고리 빠른 선택**")
    if "search_input" not in st.session_state:
        st.session_state["search_input"] = "주방용품"
        
    c1, c2, c3 = st.columns(3)
    if c1.button("🍳 주방/살림", use_container_width=True):
        st.session_state["search_input"] = "주방용품"
        st.session_state["auto_search"] = True
        st.rerun()
    if c2.button("☕ 홈카페", use_container_width=True):
        st.session_state["search_input"] = "홈카페"
        st.session_state["auto_search"] = True
        st.rerun()
    if c3.button("👶 육아/키즈", use_container_width=True):
        st.session_state["search_input"] = "육아용품"
        st.session_state["auto_search"] = True
        st.rerun()

    c4, c5, c6 = st.columns(3)
    if c4.button("💄 뷰티/스킨", use_container_width=True):
        st.session_state["search_input"] = "기초화장품"
        st.session_state["auto_search"] = True
        st.rerun()
    if c5.button("🥗 건강/식단", use_container_width=True):
        st.session_state["search_input"] = "다이어트 식품"
        st.session_state["auto_search"] = True
        st.rerun()
    if c6.button("👗 패션/잡화", use_container_width=True):
        st.session_state["search_input"] = "패션잡화"
        st.session_state["auto_search"] = True
        st.rerun()

    # 키워드 검색창
    keyword = st.text_input("검색할 제품명, 브랜드, 카테고리 입력", key="search_input", placeholder="예: 밀폐용기, 커피머신, 세라믹식기")
    
    search_clicked = st.button("🚀 실시간 인플루언서 발굴 시작", type="primary", use_container_width=True)
    auto_run = st.session_state.pop("auto_search", False)
    
    if search_clicked or auto_run or "last_results" in st.session_state:
        if search_clicked or auto_run:
            target_kw = st.session_state.get("search_input", keyword).strip()
            with st.spinner(f"'{target_kw}' 관련 {platform} {purpose} 인플루언서를 실시간 분석 중..."):
                if platform == "네이버 블로그":
                    results = search_naver_blog(target_kw, purpose=purpose, max_results=12)
                else:
                    results = search_instagram(target_kw, purpose=purpose, max_results=12)
                st.session_state["last_results"] = results
                st.session_state["last_platform"] = platform
                st.session_state["last_purpose"] = purpose
                st.session_state["last_kw"] = target_kw
        else:
            results = st.session_state.get("last_results", [])
            platform = st.session_state.get("last_platform", platform)
            purpose = st.session_state.get("last_purpose", purpose)
            target_kw = st.session_state.get("last_kw", keyword)
            
        st.write(f"총 **{len(results)}명**의 {purpose} 후보를 실시간 발굴했습니다. (검색어: **{target_kw}**)")
        
        for idx, item in enumerate(results):
            score = item["score"]
            badge_class = "score-badge-high" if score >= 88 else "score-badge-mid"
            
            with st.container():
                st.markdown(f"""
                <div class="candidate-card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                        <div>
                            <span style="font-size:1.1rem; font-weight:bold;">{item['name']}</span>
                            <span style="color:#64748b; font-size:0.9rem; margin-left:6px;">{item['handle']}</span>
                        </div>
                        <div class="{badge_class}">적합도 {score}점 · {item['level'].split()[0]}</div>
                    </div>
                    <div style="color:#334155; font-size:0.95rem; font-weight:500; margin-bottom:6px;">
                        {item['title']}
                    </div>
                    <div style="color:#64748b; font-size:0.85rem; margin-bottom:10px;">
                        {item['snippet']}
                    </div>
                    <div style="margin-bottom:12px;">
                        {''.join([f'<span class="tag-chip">#{s}</span>' for s in item.get('signals', [])])}
                        <span class="tag-chip" style="background:#e0f2fe; color:#0369a1;">{item['date']}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                btn_col1, btn_col2 = st.columns([1, 1])
                with btn_col1:
                    target_url = item["post_url"] if item["post_url"] else item["profile_url"]
                    st.link_button("🔗 프로필/글 바로가기", target_url, use_container_width=True)
                with btn_col2:
                    save_key = f"save_{item['platform']}_{item['handle']}_{idx}"
                    if st.button(f"💾 보관함에 담기 ({purpose})", key=save_key, use_container_width=True):
                        saved = save_candidate({
                            "platform": item["platform"],
                            "name": item["name"],
                            "handle": item["handle"],
                            "profile_url": item["profile_url"],
                            "post_url": item["post_url"],
                            "title": item["title"],
                            "snippet": item["snippet"],
                            "category": keyword,
                            "purpose": purpose,
                            "score": item["score"],
                            "status": "검토중",
                            "memo": f"검색 키워드: {keyword}"
                        })
                        if saved:
                            st.success(f"'{item['name']}' 후보를 보관함에 저장했습니다!")
                st.divider()

# ==========================================
# TAB 2: 내 보관함 (영구 저장 및 관리)
# ==========================================
with tab2:
    st.subheader("📁 내 관심 인플루언서 보관함")
    st.caption("서버가 재시작되어도 SQLite 데이터베이스에 영구 보존됩니다.")
    
    fcol1, fcol2, fcol3 = st.columns(3)
    with fcol1:
        f_platform = st.selectbox("플랫폼 필터", ["전체", "네이버 블로그", "인스타그램"])
    with fcol2:
        f_purpose = st.selectbox("목적 필터", ["전체", "공구", "체험단"])
    with fcol3:
        f_status = st.selectbox("상태 필터", ["전체", "검토중", "컨택완료", "협업확정", "보류"])
        
    saved_list = get_saved_candidates(platform=f_platform, purpose=f_purpose, status=f_status)
    st.write(f"현재 보관 중인 인플루언서: **{len(saved_list)}명**")
    
    # CSV 다운로드 버튼
    if saved_list:
        csv_data = export_candidates_csv(saved_list)
        st.download_button(
            label="📥 엑셀(CSV) 일괄 다운로드",
            data=csv_data.encode("utf-8-sig"),
            file_name=f"인플루언서_보관함_{f_purpose}_{f_status}.csv",
            mime="text/csv",
            use_container_width=True
        )
        st.divider()
        
        for c in saved_list:
            cid = c["id"]
            p_label = "네이버" if c["platform"] == "naver" else "인스타"
            
            with st.expander(f"[{p_label}] {c['name']} ({c['handle']}) · {c['purpose']} · {c['status']}", expanded=True):
                st.write(f"**적합도 점수:** {c['score']}점 | **저장일:** {c['created_at']}")
                st.write(f"**스니펫:** {c.get('snippet', '')}")
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.link_button("🔗 프로필 열기", c["profile_url"], use_container_width=True)
                with col_b:
                    if c.get("post_url"):
                        st.link_button("📄 최근 글 열기", c["post_url"], use_container_width=True)
                        
                # 상태 및 메모 수정
                edit_col1, edit_col2 = st.columns([1, 2])
                with edit_col1:
                    new_status = st.selectbox(
                        "진행 상태",
                        ["검토중", "컨택완료", "협업확정", "보류"],
                        index=["검토중", "컨택완료", "협업확정", "보류"].index(c["status"]) if c["status"] in ["검토중", "컨택완료", "협업확정", "보류"] else 0,
                        key=f"status_{cid}"
                    )
                with edit_col2:
                    new_memo = st.text_input("메모 (수수료, 일정 등)", value=c.get("memo", ""), key=f"memo_{cid}")
                    
                act_col1, act_col2 = st.columns([1, 1])
                with act_col1:
                    if st.button("수정 저장", key=f"btn_up_{cid}", use_container_width=True):
                        update_candidate(cid, new_status, new_memo)
                        st.success("수정되었습니다.")
                        st.rerun()
                with act_col2:
                    if st.button("삭제", key=f"btn_del_{cid}", use_container_width=True):
                        delete_candidate(cid)
                        st.warning("삭제되었습니다.")
                        st.rerun()
    else:
        st.info("보관함에 저장된 후보가 없습니다. '실시간 인플루언서 발굴' 탭에서 검색 후 [보관함에 담기]를 눌러보세요.")

# ==========================================
# TAB 3: 협업 컨택 템플릿
# ==========================================
with tab3:
    st.subheader("💬 인플루언서 컨택 템플릿 (원클릭 복사)")
    st.caption("인스타그램 DM이나 네이버 블로그 비밀댓글/쪽지로 보낼 때 복사해서 쓰실 수 있는 표준 양식입니다.")
    
    st.markdown("#### 1. 인스타그램 DM 공구 제안서")
    ig_dm_template = """안녕하세요 {인플루언서_이름} 님! 평소 피드 정성스런 콘텐츠 정말 잘 보고 있는 담당자입니다 :)

이번에 {인플루언서_이름} 님의 감성과 너무 잘 어울리는 [{제품/브랜드명}] 공구 협업을 제안드리고자 연락드렸습니다.

- 제품명: {제품명}
- 특징: {핵심 장점 1~2가지}
- 혜택: 최저가 온라인 단독 할인율 제공 + 높은 판매 수수료율(협의 가능)
- 일정: 상호 협의 후 편하신 주간에 진행 가능

궁금하신 점이나 샘플 먼저 체험해보고 싶으시다면 편하게 회신 부탁드립니다. 상세 제안서와 제품 샘플 바로 전달드리겠습니다! 감사합니다."""
    st.code(ig_dm_template, language="text")
    
    st.markdown("#### 2. 네이버 블로그 체험단/협찬 제안서 (비밀댓글·쪽지용)")
    blog_template = """안녕하세요 {블로거_이름} 님! 정성스러운 포스팅 늘 유익하게 읽고 있습니다.

다름이 아니라 저희 브랜드에서 이번에 출시된 [{제품명}] 제품 체험단 협업을 제안드리고자 비밀댓글 남깁니다.

- 제공 내역: {제품 본품 무료 제공} + {소정의 원고료 지급 협의 가능}
- 미션: 솔직하고 자연스러운 실사용 후기 포스팅 1회
- 기한: 제품 수령 후 10일 이내 자율 발행

진행 의사가 있으시거나 문의사항이 있으시면 아래 연락처나 메일로 편하게 회신 주시면 바로 샘플 발송 안내드리겠습니다.

- 회신 이메일: {담당자_이메일}
- 담당자 연락처: {연락처}

감사합니다. 좋은 하루 보내세요!"""
    st.code(blog_template, language="text")
