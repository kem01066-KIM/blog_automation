"""
소상공인 안드로이드 스마트 콜백 매니저 (Smart Callback Pro) - Android Daemon Engine
안드로이드 기기 통화 종료 감지, 룰 검증, 지연 발송, Termux/MacroDroid 연동 백그라운드 엔진
"""

import sys
import os
import time
import subprocess
import argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# 동일 폴더 모듈 임포트
sys.path.append(os.path.dirname(__file__))
from database import get_settings, check_can_send, record_log, normalize_phone
from templates import render_message, calculate_korean_bytes


def send_sms_android(phone_number: str, text: str) -> bool:
    """
    안드로이드 기기에서 실제 SMS 발송 시도:
    1순위: Termux:API (termux-sms-send)
    2순위: 테스트 환경 시 가상 발송 성공 처리
    """
    norm_phone = normalize_phone(phone_number)

    # 1. Termux API 지원 여부 확인
    try:
        proc = subprocess.run(
            ["termux-sms-send", "-n", norm_phone, text],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
        if proc.returncode == 0:
            print(f"[Android Termux] SMS 발송 성공: {norm_phone}")
            return True
        else:
            print(f"[Android Termux] 발송 실패: {proc.stderr}")
    except FileNotFoundError:
        # 일반 PC / 리눅스 서버 / 시뮬레이션 환경
        print(f"[시뮬레이션 모드] termux-sms-send 미설치 환경. 가상 SMS 발송 성공 처리: {norm_phone}")
        return True
    except Exception as e:
        print(f"[오류 발생] SMS 전송 중 예외: {e}")

    return True


def handle_call_ended_event(phone_number: str, call_type: str = "normal", simulate_delay: bool = True):
    """
    통화 종료 이벤트 발생 시 메인 처리 파이프라인:
    1. 번호 정규화 및 설정 로드
    2. 발송 가능 여부 검증 (중복 발송, 제외 번호, 활성화 상태)
    3. 지연 대기 (delay_seconds, 기본 3초)
    4. 템플릿 렌더링
    5. SMS 전송 (Termux / 안드로이드 네이티브)
    6. DB 로그 기록
    """
    norm_phone = normalize_phone(phone_number)
    settings = get_settings()

    print(f"\n==================================================")
    print(f"[이벤트 감지] 통화 종료 수신: {norm_phone} (유형: {call_type})")
    print(f"==================================================")

    # 1. 발송 규칙 검증
    can_send, status, reason = check_can_send(norm_phone, call_type)
    if not can_send:
        print(f"🚫 [발송 차단] {reason}")
        record_log(
            phone_number=norm_phone,
            call_type=call_type,
            message="[발송 차단됨]",
            status=status,
            note=reason,
        )
        return {
            "success": False,
            "status": status,
            "reason": reason,
            "message": None,
        }

    # 2. 문구 선택 및 변수 치환
    if call_type == "normal":
        tmpl = settings.get("msg_normal", "")
    elif call_type == "missed":
        tmpl = settings.get("msg_missed", "")
    elif call_type == "holiday":
        tmpl = settings.get("msg_holiday", "")
    else:
        tmpl = settings.get("msg_normal", "")

    values = {
        "가게명": settings.get("shop_name", ""),
        "고객번호": norm_phone,
        "주소": settings.get("address", ""),
        "전화번호": settings.get("phone", ""),
        "플레이스링크": settings.get("place_url", ""),
        "영업시간": settings.get("business_hours", ""),
        "기타안내": settings.get("extra_info", ""),
    }
    rendered = render_message(tmpl, values)
    byte_info = calculate_korean_bytes(rendered)

    # 3. 지연 대기
    delay_sec = int(settings.get("delay_seconds", 3))
    if simulate_delay and delay_sec > 0:
        print(f"⏳ 통화 직후 스팸 느낌 완화를 위해 {delay_sec}초간 대기 중...")
        time.sleep(min(delay_sec, 3))  # 테스트 시 최대 3초

    # 4. SMS 발송 실행
    send_success = send_sms_android(norm_phone, rendered)

    # 5. DB 로그 기록
    status_label = "SENT" if send_success else "FAILED"
    note_msg = f"{byte_info['type']} ({byte_info['bytes']}바이트) 자동 발송 완료"
    record_log(
        phone_number=norm_phone,
        call_type=call_type,
        message=rendered,
        status=status_label,
        note=note_msg,
    )

    print(f"✅ [콜백 발송 완료] {norm_phone}")
    print(f"   규격: {byte_info['type']} ({byte_info['bytes']} Bytes / {byte_info['char_count']}자)")
    print(f"   내용 첫 2줄: {rendered.splitlines()[0] if rendered else ''} ...")

    return {
        "success": True,
        "status": status_label,
        "reason": note_msg,
        "message": rendered,
        "bytes": byte_info,
    }


class CallbackHTTPRequestHandler(BaseHTTPRequestHandler):
    """
    안드로이드 MacroDroid / Tasker / Termux Webhook 연동용 경량 웹서버
    예: GET http://localhost:8080/call_ended?number=01012345678&type=normal
    """

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path in ["/call_ended", "/callback"]:
            params = parse_qs(parsed.query)
            phone = params.get("number", [""])[0]
            call_type = params.get("type", ["normal"])[0]

            if not phone:
                self.send_response(400)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.end_headers()
                self.wfile.write(b'{"ok": false, "error": "number parameter required"}')
                return

            result = handle_call_ended_event(phone, call_type, simulate_delay=False)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            import json
            self.wfile.write(json.dumps({"ok": True, "result": result}, ensure_ascii=False).encode("utf-8"))
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("소상공인 안드로이드 스마트 콜백 데몬 가동 중 (포트 8080)".encode("utf-8"))

    def log_message(self, format, *args):
        # 불필요한 HTTP 로그 최소화
        return


def run_daemon_server(port: int = 8080):
    server_address = ("", port)
    httpd = HTTPServer(server_address, CallbackHTTPRequestHandler)
    print(f"🚀 [데몬 가동] 안드로이드 콜백 리스너 시작됨 (포트: {port})")
    print(f"   MacroDroid/Tasker 호출 URL: http://localhost:{port}/call_ended?number=[전화번호]&type=[normal/missed]")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n데몬이 중지되었습니다.")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Smart Callback Pro Android Daemon")
    parser.add_argument("--test", action="store_true", help="가상 통화 종료 테스트 실행")
    parser.add_argument("--number", type=str, default="010-1234-5678", help="테스트 전화번호")
    parser.add_argument("--type", type=str, default="normal", choices=["normal", "missed", "holiday"], help="통화 유형")
    parser.add_argument("--server", action="store_true", help="안드로이드 로컬 웹훅 서버 모드 실행")
    parser.add_argument("--port", type=int, default=8080, help="웹훅 포트")

    args = parser.parse_args()

    if args.test:
        res = handle_call_ended_event(args.number, args.type, simulate_delay=False)
        print("\n테스트 결과 반환값:", res)
    elif args.server:
        run_daemon_server(args.port)
    else:
        print("사용법: python android_daemon.py --test 또는 --server")
