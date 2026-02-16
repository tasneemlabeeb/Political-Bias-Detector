# Political Bias Detector - Next.js Frontend

A modern, responsive frontend built with Next.js 14, React, TypeScript, and Tailwind CSS.

## 🚀 Features

- **Modern UI**: Beautiful gradient backgrounds, smooth animations, and responsive design
- **Real-time Filtering**: Filter articles by source, bias, date, and keywords
- **AI Integration**: Classify articles with ML and display confidence scores
- **Interactive Charts**: Visualize bias distribution across articles
- **Smooth Animations**: Framer Motion for delightful user experience
- **TypeScript**: Full type safety throughout the application
- **Tailwind CSS**: Utility-first styling with custom theme

## 📦 Installation

```bash
cd frontend-nextjs
npm install
```

## 🔧 Configuration

Create a `.env.local` file in the root directory:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 🏃 Running the Application

### Development Mode

```bash
npm run dev
```

The application will be available at [http://localhost:3000](http://localhost:3000)

### Production Build

```bash
npm run build
npm start
```

## 📁 Project Structure

```
frontend-nextjs/
├── app/
│   ├── api/              # API routes
│   │   ├── articles/     # Fetch articles endpoint
│   │   └── classify/     # AI classification endpoint
│   ├── globals.css       # Global styles
│   ├── layout.tsx        # Root layout
│   └── page.tsx          # Home page
├── components/
│   ├── Header.tsx        # Page header
│   ├── MetricCards.tsx   # Statistics cards
│   ├── BiasSpectrum.tsx  # Bias visualization
│   ├── ArticlesList.tsx  # Articles display
│   └── FilterPanel.tsx   # Filters and sorting
├── types/
│   └── index.ts          # TypeScript types
├── package.json
├── tsconfig.json
├── tailwind.config.ts
└── next.config.js
```

## 🎨 Components

### Header
Displays the main title and description with gradient text effects.

### MetricCards
Shows key statistics (total articles, filtered count, sources, AI confidence).

### BiasSpectrum
Animated horizontal bar chart showing distribution across political biases.

### FilterPanel
Collapsible panel with advanced filtering options:
- Source selection
- Bias categories
- Date range
- Keyword search
- AI confidence threshold
- Sort options

### ArticlesList
Displays article cards with:
- Title and link
- Bias badges (source & AI)
- AI confidence bars
- Summaries
- Optional AI reasoning details

## 🔌 API Integration

The app includes placeholder API routes. To connect to your Python backend:

1. Update `app/api/articles/route.ts` to fetch from your backend
2. Update `app/api/classify/route.ts` to call your classification endpoint
3. Set `NEXT_PUBLIC_API_URL` in `.env.local`

Example:

```typescript
// app/api/articles/route.ts
export async function GET() {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/articles`)
  const data = await response.json()
  return NextResponse.json(data)
}
```

## 🎨 Styling

The app uses a custom color scheme defined in `tailwind.config.ts`:

- **Bias Colors**: Blue (left) to Red (right) spectrum
- **Accents**: Teal (#0d9488) and Amber (#f59e0b)
- **Background**: Warm gradient with radial overlays
- **Cards**: White/cream with subtle shadows

## 📱 Responsive Design

Fully responsive with breakpoints:
- Mobile: < 640px
- Tablet: 640px - 1024px  
- Desktop: > 1024px

## ⚡ Performance

- **Code Splitting**: Automatic with Next.js
- **Image Optimization**: Built-in Next.js optimization
- **Server Components**: Where possible for better performance
- **Client Components**: Only where interactivity is needed

## 🛠️ Development

### Adding New Features

1. Create components in `components/`
2. Add types to `types/index.ts`
3. Import and use in `app/page.tsx`

### Customizing Styles

Edit `tailwind.config.ts` for theme changes or `app/globals.css` for global styles.

## 📝 TODO

- [ ] Connect real API endpoints
- [ ] Add error handling and loading states
- [ ] Implement data caching
- [ ] Add user authentication
- [ ] Create admin dashboard
- [ ] Add export functionality
- [ ] Implement dark mode

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a pull request

## 📄 License

MIT License - see LICENSE file for details
