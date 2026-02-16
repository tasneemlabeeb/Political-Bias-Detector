# NewsAPI Setup Guide

## Get Your Free API Key

1. Go to [https://newsapi.org/](https://newsapi.org/)
2. Click "Get API Key" or "Register"
3. Fill in your details:
   - Name
   - Email
   - Password
4. Choose the **Free Developer** plan (100 requests/day)
5. Confirm your email address
6. Copy your API key from the dashboard

## Add to Your Project

1. Open `.env` file in the project root
2. Find the line: `NEWS_API_KEY=`
3. Paste your API key after the equals sign:
   ```
   NEWS_API_KEY=your_api_key_here
   ```
4. Restart the backend server

## Free Tier Limitations

- **100 requests per day**
- Articles from the **last 30 days**
- Up to **100 results per request**
- **Live** headlines only (no archived news)

For production use, consider upgrading to a paid plan.

## API Usage

The search endpoint will now:
1. Search NewsAPI for articles matching your query
2. Fetch full article content from source websites
3. Classify each article using the ML model
4. Return detailed bias analysis

## Example Queries

- `bangladesh`
- `climate change`
- `US election`
- `artificial intelligence`
- `cryptocurrency`

## Troubleshooting

### "News search service not configured"
- Make sure `NEWS_API_KEY` is set in `.env`
- Restart the backend after adding the key

### "Too Many Requests" error
- You've hit the 100 requests/day limit
- Wait 24 hours or upgrade your plan

### No results found
- Try broader search terms
- Check if the topic is in recent news (last 30 days)
- Ensure your NewsAPI key is valid
