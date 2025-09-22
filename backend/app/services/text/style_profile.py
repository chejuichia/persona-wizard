"""Text style profile analysis and generation."""

import json
import logging
import re
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import Counter

logger = logging.getLogger(__name__)


class TextStyleProfile:
    """Analyzes text to create a style profile."""
    
    def __init__(self, text: str):
        self.text = text
        self.cleaned_text = self._clean_text(text)
        self.words = self._tokenize(self.cleaned_text)
        self.sentences = self._split_sentences(self.cleaned_text)
        self.paragraphs = self._split_paragraphs(self.cleaned_text)
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove control characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]', '', text)
        return text
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple word tokenization."""
        # Split on whitespace and punctuation, keep only alphanumeric
        words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
        return words
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting on common sentence endings
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _split_paragraphs(self, text: str) -> List[str]:
        """Split text into paragraphs."""
        paragraphs = text.split('\n\n')
        return [p.strip() for p in paragraphs if p.strip()]
    
    def analyze(self) -> Dict[str, Any]:
        """Analyze text and return style profile."""
        if not self.words:
            return self._empty_profile()
        
        # Basic statistics
        word_count = len(self.words)
        sentence_count = len(self.sentences)
        paragraph_count = len(self.paragraphs)
        
        # Average sentence length
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
        
        # Average paragraph length
        avg_paragraph_length = word_count / paragraph_count if paragraph_count > 0 else 0
        
        # Vocabulary analysis
        unique_words = len(set(self.words))
        vocabulary_richness = unique_words / word_count if word_count > 0 else 0
        
        # Most common words (excluding common stop words)
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by',
            'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did',
            'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those',
            'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them'
        }
        
        filtered_words = [w for w in self.words if w not in stop_words and len(w) > 2]
        word_freq = Counter(filtered_words)
        most_common = word_freq.most_common(20)
        
        # Punctuation analysis
        punctuation_count = len(re.findall(r'[.!?,:;]', self.text))
        exclamation_count = len(re.findall(r'!', self.text))
        question_count = len(re.findall(r'\?', self.text))
        
        # Reading level estimation (simplified Flesch Reading Ease)
        syllables = self._count_syllables(self.words)
        avg_syllables_per_word = syllables / word_count if word_count > 0 else 0
        reading_ease = 206.835 - (1.015 * avg_sentence_length) - (84.6 * avg_syllables_per_word)
        
        # Tone analysis (simplified)
        tone_indicators = self._analyze_tone()
        
        return {
            "metadata": {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "paragraph_count": paragraph_count,
                "unique_words": unique_words,
                "character_count": len(self.text),
                "character_count_no_spaces": len(self.text.replace(' ', ''))
            },
            "style_metrics": {
                "avg_sentence_length": round(avg_sentence_length, 2),
                "avg_paragraph_length": round(avg_paragraph_length, 2),
                "vocabulary_richness": round(vocabulary_richness, 3),
                "reading_ease": round(reading_ease, 1),
                "punctuation_density": round(punctuation_count / word_count, 3) if word_count > 0 else 0
            },
            "vocabulary": {
                "most_common_words": most_common,
                "vocabulary_size": unique_words,
                "stop_word_ratio": round((word_count - len(filtered_words)) / word_count, 3) if word_count > 0 else 0
            },
            "punctuation": {
                "exclamation_ratio": round(exclamation_count / word_count, 3) if word_count > 0 else 0,
                "question_ratio": round(question_count / word_count, 3) if word_count > 0 else 0,
                "total_punctuation": punctuation_count
            },
            "tone": tone_indicators,
            "text_samples": {
                "first_sentence": self.sentences[0] if self.sentences else "",
                "last_sentence": self.sentences[-1] if self.sentences else "",
                "longest_sentence": max(self.sentences, key=len) if self.sentences else "",
                "shortest_sentence": min(self.sentences, key=len) if self.sentences else ""
            }
        }
    
    def _count_syllables(self, words: List[str]) -> int:
        """Count syllables in words (simplified)."""
        total = 0
        for word in words:
            # Simple syllable counting: count vowel groups
            vowels = 'aeiouy'
            word = word.lower()
            if word:
                # Count vowel groups
                vowel_groups = 0
                prev_was_vowel = False
                for char in word:
                    is_vowel = char in vowels
                    if is_vowel and not prev_was_vowel:
                        vowel_groups += 1
                    prev_was_vowel = is_vowel
                
                # Handle silent 'e'
                if word.endswith('e') and vowel_groups > 1:
                    vowel_groups -= 1
                
                # Minimum 1 syllable per word
                total += max(1, vowel_groups)
        
        return total
    
    def _analyze_tone(self) -> Dict[str, float]:
        """Analyze tone indicators (simplified)."""
        text_lower = self.text.lower()
        
        # Positive indicators
        positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'like', 'enjoy', 'happy', 'pleased', 'satisfied']
        positive_count = sum(text_lower.count(word) for word in positive_words)
        
        # Negative indicators
        negative_words = ['bad', 'terrible', 'awful', 'hate', 'dislike', 'angry', 'sad', 'disappointed', 'frustrated', 'annoyed']
        negative_count = sum(text_lower.count(word) for word in negative_words)
        
        # Formal indicators
        formal_words = ['therefore', 'however', 'furthermore', 'moreover', 'consequently', 'nevertheless', 'thus', 'hence']
        formal_count = sum(text_lower.count(word) for word in formal_words)
        
        # Casual indicators
        casual_words = ['yeah', 'ok', 'cool', 'awesome', 'hey', 'hi', 'gonna', 'wanna', 'gotta']
        casual_count = sum(text_lower.count(word) for word in casual_words)
        
        total_words = len(self.words)
        
        return {
            "positive": round(positive_count / total_words, 3) if total_words > 0 else 0,
            "negative": round(negative_count / total_words, 3) if total_words > 0 else 0,
            "formal": round(formal_count / total_words, 3) if total_words > 0 else 0,
            "casual": round(casual_count / total_words, 3) if total_words > 0 else 0
        }
    
    def _empty_profile(self) -> Dict[str, Any]:
        """Return empty profile for empty text."""
        return {
            "metadata": {
                "word_count": 0,
                "sentence_count": 0,
                "paragraph_count": 0,
                "unique_words": 0,
                "character_count": 0,
                "character_count_no_spaces": 0
            },
            "style_metrics": {
                "avg_sentence_length": 0,
                "avg_paragraph_length": 0,
                "vocabulary_richness": 0,
                "reading_ease": 0,
                "punctuation_density": 0
            },
            "vocabulary": {
                "most_common_words": [],
                "vocabulary_size": 0,
                "stop_word_ratio": 0
            },
            "punctuation": {
                "exclamation_ratio": 0,
                "question_ratio": 0,
                "total_punctuation": 0
            },
            "tone": {
                "positive": 0,
                "negative": 0,
                "formal": 0,
                "casual": 0
            },
            "text_samples": {
                "first_sentence": "",
                "last_sentence": "",
                "longest_sentence": "",
                "shortest_sentence": ""
            }
        }
    
    def save_profile(self, output_path: Path) -> None:
        """Save style profile to JSON file."""
        profile = self.analyze()
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Style profile saved to: {output_path}")


def create_style_profile(text: str, output_path: Path) -> Dict[str, Any]:
    """Create and save a style profile from text."""
    if not text.strip():
        raise ValueError("Text cannot be empty")
    
    if len(text) < 10:
        raise ValueError("Text must be at least 10 characters long")
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Create and analyze profile
    profile_analyzer = TextStyleProfile(text)
    profile = profile_analyzer.analyze()
    
    # Save profile
    profile_analyzer.save_profile(output_path)
    
    return profile
