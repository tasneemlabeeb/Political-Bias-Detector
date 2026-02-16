"""
Video/Podcast Analysis - Transcribe and analyze bias in audio/video content.

This module provides functionality to:
- Transcribe audio from video files or podcasts
- Extract text from YouTube videos
- Analyze political bias in transcribed content
- Support multiple transcription services (Whisper, AssemblyAI, etc.)
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
import re

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    YOUTUBE_TRANSCRIPT_AVAILABLE = True
except ImportError:
    YOUTUBE_TRANSCRIPT_AVAILABLE = False

try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False


@dataclass
class MediaSegment:
    """Represents a segment of transcribed media."""
    start_time: float  # seconds
    end_time: float
    text: str
    
    # Bias analysis
    political_bias: Optional[str] = None
    ml_confidence: Optional[float] = None


@dataclass
class TranscribedMedia:
    """Represents a fully transcribed media file."""
    source_url: Optional[str]
    source_type: str  # 'youtube', 'podcast', 'video', 'audio'
    title: str
    duration: float  # seconds
    transcript: str
    segments: List[MediaSegment]
    timestamp: datetime
    
    # Metadata
    author: Optional[str] = None
    channel: Optional[str] = None
    publish_date: Optional[datetime] = None
    
    # Overall bias analysis
    political_bias: Optional[str] = None
    ml_confidence: Optional[float] = None
    ml_explanation: Optional[str] = None
    
    # Segment-level analysis
    bias_timeline: Optional[List[Dict[str, Any]]] = None


class YouTubeTranscriber:
    """Transcribe YouTube videos."""
    
    def __init__(self):
        """Initialize YouTube transcriber."""
        if not YOUTUBE_TRANSCRIPT_AVAILABLE:
            raise ImportError("youtube-transcript-api not installed. Run: pip install youtube-transcript-api")
    
    @staticmethod
    def extract_video_id(url: str) -> str:
        """Extract video ID from YouTube URL."""
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/v\/([a-zA-Z0-9_-]{11})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        # If no pattern matches, assume the input is the video ID
        if len(url) == 11:
            return url
        
        raise ValueError(f"Could not extract video ID from URL: {url}")
    
    def transcribe(self, video_url: str, language: str = 'en') -> TranscribedMedia:
        """
        Transcribe a YouTube video.
        
        Args:
            video_url: YouTube video URL or ID
            language: Preferred language code (e.g., 'en', 'es')
        """
        video_id = self.extract_video_id(video_url)
        
        try:
            # Get transcript
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=[language])
        except Exception as e:
            # Try to get any available transcript
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
        
        # Get video metadata if yt-dlp is available
        title = f"YouTube Video {video_id}"
        author = None
        channel = None
        publish_date = None
        duration = 0
        
        if YT_DLP_AVAILABLE:
            try:
                ydl_opts = {'quiet': True, 'no_warnings': True}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                    title = info.get('title', title)
                    author = info.get('uploader', None)
                    channel = info.get('channel', None)
                    duration = info.get('duration', 0)
                    upload_date = info.get('upload_date')
                    if upload_date:
                        publish_date = datetime.strptime(upload_date, '%Y%m%d')
            except:
                pass
        
        # Build segments
        segments = []
        full_text = []
        
        for entry in transcript_list:
            segment = MediaSegment(
                start_time=entry['start'],
                end_time=entry['start'] + entry['duration'],
                text=entry['text']
            )
            segments.append(segment)
            full_text.append(entry['text'])
        
        if not duration and segments:
            duration = segments[-1].end_time
        
        return TranscribedMedia(
            source_url=f"https://www.youtube.com/watch?v={video_id}",
            source_type='youtube',
            title=title,
            duration=duration,
            transcript=' '.join(full_text),
            segments=segments,
            timestamp=datetime.now(),
            author=author,
            channel=channel,
            publish_date=publish_date
        )


class WhisperTranscriber:
    """Transcribe audio/video using OpenAI Whisper API."""
    
    def __init__(self, api_key: str = None):
        """Initialize Whisper transcriber."""
        if not OPENAI_AVAILABLE:
            raise ImportError("openai not installed. Run: pip install openai")
        
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not provided")
        
        self.client = openai.OpenAI(api_key=self.api_key)
    
    def transcribe_file(
        self, 
        file_path: str,
        language: str = None,
        response_format: str = 'verbose_json'
    ) -> TranscribedMedia:
        """
        Transcribe an audio or video file.
        
        Args:
            file_path: Path to audio/video file
            language: ISO-639-1 language code (e.g., 'en', 'es')
            response_format: 'json', 'text', 'srt', 'verbose_json', 'vtt'
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Transcribe using Whisper API
        with open(file_path, 'rb') as audio_file:
            transcript_response = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,
                response_format=response_format
            )
        
        # Parse response based on format
        if response_format == 'verbose_json':
            segments = []
            for seg in transcript_response.segments:
                segments.append(MediaSegment(
                    start_time=seg['start'],
                    end_time=seg['end'],
                    text=seg['text']
                ))
            
            transcript_text = transcript_response.text
            duration = transcript_response.duration
        else:
            # For other formats, we only get text
            transcript_text = str(transcript_response)
            segments = [MediaSegment(start_time=0, end_time=0, text=transcript_text)]
            duration = 0
        
        return TranscribedMedia(
            source_url=None,
            source_type='audio' if file_path.suffix in ['.mp3', '.wav', '.m4a'] else 'video',
            title=file_path.stem,
            duration=duration,
            transcript=transcript_text,
            segments=segments,
            timestamp=datetime.now()
        )
    
    def transcribe_youtube(self, video_url: str) -> TranscribedMedia:
        """Download and transcribe a YouTube video."""
        if not YT_DLP_AVAILABLE:
            raise ImportError("yt-dlp not installed. Run: pip install yt-dlp")
        
        # Download audio
        with tempfile.TemporaryDirectory() as temp_dir:
            output_template = os.path.join(temp_dir, '%(id)s.%(ext)s')
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_template,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=True)
                video_id = info['id']
                title = info.get('title', 'Unknown')
                author = info.get('uploader', None)
                channel = info.get('channel', None)
                upload_date = info.get('upload_date')
                
                audio_file = os.path.join(temp_dir, f"{video_id}.mp3")
                
                # Transcribe
                media = self.transcribe_file(audio_file)
                
                # Update metadata
                media.source_url = video_url
                media.source_type = 'youtube'
                media.title = title
                media.author = author
                media.channel = channel
                
                if upload_date:
                    media.publish_date = datetime.strptime(upload_date, '%Y%m%d')
                
                return media


class MediaBiasAnalyzer:
    """Analyze political bias in transcribed media."""
    
    def __init__(self, bias_classifier):
        """
        Initialize with a bias classifier.
        
        Args:
            bias_classifier: Instance of BiasClassifier from bias_classifier.py
        """
        self.classifier = bias_classifier
        self.youtube_transcriber = None
        self.whisper_transcriber = None
    
    def setup_youtube(self):
        """Setup YouTube transcriber."""
        self.youtube_transcriber = YouTubeTranscriber()
    
    def setup_whisper(self, api_key: str = None):
        """Setup Whisper transcriber."""
        self.whisper_transcriber = WhisperTranscriber(api_key)
    
    def analyze_media(
        self, 
        media: TranscribedMedia,
        analyze_segments: bool = False
    ) -> TranscribedMedia:
        """
        Analyze political bias in transcribed media.
        
        Args:
            media: TranscribedMedia object
            analyze_segments: Whether to analyze individual segments
        """
        # Analyze full transcript
        if media.transcript:
            result = self.classifier.classify_text(media.transcript)
            media.political_bias = result.get('bias_label')
            media.ml_confidence = result.get('confidence')
            media.ml_explanation = result.get('explanation')
        
        # Analyze segments if requested
        if analyze_segments and media.segments:
            bias_timeline = []
            
            for segment in media.segments:
                if len(segment.text.strip()) < 20:  # Skip very short segments
                    continue
                
                result = self.classifier.classify_text(segment.text)
                segment.political_bias = result.get('bias_label')
                segment.ml_confidence = result.get('confidence')
                
                bias_timeline.append({
                    'time': segment.start_time,
                    'bias': segment.political_bias,
                    'confidence': segment.ml_confidence
                })
            
            media.bias_timeline = bias_timeline
        
        return media
    
    def analyze_youtube_video(
        self, 
        video_url: str,
        analyze_segments: bool = False
    ) -> TranscribedMedia:
        """Transcribe and analyze a YouTube video."""
        if not self.youtube_transcriber:
            self.setup_youtube()
        
        media = self.youtube_transcriber.transcribe(video_url)
        return self.analyze_media(media, analyze_segments)
    
    def analyze_audio_file(
        self, 
        file_path: str,
        analyze_segments: bool = False
    ) -> TranscribedMedia:
        """Transcribe and analyze an audio/video file."""
        if not self.whisper_transcriber:
            raise ValueError("Whisper transcriber not set up. Call setup_whisper() first")
        
        media = self.whisper_transcriber.transcribe_file(file_path)
        return self.analyze_media(media, analyze_segments)
    
    def batch_analyze_channel(
        self, 
        channel_url: str,
        max_videos: int = 10
    ) -> List[TranscribedMedia]:
        """
        Analyze multiple videos from a YouTube channel.
        
        Args:
            channel_url: YouTube channel URL
            max_videos: Maximum number of videos to analyze
        """
        if not YT_DLP_AVAILABLE:
            raise ImportError("yt-dlp not installed")
        
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'playlistend': max_videos
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            playlist_info = ydl.extract_info(channel_url, download=False)
            
            if 'entries' not in playlist_info:
                return []
            
            results = []
            for entry in playlist_info['entries'][:max_videos]:
                video_url = f"https://www.youtube.com/watch?v={entry['id']}"
                try:
                    media = self.analyze_youtube_video(video_url)
                    results.append(media)
                except Exception as e:
                    print(f"Error analyzing {video_url}: {e}")
                    continue
            
            return results
    
    def get_bias_summary(self, media_list: List[TranscribedMedia]) -> Dict[str, Any]:
        """Generate summary statistics for multiple media items."""
        from collections import Counter
        
        biases = [m.political_bias for m in media_list if m.political_bias]
        bias_dist = dict(Counter(biases))
        
        avg_confidence = sum(m.ml_confidence or 0 for m in media_list) / len(media_list) if media_list else 0
        
        return {
            'total_items': len(media_list),
            'total_duration': sum(m.duration for m in media_list),
            'bias_distribution': bias_dist,
            'avg_confidence': avg_confidence,
            'items': media_list
        }
    
    def format_timestamp(self, seconds: float) -> str:
        """Convert seconds to HH:MM:SS format."""
        return str(timedelta(seconds=int(seconds)))
