import urllib.request
import urllib.parse
from lxml import html
import re
import datetime

USER_AGENT_MOBILE = 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36'

def calculate_suitability_score(text: str, purpose: str = "공구") -> dict:
    """
    텍스트(제목, 본문 스니펫, 소개글)를 분석하여 공구/체험단 적합도 점수(0~100)와 신호 키워드를 계산합니다.
    """
    gongu_keywords = ["공구", "마켓", "최저가", "오픈", "할인", "프로필링크", "협업", "진행중", "단독", "한정수량", "특가", "공구가", "구매링크"]
    review_keywords = ["협찬", "체험단", "제공받아", "솔직후기", "원고료", "제작지원", "리뷰", "서포터즈", "광고"]
    
    found_gongu = [kw for kw in gongu_keywords if kw in text]
    found_review = [kw for kw in review_keywords if kw in text]
    
    base_score = 70
    if purpose == "공구":
        if "공구" in text or "마켓" in text:
            base_score = 88
        bonus = min(len(found_gongu) * 4, 10)
        final_score = min(base_score + bonus, 98)
        signals = found_gongu if found_gongu else ["키워드 연관"]
    else:
        if "협찬" in text or "체험단" in text or "제공받아" in text:
            base_score = 88
        bonus = min(len(found_review) * 4, 10)
        final_score = min(base_score + bonus, 98)
        signals = found_review if found_review else ["키워드 연관"]
        
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

def search_naver_blog(query: str, purpose: str = "공구", max_results: int = 15) -> list:
    """
    네이버 모바일 블로그 검색을 실시간 스크래핑하여 실제 인플루언서 후보를 발굴합니다.
    API 키가 전혀 필요하지 않습니다.
    """
    search_query = query.strip()
    if purpose == "공구" and "공구" not in search_query:
        effective_query = f"{search_query} 공구"
    elif purpose == "체험단" and "체험단" not in search_query and "협찬" not in search_query:
        effective_query = f"{search_query} 협찬"
    else:
        effective_query = search_query

    url = f"https://m.search.naver.com/search.naver?where=m_blog&query={urllib.parse.quote(effective_query)}"
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT_MOBILE})
    
    results = []
    seen_urls = set()
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode('utf-8')
            doc = html.fromstring(content)
            
            blocks = doc.xpath('//*[contains(@class, "fds-ugc-ur")]')
            for b in blocks:
                texts = [t.strip() for t in b.xpath('.//text()') if t.strip()]
                links = b.xpath('.//a[contains(@href, "blog.naver.com")]/@href')
                if not links:
                    continue
                
                post_url = links[0]
                if post_url in seen_urls:
                    continue
                seen_urls.add(post_url)
                
                blog_id_match = re.search(r'blog\.naver\.com/([a-zA-Z0-9_-]+)', post_url)
                blog_id = blog_id_match.group(1) if blog_id_match else "naver_user"
                
                author = "블로거"
                date_str = "최근"
                
                if len(texts) >= 1:
                    author = texts[0]
                for t in texts:
                    if any(w in t for w in ["일 전", "시간 전", "분 전", "주 전", "202", "어제", "방금"]):
                        date_str = t
                        break
                        
                # UI성 메타 텍스트만 제외하고 실제 본문과 제목 복원
                filtered_texts = [t for t in texts if t not in ["Keep에 저장", "Keep에 바로가기", author, date_str]]
                title = " ".join(filtered_texts[:2]) if filtered_texts else "블로그 게시글"
                snippet = " ".join(filtered_texts[2:6]) if len(filtered_texts) > 2 else ""
                
                combined_text = f"{title} {snippet}"
                score_info = calculate_suitability_score(combined_text, purpose)
                
                results.append({
                    "platform": "naver",
                    "name": author,
                    "handle": f"@{blog_id}",
                    "profile_url": f"https://m.blog.naver.com/{blog_id}",
                    "post_url": post_url,
                    "title": title,
                    "snippet": snippet,
                    "date": date_str,
                    "score": score_info["score"],
                    "level": score_info["level"],
                    "signals": score_info["signals"],
                    "purpose": purpose
                })
                
                if len(results) >= max_results:
                    break
    except Exception as e:
        print(f"Error scraping naver: {e}")
        
    return results

def search_instagram(query: str, purpose: str = "공구", max_results: int = 15) -> list:
    """
    네이버 웹 검색을 통해 공개 인스타그램 인플루언서/공구 계정을 실시간 수집합니다.
    Meta Graph API 토큰이나 비즈니스 계정 연동이 전혀 필요 없습니다.
    """
    search_query = query.strip()
    if purpose == "공구":
        ig_search = f'site:instagram.com "{search_query}" "공구"'
    else:
        ig_search = f'site:instagram.com "{search_query}" "협찬"'
        
    url = f"https://m.search.naver.com/search.naver?where=m_web&query={urllib.parse.quote(ig_search)}"
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT_MOBILE})
    
    results = []
    seen_handles = set()
    
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            content = resp.read().decode('utf-8')
            doc = html.fromstring(content)
            
            links = doc.xpath('//a[contains(@href, "instagram.com/")]')
            for l in links:
                href = l.get('href', '')
                if href.startswith('?') or 'instagram.com/p/' in href or 'instagram.com/explore' in href:
                    continue
                    
                match = re.search(r'instagram\.com/([a-zA-Z0-9_.]+)/?', href)
                if not match:
                    continue
                handle = match.group(1).strip()
                if handle in ["", "p", "reel", "stories", "explore", "about", "legal", "accounts"]:
                    continue
                if handle in seen_handles:
                    continue
                seen_handles.add(handle)
                
                parent = l.xpath('./ancestor::div[contains(@class, "total_wrap")] | ./ancestor::li')
                container = parent[0] if parent else l.getparent()
                texts = [t.strip() for t in container.xpath('.//text()') if t.strip()] if container is not None else []
                
                display_name = handle
                snippet = ""
                for t in texts:
                    if "@" in t and "Instagram" in t:
                        display_name = t.split("-")[0].replace("Instagram", "").strip()
                    elif len(t) > 15 and "instagram.com" not in t:
                        snippet += t + " "
                        
                snippet = snippet.strip()[:150]
                combined_text = f"{handle} {display_name} {snippet}"
                score_info = calculate_suitability_score(combined_text, purpose)
                
                results.append({
                    "platform": "instagram",
                    "name": display_name,
                    "handle": f"@{handle}",
                    "profile_url": f"https://www.instagram.com/{handle}/",
                    "post_url": f"https://www.instagram.com/{handle}/",
                    "title": f"인스타그램 @{handle} 프로필",
                    "snippet": snippet if snippet else f"@{handle} 님의 인스타그램 계정입니다. 클릭하여 피드 확인",
                    "date": "최근 활동",
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
