import whisper
import os

def transcribe_video(video_path: str, source_lang: str = None) -> tuple[str, str] | None:
    """
    Transcribes the video using openai-whisper.
    Saves the transcription as 'source.srt'.
    Returns the path to the SRT file and the detected language.
    """
    model_name = os.getenv("WHISPER_MODEL", "large")
    output_dir = os.path.dirname(video_path)
    
    try:
        model = whisper.load_model(model_name, device="cuda")
        # If source_lang is provided, use it; otherwise, let Whisper detect the language
        transcribe_options = {"verbose": True}
        if source_lang:
            transcribe_options["language"] = source_lang
            
        result = model.transcribe(video_path, **transcribe_options)
        detected_lang = result.get("language")

        srt_path = os.path.join(output_dir, "source.srt")
        with open(srt_path, "w", encoding="utf-8") as srt_file:
            # A simple SRT writer, can be improved.
            for i, segment in enumerate(result["segments"]):
                start = segment['start']
                end = segment['end']
                text = segment['text']
                
                srt_file.write(f"{i + 1}\n")
                srt_file.write(f"{format_timestamp(start)} --> {format_timestamp(end)}\n")
                srt_file.write(f"{text.strip()}\n\n")

        return srt_path, detected_lang
    except Exception as e:
        print(f"Error during transcription: {e}")
        return None

def format_timestamp(seconds: float) -> str:
    """Converts seconds to SRT timestamp format."""
    assert seconds >= 0, "non-negative timestamp expected"
    milliseconds = round(seconds * 1000.0)

    hours = milliseconds // 3_600_000
    milliseconds %= 3_600_000

    minutes = milliseconds // 60_000
    milliseconds %= 60_000

    seconds = milliseconds // 1_000
    milliseconds %= 1_000

    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

