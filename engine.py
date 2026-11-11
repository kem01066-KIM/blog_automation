"""
Place Insight Pro - 네이버 스마트플레이스 정밀 운영 진단 엔진 (확장 업그레이드 버전)
기본정보(15점) + 특장점(15점) + 메뉴디테일(20점) + 핵심기능(25점) + 리뷰답글(15점) + 새소식(10점) = 100점 만점
"""

import re
from typing import Dict, List, Any

def calculate_place_audit(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    네이버 스마트플레이스 6대 핵심 영역 100점 만점 정밀 진단
    """
    scores = {
        "info": 0,        # 기본 정보 정확성 (15점)
        "strengths": 0,   # 소개글 & 특장점 키워드 (15점)
        "menu": 0,        # 메뉴명 / 메뉴사진 / 설명 (20점)
        "features": 0,    # 핵심 기능(예약·스마트콜·알림받기·쿠폰·톡톡) (25점)
        "reviews": 0,     # 영수증 리뷰 & 사장님 답글 관리 (15점)
        "news": 0         # 플레이스 새소식 활성도 (10점)
    }
    
    evidences = []
    
    # -------------------------------------------------------------------------
    # 1. 기본 정보 정확성 (15점 만점)
    # -------------------------------------------------------------------------
    info_points = 0
    if data.get("address") and data.get("tel"):
        info_points += 3
    elif data.get("address"):
        info_points += 1
        evidences.append("대표 전화번호가 누락되었거나 안심번호 설정이 필요합니다.")
        
    hours = data.get("hours", "").strip()
    if len(hours) >= 15 and ("휴무" in hours or "매일" in hours or "요일" in hours):
        info_points += 4
    elif len(hours) > 0:
        info_points += 2
        evidences.append("영업시간에 브레이크타임, 라스트오더, 정기휴무일 안내가 누락되었습니다.")
    else:
        info_points += 0
        evidences.append("영업시간 및 휴무일 정보가 등록되지 않아 헛걸음 우려가 있습니다.")
        
    directions = data.get("directions", "").strip()
    if len(directions) >= 40 and any(w in directions for w in ["역", "번 출구", "도보", "거리", "맞은편", "골목", "버스", "정류장"]):
        info_points += 4
    elif len(directions) >= 15:
        info_points += 2
        evidences.append("찾아오는 길이 너무 짧아 랜드마크나 도보 분수 안내를 보강해야 합니다.")
    else:
        info_points += 0
        evidences.append("찾아오는 길 상세 안내가 없어 고객이 지도 앱을 다시 켜야 하는 번거로움이 있습니다.")
        
    parking = data.get("parking", "").strip()
    if len(parking) >= 15 and any(w in parking for w in ["대", "무료", "유료", "전용", "주차장", "공영", "발렛", "가능"]):
        info_points += 4
    elif "주차" in parking or "가능" in parking:
        info_points += 2
        evidences.append("주차 가능 여부만 있고 수용 대수나 위치 안내가 없어 자차 고객의 망설임이 발생합니다.")
    else:
        info_points += 0
        evidences.append("주차 안내가 명시되지 않아 인근 공영주차장 지원 정보라도 등록해야 합니다.")
        
    scores["info"] = min(15, info_points)
    
    # -------------------------------------------------------------------------
    # 2. 소개글 & 특장점 키워드 (15점 만점)
    # -------------------------------------------------------------------------
    strengths_points = 0
    intro = data.get("intro", "").strip()
    intro_len = len(intro)
    
    if intro_len >= 250:
        strengths_points += 5
    elif intro_len >= 120:
        strengths_points += 3
        evidences.append(f"소개글이 {intro_len}자로 다소 짧습니다. 사장님의 철학과 공간 스토리를 250자 이상 보강하세요.")
    else:
        strengths_points += 1
        evidences.append(f"소개글이 {intro_len}자로 매우 부족하여 네이버 AI 검색(스마트블록) 연관도에서 불리합니다.")
        
    selected_strengths = data.get("selected_strengths", [])
    strength_evals = []
    
    for s_item in selected_strengths:
        label = s_item.get("label", "")
        in_intro = label in intro or any(syn in intro for syn in s_item.get("synonyms", []))
        has_numbers = bool(re.search(r'\d+', intro)) if in_intro else False
        
        if in_intro and has_numbers:
            s_score = 2
            s_eval = "반영 양호"
            s_desc = "소개글에 구체적인 수치(인원/대수/스펙)와 함께 명시됨"
        elif in_intro:
            s_score = 1
            s_eval = "부분 반영"
            s_desc = "소개글에 단순 언급만 있고 수용 인원·사진 등 증거 부족"
        else:
            s_score = 0
            s_eval = "미반영"
            s_desc = "소개글이나 주요 정보에 전혀 표현되지 않음"
            
        strength_evals.append({
            "label": label,
            "status": s_eval,
            "score": int(s_score / 2 * 100),
            "evidence": s_desc,
            "icon": s_item.get("icon", "⭐")
        })
        strengths_points += s_score
        
    keywords = data.get("keywords", [])
    if len(keywords) >= 5:
        strengths_points += 4
    elif len(keywords) >= 3:
        strengths_points += 2
    else:
        strengths_points += 1
        evidences.append("플레이스 대표 키워드가 5개 미만으로 등록되어 검색 노출 기회를 놓치고 있습니다.")
        
    scores["strengths"] = min(15, strengths_points)
    
    # -------------------------------------------------------------------------
    # 3. 메뉴 상세 & 메뉴 비주얼 (20점 만점)
    # -------------------------------------------------------------------------
    menu_points = 0
    menu_items = data.get("menu_items", [])
    menu_count = len(menu_items)
    
    # 대표/시그니처 메뉴 지정 (4점)
    has_signature = data.get("has_signature_menu", True)
    if has_signature and menu_count >= 1:
        menu_points += 4
    else:
        menu_points += 1
        evidences.append("대표/추천 시그니처 메뉴가 지정되지 않아 첫 방문 고객이 선택 장애를 겪습니다.")
        
    # 메뉴 사진 등록률 (6점)
    menu_photo_ratio = data.get("menu_photo_ratio", "전체 등록")
    if menu_photo_ratio == "전체 등록":
        menu_points += 6
    elif menu_photo_ratio == "일부 등록":
        menu_points += 3
        evidences.append("메뉴 일부에만 사진이 등록되어 있습니다. 전 메뉴 사진 등록 시 주문 전환율이 35% 상승합니다.")
    else:
        menu_points += 0
        evidences.append("메뉴 사진이 전혀 없습니다! 텍스트 메뉴판은 모바일 고객 이탈 1위 원인입니다.")
        
    # 메뉴별 매력적인 한 줄 설명 (6점)
    has_menu_desc = data.get("has_menu_desc", True)
    if has_menu_desc:
        menu_points += 6
    else:
        menu_points += 2
        evidences.append("대표 메뉴에 원산지, 식감, 조리 비법 등 매력적인 설명이 누락되어 있습니다.")
        
    # 전 메뉴 가격 투명성 (4점)
    has_menu_price = data.get("has_menu_price", True)
    if has_menu_price and menu_count >= 3:
        menu_points += 4
    elif has_menu_price:
        menu_points += 2
    else:
        menu_points += 0
        evidences.append("메뉴판에 가격이 표기되지 않은 항목(변동/시가)이 많아 고객이 부담을 느낍니다.")
        
    scores["menu"] = min(20, menu_points)
    
    # -------------------------------------------------------------------------
    # 4. 네이버 플레이스 특화 기능 (25점 만점)
    # -------------------------------------------------------------------------
    features_points = 0
    
    # 네이버 예약 (6점)
    if data.get("has_reservation", False):
        features_points += 6
    else:
        features_points += 1
        evidences.append("네이버 예약이 연동되지 않아 바쁜 시간대 예약 고객을 놓치고 있습니다.")
        
    # 스마트콜 050 / 통화연결음 (5점)
    if data.get("has_smart_call", False):
        features_points += 5
    else:
        features_points += 1
        evidences.append("스마트콜(050 번호) 및 통화연결음이 꺼져 있어 통화 중/부재중 고객에게 가게 정보를 전달하지 못합니다.")
        
    # 알림받기 혜택 (5점)
    if data.get("has_alert_benefit", False):
        features_points += 5
    else:
        features_points += 0
        evidences.append("‘알림받기’ 동의 혜택이 없어 신규 소식 및 쿠폰을 받아볼 단골 모객이 차단되어 있습니다.")
        
    # 플레이스 쿠폰 (5점)
    if data.get("has_coupon", False):
        features_points += 5
    else:
        features_points += 0
        evidences.append("발행된 플레이스 쿠폰이 없습니다. ‘저장하기’ 수를 폭발시키는 핵심 장치가 비어 있습니다.")
        
    # 네이버 톡톡 상담 (4점)
    if data.get("has_talktalk", False):
        features_points += 4
    else:
        features_points += 1
        evidences.append("네이버 톡톡 채팅 상담이 꺼져 있어 전화 통화를 꺼리는 MZ세대 문의가 차단됩니다.")
        
    scores["features"] = min(25, features_points)
    
    # -------------------------------------------------------------------------
    # 5. 리뷰 관리 & 사장님 답글 (15점 만점)
    # -------------------------------------------------------------------------
    reviews_points = 0
    
    # 최근 영수증 리뷰 및 포토 리뷰 비율 (5점)
    photo_review_level = data.get("photo_review_level", "보통")
    if photo_review_level == "높음":
        reviews_points += 5
    elif photo_review_level == "보통":
        reviews_points += 3
        evidences.append("최근 영수증 리뷰 중 포토 리뷰 비율이 다소 부족합니다. 포토 리뷰 유도 이벤트가 필요합니다.")
    else:
        reviews_points += 1
        evidences.append("영수증 리뷰 수가 적거나 텍스트 리뷰 위주여서 검색자 신뢰도가 떨어집니다.")
        
    # 사장님 답글 작성률 (6점)
    reply_rate = data.get("reply_rate", "거의 안 함")
    if reply_rate == "80% 이상":
        reviews_points += 6
    elif reply_rate == "50% 수준":
        reviews_points += 3
        evidences.append("사장님 답글 작성률이 50% 수준입니다. 미답글 리뷰에 적극적인 피드백을 권장합니다.")
    else:
        reviews_points += 0
        evidences.append("손님이 정성껏 남긴 리뷰에 사장님 답글이 방치되어 있습니다! (답글 작성률 40% 미만)")
        
    # 키워드 맞춤형 정성 답글 (4점)
    reply_quality = data.get("reply_quality", "정성 답글")
    if reply_rate != "거의 안 함" and reply_quality == "정성 답글":
        reviews_points += 4
    elif reply_rate != "거의 안 함":
        reviews_points += 2
        evidences.append("사장님 답글이 단순 복붙 매크로 문구 위주여서 고객의 감동을 이끌어내기 어렵습니다.")
    else:
        reviews_points += 0
        
    scores["reviews"] = min(15, reviews_points)
    
    # -------------------------------------------------------------------------
    # 6. 새소식 & 최신 운영 활성도 (10점 만점)
    # -------------------------------------------------------------------------
    news_points = 0
    if data.get("has_recent_news", False):
        news_points += 6
        if data.get("news_has_photo_link", True):
            news_points += 4
        else:
            news_points += 2
            evidences.append("새소식에 사진이나 쿠폰/예약 링크가 빠져 있어 읽고 난 후 행동 유도가 약합니다.")
    else:
        news_points += 1
        evidences.append("최근 30일 이내 새소식 발행 이력이 없습니다. 네이버 알고리즘은 활성 매장을 우선 추천합니다.")
        
    scores["news"] = min(10, news_points)
    
    # -------------------------------------------------------------------------
    # 종합 점수 및 등급 산정
    # -------------------------------------------------------------------------
    total_score = sum(scores.values())
    
    if total_score >= 85:
        grade = "S"
        grade_desc = "플레이스 최상위 운영 중! 미세 디테일만 다듬으면 1위 굳히기가 가능합니다."
    elif total_score >= 70:
        grade = "A"
        grade_desc = "기본기는 잘 갖춰졌어요. 고객 전환 장치와 리뷰 답글만 보강하면 순위가 뜁니다."
    elif total_score >= 50:
        grade = "B"
        grade_desc = "운영 준비가 절반 수준입니다. 기능 연동, 메뉴 사진, 리뷰 답글 등 핵심 항목의 보강이 필요합니다."
    else:
        grade = "C"
        grade_desc = "플레이스 방치 상태로 고객 유입이 크게 손실되고 있습니다. 필수 기능 활성화가 시급합니다."
        
    # 핵심 발견 (Field Note)
    field_note = generate_field_note(data, strength_evals, scores)
    
    # 이번 주 15분 우선순위 과제 TOP 3
    priority_tasks = generate_priority_tasks(data, scores)
    
    return {
        "total_score": total_score,
        "grade": grade,
        "grade_desc": grade_desc,
        "scores": scores,
        "strength_evals": strength_evals,
        "field_note": field_note,
        "evidences": evidences,
        "priority_tasks": priority_tasks
    }


def generate_field_note(data: Dict[str, Any], strength_evals: List[Dict[str, Any]], scores: Dict[str, int]) -> Dict[str, str]:
    """
    매장의 가장 아픈 구멍을 찌르는 팩트 기반 필드 노트
    """
    # 1. 리뷰 답글 방치 문제
    if scores["reviews"] <= 6:
        return {
            "title": "손님의 따뜻한 리뷰가 사장님의 무응답에 식어가고 있습니다.",
            "description": "네이버 알고리즘은 사장님이 직접 소통하는 매장을 높게 평가합니다. 정성스런 포토 리뷰에 사장님 감사 답글만 꾸준히 달아도 재방문율과 신규 검색 신뢰도가 급상승합니다.",
            "tag": "핵심 발견 / 리뷰 소통 단절"
        }
        
    # 2. 핵심 기능 부재
    if scores["features"] <= 12:
        return {
            "title": "손님을 모으는 네이버의 4대 무료 기능이 꺼져 있습니다.",
            "description": "스마트콜(050), 알림받기 전용 혜택, 플레이스 쿠폰, 네이버 예약이 누락되어 손님이 플레이스에 들어와도 '저장'하거나 '예약'하지 않고 이탈합니다.",
            "tag": "핵심 발견 / 고객 전환 장치 부재"
        }
        
    # 3. 메뉴 사진 누락
    if scores["menu"] <= 10:
        return {
            "title": "메뉴판에 사진과 설명이 없어 손님이 망설이고 있습니다.",
            "description": "손님은 텍스트보다 먹음직스러운 사진 한 장으로 메뉴를 결정합니다. 전 메뉴 사진 등록과 시그니처 스토리 보강이 시급합니다.",
            "tag": "핵심 발견 / 메뉴 비주얼 공백"
        }
        
    # 4. 강점 미반영
    weak_strengths = [s for s in strength_evals if s["status"] in ["부분 반영", "미반영"]]
    if weak_strengths:
        target = weak_strengths[0]["label"]
        return {
            "title": f"‘{target}’은 설명문에만 머물러 있습니다.",
            "description": f"수용 인원, 전용 메뉴, 좌석 사진, 예약 방법이 하나로 연결되지 않아 {target}을 찾는 고객이 결정을 미루고 다른 매장으로 이탈하고 있습니다.",
            "tag": "핵심 발견 / 특장점 단절"
        }
        
    return {
        "title": "기본기는 탄탄하지만, 검색 고객을 사로잡는 킬러 새소식이 필요합니다.",
        "description": "최근 30일간 새소식을 주기적으로 발행해 '지금도 핫하게 영업 중인 활성 매장'임을 네이버 검색엔진에 증명해야 합니다.",
        "tag": "핵심 발견 / 최신성 유지"
    }


def generate_priority_tasks(data: Dict[str, Any], scores: Dict[str, int]) -> List[Dict[str, Any]]:
    """
    사장님이 이번 주 15분 만에 스마트플레이스 센터에서 바꿀 수 있는 실전 과제
    """
    tasks = []
    
    # 1. 리뷰 답글 과제
    if scores["reviews"] <= 9:
        tasks.append({
            "id": 1,
            "title": "최근 1주일 포토 리뷰 5건에 사장님 정성 답글 남기기",
            "tag": "리뷰 관리",
            "time": "15분",
            "impact": "최상",
            "action": "단순 복붙 대신 '○○님 맛있게 드셔주셔서 감사합니다. 다음엔 ○○메뉴도 추천드려요!'처럼 손님 닉네임과 메뉴를 언급하며 따뜻한 답글을 다세요."
        })
        
    # 2. 알림받기 & 쿠폰 과제
    if not data.get("has_alert_benefit") or not data.get("has_coupon"):
        tasks.append({
            "id": 2,
            "title": "‘알림받기’ 설정 고객 전용 웰컴 쿠폰 1종 즉시 발행",
            "tag": "고객 전환",
            "time": "10분",
            "impact": "높음",
            "action": "스마트플레이스 센터 > 프로모션 > 쿠폰에서 '알림받기 한 고객에게 음료 1캔 무료' 쿠폰을 만들고 [저장 후 사용] 옵션을 켜세요."
        })
        
    # 3. 메뉴 사진 및 설명 보강
    if scores["menu"] <= 14:
        tasks.append({
            "id": 3,
            "title": "대표 메뉴 3개에 고화질 음식 사진 & 1줄 스토리 추가",
            "tag": "메뉴 디테일",
            "time": "20분",
            "impact": "높음",
            "action": "스마트폰으로 밝은 자연광에서 찍은 시그니처 메뉴 사진을 등록하고, '매일 새벽 우려낸 비법 육수' 같은 킬러 설명을 덧붙이세요."
        })
        
    # 4. 스마트콜 통화연결음
    if not data.get("has_smart_call"):
        tasks.append({
            "id": 4,
            "title": "스마트콜(050) 켜고 영업시간·위치 통화연결음 세팅",
            "tag": "스마트콜",
            "time": "10분",
            "impact": "중간",
            "action": "스마트플레이스 센터 > 스마트콜에서 050 번호를 발급받고, 바쁜 피크타임 안내 멘트와 통화 종료 후 매장 위치 자동 문자 발송을 켜세요."
        })
        
    # 5. 새소식 발행
    if not data.get("has_recent_news") and len(tasks) < 3:
        tasks.append({
            "id": 5,
            "title": "새소식 스튜디오에서 생성된 단체 모임 안내글 1건 등록",
            "tag": "새소식",
            "time": "15분",
            "impact": "중간",
            "action": "새소식 스튜디오 탭에서 생성된 단체석/주차 안내 초안을 복사해 플레이스 새소식에 사진 1장과 함께 올리세요."
        })
        
    return tasks[:3]
