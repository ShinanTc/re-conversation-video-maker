import os
import re
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageSequenceClip
from groq import Groq

# =========================
# LOAD ENV VARIABLES
# =========================
load_dotenv()

# =========================
# CONFIG
# =========================
IMG_DIR = "IMG"
OUTPUT_DIR = "output"
FRAMES_DIR = os.path.join(OUTPUT_DIR, "frames")
FONT_PATH = "fonts/comic.ttf"

EMOTIONS = ["exhausted", "curious", "confused", "happy"]

os.makedirs(FRAMES_DIR, exist_ok=True)

# =========================
# GROQ CLIENT
# =========================
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
emotion_cache = {}

# =========================
# PARSE TXT
# =========================
def parse_conversations(file_path):
    dialogues = []

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        match = re.match(r'(AD|T):\s*"(.*)"', line.strip())
        if match:
            speaker = match.group(1)
            text = match.group(2)
            dialogues.append((speaker, text))

    return dialogues

# =========================
# AI EMOTION DETECTION
# =========================
def detect_emotion(text):
    if text in emotion_cache:
        return emotion_cache[text]

    prompt = f"""
Classify the emotional tone of this dialogue into EXACTLY one of:

exhausted → tired, stuck, lost, overwhelmed
curious → asking, wondering, seeking
confused → unsure, doubtful, processing
happy → relief, clarity, excitement

Return ONLY one word.

Text:
"{text}"
"""

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        emotion = response.choices[0].message.content.strip().lower()

        if emotion not in EMOTIONS:
            emotion = "exhausted"

    except Exception as e:
        print(f"[ERROR] Emotion detection failed: {e}")
        emotion = "exhausted"

    emotion_cache[text] = emotion
    return emotion

# =========================
# TEXT DRAWING (WITH BOUNDARIES)
# =========================
def draw_text_in_box(draw, text, font, box):
    x1, y1, x2, y2 = box
    max_width = x2 - x1

    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]

        if width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    # Draw from bottom
    y_text = y2 - 10

    for line in reversed(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        x_text = x1 + (x2 - x1 - text_w) // 2
        y_text -= text_h

        draw.text((x_text, y_text), line, font=font, fill="black")

# =========================
# CREATE FRAME
# =========================
def create_frame(text, speaker, emotion, index):
    base_img_path = os.path.join(IMG_DIR, f"{emotion}.png")

    if not os.path.exists(base_img_path):
        print(f"[WARNING] Missing image for emotion '{emotion}', using exhausted.")
        base_img_path = os.path.join(IMG_DIR, "exhausted.png")

    img = Image.open(base_img_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype(FONT_PATH, 42)

    W, H = img.size

    # AD → bottom-left | T → bottom-right
    if speaker == "AD":
        box = (
            0,
            int(H * 0.6),
            int(W * 0.5),
            H
        )
    else:
        box = (
            int(W * 0.5),
            int(H * 0.6),
            W,
            H
        )

    draw_text_in_box(draw, text, font, box)

    output_path = os.path.join(FRAMES_DIR, f"{index:03d}.png")
    img.save(output_path)

    return output_path

# =========================
# CREATE VIDEO
# =========================
def create_video(frame_paths):
    clip = ImageSequenceClip(frame_paths, fps=1/3)  # 3 sec per frame
    output_video_path = os.path.join(OUTPUT_DIR, "final.mp4")

    clip.write_videofile(output_video_path, codec="libx264")

# =========================
# MAIN PIPELINE
# =========================
import os
import re
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageSequenceClip
from groq import Groq

# =========================
# LOAD ENV VARIABLES
# =========================
load_dotenv(dotenv_path=".env")

# =========================
# CONFIG
# =========================
IMG_DIR = "IMG"
OUTPUT_DIR = "output"
FRAMES_DIR = os.path.join(OUTPUT_DIR, "frames")
FONT_PATH = "fonts/comic.ttf"

EMOTIONS = ["exhausted", "curious", "confused", "happy"]

os.makedirs(FRAMES_DIR, exist_ok=True)

# =========================
# GROQ CLIENT
# =========================
api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found. Check your .env file.")

client = Groq(api_key=api_key)
emotion_cache = {}

# =========================
# PARSE TXT (ROBUST)
# =========================
def parse_conversations(file_path):
    dialogues = []

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()

        if not line:
            continue

        match = re.match(r'^(AD|T)\s*:\s*["“]?(.+?)["”]?$', line)

        if match:
            speaker = match.group(1)
            text = match.group(2).strip()
            dialogues.append((speaker, text))
        else:
            print(f"[SKIPPED LINE] -> {line}")

    return dialogues

# =========================
# AI EMOTION DETECTION
# =========================
def detect_emotion(text):
    if text in emotion_cache:
        return emotion_cache[text]

    prompt = f"""
Classify the emotional tone of this dialogue into EXACTLY one of:

exhausted → tired, stuck, lost, overwhelmed
curious → asking, wondering, seeking
confused → unsure, doubtful, processing
happy → relief, clarity, excitement

Return ONLY one word.

Text:
"{text}"
"""

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        emotion = response.choices[0].message.content.strip().lower()

        if emotion not in EMOTIONS:
            emotion = "exhausted"

    except Exception as e:
        print(f"[ERROR] Emotion detection failed: {e}")
        emotion = "exhausted"

    emotion_cache[text] = emotion
    return emotion

# =========================
# TEXT DRAWING (TOP HALF)
# =========================
def draw_text_in_box(draw, text, font, box):
    x1, y1, x2, y2 = box
    max_width = x2 - x1

    words = text.split()
    lines = []
    current_line = ""

    # Wrap text
    for word in words:
        test_line = current_line + (" " if current_line else "") + word
        bbox = draw.textbbox((0, 0), test_line, font=font)
        width = bbox[2] - bbox[0]

        if width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    # Draw from bottom of TOP box
    y_text = y2 - 20  # padding from bottom of top-half box

    for line in reversed(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]

        x_text = x1 + (x2 - x1 - text_w) // 2
        y_text -= text_h

        draw.text((x_text, y_text), line, font=font, fill="black")

# =========================
# CREATE FRAME
# =========================
def create_frame(text, speaker, emotion, index):
    base_img_path = os.path.join(IMG_DIR, f"{emotion}.png")

    if not os.path.exists(base_img_path):
        print(f"[WARNING] Missing image for emotion '{emotion}', using exhausted.")
        base_img_path = os.path.join(IMG_DIR, "exhausted.png")

    img = Image.open(base_img_path).convert("RGB")
    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype(FONT_PATH, 42)

    W, H = img.size

    # TOP HALF ONLY
    if speaker == "AD":
        box = (
            0,
            0,
            int(W * 0.5),
            int(H * 0.4)
        )
    else:
        box = (
            int(W * 0.5),
            0,
            W,
            int(H * 0.4)
        )

    draw_text_in_box(draw, text, font, box)

    output_path = os.path.join(FRAMES_DIR, f"{index:03d}.png")
    img.save(output_path)

    return output_path

# =========================
# CREATE VIDEO
# =========================
def create_video(frame_paths):
    clip = ImageSequenceClip(frame_paths, fps=1/3)  # 3 sec per frame
    output_video_path = os.path.join(OUTPUT_DIR, "final.mp4")

    clip.write_videofile(output_video_path, codec="libx264")

# =========================
# MAIN PIPELINE
# =========================
def main():
    print("Parsing conversations...")
    dialogues = parse_conversations("conversations.txt")

    if not dialogues:
        print("No valid dialogues found.")
        return

    print(f"Processing {len(dialogues)} dialogue lines...")

    frame_paths = []

    for i, (speaker, text) in enumerate(dialogues):
        print(f"{speaker}: {text}")

        if speaker == "AD":
            emotion = detect_emotion(text)
        else:
            emotion = "exhausted"

        frame_path = create_frame(text, speaker, emotion, i)
        frame_paths.append(frame_path)

    print("Creating video...")
    create_video(frame_paths)

    print("Done! Check output/final.mp4")

# =========================
# RUN
# =========================
if __name__ == "__main__":
    main()