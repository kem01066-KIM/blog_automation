import streamlit as st
import os
import io
import re
import glob
import json
import zipfile
import urllib.request
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import cv2

# ==========================================
# 0. 페이지 설정 (모바일 & PC 반응형 최적화)
# ==========================================
st.set_page_config(
    page_title="바로누수 마케팅 원클릭 자동화",
    page_icon="🚰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# 모바일 친화적 커스텀 CSS
st.markdown("""
<style>
    .main-header {
        font-size: 1.8rem;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0.3rem;
    }
    .sub-header {
        font-size: 1.0rem;
        color: #4B5563;
        margin-bottom: 1.5rem;
    }
    .stButton>button {
        width: 100%;
        background-color: #2563EB;
        color: white;
        font-weight: bold;
        padding: 0.75rem;
        border-radius: 8px;
        border: none;
        font-size: 1.1rem;
    }
    .stButton>button:hover {
        background-color: #1D4ED8;
        color: white;
    }
    .card-box {
        background-color: #F3F4F6;
        border-radius: 10px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        border-left: 5px solid #2563EB;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 1. 폰트 자동 탐색 (환경별 대응)
# ==========================================
def get_korean_font(size=20):
    candidates = [
        "/usr/share/fonts/pickle-hwp/NotoSansCJKkr-Regular.otf",
        "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
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
    return ImageFont.load_default()


# ==========================================
# 2. 네이버 블로그 스크래핑 엔진
# ==========================================
def scrape_naver_blog(blog_url):
    """네이버 모바일/PC 블로그에서 제목, 본문 텍스트, w800 고화질 이미지 URL을 추출합니다."""
    # 모바일 URL로 통일
    match = re.search(r'blog\.naver\.com/([^/]+)/(\d+)', blog_url)
    if match:
        user_id, log_no = match.group(1), match.group(2)
        target_url = f"https://m.blog.naver.com/{user_id}/{log_no}"
    else:
        target_url = blog_url

    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15'
    }
    req = urllib.request.Request(target_url, headers=headers)
    
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')

    # 제목 추출
    title_match = re.search(r'<title>(.*?)</title>', html, re.DOTALL | re.IGNORECASE)
    raw_title = title_match.group(1).replace(" : 네이버 블로그", "").strip() if title_match else "현장 시공 기록"

    # 이미지 URL 추출 (mblogthumb 또는 postfiles)
    img_candidates = re.findall(r'https://postfiles\.pstatic\.net/[^\s\"\']+|https://mblogthumb-phinf\.pstatic\.net/[^\s\"\']+', html)
    
    clean_imgs = []
    seen = set()
    for img_url in img_candidates:
        # 이모티콘, 프로필, 스티커 이미지 제외
        if any(skip in img_url for skip in ['sticker', 'profile', 'static', 'dthumb', 'line']):
            continue
        base_url = img_url.split('?')[0]
        if base_url not in seen:
            seen.add(base_url)
            # w800 고화질 파라미터 적용
            clean_imgs.append(f"{base_url}?type=w800")

    # 본문 텍스트 추출 (단순 태그 제거)
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
def generate_titles_and_content(region, orig_title, orig_text, num_images, brand="바로누수설비", phone="010-0000-0000"):
    """상위노출 5대 공식과 지역(GEO) 타겟팅을 반영한 제목 3선과 완성형 본문을 생성합니다."""
    
    # 지역 파싱 (예: "대구 북구 노원동")
    region_clean = region.strip()
    words = region_clean.split()
    dong = words[-1] if words else "현장"
    gu = words[-2] if len(words) >= 2 else "대구"
    full_loc = f"{gu} {dong}"

    # 공사 성격 판별
    is_excavation = any(k in orig_text for k in ['포크레인', '굴착', '마당', '공장', '외부', '맨홀', '배관교체'])
    work_type = "공장 및 야외 대형 배관 굴착·신설" if is_excavation else "건물 실내 정밀 누수탐지 및 배관 수리"
    
    # 1. 추천 제목 3선 (CTR 최적화)
    if is_excavation:
        t1 = f"대구{gu}누수 {dong} 공장 배관 파손 역류, 포크레인 굴착부터 신규 배관 교체까지 완벽 해결"
        t2 = f"{full_loc} 누수탐지 현장 일지: 지하 매립 관로 파손 특정 및 일상생활배상책임보험 지원"
        t3 = f"대구{gu}누수 {dong} 상가·공장 바닥 물고임 원인은? 최신 내시경 탐지와 깔끔한 콘크리트 마감"
    else:
        t1 = f"대구{gu}누수 {dong} 아파트·빌라 배관 누수, 최첨단 가스·청음 탐지로 원샷 해결"
        t2 = f"{full_loc} 누수탐지 완벽 시공: 미세 크랙 배관 교체 및 일상생활배상책임보험 서류 무료 대행"
        t3 = f"대구{gu}누수 {dong} 바닥 물샘·수도요금 폭탄 해결! 타일 손상 최소화 정밀 복구"

    titles = [t1, t2, t3]

    # 2. 단계별 사진 캡션 및 본문 구성
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
    # 실제 사진 개수에 맞춤
    actual_steps = step_data[:num_images]

    # 3. 본문 텍스트 작성
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
[사진 {i:02d}: {title} 현장]

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
    """이미지 다운로드, 선명도 개선, STEP 뱃지 및 설명 자막 바를 합성합니다."""
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
            # 실패 시 빈 캔버스 대체
            img = Image.new('RGB', (800, 600), color=(50, 50, 50))

        # 대비 살짝 보정
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(1.08)

        draw = ImageDraw.Draw(img)
        w, h = img.size

        # 1. 상단 좌측: STEP 뱃지
        badge_text = f" {code} "
        draw.rounded_rectangle([(20, 20), (140, 62)], radius=8, fill=(30, 41, 59))
        draw.text((28, 26), badge_text, font=font_badge, fill=(255, 255, 255))

        # 2. 상단 우측: 브랜드 워터마크
        brand_w = 130
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

        filename = f"{idx:02d}_{step_title.replace(' ', '_')}.jpg"
        processed_images.append((filename, img))

    return processed_images


# ==========================================
# 5. 숏폼 영상 생성 엔진 (OpenCV 9:16 세로)
# ==========================================
def create_shortform_video(processed_images, output_path="shortform_leak_15s.mp4", duration=15):
    """가공된 사진들을 바탕으로 블러 배경, 줌인 효과, 프로그레스 바가 들어간 9:16 숏폼 MP4를 생성합니다."""
    if not processed_images:
        return None

    W, H = 720, 1280  # 세로 9:16 규격
    fps = 24
    num_imgs = len(processed_images)
    frames_per_img = max(int((fps * duration) / num_imgs), fps)

    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (W, H))

    for idx, (filename, pil_img) in enumerate(processed_images):
        iw, ih = pil_img.size

        # 배경: 블러 처리된 확대 이미지
        bg_pil = pil_img.resize((W, H))
        bg_cv = cv2.cvtColor(np.array(bg_pil), cv2.COLOR_RGB2BGR)
        bg_cv = cv2.GaussianBlur(bg_cv, (51, 51), 0)
        bg_cv = (bg_cv * 0.45).astype(np.uint8)

        # 전면: 원본 비율 유지 가로 맞춤
        scale = W / iw
        new_w = W
        new_h = int(ih * scale)
        fg_pil = pil_img.resize((new_w, new_h), Image.Resampling.LANCZOS)
        fg_cv = cv2.cvtColor(np.array(fg_pil), cv2.COLOR_RGB2BGR)
        y_offset = max((H - new_h) // 2, 0)

        for f in range(frames_per_img):
            frame = bg_cv.copy()

            # 부드러운 줌인 효과 (Ken Burns)
            zoom = 1.0 + (f / frames_per_img) * 0.035
            zw = int(new_w * zoom)
            zh = int(new_h * zoom)
            fg_zoomed = cv2.resize(fg_cv, (zw, zh), interpolation=cv2.INTER_LINEAR)

            zx = (zw - W) // 2
            zy = (zh - new_h) // 2
            fg_crop = fg_zoomed[zy:zy + new_h, zx:zx + W]

            if y_offset + new_h <= H:
                frame[y_offset:y_offset + new_h, 0:W] = fg_crop

            # 상단 재생 프로그레스 바
            progress = (idx * frames_per_img + f) / (num_imgs * frames_per_img)
            bar_w = int(W * progress)
            cv2.rectangle(frame, (0, 0), (bar_w, 10), (0, 165, 255), -1)

            out.write(frame)

    out.release()
    return output_path


# ==========================================
# 6. Streamlit 메인 UI 레이아웃
# ==========================================
def main():
    st.markdown('<div class="main-header">🚰 바로누수 마케팅 원클릭 생성기</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">예전 블로그 링크와 오늘 타겟 지역만 넣으면 <b>제목 3선 + 상위노출 원고 + 편집 사진 + 15초 숏폼 영상</b>까지 한번에 완성됩니다.</div>', unsafe_allow_html=True)

    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 기본 설정")
        brand_name = st.text_input("업체 상호", value="바로누수설비")
        phone_num = st.text_input("문의 전화번호", value="010-3815-1154")
        generate_video_chk = st.checkbox("숏폼 영상(9:16) 함께 제작", value=True)
        st.info("💡 모바일에서도 Chrome/Safari로 접속해 바로 사용하실 수 있습니다.")

    # 메인 입력 폼
    col1, col2 = st.columns([2, 1])
    with col1:
        default_url = "https://m.blog.naver.com/dnjswo3482/224052764862"
        input_url = st.text_input("🔗 바로누수 예전 글 링크", value=default_url, placeholder="https://m.blog.naver.com/...")
    with col2:
        input_region = st.text_input("📍 오늘 발행할 타겟 지역", value="대구 북구 노원동", placeholder="예: 대구 북구 노원동")

    start_btn = st.button("🚀 마케팅 패키지 일괄 생성하기")

    if start_btn:
        if not input_url or not input_region:
            st.warning("링크와 타겟 지역을 모두 입력해 주세요!")
            return

        with st.spinner("1/4. 네이버 블로그 원본 분석 및 고화질 이미지 추출 중..."):
            blog_data = scrape_naver_blog(input_url)
            num_imgs = len(blog_data["images"])
            st.success(f"원문 분석 완료! 고화질 사진 {num_imgs}장을 확보했습니다.")

        with st.spinner("2/4. SEO / GEO 알고리즘 기반 제목 3선 및 최적화 원고 작성 중..."):
            titles, body_text, steps = generate_titles_and_content(
                region=input_region,
                orig_title=blog_data["title"],
                orig_text=blog_data["text"],
                num_images=num_imgs,
                brand=brand_name,
                phone=phone_num
            )

        with st.spinner("3/4. 사진 선명도 보정 및 STEP 자막 라벨 일괄 합성 중..."):
            processed_images = process_and_badge_images(
                image_urls=blog_data["images"],
                steps=steps,
                brand=brand_name
            )

        video_path = None
        if generate_video_chk:
            with st.spinner("4/4. 릴스·쇼츠용 15초 9:16 숏폼 영상 렌더링 중..."):
                video_path = create_shortform_video(processed_images, "shortform_output.mp4", duration=15)

        st.balloons()

        # 결과 탭 구성
        tab1, tab2, tab3, tab4 = st.tabs(["📋 추천 제목 & 원고", "📸 편집 사진 (갤러리)", "🎬 숏폼 영상 (9:16)", "📦 전체 다운로드"])

        # TAB 1: 제목 및 원고
        with tab1:
            st.subheader("🎯 네이버 스마트블록 상위노출 추천 제목 3선")
            for i, t in enumerate(titles, 1):
                st.code(t, language="")

            st.subheader("📝 완성형 블로그 원고 (복사하여 에디터에 붙여넣기)")
            st.text_area("블로그 본문 전문", value=body_text, height=380)
            st.download_button(
                label="📄 원고 텍스트 파일(.txt) 다운로드",
                data=body_text.encode('utf-8'),
                file_name=f"원고_{input_region.replace(' ', '_')}.txt",
                mime="text/plain"
            )

        # TAB 2: 편집 사진
        with tab2:
            st.subheader(f"📸 STEP 라벨 및 설명 자막이 합성된 사진 ({len(processed_images)}장)")
            cols = st.columns(3)
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zf:
                for idx, (fname, pimg) in enumerate(processed_images):
                    with cols[idx % 3]:
                        st.image(pimg, caption=fname, use_container_width=True)
                    img_byte = io.BytesIO()
                    pimg.save(img_byte, format='JPEG', quality=90)
                    zf.writestr(fname, img_byte.getvalue())

            st.download_button(
                label="🗂️ 편집 사진 전체 ZIP 다운로드",
                data=zip_buffer.getvalue(),
                file_name=f"편집사진_{input_region.replace(' ', '_')}.zip",
                mime="application/zip"
            )

        # TAB 3: 숏폼 영상
        with tab3:
            st.subheader("🎬 릴스 / 유튜브 쇼츠 / 네이버 클립용 15초 세로 영상")
            if video_path and os.path.exists(video_path):
                st.video(video_path)
                with open(video_path, "rb") as vf:
                    video_bytes = vf.read()
                st.download_button(
                    label="🎥 숏폼 영상(.mp4) 다운로드",
                    data=video_bytes,
                    file_name=f"숏폼_{input_region.replace(' ', '_')}.mp4",
                    mime="video/mp4"
                )
            else:
                st.info("영상 생성이 비활성화되었거나 생성이 생략되었습니다.")

        # TAB 4: 전체 패키지 ZIP
        with tab4:
            st.subheader("📦 전체 결과물 원클릭 압축 다운로드")
            all_zip_buffer = io.BytesIO()
            with zipfile.ZipFile(all_zip_buffer, "w") as azf:
                # 1. 제목 및 원고
                titles_str = "\n".join([f"제목 {i}: {t}" for i, t in enumerate(titles, 1)])
                full_doc = f"{titles_str}\n\n========================\n\n{body_text}"
                azf.writestr("00_제목_및_원고.txt", full_doc.encode('utf-8'))

                # 2. 사진들
                for fname, pimg in processed_images:
                    img_byte = io.BytesIO()
                    pimg.save(img_byte, format='JPEG', quality=90)
                    azf.writestr(f"images/{fname}", img_byte.getvalue())

                # 3. 비디오
                if video_path and os.path.exists(video_path):
                    with open(video_path, "rb") as vf:
                        azf.writestr("shortform_video.mp4", vf.read())

            st.download_button(
                label="📦 전체 패키지(원고+사진+영상) ZIP 일괄 다운로드",
                data=all_zip_buffer.getvalue(),
                file_name=f"바로누수_{input_region.replace(' ', '_')}_마케팅패키지.zip",
                mime="application/zip"
            )


if __name__ == "__main__":
    main()
