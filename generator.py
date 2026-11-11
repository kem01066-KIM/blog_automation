import re
import urllib.request
import requests
from bs4 import BeautifulSoup

def extract_meta_info(url):
    """
    URL에서 메타 태그(og:title, og:description, og:image)를 추출합니다.
    """
    clean_url = url.strip()
    result = {
        "title": "",
        "desc": "",
        "image": "",
        "original_url": clean_url,
        "is_coupang": "coupang" in clean_url or "coupa.ng" in clean_url,
        "is_naver": "naver" in clean_url or "smartstore" in clean_url
    }

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        res = requests.get(clean_url, headers=headers, timeout=5, allow_redirects=True)
        if res.status_code == 200:
            soup = BeautifulSoup(res.text, 'html.parser')
            og_title = soup.find("meta", property="og:title") or soup.find("meta", attrs={"name": "title"})
            og_desc = soup.find("meta", property="og:description") or soup.find("meta", attrs={"name": "description"})
            og_img = soup.find("meta", property="og:image")

            if og_title and og_title.get("content"):
                result["title"] = og_title.get("content").strip()
            elif soup.title:
                result["title"] = soup.title.string.strip()

            if og_desc and og_desc.get("content"):
                result["desc"] = og_desc.get("content").strip()

            if og_img and og_img.get("content"):
                result["image"] = og_img.get("content").strip()
    except Exception:
        pass

    return result


def generate_threads_posts(product_name, key_points, affiliate_link, platform_type="coupang", category="생활/리빙"):
    """
    스레드 최적화 썰 글 3종(내돈내산 찐후기형, 호구방지 비교형, 일상공감 꿀팁형)을 생성합니다.
    """
    p_name = product_name.strip()
    points = key_points.strip() if key_points else "가성비 좋고 삶의 질이 올라감"
    link = affiliate_link.strip()

    # 공정위 문구 결정
    if platform_type == "coupang":
        ftc_notice = "이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다."
    elif platform_type == "naver":
        ftc_notice = "네이버 브랜드 커넥트 및 제휴 링크를 통해 수수료를 제공받을 수 있습니다."
    else:
        ftc_notice = "해당 링크를 통한 구매 시 소정의 수수료를 지급받을 수 있습니다."

    # 1. 내돈내산 찐후기형 (진정성 & 체감 경험)
    post_a_body = f"""솔직히 바이럴인 줄 알고 3주 동안 장바구니에만 넣어뒀는데...

왜 이제 샀나 싶을 정도로 삶의 질이 확 달라졌습니다.
{p_name} 쓴 지 벌써 한 달째인데 솔직한 후기 남겨봐요.

처음엔 긴가민가했거든요. 
근데 막상 써보니까 {points}.
진짜 기대 이상으로 만족도가 높아서 주변 사람들한테도 계속 영업 중입니다.

다만 딱 하나 아쉬운 점을 꼽자면, 인기 많아서 배송이나 재고가 가끔 간당간당하다는 거? 
그거 말고는 단점을 못 찾겠네요.

혹시 고민 중이신 분들은 후기 꼭 비교해보고 고르세요.
자세한 정보랑 제가 샀던 최저가 링크는 첫 댓글에 남겨둘게요!"""

    post_a_comment = f"""📌 {p_name} 최저가 확인하기
{link}

* {ftc_notice}"""

    # 2. 호구방지 비교분석형 (호기심 유발 & 합리적 소비)
    post_b_body = f"""다들 이거 살 때 비싼 대기업 거 사던데...
솔직히 말해서 돈 낭비라고 봅니다.

제가 브랜드별로 스펙이랑 리뷰 싹 다 뜯어보고 비교해봤거든요?
핵심 기능은 거의 똑같은데 가격 차이는 2~3배 나더라고요.

결국 제가 고른 건 {p_name}인데,
결론부터 말씀드리면 완전 대성공입니다.

실제로 써보면 {points}.
비싼 돈 주고 거품 낀 브랜드 이름값 낼 필요가 전혀 없어요.
딱 필요한 실속만 챙기실 분들에게 진심으로 추천합니다.

구매 링크랑 할인 정보는 첫 번째 댓글에 고정해 둘게요!"""

    post_b_comment = f"""📌 가성비 종결 {p_name} 링크
{link}

* {ftc_notice}"""

    # 3. 일상공감 꿀팁형 (스토리텔링 & 결핍 해소)
    post_c_body = f"""퇴근하고 집에 오면 손 하나 까딱하기 싫은 날 있잖아요.

맨날 시간 뺏기고 스트레스받던 일이었는데,
이거 하나 들이고 나서 퇴근 후 일상이 180도 바뀌었습니다.

{p_name} 이거 진짜 물건이네요.
직접 써보고 느낀 제일 큰 장점은 {points}.

별거 아닌 것 같아도 매일 쓰는 생활템 하나만 제대로 바꿔도 하루 피로도가 확 줄어드는 게 느껴집니다.

저처럼 일상 피로 줄이고 싶으신 분들은 꼭 한번 체크해보세요.
제가 주문했던 곳 링크는 댓글에 남겨둘게요!"""

    post_c_comment = f"""📌 삶의 질 수직 상승템 {p_name}
{link}

* {ftc_notice}"""

    # 본문 직접 삽입형 풀버전
    full_a = f"{post_a_body}\n\n👉 구매 링크: {link}\n\n* {ftc_notice}"
    full_b = f"{post_b_body}\n\n👉 구매 링크: {link}\n\n* {ftc_notice}"
    full_c = f"{post_c_body}\n\n👉 구매 링크: {link}\n\n* {ftc_notice}"

    return {
        "type_a": {
            "title": "🔥 A타입: 내돈내산 찐후기 썰",
            "body": post_a_body,
            "comment": post_a_comment,
            "full": full_a
        },
        "type_b": {
            "title": "💡 B타입: 호구방지 비교분석 썰",
            "body": post_b_body,
            "comment": post_b_comment,
            "full": full_b
        },
        "type_c": {
            "title": "☕ C타입: 일상공감 삶의 질 꿀팁 썰",
            "body": post_c_body,
            "comment": post_c_comment,
            "full": full_c
        }
    }


if __name__ == '__main__':
    # Test generation
    sample_res = generate_threads_posts(
        product_name="샤오미 핸디형 무선청소기",
        key_points="흡입력 세고 틈새 먼지 머리카락 1초 컷, 가벼워서 손목 안 아픔",
        affiliate_link="https://link.coupang.com/a/sample123",
        platform_type="coupang"
    )
    print("Type A Title:", sample_res["type_a"]["title"])
    print("Type A Body:\n", sample_res["type_a"]["body"][:150], "...")
    print("Type A Comment:\n", sample_res["type_a"]["comment"])
    print("\nSUCCESS!")
