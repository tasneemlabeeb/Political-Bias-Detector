"""
Media Transcription and Analysis API Endpoints

Endpoints for transcribing and analyzing bias in video/audio content.
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, UploadFile, File, HTTPException, status, Query
from pydantic import BaseModel, Field, HttpUrl

router = APIRouter()


class MediaSegmentResponse(BaseModel):
    """Response model for a media segment."""
    start_time: float
    end_time: float
    text: str
    political_bias: Optional[str] = None
    ml_confidence: Optional[float] = None


class BiasTimelinePoint(BaseModel):
    """Point in bias timeline."""
    time: float
    bias: str
    confidence: float


class TranscribedMediaResponse(BaseModel):
    """Response model for transcribed media."""
    source_url: Optional[str]
    source_type: str
    title: str
    duration: float
    transcript: str
    timestamp: datetime
    author: Optional[str] = None
    channel: Optional[str] = None
    publish_date: Optional[datetime] = None
    political_bias: Optional[str] = None
    ml_confidence: Optional[float] = None
    ml_explanation: Optional[str] = None
    bias_timeline: Optional[List[BiasTimelinePoint]] = None
    segments: Optional[List[MediaSegmentResponse]] = None


class YouTubeAnalysisRequest(BaseModel):
    """Request model for YouTube video analysis."""
    video_url: HttpUrl = Field(..., description="YouTube video URL")
    analyze_segments: bool = Field(False, description="Analyze individual segments for bias")


class ChannelAnalysisRequest(BaseModel):
    """Request model for YouTube channel analysis."""
    channel_url: HttpUrl = Field(..., description="YouTube channel URL")
    max_videos: int = Field(10, ge=1, le=50)


class MediaBatchResponse(BaseModel):
    """Response for batch media analysis."""
    total_items: int
    total_duration: float
    bias_distribution: dict
    avg_confidence: float
    items: List[TranscribedMediaResponse]


@router.post("/youtube/analyze", response_model=TranscribedMediaResponse)
async def analyze_youtube_video(request: YouTubeAnalysisRequest):
    """
    Transcribe and analyze political bias in a YouTube video.
    
    Uses YouTube's built-in transcripts when available.
    """
    from src.backend.media_transcriber import MediaBiasAnalyzer
    from src.backend.bias_classifier import BiasClassifier
    
    try:
        # Initialize analyzer
        classifier = BiasClassifier()
        analyzer = MediaBiasAnalyzer(classifier)
        analyzer.setup_youtube()
        
        # Analyze video
        media = analyzer.analyze_youtube_video(
            video_url=str(request.video_url),
            analyze_segments=request.analyze_segments
        )
        
        # Convert segments
        segments = None
        if media.segments and request.analyze_segments:
            segments = [MediaSegmentResponse(**s.__dict__) for s in media.segments]
        
        # Convert timeline
        bias_timeline = None
        if media.bias_timeline:
            bias_timeline = [BiasTimelinePoint(**p) for p in media.bias_timeline]
        
        return TranscribedMediaResponse(
            source_url=media.source_url,
            source_type=media.source_type,
            title=media.title,
            duration=media.duration,
            transcript=media.transcript,
            timestamp=media.timestamp,
            author=media.author,
            channel=media.channel,
            publish_date=media.publish_date,
            political_bias=media.political_bias,
            ml_confidence=media.ml_confidence,
            ml_explanation=media.ml_explanation,
            bias_timeline=bias_timeline,
            segments=segments
        )
    
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Required library not installed: {str(e)}. Install with: pip install youtube-transcript-api yt-dlp"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing video: {str(e)}"
        )


@router.post("/youtube/channel", response_model=MediaBatchResponse)
async def analyze_youtube_channel(request: ChannelAnalysisRequest):
    """
    Analyze multiple videos from a YouTube channel.
    
    Provides aggregate bias statistics across channel content.
    """
    from src.backend.media_transcriber import MediaBiasAnalyzer
    from src.backend.bias_classifier import BiasClassifier
    
    try:
        # Initialize analyzer
        classifier = BiasClassifier()
        analyzer = MediaBiasAnalyzer(classifier)
        analyzer.setup_youtube()
        
        # Analyze channel
        media_list = analyzer.batch_analyze_channel(
            channel_url=str(request.channel_url),
            max_videos=request.max_videos
        )
        
        # Get summary
        summary = analyzer.get_bias_summary(media_list)
        
        # Convert items
        items = [
            TranscribedMediaResponse(
                source_url=m.source_url,
                source_type=m.source_type,
                title=m.title,
                duration=m.duration,
                transcript=m.transcript[:500] + '...' if len(m.transcript) > 500 else m.transcript,  # Truncate for batch
                timestamp=m.timestamp,
                author=m.author,
                channel=m.channel,
                publish_date=m.publish_date,
                political_bias=m.political_bias,
                ml_confidence=m.ml_confidence,
                ml_explanation=m.ml_explanation
            )
            for m in media_list
        ]
        
        return MediaBatchResponse(
            total_items=summary['total_items'],
            total_duration=summary['total_duration'],
            bias_distribution=summary['bias_distribution'],
            avg_confidence=summary['avg_confidence'],
            items=items
        )
    
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Required library not installed: {str(e)}. Install with: pip install yt-dlp"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing channel: {str(e)}"
        )


@router.post("/upload", response_model=TranscribedMediaResponse)
async def upload_and_analyze_media(
    file: UploadFile = File(...),
    analyze_segments: bool = Query(False)
):
    """
    Upload an audio/video file for transcription and bias analysis.
    
    Requires OpenAI API key (OPENAI_API_KEY) for Whisper transcription.
    Supports: mp3, mp4, wav, m4a, webm, and other common formats.
    """
    from src.backend.media_transcriber import MediaBiasAnalyzer
    from src.backend.bias_classifier import BiasClassifier
    import tempfile
    import os
    
    # Check file size (max 25MB for Whisper API)
    MAX_SIZE = 25 * 1024 * 1024  # 25MB
    file_content = await file.read()
    
    if len(file_content) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File too large. Maximum size is 25MB."
        )
    
    try:
        # Initialize analyzer
        classifier = BiasClassifier()
        analyzer = MediaBiasAnalyzer(classifier)
        
        # Check if Whisper is configured
        try:
            analyzer.setup_whisper()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="OpenAI API key not configured. Set OPENAI_API_KEY environment variable."
            )
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
            temp_file.write(file_content)
            temp_path = temp_file.name
        
        try:
            # Analyze file
            media = analyzer.analyze_audio_file(
                file_path=temp_path,
                analyze_segments=analyze_segments
            )
            
            # Update title with original filename
            media.title = file.filename
            
            # Convert segments
            segments = None
            if media.segments and analyze_segments:
                segments = [MediaSegmentResponse(**s.__dict__) for s in media.segments]
            
            # Convert timeline
            bias_timeline = None
            if media.bias_timeline:
                bias_timeline = [BiasTimelinePoint(**p) for p in media.bias_timeline]
            
            return TranscribedMediaResponse(
                source_url=None,
                source_type=media.source_type,
                title=media.title,
                duration=media.duration,
                transcript=media.transcript,
                timestamp=media.timestamp,
                political_bias=media.political_bias,
                ml_confidence=media.ml_confidence,
                ml_explanation=media.ml_explanation,
                bias_timeline=bias_timeline,
                segments=segments
            )
        
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Required library not installed: {str(e)}. Install with: pip install openai"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing media: {str(e)}"
        )


@router.get("/formats")
async def get_supported_formats():
    """Get list of supported audio/video formats."""
    return {
        "audio_formats": [
            "mp3", "mp4", "mpeg", "mpga", "m4a", "wav", "webm"
        ],
        "video_formats": [
            "mp4", "webm", "mov", "avi"
        ],
        "max_file_size_mb": 25,
        "transcription_service": "OpenAI Whisper",
        "youtube_support": True
    }
