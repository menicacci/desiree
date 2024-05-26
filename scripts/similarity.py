from scripts import embedding
from scripts.utils import detect_number, remove_items, find_substrings
import difflib

class Similarity:

    def __init__(self, model_path='sentence-transformers/all-MiniLM-L6-v2', text_threshold=0.8, num_threshold=0.75):
        self.tokenizer, self.model = embedding.load(model_path)
        self.text_threshold = text_threshold
        self.num_threshold = num_threshold

    
    def get_similarity(self, str_1: str, str_2: str) -> float:
        if detect_number(str_1) and detect_number(str_2):
            return difflib.SequenceMatcher(None, str_1.lower(), str_2.lower()).ratio() - self.num_threshold
        else:
            return embedding.compute_similarity(
                tokenizer=self.tokenizer,
                model=self.model,
                text_1=str_1,
                text_2=str_2
            ) - self.text_threshold
        

    def check_equality(self, str_1: str, str_2: str) -> bool:
        return self.get_similarity(str_1, str_2) > 0
    

    def find_similar_strings(self, input_list: list, search_list):
        similar_strings = {input_string: [] for input_string in input_list}

        found = set()
        for input_string in input_list:
            for search_string  in search_list:
                if self.check_equality(input_string, search_string):
                    similar_strings[input_string].append(search_string)
                    found.add(input_string)

        for input_string in found:
            similar_strings[input_string] = [max(similar_strings[input_string], key=lambda x: self.get_similarity(input_string, x))]
        
        input_list = remove_items(input_list, found)
        found.clear()

        for input_string in input_list:
            similar_substrings = find_substrings(input_string, search_list, self.get_similarity)    
            if len(similar_strings) > 0:
                found.add(input_string)
                similar_strings[input_string] = similar_substrings

        input_list = remove_items(input_list, found)
        found.clear()

        for search_string in search_list:
            similar_substrings = find_substrings(search_string, input_list, self.get_similarity)
            for string in similar_substrings:
                found.add(string)
                similar_strings[string] = [search_string]

        return similar_strings                       
