import streamlit as st
import os
import io
import zipfile
from engine import (
    get_korean_font,
    scrape_naver_blog,
    search_naver_serp,
    get_related_posts,
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
        font-size: 1.65rem;
        font-weight: 800;
        color: #1E3A8A;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 0.92rem;
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
        border-radius: 8px;
        padding: 0.6rem 0.8rem;
        margin-bottom: 0.5rem;
    }
    .photo-title {
        font-weight: 700;
        color: #1E293B;
        font-size: 1.0rem;
    }
    .serp-box {
        background-color: #EFF6FF;
        border-left: 4px solid #3B82F6;
        padding: 0.8rem;
        border-radius: 6px;
        margin-bottom: 1rem;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)


# ==========================================
# 1. Streamlit 메인 UI (Session State 기반)
# ==========================================
def main():
    st.markdown('<div class="main-header">🚰 바로누수 마케팅 원클릭 생성기</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">예전 블로그 링크와 오늘 타겟 지역만 넣으면 <b>지역 실시간 검색·분석 → 맞춤형 원고 + 사진 개별 다운로드 + 15초 숏폼</b>까지 한번에 완성됩니다.</div>', unsafe_allow_html=True)

    if "baro_result" not in st.session_state:
        st.session_state.baro_result = None

    # 사이드바 설정
    with st.sidebar:
        st.header("⚙️ 기본 설정")
        brand_name = st.text_input("업체 상호", value="바로누수설비")
        
        photo_style_label = st.selectbox(
            "📸 사진 편집 스타일",
            [
                "자연스러운 스타일 (미니멀 로고+라벨, 추천)",
                "하단 자막 바 스타일 (설명글 포함)",
                "원본 보정만 (텍스트 없음)"
            ],
            index=0
        )
        if "자연스러운" in photo_style_label:
            photo_style = "natural"
        elif "하단 자막" in photo_style_label:
            photo_style = "banner"
        else:
            photo_style = "clean"

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

    start_btn = st.button("🚀 지역 검색·분석 및 원클릭 생성하기", key="generate_btn")

    # 버튼 클릭 시 실시간 분석 및 생성
    if start_btn:
        if not input_url or not input_region:
            st.warning("링크와 타겟 지역을 모두 입력해 주세요!")
            return

        with st.status(f"[{input_region}] 지역 실시간 분석 및 콘텐츠 생성 중...", expanded=True) as status:
            st.write("1/5. 네이버 블로그 원본 분석 및 고화질 시공 사진 추출 중...")
            blog_data = scrape_naver_blog(input_url)
            num_imgs = len(blog_data["images"])
            if num_imgs == 0:
                status.update(label="이미지 추출 실패", state="error")
                st.error("해당 글에서 시공 사진을 찾지 못했습니다. 블로그 링크를 다시 확인해 주세요.")
                return
            st.write(f"✓ 원문 분석 완료: 고화질 시공 사진 {num_imgs}장 확보")

            st.write(f"2/5. [{input_region}누수] 네이버 블로그 실시간 검색 및 상위노출 키워드 분석 중...")
            titles, body_text, steps, serp_titles = generate_titles_and_content(
                region=input_region,
                orig_title=blog_data["title"],
                orig_text=blog_data["text"],
                num_images=num_imgs,
                brand=brand_name
            )
            st.write(f"✓ 네이버 실시간 상위 키워드 분석 완료 ({len(serp_titles)}개 경쟁 글 참조)")

            st.write(f"3/5. 기존 블로그 흐름 100% 일치 원고 작성 완료 (복붙용 마크다운 완전 제거, 유사 이전 글 매칭)")

            st.write(f"4/5. 사진 선명도 보정 및 스타일 가공 중... ({photo_style_label})")
            processed_images = process_and_badge_images(
                image_urls=blog_data["images"],
                steps=steps,
                brand=brand_name,
                photo_style=photo_style
            )
            st.write(f"✓ 시공 사진 {len(processed_images)}장 가공 완료")

            video_bytes = None
            if generate_video_chk:
                st.write("5/5. 릴스·쇼츠용 15초 9:16 세로 숏폼 영상(H.264) 렌더링 중...")
                video_bytes = create_shortform_video(processed_images, duration=15)
                st.write("✓ 모바일 호환 숏폼 영상 제작 완료")

            status.update(label="🎉 모든 분석 및 제작 완료!", state="complete", expanded=False)

        st.session_state.baro_result = {
            "region": input_region,
            "titles": titles,
            "body_text": body_text,
            "serp_titles": serp_titles,
            "processed_images": processed_images,
            "video_bytes": video_bytes
        }
        st.balloons()
        st.rerun()

    # 결과 화면 (세션 유지)
    if st.session_state.baro_result is not None:
        res = st.session_state.baro_result
        region_clean = res["region"].replace(' ', '_')
        processed_images = res["processed_images"]
        titles = res["titles"]
        body_text = res["body_text"]
        serp_titles = res.get("serp_titles", [])
        video_bytes = res["video_bytes"]

        st.success(f"📍 **[{res['region']}]** 지역 분석 맞춤형 패키지가 완성되었습니다! 아래 탭에서 바로 확인하세요.")

        tab1, tab2, tab3 = st.tabs([
            "📋 추천 제목 & 원고 (복붙용)",
            f"📸 가공 사진 개별 저장 ({len(processed_images)}장)",
            "🎬 숏폼 영상 (9:16)"
        ])

        # TAB 1: 제목 및 원고
        with tab1:
            if serp_titles:
                with st.expander(f"🔍 [{res['region']}누수] 네이버 실시간 상위노출 포스팅 분석 결과 ({len(serp_titles)}건)"):
                    for i, stit in enumerate(serp_titles, 1):
                        st.markdown(f"- {stit}")

            st.subheader("🎯 네이버 스마트블록 추천 제목 3선")
            st.info("원하시는 제목을 터치하거나 복사하여 네이버 블로그 제목에 사용하세요.")
            for i, t in enumerate(titles, 1):
                st.code(t, language="")

            st.subheader("📝 완성형 블로그 원고 (마크다운 기호 없음)")
            st.caption("스마트에디터 ONE에 그대로 붙여넣기(Ctrl+V) 하실 수 있도록 #, *, 표 기호 없이 줄바꿈만 깔끔하게 정돈된 순수 텍스트입니다.")
            st.text_area("원고 전문", value=body_text, height=420)
            
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
            st.success("💡 **폰에서 저장하는 방법**: 각 사진 아래의 파란색 **[📥 사진 저장]** 버튼을 누르시면 압축 풀 필요 없이 폰 갤러리/다운로드 폴더에 사진이 바로 저장됩니다! (사진을 길게 꾹 눌러 저장하셔도 됩니다)")

            for item in processed_images:
                idx = item["idx"]
                code = item["code"]
                title = item["title"]
                fname = item["filename"]
                pimg = item["image"]
                ibytes = item["bytes"]

                st.markdown(f"""
                <div class="photo-card">
                    <div class="photo-title">🔹 {code}. {title}</div>
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
                st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

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
            st.subheader("🎬 15초 9:16 세로 숏폼 영상 (네이버 클립 / 릴스 / 쇼츠용)")
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
