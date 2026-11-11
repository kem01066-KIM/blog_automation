"""
소상공인 안드로이드 스마트 콜백 매니저 (Smart Callback Pro) - Database Engine
SQLite 기반 설정 관리, 발송 룰 검증, 콜백 로그 및 통계 엔진
"""

import sqlite3
import os
import json
from datetime import datetime, date

DB_PATH = os.path.join(os.path.dirname(__file__), "callback.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # 1. 설정 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            id INTEGER PRIMARY KEY,
            shop_name TEXT NOT NULL DEFAULT '수북오리 팔공점',
            category TEXT NOT NULL DEFAULT '식당/맛집',
            phone TEXT NOT NULL DEFAULT '053-982-1234',
            address TEXT NOT NULL DEFAULT '대구 동구 중대동 380',
            place_url TEXT NOT NULL DEFAULT 'https://naver.me/subuk_sample',
            business_hours TEXT NOT NULL DEFAULT '매일 11:30 ~ 21:30 (라스트오더 20:30)',
            extra_info TEXT DEFAULT '주차 30대 가능 / 단체룸 완비',
            msg_normal TEXT NOT NULL,
            msg_missed TEXT NOT NULL,
            msg_holiday TEXT NOT NULL,
            enable_normal INTEGER NOT NULL DEFAULT 1,
            enable_missed INTEGER NOT NULL DEFAULT 1,
            enable_holiday INTEGER NOT NULL DEFAULT 0,
            limit_per_day INTEGER NOT NULL DEFAULT 1,
            delay_seconds INTEGER NOT NULL DEFAULT 3,
            blacklist_numbers TEXT DEFAULT '010-0000-0000, 010-1234-5678',
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 2. 발송 로그 테이블
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS callback_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT NOT NULL,
            call_type TEXT NOT NULL, -- 'normal', 'missed', 'holiday'
            message TEXT NOT NULL,
            status TEXT NOT NULL, -- 'SENT', 'BLOCKED_DUPLICATE', 'BLOCKED_BLACKLIST', 'DISABLED'
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # 기본 설정 존재 여부 확인 및 초기 시드 주입
    cursor.execute("SELECT COUNT(*) FROM settings WHERE id = 1")
    if cursor.fetchone()[0] == 0:
        default_normal = (
            "[{가게명} 안내]\n"
            "방금 통화 감사드립니다. 고객님!\n\n"
            "저희 매장 위치와 주요 정보 안내해 드립니다.\n\n"
            "📍 오시는 길: {주소}\n"
            "⏰ 영업시간: {영업시간}\n"
            "🚗 전용 주차장: {기타안내}\n\n"
            "📌 네이버 플레이스 (사진/메뉴/예약):\n"
            "{플레이스링크}\n\n"
            "오실 때 불편하신 점 있으시면 언제든 편하게 말씀해 주세요. 정성껏 모시겠습니다! 감사합니다."
        )
        default_missed = (
            "[{가게명} 부재중 안내]\n"
            "전화를 주셨는데 바로 받지 못해 대단히 죄송합니다.\n\n"
            "현재 매장 조리 및 고객 응대 중이라 신속히 전화를 받지 못했습니다. 확인하는 대로 바로 연락드리겠습니다!\n\n"
            "급한 예약이나 문의 사항은 본 번호로 [성함/인원/날짜]를 문자로 남겨주시면 더 빠르게 확인해 드리겠습니다.\n\n"
            "📌 매장 위치 및 메뉴 안내:\n"
            "{플레이스링크}"
        )
        default_holiday = (
            "[{가게명} 영업 외 시간 안내]\n"
            "안녕하세요. {가게명}입니다.\n\n"
            "현재는 매장 마감 및 휴무 시간입니다.\n"
            "⏰ 정상 영업시간: {영업시간}\n\n"
            "문의 사항을 문자로 남겨주시면 다음 영업일 오전 오픈 즉시 연락드리겠습니다. 감사합니다!"
        )

        cursor.execute("""
            INSERT INTO settings (
                id, shop_name, category, phone, address, place_url, business_hours, extra_info,
                msg_normal, msg_missed, msg_holiday, enable_normal, enable_missed, enable_holiday,
                limit_per_day, delay_seconds, blacklist_numbers
            ) VALUES (
                1, '수북오리 팔공점', '식당/맛집', '053-982-1234', '대구 동구 중대동 380',
                'https://naver.me/subuk_sample', '매일 11:30 ~ 21:30 (라스트오더 20:30)',
                '주차 30대 가능 / 단체룸 완비',
                ?, ?, ?, 1, 1, 0, 1, 3, '010-0000-0000, 010-1234-5678'
            )
        """, (default_normal, default_missed, default_holiday))

        sample_logs = [
            ("010-1234-5678", "normal", default_normal, "SENT", "통화 종료 후 3초 정상 발송 완료"),
            ("010-9876-5432", "missed", default_missed, "SENT", "부재중 전화 감지 즉시 자동 안내 발송"),
            ("010-1234-5678", "normal", default_normal, "BLOCKED_DUPLICATE", "동일 번호 1일 1회 발송 제한 규칙으로 차단"),
        ]
        for phone, c_type, msg, status, note in sample_logs:
            cursor.execute("""
                INSERT INTO callback_logs (phone_number, call_type, message, status, note)
                VALUES (?, ?, ?, ?, ?)
            """, (phone, c_type, msg, status, note))

    conn.commit()
    conn.close()


def get_settings():
    init_db()
    conn = get_connection()
    row = conn.execute("SELECT * FROM settings WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else {}


def update_settings(data: dict):
    init_db()
    current = get_settings()
    # 병합
    merged = {**current, **data}

    conn = get_connection()
    conn.execute("""
        UPDATE settings SET
            shop_name = ?,
            category = ?,
            phone = ?,
            address = ?,
            place_url = ?,
            business_hours = ?,
            extra_info = ?,
            msg_normal = ?,
            msg_missed = ?,
            msg_holiday = ?,
            enable_normal = ?,
            enable_missed = ?,
            enable_holiday = ?,
            limit_per_day = ?,
            delay_seconds = ?,
            blacklist_numbers = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = 1
    """, (
        merged.get("shop_name", ""),
        merged.get("category", "기타"),
        merged.get("phone", ""),
        merged.get("address", ""),
        merged.get("place_url", ""),
        merged.get("business_hours", ""),
        merged.get("extra_info", ""),
        merged.get("msg_normal", ""),
        merged.get("msg_missed", ""),
        merged.get("msg_holiday", ""),
        int(merged.get("enable_normal", 1)),
        int(merged.get("enable_missed", 1)),
        int(merged.get("enable_holiday", 0)),
        int(merged.get("limit_per_day", 1)),
        int(merged.get("delay_seconds", 3)),
        merged.get("blacklist_numbers", "")
    ))
    conn.commit()
    conn.close()


def normalize_phone(phone: str) -> str:
    cleaned = "".join([c for c in phone if c.isdigit()])
    if len(cleaned) == 11 and cleaned.startswith("010"):
        return f"{cleaned[:3]}-{cleaned[3:7]}-{cleaned[7:]}"
    elif len(cleaned) == 10 and cleaned.startswith("01"):
        return f"{cleaned[:3]}-{cleaned[3:6]}-{cleaned[6:]}"
    return phone.strip()


def check_can_send(phone_number: str, call_type: str = "normal"):
    settings = get_settings()
    norm_phone = normalize_phone(phone_number)

    # 1. 유형별 활성화 검사
    if call_type == "normal" and not settings.get("enable_normal"):
        return False, "DISABLED", "정상 통화 후 콜백 발송이 비활성화되어 있습니다."
    if call_type == "missed" and not settings.get("enable_missed"):
        return False, "DISABLED", "부재중 전화 콜백 발송이 비활성화되어 있습니다."
    if call_type == "holiday" and not settings.get("enable_holiday"):
        return False, "DISABLED", "영업 외 시간 콜백 발송이 비활성화되어 있습니다."

    # 2. 제외 번호(블랙리스트) 검사
    blacklist_raw = settings.get("blacklist_numbers", "")
    blacklist = [normalize_phone(num) for num in blacklist_raw.replace("\n", ",").split(",") if num.strip()]
    if norm_phone in blacklist:
        return False, "BLOCKED_BLACKLIST", f"제외 번호 목록(가족/직원/지인)에 등록된 번호입니다: {norm_phone}"

    # 3. 1일 1회 발송 제한 검사
    if settings.get("limit_per_day"):
        conn = get_connection()
        today_str = date.today().isoformat()
        row = conn.execute("""
            SELECT COUNT(*) FROM callback_logs
            WHERE phone_number = ? AND status = 'SENT' AND date(created_at) = ?
        """, (norm_phone, today_str)).fetchone()
        conn.close()

        if row and row[0] > 0:
            return False, "BLOCKED_DUPLICATE", f"동일 번호로 오늘 이미 발송 이력이 있습니다 ({row[0]}회 발송됨). 스팸 방지 차단."

    return True, "SENT", "발송 규칙 통과: 정상 발송 가능"


def record_log(phone_number: str, call_type: str, message: str, status: str, note: str = ""):
    init_db()
    norm_phone = normalize_phone(phone_number)
    conn = get_connection()
    conn.execute("""
        INSERT INTO callback_logs (phone_number, call_type, message, status, note)
        VALUES (?, ?, ?, ?, ?)
    """, (norm_phone, call_type, message, status, note))
    conn.commit()
    conn.close()


def get_logs(limit: int = 100, search: str = ""):
    init_db()
    conn = get_connection()
    if search:
        query = f"%{search}%"
        rows = conn.execute("""
            SELECT * FROM callback_logs
            WHERE phone_number LIKE ? OR message LIKE ? OR note LIKE ?
            ORDER BY id DESC LIMIT ?
        """, (query, query, query, limit)).fetchall()
    else:
        rows = conn.execute("""
            SELECT * FROM callback_logs
            ORDER BY id DESC LIMIT ?
        """, (limit,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stats():
    init_db()
    conn = get_connection()
    today_str = date.today().isoformat()

    total_all = conn.execute("SELECT COUNT(*) FROM callback_logs").fetchone()[0]
    sent_today = conn.execute(
        "SELECT COUNT(*) FROM callback_logs WHERE status = 'SENT' AND date(created_at) = ?", (today_str,)
    ).fetchone()[0]
    blocked_today = conn.execute(
        "SELECT COUNT(*) FROM callback_logs WHERE status != 'SENT' AND date(created_at) = ?", (today_str,)
    ).fetchone()[0]
    normal_today = conn.execute(
        "SELECT COUNT(*) FROM callback_logs WHERE status = 'SENT' AND call_type = 'normal' AND date(created_at) = ?", (today_str,)
    ).fetchone()[0]
    missed_today = conn.execute(
        "SELECT COUNT(*) FROM callback_logs WHERE status = 'SENT' AND call_type = 'missed' AND date(created_at) = ?", (today_str,)
    ).fetchone()[0]

    conn.close()
    return {
        "total_all": total_all,
        "sent_today": sent_today,
        "blocked_today": blocked_today,
        "normal_today": normal_today,
        "missed_today": missed_today,
    }


def clear_logs():
    init_db()
    conn = get_connection()
    conn.execute("DELETE FROM callback_logs")
    conn.commit()
    conn.close()
