"""
Utility functions for prompt validation and analysis
Provides helper functions for character counting, word analysis, and optimization tracking
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class PromptAnalyzer:
    """Utility class for analyzing and processing prompts"""
    
    # Configuration constants
    MAX_LENGTH = 10000
    OPTIMIZATION_THRESHOLD = 3000
    TARGET_LENGTH = 2800
    
    @staticmethod
    def count_characters(text: str) -> int:
        """Count characters in text"""
        return len(text) if text else 0
    
    @staticmethod
    def count_words(text: str) -> int:
        """Count words in text"""
        if not text:
            return 0
        return len(text.split())
    
    @staticmethod
    def count_sentences(text: str) -> int:
        """Count sentences in text"""
        if not text:
            return 0
        # Simple sentence counting using periods, exclamation marks, and question marks
        sentences = re.split(r'[.!?]+', text)
        return len([s for s in sentences if s.strip()])
    
    @staticmethod
    def extract_keywords(text: str, min_length: int = 3) -> List[str]:
        """Extract keywords from text (words longer than min_length)"""
        if not text:
            return []
        
        # Remove punctuation and split into words
        words = re.findall(r'\b[a-zA-Z]{' + str(min_length) + ',}\b', text.lower())
        
        # Remove common stop words
        stop_words = {
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can', 'had', 'her', 'was', 'one', 'our',
            'out', 'day', 'get', 'has', 'him', 'his', 'how', 'man', 'new', 'now', 'old', 'see', 'two', 'way',
            'who', 'boy', 'did', 'its', 'let', 'put', 'say', 'she', 'too', 'use', 'with', 'into', 'than', 'this',
            'have', 'from', 'they', 'know', 'want', 'been', 'good', 'much', 'some', 'time', 'very', 'when', 'come',
            'here', 'just', 'like', 'long', 'make', 'many', 'over', 'such', 'take', 'well', 'were'
        }
        
        keywords = [word for word in words if word not in stop_words]
        
        # Remove duplicates while preserving order
        seen = set()
        unique_keywords = []
        for word in keywords:
            if word not in seen:
                seen.add(word)
                unique_keywords.append(word)
        
        return unique_keywords
    
    @staticmethod
    def analyze_prompt_structure(text: str) -> Dict[str, Any]:
        """Analyze the structure and components of a prompt"""
        if not text:
            return {
                "subject_detected": False,
                "style_keywords": [],
                "quality_terms": [],
                "technical_specs": [],
                "descriptive_adjectives": [],
                "composition_terms": []
            }
        
        text_lower = text.lower()
        
        # Common style keywords
        style_keywords = []
        style_patterns = [
            'digital art', 'oil painting', 'watercolor', 'photorealistic', 'anime', 'cartoon',
            'realistic', 'abstract', 'surreal', 'minimalist', 'vintage', 'modern'
        ]
        for pattern in style_patterns:
            if pattern in text_lower:
                style_keywords.append(pattern)
        
        # Quality terms
        quality_terms = []
        quality_patterns = [
            'masterpiece', 'best quality', 'high quality', 'highly detailed', 'ultra detailed',
            'intricate', '8k', '4k', 'hd', 'ultra hd', 'professional', 'award winning'
        ]
        for pattern in quality_patterns:
            if pattern in text_lower:
                quality_terms.append(pattern)
        
        # Technical specifications
        technical_specs = []
        tech_patterns = [
            r'\d+mm', r'f/\d+\.?\d*', r'\d+k', r'iso \d+', 'canon', 'nikon', 'sony',
            'bokeh', 'depth of field', 'shallow focus', 'macro', 'wide angle'
        ]
        for pattern in tech_patterns:
            matches = re.findall(pattern, text_lower)
            technical_specs.extend(matches)
        
        # Composition terms
        composition_terms = []
        comp_patterns = [
            'close-up', 'wide shot', 'medium shot', 'rule of thirds', 'golden ratio',
            'symmetrical', 'asymmetrical', 'centered', 'off-center', 'portrait', 'landscape'
        ]
        for pattern in comp_patterns:
            if pattern in text_lower:
                composition_terms.append(pattern)
        
        # Simple subject detection (look for common subjects)
        subject_detected = bool(re.search(r'\b(woman|man|person|girl|boy|cat|dog|house|car|tree|flower|landscape|portrait|character)\b', text_lower))
        
        return {
            "subject_detected": subject_detected,
            "style_keywords": style_keywords,
            "quality_terms": quality_terms,
            "technical_specs": technical_specs,
            "composition_terms": composition_terms,
            "descriptive_adjectives": len(re.findall(r'\b(beautiful|gorgeous|stunning|amazing|incredible|fantastic|wonderful|perfect|excellent|brilliant)\b', text_lower))
        }
    
    @classmethod
    def get_full_analysis(cls, text: str) -> Dict[str, Any]:
        """Get comprehensive analysis of a prompt"""
        char_count = cls.count_characters(text)
        word_count = cls.count_words(text)
        sentence_count = cls.count_sentences(text)
        keywords = cls.extract_keywords(text)
        structure = cls.analyze_prompt_structure(text)
        
        return {
            "character_count": char_count,
            "word_count": word_count,
            "sentence_count": sentence_count,
            "keywords": keywords[:20],  # Limit to top 20 keywords
            "keyword_count": len(keywords),
            "structure": structure,
            "needs_optimization": char_count > cls.OPTIMIZATION_THRESHOLD,
            "exceeds_maximum": char_count > cls.MAX_LENGTH,
            "optimization_threshold": cls.OPTIMIZATION_THRESHOLD,
            "maximum_length": cls.MAX_LENGTH,
            "target_length": cls.TARGET_LENGTH,
            "estimated_reduction_needed": max(0, char_count - cls.TARGET_LENGTH),
            "complexity_score": cls._calculate_complexity_score(char_count, word_count, sentence_count, len(keywords)),
            "readability_score": cls._calculate_readability_score(char_count, word_count, sentence_count)
        }
    
    @staticmethod
    def _calculate_complexity_score(char_count: int, word_count: int, sentence_count: int, keyword_count: int) -> float:
        """Calculate a complexity score for the prompt (0-100)"""
        if word_count == 0:
            return 0.0
        
        # Factors contributing to complexity
        avg_word_length = char_count / word_count if word_count > 0 else 0
        avg_sentence_length = word_count / sentence_count if sentence_count > 0 else word_count
        keyword_density = keyword_count / word_count if word_count > 0 else 0
        
        # Normalize and combine factors
        complexity = (
            min(avg_word_length / 10, 1) * 30 +  # Word length complexity (0-30)
            min(avg_sentence_length / 20, 1) * 40 +  # Sentence length complexity (0-40)
            min(keyword_density * 2, 1) * 30  # Keyword density complexity (0-30)
        )
        
        return round(complexity, 2)
    
    @staticmethod
    def _calculate_readability_score(char_count: int, word_count: int, sentence_count: int) -> float:
        """Calculate a readability score for the prompt (0-100, higher is more readable)"""
        if word_count == 0 or sentence_count == 0:
            return 0.0
        
        # Simple readability metric based on average word and sentence length
        avg_word_length = char_count / word_count
        avg_sentence_length = word_count / sentence_count
        
        # Ideal ranges: 4-6 chars per word, 10-20 words per sentence
        word_score = max(0, 100 - abs(avg_word_length - 5) * 10)
        sentence_score = max(0, 100 - abs(avg_sentence_length - 15) * 3)
        
        readability = (word_score + sentence_score) / 2
        return round(readability, 2)

class OptimizationTracker:
    """Track optimization operations and statistics"""
    
    def __init__(self):
        self.optimizations = []
    
    def record_optimization(
        self,
        original_length: int,
        optimized_length: int,
        optimization_time: float,
        success: bool,
        model_used: Optional[str] = None,
        error_message: Optional[str] = None
    ):
        """Record an optimization operation"""
        record = {
            "timestamp": datetime.utcnow().isoformat(),
            "original_length": original_length,
            "optimized_length": optimized_length,
            "reduction": original_length - optimized_length,
            "reduction_percentage": ((original_length - optimized_length) / original_length * 100) if original_length > 0 else 0,
            "optimization_time": optimization_time,
            "success": success,
            "model_used": model_used,
            "error_message": error_message
        }
        
        self.optimizations.append(record)
        
        # Keep only last 100 records to prevent memory issues
        if len(self.optimizations) > 100:
            self.optimizations = self.optimizations[-100:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get optimization statistics"""
        if not self.optimizations:
            return {
                "total_optimizations": 0,
                "success_rate": 0.0,
                "average_reduction": 0.0,
                "average_time": 0.0,
                "total_characters_saved": 0
            }
        
        successful = [opt for opt in self.optimizations if opt["success"]]
        
        return {
            "total_optimizations": len(self.optimizations),
            "success_rate": (len(successful) / len(self.optimizations)) * 100,
            "average_reduction": sum(opt["reduction"] for opt in successful) / len(successful) if successful else 0,
            "average_reduction_percentage": sum(opt["reduction_percentage"] for opt in successful) / len(successful) if successful else 0,
            "average_time": sum(opt["optimization_time"] for opt in successful) / len(successful) if successful else 0,
            "total_characters_saved": sum(opt["reduction"] for opt in successful),
            "recent_optimizations": self.optimizations[-10:]  # Last 10 operations
        }

# Global tracker instance
global_tracker = OptimizationTracker()

def get_optimization_tracker() -> OptimizationTracker:
    """Get the global optimization tracker"""
    return global_tracker

def analyze_prompt(text: str) -> Dict[str, Any]:
    """Convenience function for full prompt analysis"""
    return PromptAnalyzer.get_full_analysis(text)

def validate_prompt_length(text: str) -> Tuple[bool, Optional[str]]:
    """Validate prompt length and return validation result"""
    if not text:
        return False, "Prompt cannot be empty"
    
    length = len(text)
    
    if length > PromptAnalyzer.MAX_LENGTH:
        return False, f"Prompt exceeds maximum length of {PromptAnalyzer.MAX_LENGTH} characters (current: {length})"
    
    return True, None

def needs_optimization(text: str) -> bool:
    """Check if prompt needs optimization"""
    return len(text) > PromptAnalyzer.OPTIMIZATION_THRESHOLD if text else False

def estimate_optimization_time(text_length: int) -> float:
    """Estimate optimization time based on text length"""
    # Base time + time per character (rough estimate)
    base_time = 5.0  # 5 seconds base
    time_per_char = 0.001  # 1ms per character
    
    estimated = base_time + (text_length * time_per_char)
    return min(estimated, 120.0)  # Cap at 2 minutes