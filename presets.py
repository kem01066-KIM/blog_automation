"""
Place Insight Pro - 검증된 실전 매장 프리셋 데이터 (확장 업그레이드 버전)
"""

PRESETS = {
    "수북오리 팔공점 (대구 동구 / 팔공산 맛집)": {
        "name": "수북오리 팔공점",
        "category": "오리요리 / 백숙",
        "region": "대구 동구 팔공산",
        "address": "대구 동구 파계로 603 (중대동 380)",
        "tel": "053-982-1234",
        "hours": "매일 11:00 ~ 21:00 (라스트오더 20:00 / 매주 화요일 정기휴무)",
        "directions": "파계사 삼거리 방향에서 파계로를 따라 1.5km 직진, 팔공산 자동차극장 맞은편 우측 큰 간판 진입로로 들어오시면 됩니다.",
        "parking": "대형 버스 및 승용차 50대 이상 동시 주차 가능한 넓은 전용 주차장 완비 (무료 주차)",
        "intro": "대구 팔공산의 맑은 공기 속에서 즐기는 생오리 숯불구이와 능이오리백숙 전문점입니다. 신선한 오리고기와 정갈한 반찬으로 모십니다.",
        "selected_strengths": [
            {"label": "단체 가능", "icon": "👥", "synonyms": ["단체석", "모임", "회식", "대형룸"]},
            {"label": "주차 편리", "icon": "🚗", "synonyms": ["전용 주차장", "주차장", "무료 주차"]},
            {"label": "아이 놀이방/마당", "icon": "🌿", "synonyms": ["놀이방", "족구장", "마당", "야외"]}
        ],
        "keywords": ["팔공산맛집", "팔공산오리백숙", "팔공산단체모임", "대구오리고기", "파계사맛집"],
        "photo_count": 14,
        # 메뉴 상세
        "has_signature_menu": True,
        "menu_photo_ratio": "일부 등록",
        "has_menu_desc": True,
        "has_menu_price": True,
        "menu_items": [
            {"name": "능이오리백숙", "price": "70,000원", "desc": "12가지 한약재와 능이버섯으로 진하게 우려낸 최고의 보양식 (3~4인용)"},
            {"name": "생오리 숯불구이", "price": "50,000원", "desc": "국내산 1등급 생오리만을 엄선해 참숯에 구워 먹는 담백한 구이"},
            {"name": "오리양념불고기", "price": "52,000원", "desc": "신선한 야채와 특제 천연 과일 양념으로 매콤달콤 볶아낸 인기 메뉴"},
            {"name": "오리훈제바베큐", "price": "55,000원", "desc": "기름기를 쏙 빼고 참나무 향을 가득 머금은 부드러운 훈제"}
        ],
        "amenities": ["단체석", "주차", "예약", "무선 인터넷", "남/녀 화장실 구분", "유아의자"],
        # 핵심 기능
        "has_reservation": True,
        "has_smart_call": True,
        "has_alert_benefit": False,
        "has_coupon": False,
        "has_talktalk": False,
        # 리뷰 및 답글
        "photo_review_level": "보통",
        "reply_rate": "거의 안 함",
        "reply_quality": "복붙 매크로",
        # 새소식
        "has_recent_news": True, # 10/24 발행 확인
        "news_has_photo_link": True,
        "competitors": [
            {"name": "수북오리 팔공점", "capacity": "미표기 (실제 100인)", "menu": "단품 4종 (일부 사진)", "features": "예약O · 쿠폰X · 알림X", "reply": "답글 5% (방치)", "news": "10/24 발행 (활성)"},
            {"name": "팔공산 A가든 (1위)", "capacity": "최대 120인 룸", "menu": "회식 코스 A/B (사진 100%)", "features": "예약O · 도토리묵쿠폰 · 알림혜택", "reply": "답글 92% (정성)", "news": "월 3회 발행"},
            {"name": "파계로 B식당 (2위)", "capacity": "최대 60인", "menu": "세트 3종 (사진 100%)", "features": "전화만 · 음료쿠폰", "reply": "답글 65%", "news": "월 1회 발행"}
        ]
    },
    "정든밥상 (서울 성수동 / 원래 데모 매장)": {
        "name": "정든밥상",
        "category": "한식 / 솥밥",
        "region": "서울 성동구 성수동",
        "address": "서울 성동구 성수일로 48 1층",
        "tel": "02-468-1234",
        "hours": "매일 11:30 ~ 21:30 (브레이크타임 15:00~17:00 / 일요일 휴무)",
        "directions": "성수역 3번 출구에서 성수카페거리 방면으로 도보 5분 직진",
        "parking": "매장 앞 2대 주차 가능 (협소, 인근 성수 공영주차장 이용 권장)",
        "intro": "정성 가득한 어머니의 집밥을 담은 성수동 솥밥 전문점입니다. 단체 가능하고 아이 놀이방이 있습니다.",
        "selected_strengths": [
            {"label": "단체 가능", "icon": "👥", "synonyms": ["단체석", "모임", "회식"]},
            {"label": "아이 놀이방", "icon": "👶", "synonyms": ["놀이방", "키즈존", "아기의자"]},
            {"label": "주차 편리", "icon": "🚗", "synonyms": ["주차장", "무료주차"]}
        ],
        "keywords": ["성수역맛집", "성수동한식", "성수동솥밥", "성수가족외식", "성수아이동반"],
        "photo_count": 18,
        # 메뉴 상세
        "has_signature_menu": True,
        "menu_photo_ratio": "전체 등록",
        "has_menu_desc": True,
        "has_menu_price": True,
        "menu_items": [
            {"name": "제육 솥밥 정식", "price": "14,000원", "desc": "불맛 가득한 제육볶음과 갓 지은 갓 도정 쌀 솥밥"},
            {"name": "보리굴비 솥밥 정식", "price": "22,000원", "desc": "영광 법성포 보리굴비와 시원한 녹차물 솥밥"},
            {"name": "소불고기 전골 (2인)", "price": "36,000원", "desc": "각종 버섯과 야채가 푸짐하게 들어간 달콤 짭조름한 전골"}
        ],
        "amenities": ["단체석", "포장", "유아의자", "무선 인터넷"],
        # 핵심 기능
        "has_reservation": False,
        "has_smart_call": False,
        "has_alert_benefit": False,
        "has_coupon": False,
        "has_talktalk": True,
        # 리뷰 및 답글
        "photo_review_level": "보통",
        "reply_rate": "50% 수준",
        "reply_quality": "정성 답글",
        # 새소식
        "has_recent_news": True, # 10/24 발행 확인
        "news_has_photo_link": True,
        "competitors": [
            {"name": "정든밥상", "capacity": "확인 필요", "menu": "정식 3종 (사진 100%)", "features": "예약X · 톡톡O · 쿠폰X", "reply": "답글 50%", "news": "10/24 발행 (활성)"},
            {"name": "성수 ○○식당 (1위)", "capacity": "최대 40인", "menu": "런치·회식 세트 (사진 100%)", "features": "예약O · 음료쿠폰 · 알림혜택", "reply": "답글 88% (정성)", "news": "월 2회 발행"},
            {"name": "골목 ○○ (2위)", "capacity": "최대 30인", "menu": "코스 3종", "features": "예약O · 사이드쿠폰", "reply": "답글 70%", "news": "10/24 발행 (활성)"}
        ]
    },
    "바로누수설비 (대구 서구 / 누수탐지 전문)": {
        "name": "바로누수설비",
        "category": "누수탐지 / 배관공사",
        "region": "대구 전지역",
        "address": "대구 서구 중리동 123",
        "tel": "010-1234-5678",
        "hours": "24시간 연중무휴 (야간 긴급출동 가능)",
        "directions": "대구 전지역 30분 이내 긴급 출동 방문 서비스 제공",
        "parking": "방문 현장 주차 가능",
        "intro": "30년 경력의 국가공인 설비 전문가가 직접 시공하는 대구 대표 누수탐지 전문업체입니다. 최첨단 가스탐지기와 청음기를 보유하고 있으며, 원인 못 찾으면 0원 원칙을 지킵니다. 아파트·빌라·공장 배관공사 및 일상배상책임보험 100% 무료 서류 대행을 지원합니다.",
        "selected_strengths": [
            {"label": "24시간 긴급출동", "icon": "🚨", "synonyms": ["긴급출동", "야간출동", "당일출동"]},
            {"label": "못 찾으면 0원", "icon": "💰", "synonyms": ["비용0원", "무료", "실패0원"]},
            {"label": "보험 서류 대행", "icon": "📋", "synonyms": ["일상배상", "보험처리", "보험서류"]}
        ],
        "keywords": ["대구누수", "대구누수탐지", "중리동누수", "대구배관공사", "대구방수"],
        "photo_count": 32,
        # 메뉴 상세
        "has_signature_menu": True,
        "menu_photo_ratio": "전체 등록",
        "has_menu_desc": True,
        "has_menu_price": True,
        "menu_items": [
            {"name": "미세 누수 정밀 탐지", "price": "300,000원~", "desc": "독일제 최첨단 가스탐지기 및 청음기 정밀 진단"},
            {"name": "배관 고압 세척 & 내시경", "price": "250,000원~", "desc": "막힌 하수구 및 배관 속을 100% 뚫어내는 고압세척"},
            {"name": "욕실 및 옥상 방수 공사", "price": "견적 상담", "desc": "우레탄 3중 특수 방수 도포 및 하자 보증 3년"}
        ],
        "amenities": ["주차", "방문출장", "예약"],
        # 핵심 기능
        "has_reservation": True,
        "has_smart_call": True,
        "has_alert_benefit": True,
        "has_coupon": True,
        "has_talktalk": True,
        # 리뷰 및 답글
        "photo_review_level": "높음",
        "reply_rate": "80% 이상",
        "reply_quality": "정성 답글",
        # 새소식
        "has_recent_news": True,
        "news_has_photo_link": True,
        "competitors": [
            {"name": "바로누수설비", "capacity": "대구 전지역", "menu": "시공 3종 (사진 100%)", "features": "예약O · 쿠폰O · 스마트콜O", "reply": "답글 95% (정성)", "news": "월 4회 발행"},
            {"name": "대구 1등 누수", "capacity": "대구·경북", "menu": "탐지 전문", "features": "예약O · 쿠폰X", "reply": "답글 40%", "news": "월 1회 발행"},
            {"name": "착한 설비", "capacity": "대구 전지역", "menu": "단품 시공", "features": "전화만", "reply": "답글 10%", "news": "10/24 발행 (활성)"}
        ]
    }
}
