# Quick Start Guide - New Features

## 🚀 What's New

Three powerful features have been added to your Political Bias Detector:

1. **Social Media Analysis** - Analyze Twitter & Reddit for political bias
2. **Video/Audio Analysis** - Transcribe and analyze YouTube videos & podcasts
3. **Citation Network** - Discover how news sources cite each other

---

## ⚡ Try It Now (No Setup Required)

### Option 1: Frontend Demo

The Next.js frontend is already running with demo data:

```bash
# If not already running:
cd frontend-nextjs
npm run dev
```

Visit: http://localhost:3000

**Try these features:**
- Click "Social Media" in the navigation
- Click "Video & Audio" in the navigation  
- Click "Citation Network" → "Create Demo Network"

### Option 2: Backend with Mock Data

The endpoints work without API keys (returns empty/mock data):

```bash
# Start FastAPI backend
cd backend
uvicorn main:app --reload --port 8000
```

Visit: http://localhost:8000/api/docs

---

## 🔑 Full Setup (With Real APIs)

### 1. Install Dependencies

```bash
pip install -r requirements-features.txt
```

This installs:
- `praw` - Reddit API
- `tweepy` - Twitter API  
- `openai` - Whisper transcription
- `youtube-transcript-api` - YouTube captions
- `yt-dlp` - YouTube downloader
- `networkx` - Graph analysis
- `python-louvain` - Community detection

### 2. Get API Keys

#### Reddit (Free)
1. Go to https://www.reddit.com/prefs/apps
2. Click "Create App" → "script"
3. Copy client ID and secret

#### Twitter (Free tier available)
1. Go to https://developer.twitter.com
2. Create app → Get Bearer Token

#### OpenAI (Paid - $0.006/minute)
1. Go to https://platform.openai.com/api-keys
2. Create API key

### 3. Set Environment Variables

Create `.env` file:

```bash
# Reddit
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_secret_here
REDDIT_USER_AGENT=BiasDetector/1.0

# Twitter
TWITTER_BEARER_TOKEN=your_bearer_token_here

# OpenAI (for Whisper)
OPENAI_API_KEY=sk-your_key_here
```

### 4. Test

```python
# Test Reddit
from src.backend.social_media_analyzer import RedditAnalyzer
reddit = RedditAnalyzer()
posts = reddit.fetch_subreddit_posts('politics', limit=10)
print(f"Fetched {len(posts)} posts")

# Test YouTube (free - uses captions)
from src.backend.media_transcriber import YouTubeTranscriber
yt = YouTubeTranscriber()
media = yt.transcribe('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
print(f"Transcribed: {media.title}")

# Test Citation Network (no API needed)
from src.backend.citation_network import CitationNetwork
network = CitationNetwork()
network.add_source("CNN", "cnn.com", "left")
print(f"Network has {len(network.sources)} sources")
```

---

## 📱 Using the Frontend

### Social Media Page

1. Navigate to http://localhost:3000/social-media
2. Select **Reddit** or **Twitter**
3. Enter search query:
   - Reddit: subreddit name (e.g., "politics", "news")
   - Twitter: keyword or hashtag (e.g., "#election2024")
4. Click **Analyze**
5. View bias distribution, posts, and stats

### Media Analysis Page

1. Navigate to http://localhost:3000/media
2. Choose **YouTube Video** or **Upload File**
3. For YouTube:
   - Paste video URL
   - Click Analyze
4. For Upload:
   - Drag & drop audio/video file (max 25MB)
   - Click Analyze File
5. View transcript, bias timeline, and segments

### Citation Network Page

1. Navigate to http://localhost:3000/citations
2. Click **Create Demo Network** to see sample data
3. Explore:
   - Network statistics
   - Most cited sources
   - Echo chambers detected
   - Cross-bias citation matrix
   - Source authority rankings

---

## 📊 Backend API Usage

### Social Media Endpoints

```bash
# Analyze Reddit subreddit
curl -X POST http://localhost:8000/api/v1/social-media/reddit/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "subreddit": "politics",
    "limit": 50,
    "analyze_comments": true
  }'

# Analyze Twitter topic
curl -X POST http://localhost:8000/api/v1/social-media/twitter/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "query": "climate change",
    "max_results": 100
  }'
```

### Media Endpoints

```bash
# Analyze YouTube video
curl -X POST http://localhost:8000/api/v1/media/youtube/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://www.youtube.com/watch?v=VIDEO_ID",
    "analyze_segments": true
  }'

# Upload audio file
curl -X POST http://localhost:8000/api/v1/media/upload \
  -F "file=@podcast.mp3" \
  -F "analyze_segments=true"
```

### Citation Network Endpoints

```bash
# Create demo network
curl -X POST http://localhost:8000/api/v1/citations/demo

# Get network summary
curl http://localhost:8000/api/v1/citations/summary

# Detect echo chambers
curl http://localhost:8000/api/v1/citations/echo-chambers?min_size=3

# Get cross-bias citations
curl http://localhost:8000/api/v1/citations/cross-bias
```

---

## 🎯 What Each Feature Does

### Social Media Analysis
- **Input:** Subreddit name or Twitter query
- **Process:** Fetches posts → Analyzes bias → Aggregates stats
- **Output:** 
  - Bias distribution chart
  - Individual post classifications
  - Comment analysis (Reddit)
  - Hashtag bias patterns (Twitter)
  - Confidence scores

### Video/Audio Analysis
- **Input:** YouTube URL or audio/video file
- **Process:** Transcribe → Analyze transcript → Segment analysis
- **Output:**
  - Full transcript text
  - Overall bias classification
  - Timeline of bias changes
  - Segment-by-segment breakdown
  - Confidence scores

### Citation Network
- **Input:** Articles with citations/mentions
- **Process:** Extract citations → Build graph → Detect communities
- **Output:**
  - Authority scores (PageRank)
  - Echo chamber detection
  - Cross-bias citation patterns
  - Source influence rankings
  - Network visualization data

---

## 💡 Examples

### Example 1: Compare Reddit vs Twitter on a Topic

```python
from src.backend.social_media_analyzer import SocialMediaBiasAnalyzer
from src.backend.bias_classifier import BiasClassifier

classifier = BiasClassifier()
analyzer = SocialMediaBiasAnalyzer(classifier)
analyzer.connect_reddit()
analyzer.connect_twitter()

result = analyzer.compare_platforms(
    topic="climate change",
    reddit_subreddit="all"
)

print("Twitter bias:", result['twitter']['bias_distribution'])
print("Reddit bias:", result['reddit']['bias_distribution'])
```

### Example 2: Analyze YouTube Channel

```python
from src.backend.media_transcriber import MediaBiasAnalyzer
from src.backend.bias_classifier import BiasClassifier

classifier = BiasClassifier()
analyzer = MediaBiasAnalyzer(classifier)
analyzer.setup_youtube()

videos = analyzer.batch_analyze_channel(
    channel_url="https://www.youtube.com/@newsnetwork",
    max_videos=10
)

summary = analyzer.get_bias_summary(videos)
print(f"Analyzed {summary['total_items']} videos")
print(f"Bias distribution: {summary['bias_distribution']}")
```

### Example 3: Build Citation Network

```python
from src.backend.citation_network import CitationExtractor, CitationNetwork

extractor = CitationExtractor()
network = CitationNetwork()

# Add sources
sources = [
    ("CNN", "cnn.com", "left"),
    ("Fox News", "foxnews.com", "right"),
    ("Reuters", "reuters.com", "center")
]

for name, domain, bias in sources:
    network.add_source(name, domain, bias)

# Analyze a group of articles (pseudo-code)
for article in articles:
    citations = extractor.extract_hyperlinks(
        article.html, article.id, article.source
    )
    for citation in citations:
        network.add_citation(citation)

# Get insights
chambers = network.detect_echo_chambers()
print(f"Found {len(chambers)} echo chambers")

summary = network.get_network_summary()
print(f"Network density: {summary['network_density']}")
```

---

## 🐛 Common Issues

### "ImportError: No module named 'praw'"
```bash
pip install -r requirements-features.txt
```

### "ValueError: Reddit credentials not provided"
Set `REDDIT_CLIENT_ID` and `REDDIT_CLIENT_SECRET` in `.env`

### "ValueError: OpenAI API key not provided"
Set `OPENAI_API_KEY` in `.env`

### "No transcript available for this video"
Some YouTube videos don't have captions. Try another video or use Whisper with yt-dlp.

### Frontend shows no data
- Make sure backend is running on port 8000
- Or use demo mode (API routes return mock data)

---

## 📚 Learn More

- Full documentation: [FEATURES_DOCUMENTATION.md](FEATURES_DOCUMENTATION.md)
- API documentation: http://localhost:8000/api/docs (when backend is running)
- Frontend: http://localhost:3000

---

## ✅ Quick Checklist

- [ ] Install dependencies: `pip install -r requirements-features.txt`
- [ ] Set environment variables in `.env`
- [ ] Start backend: `uvicorn backend.main:app --reload`
- [ ] Start frontend: `cd frontend-nextjs && npm run dev`
- [ ] Visit http://localhost:3000
- [ ] Try "Create Demo Network" in Citation Network
- [ ] Test with your API keys for real data

---

## 🎉 You're Ready!

All three features are now available in your Political Bias Detector. Start exploring!
