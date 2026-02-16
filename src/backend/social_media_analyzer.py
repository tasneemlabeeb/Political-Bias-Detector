"""
Social Media Integration - Analyze Twitter/Reddit posts for political bias.

This module provides functionality to:
- Fetch posts from Twitter (via API) and Reddit (via PRAW)
- Analyze bias in comments and threads
- Track bias distribution across social platforms
- Identify trending topics and their bias patterns
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any

try:
    import praw
    REDDIT_AVAILABLE = True
except ImportError:
    REDDIT_AVAILABLE = False

try:
    import tweepy
    TWITTER_AVAILABLE = True
except ImportError:
    TWITTER_AVAILABLE = False


@dataclass
class SocialPost:
    """Represents a social media post."""
    platform: str  # 'twitter' or 'reddit'
    post_id: str
    author: str
    content: str
    timestamp: datetime
    url: str
    score: int  # upvotes/likes
    comments_count: int
    subreddit: Optional[str] = None  # For Reddit
    hashtags: List[str] = None  # For Twitter
    
    # Bias analysis results
    political_bias: Optional[str] = None
    ml_confidence: Optional[float] = None
    ml_explanation: Optional[str] = None


@dataclass
class Comment:
    """Represents a comment on a social post."""
    comment_id: str
    post_id: str
    author: str
    content: str
    timestamp: datetime
    score: int
    
    # Bias analysis
    political_bias: Optional[str] = None
    ml_confidence: Optional[float] = None


class RedditAnalyzer:
    """Analyze Reddit posts and comments for political bias."""
    
    def __init__(self, client_id: str = None, client_secret: str = None, user_agent: str = None):
        """Initialize Reddit API client."""
        if not REDDIT_AVAILABLE:
            raise ImportError("praw is not installed. Run: pip install praw")
        
        self.client_id = client_id or os.getenv('REDDIT_CLIENT_ID')
        self.client_secret = client_secret or os.getenv('REDDIT_CLIENT_SECRET')
        self.user_agent = user_agent or os.getenv('REDDIT_USER_AGENT', 'BiasDetector/1.0')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Reddit credentials not provided")
        
        self.reddit = praw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.user_agent
        )
    
    def fetch_subreddit_posts(
        self, 
        subreddit: str, 
        limit: int = 100,
        time_filter: str = 'day'
    ) -> List[SocialPost]:
        """
        Fetch top posts from a subreddit.
        
        Args:
            subreddit: Subreddit name (e.g., 'politics', 'news')
            limit: Number of posts to fetch
            time_filter: 'hour', 'day', 'week', 'month', 'year', 'all'
        """
        posts = []
        subreddit_obj = self.reddit.subreddit(subreddit)
        
        for submission in subreddit_obj.top(time_filter=time_filter, limit=limit):
            post = SocialPost(
                platform='reddit',
                post_id=submission.id,
                author=str(submission.author),
                content=f"{submission.title}\n\n{submission.selftext}",
                timestamp=datetime.fromtimestamp(submission.created_utc),
                url=f"https://reddit.com{submission.permalink}",
                score=submission.score,
                comments_count=submission.num_comments,
                subreddit=subreddit
            )
            posts.append(post)
        
        return posts
    
    def fetch_comments(self, post_id: str, limit: int = 50) -> List[Comment]:
        """Fetch comments from a Reddit post."""
        comments = []
        submission = self.reddit.submission(id=post_id)
        submission.comments.replace_more(limit=0)
        
        for comment in submission.comments.list()[:limit]:
            if hasattr(comment, 'body'):
                comments.append(Comment(
                    comment_id=comment.id,
                    post_id=post_id,
                    author=str(comment.author),
                    content=comment.body,
                    timestamp=datetime.fromtimestamp(comment.created_utc),
                    score=comment.score
                ))
        
        return comments
    
    def search_posts(self, query: str, subreddit: str = 'all', limit: int = 50) -> List[SocialPost]:
        """Search Reddit posts by keyword."""
        posts = []
        subreddit_obj = self.reddit.subreddit(subreddit)
        
        for submission in subreddit_obj.search(query, limit=limit):
            post = SocialPost(
                platform='reddit',
                post_id=submission.id,
                author=str(submission.author),
                content=f"{submission.title}\n\n{submission.selftext}",
                timestamp=datetime.fromtimestamp(submission.created_utc),
                url=f"https://reddit.com{submission.permalink}",
                score=submission.score,
                comments_count=submission.num_comments,
                subreddit=submission.subreddit.display_name
            )
            posts.append(post)
        
        return posts


class TwitterAnalyzer:
    """Analyze Twitter posts for political bias."""
    
    def __init__(self, bearer_token: str = None):
        """Initialize Twitter API client (API v2)."""
        if not TWITTER_AVAILABLE:
            raise ImportError("tweepy is not installed. Run: pip install tweepy")
        
        self.bearer_token = bearer_token or os.getenv('TWITTER_BEARER_TOKEN')
        
        if not self.bearer_token:
            raise ValueError("Twitter bearer token not provided")
        
        self.client = tweepy.Client(bearer_token=self.bearer_token)
    
    def search_tweets(
        self, 
        query: str, 
        max_results: int = 100,
        start_time: datetime = None
    ) -> List[SocialPost]:
        """
        Search recent tweets by query.
        
        Args:
            query: Search query (supports Twitter query operators)
            max_results: Number of tweets (10-100)
            start_time: Filter tweets after this time
        """
        posts = []
        
        response = self.client.search_recent_tweets(
            query=query,
            max_results=min(max_results, 100),
            start_time=start_time,
            tweet_fields=['created_at', 'public_metrics', 'entities', 'author_id'],
            expansions=['author_id']
        )
        
        if not response.data:
            return posts
        
        # Create username lookup
        users = {user.id: user.username for user in response.includes.get('users', [])}
        
        for tweet in response.data:
            # Extract hashtags
            hashtags = []
            if tweet.entities and 'hashtags' in tweet.entities:
                hashtags = [tag['tag'] for tag in tweet.entities['hashtags']]
            
            post = SocialPost(
                platform='twitter',
                post_id=tweet.id,
                author=users.get(tweet.author_id, 'unknown'),
                content=tweet.text,
                timestamp=tweet.created_at,
                url=f"https://twitter.com/user/status/{tweet.id}",
                score=tweet.public_metrics.get('like_count', 0),
                comments_count=tweet.public_metrics.get('reply_count', 0),
                hashtags=hashtags
            )
            posts.append(post)
        
        return posts
    
    def get_user_tweets(self, username: str, max_results: int = 100) -> List[SocialPost]:
        """Fetch recent tweets from a specific user."""
        # Get user ID
        user = self.client.get_user(username=username)
        if not user.data:
            return []
        
        user_id = user.data.id
        
        response = self.client.get_users_tweets(
            id=user_id,
            max_results=min(max_results, 100),
            tweet_fields=['created_at', 'public_metrics', 'entities']
        )
        
        if not response.data:
            return []
        
        posts = []
        for tweet in response.data:
            hashtags = []
            if tweet.entities and 'hashtags' in tweet.entities:
                hashtags = [tag['tag'] for tag in tweet.entities['hashtags']]
            
            post = SocialPost(
                platform='twitter',
                post_id=tweet.id,
                author=username,
                content=tweet.text,
                timestamp=tweet.created_at,
                url=f"https://twitter.com/{username}/status/{tweet.id}",
                score=tweet.public_metrics.get('like_count', 0),
                comments_count=tweet.public_metrics.get('reply_count', 0),
                hashtags=hashtags
            )
            posts.append(post)
        
        return posts


class SocialMediaBiasAnalyzer:
    """Main class to analyze bias across social media platforms."""
    
    def __init__(self, bias_classifier):
        """
        Initialize with a bias classifier.
        
        Args:
            bias_classifier: Instance of BiasClassifier from bias_classifier.py
        """
        self.classifier = bias_classifier
        self.reddit = None
        self.twitter = None
    
    def connect_reddit(self, client_id: str = None, client_secret: str = None):
        """Connect to Reddit API."""
        self.reddit = RedditAnalyzer(client_id, client_secret)
    
    def connect_twitter(self, bearer_token: str = None):
        """Connect to Twitter API."""
        self.twitter = TwitterAnalyzer(bearer_token)
    
    def analyze_post(self, post: SocialPost) -> SocialPost:
        """Analyze political bias of a social media post."""
        if not post.content.strip():
            return post
        
        # Use the bias classifier
        result = self.classifier.classify_text(post.content)
        
        post.political_bias = result.get('bias_label')
        post.ml_confidence = result.get('confidence')
        post.ml_explanation = result.get('explanation')
        
        return post
    
    def analyze_comment(self, comment: Comment) -> Comment:
        """Analyze political bias of a comment."""
        if not comment.content.strip():
            return comment
        
        result = self.classifier.classify_text(comment.content)
        
        comment.political_bias = result.get('bias_label')
        comment.ml_confidence = result.get('confidence')
        
        return comment
    
    def analyze_reddit_thread(
        self, 
        subreddit: str, 
        limit: int = 50,
        analyze_comments: bool = True
    ) -> Dict[str, Any]:
        """
        Analyze a full Reddit thread for bias patterns.
        
        Returns:
            Dictionary with posts, comments, and aggregate statistics
        """
        if not self.reddit:
            raise ValueError("Reddit not connected. Call connect_reddit() first")
        
        # Fetch posts
        posts = self.reddit.fetch_subreddit_posts(subreddit, limit=limit)
        
        # Analyze posts
        analyzed_posts = [self.analyze_post(post) for post in posts]
        
        # Analyze comments if requested
        all_comments = []
        if analyze_comments:
            for post in analyzed_posts[:10]:  # Limit to first 10 posts
                comments = self.reddit.fetch_comments(post.post_id, limit=20)
                all_comments.extend([self.analyze_comment(c) for c in comments])
        
        # Calculate statistics
        post_bias_dist = self._calculate_bias_distribution([p.political_bias for p in analyzed_posts])
        comment_bias_dist = self._calculate_bias_distribution([c.political_bias for c in all_comments])
        
        return {
            'subreddit': subreddit,
            'posts': analyzed_posts,
            'posts_count': len(analyzed_posts),
            'post_bias_distribution': post_bias_dist,
            'comments': all_comments,
            'comments_count': len(all_comments),
            'comment_bias_distribution': comment_bias_dist,
            'avg_confidence': sum(p.ml_confidence or 0 for p in analyzed_posts) / len(analyzed_posts) if analyzed_posts else 0
        }
    
    def analyze_twitter_topic(
        self, 
        query: str, 
        max_results: int = 100
    ) -> Dict[str, Any]:
        """Analyze Twitter posts about a topic."""
        if not self.twitter:
            raise ValueError("Twitter not connected. Call connect_twitter() first")
        
        # Fetch tweets
        posts = self.twitter.search_tweets(query, max_results=max_results)
        
        # Analyze posts
        analyzed_posts = [self.analyze_post(post) for post in posts]
        
        # Extract hashtag patterns
        hashtag_bias = {}
        for post in analyzed_posts:
            if post.hashtags and post.political_bias:
                for tag in post.hashtags:
                    if tag not in hashtag_bias:
                        hashtag_bias[tag] = []
                    hashtag_bias[tag].append(post.political_bias)
        
        # Calculate statistics
        bias_dist = self._calculate_bias_distribution([p.political_bias for p in analyzed_posts])
        
        return {
            'query': query,
            'posts': analyzed_posts,
            'posts_count': len(analyzed_posts),
            'bias_distribution': bias_dist,
            'hashtag_bias': {
                tag: self._calculate_bias_distribution(biases) 
                for tag, biases in hashtag_bias.items()
            },
            'avg_confidence': sum(p.ml_confidence or 0 for p in analyzed_posts) / len(analyzed_posts) if analyzed_posts else 0
        }
    
    def _calculate_bias_distribution(self, biases: List[Optional[str]]) -> Dict[str, int]:
        """Calculate distribution of bias labels."""
        from collections import Counter
        valid_biases = [b for b in biases if b]
        return dict(Counter(valid_biases))
    
    def compare_platforms(
        self, 
        topic: str,
        reddit_subreddit: str = 'all'
    ) -> Dict[str, Any]:
        """Compare how a topic is discussed across Reddit and Twitter."""
        results = {}
        
        if self.twitter:
            results['twitter'] = self.analyze_twitter_topic(topic, max_results=100)
        
        if self.reddit:
            posts = self.reddit.search_posts(topic, subreddit=reddit_subreddit, limit=100)
            analyzed_posts = [self.analyze_post(post) for post in posts]
            results['reddit'] = {
                'query': topic,
                'posts': analyzed_posts,
                'posts_count': len(analyzed_posts),
                'bias_distribution': self._calculate_bias_distribution([p.political_bias for p in analyzed_posts])
            }
        
        return results
