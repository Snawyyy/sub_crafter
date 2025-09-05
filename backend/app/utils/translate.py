import google.generativeai as genai
import os

def translate_srt(srt_path: str, target_lang: str, source_lang: str = "en") -> str | None:
    """
    Translates an SRT file using the Gemini API.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment.")
        return None

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-2.5-flash')

    try:
        with open(srt_path, "r", encoding="utf-8") as f:
            srt_content = f.read()

        prompt = f"""Translate the following SRT subtitles from {source_lang} into {target_lang}.

**Instructions:**
- **Do not translate literally.** Preserve the original's tone, vibe, and meaning.
- **Adapt cultural references, slang, and jokes** to be natural and meaningful in {target_lang}.
- **Maintain the SRT format perfectly.** Do not change timecodes or entry numbers.

**SRT Content:**
{srt_content}"""
        
        response = model.generate_content(prompt)
        
        translated_srt_content = response.text.strip()
        if not translated_srt_content:
            print("Error: Gemini API returned an empty translation.")
            return None

        translated_srt_path = srt_path.replace("source.srt", f"translated_{target_lang}.srt")

        with open(translated_srt_path, "w", encoding="utf-8") as f:
            f.write(translated_srt_content)
            
        return translated_srt_path

    except Exception as e:
        print(f"Error during translation: {e}")
        return None

