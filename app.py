import streamlit as st
import os
import io
import zipfile
from engine import (
    get_korean_font,
    scrape_naver_blog,
    generate_titles_and_content,
    process_and_badge_images,
    create_shortform_video
)

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
        font-size: 1.7rem;
        font-weight: 800;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 0.95rem;
        color: #4B5563;
        margin-bottom: 1.2rem;
        line-height: 1.4;
    }
    .stButton>button {
        width: 100%;
        background-color: #2563EB;
        color: white;
        font-weight: bold;
        padding: 0.8rem;
        border-radius: 8px;
        border: none;
        font-size: 1.05rem;
    }
    .stButton>button:hover {
        background-color: #1D4ED8;
        color: white;
    }
    .photo-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 10px;
        padding: 0.8rem;
        margin-bottom: 0.8rem;
    }
    .photo-title {
        font-weight: 700;
        color: #1E293B;
        font-size: 1.05rem;
        margin-bottom: 0.3rem;
    }
    .photo-desc {
        color: #64748B;
        font-size: 0.88rem;
        margin-bottom: 0.4rem;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 1. Streamlit 메인 UI (Session State 기반)
# ==========================================
def main():
    st.markdown('<div class="main-header">🚰 바로누수 마케팅 원클릭 생성기</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">예전 블로그 링크와 오늘 타겟 지역만 넣으면 <b>제목 3선 + 완성형 원고 + 사진 개별 다운로드 + 15초 숏폼 영상</b>까지 한번에 완성됩니다.</div>', unsafe_allow_html=True)

    # 1. 세션 상태 초기화
    if "baro_result" not in st.session_state:
        st.session_state.baro_result = None

    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 기본 설정")
        brand_name = st.text_input("업체 상호", value="바로누수설비")
        phone_num = st.text_input("문의 전화번호", value="010-3815-1154")
        generate_video_chk = st.checkbox("숏폼 영상(9:16) 함께 제작", value=True)
        st.info("💡 모바일(스마트폰) 브라우저에 최적화되어 있습니다.")
        if st.session_state.baro_result is not None:
            if st.button("🔄 새로운 지역으로 다시 만들기"):
                st.session_state.baro_result = None
                st.rerun()

    # 메인 입력 폼
    col1, col2 = st.columns([2, 1])
    with col1:
        default_url = "https://m.blog.naver.com/dnjswo3482/224052764862"
        input_url = st.text_input("🔗 바로누수 예전 글 링크", value=default_url, placeholder="https://m.blog.naver.com/...")
    with col2:
        input_region = st.text_input("📍 오늘 발행할 타겟 지역", value="대구 북구 노원동", placeholder="예: 대구 북구 노원동")

    start_btn = st.button("🚀 마케팅 패키지 일괄 생성하기", key="generate_btn")

    # 2. 버튼 클릭 시 데이터 생성 및 세션 저장
    if start_btn:
        if not input_url or not input_region:
            st.warning("링크와 타겟 지역을 모두 입력해 주세요!")
            return

        with st.status("마케팅 패키지 생성 중...", expanded=True) as status:
            st.write("1/4. 네이버 블로그 원본 분석 및 고화질 이미지 추출 중...")
            blog_data = scrape_naver_blog(input_url)
            num_imgs = len(blog_data["images"])
            if num_imgs == 0:
                status.update(label="이미지 추출 실패", state="error")
                st.error("해당 글에서 시공 사진을 찾지 못했습니다. 블로그 링크를 다시 확인해 주세요.")
                return
            st.write(f"✓ 원문 분석 완료: 고화질 시공 사진 {num_imgs}장 확보")

            st.write("2/4. SEO/GEO 알고리즘 기반 상위노출 제목 3선 및 5단계 원고 작성 중...")
            titles, body_text, steps = generate_titles_and_content(
                region=input_region,
                orig_title=blog_data["title"],
                orig_text=blog_data["text"],
                num_images=num_imgs,
                brand=brand_name,
                phone=phone_num
            )
            st.write("✓ 상위노출 원고 및 캡션 매핑 완료")

            st.write("3/4. 사진 대비 보정, STEP 뱃지 및 설명 자막 합성 중...")
            processed_images = process_and_badge_images(
                image_urls=blog_data["images"],
                steps=steps,
                brand=brand_name
            )
            st.write(f"✓ 사진 {len(processed_images)}장 개별 가공 완료")

            video_bytes = None
            if generate_video_chk:
                st.write("4/4. 릴스·쇼츠용 15초 9:16 세로 숏폼 영상(H.264) 렌더링 중...")
                video_bytes = create_shortform_video(processed_images, duration=15)
                st.write("✓ 모바일 호환 숏폼 영상 제작 완료")

            status.update(label="🎉 모든 제작 완료!", state="complete", expanded=False)

        # 세션에 영구 보존
        st.session_state.baro_result = {
            "region": input_region,
            "titles": titles,
            "body_text": body_text,
            "processed_images": processed_images,
            "video_bytes": video_bytes
        }
        st.balloons()
        st.rerun()

    # 3. 결과 화면 렌더링 (세션에서 불러오므로 탭 이동/다운로드 시 절대 사라지지 않음)
    if st.session_state.baro_result is not None:
        res = st.session_state.baro_result
        region_clean = res["region"].replace(' ', '_')
        processed_images = res["processed_images"]
        titles = res["titles"]
        body_text = res["body_text"]
        video_bytes = res["video_bytes"]

        st.success(f"📍 **[{res['region']}]** 마케팅 패키지가 완성되었습니다! 아래 탭에서 바로 확인하고 저장하세요.")

        # 탭 구성
        tab1, tab2, tab3 = st.tabs([
            "📋 추천 제목 & 원고",
            f"📸 가공 사진 개별 저장 ({len(processed_images)}장)",
            "🎬 숏폼 영상 (9:16)"
        ])

        # TAB 1: 제목 및 원고
        with tab1:
            st.subheader("🎯 네이버 스마트블록 상위노출 추천 제목 3선")
            st.info("원하시는 제목을 터치하거나 복사하여 네이버 블로그 제목에 사용하세요.")
            for i, t in enumerate(titles, 1):
                st.code(t, language="")

            st.subheader("📝 완성형 블로그 원고")
            st.text_area("원고 전문 (복사하여 블로그 에디터에 붙여넣기)", value=body_text, height=360)
            
            st.download_button(
                label="📄 원고 텍스트 파일(.txt) 저장",
                data=body_text.encode('utf-8'),
                file_name=f"원고_{region_clean}.txt",
                mime="text/plain",
                use_container_width=True
            )

        # TAB 2: 가공 사진 (개별 다운로드 중심)
        with tab2:
            st.subheader(f"📸 가공 사진 {len(processed_images)}장 개별 저장")
            st.success("💡 **폰에서 저장하는 방법**: 각 사진 아래의 파란색 **[📥 사진 저장]** 버튼을 누르시면 갤러리/다운로드 폴더에 사진이 바로 저장됩니다! (사진을 길게 꾹 눌러 '이미지 저장'하셔도 됩니다)")

            for item in processed_images:
                idx = item["idx"]
                code = item["code"]
                title = item["title"]
                desc = item["desc"]
                fname = item["filename"]
                pimg = item["image"]
                ibytes = item["bytes"]

                st.markdown(f"""
                <div class="photo-card">
                    <div class="photo-title">🔹 {code}. {title}</div>
                    <div class="photo-desc">{desc}</div>
                </div>
                """, unsafe_allow_html=True)

                st.image(pimg, use_container_width=True)

                st.download_button(
                    label=f"📥 {code} 사진 바로 저장 ({fname})",
                    data=ibytes,
                    file_name=fname,
                    mime="image/jpeg",
                    key=f"dl_single_img_{idx}",
                    use_container_width=True
                )
                st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

            # PC 사용자를 위한 일괄 ZIP (하단 접힘 메뉴)
            with st.expander("💻 (선택사항) PC용 전체 사진 일괄 ZIP 다운로드"):
                zip_buffer = io.BytesIO()
                with zipfile.ZipFile(zip_buffer, "w") as zf:
                    for item in processed_images:
                        zf.writestr(item["filename"], item["bytes"])
                st.download_button(
                    label="🗂️ 전체 사진 ZIP 일괄 다운로드",
                    data=zip_buffer.getvalue(),
                    file_name=f"편집사진_{region_clean}.zip",
                    mime="application/zip",
                    use_container_width=True
                )

        # TAB 3: 숏폼 영상
        with tab3:
            st.subheader("🎬 15초 9:16 세로 숏폼 영상 (릴스 / 쇼츠 / 클립용)")
            if video_bytes:
                st.video(video_bytes)
                st.download_button(
                    label=f"🎥 숏폼 영상(.mp4) 스마트폰에 저장",
                    data=video_bytes,
                    file_name=f"숏폼_{region_clean}_15s.mp4",
                    mime="video/mp4",
                    use_container_width=True
                )
            else:
                st.info("숏폼 영상 생성이 생략되었습니다. 사이드바 설정을 확인해 주세요.")


if __name__ == "__main__":
    main()
