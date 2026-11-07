import argparse
import os
import zipfile
import io
from app import scrape_naver_blog, generate_titles_and_content, process_and_badge_images, create_shortform_video

def main():
    parser = argparse.ArgumentParser(description="바로누수 마케팅 원클릭 자동 생성 CLI")
    parser.add_argument("--url", required=True, help="바로누수 예전 네이버 블로그 URL")
    parser.add_argument("--region", default="대구 북구 노원동", help="타겟 지역 (예: 대구 북구 노원동)")
    parser.add_argument("--brand", default="바로누수설비", help="업체 상호")
    parser.add_argument("--phone", default="010-3815-1154", help="문의 전화번호")
    parser.add_argument("--no-video", action="store_true", help="숏폼 영상 제작 생략")
    args = parser.parse_args()

    clean_region = args.region.replace(" ", "_")
    output_dir = f"결과물_{clean_region}"
    os.makedirs(f"{output_dir}/images", exist_ok=True)

    print(f"[*] 1/4. 블로그 원본 분석 및 이미지 추출 중... ({args.url})")
    blog_data = scrape_naver_blog(args.url)
    num_imgs = len(blog_data["images"])
    print(f"[+] 사진 {num_imgs}장 확보 완료!")

    print(f"[*] 2/4. SEO/GEO 기반 제목 3선 및 5단계 본문 작성 중... (지역: {args.region})")
    titles, body_text, steps = generate_titles_and_content(
        region=args.region,
        orig_title=blog_data["title"],
        orig_text=blog_data["text"],
        num_images=num_imgs,
        brand=args.brand,
        phone=args.phone
    )

    # 1. 제목 및 본문 파일 저장
    doc_path = f"{output_dir}/00_제목3선_및_블로그원고.txt"
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write("=== [네이버 스마트블록 추천 제목 3선] ===\n")
        for i, t in enumerate(titles, 1):
            f.write(f"제목 {i}: {t}\n")
        f.write("\n=========================================\n\n")
        f.write(body_text)
    print(f"[+] 원고 저장 완료: {doc_path}")

    print("[*] 3/4. 사진 대비 보정 및 STEP 자막 라벨 합성 중...")
    processed_images = process_and_badge_images(blog_data["images"], steps, brand=args.brand)
    for fname, pimg in processed_images:
        pimg.save(f"{output_dir}/images/{fname}", quality=92)
    print(f"[+] 사진 {len(processed_images)}장 가공 및 저장 완료: {output_dir}/images/")

    if not args.no_video:
        print("[*] 4/4. 릴스·쇼츠용 15초 9:16 숏폼 영상 제작 중...")
        video_path = f"{output_dir}/숏폼_{clean_region}_15s.mp4"
        create_shortform_video(processed_images, video_path, duration=15)
        print(f"[+] 숏폼 영상 렌더링 완료: {video_path}")

    # 전체 압축파일 생성
    zip_path = f"{output_dir}/{clean_region}_마케팅패키지.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(doc_path, arcname="00_제목3선_및_블로그원고.txt")
        for fname, _ in processed_images:
            zf.write(f"{output_dir}/images/{fname}", arcname=f"images/{fname}")
        if not args.no_video and os.path.exists(video_path):
            zf.write(video_path, arcname="shortform_video.mp4")

    print(f"\n🎉 모든 작업 완료! 패키지 압축파일: {zip_path}")

if __name__ == "__main__":
    main()
