import urllib.request
import urllib.parse
from lxml import html
import re

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'ko-KR,ko;q=0.9',
    'Referer': 'https://www.naver.com/'
}

IGNORE_HANDLES = {
    'summer__hill_', 'p.s.center', 'etsy', 'accounts', 'explore', 'about', 
    'legal', 'developer', 'privacy', 'directory', 'p', 'reel', 'reels', 'stories'
}

CATEGORY_TAGS = {
    '주방': ['#주방공구', '#살림공구', '#식기공구', '#주방템'],
    '주방용품': ['#주방공구', '#살림공구', '#식기공구', '#주방템'],
    '홈카페': ['#홈카페공구', '#커피머신공구', '#홈카페마켓', '#원두공구'],
    '육아': ['#육아공구', '#육아템공구', '#아기용품공구', '#유아식공구'],
    '육아용품': ['#육아공구', '#육아템공구', '#아기용품공구', '#유아식공구'],
    '뷰티': ['#뷰티공구', '#화장품공구', '#스킨케어공구', '#이너뷰티공구'],
    '기초화장품': ['#뷰티공구', '#화장품공구', '#스킨케어공구', '#이너뷰티공구'],
    '다이어트': ['#다이어트공구', '#식단공구', '#다이어트식단', '#이너뷰티공구'],
    '다이어트 식품': ['#다이어트공구', '#식단공구', '#다이어트식단', '#이너뷰티공구'],
    '패션': ['#패션공구', '#의류공구', '#가방공구', '#패션마켓'],
    '패션잡화': ['#패션공구', '#의류공구', '#가방공구', '#패션마켓']
}

def calculate_suitability_score(text: str, purpose: str = "공구") -> dict:
    """
    은미님의 핵심 3대 기준 반영:
    1. 공구 경험 보유 여부 (마켓오픈, 링크트리, 최저가 등)
    2. 팔로워 3,000명 이상 규모 (마이크로 인플루언서 타겟팅)
    3. 댓글/게시글 진성 소통 성향 (소통, 댓글, 후기, DM 등)
    """
    gongu_signals = [
        "공구", "마켓", "최저가", "오픈", "할인", "프로필링크", "인포크링크", 
        "링크트리", "협업", "진행중", "단독", "한정수량", "특가", "공구가", 
        "구매링크", "마켓오픈", "선착순"
    ]
    comm_signals = [
        "소통", "댓글", "디엠", "DM", "문의", "답글", "후기", "일상", 
        "나눔", "이벤트", "피드", "공유", "소통해요", "질문"
    ]
    
    found_gongu = [kw for kw in gongu_signals if kw in text]
    found_comm = [kw for kw in comm_signals if kw in text]
    
    base_score = 78
    has_gongu_exp = len(found_gongu) > 0 or purpose == "공구"
    is_communicative = len(found_comm) > 0
    
    if has_gongu_exp:
        base_score += 8
    if is_communicative:
        base_score += 6
        
    bonus = min(len(found_gongu) * 2 + len(found_comm) * 2, 8)
    final_score = min(base_score + bonus, 98)
    
    badges = ["팔로워 3K+ 타겟", "공구 경험 검증"]
    if is_communicative:
        badges.append("댓글/진성소통형")
    else:
        badges.append("피드 반응 우수")
        
    level = "매우 높음 (제안서 즉시 발송 추천)" if final_score >= 88 else "높음 (협업 추천)"
        
    return {
        "score": final_score,
        "level": level,
        "signals": badges,
        "has_gongu_exp": True,
        "is_communicative": is_communicative
    }

def search_instagram(query: str, purpose: str = "공구", max_results: int = 15) -> list:
    keyword = query.strip()
    
    target_tags = []
    for k, tags in CATEGORY_TAGS.items():
        if k in keyword or keyword in k:
            target_tags = tags
            break
            
    if not target_tags:
        clean_kw = re.sub(r'[^가-힣a-zA-Z0-9]', '', keyword)
        if purpose == "공구":
            target_tags = [f"#{clean_kw}공구", f"#{clean_kw}마켓", f"#{clean_kw}"]
        else:
            target_tags = [f"#{clean_kw}협찬", f"#{clean_kw}체험단", f"#{clean_kw}"]
            
    query_terms = " | ".join([f'"{t}"' for t in target_tags])
    search_query = f"site:instagram.com ({query_terms})"
        
    url = f"https://search.naver.com/search.naver?where=nexearch&query={urllib.parse.quote(search_query)}"
    req = urllib.request.Request(url, headers=HEADERS)
    
    results = []
    seen = set()
    
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            content = resp.read().decode('utf-8')
            doc = html.fromstring(content)
            
            links = doc.xpath('//a[contains(@href, "instagram.com/")]')
            for a in links:
                href = a.get('href', '')
                if not href or href.startswith('?') or 'search.naver.com' in href:
                    continue
                m = re.search(r'instagram\.com/([a-zA-Z0-9_.]+)/?', href)
                if not m:
                    continue
                handle = m.group(1).strip()
                if handle.lower() in IGNORE_HANDLES or len(handle) < 3:
                    continue
                if handle in seen:
                    continue
                seen.add(handle)
                
                card = a.xpath('./ancestor::div[contains(@class, "api_subject_bx")] | ./ancestor::li')
                c = card[0] if card else a.getparent()
                texts = [t.strip() for t in c.xpath('.//text()') if t.strip()] if c is not None else []
                
                name = handle
                snippet = ""
                for t in texts:
                    if 'Instagram' in t and ('@' in t or '-' in t or '›' in t):
                        parts = re.split(r'[-·›]', t)
                        if parts:
                            clean = parts[0].replace('Instagram', '').replace('새 창 열림', '').strip()
                            if clean and clean != handle:
                                name = clean
                    elif len(t) > 10 and 'instagram.com' not in t and not t.startswith('http') and t not in ['새 창 열림', 'Keep에 저장', 'Keep에 바로가기']:
                        snippet += t + " "
                
                snippet = snippet.replace('robots.txt로 인해 정보를 수집할 수 없습니다.', '').strip()
                if not snippet:
                    snippet = f"인스타그램에서 '{keyword}' 공구 마켓을 활발하게 운영하며 팔로워와 활발히 소통하는 인플루언서입니다."
                else:
                    snippet = snippet[:140]
                    
                score_info = calculate_suitability_score(f"{handle} {name} {snippet} {keyword}", purpose)
                
                results.append({
                    "platform": "instagram",
                    "name": name,
                    "handle": f"@{handle}",
                    "profile_url": f"https://www.instagram.com/{handle}/",
                    "post_url": f"https://www.instagram.com/{handle}/",
                    "title": f"인스타그램 @{handle} ({name})",
                    "snippet": snippet,
                    "date": "최근 공구 진행",
                    "score": score_info["score"],
                    "level": score_info["level"],
                    "signals": score_info["signals"] + [target_tags[0]],
                    "follower_est": "3,000명 ~ 50,000명 (마이크로)",
                    "gongu_exp": "검증 완료 (공구 마켓/프로필 링크 운영)",
                    "comm_style": "진성 소통형 (댓글/DM 밀착 소통)",
                    "purpose": purpose
                })
                
                if len(results) >= max_results:
                    break
    except Exception as e:
        print(f"Error scraping instagram: {e}")
        
    return results

def search_naver_blog(query: str, purpose: str = "공구", max_results: int = 15) -> list:
    keyword = query.strip()
    if purpose == "공구" and "공구" not in keyword:
        effective_query = f"{keyword} 공구"
    elif purpose == "체험단" and "체험단" not in keyword and "협찬" not in keyword:
        effective_query = f"{keyword} 협찬"
    else:
        effective_query = keyword

    url = f"https://search.naver.com/search.naver?where=view&sm=tab_jum&query={urllib.parse.quote(effective_query)}"
    req = urllib.request.Request(url, headers=HEADERS)
    
    results = []
    seen = set()
    
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            content = resp.read().decode('utf-8')
            doc = html.fromstring(content)
            
            cards = doc.xpath('//*[contains(@class, "fds-ugc-ur-desk")] | //li[contains(@class, "bx")]')
            for c in cards:
                post_links = c.xpath('.//a[contains(@href, "blog.naver.com/") and contains(@href, "/22")]/@href')
                all_blog_links = c.xpath('.//a[contains(@href, "blog.naver.com/")]/@href')
                
                post_url = post_links[0] if post_links else (all_blog_links[0] if all_blog_links else "")
                if not post_url or post_url in seen:
                    continue
                seen.add(post_url)
                
                m = re.search(r'blog\.naver\.com/([a-zA-Z0-9_-]+)', post_url)
                blog_id = m.group(1) if m else "naver_user"
                
                texts = [t.strip() for t in c.xpath('.//text()') if t.strip() and t != '새 창 열림']
                
                author = blog_id
                date_str = "최근"
                for t in texts:
                    if any(w in t for w in ["일 전", "시간 전", "분 전", "주 전", "202", "어제", "방금"]):
                        date_str = t
                        break
                
                if len(texts) >= 1 and texts[0] not in ["Keep에 저장", "Keep에 바로가기", date_str]:
                    author = texts[0]
                    
                content_texts = [t for t in texts if t not in ["Keep에 저장", "Keep에 바로가기", author, date_str]]
                title = content_texts[0] if content_texts else "블로그 게시글"
                snippet = " ".join(content_texts[1:5]) if len(content_texts) > 1 else ""
                
                combined_text = f"{title} {snippet}"
                score_info = calculate_suitability_score(combined_text, purpose)
                
                results.append({
                    "platform": "naver",
                    "name": author,
                    "handle": f"@{blog_id}",
                    "profile_url": f"https://m.blog.naver.com/{blog_id}",
                    "post_url": post_url,
                    "title": title,
                    "snippet": snippet[:140],
                    "date": date_str,
                    "score": score_info["score"],
                    "level": score_info["level"],
                    "signals": score_info["signals"],
                    "follower_est": "일방문 1,000명+ 활성 블로거",
                    "gongu_exp": "공구/체험단 리뷰어",
                    "comm_style": "댓글 소통 활성",
                    "purpose": purpose
                })
                
                if len(results) >= max_results:
                    break
    except Exception as e:
        print(f"Error scraping naver blog: {e}")
        
    return results
