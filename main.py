import os
import re
import shutil
import sys
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageSequenceClip
from groq import Groq

# =========================
# CONFIG
# =========================
load_dotenv()
sys.stdout.reconfigure(encoding='utf-8')

IMG_DIR = "IMG"
OUTPUT_DIR = "output"
FRAMES_DIR = os.path.join(OUTPUT_DIR, "frames")
FONT_PATH = "fonts/comic.ttf"
EMOTIONS = ["exhausted", "curious", "confused", "happy"]
CONVERSATIONS_FILE = "conversations.txt"

os.makedirs(FRAMES_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# =========================
# GROQ CLIENT
# =========================
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found. Check your .env file.")

client = Groq(api_key=api_key)
emotion_cache = {}


# =========================
# PARSE CONVERSATIONS
# Always returns a list of sets.
# Single video  → one set  → [[...dialogues...]]
# Bulk videos   → N sets   → [[...], [...], ...]
# =========================
def parse_conversations(file_path):
    conversation_sets = []
    current_set = []

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if line.startswith("---"):
                if current_set:
                    conversation_sets.append(current_set)
                    current_set = []
                continue

            if not line:
                continue

            match = re.match(r'^(AD|T)\s*:\s*[""]?(.+?)[""]?$', line)
            if match:
                current_set.append((match.group(1), match.group(2).strip()))
            else:
                print(f"[SKIPPED LINE] -> {line}")

    if current_set:
        conversation_sets.append(current_set)

    return conversation_sets


# =========================
# EMOTION DETECTION
# =========================
def detect_emotion(text):
    if text in emotion_cache:
        return emotion_cache[text]

    prompt = f"""Classify the emotional tone of this dialogue into EXACTLY one of:

exhausted → tired, stuck, lost, overwhelmed
curious → asking, wondering, seeking
confused → unsure, doubtful, processing
happy → relief, clarity, excitement

Return ONLY one word.

Text: "{text}"
"""
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
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
# TEXT DRAWING
# =========================
def draw_text_in_box(draw, text, font, box):
    x1, y1, x2, y2 = box
    max_width = x2 - x1

    words = text.split()
    lines = []
    current_line = ""

    for word in words:
        test_line = f"{current_line} {word}".strip()
        width = draw.textbbox((0, 0), test_line, font=font)[2]
        if width <= max_width:
            current_line = test_line
        else:
            lines.append(current_line)
            current_line = word

    if current_line:
        lines.append(current_line)

    y_text = y2 - 20
    for line in reversed(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x_text = x1 + (max_width - text_w) // 2
        y_text -= text_h
        draw.text((x_text, y_text), line, font=font, fill="#113426")


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
    font = ImageFont.truetype(FONT_PATH, 32)
    W, H = img.size

    box = (0, 0, int(W * 0.5), int(H * 0.4)) if speaker == "AD" else (int(W * 0.5), 0, W, int(H * 0.4))

    draw_text_in_box(draw, text, font, box)

    output_path = os.path.join(FRAMES_DIR, f"{index:03d}.png")
    img.save(output_path)
    return output_path


# =========================
# CLEAR FRAMES
# =========================
def clear_frames():
    if os.path.exists(FRAMES_DIR):
        shutil.rmtree(FRAMES_DIR)
    os.makedirs(FRAMES_DIR, exist_ok=True)


# =========================
# CREATE VIDEO
# =========================
def create_video(frame_paths, output_filename):
    clip = ImageSequenceClip(frame_paths, fps=1/3)
    output_path = os.path.join(OUTPUT_DIR, output_filename)
    clip.write_videofile(output_path, codec="libx264")
    print(f"Saved → {output_path}")


# =========================
# PROCESS A SINGLE SET
# =========================
def process_set(dialogues, set_index, is_bulk):
    label = f"set {set_index + 1}" if is_bulk else "conversation"
    print(f"\nProcessing {label} ({len(dialogues)} lines)...")

    clear_frames()
    frame_paths = []
    last_emotion = "exhausted"
    first_ad_seen = False

    for i, (speaker, text) in enumerate(dialogues):
        print(f"  {speaker}: {text}")
        if speaker == "AD":
            if first_ad_seen:
                last_emotion = detect_emotion(text)
            else:
                # First AD line always uses exhausted; start tracking from the next one
                first_ad_seen = True
        frame_paths.append(create_frame(text, speaker, last_emotion, i))

    output_filename = f"final_{set_index + 1}.mp4" if is_bulk else "final.mp4"
    create_video(frame_paths, output_filename)


# =========================
# MAIN
# =========================
def main():
    print(f"Reading {CONVERSATIONS_FILE}...")
    conversation_sets = parse_conversations(CONVERSATIONS_FILE)

    if not conversation_sets:
        print("No valid conversations found.")
        return

    is_bulk = len(conversation_sets) > 1
    mode = f"BULK ({len(conversation_sets)} videos)" if is_bulk else "SINGLE video"
    print(f"Mode detected: {mode}")

    for set_index, dialogues in enumerate(conversation_sets):
        process_set(dialogues, set_index, is_bulk)

    print("\nDone! All videos generated.")


if __name__ == "__main__":
    main()