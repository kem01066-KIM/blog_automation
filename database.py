import sqlite3
import os
import datetime
import csv
import io

DB_PATH = os.path.join(os.path.dirname(__file__), "influencers.db")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT NOT NULL,          -- 'naver' or 'instagram'
        name TEXT NOT NULL,
        handle TEXT NOT NULL,
        profile_url TEXT NOT NULL,
        post_url TEXT,
        title TEXT,
        snippet TEXT,
        category TEXT,
        purpose TEXT NOT NULL,           -- '공구' or '체험단'
        score INTEGER DEFAULT 80,
        status TEXT DEFAULT '검토중',     -- '검토중', '컨택완료', '협업확정', '보류'
        memo TEXT DEFAULT '',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(platform, handle, purpose)
    )
    """)
    conn.commit()
    conn.close()

def save_candidate(c: dict) -> bool:
    """후보를 DB에 저장합니다. 이미 존재하는 경우 업데이트합니다."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
        INSERT INTO candidates (
            platform, name, handle, profile_url, post_url, title, snippet, category, purpose, score, status, memo, created_at
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        ON CONFLICT(platform, handle, purpose) DO UPDATE SET
            name=excluded.name,
            profile_url=excluded.profile_url,
            post_url=excluded.post_url,
            title=excluded.title,
            snippet=excluded.snippet,
            score=excluded.score
        """, (
            c.get("platform", "naver"),
            c.get("name", ""),
            c.get("handle", ""),
            c.get("profile_url", ""),
            c.get("post_url", ""),
            c.get("title", ""),
            c.get("snippet", ""),
            c.get("category", "일반"),
            c.get("purpose", "공구"),
            c.get("score", 80),
            c.get("status", "검토중"),
            c.get("memo", ""),
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"DB Save error: {e}")
        return False
    finally:
        conn.close()

def get_saved_candidates(platform: str = "전체", purpose: str = "전체", status: str = "전체") -> list:
    """저장된 인플루언서 후보 목록을 조회합니다."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM candidates WHERE 1=1"
    params = []
    
    if platform != "전체":
        query += " AND platform = ?"
        params.append("naver" if platform == "네이버 블로그" else "instagram")
    if purpose != "전체":
        query += " AND purpose = ?"
        params.append(purpose)
    if status != "전체":
        query += " AND status = ?"
        params.append(status)
        
    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    results = [dict(r) for r in rows]
    conn.close()
    return results

def update_candidate(cand_id: int, status: str, memo: str) -> bool:
    """후보 상태 및 메모를 업데이트합니다."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE candidates SET status = ?, memo = ? WHERE id = ?", (status, memo, cand_id))
        conn.commit()
        return True
    except Exception as e:
        print(f"DB Update error: {e}")
        return False
    finally:
        conn.close()

def delete_candidate(cand_id: int) -> bool:
    """후보를 삭제합니다."""
    init_db()
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM candidates WHERE id = ?", (cand_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"DB Delete error: {e}")
        return False
    finally:
        conn.close()

def export_candidates_csv(candidates: list) -> str:
    """후보 목록을 CSV 텍스트로 내보냅니다."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "플랫폼", "이름", "아이디/핸들", "목적", "적합도점수", "진행상태", "프로필링크", "최신글링크", "메모", "저장일시"])
    for c in candidates:
        writer.writerow([
            c.get("id", ""),
            "네이버 블로그" if c.get("platform") == "naver" else "인스타그램",
            c.get("name", ""),
            c.get("handle", ""),
            c.get("purpose", ""),
            f"{c.get('score', 0)}점",
            c.get("status", "검토중"),
            c.get("profile_url", ""),
            c.get("post_url", ""),
            c.get("memo", ""),
            c.get("created_at", "")
        ])
    return output.getvalue()
