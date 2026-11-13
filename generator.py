import re
import urllib.parse
import requests
from bs4 import BeautifulSoup

def clean_url(url):
    """
    URL 공백 제거 및 스키마(https://) 자동 보정
    """
    clean = url.strip()
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
    title = raw_title.strip()
    
    # 대표적인 쇼핑몰 접미사 패턴 제거
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
    어떤 비정상 URL이나 차단(403 등)이 발생해도 절대 에러로 멈추지 않고 안전한 딕셔너리를 반환합니다.
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

    # 쿠팡 링크는 대부분 봇 방어(403)가 걸려 있으므로 사전 안내 설정
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
            
            # OpenGraph 우선 탐색
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
    except Exception as e:
        # 어떤 타임아웃이나 파싱 에러도 절대 밖으로 터지지 않음
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

def generate_threads_posts(product_name, key_points, affiliate_link, platform_type="coupang", category="생활/가전"):
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

    # 풀버전 일체형 (필요한 사람용)
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
