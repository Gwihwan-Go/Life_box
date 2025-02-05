#This file deals with the language data
# Categorizing Logic
# raw_words -> core_words -> lemmatization -> if any word of words in category_list -> category

from enum import Enum
from typing import Dict, List, Optional
import json
import re
from textblob import TextBlob, Word

class ActivityCategory(Enum):
    ACADEMIC = '📖Academic'
    WORK = '💰Work'
    CHORES = '🧹Chores'
    SLEEP = '💤Sleep'
    OTHER = 'others'

class ActivityClassifier:
    """Base class for activity classification strategies."""
    
    def __init__(self, key_list_path: str = "resources/key_list.json"):
        self.key_list = self.load_key_list(key_list_path)
        
    def load_key_list(self, path: str) -> Dict:
        """Load classification rules from JSON file."""
        with open(path) as f:
            return json.load(f)
    
    def classify(self, activity: str) -> str:
        """Classify an activity into a category."""
        processed = self.preprocess(activity)
        return self.search(processed) or ActivityCategory.OTHER.value
    
    def preprocess(self, text: str) -> str:
        """Preprocess text before classification."""
        text = re.sub('[^a-zA-Z]+', ' ', text)
        text = text.lower().strip()
        
        if not text:
            return 'others'
            
        # Lemmatization
        blob = TextBlob(text)
        words = []
        for word in blob.words:
            try:
                lemma = Word(word).lemmatize()
                words.append(str(lemma))
            except:
                words.append(word)
                
        return ' '.join(words)
    
    def search(self, target: str) -> Optional[str]:
        """Search for matching category in key_list."""
        for key, word_list in self.key_list.items():
            if any(word in target for word in word_list):
                return key
        return None

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

def get_classifier(config: Dict = None) -> ActivityClassifier:
    """Factory function to get appropriate classifier."""
    if config and config.get('use_llm'):
        return LLMActivityClassifier(config)
    return ActivityClassifier()

# Helper functions
def log_unclassified(word: str, path: str = 'resources/unlisted_words.txt'):
    """Log words that couldn't be classified."""
    with open(path, 'a') as f:
        f.write(f"{word}\n")

def print_and_clear_unlist_words(path: str = 'resources/unlisted_words.txt'):
    """Print and clear the unclassified words log."""
    try:
        with open(path, 'r') as f:
            words = f.read().strip().split('\n')
            for word in words:
                print(f"unlisted words: {word}")
        
        with open(path, 'w') as f:
            pass
        print("unlisted words file has been cleared")
    except FileNotFoundError:
        pass

def categorize(words) :
    """
    algorithm of categorizing words
    input :
        word(str) : target word or words ex) 'nap', 'play at park'
    output :
        category(str) : representation of the word
    """
    key_list=get_classifier().key_list
    words = re.sub('[^a-zA-Z]+', ' ', words) #remove non-alphabet from
    for word in words.split() :
        word = get_classifier().preprocess(word)
        cate = get_classifier().search(word) ##categroize dictionary key to more representative ones
        if cate is not None :
            print(f"{cate} <- {words}({word})", end='') # continue print divided hour at interpret_table_contents in html_parser 
            return cate
    log_unclassified(get_classifier().preprocess(words))
    print(f"{get_classifier().preprocess(words)}({words}) doesn't exist in the key list", end='')
    return ActivityCategory.OTHER.value

if __name__ == "__main__" :
    # print(categorize(['coda - homwork (hi) hello']))
    print_and_clear_unlist_words()
