"""
LLM Service for Political Bias Detection

Integrates Google Gemini API for:
1. Topic-based query generation
2. Enhanced bias classification
3. Reasoning and explanation generation
"""

import logging
import os
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

# Import Gemini SDK when available
try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("Google Generative AI SDK not installed. Run: pip install google-generativeai")


class GeminiService:
    """Service for interacting with Google Gemini API."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini service.
        
        Args:
            api_key: Google Gemini API key (or uses GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.enabled = False
        self.model = None
        
        if not GEMINI_AVAILABLE:
            logger.warning("Gemini SDK not available")
            return
            
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set. LLM features will use fallback methods.")
            return
        
        try:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            self.enabled = True
            logger.info("Gemini API initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini API: {e}")
    
    def generate_search_queries(self, topic: str, num_queries: int = 5) -> List[str]:
        """
        Generate diverse search queries for a given topic using Gemini.
        
        Args:
            topic: The topic to generate queries for
            num_queries: Number of diverse queries to generate
            
        Returns:
            List of search query strings
        """
        if not self.enabled:
            return self._fallback_generate_queries(topic)
        
        try:
            prompt = f"""You are a news search expert. Generate {num_queries} diverse and specific search queries for finding news articles about the following topic.

Topic: {topic}

Requirements:
- Each query should approach the topic from a different angle
- Include queries that might reveal different political perspectives
- Keep queries concise (3-8 words each)
- Focus on recent news and current events
- Return ONLY the queries, one per line, no numbering or extra text

Example format:
climate change legislation
environmental policy debate
renewable energy initiatives
carbon emissions regulations
green new deal controversy"""

            response = self.model.generate_content(prompt)
            queries = [q.strip() for q in response.text.strip().split('\n') if q.strip()]
            
            # Ensure we have the topic itself as first query
            if topic.lower() not in [q.lower() for q in queries]:
                queries.insert(0, topic)
            
            return queries[:num_queries]
            
        except Exception as e:
            logger.error(f"Gemini query generation failed: {e}")
            return self._fallback_generate_queries(topic)
    
    def classify_bias(self, text: str, title: str = "") -> Dict[str, any]:
        """
        Classify political bias of text using Gemini.
        
        Args:
            text: Article text to classify
            title: Article title (optional)
            
        Returns:
            Dict with keys: bias, confidence, reasoning
        """
        if not self.enabled:
            return self._fallback_classify(text)
        
        try:
            full_text = f"{title}\n\n{text}" if title else text
            
            prompt = f"""You are an expert political analyst. Analyze the following news article text for political bias.

Classify it into ONE of these categories:
- Left-Leaning
- Center-Left
- Centrist
- Center-Right
- Right-Leaning

Consider:
1. Language choice and framing
2. Source selection and quotes
3. Emotional vs factual tone
4. What's emphasized vs omitted
5. Headlines and narrative structure

Article text:
{full_text[:2000]}

Provide your analysis in this EXACT format:
BIAS: [category]
CONFIDENCE: [0.0-1.0]
REASONING: [brief explanation in one sentence]

Example:
BIAS: Center-Left
CONFIDENCE: 0.78
REASONING: Article uses emotionally charged language favoring progressive policies while minimizing conservative viewpoints."""

            response = self.model.generate_content(prompt)
            result = self._parse_bias_response(response.text)
            
            if result:
                return result
            else:
                logger.warning("Failed to parse Gemini response, using fallback")
                return self._fallback_classify(text)
                
        except Exception as e:
            logger.error(f"Gemini bias classification failed: {e}")
            return self._fallback_classify(text)
    
    def _parse_bias_response(self, response_text: str) -> Optional[Dict]:
        """Parse Gemini's bias classification response."""
        try:
            lines = response_text.strip().split('\n')
            result = {}
            
            for line in lines:
                line = line.strip()
                if line.startswith('BIAS:'):
                    bias = line.replace('BIAS:', '').strip()
                    # Validate bias category
                    valid_biases = ['Left-Leaning', 'Center-Left', 'Centrist', 'Center-Right', 'Right-Leaning']
                    if bias in valid_biases:
                        result['bias'] = bias
                elif line.startswith('CONFIDENCE:'):
                    conf_str = line.replace('CONFIDENCE:', '').strip()
                    result['confidence'] = float(conf_str)
                elif line.startswith('REASONING:'):
                    result['reasoning'] = line.replace('REASONING:', '').strip()
            
            if 'bias' in result and 'confidence' in result and 'reasoning' in result:
                return {
                    'ml_bias': result['bias'],
                    'ml_confidence': result['confidence'],
                    'ml_reasoning': result['reasoning']
                }
            return None
            
        except Exception as e:
            logger.error(f"Error parsing bias response: {e}")
            return None
    
    def _fallback_generate_queries(self, topic: str) -> List[str]:
        """Fallback query generation when Gemini is not available."""
        topic_lower = topic.lower()
        queries = [
            topic,
            f"{topic} news",
            f"{topic} latest updates",
        ]
        
        # Context-aware queries
        if any(word in topic_lower for word in ['politics', 'election', 'policy', 'government']):
            queries.extend([f"{topic} analysis", f"{topic} debate"])
        elif any(word in topic_lower for word in ['economy', 'market', 'business']):
            queries.append(f"{topic} economic impact")
        elif any(word in topic_lower for word in ['climate', 'environment', 'energy']):
            queries.append(f"{topic} environmental policy")
        elif any(word in topic_lower for word in ['health', 'medical', 'vaccine']):
            queries.append(f"{topic} public health")
        
        return queries[:5]
    
    def _fallback_classify(self, text: str) -> Dict:
        """Fallback bias classification when Gemini is not available."""
        text_len = len(text)
        
        # Simple heuristic
        loaded_words = ['crisis', 'disaster', 'controversial', 'slams', 'blasts', 'attacks', 'outrage']
        loaded_count = sum(1 for word in loaded_words if word in text.lower())
        
        if text_len < 150:
            return {
                "ml_bias": "Centrist",
                "ml_confidence": 0.62,
                "ml_reasoning": "Brief neutral reporting detected (fallback classifier)"
            }
        elif loaded_count >= 2:
            return {
                "ml_bias": "Center-Left" if hash(text) % 2 == 0 else "Center-Right",
                "ml_confidence": 0.71,
                "ml_reasoning": f"Emotionally charged language detected ({loaded_count} indicators, fallback classifier)"
            }
        else:
            return {
                "ml_bias": "Centrist",
                "ml_confidence": 0.68,
                "ml_reasoning": "Balanced reporting style detected (fallback classifier)"
            }


# Global instance
_gemini_service = None

def get_gemini_service() -> GeminiService:
    """Get or create global Gemini service instance."""
    global _gemini_service
    if _gemini_service is None:
        _gemini_service = GeminiService()
    return _gemini_service
