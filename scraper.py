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

def calculate_suitability_score(text: str, purpose: str = "공구") -> dict:
    gongu_keywords = ["공구", "마켓", "최저가", "오픈", "할인", "프로필링크", "협업", "진행중", "단독", "한정수량", "특가", "공구가", "구매링크", "마켓오픈", "선착순"]
    review_keywords = ["협찬", "체험단", "제공받아", "솔직후기", "원고료", "제작지원", "리뷰", "서포터즈", "광고", "무료제공"]
    
    found_gongu = [kw for kw in gongu_keywords if kw in text]
    found_review = [kw for kw in review_keywords if kw in text]
    
    base_score = 75
    if purpose == "공구":
        if "공구" in text or "마켓" in text:
            base_score = 88
        bonus = min(len(found_gongu) * 3, 10)
        final_score = min(base_score + bonus, 98)
        signals = found_gongu if found_gongu else ["공구/마켓 연관"]
    else:
        if "협찬" in text or "체험단" in text or "제공받아" in text:
            base_score = 88
        bonus = min(len(found_review) * 3, 10)
        final_score = min(base_score + bonus, 98)
        signals = found_review if found_review else ["체험단/협찬 연관"]
        
    if final_score >= 88:
        level = "매우 높음 (강력 추천)"
    elif final_score >= 75:
        level = "높음 (협업 추천)"
    else:
        level = "보통 (검토 필요)"
        
    return {
        "score": final_score,
        "level": level,
        "signals": signals
    }

def search_instagram(query: str, purpose: str = "공구", max_results: int = 15) -> list:
    """
    인스타그램 실제 공구/협찬 인플루언서를 실시간으로 검색·추출합니다.
    Meta API 키나 계정 연동 없이 즉시 동작합니다.
    """
    keyword = query.strip()
    if purpose == "공구":
        search_query = f'site:instagram.com "{keyword}" ("공구마켓" | "공구오픈" | "공구진행" | "공구")'
    else:
        search_query = f'site:instagram.com "{keyword}" ("협찬" | "체험단" | "서포터즈")'
        
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
                if handle.lower() in ['', 'p', 'reel', 'reels', 'stories', 'explore', 'about', 'legal', 'accounts', 'developer', 'privacy', 'directory']:
                    continue
                if handle in seen:
                    continue
                seen.add(handle)
                
                # 상위 카드 텍스트 수집
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
                    elif len(t) > 12 and 'instagram.com' not in t and not t.startswith('http') and t not in ['새 창 열림', 'Keep에 저장', 'Keep에 바로가기']:
                        snippet += t + " "
                
                snippet = snippet.replace('robots.txt로 인해 정보를 수집할 수 없습니다.', '').strip()
                if not snippet:
                    snippet = f"인스타그램에서 '{keyword}' {purpose} 활동을 진행하는 인플루언서 계정입니다."
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
                    "date": "실시간 활동",
                    "score": score_info["score"],
                    "level": score_info["level"],
                    "signals": score_info["signals"],
                    "purpose": purpose
                })
                
                if len(results) >= max_results:
                    break
    except Exception as e:
        print(f"Error scraping instagram: {e}")
        
    return results

def search_naver_blog(query: str, purpose: str = "공구", max_results: int = 15) -> list:
    """
    네이버 블로그 실시간 공구/협찬 글을 스크래핑하여 실제 인플루언서를 발굴합니다.
    """
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
                
                # author 찾기
                if len(texts) >= 1 and texts[0] not in ["Keep에 저장", "Keep에 바로가기", date_str]:
                    author = texts[0]
                    
                # 본문 텍스트들 합치기
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
                    "purpose": purpose
                })
                
                if len(results) >= max_results:
                    break
    except Exception as e:
        print(f"Error scraping naver blog: {e}")
        
    return results
