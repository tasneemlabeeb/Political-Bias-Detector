# New Features Documentation

## Overview

Three major features have been added to the Political Bias Detector:

1. **Social Media Integration** - Analyze bias in Twitter/Reddit posts
2. **Video/Audio Analysis** - Transcribe and analyze podcasts/videos
3. **Citation Network** - Map source relationships and detect echo chambers

---

## 1. Social Media Integration

### Backend Module
**Location:** `src/backend/social_media_analyzer.py`

### Features
- Analyze Reddit subreddits and posts
- Analyze Twitter tweets and hashtags
- Track bias distribution across comments
- Compare platforms side-by-side
- Extract trending topics with bias patterns

### API Endpoints
**Location:** `backend/api/v1/endpoints/social_media.py`

#### Analyze Reddit Subreddit
```
POST /api/v1/social-media/reddit/analyze
Body: {
  "subreddit": "politics",
  "limit": 50,
  "time_filter": "day",
  "analyze_comments": true
}
```

#### Analyze Twitter Topic
```
POST /api/v1/social-media/twitter/analyze
Body: {
  "query": "#election2024",
  "max_results": 100
}
```

#### Search Reddit
```
GET /api/v1/social-media/reddit/search?query=climate&subreddit=all&limit=50
```

#### Compare Platforms
```
POST /api/v1/social-media/compare
Body: {
  "topic": "climate change",
  "reddit_subreddit": "all"
}
```

### Frontend Page
**Location:** `frontend-nextjs/app/social-media/page.tsx`

**Features:**
- Switch between Reddit and Twitter analysis
- Live search and analysis
- Bias distribution charts
- Post-level confidence scores
- Hashtag bias mapping (Twitter)

### Setup Requirements

Install dependencies:
```bash
pip install praw tweepy
```

Set environment variables:
```bash
# Reddit
export REDDIT_CLIENT_ID="your_client_id"
export REDDIT_CLIENT_SECRET="your_client_secret"
export REDDIT_USER_AGENT="BiasDetector/1.0"

# Twitter
export TWITTER_BEARER_TOKEN="your_bearer_token"
```

### Usage Example

```python
from src.backend.social_media_analyzer import SocialMediaBiasAnalyzer
from src.backend.bias_classifier import BiasClassifier

classifier = BiasClassifier()
analyzer = SocialMediaBiasAnalyzer(classifier)

# Connect to Reddit
analyzer.connect_reddit()

# Analyze subreddit
result = analyzer.analyze_reddit_thread(
    subreddit='politics',
    limit=100,
    analyze_comments=True
)

print(f"Analyzed {result['posts_count']} posts")
print(f"Bias distribution: {result['post_bias_distribution']}")
```

---

## 2. Video/Audio Analysis

### Backend Module
**Location:** `src/backend/media_transcriber.py`

### Features
- Transcribe YouTube videos (using built-in captions)
- Transcribe audio/video files (using OpenAI Whisper)
- Analyze full transcript for overall bias
- Segment-level bias analysis with timeline
- Batch analyze entire YouTube channels

### API Endpoints
**Location:** `backend/api/v1/endpoints/media.py`

#### Analyze YouTube Video
```
POST /api/v1/media/youtube/analyze
Body: {
  "video_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "analyze_segments": true
}
```

#### Analyze YouTube Channel
```
POST /api/v1/media/youtube/channel
Body: {
  "channel_url": "https://www.youtube.com/@channelname",
  "max_videos": 10
}
```

#### Upload Audio/Video File
```
POST /api/v1/media/upload
Form Data:
  file: [audio/video file]
  analyze_segments: true
```

#### Get Supported Formats
```
GET /api/v1/media/formats
```

### Frontend Page
**Location:** `frontend-nextjs/app/media/page.tsx`

**Features:**
- YouTube URL input
- File upload (drag & drop)
- Full transcript display
- Bias timeline visualization
- Segment-by-segment analysis
- Video metadata display

### Setup Requirements

Install dependencies:
```bash
pip install openai youtube-transcript-api yt-dlp
```

Set environment variable:
```bash
export OPENAI_API_KEY="your_openai_api_key"
```

### Usage Example

```python
from src.backend.media_transcriber import MediaBiasAnalyzer
from src.backend.bias_classifier import BiasClassifier

classifier = BiasClassifier()
analyzer = MediaBiasAnalyzer(classifier)

# Setup YouTube transcriber
analyzer.setup_youtube()

# Analyze a YouTube video
media = analyzer.analyze_youtube_video(
    video_url="https://www.youtube.com/watch?v=VIDEO_ID",
    analyze_segments=True
)

print(f"Title: {media.title}")
print(f"Duration: {media.duration}s")
print(f"Overall bias: {media.political_bias}")
print(f"Confidence: {media.ml_confidence}")

# View bias timeline
for point in media.bias_timeline:
    print(f"{point['time']}s - {point['bias']} ({point['confidence']:.2%})")
```

**For audio files with Whisper:**
```python
analyzer.setup_whisper()  # Requires OPENAI_API_KEY

media = analyzer.analyze_audio_file(
    file_path="podcast.mp3",
    analyze_segments=True
)
```

---

## 3. Citation Network

### Backend Module
**Location:** `src/backend/citation_network.py`

### Features
- Extract citations from articles (hyperlinks, mentions)
- Build directed citation graphs
- Calculate authority scores (PageRank)
- Detect echo chambers using community detection
- Analyze cross-bias citation patterns
- Identify most influential sources

### API Endpoints
**Location:** `backend/api/v1/endpoints/citations.py`

#### Build Network from Articles
```
POST /api/v1/citations/build
Body: {
  "article_ids": ["id1", "id2", ...],
  "extract_from_html": true,
  "extract_from_text": true
}
```

#### Add Citation Manually
```
POST /api/v1/citations/add
Body: {
  "from_source": "CNN",
  "to_source": "New York Times",
  "from_article_id": "article123",
  "to_url": "https://nytimes.com/article",
  "citation_type": "hyperlink",
  "from_bias": "left",
  "to_bias": "left_leaning"
}
```

#### Get Network Summary
```
GET /api/v1/citations/summary
```

#### Get All Sources
```
GET /api/v1/citations/sources?min_citations=5&bias=left&sort_by=authority
```

#### Detect Echo Chambers
```
GET /api/v1/citations/echo-chambers?min_size=3
```

#### Get Cross-Bias Citations
```
GET /api/v1/citations/cross-bias
```

#### Get Visualization Data
```
GET /api/v1/citations/visualization
```

#### Create Demo Network
```
POST /api/v1/citations/demo
```

### Frontend Page
**Location:** `frontend-nextjs/app/citations/page.tsx`

**Features:**
- Network summary statistics
- Most cited/citing sources
- Echo chamber detection
- Cross-bias citation matrix
- Insularity scores
- Authority rankings
- Source-level metrics

### Setup Requirements

Install dependencies:
```bash
pip install networkx python-louvain beautifulsoup4
```

### Usage Example

```python
from src.backend.citation_network import CitationNetwork, Citation

# Create network
network = CitationNetwork()

# Add sources
network.add_source("CNN", "cnn.com", "left")
network.add_source("Fox News", "foxnews.com", "right")
network.add_source("Reuters", "reuters.com", "center")

# Add citation
citation = Citation(
    from_source="CNN",
    to_source="Reuters",
    from_article_id="cnn_123",
    to_url="https://reuters.com/article",
    context="According to Reuters...",
    citation_type="mention",
    from_bias="left",
    to_bias="center"
)
network.add_citation(citation)

# Calculate metrics
network.calculate_authority_scores()
network.calculate_echo_chamber_scores()

# Detect echo chambers
chambers = network.detect_echo_chambers(min_size=3)

for chamber in chambers:
    print(f"Chamber {chamber.chamber_id}:")
    print(f"  Bias: {chamber.dominant_bias}")
    print(f"  Sources: {chamber.sources}")
    print(f"  Insularity: {chamber.insularity_score:.1%}")

# Get summary
summary = network.get_network_summary()
print(f"Total sources: {summary['total_sources']}")
print(f"Total citations: {summary['total_citations']}")
print(f"Network density: {summary['network_density']:.3f}")
```

---

## Installation

### Backend
```bash
cd "Political Bias Detector"
pip install -r requirements-features.txt
```

### Frontend
The Next.js frontend already has all necessary dependencies. Navigation is automatically added.

---

## Environment Variables

Create a `.env` file:

```bash
# Social Media APIs
REDDIT_CLIENT_ID=your_reddit_client_id
REDDIT_CLIENT_SECRET=your_reddit_secret
REDDIT_USER_AGENT=BiasDetector/1.0
TWITTER_BEARER_TOKEN=your_twitter_token

# Transcription
OPENAI_API_KEY=your_openai_key
```

---

## Frontend Navigation

All features are accessible via the top navigation bar:

1. **News Reader** - Original article reader (home page)
2. **Social Media** - Twitter/Reddit analysis
3. **Video & Audio** - Media transcription and analysis
4. **Citation Network** - Source relationship visualization

---

## API Integration

### Connecting Frontend to Backend

Update Next.js API routes to proxy to FastAPI backend:

```typescript
// frontend-nextjs/app/api/social-media/reddit/route.ts
export async function POST(request: Request) {
  const body = await request.json()
  
  const response = await fetch('http://localhost:8000/api/v1/social-media/reddit/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body)
  })
  
  return response
}
```

---

## Demo Mode

Each feature includes mock/demo data for testing without API credentials:

### Social Media
Returns empty results until connected to real APIs

### Media Analysis
Returns mock transcription data

### Citation Network
Use "Create Demo Network" button to generate sample network with 8 sources and 13 citations

---

## Future Enhancements

### Social Media
- Sentiment analysis on comments
- Thread-level conversation tracking
- Real-time streaming

### Media
- Support for more video platforms (Rumble, Vimeo)
- Speaker diarization
- Visual content analysis

### Citation Network
- Interactive graph visualization (D3.js, Cytoscape)
- Circular reporting detection
- Source reliability scoring
- Export as graph image

---

## Troubleshooting

### "Required library not installed"
Run: `pip install -r requirements-features.txt`

### "API key not configured"
Set environment variables in `.env` file

### "No results returned"
Check API credentials and rate limits

### Frontend shows empty data
- For development: demo data is automatically available
- For production: connect Next.js API routes to FastAPI backend (port 8000)

---

## Architecture

```
┌─────────────────────────────────────────┐
│         Next.js Frontend (Port 3000)    │
│  ┌──────────┬──────────┬──────────────┐ │
│  │  Social  │  Media   │  Citations   │ │
│  │  Media   │ Analysis │  Network     │ │
│  └─────┬────┴─────┬────┴──────┬───────┘ │
└────────┼──────────┼───────────┼─────────┘
         │          │           │
         ▼          ▼           ▼
┌─────────────────────────────────────────┐
│      FastAPI Backend (Port 8000)        │
│  ┌──────────┬──────────┬──────────────┐ │
│  │  Social  │  Media   │  Citation    │ │
│  │  Media   │  Trans-  │  Network     │ │
│  │  Analyzer│  criber  │  Builder     │ │
│  └─────┬────┴─────┬────┴──────┬───────┘ │
└────────┼──────────┼───────────┼─────────┘
         │          │           │
         ▼          ▼           ▼
┌─────────────────────────────────────────┐
│          External APIs                  │
│  Reddit・Twitter・Whisper・YouTube       │
└─────────────────────────────────────────┘
```

---

## Files Created

### Backend
- `src/backend/social_media_analyzer.py` - Social media integration
- `src/backend/media_transcriber.py` - Video/audio transcription
- `src/backend/citation_network.py` - Citation network analysis
- `backend/api/v1/endpoints/social_media.py` - Social media API
- `backend/api/v1/endpoints/media.py` - Media analysis API
- `backend/api/v1/endpoints/citations.py` - Citation network API

### Frontend
- `frontend-nextjs/app/social-media/page.tsx` - Social media UI
- `frontend-nextjs/app/media/page.tsx` - Media analysis UI
- `frontend-nextjs/app/citations/page.tsx` - Citation network UI
- `frontend-nextjs/components/Navigation.tsx` - Top navigation
- `frontend-nextjs/app/api/social-media/*` - API route proxies
- `frontend-nextjs/app/api/media/*` - API route proxies
- `frontend-nextjs/app/api/citations/*` - API route proxies

### Documentation
- `requirements-features.txt` - New dependencies
- `FEATURES_DOCUMENTATION.md` - This file
