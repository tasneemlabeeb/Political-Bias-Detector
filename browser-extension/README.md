# Political Bias Detector - Browser Extension

A Chrome/Firefox extension for real-time political bias detection on news articles.

## Features

- 🔍 **Automatic Detection**: Analyzes news articles as you browse
- 📊 **Visual Indicators**: Color-coded bias badges and spectrum visualization
- ⚡ **Fast Analysis**: Powered by ML models via REST API
- 🎨 **Clean UI**: Non-intrusive floating badge
- ⚙️ **Customizable**: Configure API endpoint, auto-analysis, and more

## Installation

### Development Installation

1. **Build the extension** (if needed):
   ```bash
   # No build step required - plain JavaScript
   ```

2. **Load in Chrome**:
   - Open `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select the `browser-extension/` directory

3. **Load in Firefox**:
   - Open `about:debugging#/runtime/this-firefox`
   - Click "Load Temporary Add-on"
   - Select `manifest.json` from `browser-extension/` directory

### Production Installation

1. **Package the extension**:
   ```bash
   cd browser-extension/
   zip -r bias-detector.zip . -x "*.git*" "*.DS_Store"
   ```

2. **Submit to Chrome Web Store / Firefox Add-ons**

## Configuration

### Backend API

The extension needs to connect to your FastAPI backend:

1. Open extension options (right-click icon → Options)
2. Set API URL: `http://localhost:8000/api/v1` (development) or your production URL
3. (Optional) Add API key for authentication

### Settings

- **Enable/Disable**: Toggle extension on/off
- **Auto-analyze**: Automatically analyze pages on load
- **API Configuration**: Set backend URL and API key
- **News Domains**: Customize which sites to analyze

## Usage

### Manual Analysis

1. Navigate to a news article
2. Click the extension icon
3. Click "Analyze This Page"
4. View results in the popup

### Automatic Analysis

If auto-analysis is enabled:
1. Navigate to a news article
2. Wait 2 seconds for automatic analysis
3. A floating badge will appear with results

### Badge Interactions

- **Drag**: Click and drag the header to reposition
- **Close**: Click the × button to dismiss
- **Details**: View detailed metrics in the badge

## Supported News Sites

Default list includes:
- CNN
- Fox News
- New York Times
- Washington Post
- BBC
- The Guardian
- Wall Street Journal
- Reuters
- AP News
- NPR
- Politico
- The Hill

## API Integration

The extension communicates with your backend API:

### Endpoints Used

```javascript
POST /api/v1/classify/text
{
  "text": "article content...",
  "title": "article title"
}
```

### Response Format

```json
{
  "bias_label": "Center-Left",
  "confidence": 0.85,
  "direction_score": -0.23,
  "intensity_score": 0.65,
  "spectrum": {
    "left": 0.35,
    "center": 0.45,
    "right": 0.20
  },
  "explanation": "Model analysis..."
}
```

## Architecture

```
browser-extension/
├── manifest.json          # Extension configuration
├── background.js          # Background service worker
├── content.js             # Content script (page analysis)
├── content.css            # Badge styles
├── popup.html             # Extension popup UI
├── popup.js               # Popup logic
├── options.html           # Settings page
├── options.js             # Settings logic
└── icons/                 # Extension icons
    ├── icon16.png
    ├── icon48.png
    └── icon128.png
```

## Development

### Testing

1. Start the backend API:
   ```bash
   docker-compose up
   ```

2. Load extension in browser (see Installation)

3. Navigate to a test article and analyze

### Debugging

- **Chrome**: Right-click extension icon → Inspect popup
- **Firefox**: about:debugging → Inspect
- **Console logs**: Check browser console on news article pages

## Permissions

The extension requires:

- `activeTab`: Access current tab content
- `storage`: Save settings and analysis cache
- `scripting`: Inject content scripts
- `host_permissions`: Connect to API backend

## Privacy

- No data is collected or stored remotely
- Article text is sent to your backend API for analysis only
- Analysis results cached locally
- No tracking or analytics

## Roadmap

- [ ] Add Firefox-specific optimizations
- [ ] Offline mode with cached models
- [ ] Multi-language support
- [ ] Dark mode
- [ ] Customizable badge position
- [ ] Export analysis history
- [ ] Comparison mode (view multiple articles)
- [ ] Social sharing integration

## Troubleshooting

### Extension not working

1. Check backend API is running: `curl http://localhost:8000/health`
2. Verify API URL in extension settings
3. Check browser console for errors
4. Reload the extension

### No analysis on page

- Verify it's a supported news domain
- Check article has sufficient text content
- Open browser console and look for "BiasDetector" logs

### API connection errors

- Check CORS settings in backend config
- Verify API endpoint URL
- Check network tab in dev tools

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file

## Support

- Report issues: GitHub Issues
- Email: support@biasdetector.com
- Documentation: https://docs.biasdetector.com
