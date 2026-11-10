import argparse
import os
from engine import (
    scrape_naver_blog,
    generate_titles_and_content,
    process_and_badge_images,
    create_shortform_video
)

def main():
    parser = argparse.ArgumentParser(description="바로누수 마케팅 원클릭 자동 생성 CLI")
    parser.add_argument("--url", default="https://m.blog.naver.com/dnjswo3482/224052764862", help="바로누수 예전 네이버 블로그 URL")
    parser.add_argument("--region", default="대구 북구 노원동", help="타겟 지역 (예: 대구 북구 노원동)")
    parser.add_argument("--brand", default="바로누수설비", help="업체 상호")
    parser.add_argument("--style", default="natural", choices=["natural", "banner", "clean"], help="사진 편집 스타일")
    parser.add_argument("--no-video", action="store_true", help="숏폼 영상 제작 생략")
    args = parser.parse_args()

    clean_region = args.region.replace(" ", "_")
    output_dir = f"결과물_{clean_region}"
    os.makedirs(f"{output_dir}/images", exist_ok=True)

    print(f"[*] 1/4. 블로그 원본 분석 및 이미지 추출 중... ({args.url})")
    blog_data = scrape_naver_blog(args.url)
    num_imgs = len(blog_data["images"])
    print(f"[+] 사진 {num_imgs}장 확보 완료!")

    print(f"[*] 2/4. [{args.region}] 실시간 네이버 검색 및 맞춤 원고 작성 중...")
    titles, body_text, steps, serp_titles = generate_titles_and_content(
        region=args.region,
        orig_title=blog_data["title"],
        orig_text=blog_data["text"],
        num_images=num_imgs,
        brand=args.brand
    )

    doc_path = f"{output_dir}/00_제목3선_및_블로그원고.txt"
    with open(doc_path, "w", encoding="utf-8") as f:
        f.write("=== [네이버 스마트블록 추천 제목 3선] ===\n")
        for i, t in enumerate(titles, 1):
            f.write(f"제목 {i}: {t}\n")
        f.write("\n=========================================\n\n")
        f.write(body_text)
    print(f"[+] 원고 저장 완료 (마크다운 기호 없음): {doc_path}")

    print(f"[*] 3/4. 사진 스타일({args.style}) 가공 및 저장 중...")
    processed_images = process_and_badge_images(
        image_urls=blog_data["images"],
        steps=steps,
        brand=args.brand,
        photo_style=args.style
    )
    for item in processed_images:
        fname = item["filename"]
        img_bytes = item["bytes"]
        with open(f"{output_dir}/images/{fname}", "wb") as f:
            f.write(img_bytes)
    print(f"[+] 사진 {len(processed_images)}장 가공 및 저장 완료: {output_dir}/images/")

    if not args.no_video:
        print("[*] 4/4. 릴스·쇼츠용 15초 9:16 숏폼 영상(H.264) 제작 중...")
        video_bytes = create_shortform_video(processed_images, duration=15)
        if video_bytes:
            video_path = f"{output_dir}/숏폼_{clean_region}_15s.mp4"
            with open(video_path, "wb") as vf:
                vf.write(video_bytes)
            print(f"[+] 숏폼 영상 렌더링 완료: {video_path}")

    print(f"\n🎉 모든 작업 완료! 결과물 폴더: {output_dir}")

if __name__ == "__main__":
    main()
