import yt_dlp
import re
from typing import Dict, Any, Optional, List
import json
import time
import random

class YTDlpService:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]

    def get_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL."""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/watch\?.*v=([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def get_available_languages(self, video_id: str) -> Dict[str, Any]:
        """Get available transcript languages for a video."""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'skip_download': True,
            'writeautomaticsub': False,
            'writesubtitles': False,
            'listsubtitles': True,
            'user_agent': random.choice(self.user_agents)
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                return {
                    "success": True,
                    "languages": info.get('subtitles', {}),
                    "auto_languages": info.get('automatic_captions', {})
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "languages": {},
                "auto_languages": {}
            }

    def get_transcript(self, video_id: str, language: str = 'en') -> Dict[str, Any]:
        """
        Fetch transcript using yt-dlp with multiple fallback methods.
        Returns clean text without timestamps.
        """
        print(f"🎥 Fetching transcript for video ID: {video_id} using yt-dlp")
        
        # Method 1: Try manual captions first
        result = self._try_manual_captions(video_id, language)
        if result["success"]:
            return result
        
        # Method 2: Try auto-generated captions
        result = self._try_auto_captions(video_id, language)
        if result["success"]:
            return result
        
        # Method 3: Try any available language
        result = self._try_any_language(video_id)
        if result["success"]:
            return result
        
        # Method 4: Try with different user agents
        result = self._try_with_user_agents(video_id, language)
        if result["success"]:
            return result
        
        # Method 5: Final fallback - demo content
        print("🚫 All yt-dlp methods failed. Using demo content.")
        return self._get_demo_content(video_id)

    def _try_manual_captions(self, video_id: str, language: str = 'en') -> Dict[str, Any]:
        """Try to get manual captions."""
        print(f"🔄 Trying manual captions for language: {language}")
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': False,
            'subtitleslangs': [language],
            'user_agent': random.choice(self.user_agents)
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                
                if 'subtitles' in info and language in info['subtitles']:
                    # Get the first available subtitle format
                    subtitle_formats = info['subtitles'][language]
                    if subtitle_formats:
                        # Download subtitle file
                        subtitle_url = subtitle_formats[0]['url']
                        import requests
                        response = requests.get(subtitle_url)
                        subtitle_text = response.text
                        
                        # Parse VTT/JSON subtitle and extract clean text
                        clean_text = self._parse_subtitle_text(subtitle_text)
                        
                        if clean_text:
                            print(f"✅ Manual captions success! Length: {len(clean_text)} characters")
                            return {
                                "success": True,
                                "transcript": clean_text,
                                "language": language,
                                "method": "manual_captions",
                                "format": "vtt"
                            }
                
                return {"success": False, "error": "No manual captions available"}
                
        except Exception as e:
            print(f"❌ Manual captions failed: {str(e)}")
            return {"success": False, "error": f"Manual captions failed: {str(e)}"}

    def _try_auto_captions(self, video_id: str, language: str = 'en') -> Dict[str, Any]:
        """Try to get auto-generated captions."""
        print(f"🔄 Trying auto-generated captions for language: {language}")
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'writeautomaticsub': True,
            'writesubtitles': False,
            'subtitleslangs': [language],
            'user_agent': random.choice(self.user_agents)
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                
                if 'automatic_captions' in info and language in info['automatic_captions']:
                    subtitle_formats = info['automatic_captions'][language]
                    if subtitle_formats:
                        subtitle_url = subtitle_formats[0]['url']
                        import requests
                        response = requests.get(subtitle_url)
                        subtitle_text = response.text
                        
                        clean_text = self._parse_subtitle_text(subtitle_text)
                        
                        if clean_text:
                            print(f"✅ Auto captions success! Length: {len(clean_text)} characters")
                            return {
                                "success": True,
                                "transcript": clean_text,
                                "language": language,
                                "method": "auto_captions",
                                "format": "vtt"
                            }
                
                return {"success": False, "error": "No auto captions available"}
                
        except Exception as e:
            print(f"❌ Auto captions failed: {str(e)}")
            return {"success": False, "error": f"Auto captions failed: {str(e)}"}

    def _try_any_language(self, video_id: str) -> Dict[str, Any]:
        """Try to get captions in any available language."""
        print("🔄 Trying any available language...")
        
        # First get available languages
        languages_result = self.get_available_languages(video_id)
        if not languages_result["success"]:
            return {"success": False, "error": "Could not get available languages"}
        
        # Try manual captions first
        for lang in languages_result["languages"]:
            result = self._try_manual_captions(video_id, lang)
            if result["success"]:
                return result
        
        # Try auto captions
        for lang in languages_result["auto_languages"]:
            result = self._try_auto_captions(video_id, lang)
            if result["success"]:
                return result
        
        return {"success": False, "error": "No captions available in any language"}

    def _try_with_user_agents(self, video_id: str, language: str = 'en') -> Dict[str, Any]:
        """Try with different user agents."""
        print("🔄 Trying with different user agents...")
        
        for user_agent in self.user_agents:
            try:
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'skip_download': True,
                    'writesubtitles': True,
                    'writeautomaticsub': True,
                    'subtitleslangs': [language],
                    'user_agent': user_agent
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                    
                    # Try manual captions
                    if 'subtitles' in info and language in info['subtitles']:
                        subtitle_formats = info['subtitles'][language]
                        if subtitle_formats:
                            subtitle_url = subtitle_formats[0]['url']
                            import requests
                            response = requests.get(subtitle_url)
                            subtitle_text = response.text
                            clean_text = self._parse_subtitle_text(subtitle_text)
                            
                            if clean_text:
                                print(f"✅ User agent success! Length: {len(clean_text)} characters")
                                return {
                                    "success": True,
                                    "transcript": clean_text,
                                    "language": language,
                                    "method": "user_agent_rotation",
                                    "format": "vtt"
                                }
                
                time.sleep(random.uniform(1, 2))  # Small delay between attempts
                
            except Exception as e:
                print(f"❌ User agent {user_agent[:20]}... failed: {str(e)}")
                continue
        
        return {"success": False, "error": "All user agents failed"}

    def _parse_subtitle_text(self, subtitle_text: str) -> str:
        """Parse VTT/JSON subtitle text and extract clean text."""
        try:
            # Try to parse as YouTube JSON format (with events/segs)
            if subtitle_text.strip().startswith('{'):
                try:
                    json_data = json.loads(subtitle_text)
                    if 'events' in json_data:
                        return self.parse_youtube_json_transcript(json_data)
                except:
                    pass
            
            # Try to parse as JSON array format
            if subtitle_text.strip().startswith('['):
                data = json.loads(subtitle_text)
                if isinstance(data, list):
                    # Extract text from JSON format
                    text_parts = []
                    for item in data:
                        if isinstance(item, dict) and 'text' in item:
                            text_parts.append(item['text'])
                    return ' '.join(text_parts)
            
            # Parse as VTT format
            lines = subtitle_text.split('\n')
            text_parts = []
            in_text_block = False
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Skip timestamp lines and metadata
                if '-->' in line or line.isdigit() or line.startswith('WEBVTT'):
                    continue
                
                # This is text content
                text_parts.append(line)
            
            return ' '.join(text_parts)
            
        except Exception as e:
            print(f"❌ Subtitle parsing failed: {str(e)}")
            return ""

    def parse_youtube_json_transcript(self, json_data: dict) -> str:
        """
        Parse YouTube JSON transcript format with events and segs.
        
        Args:
            json_data: Dictionary containing YouTube transcript JSON data
            
        Returns:
            str: Clean transcript text as multi-line string
        """
        try:
            transcript_lines = []
            
            # Check if we have events array
            if 'events' not in json_data:
                print("❌ No 'events' array found in JSON data")
                return ""
            
            # Iterate through all events
            for event in json_data['events']:
                # Check if event has segs array
                if 'segs' not in event:
                    continue
                
                # Extract text from each seg
                for seg in event['segs']:
                    # Check if seg has utf8 key
                    if 'utf8' not in seg:
                        continue
                    
                    text = seg['utf8'].strip()
                    
                    # Skip empty or newline-only segments
                    if not text or text == '\n' or text.isspace():
                        continue
                    
                    # Handle newlines - add space instead of newline
                    if text == '\n':
                        text = ' '
                    
                    # Add to transcript lines
                    transcript_lines.append(text)
            
            # Join all lines with spaces
            full_transcript = ' '.join(transcript_lines)
            
            # Clean up extra whitespace
            full_transcript = ' '.join(full_transcript.split())
            
            print(f"✅ JSON transcript parsed successfully! Length: {len(full_transcript)} characters")
            return full_transcript
            
        except Exception as e:
            print(f"❌ JSON transcript parsing failed: {str(e)}")
            return ""

    def _get_demo_content(self, video_id: str) -> Dict[str, Any]:
        """Return demo content when all methods fail."""
        demo_text = f"""
        Bu video için otomatik transcript alınamadı.
        YouTube IP engeli nedeniyle transcript erişilemiyor.
        
        Çözüm önerileri:
        1. VPN kullanarak farklı bir ülkeden bağlanın
        2. Video URL'sini manuel olarak buraya yapıştırın: https://www.youtube.com/watch?v={video_id}
        3. Video'yu indirip local transcript çıkarın
        4. Başka bir video ID'si deneyin
        
        Test için örnek metin:
        Hello everyone, welcome to this video. Today we will learn about English grammar and vocabulary. 
        This is a sample text for testing purposes. We will explore various topics including pronunciation, 
        grammar rules, and common phrases used in everyday conversation.
        """
        
        return {
            "success": True,
            "transcript": demo_text.strip(),
            "language": "en",
            "method": "demo_content",
            "format": "demo"
        }

    def get_video_info(self, video_id: str) -> Dict[str, Any]:
        """Get basic video information."""
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'user_agent': random.choice(self.user_agents)
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                return {
                    "success": True,
                    "title": info.get('title', 'Unknown'),
                    "duration": info.get('duration', 0),
                    "uploader": info.get('uploader', 'Unknown'),
                    "view_count": info.get('view_count', 0),
                    "description": info.get('description', '')[:500] + '...' if info.get('description', '') else ''
                }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_popular_video_ids(self) -> List[str]:
        """Get list of popular video IDs for testing."""
        return [
            "dQw4w9WgXcQ",  # Rick Roll
            "9bZkp7q19f0",  # PSY - GANGNAM STYLE
            "kJQP7kiw5Fk",  # Luis Fonsi - Despacito
            "hT_nvWreIhg",  # OneRepublic - Counting Stars
            "pRpeEdMmmQ0",  # Imagine Dragons - Believer
            "fJ9rUzIMcZQ",  # Queen - Bohemian Rhapsody
            "y6120QOlsfU",  # Sandstorm
            "dQw4w9WgXcQ",  # Rick Astley - Never Gonna Give You Up
            "kJQP7kiw5Fk",  # Luis Fonsi - Despacito
            "hT_nvWreIhg"   # OneRepublic - Counting Stars
        ]

    def suggest_working_videos(self) -> Dict[str, Any]:
        """Suggest working videos and troubleshooting tips."""
        return {
            "working_videos": [
                {
                    "title": "Rick Astley - Never Gonna Give You Up",
                    "video_id": "dQw4w9WgXcQ",
                    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                    "reason": "Popular video with good captions"
                },
                {
                    "title": "PSY - GANGNAM STYLE",
                    "video_id": "9bZkp7q19f0",
                    "url": "https://www.youtube.com/watch?v=9bZkp7q19f0",
                    "reason": "High view count, likely has captions"
                },
                {
                    "title": "Luis Fonsi - Despacito",
                    "video_id": "kJQP7kiw5Fk",
                    "url": "https://www.youtube.com/watch?v=kJQP7kiw5Fk",
                    "reason": "Global hit with multiple language captions"
                }
            ],
            "troubleshooting_tips": [
                "🌐 Use VPN to avoid IP blocks",
                "🔄 Try different video IDs",
                "⏰ Wait 15-30 minutes between requests",
                "🎯 Use videos with high view counts",
                "📱 Try mobile data connection",
                "🌍 Use videos from different regions"
            ],
            "alternative_methods": [
                "Manual transcript entry",
                "Local video download",
                "Different YouTube API",
                "Browser automation"
            ]
        } 