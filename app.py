"""
소상공인 안드로이드 스마트 콜백 매니저 (Smart Callback Pro) - Streamlit Web UI
전화 통화 종료 시 네이버 플레이스 링크, 약도, 영업시간, 맞춤 안내 자동 발송 관리기
"""

import streamlit as st
import pandas as pd
import json
import os
import sys
from datetime import datetime

# 모듈 경로 추가
sys.path.append(os.path.dirname(__file__))
from database import (
    get_settings,
    update_settings,
    check_can_send,
    record_log,
    get_logs,
    get_stats,
    clear_logs,
    normalize_phone,
)
from templates import (
    INDUSTRY_TEMPLATES,
    render_message,
    calculate_korean_bytes,
)
from android_daemon import handle_call_ended_event

st.set_page_config(
    page_title="스마트 콜백 Pro - 소상공인 통화 후 문자 자동발송",
    page_icon="📱",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 모바일 반응형 커스텀 CSS
st.markdown("""
<style>
    .main {
        max-width: 1000px;
        margin: 0 auto;
        padding-top: 10px;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 12px;
        padding: 14px 18px;
        border: 1px solid #e9ecef;
        text-align: center;
    }
    .metric-val {
        font-size: 26px;
        font-weight: 800;
        color: #1a73e8;
    }
    .metric-lbl {
        font-size: 13px;
        color: #6c757d;
        margin-top: 4px;
    }
    /* 스마트폰 문자 프리뷰 박스 */
    .phone-container {
        background-color: #f1f3f5;
        border: 2px solid #dee2e6;
        border-radius: 24px;
        padding: 16px;
        max-width: 420px;
        margin: 0 auto 15px auto;
        box-shadow: 0 4px 12px rgba(0,0,0,0.06);
    }
    .phone-header {
        text-align: center;
        font-weight: 700;
        font-size: 14px;
        color: #495057;
        padding-bottom: 10px;
        border-bottom: 1px solid #dee2e6;
        margin-bottom: 12px;
    }
    .sms-bubble {
        background-color: #ffffff;
        border: 1px solid #ced4da;
        border-radius: 16px 16px 16px 2px;
        padding: 14px;
        font-size: 13px;
        line-height: 1.55;
        color: #212529;
        white-space: pre-wrap;
        word-break: break-all;
    }
    .sms-footer {
        display: flex;
        justify-content: space-between;
        margin-top: 6px;
        font-size: 11px;
        color: #868e96;
    }
</style>
""", unsafe_allow_html=True)

# 1. 헤더 영역
st.markdown("### 📱 소상공인 안드로이드 스마트 콜백 Pro")
st.caption("통화가 끝나면 사장님의 네이버 플레이스 링크, 매장 약도, 영업시간, 맞춤 안내를 고객 폰으로 자동 발송합니다 (문자 비용 0원).")

# 2. 통계 대시보드
stats = get_stats()
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{stats["sent_today"]}건</div><div class="metric-lbl">오늘 정상 발송</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{stats["missed_today"]}건</div><div class="metric-lbl">부재중 자동 응대</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{stats["blocked_today"]}건</div><div class="metric-lbl">중복/제외 차단 방어</div></div>', unsafe_allow_html=True)
with col4:
    st.markdown(f'<div class="metric-card"><div class="metric-val">{stats["total_all"]}건</div><div class="metric-lbl">누적 관리 이력</div></div>', unsafe_allow_html=True)

st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

# 설정 로드
settings = get_settings()

# 세션 상태에 편집 값 보관
if "draft_settings" not in st.session_state:
    st.session_state.draft_settings = settings.copy()

# 3. 메인 탭 구성
tabs = st.tabs([
    "💬 콜백 문구 & 실시간 프리뷰",
    "⚙️ 스마트 발송 규칙 & 폰 연동",
    "🧪 통화 종료 시뮬레이터",
    "📊 발송 이력 & 통계",
])

# ==============================================================================
# TAB 1: 문구 설정 & 프리뷰
# ==============================================================================
with tabs[0]:
    st.markdown("#### 1. 업종별 추천 템플릿 원클릭 불러오기")
    st.write("사장님의 업종을 선택하시면 검증된 실전 문구와 매장 안내 양식이 즉시 세팅됩니다:")

    template_cols = st.columns(len(INDUSTRY_TEMPLATES))
    for i, (cat_name, cat_data) in enumerate(INDUSTRY_TEMPLATES.items()):
        with template_cols[i]:
            if st.button(f"{cat_data['icon']} {cat_name}", key=f"btn_cat_{i}", use_container_width=True):
                st.session_state.draft_settings["category"] = cat_name
                st.session_state.draft_settings["shop_name"] = cat_data["defaults"]["shop_name"]
                st.session_state.draft_settings["phone"] = cat_data["defaults"]["phone"]
                st.session_state.draft_settings["address"] = cat_data["defaults"]["address"]
                st.session_state.draft_settings["place_url"] = cat_data["defaults"]["place_url"]
                st.session_state.draft_settings["business_hours"] = cat_data["defaults"]["business_hours"]
                st.session_state.draft_settings["extra_info"] = cat_data["defaults"]["extra_info"]
                st.session_state.draft_settings["msg_normal"] = cat_data["msg_normal"]
                st.session_state.draft_settings["msg_missed"] = cat_data["msg_missed"]
                st.session_state.draft_settings["msg_holiday"] = cat_data["msg_holiday"]
                st.success(f"'{cat_name}' 업종 맞춤 템플릿을 불러왔습니다!")
                st.rerun()

    st.markdown("---")

    col_edit, col_preview = st.columns([1.1, 0.9])

    with col_edit:
        st.markdown("#### 2. 우리 가게 기본 정보 입력")
        s = st.session_state.draft_settings

        c1, c2 = st.columns(2)
        with c1:
            shop_name = st.text_input("상호명 / 가게명", value=s.get("shop_name", "수북오리 팔공점"))
            phone = st.text_input("매장 대표 전화번호", value=s.get("phone", "053-982-1234"))
            address = st.text_input("매장 주소 / 출동 구역", value=s.get("address", "대구 동구 중대동 380"))
        with c2:
            category = st.selectbox(
                "업종 분류",
                options=list(INDUSTRY_TEMPLATES.keys()) + ["기타"],
                index=list(INDUSTRY_TEMPLATES.keys()).index(s.get("category", "식당/맛집")) if s.get("category") in INDUSTRY_TEMPLATES else 0,
            )
            place_url = st.text_input("네이버 플레이스 / 예약 링크", value=s.get("place_url", "https://naver.me/sample"))
            business_hours = st.text_input("영업시간 / 휴무일", value=s.get("business_hours", "매일 11:30 ~ 21:30"))

        extra_info = st.text_input("주차장 / 특장점 / 계좌번호 안내", value=s.get("extra_info", "전용 무료 주차 30대 완비"))

        st.markdown("#### 3. 상황별 맞춤 콜백 문구 편집")
        st.caption("문구 내 `{가게명}`, `{주소}`, `{영업시간}`, `{플레이스링크}` 등은 입력한 정보로 자동 치환됩니다.")

        msg_tab1, msg_tab2, msg_tab3 = st.tabs([
            "📞 정상 통화 종료 후",
            "🚫 부재중 전화 시",
            "🌙 영업 외/휴무 시간",
        ])

        with msg_tab1:
            enable_normal = st.toggle("정상 통화 후 자동 발송 켜기", value=bool(s.get("enable_normal", 1)), key="tog_norm")
            msg_normal = st.text_area(
                "정상 통화 후 발송 문구",
                value=s.get("msg_normal", ""),
                height=220,
                key="txt_norm",
            )
            b_norm = calculate_korean_bytes(render_message(msg_normal, {
                "가게명": shop_name, "주소": address, "영업시간": business_hours,
                "플레이스링크": place_url, "기타안내": extra_info, "전화번호": phone,
            }))
            st.info(f"📊 규격: **{b_norm['type']}** ({b_norm['bytes']} 바이트 / {b_norm['char_count']}자)")

        with msg_tab2:
            enable_missed = st.toggle("부재중 전화 시 자동 발송 켜기", value=bool(s.get("enable_missed", 1)), key="tog_miss")
            msg_missed = st.text_area(
                "부재중 전화 감지 시 발송 문구",
                value=s.get("msg_missed", ""),
                height=220,
                key="txt_miss",
            )
            b_miss = calculate_korean_bytes(render_message(msg_missed, {
                "가게명": shop_name, "주소": address, "영업시간": business_hours,
                "플레이스링크": place_url, "기타안내": extra_info, "전화번호": phone,
            }))
            st.info(f"📊 규격: **{b_miss['type']}** ({b_miss['bytes']} 바이트 / {b_miss['char_count']}자)")

        with msg_tab3:
            enable_holiday = st.toggle("영업 외 시간 통화 시 발송 켜기", value=bool(s.get("enable_holiday", 0)), key="tog_holi")
            msg_holiday = st.text_area(
                "영업 외/휴무 시간 발송 문구",
                value=s.get("msg_holiday", ""),
                height=220,
                key="txt_holi",
            )
            b_holi = calculate_korean_bytes(render_message(msg_holiday, {
                "가게명": shop_name, "주소": address, "영업시간": business_hours,
                "플레이스링크": place_url, "기타안내": extra_info, "전화번호": phone,
            }))
            st.info(f"📊 규격: **{b_holi['type']}** ({b_holi['bytes']} 바이트 / {b_holi['char_count']}자)")

        # 세션 반영
        s["shop_name"] = shop_name
        s["phone"] = phone
        s["address"] = address
        s["category"] = category
        s["place_url"] = place_url
        s["business_hours"] = business_hours
        s["extra_info"] = extra_info
        s["msg_normal"] = msg_normal
        s["msg_missed"] = msg_missed
        s["msg_holiday"] = msg_holiday
        s["enable_normal"] = int(enable_normal)
        s["enable_missed"] = int(enable_missed)
        s["enable_holiday"] = int(enable_holiday)

        if st.button("💾 설정 내용 저장하기", type="primary", use_container_width=True):
            update_settings(s)
            st.success("✅ 콜백 설정 및 맞춤 문구가 안전하게 저장되었습니다!")
            st.rerun()

    with col_preview:
        st.markdown("#### 📱 고객 스마트폰 수신 실시간 미리보기")
        st.caption("고객이 통화를 마쳤을 때 실제 문자함에 도착하는 화면입니다:")

        view_mode = st.radio(
            "미리보기 상황 선택",
            options=["정상 통화 후", "부재중 전화 시", "영업 외 시간"],
            horizontal=True,
        )

        active_tmpl = msg_normal if view_mode == "정상 통화 후" else (msg_missed if view_mode == "부재중 전화 시" else msg_holiday)
        preview_values = {
            "가게명": shop_name,
            "고객번호": "010-1234-5678",
            "주소": address,
            "전화번호": phone,
            "플레이스링크": place_url,
            "영업시간": business_hours,
            "기타안내": extra_info,
        }
        rendered_preview = render_message(active_tmpl, preview_values)
        p_bytes = calculate_korean_bytes(rendered_preview)

        # 스마트폰 프레임 렌더링
        now_time = datetime.now().strftime("%p %I:%M").replace("AM", "오전").replace("PM", "오후")
        st.markdown(f"""
        <div class="phone-container">
            <div class="phone-header">
                💬 {shop_name} ({phone})
            </div>
            <div class="sms-bubble">{rendered_preview}</div>
            <div class="sms-footer">
                <span>{p_bytes["type"]}</span>
                <span>{now_time} 수신됨</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.caption(f"💡 통신사 문자 용량: **{p_bytes['bytes']} / 2,000 바이트** (글자 수: {p_bytes['char_count']}자)")

# ==============================================================================
# TAB 2: 스마트 발송 규칙 & 안드로이드 연동
# ==============================================================================
with tabs[1]:
    st.markdown("#### ⚙️ 스팸 방지 및 발송 규칙 세팅")
    s = st.session_state.draft_settings

    rc1, rc2 = st.columns(2)
    with rc1:
        limit_per_day = st.toggle(
            "🛡️ 동일 번호 1일 1회 발송 제한 (강력 권장)",
            value=bool(s.get("limit_per_day", 1)),
            help="같은 손님과 하루에 여러 번 통화해도 문자는 하루에 딱 1번만 발송해 스팸 피로감을 차단합니다.",
        )
        delay_seconds = st.slider(
            "⏳ 통화 종료 후 발송 지연 시간 (초)",
            min_value=1,
            max_value=15,
            value=int(s.get("delay_seconds", 3)),
            help="통화 끊자마자 0.1초 만에 오면 기계 느낌이 나므로, 3~5초 뒤 자연스럽게 도착하도록 지연합니다.",
        )

    with rc2:
        blacklist_raw = st.text_area(
            "🚫 발송 제외 번호 (가족, 직원, 고정 거래처 등)",
            value=s.get("blacklist_numbers", ""),
            height=110,
            help="문자가 가면 안 되는 번호들을 쉼표(,)나 줄바꿈으로 등록하세요.",
        )

    s["limit_per_day"] = int(limit_per_day)
    s["delay_seconds"] = int(delay_seconds)
    s["blacklist_numbers"] = blacklist_raw

    if st.button("💾 발송 규칙 저장하기", key="btn_save_rules", type="primary"):
        update_settings(s)
        st.success("발송 규칙이 업데이트되었습니다!")
        st.rerun()

    st.markdown("---")
    st.markdown("#### 📱 안드로이드 스마트폰 1분 연동 가이드")
    st.info("사장님의 안드로이드 폰에서 통화 종료를 감지해 무료 문자를 자동으로 쏘는 2가지 방법입니다:")

    guide_col1, guide_col2 = st.columns(2)
    with guide_col1:
        st.markdown("##### 🥇 방법 A: 안드로이드 자동화 앱 1분 세팅 (추천)")
        st.write("""
        1. 구글 플레이스토어에서 무료 앱 **[MacroDroid]** 또는 **[Tasker]** 설치
        2. **트리거(조건)**: [통화] ➡️ [통화 종료됨] 선택
        3. **동작(실행)**: [SMS 발송] 선택 후 위 설정된 문구 붙여넣기 (또는 아래 설정 JSON 불러오기)
        4. 비용 0원으로 안드로이드 기본 무료문자 무제한 자동 발송 완성!
        """)

        # 설정 JSON 내보내기 버튼
        export_data = {
            "service": "SmartCallbackPro",
            "shop_name": s.get("shop_name"),
            "msg_normal": render_message(s.get("msg_normal", ""), s),
            "msg_missed": render_message(s.get("msg_missed", ""), s),
            "limit_per_day": bool(s.get("limit_per_day", 1)),
            "delay_sec": int(s.get("delay_seconds", 3)),
            "blacklist": [num.strip() for num in s.get("blacklist_numbers", "").split(",") if num.strip()],
        }
        json_str = json.dumps(export_data, ensure_ascii=False, indent=2)
        st.download_button(
            label="📥 안드로이드 연동 설정 파일 다운로드 (callback_config.json)",
            data=json_str,
            file_name="callback_config.json",
            mime="application/json",
            use_container_width=True,
        )

    with guide_col2:
        st.markdown("##### 🥈 방법 B: 안드로이드 Termux 파이썬 데몬 구동")
        st.write("""
        안드로이드 Termux 환경에서 백그라운드 리스너를 직접 돌리는 전문 개발/에이전트 방식입니다:
        ```bash
        # 1. Termux에서 데몬 실행
        python android_daemon.py --server --port 8080

        # 2. 통화 종료 웹훅 호출 시 즉시 룰 검증 및 무료 발송
        curl "http://localhost:8080/call_ended?number=01012345678&type=normal"
        ```
        """)

# ==============================================================================
# TAB 3: 통화 종료 시뮬레이터
# ==============================================================================
with tabs[2]:
    st.markdown("#### 🧪 방금 손님과 통화가 끝났을 때 가상 시뮬레이션")
    st.caption("안드로이드 기기가 통화 종료 이벤트를 감지했을 때 룰 검증과 문구 생성이 어떻게 이뤄지는지 실시간으로 테스트해 보세요.")

    sim_c1, sim_c2 = st.columns([1, 1.2])

    with sim_c1:
        sim_phone = st.text_input("테스트 전화번호 입력", value="010-1234-5678", key="sim_p")
        sim_type = st.selectbox(
            "통화 상황 선택",
            options=["normal", "missed", "holiday"],
            format_func=lambda x: "📞 정상 통화 종료" if x == "normal" else ("🚫 부재중 전화" if x == "missed" else "🌙 영업 외 시간 통화"),
            key="sim_t",
        )

        st.write("💡 **테스트 팁**:")
        st.caption("- 동일 번호로 2번 연속 누르면 '1일 1회 스팸 방지 규칙'으로 자동 차단되는지 확인 가능")
        st.caption("- 제외 번호 목록에 있는 번호를 넣으면 차단되는지 확인 가능")

        if st.button("📞 [가상 통화 종료 이벤트 발생!]", type="primary", use_container_width=True):
            with st.spinner("통화 종료 감지 ➡️ 발송 규칙 검증 ➡️ SMS 전송 파이프라인 가동 중..."):
                res = handle_call_ended_event(sim_phone, sim_type, simulate_delay=False)
                st.session_state["last_sim_result"] = res

    with sim_c2:
        st.markdown("##### 📋 실시간 실행 결과 로그")
        if "last_sim_result" in st.session_state:
            res = st.session_state["last_sim_result"]
            if res["success"]:
                st.success(f"✅ **발송 성공**: {res['reason']}")
                st.markdown(f"**실제 발송된 문구 내용:**")
                st.code(res["message"], language="text")
                if "bytes" in res and res["bytes"]:
                    st.caption(f"규격: {res['bytes']['type']} | 용량: {res['bytes']['bytes']} 바이트 ({res['bytes']['char_count']}자)")
            else:
                st.error(f"🚫 **발송 차단됨**: {res['reason']}")
                st.warning("스팸 방지 또는 제외 번호 규칙에 따라 손님 폰으로 문자가 나가지 않았습니다.")
        else:
            st.info("왼쪽에서 [가상 통화 종료 이벤트 발생!] 버튼을 누르면 실시간 처리 결과가 나타납니다.")

# ==============================================================================
# TAB 4: 발송 이력 & 통계
# ==============================================================================
with tabs[3]:
    st.markdown("#### 📊 콜백 문자 발송 이력 관리")

    sc1, sc2 = st.columns([2, 1])
    with sc1:
        search_kw = st.text_input("🔍 전화번호 또는 내용 검색", placeholder="010-1234 또는 수북오리...")
    with sc2:
        limit_cnt = st.selectbox("조회 건수", [20, 50, 100, 200], index=1)

    logs = get_logs(limit=limit_cnt, search=search_kw)

    if logs:
        df = pd.DataFrame(logs)
        df_display = df[["id", "created_at", "phone_number", "call_type", "status", "note", "message"]].copy()
        df_display.columns = ["번호", "발송일시", "수신자번호", "통화유형", "상태", "처리결과", "전송문구"]

        st.dataframe(df_display, use_container_width=True, height=350)

        # 엑셀/CSV 다운로드
        csv_data = df_display.to_csv(index=False).encode("utf-8-sig")
        c_down1, c_down2 = st.columns([1, 1])
        with c_down1:
            st.download_button(
                label="📥 발송 이력 CSV 다운로드",
                data=csv_data,
                file_name=f"스마트콜백_발송이력_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with c_down2:
            if st.button("🗑️ 전체 이력 초기화", use_container_width=True):
                clear_logs()
                st.success("발송 이력이 초기화되었습니다.")
                st.rerun()
    else:
        st.info("조회된 발송 이력이 없습니다.")
