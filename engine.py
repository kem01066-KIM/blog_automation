"""
Place Insight Pro - 네이버 스마트플레이스 정밀 운영 진단 엔진
"""

import re
from typing import Dict, List, Any

def calculate_place_audit(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    네이버 스마트플레이스 운영 데이터 기반 100점 만점 정밀 진단 계산
    """
    scores = {
        "info": 0,        # 정보 정확성 & 완성도 (25점)
        "strengths": 0,   # 특장점 반영도 (25점)
        "content": 0,     # 비주얼 & 메뉴 콘텐츠 (25점)
        "conversion": 0   # 고객 전환 장치 (25점)
    }
    
    evidences = []
    tasks = []
    
    # 1. 정보 정확성 (25점 만점)
    info_points = 0
    # 주소 및 전화번호 (5점)
    if data.get("address") and data.get("tel"):
        info_points += 5
    elif data.get("address"):
        info_points += 3
        evidences.append("대표 전화번호가 누락되었거나 안심번호 설정이 필요합니다.")
        
    # 영업시간 및 휴무일 (5점)
    hours = data.get("hours", "").strip()
    if len(hours) >= 15 and ("휴무" in hours or "매일" in hours or "요일" in hours):
        info_points += 5
    elif len(hours) > 0:
        info_points += 3
        evidences.append("영업시간에 브레이크타임, 라스트오더, 정기휴무일 안내가 누락되어 문의 전화 피로가 발생할 수 있습니다.")
    else:
        info_points += 1
        evidences.append("영업시간 및 휴무일 정보가 등록되지 않아 헛걸음 우려가 있습니다.")
        
    # 찾아오는 길 상세도 (5점)
    directions = data.get("directions", "").strip()
    if len(directions) >= 40 and any(w in directions for w in ["역", "번 출구", "도보", "거리", "맞은편", "골목", "버스", "정류장"]):
        info_points += 5
    elif len(directions) >= 15:
        info_points += 3
        evidences.append("찾아오는 길이 너무 짧아 랜드마크나 도보 분수 안내를 보강해야 합니다.")
    else:
        info_points += 1
        evidences.append("찾아오는 길 상세 안내가 없어 고객이 지도 앱을 다시 켜야 하는 번거로움이 있습니다.")
        
    # 주차 안내 (5점)
    parking = data.get("parking", "").strip()
    if len(parking) >= 15 and any(w in parking for w in ["대", "무료", "유료", "전용", "주차장", "공영", "발렛", "가능"]):
        info_points += 5
    elif "주차" in parking or "가능" in parking:
        info_points += 3
        evidences.append("주차 가능 여부만 있고 수용 대수나 위치 안내가 없어 자차 고객의 망설임이 발생합니다.")
    else:
        info_points += 0
        evidences.append("주차 안내가 명시되지 않아 인근 공영주차장 지원 정보라도 등록해야 합니다.")
        
    # 편의시설 및 부가정보 (5점)
    amenities = data.get("amenities", [])
    if len(amenities) >= 4:
        info_points += 5
    elif len(amenities) >= 2:
        info_points += 3
    else:
        info_points += 1
        evidences.append("단체석, 예약, 무선인터넷, 유아의자 등 편의시설 태그가 부족합니다.")
        
    scores["info"] = min(25, info_points)
    
    # 2. 특장점 반영도 (25점 만점)
    strengths_points = 0
    intro = data.get("intro", "").strip()
    intro_len = len(intro)
    
    # 소개글 분량 (7점)
    if intro_len >= 250:
        strengths_points += 7
    elif intro_len >= 120:
        strengths_points += 5
        evidences.append(f"소개글이 {intro_len}자로 다소 짧습니다. 사장님의 철학과 공간 스토리를 250자 이상 보강하세요.")
    else:
        strengths_points += 2
        evidences.append(f"소개글이 {intro_len}자로 매우 부족하여 네이버 AI 검색(스마트블록) 연관도에서 불리합니다.")
        
    # 사장님이 선택한 3대 강점 분석 (각 4점씩 12점)
    selected_strengths = data.get("selected_strengths", [])
    strength_evals = []
    
    for s_item in selected_strengths:
        label = s_item.get("label", "")
        # 점검: 소개글 언급 여부, 구체적 수치(숫자) 언급 여부, 사진/메뉴 언급 여부
        in_intro = label in intro or any(syn in intro for syn in s_item.get("synonyms", []))
        has_numbers = bool(re.search(r'\d+', intro)) if in_intro else False
        
        if in_intro and has_numbers:
            s_score = 4
            s_eval = "반영 양호"
            s_desc = "소개글에 구체적인 수치(인원/대수/스펙)와 함께 명시됨"
        elif in_intro:
            s_score = 2
            s_eval = "부분 반영"
            s_desc = "소개글에 단순 언급만 있고 수용 인원·사진 등 증거 부족"
        else:
            s_score = 0
            s_eval = "미반영"
            s_desc = "소개글이나 주요 정보에 전혀 표현되지 않음"
            
        strength_evals.append({
            "label": label,
            "status": s_eval,
            "score": int(s_score / 4 * 100),
            "evidence": s_desc,
            "icon": s_item.get("icon", "⭐")
        })
        strengths_points += s_score
        
    # 대표 키워드 5개 등록 (6점)
    keywords = data.get("keywords", [])
    if len(keywords) >= 5:
        strengths_points += 6
    elif len(keywords) >= 3:
        strengths_points += 4
    else:
        strengths_points += 2
        evidences.append("플레이스 대표 키워드가 5개 미만으로 등록되어 검색 노출 기회를 놓치고 있습니다.")
        
    scores["strengths"] = min(25, strengths_points)
    
    # 3. 비주얼 & 메뉴 콘텐츠 (25점 만점)
    content_points = 0
    photo_count = data.get("photo_count", 0)
    
    # 사진 수 (10점)
    if photo_count >= 25:
        content_points += 10
    elif photo_count >= 12:
        content_points += 7
        evidences.append(f"등록 사진이 {photo_count}장입니다. 공간·인테리어·단체석 사진을 25장 이상 채우는 것이 유리합니다.")
    else:
        content_points += 3
        evidences.append(f"등록 사진이 {photo_count}장으로 매우 적습니다. 고객은 사진으로 매장의 분위기를 판단합니다.")
        
    # 메뉴판 가격 및 설명 (15점)
    menu_count = len(data.get("menu_items", []))
    has_menu_desc = any(bool(m.get("desc")) for m in data.get("menu_items", []))
    has_menu_photos = data.get("has_menu_photos", True)
    
    if menu_count >= 5:
        content_points += 5
    elif menu_count >= 1:
        content_points += 3
    else:
        content_points += 1
        evidences.append("메뉴가 등록되지 않았거나 1~2개뿐입니다.")
        
    if has_menu_desc:
        content_points += 5
    else:
        content_points += 2
        evidences.append("대표 메뉴에 매력적인 한 줄 설명(원산지, 조리법, 맛 포인트)이 없습니다.")
        
    if has_menu_photos:
        content_points += 5
    else:
        content_points += 1
        evidences.append("메뉴 사진이 등록되지 않아 텍스트만 보입니다. 메뉴 사진 등록이 시급합니다.")
        
    scores["content"] = min(25, content_points)
    
    # 4. 고객 전환 장치 (25점 만점)
    conversion_points = 0
    
    # 네이버 예약 (7점)
    if data.get("has_reservation", False):
        conversion_points += 7
    else:
        conversion_points += 1
        evidences.append("네이버 예약이 연동되지 않아 전화 통화가 어려운 상황에서 고객 이탈이 발생합니다.")
        
    # 네이버 톡톡 상담 (5점)
    if data.get("has_talktalk", False):
        conversion_points += 5
    else:
        conversion_points += 1
        evidences.append("네이버 톡톡이 꺼져 있어 실시간 채팅 문의 고객을 놓치고 있습니다.")
        
    # 플레이스 쿠폰 (6점)
    if data.get("has_coupon", False):
        conversion_points += 6
    else:
        conversion_points += 0
        evidences.append("발행된 플레이스 쿠폰이 없습니다. '첫 방문 음료 쿠폰' 등은 '저장하기' 수를 폭발시키는 핵심 장치입니다.")
        
    # 최근 30일 이내 새소식 (7점)
    if data.get("has_recent_news", False):
        conversion_points += 7
    else:
        conversion_points += 1
        evidences.append("최근 30일 이내 새소식 발행 이력이 없습니다. 네이버 알고리즘은 활성 매장을 우선 추천합니다.")
        
    scores["conversion"] = min(25, conversion_points)
    
    # 종합 점수 계산
    total_score = sum(scores.values())
    
    if total_score >= 85:
        grade = "S"
        grade_desc = "플레이스 최상위 운영 중! 미세 디테일만 다듬으면 1위 굳히기가 가능합니다."
    elif total_score >= 70:
        grade = "A"
        grade_desc = "기본기는 잘 갖춰졌어요. 고객 전환 장치와 특장점 증거만 보강하면 순위가 뜁니다."
    elif total_score >= 50:
        grade = "B"
        grade_desc = "운영 준비가 절반 수준입니다. 소개글·사진·쿠폰 등 핵심 항목의 집중 보강이 필요합니다."
    else:
        grade = "C"
        grade_desc = "플레이스 방치 상태로 고객 유입이 크게 손실되고 있습니다. 필수 정보 재정비가 시급합니다."
        
    # 핵심 발견 (Field Note 01)
    field_note = generate_field_note(data, strength_evals, scores)
    
    # 이번 주 15분 액션 플랜 TOP 3 생성
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
    store_name = data.get("name", "매장")
    
    # 약점 강점 찾기
    weak_strengths = [s for s in strength_evals if s["status"] in ["부분 반영", "미반영"]]
    
    if weak_strengths:
        target = weak_strengths[0]["label"]
        return {
            "title": f"‘{target}’은 설명문에만 머물러 있습니다.",
            "description": f"수용 인원, 전용 메뉴, 좌석 사진, 예약 방법이 하나로 연결되지 않아 {target}을 찾는 고객이 결정을 미루고 다른 매장으로 이탈하고 있습니다.",
            "tag": "핵심 발견 / 특장점 단절"
        }
    elif not data.get("has_recent_news"):
        return {
            "title": "가게 문은 열려 있는데, 플레이스는 잠들어 보입니다.",
            "description": "최근 30일간 새소식 업데이트가 없어 고객이 '지금도 영업하나?', '예약이 되나?' 의구심을 갖게 됩니다. 살아있는 가게임을 새소식으로 보여주어야 합니다.",
            "tag": "핵심 발견 / 신선도 저하"
        }
    elif not data.get("has_coupon"):
        return {
            "title": "방문 고객을 '단골'과 '저장'으로 묶을 미끼가 없습니다.",
            "description": "상위 1~3위 경쟁업체는 모두 플레이스 쿠폰(음료·사이드 증정)으로 고객의 '플레이스 저장하기'를 유도해 검색 순위 가산점을 챙기고 있습니다.",
            "tag": "핵심 발견 / 전환 장치 부재"
        }
    else:
        return {
            "title": "기본기는 탄탄하지만, 검색 고객을 압도하는 킬러 콘텐츠가 부족합니다.",
            "description": "단골 손님들의 생생한 포토 리뷰와 시그니처 메뉴의 맛있는 스토리를 새소식에 주기적으로 노출해 검색 방문 전환율을 극대화해야 합니다.",
            "tag": "핵심 발견 / 킬러 콘텐츠"
        }


def generate_priority_tasks(data: Dict[str, Any], scores: Dict[str, int]) -> List[Dict[str, Any]]:
    """
    사장님이 이번 주 15분~25분 만에 스마트플레이스 센터에서 바꿀 수 있는 실전 과제
    """
    tasks = []
    
    # 1. 특장점/소개글 과제
    if scores["strengths"] < 20:
        tasks.append({
            "id": 1,
            "title": "소개글 첫 3줄에 '수용 인원·주차 대수·예약 방법' 숫자 명시",
            "tag": "특장점 보강",
            "time": "15분",
            "impact": "높음",
            "action": "‘단체 가능’ 대신 ‘최대 40인 단체룸 완비, 전용 주차장 30대, 네이버 1초 간편 예약 가능’처럼 숫자로 명확히 바꿔 적으세요."
        })
        
    # 2. 쿠폰 발행 과제
    if not data.get("has_coupon"):
        tasks.append({
            "id": 2,
            "title": "‘저장하기’ 유도용 플레이스 웰컴 쿠폰 1종 즉시 발행",
            "tag": "고객 전환",
            "time": "10분",
            "impact": "높음",
            "action": "스마트플레이스 센터 > 프로모션 > 쿠폰에서 ‘음료 1캔 무료’ 또는 ‘테이블당 2,000원 할인’ 쿠폰을 만들고 [저장 후 사용] 옵션을 켜세요."
        })
        
    # 3. 새소식 발행 과제
    if not data.get("has_recent_news"):
        tasks.append({
            "id": 3,
            "title": "이번 주 매장 공간/메뉴 사진 1장 넣고 새소식 1건 발행",
            "tag": "노출 활성",
            "time": "15분",
            "impact": "중간",
            "action": "새소식 스튜디오에서 생성된 단체 모임 안내 초안을 복사해 플레이스 새소식에 사진 1장과 함께 등록하세요."
        })
        
    # 4. 찾아오는 길/주차 과제
    if scores["info"] < 20 and len(tasks) < 3:
        tasks.append({
            "id": 4,
            "title": "‘찾아오는 길’에 지하철/랜드마크 기준 도보 분수 기재",
            "tag": "정보 정확성",
            "time": "10분",
            "impact": "중간",
            "action": "‘○○역 ○번 출구에서 ○○은행 방향 도보 3분’처럼 길치 고객도 한 번에 찾아오게 상세 도보 동선을 적어두세요."
        })
        
    # 5. 대표사진 교체 과제
    if len(tasks) < 3:
        tasks.append({
            "id": 5,
            "title": "대표사진 1순위를 ‘음식 단독’에서 ‘공간+시그니처 상차림’으로 교체",
            "tag": "콘텐츠",
            "time": "20분",
            "impact": "높음",
            "action": "검색 결과 썸네일에서 손님이 매장의 규모와 쾌적함을 바로 느낄 수 있는 와이드 상차림 사진을 1번 대표사진으로 지정하세요."
        })
        
    return tasks[:3]
