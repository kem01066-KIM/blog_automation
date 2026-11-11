import sqlite3
import json
import os
import pandas as pd
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "atomy_crm.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            member_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            join_date TEXT NOT NULL,
            sponsor_id TEXT,
            line TEXT NOT NULL,
            status TEXT NOT NULL,
            interested_products TEXT,
            recent_order TEXT,
            notes TEXT,
            message_history TEXT DEFAULT '[]',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    
    # Check if empty, populate with rich sample data if so
    cursor.execute("SELECT COUNT(*) FROM members")
    count = cursor.fetchone()[0]
    if count == 0:
        seed_sample_data(conn)
    conn.close()

def seed_sample_data(conn):
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sample_members = [
        (
            "10000001", "김은숙", "010-1234-5678", "2026-01-15", "", "본인", "핵심파트너",
            "헤모힘, 앱솔루트 셀랙티브 전 라인", "앱솔루트 6종 (2026-11-01)",
            "팀 리더(본인). 좌·우 라인 균형 성장 및 파트너 후원 집중 관리 중.",
            json.dumps([{"date": "2026-11-01", "template": "시스템 공지", "content": "11월 팀 전략 미팅 안내"}], ensure_ascii=False),
            now, now
        ),
        (
            "10000002", "박지현", "010-2345-6789", "2026-06-10", "10000001", "좌측", "핵심파트너",
            "헤모힘, 홍삼단, 밀크씨슬", "헤모힘 4세트 (2026-10-28)",
            "좌측 라인 메인 리더. 매주 목요일 원데이 세미나 참석하며 신규 소비자 발굴 활발함.",
            json.dumps([{"date": "2026-11-05", "template": "세미나 공지", "content": "목요 세미나 일정 공유드립니다."}], ensure_ascii=False),
            now, now
        ),
        (
            "10000003", "이수진", "010-3456-7890", "2026-08-15", "10000002", "좌측", "재구매도래",
            "헤모힘, 이브닝케어 4종", "헤모힘 1세트 (2026-09-20)",
            "헤모힘 복용 2달 차. 곧 소진 시점이라 환절기 건강 안부 및 재구매 혜택 안내 타이밍임.",
            json.dumps([{"date": "2026-09-25", "template": "복용법 안내", "content": "헤모힘 따뜻한 물과 함께 섭취 안내"}], ensure_ascii=False),
            now, now
        ),
        (
            "10000004", "정미경", "010-4567-8901", "2026-10-02", "10000002", "좌측", "신규가입",
            "앱솔루트 스킨케어, 칫솔·치약", "치약 5개 세트 (2026-10-05)",
            "화장품 샘플 써보고 만족해 가입함. 모바일 쇼핑몰 로그인 및 결제 방법 안내 완료.",
            json.dumps([{"date": "2026-10-03", "template": "신규가입 환영", "content": "애터미 가족이 되신 것을 환영합니다!"}], ensure_ascii=False),
            now, now
        ),
        (
            "10000005", "김선옥", "010-5678-9012", "2026-10-20", "10000003", "좌측", "반응·관심자",
            "친애 유산균, 식물성 알래스카 오메가3", "유산균 1박스 (2026-10-22)",
            "건강기능식품 관심 많음. 지난번 가족 건강 문자 확인 후 오메가3 성분 문의해옴.",
            json.dumps([{"date": "2026-11-08", "template": "반응자 후속 케어", "content": "오메가3 원료 및 섭취 팁 공유"}], ensure_ascii=False),
            now, now
        ),
        (
            "10000006", "최영미", "010-6789-0123", "2026-07-01", "10000001", "우측", "핵심파트너",
            "앱솔루트 셀랙티브, 비타민C, 카페아라비카", "앱솔루트 6종 (2026-11-02)",
            "우측 라인 메인 사업자. 지인 카페 운영하며 자연스러운 제품 소개로 하위 소비자 탄탄함.",
            json.dumps([{"date": "2026-11-02", "template": "프로모션 공유", "content": "11월 프로모션 및 PV 적립 안내"}], ensure_ascii=False),
            now, now
        ),
        (
            "10000007", "강도현", "010-7890-1234", "2026-09-10", "10000006", "우측", "최근구매자",
            "남성 올인원 스킨, 밀크씨슬 듀얼케어", "밀크씨슬 2통 (2026-11-08)",
            "야외 영업직이라 피로 개선 관심. 지난주 배송받고 제품 만족도 높음 확인.",
            json.dumps([{"date": "2026-11-08", "template": "배송 안부", "content": "제품 잘 도착하셨는지 안부 인사"}], ensure_ascii=False),
            now, now
        ),
        (
            "10000008", "한상철", "010-8901-2345", "2026-10-15", "10000006", "우측", "반응·관심자",
            "헤모힘, 혈당케어 바나바", "바나바 혈당케어 (2026-10-18)",
            "당뇨 가족력 있어 혈당케어에 민감. 헤모힘 병용 섭취 효과 문의해 와서 상담 진행 중.",
            json.dumps([{"date": "2026-11-09", "template": "건강 정보", "content": "식후 혈당 상승 억제 생활 가이드 전달"}], ensure_ascii=False),
            now, now
        ),
        (
            "10000009", "윤서아", "010-9012-3456", "2026-11-05", "10000007", "우측", "신규가입",
            "딥퓨어 클렌징워터, 에어리선스틱", "선스틱 2개 (2026-11-06)",
            "SNS 릴스 보고 가입함. 20대 딸과 함께 쓸 순한 클렌징 제품 추가 탐색 중.",
            json.dumps([{"date": "2026-11-06", "template": "신규가입 환영", "content": "애터미 모바일 쇼핑몰 적립 팁 안내"}], ensure_ascii=False),
            now, now
        ),
    ]
    cursor.executemany("""
        INSERT INTO members (
            member_id, name, phone, join_date, sponsor_id, line, status,
            interested_products, recent_order, notes, message_history,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, sample_members)
    conn.commit()

def get_all_members():
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM members ORDER BY id ASC", conn)
    conn.close()
    return df

def get_member_by_id(member_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM members WHERE member_id = ?", (member_id,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def add_member(data):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    history = json.dumps(data.get("message_history", []), ensure_ascii=False)
    cursor.execute("""
        INSERT INTO members (
            member_id, name, phone, join_date, sponsor_id, line, status,
            interested_products, recent_order, notes, message_history,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(data["member_id"]).strip(),
        str(data["name"]).strip(),
        str(data["phone"]).strip(),
        str(data["join_date"]).strip(),
        str(data.get("sponsor_id", "")).strip(),
        str(data["line"]).strip(),
        str(data["status"]).strip(),
        str(data.get("interested_products", "")).strip(),
        str(data.get("recent_order", "")).strip(),
        str(data.get("notes", "")).strip(),
        history,
        now, now
    ))
    conn.commit()
    conn.close()

def update_member(member_id, data):
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        UPDATE members SET
            name = ?,
            phone = ?,
            join_date = ?,
            sponsor_id = ?,
            line = ?,
            status = ?,
            interested_products = ?,
            recent_order = ?,
            notes = ?,
            updated_at = ?
        WHERE member_id = ?
    """, (
        str(data["name"]).strip(),
        str(data["phone"]).strip(),
        str(data["join_date"]).strip(),
        str(data.get("sponsor_id", "")).strip(),
        str(data["line"]).strip(),
        str(data["status"]).strip(),
        str(data.get("interested_products", "")).strip(),
        str(data.get("recent_order", "")).strip(),
        str(data.get("notes", "")).strip(),
        now,
        str(member_id).strip()
    ))
    conn.commit()
    conn.close()

def delete_member(member_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM members WHERE member_id = ?", (str(member_id).strip(),))
    conn.commit()
    conn.close()

def append_message_history(member_id, template_name, content):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT message_history FROM members WHERE member_id = ?", (str(member_id).strip(),))
    row = cursor.fetchone()
    if row:
        history_raw = row[0]
        try:
            history = json.loads(history_raw) if history_raw else []
        except Exception:
            history = []
        new_entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "template": template_name,
            "content": content
        }
        history.append(new_entry)
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            UPDATE members SET message_history = ?, updated_at = ? WHERE member_id = ?
        """, (json.dumps(history, ensure_ascii=False), now, str(member_id).strip()))
        conn.commit()
    conn.close()

def reset_to_sample():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DROP TABLE IF EXISTS members")
    conn.commit()
    conn.close()
    init_db()
