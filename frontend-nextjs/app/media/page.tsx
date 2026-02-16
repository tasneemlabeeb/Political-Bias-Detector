'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { Video, Upload, Youtube, Play, FileAudio } from 'lucide-react'

export default function MediaAnalysisPage() {
  const [analysisType, setAnalysisType] = useState<'youtube' | 'upload'>('youtube')
  const [youtubeUrl, setYoutubeUrl] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [results, setResults] = useState<any>(null)

  const analyzeYouTube = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/media/youtube', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          video_url: youtubeUrl,
          analyze_segments: true
        })
      })
      const data = await response.json()
      setResults(data)
    } catch (error) {
      console.error('Error analyzing YouTube video:', error)
    }
    setLoading(false)
  }

  const analyzeUpload = async () => {
    if (!file) return
    
    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('analyze_segments', 'true')
      
      const response = await fetch('/api/media/upload', {
        method: 'POST',
        body: formData
      })
      const data = await response.json()
      setResults(data)
    } catch (error) {
      console.error('Error analyzing uploaded file:', error)
    }
    setLoading(false)
  }

  const handleAnalyze = () => {
    analysisType === 'youtube' ? analyzeYouTube() : analyzeUpload()
  }

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <div className="min-h-screen bg-white p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-bold text-[var(--ink)] mb-2">
            Video & Audio Bias Analysis
          </h1>
          <p className="text-[var(--muted)]">
            Transcribe and analyze political bias in video and podcast content
          </p>
        </motion.div>

        {/* Analysis Type Selection */}
        <div className="card p-6 mb-8">
          <div className="flex gap-4 mb-6">
            <button
              onClick={() => setAnalysisType('youtube')}
              className={`flex-1 py-3 px-6 font-bold transition-all ${
                analysisType === 'youtube'
                  ? 'bg-[#142c4c] text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Youtube className="w-5 h-5 inline-block mr-2" />
              YouTube Video
            </button>
            <button
              onClick={() => setAnalysisType('upload')}
              className={`flex-1 py-3 px-6 font-bold transition-all ${
                analysisType === 'upload'
                  ? 'bg-[#142c4c] text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <Upload className="w-5 h-5 inline-block mr-2" />
              Upload File
            </button>
          </div>

          {analysisType === 'youtube' ? (
            <div className="flex gap-4">
              <input
                type="text"
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
                placeholder="Enter YouTube video URL"
                className="flex-1 border border-gray-300 p-3 text-sm focus:ring-2 focus:ring-[#142c4c] focus:border-transparent"
              />
              <button
                onClick={handleAnalyze}
                disabled={loading || !youtubeUrl.trim()}
                className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <Play className="w-5 h-5 inline-block mr-2" />
                {loading ? 'Analyzing...' : 'Analyze'}
              </button>
            </div>
          ) : (
            <div>
              <label className="block border-2 border-dashed border-gray-300 p-8 text-center hover:border-[#142c4c] cursor-pointer transition-colors">
                <input
                  type="file"
                  accept="audio/*,video/*"
                  onChange={(e) => setFile(e.target.files?.[0] || null)}
                  className="hidden"
                />
                <FileAudio className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                <div className="text-sm text-[var(--muted)] mb-2">
                  {file ? file.name : 'Click to upload audio or video file'}
                </div>
                <div className="text-xs text-[var(--muted)]">
                  Supports MP3, MP4, WAV, M4A, WebM (max 25MB)
                </div>
              </label>
              {file && (
                <button
                  onClick={handleAnalyze}
                  disabled={loading}
                  className="btn-primary w-full mt-4 disabled:opacity-50"
                >
                  <Upload className="w-5 h-5 inline-block mr-2" />
                  {loading ? 'Analyzing...' : 'Analyze File'}
                </button>
              )}
            </div>
          )}
        </div>

        {/* Results */}
        {results && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            {/* Media Info */}
            <div className="card p-6">
              <h3 className="text-2xl font-bold text-[var(--ink)] mb-4">
                {results.title}
              </h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                <div>
                  <div className="text-xs text-[var(--muted)] mb-1">Duration</div>
                  <div className="font-semibold">{formatTime(results.duration)}</div>
                </div>
                {results.author && (
                  <div>
                    <div className="text-xs text-[var(--muted)] mb-1">Author</div>
                    <div className="font-semibold">{results.author}</div>
                  </div>
                )}
                {results.channel && (
                  <div>
                    <div className="text-xs text-[var(--muted)] mb-1">Channel</div>
                    <div className="font-semibold">{results.channel}</div>
                  </div>
                )}
                {results.publish_date && (
                  <div>
                    <div className="text-xs text-[var(--muted)] mb-1">Published</div>
                    <div className="font-semibold">
                      {new Date(results.publish_date).toLocaleDateString()}
                    </div>
                  </div>
                )}
              </div>

              {/* Overall Bias */}
              {results.political_bias && (
                <div className="border-t border-gray-200 pt-4">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-bold text-lg">Overall Bias</h4>
                    <span className="px-4 py-2 bg-[#142c4c] text-white font-bold">
                      {results.political_bias}
                    </span>
                  </div>
                  {results.ml_confidence && (
                    <div className="flex items-center gap-3 mb-3">
                      <span className="text-sm font-semibold text-[var(--muted)]">
                        Confidence
                      </span>
                      <div className="flex-1 h-2 bg-gray-200">
                        <div
                          className="h-full bg-[#142c4c]"
                          style={{ width: `${results.ml_confidence * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-bold">
                        {(results.ml_confidence * 100).toFixed(0)}%
                      </span>
                    </div>
                  )}
                  {results.ml_explanation && (
                    <div className="bg-gray-50 border border-gray-200 p-4 text-sm">
                      <div className="font-semibold mb-2">AI Analysis:</div>
                      <p className="text-[var(--muted)]">{results.ml_explanation}</p>
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Bias Timeline */}
            {results.bias_timeline && results.bias_timeline.length > 0 && (
              <div className="card p-6">
                <h3 className="text-xl font-bold text-[var(--ink)] mb-4">
                  Bias Timeline
                </h3>
                <div className="space-y-2">
                  {results.bias_timeline.map((point: any, idx: number) => (
                    <div key={idx} className="flex items-center gap-4">
                      <div className="w-16 text-sm font-semibold text-[var(--muted)]">
                        {formatTime(point.time)}
                      </div>
                      <div className="flex-1 flex items-center gap-2">
                        <span className="px-3 py-1 bg-[#142c4c] text-white text-xs font-bold">
                          {point.bias}
                        </span>
                        <div className="flex-1 h-1 bg-gray-200">
                          <div
                            className="h-full bg-[#142c4c]"
                            style={{ width: `${point.confidence * 100}%` }}
                          />
                        </div>
                        <span className="text-xs font-semibold">
                          {(point.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Transcript */}
            <div className="card p-6">
              <h3 className="text-xl font-bold text-[var(--ink)] mb-4">
                Transcript
              </h3>
              <div className="bg-gray-50 border border-gray-200 p-4 text-sm text-[var(--muted)] max-h-96 overflow-y-auto">
                {results.transcript}
              </div>
            </div>
          </motion.div>
        )}

        {/* Empty State */}
        {!results && !loading && (
          <div className="card p-12 text-center">
            <Video className="w-16 h-16 mx-auto mb-4 text-gray-400" />
            <h3 className="text-xl font-bold text-[var(--ink)] mb-2">
              Analyze Video & Audio Content
            </h3>
            <p className="text-[var(--muted)] max-w-md mx-auto">
              Upload a media file or provide a YouTube URL to transcribe and analyze
              political bias in the content
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
