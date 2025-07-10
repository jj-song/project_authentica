#!/usr/bin/env python3
"""
Humanizer module for Project Authentica.
Provides functions to make AI-generated text appear more human-like.
"""

import random
import re
from typing import List, Dict, Any, Optional, Tuple


class TextHumanizer:
    """
    Transforms AI-generated text to appear more human-like by introducing
    deliberate imperfections and natural language patterns.
    """
    
    # Common typos people make when typing quickly
    COMMON_TYPOS = {
        'the': ['teh', 'hte', 'th'],
        'and': ['adn', 'nad', 'an'],
        'that': ['taht', 'tht', 'ttha'],
        'with': ['wiht', 'wtih', 'wth'],
        'have': ['ahve', 'hvae', 'hve'],
        'this': ['tihs', 'thsi', 'tis'],
        'would': ['woudl', 'wuold', 'wold'],
        'there': ['tehre', 'thre', 'ther'],
        'their': ['thier', 'thir', 'theri'],
        'your': ['yoru', 'youre', 'ur'],
        'about': ['aobut', 'abotu', 'bout'],
        'what': ['waht', 'whta', 'wat'],
        'just': ['jsut', 'juts', 'jst'],
        'like': ['liek', 'lke', 'lik'],
        'know': ['knwo', 'kno', 'konw'],
        'people': ['poeple', 'peopel', 'ppl'],
        'because': ['becuase', 'becase', 'cuz', 'bc'],
        'really': ['realy', 'relly', 'rly'],
        'think': ['thikn', 'thnk', 'tink'],
        'should': ['shuold', 'shoudl', 'shud'],
    }
    
    # Filler words to occasionally insert
    FILLER_WORDS = [
        'like', 'um', 'uh', 'you know', 'I mean', 'actually', 'basically',
        'honestly', 'literally', 'seriously', 'I guess', 'kinda', 'sorta',
        'well', 'anyway', 'so', 'yeah', 'tbh', 'I think', 'probably'
    ]
    
    # Contractions to replace formal phrases
    CONTRACTIONS = {
        'it is': ["it's"],
        'do not': ["don't"],
        'does not': ["doesn't"],
        'did not': ["didn't"],
        'is not': ["isn't"],
        'are not': ["aren't"],
        'was not': ["wasn't"],
        'were not': ["weren't"],
        'have not': ["haven't"],
        'has not': ["hasn't"],
        'had not': ["hadn't"],
        'will not': ["won't"],
        'would not': ["wouldn't"],
        'could not': ["couldn't"],
        'should not': ["shouldn't"],
        'cannot': ["can't"],
        'I am': ["I'm"],
        'you are': ["you're"],
        'he is': ["he's"],
        'she is': ["she's"],
        'it is': ["it's"],
        'we are': ["we're"],
        'they are': ["they're"],
        'I have': ["I've"],
        'you have': ["you've"],
        'we have': ["we've"],
        'they have': ["they've"],
        'I will': ["I'll"],
        'you will': ["you'll"],
        'he will': ["he'll"],
        'she will': ["she'll"],
        'it will': ["it'll"],
        'we will': ["we'll"],
        'they will': ["they'll"],
        'I would': ["I'd"],
        'you would': ["you'd"],
        'he would': ["he'd"],
        'she would': ["she'd"],
        'it would': ["it'd"],
        'we would': ["we'd"],
        'they would': ["they'd"],
        'going to': ['gonna'],
        'want to': ['wanna'],
        'got to': ['gotta'],
        'kind of': ['kinda'],
        'sort of': ['sorta'],
        'out of': ['outta'],
        'trying to': ['tryna'],
    }
    
    # Informal abbreviations
    ABBREVIATIONS = {
        'though': ['tho'],
        'through': ['thru'],
        'because': ['cuz', 'bc', 'cause'],
        'probably': ['prob'],
        'definitely': ['def'],
        'whatever': ['w/e'],
        'something': ['smth', 'somethin'],
        'about': ['bout'],
        'before': ['b4'],
        'tonight': ['tonite'],
        'tomorrow': ['tmrw'],
        'them': ['em'],
        'you': ['u'],
        'your': ['ur'],
        'are': ['r'],
        'for': ['4'],
        'to': ['2'],
        'too': ['2'],
        'be': ['b'],
        'see': ['c'],
        'okay': ['ok', 'k'],
        'please': ['pls'],
        'thanks': ['thx'],
        'with': ['w/'],
        'without': ['w/o'],
        'people': ['ppl'],
        'really': ['rly'],
        'never': ['nvr'],
        'ever': ['evr'],
        'every': ['evry'],
        'love': ['luv'],
        'know': ['kno'],
        'why': ['y'],
        'what': ['wut', 'wat'],
        'great': ['gr8'],
        'wait': ['w8'],
        'mate': ['m8'],
        'later': ['l8r'],
        'straight': ['str8'],
    }
    
    def __init__(self, humanization_level: float = 0.5):
        """
        Initialize the TextHumanizer with a specified humanization level.
        
        Args:
            humanization_level (float): A value between 0.0 (minimal humanization) 
                                       and 1.0 (maximum humanization)
        """
        self.humanization_level = max(0.0, min(1.0, humanization_level))
        
        # Calculate probabilities based on humanization level
        self.typo_probability = 0.03 * self.humanization_level
        self.filler_probability = 0.05 * self.humanization_level
        self.contraction_probability = 0.6 * self.humanization_level
        self.abbreviation_probability = 0.1 * self.humanization_level
        self.punctuation_error_probability = 0.08 * self.humanization_level
        self.capitalization_error_probability = 0.08 * self.humanization_level
        self.self_correction_probability = 0.02 * self.humanization_level
        
    def humanize_text(self, text: str) -> str:
        """
        Apply various humanization techniques to make text appear more natural.
        
        Args:
            text (str): The AI-generated text to humanize
            
        Returns:
            str: Humanized text
        """
        # Split into sentences for easier processing
        sentences = self._split_into_sentences(text)
        
        # Process each sentence
        humanized_sentences = []
        for sentence in sentences:
            if not sentence.strip():
                humanized_sentences.append(sentence)
                continue
                
            # Apply transformations
            processed = sentence
            
            # Apply contractions
            processed = self._apply_contractions(processed)
            
            # Apply abbreviations
            processed = self._apply_abbreviations(processed)
            
            # Add typos
            processed = self._add_typos(processed)
            
            # Add filler words
            processed = self._add_filler_words(processed)
            
            # Modify punctuation
            processed = self._modify_punctuation(processed)
            
            # Modify capitalization
            processed = self._modify_capitalization(processed)
            
            humanized_sentences.append(processed)
        
        # Join sentences back together
        result = ' '.join(humanized_sentences)
        
        # Add self-corrections
        result = self._add_self_corrections(result)
        
        # Add double spaces occasionally
        result = self._add_double_spaces(result)
        
        return result
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        # Simple sentence splitting - not perfect but good enough for this purpose
        sentences = re.split(r'([.!?])\s+', text)
        
        # Recombine the sentences with their punctuation
        result = []
        i = 0
        while i < len(sentences):
            if i + 1 < len(sentences) and sentences[i+1] in ['.', '!', '?']:
                result.append(sentences[i] + sentences[i+1])
                i += 2
            else:
                result.append(sentences[i])
                i += 1
                
        return result
    
    def _add_typos(self, text: str) -> str:
        """Add realistic typos to text."""
        words = text.split()
        result = []
        
        for word in words:
            # Check if we should introduce a typo
            if random.random() < self.typo_probability:
                # Strip punctuation for matching
                clean_word = word.lower()
                for char in '.,!?;:()[]{}""\'':
                    clean_word = clean_word.replace(char, '')
                
                # Check if this word has common typos
                if clean_word in self.COMMON_TYPOS:
                    # Get the typo version
                    typo = random.choice(self.COMMON_TYPOS[clean_word])
                    
                    # Preserve capitalization
                    if word[0].isupper() and len(typo) > 0:
                        typo = typo[0].upper() + typo[1:]
                    
                    # Preserve punctuation
                    for i, char in enumerate(word):
                        if char in '.,!?;:()[]{}""\'':
                            if i == len(word) - 1:  # Punctuation at the end
                                typo += char
                            # Handle other positions if needed
                    
                    result.append(typo)
                else:
                    # For words not in our typo dictionary, occasionally transpose letters
                    if len(word) > 3 and random.random() < 0.5:
                        pos = random.randint(1, len(word) - 2)
                        word_list = list(word)
                        word_list[pos], word_list[pos + 1] = word_list[pos + 1], word_list[pos]
                        result.append(''.join(word_list))
                    else:
                        result.append(word)
            else:
                result.append(word)
        
        return ' '.join(result)
    
    def _add_filler_words(self, text: str) -> str:
        """Add filler words to text."""
        if random.random() < self.filler_probability:
            filler = random.choice(self.FILLER_WORDS)
            
            # Decide where to insert the filler
            if random.random() < 0.3 and not text.startswith(('I ', 'The ', 'This ', 'That ', 'It ')):
                # At the beginning
                if text[0].isupper():
                    filler = filler.capitalize()
                text = f"{filler}, {text[0].lower()}{text[1:]}"
            else:
                # In the middle - find a good spot after a comma or mid-sentence
                parts = text.split(', ')
                if len(parts) > 1 and random.random() < 0.7:
                    insert_idx = random.randint(1, len(parts) - 1)
                    parts[insert_idx] = f"{filler}, {parts[insert_idx]}"
                    text = ', '.join(parts)
                else:
                    words = text.split()
                    if len(words) > 4:
                        insert_idx = random.randint(2, len(words) - 2)
                        words.insert(insert_idx, filler)
                        text = ' '.join(words)
        
        return text
    
    def _apply_contractions(self, text: str) -> str:
        """Replace formal phrases with contractions."""
        for formal, contractions in self.CONTRACTIONS.items():
            if formal in text.lower() and random.random() < self.contraction_probability:
                contraction = random.choice(contractions)
                # Case-insensitive replacement while preserving case
                pattern = re.compile(re.escape(formal), re.IGNORECASE)
                
                def replace_with_case(match):
                    matched_text = match.group(0)
                    if matched_text[0].isupper():
                        return contraction[0].upper() + contraction[1:]
                    return contraction
                
                text = pattern.sub(replace_with_case, text)
        
        return text
    
    def _apply_abbreviations(self, text: str) -> str:
        """Replace words with their abbreviated forms."""
        words = text.split()
        result = []
        
        for word in words:
            # Clean word for matching
            clean_word = word.lower()
            for char in '.,!?;:()[]{}""\'':
                clean_word = clean_word.replace(char, '')
            
            # Check if we should abbreviate
            if clean_word in self.ABBREVIATIONS and random.random() < self.abbreviation_probability:
                abbr = random.choice(self.ABBREVIATIONS[clean_word])
                
                # Preserve capitalization
                if word[0].isupper() and len(abbr) > 0:
                    abbr = abbr[0].upper() + abbr[1:]
                
                # Preserve punctuation
                for i, char in enumerate(word):
                    if char in '.,!?;:()[]{}""\'':
                        if i == len(word) - 1:  # Punctuation at the end
                            abbr += char
                
                result.append(abbr)
            else:
                result.append(word)
        
        return ' '.join(result)
    
    def _modify_punctuation(self, text: str) -> str:
        """Modify punctuation to be more human-like."""
        if not text or random.random() >= self.punctuation_error_probability:
            return text
        
        # Different punctuation modifications
        mods = [
            # Missing end punctuation
            lambda t: t[:-1] if t and t[-1] in '.!?' else t,
            
            # Extra comma
            lambda t: self._insert_extra_comma(t),
            
            # Missing comma
            lambda t: t.replace(', ', ' ') if ', ' in t else t,
            
            # Multiple punctuation
            lambda t: t[:-1] + '..' if t and t[-1] == '.' else t,
            
            # Replace period with exclamation or question mark
            lambda t: t[:-1] + '!' if t and t[-1] == '.' and random.random() < 0.3 else t,
        ]
        
        # Apply a random modification
        return random.choice(mods)(text)
    
    def _insert_extra_comma(self, text: str) -> str:
        """Insert an extra comma in the text."""
        words = text.split()
        if len(words) < 4:
            return text
            
        # Find a position to insert a comma
        pos = random.randint(2, len(words) - 2)
        words[pos] = words[pos] + ','
        
        return ' '.join(words)
    
    def _modify_capitalization(self, text: str) -> str:
        """Modify capitalization to be more human-like."""
        if not text or random.random() >= self.capitalization_error_probability:
            return text
            
        # Different capitalization modifications
        mods = [
            # Lowercase first letter of sentence
            lambda t: t[0].lower() + t[1:] if t and t[0].isupper() else t,
            
            # Uppercase a random word for emphasis
            lambda t: self._emphasize_random_word(t),
            
            # Lowercase a proper noun
            lambda t: re.sub(r'\b([A-Z][a-z]+)\b', lambda m: m.group(0).lower(), t, count=1),
        ]
        
        # Apply a random modification
        return random.choice(mods)(text)
    
    def _emphasize_random_word(self, text: str) -> str:
        """Uppercase a random word for emphasis."""
        words = text.split()
        if len(words) < 3:
            return text
            
        # Find emphasis-worthy words (adjectives, nouns, etc.)
        emphasis_candidates = [i for i, word in enumerate(words) 
                              if len(word) > 3 and word.isalpha() and not word[0].isupper()]
        
        if not emphasis_candidates:
            return text
            
        # Select a random word to emphasize
        pos = random.choice(emphasis_candidates)
        words[pos] = words[pos].upper()
        
        return ' '.join(words)
    
    def _add_self_corrections(self, text: str) -> str:
        """Add self-corrections to the text."""
        if random.random() >= self.self_correction_probability:
            return text
            
        # Different self-correction patterns
        corrections = [
            # Word correction
            lambda t: self._insert_word_correction(t),
            
            # Asterisk correction
            lambda t: self._insert_asterisk_correction(t),
            
            # "I mean" correction
            lambda t: self._insert_i_mean_correction(t),
        ]
        
        # Apply a random correction
        return random.choice(corrections)(text)
    
    def _insert_word_correction(self, text: str) -> str:
        """Insert a word correction like 'word, I meant other_word'."""
        words = text.split()
        if len(words) < 5:
            return text
            
        # Find a position to insert a correction
        pos = random.randint(3, len(words) - 2)
        
        # Get a word to "correct"
        word = words[pos]
        
        # Create a correction
        if len(word) > 4:
            correction = f"{word}, I meant {word[0]}{word[2:]}"
            words[pos] = correction
        
        return ' '.join(words)
    
    def _insert_asterisk_correction(self, text: str) -> str:
        """Insert an asterisk correction like 'word *correction'."""
        words = text.split()
        if len(words) < 5:
            return text
            
        # Find a position to insert a correction
        pos = random.randint(3, len(words) - 2)
        
        # Get a word to "correct"
        word = words[pos]
        
        # Create a correction
        if len(word) > 4:
            # Swap two letters
            char_list = list(word)
            i = random.randint(1, len(char_list) - 2)
            char_list[i], char_list[i+1] = char_list[i+1], char_list[i]
            misspelled = ''.join(char_list)
            
            words[pos] = misspelled
            words.insert(pos + 1, f"*{word}")
        
        return ' '.join(words)
    
    def _insert_i_mean_correction(self, text: str) -> str:
        """Insert an 'I mean' correction."""
        sentences = self._split_into_sentences(text)
        if len(sentences) < 2:
            return text
            
        # Choose a random sentence to modify
        pos = random.randint(0, len(sentences) - 2)
        
        # Add the correction phrase
        correction_phrases = ["I mean", "wait", "actually", "or rather", "or I guess"]
        phrase = random.choice(correction_phrases)
        
        # Add to the beginning of the next sentence
        if sentences[pos + 1][0].isupper():
            sentences[pos + 1] = f"{phrase}, {sentences[pos + 1][0].lower()}{sentences[pos + 1][1:]}"
        else:
            sentences[pos + 1] = f"{phrase}, {sentences[pos + 1]}"
        
        return ' '.join(sentences)
    
    def _add_double_spaces(self, text: str) -> str:
        """Add occasional double spaces between words."""
        if random.random() < 0.2 * self.humanization_level:
            words = text.split()
            if len(words) < 5:
                return text
                
            # Find a position to insert a double space
            pos = random.randint(2, len(words) - 2)
            
            # Join with double space at that position
            result = ' '.join(words[:pos]) + '  ' + ' '.join(words[pos:])
            return result
        
        return text


def humanize_text(text: str, level: float = 0.5) -> str:
    """
    Convenience function to humanize text with a specified level.
    
    Args:
        text (str): The text to humanize
        level (float): Humanization level from 0.0 to 1.0
        
    Returns:
        str: Humanized text
    """
    humanizer = TextHumanizer(humanization_level=level)
    return humanizer.humanize_text(text)


if __name__ == "__main__":
    # Example usage
    test_text = """
    I believe that artificial intelligence will significantly impact society in the future. 
    It is important to consider both the positive and negative implications. 
    There are many benefits including increased efficiency and new capabilities, 
    but we must also be cautious about potential risks such as privacy concerns and job displacement.
    What do you think about this topic? I would be interested in hearing your perspective.
    """
    
    humanizer = TextHumanizer(humanization_level=0.7)
    humanized = humanizer.humanize_text(test_text)
    
    print("Original:")
    print(test_text)
    print("\nHumanized:")
    print(humanized) 