import streamlit as st
import pandas as pd
import json
import io
from datetime import datetime
import database as db

# Page Configuration (Mobile & Desktop Responsive)
st.set_page_config(
    page_title="애터미 하부회원 CRM Pro",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;600;700;800&display=swap');
    html, body, [class*="css"] {
        font-family: 'Pretendard', -apple-system, sans-serif;
    }
    .main-header {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 50%, #0284C7 100%);
        padding: 18px 20px;
        border-radius: 14px;
        color: white;
        margin-bottom: 20px;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }
    .metric-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 12px 14px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .member-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 14px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.04);
        transition: all 0.2s ease;
    }
    .member-card:hover {
        border-color: #2563EB;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.08);
    }
    .badge-left {
        background-color: #EFF6FF;
        color: #1D4ED8;
        border: 1px solid #BFDBFE;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 700;
    }
    .badge-right {
        background-color: #ECFDF5;
        color: #047857;
        border: 1px solid #A7F3D0;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 700;
    }
    .badge-root {
        background-color: #F5F3FF;
        color: #6D28D9;
        border: 1px solid #DDD6FE;
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 700;
    }
    .status-badge {
        padding: 3px 8px;
        border-radius: 6px;
        font-size: 12px;
        font-weight: 600;
    }
    .status-partner { background: #FEF3C7; color: #B45309; }
    .status-lead { background: #FEE2E2; color: #B91C1C; }
    .status-repurchase { background: #E0E7FF; color: #4338CA; }
    .status-new { background: #E0F2FE; color: #0369A1; }
    .status-buyer { background: #F1F5F9; color: #475569; }
</style>
""", unsafe_allow_html=True)

# Initialize DB
db.init_db()

# Top Header
st.markdown("""
<div class="main-header">
    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:10px;">
        <div>
            <h2 style="margin:0; font-size:24px; font-weight:800; color:white;">💼 애터미 하부회원 CRM Pro</h2>
            <p style="margin:4px 0 0 0; font-size:13px; opacity:0.9;">좌·우 계보도 시각화 · 특이사항 메모 · 반응자·구매자 맞춤 문자 1초 추출</p>
        </div>
        <div style="background:rgba(255,255,255,0.18); padding:6px 12px; border-radius:8px; font-size:12px; font-weight:600;">
            📱 폰 무료문자 앱 연동 지원
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Fetch all members
df_members = db.get_all_members()

# Global Metrics Bar
m_total = len(df_members)
m_left = len(df_members[df_members["line"] == "좌측"])
m_right = len(df_members[df_members["line"] == "우측"])
m_care = len(df_members[df_members["status"].isin(["반응·관심자", "재구매도래", "신규가입"])])

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(f"""<div class="metric-card"><div style="font-size:11px; color:#64748B; font-weight:600;">전체 관리 회원</div><div style="font-size:22px; font-weight:800; color:#1E293B;">{m_total}명</div></div>""", unsafe_allow_html=True)
with c2:
    st.markdown(f"""<div class="metric-card"><div style="font-size:11px; color:#2563EB; font-weight:600;">좌측 라인</div><div style="font-size:22px; font-weight:800; color:#2563EB;">{m_left}명</div></div>""", unsafe_allow_html=True)
with c3:
    st.markdown(f"""<div class="metric-card"><div style="font-size:11px; color:#059669; font-weight:600;">우측 라인</div><div style="font-size:22px; font-weight:800; color:#059669;">{m_right}명</div></div>""", unsafe_allow_html=True)
with c4:
    st.markdown(f"""<div class="metric-card"><div style="font-size:11px; color:#DC2626; font-weight:600;">집중 케어 대상</div><div style="font-size:22px; font-weight:800; color:#DC2626;">{m_care}명</div></div>""", unsafe_allow_html=True)

st.write("")

# Navigation Tabs
tab_list = ["📋 회원 관리 & 스마트 필터", "🌳 계보도 조직도 맵", "💬 맞춤 문자 생성기 (폰 무료문자)", "➕ 신규 등록 & 엑셀 연동"]
active_tab = st.radio("메뉴 선택", tab_list, horizontal=True, label_visibility="collapsed")

# -------------------------------------------------------------
# TAB 1: 회원 관리 & 스마트 필터
# -------------------------------------------------------------
if active_tab == tab_list[0]:
    st.subheader("📋 회원 목록 및 특이사항 CRM")
    
    # Filter Row
    fc1, fc2, fc3 = st.columns([1.5, 1, 1.5])
    with fc1:
        status_options = ["전체 상태", "반응·관심자", "재구매도래", "신규가입", "최근구매자", "핵심파트너"]
        selected_status = st.selectbox("회원 상태 필터", status_options, index=0)
    with fc2:
        line_options = ["전체 라인", "좌측", "우측"]
        selected_line = st.selectbox("라인 필터", line_options, index=0)
    with fc3:
        search_query = st.text_input("🔍 이름·번호·제품 검색", placeholder="예: 김선옥, 헤모힘, 5678")

    # Filter Dataframe
    filtered_df = df_members.copy()
    if selected_status != "전체 상태":
        filtered_df = filtered_df[filtered_df["status"] == selected_status]
    if selected_line != "전체 라인":
        filtered_df = filtered_df[filtered_df["line"] == selected_line]
    if search_query:
        q = search_query.strip().lower()
        filtered_df = filtered_df[
            filtered_df["name"].str.lower().str.contains(q, na=False) |
            filtered_df["phone"].str.contains(q, na=False) |
            filtered_df["member_id"].str.contains(q, na=False) |
            filtered_df["interested_products"].str.lower().str.contains(q, na=False) |
            filtered_df["notes"].str.lower().str.contains(q, na=False)
        ]

    st.caption(f"조회 결과: 총 **{len(filtered_df)}명**")
    
    view_mode = st.radio("보기 방식", ["카드 뷰 (상세/메모)", "테이블 뷰 (한눈에 보기)"], horizontal=True, label_visibility="collapsed")
    
    if view_mode == "카드 뷰 (상세/메모)":
        if len(filtered_df) == 0:
            st.info("조건에 맞는 회원이 없습니다.")
        else:
            for _, row in filtered_df.iterrows():
                mid = row["member_id"]
                name = row["name"]
                phone = row["phone"]
                line = row["line"]
                status = row["status"]
                join_date = row["join_date"]
                sponsor = row["sponsor_id"]
                products = row["interested_products"]
                order = row["recent_order"]
                notes = row["notes"]
                
                # Parse message history
                try:
                    history = json.loads(row["message_history"]) if row["message_history"] else []
                except Exception:
                    history = []
                
                # Line Badge Class
                line_cls = "badge-root" if line == "본인" else ("badge-left" if line == "좌측" else "badge-right")
                
                # Status Badge Class
                if status == "핵심파트너":
                    stat_cls = "status-badge status-partner"
                elif status == "반응·관심자":
                    stat_cls = "status-badge status-lead"
                elif status == "재구매도래":
                    stat_cls = "status-badge status-repurchase"
                elif status == "신규가입":
                    stat_cls = "status-badge status-new"
                else:
                    stat_cls = "status-badge status-buyer"

                with st.container():
                    st.markdown(f"""
                    <div class="member-card">
                        <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; margin-bottom:8px;">
                            <div>
                                <span style="font-size:18px; font-weight:800; color:#1E293B; margin-right:8px;">{name}</span>
                                <span style="font-size:12px; color:#64748B;">({mid})</span>
                                <span class="{line_cls}" style="margin-left:6px;">{line}</span>
                                <span class="{stat_cls}" style="margin-left:4px;">{status}</span>
                            </div>
                            <div style="font-size:13px; font-weight:700; color:#2563EB;">
                                📞 <a href="tel:{phone}" style="text-decoration:none; color:#2563EB;">{phone}</a>
                                <span style="margin-left:8px; color:#94A3B8;">|</span>
                                <span style="font-size:12px; color:#64748B; margin-left:8px;">가입일: {join_date}</span>
                            </div>
                        </div>
                        <div style="background:#F8FAFC; padding:10px 12px; border-radius:8px; font-size:13px; margin-bottom:8px;">
                            <div style="margin-bottom:4px;"><strong>🛒 관심 제품:</strong> <span style="color:#0284C7;">{products if products else '미등록'}</span></div>
                            <div style="margin-bottom:4px;"><strong>📦 최근 주문:</strong> {order if order else '내역 없음'}</div>
                            <div><strong>📝 특이사항/메모:</strong> <span style="color:#B45309; font-weight:600;">{notes if notes else '기록된 메모 없음'}</span></div>
                        </div>
                        <div style="display:flex; justify-content:space-between; align-items:center; font-size:12px; color:#64748B;">
                            <div>후원인: {sponsor if sponsor else '최상위(본인)'} &nbsp;|&nbsp; 문자 발송 이력: <strong>{len(history)}건</strong></div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Edit / Action Expander
                    with st.expander(f"✏️ {name} 사장님 메모 수정 & 발송 이력 보기"):
                        e1, e2 = st.columns([1.2, 1])
                        with e1:
                            st.markdown("**특이사항 / 상담 메모 업데이트**")
                            new_notes = st.text_area("특이사항 메모", value=notes, key=f"notes_{mid}", height=90)
                            new_status = st.selectbox("회원 상태 변경", ["반응·관심자", "재구매도래", "신규가입", "최근구매자", "핵심파트너", "단순소비자"], index=["반응·관심자", "재구매도래", "신규가입", "최근구매자", "핵심파트너", "단순소비자"].index(status) if status in ["반응·관심자", "재구매도래", "신규가입", "최근구매자", "핵심파트너", "단순소비자"] else 0, key=f"stat_{mid}")
                            new_products = st.text_input("관심 제품", value=products, key=f"prod_{mid}")
                            new_order = st.text_input("최근 주문", value=order, key=f"ord_{mid}")
                            
                            if st.button("💾 메모 및 상태 저장", key=f"save_{mid}"):
                                update_data = {
                                    "name": name,
                                    "phone": phone,
                                    "join_date": join_date,
                                    "sponsor_id": sponsor,
                                    "line": line,
                                    "status": new_status,
                                    "interested_products": new_products,
                                    "recent_order": new_order,
                                    "notes": new_notes
                                }
                                db.update_member(mid, update_data)
                                st.success(f"{name} 님의 메모와 상태가 성공적으로 저장되었습니다!")
                                st.rerun()
                                
                        with e2:
                            st.markdown("**최근 문자 발송 이력**")
                            if len(history) == 0:
                                st.caption("발송된 문자 이력이 없습니다.")
                            else:
                                for h in reversed(history[-5:]):
                                    st.markdown(f"""
                                    <div style="background:#FFFFFF; border:1px solid #E2E8F0; padding:8px; border-radius:6px; margin-bottom:6px; font-size:12px;">
                                        <div style="font-weight:700; color:#2563EB;">[{h.get('template', '일반')}] <span style="font-weight:400; color:#64748B;">{h.get('date', '')}</span></div>
                                        <div style="margin-top:4px; color:#334155;">{h.get('content', '')}</div>
                                    </div>
                                    """, unsafe_allow_html=True)
                            
                            st.write("")
                            if st.button(f"🗑️ {name} 회원 삭제", key=f"del_{mid}", help="이 회원을 DB에서 삭제합니다."):
                                db.delete_member(mid)
                                st.warning(f"{name} 회원이 삭제되었습니다.")
                                st.rerun()

    else:
        # Table View
        display_df = filtered_df[["member_id", "name", "phone", "line", "status", "interested_products", "notes", "recent_order", "join_date"]].copy()
        display_df.columns = ["회원번호", "성명", "전화번호", "라인", "상태", "관심제품", "특이사항 메모", "최근주문", "가입일"]
        st.dataframe(display_df, use_container_width=True, hide_index=True)


# -------------------------------------------------------------
# TAB 2: 계보도 조직도 맵
# -------------------------------------------------------------
elif active_tab == tab_list[1]:
    st.subheader("🌳 애터미 좌·우 바이너리 계보도 맵")
    st.caption("스폰서와 파트너 간의 좌·우 라인 구조를 한눈에 파악하고 회원을 클릭하여 상세 정보를 확인하세요.")
    
    # Visual Tree Rendering
    root_members = df_members[df_members["sponsor_id"] == ""]
    if len(root_members) == 0:
        root_members = df_members.head(1)
    
    root = root_members.iloc[0]
    
    left_line_members = df_members[df_members["line"] == "좌측"]
    right_line_members = df_members[df_members["line"] == "우측"]
    
    # Interactive Tree Diagram (HTML/CSS)
    tree_html = f"""
    <div style="background:#F8FAFC; border:1px solid #E2E8F0; border-radius:14px; padding:20px; text-align:center; overflow-x:auto;">
        <!-- ROOT NODE -->
        <div style="display:inline-block; background:#FFFFFF; border:2px solid #7C3AED; border-radius:12px; padding:12px 20px; box-shadow:0 4px 10px rgba(124,58,237,0.15); min-width:200px;">
            <div style="font-size:11px; color:#7C3AED; font-weight:800; letter-spacing:1px;">★ 팀 리더 (본인)</div>
            <div style="font-size:18px; font-weight:800; color:#1E293B; margin:2px 0;">{root['name']} <span style="font-size:12px; color:#64748B;">({root['member_id']})</span></div>
            <div style="font-size:12px; color:#6D28D9; font-weight:600;">{root['status']}</div>
        </div>

        <!-- CONNECTOR LINE -->
        <div style="width:2px; height:24px; background:#CBD5E1; margin:0 auto;"></div>
        <div style="width:60%; height:2px; background:#CBD5E1; margin:0 auto;"></div>

        <!-- BRANCHES CONTAINER -->
        <div style="display:flex; justify-content:space-around; gap:20px; margin-top:0px;">
            <!-- LEFT LINE COLUMN -->
            <div style="flex:1; max-width:48%; text-align:center;">
                <div style="width:2px; height:20px; background:#2563EB; margin:0 auto;"></div>
                <div style="background:#EFF6FF; border:1.5px solid #93C5FD; border-radius:10px; padding:8px; margin-bottom:12px;">
                    <span style="font-size:14px; font-weight:800; color:#1D4ED8;">🔵 좌측 라인 ({len(left_line_members)}명)</span>
                </div>
    """
    
    for _, lm in left_line_members.iterrows():
        tree_html += f"""
                <div style="background:#FFFFFF; border:1.5px solid #BFDBFE; border-radius:10px; padding:10px; margin-bottom:10px; box-shadow:0 2px 5px rgba(37,99,235,0.06); text-align:left;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:15px; font-weight:800; color:#1E293B;">{lm['name']} <span style="font-size:11px; color:#64748B;">({lm['member_id']})</span></span>
                        <span style="font-size:11px; padding:2px 6px; border-radius:4px; font-weight:700; background:#DBEAFE; color:#1E40AF;">{lm['status']}</span>
                    </div>
                    <div style="font-size:12px; color:#2563EB; margin-top:4px;">📞 {lm['phone']}</div>
                    <div style="font-size:11px; color:#64748B; margin-top:2px;">관심: {lm['interested_products'][:25]}...</div>
                    <div style="font-size:11px; color:#B45309; margin-top:2px; background:#FEF3C7; padding:2px 6px; border-radius:4px;">메모: {lm['notes'][:30]}...</div>
                </div>
        """
        
    tree_html += f"""
            </div>

            <!-- RIGHT LINE COLUMN -->
            <div style="flex:1; max-width:48%; text-align:center;">
                <div style="width:2px; height:20px; background:#059669; margin:0 auto;"></div>
                <div style="background:#ECFDF5; border:1.5px solid #6EE7B7; border-radius:10px; padding:8px; margin-bottom:12px;">
                    <span style="font-size:14px; font-weight:800; color:#047857;">🟢 우측 라인 ({len(right_line_members)}명)</span>
                </div>
    """
    
    for _, rm in right_line_members.iterrows():
        tree_html += f"""
                <div style="background:#FFFFFF; border:1.5px solid #A7F3D0; border-radius:10px; padding:10px; margin-bottom:10px; box-shadow:0 2px 5px rgba(5,150,105,0.06); text-align:left;">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <span style="font-size:15px; font-weight:800; color:#1E293B;">{rm['name']} <span style="font-size:11px; color:#64748B;">({rm['member_id']})</span></span>
                        <span style="font-size:11px; padding:2px 6px; border-radius:4px; font-weight:700; background:#D1FAE5; color:#065F46;">{rm['status']}</span>
                    </div>
                    <div style="font-size:12px; color:#059669; margin-top:4px;">📞 {rm['phone']}</div>
                    <div style="font-size:11px; color:#64748B; margin-top:2px;">관심: {rm['interested_products'][:25]}...</div>
                    <div style="font-size:11px; color:#B45309; margin-top:2px; background:#FEF3C7; padding:2px 6px; border-radius:4px;">메모: {rm['notes'][:30]}...</div>
                </div>
        """

    tree_html += """
            </div>
        </div>
    </div>
    """
    
    st.components.v1.html(tree_html, height=620, scrolling=True)
    
    st.write("")
    st.markdown("#### 🔍 특정 회원 집중 탐색")
    selected_tree_member = st.selectbox("조직도에서 살펴볼 회원을 선택하세요", df_members["name"].tolist() + " (" + df_members["member_id"].astype(str) + ")")
    target_mid = selected_tree_member.split("(")[-1].replace(")", "").strip()
    target_row = df_members[df_members["member_id"] == target_mid].iloc[0]
    
    tc1, tc2 = st.columns(2)
    with tc1:
        st.info(f"**회원 정보**: {target_row['name']} ({target_row['member_id']}) | 라인: {target_row['line']} | 상태: {target_row['status']}\n\n"
                f"**연락처**: {target_row['phone']} | 가입일: {target_row['join_date']}\n\n"
                f"**후원인**: {target_row['sponsor_id'] if target_row['sponsor_id'] else '최상위'}")
    with tc2:
        st.warning(f"**관심 제품**: {target_row['interested_products']}\n\n"
                   f"**최근 주문**: {target_row['recent_order']}\n\n"
                   f"**특이사항 메모**: {target_row['notes']}")


# -------------------------------------------------------------
# TAB 3: 맞춤 문자 생성기 (폰 무료문자 연동)
# -------------------------------------------------------------
elif active_tab == tab_list[2]:
    st.subheader("💬 타겟 맞춤 문자 생성기 (폰 무료문자 연동)")
    st.caption("회원 상태별로 대상을 1초 만에 추려내고, 개인 이름이 자동으로 들어간 발송 파일(.xlsx)을 다운받아 폰 무료문자 앱에 넣으세요.")
    
    sc1, sc2 = st.columns([1, 1.2])
    
    with sc1:
        st.markdown("##### 1단계: 발송 대상 타겟 선택")
        target_mode = st.radio("대상 선택 방식", ["상태별 자동 선택", "개별 회원 직접 선택"], horizontal=True)
        
        target_members = []
        if target_mode == "상태별 자동 선택":
            target_status = st.selectbox("발송할 대상 그룹", ["반응·관심자", "재구매도래", "신규가입", "최근구매자", "핵심파트너", "전체 회원"])
            if target_status == "전체 회원":
                target_members = df_members
            else:
                target_members = df_members[df_members["status"] == target_status]
        else:
            selected_names = st.multiselect("발송할 회원을 직접 선택하세요", df_members["name"].tolist(), default=df_members["name"].tolist()[:3])
            target_members = df_members[df_members["name"].isin(selected_names)]
            
        st.success(f"🎯 선택된 발송 대상: **총 {len(target_members)}명**")
        
        # Display short list
        if len(target_members) > 0:
            target_preview_text = ", ".join([f"{r['name']}({r['phone']})" for _, r in target_members.head(6).iterrows()])
            if len(target_members) > 6:
                target_preview_text += f" 외 {len(target_members)-6}명"
            st.caption(f"수신 명단: {target_preview_text}")

    with sc2:
        st.markdown("##### 2단계: 메시지 템플릿 선택 & 작성")
        templates = {
            "반응·관심자 1:1 감사 & 후속 케어": "{이름} 사장님 안녕하세요! 지난번 문의주신 제품 정보 잘 살펴보셨나요? 평소 관심 있으셨던 제품에 꼭 맞는 실전 섭취·사용 팁을 정리해 두었으니, 편하신 시간에 문자나 전화 주시면 자세히 안내해 드릴게요. 늘 응원합니다! 😊",
            "재구매 시점 도래 안부 & 프로모션": "{이름} 사장님, 환절기에 건강히 잘 지내고 계시죠? 챙겨드시는 헤모힘과 영양제가 슬슬 소진되실 시점이라 안부 겸 연락드렸어요. 필요하시면 이번 주 추가 적립 혜택 챙겨서 도와드릴게요. 좋은 하루 보내세요!",
            "신규가입 웰컴 & 쇼핑몰 적립 안내": "{이름} 사장님, 애터미 가족이 되신 것을 진심으로 환영합니다! 🎉 회원번호({회원번호})로 애터미 앱에 로그인하시면 전 제품을 회원가와 포인트 혜택으로 바로 만나보실 수 있어요. 주문 중 궁금하신 점은 언제든 편하게 말씀해 주세요!",
            "신상품 출시 & 원데이 세미나 공지": "{이름} 사장님, 이번 주 애터미 신제품 소식과 알짜 세미나 일정 공유해 드려요! 바쁘시더라도 놓치면 아쉬운 혜택들이 많으니 꼭 살펴보시고, 필요한 자료 있으시면 언제든 편하게 톡 남겨주세요!",
            "직접 작성": "{이름} 사장님 안녕하세요! "
        }
        
        selected_tpl_key = st.selectbox("추천 템플릿 불러오기", list(templates.keys()), index=0)
        message_template = st.text_area("메시지 본문 ({이름}, {회원번호} 치환자 지원)", value=templates[selected_tpl_key], height=130)
        st.caption("💡 `{이름}`과 `{회원번호}`를 넣으면 회원마다 개인 정보로 자동 변경됩니다.")

    st.write("---")
    
    # Step 3: Live Preview & Export
    if len(target_members) > 0:
        st.markdown("##### 3단계: 개인별 실시간 미리보기 & 발송 파일 생성")
        
        # Live Preview Box
        first_row = target_members.iloc[0]
        preview_sample = message_template.replace("{이름}", first_row["name"]).replace("{회원번호}", first_row["member_id"])
        
        p1, p2 = st.columns([1.2, 1])
        with p1:
            st.markdown(f"**실제 발송 미리보기 예시 (수신자: {first_row['name']} 사장님 / {first_row['phone']})**")
            st.markdown(f"""
            <div style="background:#F1F5F9; border-left:4px solid #2563EB; padding:12px 16px; border-radius:6px; font-size:14px; line-height:1.6; color:#1E293B; white-space:pre-wrap;">{preview_sample}</div>
            """, unsafe_allow_html=True)
            
        with p2:
            st.markdown("**발송 파일 생성 및 액션**")
            
            # Prepare Export DataFrame
            export_rows = []
            for _, r in target_members.iterrows():
                final_msg = message_template.replace("{이름}", r["name"]).replace("{회원번호}", r["member_id"])
                export_rows.append({
                    "이름": r["name"],
                    "전화번호": r["phone"],
                    "회원번호": r["member_id"],
                    "발송메시지": final_msg
                })
            df_export = pd.DataFrame(export_rows)
            
            # Create Excel in Memory
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False, sheet_name="발송명단")
            excel_data = output.getvalue()
            
            st.download_button(
                label="📥 폰 무료문자 앱용 엑셀 다운로드 (.xlsx)",
                data=excel_data,
                file_name=f"애터미_맞춤문자_{selected_tpl_key[:8]}_{datetime.now().strftime('%m%d_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
            
            # Record to History Button
            if st.button("💾 선택된 회원들의 발송 이력에 자동 기록", use_container_width=True):
                for _, r in target_members.iterrows():
                    final_msg = message_template.replace("{이름}", r["name"]).replace("{회원번호}", r["member_id"])
                    db.append_message_history(r["member_id"], selected_tpl_key, final_msg)
                st.success(f"{len(target_members)}명의 회원 카드에 문자 발송 이력이 자동 기록되었습니다!")
                st.rerun()

        # Copyable Text Area
        st.write("")
        with st.expander("📋 화면에서 전체 발송 텍스트 한 번에 복사하기 (클립보드용)"):
            all_text = ""
            for item in export_rows:
                all_text += f"[{item['이름']} / {item['전화번호']}]\n{item['발송메시지']}\n--------------------\n"
            st.text_area("전체 명단 복사창", value=all_text, height=200)


# -------------------------------------------------------------
# TAB 4: 신규 등록 & 엑셀 연동
# -------------------------------------------------------------
elif active_tab == tab_list[3]:
    st.subheader("➕ 회원 신규 등록 및 엑셀 대량 관리")
    
    r1, r2 = st.columns([1.2, 1])
    
    with r1:
        st.markdown("##### 1명 신규 회원 개별 등록")
        with st.form("add_member_form", clear_on_submit=True):
            f_mid = st.text_input("회원번호 (필수)", placeholder="예: 10000010")
            f_name = st.text_input("이름 (필수)", placeholder="예: 홍길동")
            f_phone = st.text_input("전화번호 (필수)", placeholder="예: 010-1234-5678")
            f_date = st.date_input("가입일", value=datetime.now())
            f_sponsor = st.text_input("후원인 회원번호", placeholder="예: 10000001")
            f_line = st.selectbox("라인 구분", ["좌측", "우측", "본인"])
            f_status = st.selectbox("회원 상태", ["신규가입", "반응·관심자", "최근구매자", "재구매도래", "핵심파트너", "단순소비자"])
            f_prod = st.text_input("관심 제품", placeholder="예: 헤모힘, 앱솔루트 화장품")
            f_notes = st.text_area("특이사항 / 첫 상담 메모", placeholder="예: 무릎 관절염 고민, 가족과 함께 섭취 희망")
            
            submitted = st.form_submit_button("✅ 신규 회원 등록하기")
            if submitted:
                if not f_mid or not f_name or not f_phone:
                    st.error("회원번호, 이름, 전화번호는 필수 입력 항목입니다.")
                else:
                    new_data = {
                        "member_id": f_mid,
                        "name": f_name,
                        "phone": f_phone,
                        "join_date": f_date.strftime("%Y-%m-%d"),
                        "sponsor_id": f_sponsor,
                        "line": f_line,
                        "status": f_status,
                        "interested_products": f_prod,
                        "recent_order": "신규 등록",
                        "notes": f_notes,
                        "message_history": []
                    }
                    try:
                        db.add_member(new_data)
                        st.success(f"{f_name} 사장님이 성공적으로 등록되었습니다!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"등록 실패: 이미 등록된 회원번호이거나 오류가 발생했습니다. ({e})")

    with r2:
        st.markdown("##### 엑셀 대량 등록 및 백업")
        
        # Download Sample Template
        sample_df = pd.DataFrame([
            {
                "member_id": "10000099",
                "name": "홍길동",
                "phone": "010-9999-8888",
                "join_date": "2026-11-10",
                "sponsor_id": "10000001",
                "line": "좌측",
                "status": "신규가입",
                "interested_products": "헤모힘, 칫솔",
                "recent_order": "치약 1세트",
                "notes": "지인 소개 가입"
            }
        ])
        s_output = io.BytesIO()
        with pd.ExcelWriter(s_output, engine='openpyxl') as s_writer:
            sample_df.to_excel(s_writer, index=False, sheet_name="샘플양식")
        st.download_button(
            label="📄 엑셀 업로드용 양식 다운로드 (.xlsx)",
            data=s_output.getvalue(),
            file_name="애터미_회원등록_샘플양식.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        st.write("")
        st.markdown("**엑셀 파일 일괄 업로드**")
        uploaded_file = st.file_uploader("작성한 엑셀 파일 선택", type=["xlsx", "csv"])
        if uploaded_file is not None:
            try:
                if uploaded_file.name.endswith(".csv"):
                    up_df = pd.read_csv(uploaded_file)
                else:
                    up_df = pd.read_excel(uploaded_file)
                
                st.write(f"업로드된 데이터: 총 **{len(up_df)}건** 확인")
                if st.button("🚀 위 데이터 전체 DB에 저장하기"):
                    success_count = 0
                    for _, urow in up_df.iterrows():
                        u_data = {
                            "member_id": str(urow.get("member_id", "")),
                            "name": str(urow.get("name", "")),
                            "phone": str(urow.get("phone", "")),
                            "join_date": str(urow.get("join_date", datetime.now().strftime("%Y-%m-%d"))),
                            "sponsor_id": str(urow.get("sponsor_id", "")),
                            "line": str(urow.get("line", "좌측")),
                            "status": str(urow.get("status", "신규가입")),
                            "interested_products": str(urow.get("interested_products", "")),
                            "recent_order": str(urow.get("recent_order", "")),
                            "notes": str(urow.get("notes", "")),
                            "message_history": []
                        }
                        if u_data["member_id"] and u_data["name"] and u_data["phone"]:
                            try:
                                db.add_member(u_data)
                                success_count += 1
                            except Exception:
                                pass
                    st.success(f"{success_count}건의 회원이 DB에 성공적으로 등록되었습니다!")
                    st.rerun()
            except Exception as e:
                st.error(f"파일을 읽는 중 오류가 발생했습니다: {e}")

        st.write("---")
        st.markdown("**전체 데이터 백업 & 초기화**")
        # Full DB Export
        all_output = io.BytesIO()
        with pd.ExcelWriter(all_output, engine='openpyxl') as all_writer:
            df_members.to_excel(all_writer, index=False, sheet_name="전체회원")
        st.download_button(
            label="💾 전체 회원 DB 엑셀 백업 다운로드",
            data=all_output.getvalue(),
            file_name=f"애터미_전체회원_백업_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        
        st.write("")
        if st.button("🔄 샘플 데이터로 초기화", help="기존 데이터를 지우고 시연용 9명 샘플 데이터로 리셋합니다."):
            db.reset_to_sample()
            st.success("샘플 데이터로 성공적으로 초기화되었습니다!")
            st.rerun()
