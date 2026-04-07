# Conversation Video Generator

## How to Use

1. Add your conversations to `conversations.txt`
2. Run `python main.py`

That's it. The script automatically detects whether to generate a single video or multiple videos based on what's in the file.

---

## Single Video

Just write your dialogue straight into `conversations.txt` with no separators:

```
AD: "Why do I feel like I'm wasting time?"
T: "Because your days look the same."

AD: "But I'm doing things."
T: "Doing doesn't always mean experiencing."
```

Output: `output/final.mp4`

---

## Multiple Videos

Separate each video's conversation block with a `---` line:

```
AD: "Why does my life feel… stuck?"
T: "Because you stopped exploring."

AD: "Exploring what? I go out, I hang out…"
T: "Not places. Yourself."
--------------------
AD: "That sounds uncomfortable."
T: "Exactly. That's where you meet the version of you that isn't stuck."
```

Output: `output/final_1.mp4`, `output/final_2.mp4`, and so on.

---

## Requirements

- Add your Groq API key to a `.env` file:
  ```
  GROQ_API_KEY=your_key_here
  ```
- Emotion images (`exhausted.png`, `curious.png`, `confused.png`, `happy.png`) must be present in the `IMG/` folder
- Font file must be present at `fonts/comic.ttf`

# TODO
* ⁠Reduce the text appearance at a time