"""
Social Media Analysis API Endpoints

Endpoints for analyzing bias in social media posts from Twitter and Reddit.
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field

router = APIRouter()


class SocialPostResponse(BaseModel):
    """Response model for a social media post."""
    platform: str
    post_id: str
    author: str
    content: str
    timestamp: datetime
    url: str
    score: int
    comments_count: int
    subreddit: Optional[str] = None
    hashtags: Optional[List[str]] = None
    political_bias: Optional[str] = None
    ml_confidence: Optional[float] = None
    ml_explanation: Optional[str] = None


class CommentResponse(BaseModel):
    """Response model for a comment."""
    comment_id: str
    post_id: str
    author: str
    content: str
    timestamp: datetime
    score: int
    political_bias: Optional[str] = None
    ml_confidence: Optional[float] = None


class BiasDistribution(BaseModel):
    """Bias distribution statistics."""
    left_leaning: int = 0
    left: int = 0
    center: int = 0
    right: int = 0
    right_leaning: int = 0


class RedditAnalysisRequest(BaseModel):
    """Request model for Reddit analysis."""
    subreddit: str = Field(..., min_length=1, max_length=50)
    limit: int = Field(50, ge=1, le=100)
    time_filter: str = Field('day', pattern='^(hour|day|week|month|year|all)$')
    analyze_comments: bool = False


class RedditAnalysisResponse(BaseModel):
    """Response model for Reddit analysis."""
    subreddit: str
    posts: List[SocialPostResponse]
    posts_count: int
    post_bias_distribution: BiasDistribution
    comments: List[CommentResponse]
    comments_count: int
    comment_bias_distribution: BiasDistribution
    avg_confidence: float


class TwitterAnalysisRequest(BaseModel):
    """Request model for Twitter analysis."""
    query: str = Field(..., min_length=1, max_length=500)
    max_results: int = Field(100, ge=10, le=100)


class TwitterAnalysisResponse(BaseModel):
    """Response model for Twitter analysis."""
    query: str
    posts: List[SocialPostResponse]
    posts_count: int
    bias_distribution: BiasDistribution
    hashtag_bias: dict
    avg_confidence: float


class PlatformComparisonRequest(BaseModel):
    """Request model for cross-platform comparison."""
    topic: str = Field(..., min_length=1, max_length=200)
    reddit_subreddit: str = Field('all', max_length=50)


@router.post("/reddit/analyze", response_model=RedditAnalysisResponse)
async def analyze_reddit_subreddit(request: RedditAnalysisRequest):
    """
    Analyze posts and comments from a Reddit subreddit for political bias.
    
    Requires REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET environment variables.
    """
    from src.backend.social_media_analyzer import SocialMediaBiasAnalyzer, RedditAnalyzer
    from src.backend.bias_classifier import BiasClassifier
    
    try:
        # Initialize classifier
        classifier = BiasClassifier()
        analyzer = SocialMediaBiasAnalyzer(classifier)
        
        # Connect to Reddit
        analyzer.connect_reddit()
        
        # Analyze subreddit
        result = analyzer.analyze_reddit_thread(
            subreddit=request.subreddit,
            limit=request.limit,
            analyze_comments=request.analyze_comments
        )
        
        # Convert to response model
        return RedditAnalysisResponse(
            subreddit=result['subreddit'],
            posts=[SocialPostResponse(**p.__dict__) for p in result['posts']],
            posts_count=result['posts_count'],
            post_bias_distribution=BiasDistribution(**result['post_bias_distribution']),
            comments=[CommentResponse(**c.__dict__) for c in result['comments']],
            comments_count=result['comments_count'],
            comment_bias_distribution=BiasDistribution(**result['comment_bias_distribution']),
            avg_confidence=result['avg_confidence']
        )
    
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Required library not installed: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing Reddit: {str(e)}"
        )


@router.post("/twitter/analyze", response_model=TwitterAnalysisResponse)
async def analyze_twitter_topic(request: TwitterAnalysisRequest):
    """
    Analyze tweets about a specific topic for political bias.
    
    Requires TWITTER_BEARER_TOKEN environment variable.
    """
    from src.backend.social_media_analyzer import SocialMediaBiasAnalyzer
    from src.backend.bias_classifier import BiasClassifier
    
    try:
        # Initialize classifier
        classifier = BiasClassifier()
        analyzer = SocialMediaBiasAnalyzer(classifier)
        
        # Connect to Twitter
        analyzer.connect_twitter()
        
        # Analyze topic
        result = analyzer.analyze_twitter_topic(
            query=request.query,
            max_results=request.max_results
        )
        
        # Convert to response model
        return TwitterAnalysisResponse(
            query=result['query'],
            posts=[SocialPostResponse(**p.__dict__) for p in result['posts']],
            posts_count=result['posts_count'],
            bias_distribution=BiasDistribution(**result['bias_distribution']),
            hashtag_bias=result['hashtag_bias'],
            avg_confidence=result['avg_confidence']
        )
    
    except ImportError as e:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail=f"Required library not installed: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing Twitter: {str(e)}"
        )


@router.post("/compare", response_model=dict)
async def compare_platforms(request: PlatformComparisonRequest):
    """
    Compare how a topic is discussed across Reddit and Twitter.
    
    Requires both Reddit and Twitter API credentials.
    """
    from src.backend.social_media_analyzer import SocialMediaBiasAnalyzer
    from src.backend.bias_classifier import BiasClassifier
    
    try:
        # Initialize classifier
        classifier = BiasClassifier()
        analyzer = SocialMediaBiasAnalyzer(classifier)
        
        # Connect to both platforms
        try:
            analyzer.connect_reddit()
        except:
            pass
        
        try:
            analyzer.connect_twitter()
        except:
            pass
        
        # Compare platforms
        result = analyzer.compare_platforms(
            topic=request.topic,
            reddit_subreddit=request.reddit_subreddit
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error comparing platforms: {str(e)}"
        )


@router.get("/reddit/search")
async def search_reddit(
    query: str = Query(..., min_length=1, max_length=200),
    subreddit: str = Query('all', max_length=50),
    limit: int = Query(50, ge=1, le=100)
):
    """Search Reddit posts by keyword and analyze bias."""
    from src.backend.social_media_analyzer import SocialMediaBiasAnalyzer, RedditAnalyzer
    from src.backend.bias_classifier import BiasClassifier
    
    try:
        classifier = BiasClassifier()
        analyzer = SocialMediaBiasAnalyzer(classifier)
        analyzer.connect_reddit()
        
        posts = analyzer.reddit.search_posts(query, subreddit, limit)
        analyzed_posts = [analyzer.analyze_post(post) for post in posts]
        
        return {
            'query': query,
            'subreddit': subreddit,
            'posts': [SocialPostResponse(**p.__dict__) for p in analyzed_posts],
            'count': len(analyzed_posts)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching Reddit: {str(e)}"
        )
