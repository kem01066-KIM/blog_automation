import os
import io
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter
import imageio
from bs4 import BeautifulSoup

# ==========================================
# 0. 폰트 자동 탐색 (환경별 대응)
# ==========================================
def get_korean_font(size=20):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "fonts", "NanumGothic.ttf"),
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/pickle-hwp/NotoSansCJKkr-Regular.otf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/gulim.ttc",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/Library/Fonts/NanumGothic.ttf"
    ]
    for font_path in candidates:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                continue

    try:
        font_dir = os.path.join(base_dir, "fonts")
        os.makedirs(font_dir, exist_ok=True)
        local_font = os.path.join(font_dir, "NanumGothic.ttf")
        if not os.path.exists(local_font):
            urllib.request.urlretrieve(
                "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf",
                local_font
            )
        return ImageFont.truetype(local_font, size)
    except Exception:
        pass

    return ImageFont.load_default()


# ==========================================
# 1. 네이버 블로그 스크래핑 엔진
# ==========================================
def scrape_naver_blog(blog_url):
    """네이버 모바일/PC 블로그에서 제목, 본문 텍스트, 고화질 시공 이미지 URL을 추출합니다."""
    user_id, log_no = None, None
    m1 = re.search(r'blog\.naver\.com/([^/?&]+)/(\d+)', blog_url)
    m2 = re.search(r'blogId=([^&]+).*?logNo=(\d+)', blog_url)

    if m1:
        user_id, log_no = m1.group(1), m1.group(2)
    elif m2:
        user_id, log_no = m2.group(1), m2.group(2)

    if user_id and log_no:
        target_url = f"https://m.blog.naver.com/{user_id}/{log_no}"
    else:
        target_url = blog_url.strip()

    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15'
    }
    req = urllib.request.Request(target_url, headers=headers)
    
    with urllib.request.urlopen(req, timeout=12) as resp:
        html = resp.read().decode('utf-8', errors='ignore')

    title_match = re.search(r'<title>(.*?)</title>', html, re.DOTALL | re.IGNORECASE)
    raw_title = title_match.group(1).replace(" : 네이버 블로그", "").strip() if title_match else "현장 시공 기록"

    img_candidates = re.findall(
        r'https://postfiles\.pstatic\.net/[^\s\"\'\<\>]+|https://mblogthumb-phinf\.pstatic\.net/[^\s\"\'\<\>]+',
        html
    )

    clean_imgs = []
    seen = set()
    for img_url in img_candidates:
        base_url = img_url.split('?')[0].replace('&quot;', '').replace('&amp;', '&').rstrip(')\"\'')
        base_lower = base_url.lower()

        skip_patterns = ['/sticker/', '/profile/', 'emoticon', 'editor_profile', 'ico_', '.gif', 'line_sticker', 'blog_profile']
        if any(skip in base_lower for skip in skip_patterns):
            continue

        if base_url not in seen:
            seen.add(base_url)
            clean_imgs.append(f"{base_url}?type=w800")

    text_cleaned = re.sub(r'<script.*?</script>', '', html, flags=re.DOTALL)
    text_cleaned = re.sub(r'<style.*?</style>', '', text_cleaned, flags=re.DOTALL)
    text_cleaned = re.sub(r'<[^>]+>', ' ', text_cleaned)
    text_cleaned = re.sub(r'\s+', ' ', text_cleaned).strip()

    return {
        "title": raw_title,
        "images": clean_imgs,
        "text": text_cleaned[:3000]
    }


# ==========================================
# 2. 타겟 지역 실시간 네이버 SERP 검색·분석
# ==========================================
def search_naver_serp(region):
    """해당 지역의 상위노출 포스팅 제목과 연관 키워드를 실시간 검색·분석합니다."""
    query = f"{region}누수".replace(" ", "")
    url = f"https://search.naver.com/search.naver?where=blog&sm=tab_jum&query={urllib.parse.quote(query)}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
        'Accept-Language': 'ko-KR,ko;q=0.9'
    }
    top_titles = []
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as resp:
            html = resp.read().decode('utf-8', errors='ignore')
        soup = BeautifulSoup(html, 'html.parser')
        for a in soup.find_all('a'):
            href = a.get('href', '')
            if 'blog.naver.com/' in href and re.search(r'/\d{10,}', href):
                t = a.get_text(strip=True).replace('새 창 열림', '').strip()
                if len(t) > 10 and '누수' in t and t not in top_titles:
                    top_titles.append(t)
    except Exception:
        pass

    return {
        "query": query,
        "top_titles": top_titles[:5]
    }


# ==========================================
# 3. 바로누수 블로그 유사 이전 글 자동 매칭
# ==========================================
FALLBACK_BARO_POSTS = [
    {"title": "대구 서구 누수 이현동 다세대 원룸,욕실 세면대 밑 PB온수배관 꺾임 누수 해결", "url": "https://blog.naver.com/dnjswo3482/224468574834"},
    {"title": "대구 달서구 누수 상리동 필로티 빌라 주차장 천장 물샘 누수 체크 방법, PB 온수배관 교체 사례", "url": "https://blog.naver.com/dnjswo3482/224467767310"},
    {"title": "대구 동구 누수 지묘동 아파트 1층 누수, 지하로 떨어진 물의 원인 꺾어 묻은 PB배관 크랙 찾아 해결", "url": "https://blog.naver.com/dnjswo3482/224461926757"},
    {"title": "대구 북구 누수 산격동 공장, 계량기가 멈추지 않던 이유! T부속 크랙 찾아 해결", "url": "https://blog.naver.com/dnjswo3482/224456013558"},
    {"title": "대구서구누수 내당동 주택누수 해결했어요", "url": "https://blog.naver.com/dnjswo3482/224442880346"},
    {"title": "대구 북구 누수 노후 아파트의 고질병, 온수배관 결함 정밀 탐지로 완벽 해결 후기!", "url": "https://blog.naver.com/dnjswo3482/224338256916"},
    {"title": "대구 중구 누수 수도세 폭탄의 미스터리! 30년 노후 배관 완벽 해결 과정", "url": "https://blog.naver.com/dnjswo3482/224342898115"},
    {"title": "대구 동구 누수 율암동 바닥 매립 배관 손상, 원인부터 마감까지 한번에", "url": "https://blog.naver.com/dnjswo3482/224430154820"},
    {"title": "대구동구누수 신천동 빌라 배관 동파 보일러 PB온수배관 누수 전용 부속 사용으로 완벽하게 해결", "url": "https://blog.naver.com/dnjswo3482/224425890123"}
]

def get_related_posts(target_gu, target_dong, exclude_url=""):
    """타겟 지역(구/동)과 일치하거나 유사한 바로누수 블로그의 실제 이전 글 2건을 매칭합니다."""
    rss_url = "https://rss.blog.naver.com/dnjswo3482.xml"
    headers = {'User-Agent': 'Mozilla/5.0'}
    posts = []
    try:
        req = urllib.request.Request(rss_url, headers=headers)
        with urllib.request.urlopen(req, timeout=6) as resp:
            xml_data = resp.read()
        root = ET.fromstring(xml_data)
        for it in root.findall('.//item'):
            title = it.find('title').text if it.find('title') is not None else ''
            link = it.find('link').text if it.find('link') is not None else ''
            clean_link = link.split('?')[0]
            if clean_link == exclude_url:
                continue
            posts.append({"title": title, "url": clean_link})
    except Exception:
        posts = FALLBACK_BARO_POSTS

    if not posts:
        posts = FALLBACK_BARO_POSTS

    # 1순위: 같은 구 또는 같은 동
    same_gu = [p for p in posts if (target_gu and target_gu in p["title"]) or (target_dong and target_dong in p["title"])]
    # 2순위: 기타 대구 누수 글
    other_daegu = [p for p in posts if "대구" in p["title"] and p not in same_gu]

    candidates = same_gu + other_daegu
    return candidates[:2] if len(candidates) >= 2 else posts[:2]


def get_daegu_neighbors(gu, dong):
    """대구 지역구별 인근 주요 동 목록을 반환합니다."""
    neighbors_map = {
        '북구': ['침산동', '산격동', '복현동', '칠성동', '대현동', '태전동', '고성동'],
        '서구': ['평리동', '비산동', '내당동', '이현동', '중리동', '원대동'],
        '동구': ['신서동', '각산동', '율하동', '신천동', '지묘동', '방촌동', '효목동'],
        '달서구': ['상리동', '상인동', '월성동', '진천동', '송현동', '본리동', '감삼동'],
        '수성구': ['범어동', '만촌동', '황금동', '두산동', '지산동', '시지동'],
        '중구': ['동인동', '삼덕동', '남산동', '대봉동', '대신동'],
        '남구': ['대명동', '이천동', '봉덕동']
    }
    all_dongs = neighbors_map.get(gu, ['대구 전 지역'])
    filtered = [d for d in all_dongs if d != dong]
    return '·'.join(filtered[:4])


# ==========================================
# 4. 상위노출 원고 및 제목 생성 엔진 (마크다운 완전 배제)
# ==========================================
def generate_titles_and_content(region, orig_title, orig_text, num_images, brand="바로누수설비"):
    """
    네이버 실시간 SERP 분석을 반영하고, 바로누수 최근 글의 자연스러운 대화체와
    [현장 요약], 5단계 공정, 체크리스트, 연관 글 링크를 완벽히 구현합니다.
    (스마트에디터 ONE 복붙을 위해 마크다운 기호 및 전화번호 완전 제거)
    """
    region_clean = region.strip()
    words = region_clean.split()
    dong = words[-1] if words else "현장"
    gu = words[-2] if len(words) >= 2 else "대구"
    full_loc = f"{gu} {dong}"

    # 1. 실시간 네이버 검색 분석
    serp_data = search_naver_serp(full_loc)
    serp_titles = serp_data.get("top_titles", [])

    # 2. 건물 유형 및 증상 판별
    is_factory = any(k in orig_text for k in ['공장', '포크레인', '굴착', '마당', '맨홀', '배관 파손', '공단'])
    is_villa = any(k in orig_text for k in ['빌라', '필로티', '원룸', '다세대', '주차장'])
    
    if is_factory:
        b_type = "공장"
        client_quote = "바닥 쪽에서 물이 고이고 계량기가 멈추질 않아요"
        symptom_desc = "바닥 물고임 및 매립 배관 손상"
        building_story = f"공장 및 상가 건물은 지하 매립 관로가 깊고 넓게 묻혀 있어,\n정밀 장비 없이 섣불리 바닥을 파내면 비용과 공사 규모만 커질 수 있습니다.\n생산 라인이나 영업에 지장을 주지 않도록\n빠르고 정확하게 지점을 짚어내는 것이 무엇보다 중요했어요."
    elif is_villa:
        b_type = "빌라"
        client_quote = "주차장 천장에서 물이 떨어지고 바닥이 축축해요"
        symptom_desc = "주차장 천장 물 떨어짐 및 보일러실 배관 누수"
        building_story = f"필로티 구조나 다세대 건물은 1층 주차장 천장으로 물이 새더라도\n실제 누수 원인은 윗세대 보일러실이나 욕실 바닥에 숨어 있는 경우가 많습니다.\n눈에 보이는 천장만 보고 판단하기보다\n정밀 탐지로 배관의 이상 유무를 확실하게 짚어내는 과정이 필요했어요."
    else:
        b_type = "주택"
        client_quote = "욕실 쪽에서 물이 새는 것 같은데 어디가 문제인지 도통 모르겠어요"
        symptom_desc = "욕실 바닥 물비침 및 미세 배관 누수"
        building_story = f"여러 세대가 함께 생활하거나 배관이 바닥 아래 복잡하게 얽혀 있는 건물은\n작은 누수라도 제때 잡지 못하면\n아랫집 피해나 건물 바닥 습기로 번지기 쉽습니다.\n겉으로는 멀쩡해 보이는 바닥 아래에서 어떤 일이 있었는지,\n빠르고 정확한 대구 {gu} 누수 탐지 과정,\n함께 살펴보실까요?"

    # 3. 추천 제목 3선 (검색어 반영 및 CTR 최적화)
    if is_factory:
        t1 = f"대구 {gu} 누수 {dong} {b_type} 바닥 물고임 원인! 매립 배관 파손부터 완벽 교체까지"
        t2 = f"대구 {gu} 누수 {dong} {b_type} 계량기 계속 돌던 이유, 정밀 탐지로 문제 구간 찾아 해결"
        t3 = f"대구 {gu} 누수 {dong} 현장 일지: 지하 관로 누수 특정 및 신규 배관 시공"
    elif is_villa:
        t1 = f"대구 {gu} 누수 {dong} 필로티 {b_type} 주차장 천장 물샘 체크 방법, PB 온수배관 교체 사례"
        t2 = f"대구 {gu} 누수 {dong} {b_type} 천장 물 떨어짐 원인은? 정밀 가스·청음 탐지와 깔끔한 복구"
        t3 = f"대구 {gu} 누수 {dong} {b_type} 보일러실 배관 누수, 최소 굴착으로 원샷 해결 후기"
    else:
        t1 = f"대구 {gu} 누수 {dong} {b_type}, 욕실 바닥 아래 PB 온수배관 꺾임 누수 해결"
        t2 = f"대구 {gu} 누수 {dong} {b_type} 바닥 물비침 원인은? 정밀 청음 탐지와 타일 복구"
        t3 = f"대구 {gu} 누수 {dong} 수도요금 폭탄과 바닥 물샘, 정품 부속 교체로 완벽 해결 후기"

    titles = [t1, t2, t3]

    # 4. 연관 글 및 인근 동 매칭
    related = get_related_posts(gu, dong)
    neighbor_str = get_daegu_neighbors(gu, dong)

    # 5. 본문 구성 (마크다운 기호 #, *, --- 완전 배제, 자연스러운 네이버 에디터 줄바꿈)
    lines = [
        f"​\n​\n{client_quote}\n​",
        f"안녕하세요\n대구 {gu} 누수 탐지부터 복구까지 책임지는\n{brand}입니다\n​",
        f"[현장 요약]\n현장 : 대구 {gu} {dong} {b_type}\n의뢰 : {symptom_desc}\n진단 : 압력검사 후 정밀 탐지로 배관 라인 확인\n원인 : 바닥 속 노후 PB 온수배관 꺾임부 미세 크랙 누수\n해결 : 문제 구간 절단 후 전용 엘보 부속 재시공, 재압력검사, 미장 타일 마감\n​",
        f"이번 현장은 대구 {gu} {dong}의\n{b_type} 현장이에요.\n​\n{building_story}\n​\n함께 살펴보실까요?\n​\n​",
        f"압력 검사로\n누수 여부부터 확인\n​\n가장 먼저 배관에 압력검사 장비를 연결했어요.\n배관에 공압을 걸어두고 게이지가 떨어지는지 지켜보면\n정말 배관에서 새는 누수인지 확실하게 가려낼 수 있어요.\n​\n직수와 온수를 나누어 각각 압력을 걸어보니\n온수 배관 쪽에서 미세하게 압력이 떨어지는 것이 확인되었습니다.\n\n[사진 01: 배관 압력검사 게이지 측정 현장]\n​\n​",
        f"청음 장비로\n정확한 누수 지점 찾기\n​\n다음은 정밀 누수탐지 장비를 꺼냈어요.\n​\n헤드폰을 끼고 바닥 라인을 따라 센서를 옮겨 가며\n물 새는 소리를 하나하나 짚어 나갔습니다.\n​\n여러 번 반복해서 확인한 끝에\n바닥 특정 지점에서 누수음이 가장 강하게 잡혔어요.\n위치를 정확하게 짚어야 바닥을 넓게 깨지 않고\n필요한 부분만 최소한으로 열 수 있답니다.\n\n[사진 02: 청음 탐지기로 누수음 추적 현장]\n​\n​",
        f"필요한 만큼만\n조심스럽게 바닥 굴착\n​\n탐지된 위치에 정확히 표시를 하고\n바닥 타일과 몰탈을 조심스럽게 걷어냈어요.\n​\n주변 타일이 손상되지 않도록 필요한 범위만 컷팅하고,\n배수구나 주변 틈새로는 먼지와 이물질이 들어가지 않도록\n보양 작업을 꼼꼼히 마친 뒤 작업했습니다.\n\n[사진 03: 바닥 굴착 및 배관 노출 현장]\n​\n​",
        f"꺾여서 묻힌 PB배관,\n누수의 원인 확인\n​\n바닥을 걷어내자 문제의 PB 온수배관이 모습을 드러냈어요.\n​\n배관이 부속 없이 둥글게 꺾인 채로 매립되어 있었는데,\n오랜 시간 온수의 열기와 수압을 받으면서\n꺾인 부위에 힘이 실려 결국 미세한 크랙이 생긴 상태였습니다.\n​\n그 틈새로 새어 나온 물이 바닥 아래로 조금씩 스며들고 있었던 것이죠.\n\n[사진 04: 누수 원인인 PB배관 크랙 지점]\n​\n​",
        f"전용 엘보 부속으로\n꺾임 없이 튼튼하게 재시공\n​\n문제가 된 노후 배관 구간을 깔끔하게 절단해 적출했어요.\n​\n그리고 배관이 억지로 꺾이지 않도록\n정품 엘보 전용 부속을 사용해 새 배관을 단단하게 체결했습니다.\n좋은 부속으로 올바른 각도를 잡아주어야\n오랜 세월이 지나도 같은 자리에 하자가 생기지 않아요.\n\n[사진 05: 신규 배관 및 엘보 부속 연결 완료]\n​\n​",
        f"재압력검사로\n완벽한 시공 한 번 더 확인\n​\n배관 연결이 끝났다고 바로 덮지 않아요.\n​\n다시 압력 게이지를 연결하고 공압을 주입해\n더 이상의 미세 누수나 압력 저하가 없는지 꼼꼼하게 검증했습니다.\n바늘이 미동도 없이 안정적으로 유지되는 것을 확인한 뒤에야\n비로소 다음 복구 공정으로 넘어갑니다.\n\n[사진 06: 재압력검사 및 수밀 테스트]\n​\n​",
        f"미장부터 타일 부착까지\n깔끔하게 마무리\n​\n굴착했던 자리는 몰탈로 단단하게 메우고 미장 작업을 진행했어요.\n기존 바닥과 단차가 생기지 않도록 평평하게 맞춘 뒤,\n타일을 부착하고 줄눈까지 꼼꼼히 채워 원래 모습으로 복구했습니다.\n​\n정확한 지점만 최소한으로 열었기 때문에\n마감 후에도 흔적이 도드라지지 않고 깔끔하게 정리되었어요.\n\n[사진 07: 미장 및 타일 복구 마감 현장]\n​\n​",
        f"알아두면 좋은 {b_type} 누수 체크 방법\n​\n1. 물을 쓰지 않는데도 수도계량기 별침이 조금씩 움직이는 경우\n2. 바닥이나 벽면이 유난히 축축하거나 장판 아래에 누런 물 얼룩이 생기는 경우\n3. 평소와 달리 수도요금이 갑자기 많이 청구된 경우\n4. 아랫집 천장이나 주차장 천장으로 물방울이 떨어지거나 곰팡이가 피어나는 경우\n5. 아랫집 피해가 발생한 경우 가입해 두신 일상생활배상책임보험(일배책)으로 보상이 가능하며, 수리 사진과 증빙 서류를 챙겨두시면 좋습니다.\n​\n​\n누수는 방치할수록 바닥 곰팡이와 이웃 피해로 번지기 쉬워요.\n정밀 탐지로 위치를 먼저 잡으면\n필요한 곳만 최소한으로 열고 빠르게 고칠 수 있습니다.\n​\n대구 {gu} 누수, {dong}을 비롯해\n{neighbor_str} 어디든\n{brand}에 편하게 문의 주세요.\n​\n읽어주셔서 감사합니다!\n​"
    ]

    # 유사 이전 글 링크 추가
    if related:
        lines.append("\n함께 읽으면 좋은 글\n")
        for p in related:
            lines.append(f"• {p['title']}\n{p['url']}\n")

    full_body = "\n".join(lines)

    step_captions = [
        ("STEP 01", "배관 압력검사"),
        ("STEP 02", "정밀 청음 탐지"),
        ("STEP 03", "최소 바닥 굴착"),
        ("STEP 04", "원인 배관 확인"),
        ("STEP 05", "전용 부속 교체"),
        ("STEP 06", "재압력검사 검증"),
        ("STEP 07", "미장 타일 마감")
    ]

    return titles, full_body.strip(), step_captions, serp_titles


# ==========================================
# 5. 이미지 가공 엔진 (자연스러운 미니멀 워터마크 지원)
# ==========================================
def process_and_badge_images(image_urls, steps, brand="바로누수설비", photo_style="natural"):
    """
    이미지 다운로드 및 가공.
    - natural (기본값): 기존 사진 스타일을 해치지 않는 미니멀 상단 워터마크 + 선명도 보정
    - banner: 하단 자막 바 포함
    - clean: 텍스트 없이 선명도 보정만 적용
    """
    processed_images = []
    
    font_badge = get_korean_font(22)
    font_brand = get_korean_font(20)
    font_title = get_korean_font(22)
    font_desc = get_korean_font(18)

    headers = {'User-Agent': 'Mozilla/5.0'}

    for idx, url in enumerate(image_urls, 1):
        if idx <= len(steps):
            code, step_title = steps[idx - 1]
        else:
            code = f"STEP {idx:02d}"
            step_title = "현장 시공 과정"

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw_data = resp.read()
                img = Image.open(io.BytesIO(raw_data)).convert('RGB')
        except Exception:
            img = Image.new('RGB', (800, 600), color=(60, 60, 60))

        # 대비 살짝 개선 (자연스러운 선명도)
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.06)

        draw = ImageDraw.Draw(img)
        w, h = img.size

        if photo_style == "natural":
            # 1. 자연스러운 미니멀 스타일 (기본값: 기존 글과 이질감 없음)
            # 좌측 상단: 작은 STEP 라벨
            badge_text = f" {code} "
            draw.rounded_rectangle([(18, 18), (125, 52)], radius=6, fill=(30, 41, 59))
            draw.text((24, 23), badge_text, font=font_badge, fill=(255, 255, 255))

            # 우측 상단: 깔끔한 브랜드 워터마크
            brand_w = 125
            draw.rounded_rectangle([(w - brand_w - 18, 18), (w - 18, 52)], radius=6, fill=(37, 99, 235))
            draw.text((w - brand_w - 8, 23), f" {brand} ", font=font_brand, fill=(255, 255, 255))

        elif photo_style == "banner":
            # 2. 하단 설명 자막 바 스타일
            badge_text = f" {code} "
            draw.rounded_rectangle([(20, 20), (140, 60)], radius=8, fill=(30, 41, 59))
            draw.text((28, 25), badge_text, font=font_badge, fill=(255, 255, 255))

            brand_w = 135
            draw.rounded_rectangle([(w - brand_w - 20, 20), (w - 20, 58)], radius=6, fill=(37, 99, 235))
            draw.text((w - brand_w - 10, 25), f" {brand} ", font=font_brand, fill=(255, 255, 255))

            bar_h = 80
            overlay = Image.new('RGBA', (w, bar_h), (15, 23, 42, 220))
            img.paste(overlay, (0, h - bar_h), overlay)
            draw.rectangle([(0, h - bar_h), (w, h - bar_h + 4)], fill=(37, 99, 235))
            draw.text((25, h - bar_h + 12), f"[{step_title}]", font=font_title, fill=(96, 165, 250))
            draw.text((25, h - bar_h + 45), f"{brand} 대구 현장 책임 시공", font=font_desc, fill=(241, 245, 249))

        # photo_style == "clean"인 경우 텍스트 없이 선명도 보정만 유지

        filename = f"{idx:02d}_{code.replace(' ', '_')}_{step_title.replace(' ', '_')}.jpg"
        
        img_byte_io = io.BytesIO()
        img.save(img_byte_io, format='JPEG', quality=92)
        img_bytes = img_byte_io.getvalue()

        processed_images.append({
            "idx": idx,
            "filename": filename,
            "code": code,
            "title": step_title,
            "image": img,
            "bytes": img_bytes
        })

    return processed_images


# ==========================================
# 6. 숏폼 영상 생성 엔진 (H.264 MP4)
# ==========================================
def create_shortform_video(processed_images, duration=15):
    """모바일 호환 H.264 9:16 숏폼 MP4 비디오 바이트를 생성합니다."""
    if not processed_images:
        return None

    W, H = 720, 1280
    fps = 24
    num_imgs = len(processed_images)
    frames_per_img = max(int((fps * duration) / num_imgs), fps)

    temp_video_path = "/tmp/shortform_render.mp4"

    try:
        writer = imageio.get_writer(
            temp_video_path,
            fps=fps,
            codec='libx264',
            pixelformat='yuv420p',
            quality=8
        )

        for idx, item in enumerate(processed_images):
            pil_img = item["image"]
            iw, ih = pil_img.size

            bg_pil = pil_img.resize((W, H), Image.Resampling.BILINEAR).filter(ImageFilter.GaussianBlur(radius=25))
            bg_pil = ImageEnhance.Brightness(bg_pil).enhance(0.45)

            scale = W / iw
            new_w = W
            new_h = int(ih * scale)
            y_offset = max((H - new_h) // 2, 0)

            for f in range(frames_per_img):
                frame = bg_pil.copy()

                zoom = 1.0 + (f / frames_per_img) * 0.035
                zw = int(new_w * zoom)
                zh = int(new_h * zoom)
                fg_zoomed = pil_img.resize((zw, zh), Image.Resampling.BILINEAR)

                zx = max((zw - W) // 2, 0)
                zy = max((zh - new_h) // 2, 0)
                fg_crop = fg_zoomed.crop((zx, zy, zx + W, zy + new_h))

                if y_offset + new_h <= H:
                    frame.paste(fg_crop, (0, y_offset))

                progress = (idx * frames_per_img + f) / (num_imgs * frames_per_img)
                bar_w = int(W * progress)
                draw = ImageDraw.Draw(frame)
                draw.rectangle([(0, 0), (bar_w, 10)], fill=(255, 165, 0))

                writer.append_data(np.array(frame))

        writer.close()

        with open(temp_video_path, "rb") as vf:
            video_bytes = vf.read()
        
        try:
            os.remove(temp_video_path)
        except Exception:
            pass

        return video_bytes
    except Exception as e:
        print(f"영상 인코딩 중 오류 발생: {e}")
        return None
