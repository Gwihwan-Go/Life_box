#This file deals with the language data
# Categorizing Logic
# raw_words -> core_words -> lemmatization -> if any word of words in category_list -> category

from enum import Enum
from typing import Dict, List, Optional
import json
import re
from textblob import TextBlob, Word

# Constants
KEYLIST_SAVE_PATH = "resources/key_list.json"
UNLIST_WORDS_PATH = 'resources/unlisted_words.txt'

class ActivityCategory(Enum):
    ACADEMIC = '📖Academic'
    WORK = '💰Work'
    CHORES = '🧹Chores'
    SLEEP = '💤Sleep'
    OTHER = 'others'

class ActivityClassifier:
    """Simple activity classifier using keyword matching."""
    
    def __init__(self, key_list_path: str = KEYLIST_SAVE_PATH):
        self.key_list = self.load_key_list(key_list_path)
    
    def load_key_list(self, path: str) -> Dict:
        """Load classification rules from JSON file."""
        try:
            with open(path) as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading key list: {e}")
            return {}
    
    def preprocess(self, text: str) -> str:
        """Basic text preprocessing."""
        text = re.sub('[^a-zA-Z]+', ' ', text)
        return text.lower().strip() or 'others'
    
    def search(self, target: str) -> Optional[str]:
        """Search for matching category."""
        target = target.lower()
        for key, word_list in self.key_list.items():
            if any(word in target for word in word_list):
                return key
        return None
    
    def categorize(self, activity: str) -> str:
        """Categorize an activity."""
        try:
            words = self.preprocess(activity)
            for word in words.split():
                category = self.search(word)
                if category:
                    print(f"{category} <- {activity}({word})", end='')
                    return category
            
            self.log_unclassified(words)
            print(f"{words}({activity}) doesn't exist in the key list", end='')
            return 'others'
        except Exception as e:
            print(f"Categorization error: {e}")
            return 'others'
    
    def log_unclassified(self, word: str) -> None:
        """Log unclassified words for future improvement."""
        try:
            with open(UNLIST_WORDS_PATH, 'a') as f:
                f.write(f"{word}\n")
        except Exception as e:
            print(f"Error logging unclassified word: {e}")

# Global classifier instance
_classifier = ActivityClassifier()

# Public interface
def categorize(activity: str) -> str:
    """Public interface for activity categorization."""
    return _classifier.categorize(activity)

def print_and_clear_unlist_words() -> None:
    """Print and clear the unclassified words log."""
    try:
        with open(UNLIST_WORDS_PATH, 'r') as f:
            words = f.read().strip().split('\n')
            for word in words:
                if word:  # Skip empty lines
                    print(f"unlisted words: {word}")
        
        with open(UNLIST_WORDS_PATH, 'w') as f:
            pass  # Clear file
        print("unlisted words file has been cleared")
    except FileNotFoundError:
        pass  # Ignore if file doesn't exist

def get_classifier(config: Dict = None) -> ActivityClassifier:
    """Factory function to get appropriate classifier."""
    if config and config.get('use_llm'):
        return LLMActivityClassifier(config)
    return ActivityClassifier()

class LLMActivityClassifier(ActivityClassifier):
    """Future LLM-based classifier."""
    
    def __init__(self, model_config: Dict):
        super().__init__()
        self.model_config = model_config
        
    def classify(self, activity: str) -> str:
        """
        Override with LLM-based classification.
        To be implemented when integrating LLM.
        """
        # TODO: Implement LLM classification
        return super().classify(activity)

if __name__ == "__main__" :
    # print(categorize(['coda - homwork (hi) hello']))
    print_and_clear_unlist_words()
