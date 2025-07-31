from youtube_transcript_api import YouTubeTranscriptApi
import re
from typing import Optional, Dict, Any

# Updated: 2025-01-17 - Fixed FetchedTranscriptSnippet usage

class YouTubeService:
    def __init__(self):
        pass

    def get_video_id(self, url: str) -> Optional[str]:
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

    def get_transcript(self, video_id: str) -> Dict[str, Any]:
        """
        Fetches the transcript for a given YouTube video ID.
        Returns a dictionary with success status and transcript or error message.
        """
        try:
            print(f"Fetching transcript for video ID: {video_id}")
            
            # Try to get transcript with English first
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
                full_transcript = " ".join([item['text'] for item in transcript_list])
                print(f"Found English transcript, length: {len(full_transcript)} characters")
                return {
                    "success": True,
                    "transcript": full_transcript,
                    "language": "en"
                }
            except Exception as e:
                print(f"English transcript failed: {e}")
            
            # Try any available language
            try:
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
                full_transcript = " ".join([item['text'] for item in transcript_list])
                print(f"Found transcript in available language, length: {len(full_transcript)} characters")
                return {
                    "success": True,
                    "transcript": full_transcript,
                    "language": "auto"
                }
            except Exception as e:
                print(f"Any language transcript failed: {e}")
                
            return {
                "success": False,
                "error": "No transcripts available for this video",
                "transcript": ""
            }
            
        except Exception as e:
            error_message = f"Error fetching transcript: {str(e)}"
            print(error_message)
            return {
                "success": False,
                "error": error_message,
                "transcript": ""
            }

# Backward compatibility functions
def get_video_id(url: str) -> Optional[str]:
    """
    Extracts the video ID from a YouTube URL.
    """
    service = YouTubeService()
    return service.get_video_id(url)

def get_transcript(video_id: str) -> str:
    """
    Fetches the transcript for a given YouTube video ID.
    """
    service = YouTubeService()
    result = service.get_transcript(video_id)
    return result.get("transcript", "") 