from youtube_transcript_api import YouTubeTranscriptApi
import re
from typing import Optional

# Updated: 2025-01-17 - Fixed FetchedTranscriptSnippet usage

def get_video_id(url: str) -> Optional[str]:
    """
    Extracts the video ID from a YouTube URL.
    """
    patterns = [
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
        r'(?:https?:\/\/)?(?:www\.)?youtube\.com\/v\/([a-zA-Z0-9_-]{11})'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def get_transcript(video_id: str) -> str:
    """
    Fetches the transcript for a given YouTube video ID.
    """
    try:
        print(f"Fetching transcript for video ID: {video_id}")
        
        # Try to get transcript with old API version
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
            full_transcript = " ".join([item['text'] for item in transcript_list])
            print(f"Found English transcript, length: {len(full_transcript)} characters")
            return full_transcript
        except Exception as e:
            print(f"English transcript failed: {e}")
        
        # Try any language
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            full_transcript = " ".join([item['text'] for item in transcript_list])
            print(f"Found any transcript, length: {len(full_transcript)} characters")
            return full_transcript
        except Exception as e:
            print(f"Any transcript failed: {e}")
            
        print("No transcripts found for this video")
        return ""
        
    except Exception as e:
        print(f"Error fetching transcript: {e}")
        return "" 