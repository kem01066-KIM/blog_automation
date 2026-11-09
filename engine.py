import os
import io
import re
import urllib.request
import urllib.parse
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import cv2
import imageio

# ==========================================
# 1. 폰트 자동 탐색 (환경별 대응)
# ==========================================
def get_korean_font(size=20):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "fonts", "NanumGothic.ttf"),
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
        "/usr/share/fonts/pickle-hwp/NotoSansCJKkr-Regular.otf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/gulim.ttc",
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/Library/Fonts/NanumGothic.ttf"
    ]
    for font_path in candidates:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                continue

    # 로컬 다운로드 시도 (Google Fonts)
    try:
        font_dir = os.path.join(base_dir, "fonts")
        os.makedirs(font_dir, exist_ok=True)
        local_font = os.path.join(font_dir, "NanumGothic.ttf")
        if not os.path.exists(local_font):
            urllib.request.urlretrieve(
                "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf",
                local_font
            )
        return ImageFont.truetype(local_font, size)
    except Exception:
        pass

    return ImageFont.load_default()


# ==========================================
# 2. 네이버 블로그 스크래핑 엔진
# ==========================================
def scrape_naver_blog(blog_url):
    """네이버 모바일/PC 블로그에서 제목, 본문 텍스트, 고화질 시공 이미지 URL을 추출합니다."""
    user_id, log_no = None, None
    m1 = re.search(r'blog\.naver\.com/([^/?&]+)/(\d+)', blog_url)
    m2 = re.search(r'blogId=([^&]+).*?logNo=(\d+)', blog_url)

    if m1:
        user_id, log_no = m1.group(1), m1.group(2)
    elif m2:
        user_id, log_no = m2.group(1), m2.group(2)

    if user_id and log_no:
        target_url = f"https://m.blog.naver.com/{user_id}/{log_no}"
    else:
        target_url = blog_url.strip()

    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15'
    }
    req = urllib.request.Request(target_url, headers=headers)
    
    with urllib.request.urlopen(req, timeout=12) as resp:
        html = resp.read().decode('utf-8', errors='ignore')

    # 제목 추출
    title_match = re.search(r'<title>(.*?)</title>', html, re.DOTALL | re.IGNORECASE)
    raw_title = title_match.group(1).replace(" : 네이버 블로그", "").strip() if title_match else "현장 시공 기록"

    # 이미지 URL 추출 (mblogthumb 또는 postfiles)
    img_candidates = re.findall(
        r'https://postfiles\.pstatic\.net/[^\s\"\'\<\>]+|https://mblogthumb-phinf\.pstatic\.net/[^\s\"\'\<\>]+',
        html
    )

    clean_imgs = []
    seen = set()
    for img_url in img_candidates:
        base_url = img_url.split('?')[0].replace('&quot;', '').replace('&amp;', '&').rstrip(')\"\'')
        base_lower = base_url.lower()

        # 스티커, 프로필, 아이콘, GIF 애니메이션 제외
        skip_patterns = ['/sticker/', '/profile/', 'emoticon', 'editor_profile', 'ico_', '.gif', 'line_sticker', 'blog_profile']
        if any(skip in base_lower for skip in skip_patterns):
            continue

        if base_url not in seen:
            seen.add(base_url)
            clean_imgs.append(f"{base_url}?type=w800")

    # 본문 텍스트 추출
    text_cleaned = re.sub(r'<script.*?</script>', '', html, flags=re.DOTALL)
    text_cleaned = re.sub(r'<style.*?</style>', '', text_cleaned, flags=re.DOTALL)
    text_cleaned = re.sub(r'<[^>]+>', ' ', text_cleaned)
    text_cleaned = re.sub(r'\s+', ' ', text_cleaned).strip()

    return {
        "title": raw_title,
        "images": clean_imgs,
        "text": text_cleaned[:3000]
    }


# ==========================================
# 3. SEO / GEO 원고 및 제목 생성 엔진
# ==========================================
def generate_titles_and_content(region, orig_title, orig_text, num_images, brand="바로누수설비", phone="010-3815-1154"):
    """상위노출 5대 공식과 지역(GEO) 타겟팅을 반영한 제목 3선과 완성형 본문을 생성합니다."""
    
    region_clean = region.strip()
    words = region_clean.split()
    dong = words[-1] if words else "현장"
    gu = words[-2] if len(words) >= 2 else "대구"
    full_loc = f"{gu} {dong}"

    is_excavation = any(k in orig_text for k in ['포크레인', '굴착', '마당', '공장', '외부', '맨홀', '배관교체', '배관 파손'])
    
    # 추천 제목 3선
    if is_excavation:
        t1 = f"대구{gu}누수 {dong} 공장 배관 파손 역류, 포크레인 굴착부터 신규 배관 교체까지 완벽 해결"
        t2 = f"{full_loc} 누수탐지 현장 일지: 지하 매립 관로 파손 특정 및 일상생활배상책임보험 지원"
        t3 = f"대구{gu}누수 {dong} 상가·공장 바닥 물고임 원인은? 최신 내시경 탐지와 깔끔한 콘크리트 마감"
    else:
        t1 = f"대구{gu}누수 {dong} 아파트·빌라 배관 누수, 최첨단 가스·청음 탐지로 원샷 해결"
        t2 = f"{full_loc} 누수탐지 완벽 시공: 미세 크랙 배관 교체 및 일상생활배상책임보험 서류 무료 대행"
        t3 = f"대구{gu}누수 {dong} 바닥 물샘·수도요금 폭탄 해결! 타일 손상 최소화 정밀 복구"

    titles = [t1, t2, t3]

    # 단계별 사진 캡션
    step_data = [
        ("STEP 01", "현장 출동", f"{full_loc} 누수 의뢰 현장 신속 도착 및 상황 확인"),
        ("STEP 02", "정밀 탐지", "최신 청음식·가스식 및 관로 내시경 장비 투입"),
        ("STEP 03", "원인 특정", "지하 매립 배관 파손 및 크랙 발생 지점 정밀 판독"),
        ("STEP 04", "정밀 굴착", "작업 반경 최소화 바닥 컷팅 및 굴착 착수"),
        ("STEP 05", "파손 확인", "흙 속 드러난 노후 파손 배관 및 누수 부속 확인"),
        ("STEP 06", "노후관 철거", "부식되어 제 기능 상실한 불량 배관 깔끔히 적출"),
        ("STEP 07", "신설 교체", "고강도 신규 정품 PVC/PB 배관 연결 및 완벽 체결"),
        ("STEP 08", "압력 테스트", "배관 내 공압 5bar 주입, 미세 누수 0% 정밀 검증"),
        ("STEP 09", "되메우기", "지반 침하 방지를 위한 흙 되메우기 및 단단한 지반 다짐"),
        ("STEP 10", "마감 복구", "기존 바닥과 단차 없이 완벽한 미장 및 타일 마감"),
        ("STEP 11", "시공 완료", f"{full_loc} 누수 공사 최종 점검 및 보험 서류 완비")
    ]
    
    actual_steps = []
    for i in range(num_images):
        if i < len(step_data):
            actual_steps.append(step_data[i])
        else:
            actual_steps.append((f"STEP {i+1:02d}", f"추가 시공 공정 {i+1}", f"{full_loc} 현장 맞춤형 정밀 보강 작업"))

    body = f"""[현장 요약 카드]
■ 현장 위치: {region_clean} 일대
■ 건물 유형: 상가, 주택, 공장 밀집 구역
■ 의뢰 증상: 바닥 물비침, 계량기 고속 회전, 수도요금 급증
■ 진단 원인: 지하 매립 노후 배관 부식 및 연결 부속 크랙
■ 해결 공정: 최첨단 장비 정밀 탐지 → 배관 신설 교체 → 공압 테스트 → 완벽 복구
■ 혜택 지원: 일상생활배상책임보험(일배책) 서류 100% 무료 대행

---

안녕하세요, 대구 전 지역 누수 문제를 정밀하게 해결하는 {brand}입니다.

오늘은 {full_loc} 인근에서 발생한 긴급 누수 의뢰를 받고 현장으로 신속하게 출동했습니다.
{dong} 지역은 노후 배관이나 복잡한 지하 매설 라인이 많아 정밀 장비 없이 섣불리 바닥을 깨면 비용과 공사 규모만 커질 수 있습니다. {brand}은 첨단 탐지기를 바탕으로 '최소 타공, 정확한 원인 규명'을 원칙으로 작업합니다.

"""
    for i, (code, title, desc) in enumerate(actual_steps, 1):
        body += f"""
### {code}. {title}
{desc}
[사진 {i:02d}: {code} {title} 현장]

{dong} 현장에서 {title} 공정을 꼼꼼하게 진행했습니다. 작업 전후 과정을 고객님께 투명하게 설명해 드리며 안심하고 맡기실 수 있도록 원스톱으로 관리합니다.
"""

    body += f"""
---

💡 {dong} 현장 설비팀의 배관 관리 TIP
1. 수도요금이 평소보다 갑자기 2~3배 이상 나왔다면 즉시 메인 밸브를 잠그고 계량기 별표 회전 여부를 확인하세요.
2. 바닥이나 벽면에 습기가 차거나 곰팡이가 피어난다면 이미 배관 미세 누수가 진행 중일 확률이 높습니다.
3. 아랫집 피해가 발생한 경우 가입해 두신 '일상생활배상책임보험(일배책)'으로 공사비와 피해 복구비를 보상받으실 수 있으며, {brand}에서 필요한 증빙 서류 일체를 무료로 작성해 드립니다.

누수는 방치할수록 지반 침하와 추가 피해로 이어집니다.
대구 전 지역 언제든 편하게 문의해 주시면 정직하고 확실하게 해결해 드리겠습니다.

📞 {brand} 직통 상담: {phone}
대구 전 지역 24시간 긴급 출동 / 미해결 시 0원 안심 보증

#대구{gu}누수 #{dong}누수 #대구누수탐지 #대구배관교체 #{brand} #누수보험서류
"""

    return titles, body.strip(), actual_steps


# ==========================================
# 4. 이미지 가공 엔진 (Pillow)
# ==========================================
def process_and_badge_images(image_urls, steps, brand="바로누수설비"):
    """이미지 다운로드, 선명도 개선, STEP 뱃지 및 설명 자막 바를 합성하고 바이트를 함께 반환합니다."""
    processed_images = []
    
    font_badge = get_korean_font(24)
    font_title = get_korean_font(22)
    font_desc = get_korean_font(18)
    font_brand = get_korean_font(18)

    headers = {'User-Agent': 'Mozilla/5.0'}

    for idx, (url, (code, step_title, step_desc)) in enumerate(zip(image_urls, steps), 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as resp:
                raw_data = resp.read()
                img = Image.open(io.BytesIO(raw_data)).convert('RGB')
        except Exception:
            img = Image.new('RGB', (800, 600), color=(50, 50, 50))

        # 대비 보정
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.08)

        draw = ImageDraw.Draw(img)
        w, h = img.size

        # 1. 상단 좌측: STEP 뱃지
        badge_text = f" {code} "
        draw.rounded_rectangle([(20, 20), (145, 62)], radius=8, fill=(30, 41, 59))
        draw.text((28, 26), badge_text, font=font_badge, fill=(255, 255, 255))

        # 2. 상단 우측: 브랜드 워터마크
        brand_w = 135
        draw.rounded_rectangle([(w - brand_w - 20, 20), (w - 20, 58)], radius=6, fill=(37, 99, 235))
        draw.text((w - brand_w - 10, 26), f" {brand} ", font=font_brand, fill=(255, 255, 255))

        # 3. 하단 자막 바 (오버레이)
        bar_h = 85
        overlay = Image.new('RGBA', (w, bar_h), (15, 23, 42, 220))
        img.paste(overlay, (0, h - bar_h), overlay)

        # 파란색 포인트 라인
        draw.rectangle([(0, h - bar_h), (w, h - bar_h + 4)], fill=(37, 99, 235))

        # 자막 텍스트
        draw.text((25, h - bar_h + 12), f"[{step_title}]", font=font_title, fill=(96, 165, 250))
        draw.text((25, h - bar_h + 45), step_desc, font=font_desc, fill=(241, 245, 249))

        filename = f"{idx:02d}_{code.replace(' ', '_')}_{step_title.replace(' ', '_')}.jpg"
        
        # JPEG 바이트 인코딩
        img_byte_io = io.BytesIO()
        img.save(img_byte_io, format='JPEG', quality=90)
        img_bytes = img_byte_io.getvalue()

        processed_images.append({
            "idx": idx,
            "filename": filename,
            "code": code,
            "title": step_title,
            "desc": step_desc,
            "image": img,
            "bytes": img_bytes
        })

    return processed_images


# ==========================================
# 5. 숏폼 영상 생성 엔진 (H.264 MP4)
# ==========================================
def create_shortform_video(processed_images, duration=15):
    """가공된 사진들로 모바일 호환 H.264 9:16 숏폼 MP4 비디오 바이트를 생성합니다."""
    if not processed_images:
        return None

    W, H = 720, 1280  # 세로 9:16 규격
    fps = 24
    num_imgs = len(processed_images)
    frames_per_img = max(int((fps * duration) / num_imgs), fps)

    temp_video_path = "/tmp/shortform_render.mp4"

    try:
        writer = imageio.get_writer(
            temp_video_path,
            fps=fps,
            codec='libx264',
            pixelformat='yuv420p',
            quality=8
        )

        for idx, item in enumerate(processed_images):
            pil_img = item["image"]
            iw, ih = pil_img.size

            bg_pil = pil_img.resize((W, H))
            bg_cv = cv2.cvtColor(np.array(bg_pil), cv2.COLOR_RGB2BGR)
            bg_cv = cv2.GaussianBlur(bg_cv, (51, 51), 0)
            bg_cv = (bg_cv * 0.45).astype(np.uint8)

            scale = W / iw
            new_w = W
            new_h = int(ih * scale)
            fg_pil = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
            fg_cv = cv2.cvtColor(np.array(fg_pil), cv2.COLOR_RGB2BGR)
            y_offset = max((H - new_h) // 2, 0)

            for f in range(frames_per_img):
                frame = bg_cv.copy()

                zoom = 1.0 + (f / frames_per_img) * 0.035
                zw = int(new_w * zoom)
                zh = int(new_h * zoom)
                fg_zoomed = cv2.resize(fg_cv, (zw, zh), interpolation=cv2.INTER_LINEAR)

                zx = (zw - W) // 2
                zy = (zh - new_h) // 2
                fg_crop = fg_zoomed[zy:zy + new_h, zx:zx + W]

                if y_offset + new_h <= H:
                    frame[y_offset:y_offset + new_h, 0:W] = fg_crop

                progress = (idx * frames_per_img + f) / (num_imgs * frames_per_img)
                bar_w = int(W * progress)
                cv2.rectangle(frame, (0, 0), (bar_w, 10), (0, 165, 255), -1)

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                writer.append_data(frame_rgb)

        writer.close()

        with open(temp_video_path, "rb") as vf:
            video_bytes = vf.read()
        
        try:
            os.remove(temp_video_path)
        except Exception:
            pass

        return video_bytes
    except Exception as e:
        print(f"영상 인코딩 중 오류 발생: {e}")
        return None
