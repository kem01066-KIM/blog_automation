import streamlit as st
import os
import sys
import re
import urllib.parse
import requests
from bs4 import BeautifulSoup

# =============================================================
# 0. Core Business Logic (All-in-One 무결점 엔진)
# =============================================================

def clean_url(url):
    """
    URL 공백 제거 및 스키마(https://) 자동 보정
    """
    if not url:
        return ""
    clean = str(url).strip()
    if not clean:
        return ""
    if not clean.startswith(('http://', 'https://')):
        clean = 'https://' + clean
    return clean

def clean_product_title(raw_title):
    """
    쇼핑몰 메타태그에서 붙는 불필요한 홍보 문구/접미사 제거
    예: '샤오미 핸디 청소기 : 네이버 쇼핑' -> '샤오미 핸디 청소기'
    """
    if not raw_title:
        return ""
    title = str(raw_title).strip()
    
    patterns = [
        r'\s*[:\|\-]\s*(네이버\s*쇼핑|스마트스토어|쿠팡!*|11번가|G마켓|옥션|오늘의집|아이디어스|티몬|위메프).*$',
        r'\[.*?무료배송.*?\]',
        r'\[.*?당일발송.*?\]',
        r'\(.*?특가.*?결제\)',
        r'★.*?★',
    ]
    for p in patterns:
        title = re.sub(p, '', title, flags=re.IGNORECASE)
        
    return title.strip()

def safe_extract_meta(url):
    """
    제휴 링크 또는 상품 링크에서 안전하게 메타 정보를 추출합니다.
    어떤 비정상 URL이나 403 차단이 발생해도 절대 멈추지 않고 안전한 딕셔너리를 반환합니다.
    """
    clean = clean_url(url)
    if not clean:
        return {
            "ok": False,
            "status": "empty",
            "message": "링크가 입력되지 않았습니다.",
            "url": "",
            "platform": "etc",
            "title": "",
            "desc": "",
            "image": ""
        }

    is_coupang = "coupang.com" in clean or "coupa.ng" in clean
    is_naver = "naver.com" in clean or "smartstore" in clean
    platform = "coupang" if is_coupang else ("naver" if is_naver else "etc")

    result = {
        "ok": True,
        "status": "success",
        "message": "메타 추출 완료",
        "url": clean,
        "platform": platform,
        "title": "",
        "desc": "",
        "image": ""
    }

    if is_coupang:
        result["message"] = "쿠팡 파트너스 링크가 감지되었습니다. (보안 정책상 상품명을 아래에 직접 확인·입력해 주세요)"

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        res = requests.get(clean, headers=headers, timeout=4, allow_redirects=True)
        
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            
            og_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "title"})
            og_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
            og_image = soup.find("meta", property="og:image")

            raw_title = ""
            if og_title and og_title.get("content"):
                raw_title = og_title.get("content").strip()
            elif soup.title and soup.title.string:
                raw_title = soup.title.string.strip()

            if raw_title:
                result["title"] = clean_product_title(raw_title)

            if og_desc and og_desc.get("content"):
                result["desc"] = og_desc.get("content").strip()

            if og_image and og_image.get("content"):
                img_url = og_image.get("content").strip()
                if img_url.startswith("//"):
                    img_url = "https:" + img_url
                result["image"] = img_url
                
            if result["title"]:
                result["message"] = f"'{result['title'][:25]}...' 상품 정보 자동 인식 성공!"
        else:
            if not is_coupang:
                result["message"] = f"링크 접속 응답({res.status_code}): 상품명을 직접 입력해 주세요."
    except Exception:
        result["message"] = "링크 직접 조회 제한: 상품명과 특징을 직접 입력해 주세요."

    return result

def get_ftc_notice(platform_type="coupang"):
    """
    공정거래위원회 표시광고 심사지침 필수 경제적 이해관계 고지 문구
    """
    if platform_type == "coupang":
        return "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."
    elif platform_type == "naver":
        return "네이버 브랜드 커넥트 및 제휴 링크를 통해 일정액의 수수료를 제공받을 수 있습니다."
    else:
        return "본 게시글은 제휴마케팅 링크를 포함하고 있으며, 구매 시 소정의 수수료를 지급받을 수 있습니다."

def generate_threads_posts(product_name, key_points, affiliate_link, platform_type="coupang"):
    """
    스레드 알고리즘 도달률 최적화 썰 글 4종과 첫 댓글을 생성합니다.
    """
    p_name = product_name.strip() if product_name else "이 상품"
    points = key_points.strip() if key_points else "가성비 좋고 삶의 질이 확 올라감"
    link = clean_url(affiliate_link) if affiliate_link else "[첫 댓글에 남겨둘 링크]"
    ftc = get_ftc_notice(platform_type)

    # 1. [A타입] 내돈내산 찐후기형 (진정성 & 바이럴 의심 파훼)
    post_a_body = f"""솔직히 바이럴인 줄 알고 3주 동안 장바구니에만 담아뒀었거든요?

근데 왜 이제 샀나 싶을 정도로 삶의 질이 확 달라졌습니다.
{p_name} 쓴 지 벌써 한 달 넘었는데 솔직한 후기 남겨봐요.

처음엔 긴가민가했는데,
직접 써보니까 {points}.
진짜 기대 이상으로 만족도가 높아서 주변 지인들한테도 계속 영업 중입니다.

딱 하나 아쉬운 점 꼽자면 인기 많아서 가끔 품절되거나 배송 밀리는 거? 그거 말고는 단점을 못 찾겠네요.

혹시 고민 중이신 분들은 후기 꼼꼼히 비교해보고 고르세요!
자세한 정보랑 제가 샀던 최저가 링크는 첫 댓글에 남겨둘게요 👇"""

    post_a_comment = f"""📌 {p_name} 최저가 구매 링크
{link}

* {ftc}"""

    # 2. [B타입] 호구방지 비교분석형 (합리적 소비 자극)
    post_b_body = f"""다들 이거 살 때 비싼 대기업 유명 브랜드 거 사던데...
솔직히 말해서 돈 낭비라고 봅니다.

제가 성격상 브랜드별로 스펙이랑 실구매 리뷰 싹 다 뜯어보고 비교해봤거든요?
핵심 기능은 거의 똑같은데 가격 차이는 2~3배 나더라고요.

결국 제가 고른 건 {p_name}인데,
결론부터 말씀드리면 완전 대성공입니다.

실제로 써보면 {points}.
비싼 돈 주고 거품 낀 브랜드 이름값 낼 필요가 전혀 없어요.
딱 필요한 실속만 챙기실 분들에게 진심으로 추천합니다.

구매 링크랑 할인 정보는 첫 번째 댓글에 고정해 둘게요 👇"""

    post_b_comment = f"""📌 가성비 종결 {p_name} 링크
{link}

* {ftc}"""

    # 3. [C타입] 일상공감 스트레스해소형 (감정 공감 & 삶의 질)
    post_c_body = f"""퇴근하고 집에 오면 손 하나 까딱하기 싫은 날 있잖아요.

맨날 귀찮고 스트레스받던 일이었는데,
이거 하나 들이고 나서 퇴근 후 일상이 180도 바뀌었습니다.

{p_name} 이거 진짜 물건이네요.
직접 써보고 느낀 제일 큰 장점은 {points}.

별거 아닌 것 같아도 매일 쓰는 생활템 하나만 제대로 바꿔도 하루 피로도가 확 줄어드는 게 느껴집니다.

저처럼 일상 스트레스 줄이고 삶의 질 올리고 싶으신 분들은 꼭 한번 체크해보세요.
제가 주문했던 곳 링크는 댓글에 남겨둘게요 👇"""

    post_c_comment = f"""📌 삶의 질 수직상승템 {p_name}
{link}

* {ftc}"""

    # 4. [D타입] 단점부터 까는 솔직리뷰형 (신뢰도 200% 극대화)
    post_d_body = f"""광고 다 거르고 {p_name} 딱 2주 써본 솔직 단점부터 깝니다.

단점: 디자인이나 포장이 엄청 고급스럽진 않음. 딱 실용성 위주.
그리고 처음에 사용법 익히는 데 하루 정도 걸렸음.

근데 이 단점 다 씹어먹는 치명적인 장점이 뭐냐면...
{points}.

솔직히 이 가격에 이 정도 퍼포먼스면 단점 투덜댈 시간도 아깝습니다.
가격 오르거나 품절되기 전에 미리 쟁여두는 거 추천해요.

최저가 링크는 첫 댓글에 고정해 뒀습니다 👇"""

    post_d_comment = f"""📌 솔직후기 {p_name} 최저가 확인
{link}

* {ftc}"""

    full_a = f"{post_a_body}\n\n👉 링크: {link}\n\n* {ftc}"
    full_b = f"{post_b_body}\n\n👉 링크: {link}\n\n* {ftc}"
    full_c = f"{post_c_body}\n\n👉 링크: {link}\n\n* {ftc}"
    full_d = f"{post_d_body}\n\n👉 링크: {link}\n\n* {ftc}"

    return {
        "type_a": {
            "title": "🔥 A타입: 내돈내산 찐후기 썰",
            "subtitle": "바이럴 의심을 깨고 실사용 한 달 만족감을 전달하는 정석 썰",
            "body": post_a_body,
            "comment": post_a_comment,
            "full": full_a
        },
        "type_b": {
            "title": "💡 B타입: 호구방지 비교분석 썰",
            "subtitle": "대기업 브랜드 거품을 팩트로 짚고 가성비 실속을 자극하는 썰",
            "body": post_b_body,
            "comment": post_b_comment,
            "full": full_b
        },
        "type_c": {
            "title": "☕ C타입: 일상공감 삶의질 썰",
            "subtitle": "퇴근길 피로와 귀찮음을 한 방에 날려주는 공감대 형성 썰",
            "body": post_c_body,
            "comment": post_c_comment,
            "full": full_c
        },
        "type_d": {
            "title": "🎯 D타입: 단점부터 까는 솔직 썰",
            "subtitle": "사소한 단점을 먼저 짚어 신뢰도를 200% 올려 구매 전환시키는 썰",
            "body": post_d_body,
            "comment": post_d_comment,
            "full": full_d
        }
    }

def generate_reply_templates(product_name, affiliate_link, platform_type="coupang"):
    """
    독자들이 스레드 댓글을 달았을 때 알고리즘 점수(체류 시간 및 인터랙션)를 극대화하는
    상황별 5대 실전 답글(대댓글) 템플릿 세트
    """
    p_name = product_name.strip() if product_name else "이 제품"
    link = clean_url(affiliate_link) if affiliate_link else "[첫 댓글 링크 확인]"

    replies = [
        {
            "category": "🔗 링크 문의 댓글",
            "trigger": "어디서 사요? / 링크 안 보여요 / 정보 좀요!",
            "reply": f"첫 댓글 상단에 {p_name} 최저가 링크 고정해 뒀어요! 혹시 안 보이시면 여기 링크 참고해보세요 👉 {link}"
        },
        {
            "category": "💰 가격 / 가성비 문의 댓글",
            "trigger": "얼마예요? / 살만한 가격인가요?",
            "reply": f"제가 살 때는 쿠폰 먹여서 되게 착하게 샀어요! 날짜마다 할인율이 조금씩 달라서 첫 댓글 링크 들어가셔서 실시간 쿠폰 꼭 확인해보세요 ㅎㅎ"
        },
        {
            "category": "🛡️ 찐후기 / 의심 댓글",
            "trigger": "진짜 좋아요? / 광고 아니죠?",
            "reply": f"저도 바이럴에 워낙 많이 데여서 3주 동안 고민하다 산 내돈내산이에요 ㅋㅋ 써보고 별로였으면 스레드에 욕 박았을 텐데 진짜 만족해서 올렸습니다!"
        },
        {
            "category": "⚠️ 단점 / 호환성 문의 댓글",
            "trigger": "소음이나 단점은 없나요? / 쓰기 불편하지 않나요?",
            "reply": f"솔직히 완벽한 물건은 아니라서 사소한 아쉬움은 있는데, 핵심 기능 하나만으로도 본전은 충분히 뽑더라고요. 자세한 스펙은 첫 댓글 링크 리뷰란 꼭 확인해 보세요!"
        },
        {
            "category": "🎁 선물 / 추천 문의 댓글",
            "trigger": "부모님(또는 친구) 선물로 사드려도 괜찮을까요?",
            "reply": f"완전 추천해요! 실용적이라 받는 사람도 호불호 없이 진짜 좋아할 아이템입니다. 패키징도 깔끔하게 와서 선물용으로 손색없어요 ㅎㅎ"
        }
    ]
    return replies


# =============================================================
# 1. Streamlit Config & Page Styling
# =============================================================
st.set_page_config(
    page_title="스레드 제휴마케팅 썰 글 & 댓글 생성기 Pro",
    page_icon="🧵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

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


# =============================================================
# 2. Session State 초기화 (Single Source of Truth)
# =============================================================
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


# =============================================================
# 3. Callbacks (위젯 렌더링 전 사전 처리로 에러 원천 차단)
# =============================================================
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


# =============================================================
# 4. Header Section
# =============================================================
st.markdown('<div class="badge-tag">THREADS AUTO MARKETING PRO</div>', unsafe_allow_html=True)
st.markdown('<div class="main-title">🧵 스레드 제휴마케팅 썰 글 & 댓글/답글 생성기</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">제휴 링크와 키워드만 넣으면, <b>1) 스레드 도달률 5배 썰 글 4종</b>, <b>2) 공정위 첫 댓글</b>, <b>3) 독자 댓글용 자동 답글 5종</b>까지 한 방에 뽑아드립니다.</div>', unsafe_allow_html=True)

st.divider()


# =============================================================
# 5. Preset Buttons (1초 빠른 테스트)
# =============================================================
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


# =============================================================
# 6. Inputs Section
# =============================================================
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

curr_url = st.session_state["url_input"]
curr_name = st.session_state["name_input"]
curr_plat = st.session_state["plat_input"]
curr_points = st.session_state["points_input"]

plat_code = "coupang" if curr_plat == "쿠팡 파트너스" else ("naver" if "네이버" in curr_plat else "etc")

st.write("")
generate_btn = st.button("🚀 스레드 썰 글 4종 + 댓글/답글 일괄 생성하기", type="primary", use_container_width=True)


# =============================================================
# 7. Output Section
# =============================================================
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

st.divider()
st.caption("Threads Affiliate Marketing Pro v2.0 · 무결점 실전 배포 엔진")
