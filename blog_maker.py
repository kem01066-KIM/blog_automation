import os
import sys
import time
import requests
from bs4 import BeautifulSoup
from PIL import Image, ImageEnhance
import io
import random
import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types
from gtts import gTTS
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips

# 환경변수(.env) 로드
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY or API_KEY == "이곳에_복사한_키를_붙여넣으세요":
    print("❌ 오류: .env 파일에 Gemini API 키를 입력해주세요.")
    sys.exit(1)

# 구글 API 최신 클라이언트 생성
client = genai.Client(api_key=API_KEY)

# ==========================================
# 1. 크롤링 & 이미지 세탁
# ==========================================
def wash_image(image_bytes, output_path):
    try:
        img = Image.open(io.BytesIO(image_bytes))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        w, h = img.size
        img = img.crop((2, 2, w - 2, h - 2))
        
        scale = random.uniform(0.98, 1.02)
        new_size = (int(img.width * scale), int(img.height * scale))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        img = ImageEnhance.Brightness(img).enhance(random.uniform(0.98, 1.02))
        img = ImageEnhance.Color(img).enhance(random.uniform(0.98, 1.02))
        
        img.save(output_path, "JPEG", quality=95)
        return True
    except Exception as e:
        print(f"이미지 세탁 실패: {e}")
        return False

def scrape_and_wash(url, out_dir):
    print("▶ [1/4] 원본 글 내용과 이미지 다운로드 중...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    if "blog.naver.com" in url and "PostView.naver" not in url:
        parts = url.split("/")
        blog_id = parts[-2]
        log_no = parts[-1]
        url = f"https://blog.naver.com/PostView.naver?blogId={blog_id}&logNo={log_no}"
        
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    
    original_text = soup.get_text(separator="\n", strip=True)
    
    images = soup.select('.se-image-resource')
    if not images:
        images = soup.find_all('img', id=lambda x: x and x.startswith('img_'))
        
    # --- 추가 및 변경된 부분 ---
    # 첫 번째 사진은 썸네일로 간주하여 완전히 제외(무시)합니다.
    if len(images) > 0:
        images = images[1:]
        
    count = 2  # 폴더에 저장되는 사진 번호를 2번부터 시작
    # ---------------------------
    
    washed_image_paths = []
    
    for img_tag in images:
        src = img_tag.get('data-lazy-src') or img_tag.get('src')
        if src and "postfiles.pstatic.net" in src:
            img_res = requests.get(src, headers=headers)
            if img_res.status_code == 200:
                out_path = os.path.join(out_dir, f"이미지_{count}.jpg")
                if wash_image(img_res.content, out_path):
                    washed_image_paths.append(out_path)
                count += 1
                
    print(f"  └ 원본 텍스트 추출 완료 및 총 {len(washed_image_paths)}개의 이미지 세탁 완료!")
    return original_text, washed_image_paths


# ==========================================
# 2. AI 원고 생성 (최신 API 방식)
# ==========================================
def generate_blog_post(original_text, region, keyword, num_images):
    print("▶ [2/4] AI가 새 원고와 영상 대본을 작성 중입니다. (약 30초 소요)...")
    
    # 2번부터 시작하므로 마지막 이미지 번호 계산
    last_img_num = num_images + 1 if num_images > 0 else 0
    
    prompt = f"""
    너는 네이버 블로그 검색 노출(SEO) 및 AI 검색(CUE:) 최적화의 최고 전문가야.
    내가 제공하는 [원본 글 내용]의 맥락과 흐름을 그대로 유지하되, 모든 배경과 정보를 [{region}]에 맞춰 완전히 새로운 글로 다시 작성해줘.

    다음 규칙을 무조건 지켜야 해:
    1. 글 가장 최상단에 방문자의 클릭을 유도할 수 있는 매력적인 블로그 제목 3가지를 추천해서 적어줘 (예: 💡 추천 제목 1: ...).
    2. 추천 제목들 바로 아래에 핵심 요약 3줄을 적고, 그 아래에 본문 내용을 한눈에 볼 수 있는 마크다운 표를 삽입해 (표의 행(Row)은 반드시 3~4개로만 아주 짧고 간결하게 작성할 것).
    3. 메인 키워드 "[{keyword}]"를 본문에 4~5회 자연스럽게 반복 (이때 단어 사이의 띄어쓰기를 임의로 없애지 말고, 제시된 형태 그대로 반드시 유지할 것).
    4. 공백 제외 최소 1500자 이상 상세하게. "최상", "최고", 욕설 절대 금지.
    5. 서브 제목은 이모지와 대괄호(예: 📌 [새로운 지역])로 강조, 한 문단이 짧게 자주 줄바꿈.
    6. 전체 텍스트는 <div style="text-align: center;"> 로 시작해서 </div>로 끝나도록 감쌀 것 (가운데 정렬).
    7. 글 맨 앞부분에 `[대표 썸네일 이미지]`, 내용 흐름에 맞춰 `[이미지 2]` 부터 `[이미지 {last_img_num}]` 까지 수집된 모든 이미지의 삽입 위치 마커를 문맥에 맞게 골고루 분산해서 전부 추가해. 글 마지막 줄 전에는 `[요약 영상]` 마커 추가.
    8. 글 마지막에 관련된 해시태그 5개 작성.
    9. **[매우 중요] 글이 모두 끝난 뒤 </div> 바깥쪽에, 반드시 `---대본---` 이라고 적고 그 아래에 영상에 들어갈 15초 분량(3~4문장)의 낭독용 나레이션 대본만 따로 적어줄 것.**

    [입력 데이터]
    - 원본 글 내용: {original_text[:3000]}
    - 새로운 지역: {region}
    - 메인 키워드: {keyword}
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.7,
            top_p=0.9,
            top_k=50,
            max_output_tokens=8192,
        )
    )
    return response.text


# ==========================================
# 3. 동영상 생성 (TTS + 슬라이드쇼)
# ==========================================
def make_video(tts_text, image_paths, out_dir, thumbnail_path=""):
    print("[3/4] 요약 영상을 렌더링 중입니다...")
    
    if thumbnail_path:
        if os.path.exists(thumbnail_path):
            print("  - 사용자 제공 썸네일을 영상 맨 앞에 성공적으로 배치합니다!")
            image_paths = [thumbnail_path] + image_paths
        else:
            print(f"  - 에러: 썸네일 사진을 찾을 수 없어서 건너뜁니다! (입력된 경로: [{thumbnail_path}])")

    if not image_paths or not tts_text:
        print("  - 이미지나 대본이 없어 영상 제작을 건너뜁니다.")
        return
        
    try:
        from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, vfx
        import tempfile
        
        audio_path = os.path.join(out_dir, "temp_voice.mp3")
        tts = gTTS(text=tts_text, lang='ko')
        tts.save(audio_path)
        
        audio = AudioFileClip(audio_path)
        audio = audio.fx(vfx.speedx, 1.25)
        duration = audio.duration
        
        time_per_image = duration / len(image_paths)
        
        temp_paths = []
        for i, img_path in enumerate(image_paths):
            img = Image.open(img_path).convert("RGB")
            img.thumbnail((1080, 1080), Image.Resampling.LANCZOS)
            
            bg = Image.new("RGB", (1080, 1080), (0, 0, 0))
            offset_x = (1080 - img.width) // 2
            offset_y = (1080 - img.height) // 2
            bg.paste(img, (offset_x, offset_y))
            
            temp_path = os.path.join(out_dir, f"temp_vid_img_{i}.jpg")
            bg.save(temp_path, "JPEG", quality=95)
            temp_paths.append(temp_path)
            
        clips = []
        for tmp_img in temp_paths:
            clips.append(ImageClip(tmp_img).set_duration(time_per_image))
            
        final_clip = concatenate_videoclips(clips, method="chain")
        final_clip = final_clip.set_audio(audio)
        
        video_path = os.path.join(out_dir, "요약영상.mp4")
        safe_temp_audio = os.path.join(tempfile.gettempdir(), "safe_temp_audio.mp4")
        
        final_clip.write_videofile(
            video_path, 
            fps=24, 
            codec="libx264", 
            audio_codec="aac", 
            temp_audiofile=safe_temp_audio,
            logger=None
        )
        
        audio.close()
        final_clip.close()
        os.remove(audio_path)
        
        for tmp in temp_paths:
            if os.path.exists(tmp):
                os.remove(tmp)
                
        print("  - 요약 영상(mp4) 제작 완료!")
    except Exception as e:
        print(f"  - 영상 제작 실패 (MoviePy 오류): {e}")


# ==========================================
# 메인 실행
# ==========================================
def main():
    print("\n" + "="*50)
    print("   네이버 블로그 재생성 자동화 프로그램 (키워드 선택 기능)")
    print("="*50 + "\n")
    
    while True:
        url = input("\n1. 참고할 원본 네이버 블로그 URL을 입력하세요 (종료하려면 엔터): ").strip()
        if not url:
            break
            
        region = input("2. 타겟으로 하는 새로운 지역명을 입력하세요 (예: 부산 해운대): ").strip()
        
        # 💡 누수 vs 하수구막힘 선택 기능 추가!
        while True:
            choice = input("3. 작업할 키워드를 선택하세요 (1: 누수,  2: 하수구막힘): ").strip()
            if choice == '1':
                keyword = f"{region} 누수"
                break
            elif choice == '2':
                keyword = f"{region} 하수구막힘"
                break
            else:
                print("  - 잘못된 입력입니다. 숫자 1 또는 2를 입력해주세요.")
        
        print(f"\n- 메인 키워드가 최종 [{keyword}] 로 설정되었습니다.")
        
        print("\n작업을 시작합니다! (약 1~2분 소요됩니다)")
        
        today = datetime.datetime.now().strftime("%m%d")
        folder_name = f"{today}_{keyword}"
        base_dir = os.path.dirname(os.path.abspath(__file__))
        out_dir = os.path.join(base_dir, folder_name)
        
        if not os.path.exists(out_dir):
            os.makedirs(out_dir)
            
        print(f"\n- 작업 폴더 생성됨: {out_dir}")
        
        thumbnail_path = os.path.join(base_dir, "대표.jpg")
        if os.path.exists(thumbnail_path):
            print(f"- 블로그자동화 폴더 안에서 [대표.jpg] 파일이 발견되어, 영상 맨 앞에 자동으로 장착됩니다!")
        else:
            thumbnail_path = ""
        
        original_text, image_paths = scrape_and_wash(url, out_dir)
        
        ai_result = generate_blog_post(original_text, region, keyword, len(image_paths))
        
        import re
        parts = re.split(r'-+\s*대본\s*-*', ai_result)
        
        blog_text = parts[0].strip()
        tts_text = parts[1].strip() if len(parts) > 1 else ""
        
        txt_path = os.path.join(out_dir, "원고.txt")
        with open(txt_path, "w", encoding="utf-8") as f:
            f.write(blog_text)
        print("  - 원고(.txt) 작성 및 저장 완료!")
        
        make_video(tts_text, image_paths, out_dir, thumbnail_path)
        
        print("\n" + "="*50)
        print(" 이번 작업이 완벽하게 완료되었습니다!")
        print(f" 생성된 [{folder_name}] 폴더를 확인해 주세요!")
        print("="*50 + "\n")
        
        answer = input("다른 글로 작업을 계속하시겠습니까? (y/n, 그냥 엔터치면 계속!): ").strip().lower()
        if answer == 'n':
            print("\n수고하셨습니다. 프로그램을 완전히 종료합니다.")
            break
            
        print("\n" + "-"*50)




if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        input("\n[안내] 프로그램이 종료되었습니다. 창을 닫으려면 엔터 키를 누르세요...")




