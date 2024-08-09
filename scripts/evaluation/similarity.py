from scripts import utils
from scripts.evaluation import embedding


class Similarity:

    def __init__(self, use_embeddings=True):
        self.use_embeddings = use_embeddings

        if self.use_embeddings:
            self.tokenizer, self.model = embedding.load('sentence-transformers/all-MiniLM-L6-v2')
        
        self.text_threshold = 0.75
        self.number_threshold = 0.8 if self.use_embeddings else 0.6

    
    def get_similarity(self, str_1: str, str_2: str) -> float:
        if utils.detect_number(str_1) and utils.detect_number(str_2):
            return utils.fuzzy_string_similarity(str_1, str_2) - self.number_threshold
        else:
            if self.use_embeddings:
                similarity_score = embedding.compute_similarity(
                    tokenizer=self.tokenizer,
                    model=self.model,
                    text_1=str_1,
                    text_2=str_2)
            else:
                similarity_score = utils.fuzzy_string_similarity(str_1, str_2)

            return similarity_score - self.text_threshold


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
        
        input_list = utils.remove_items(input_list, found)
        found.clear()

        for input_string in input_list:
            similar_substrings = utils.find_substrings(input_string, search_list, self.get_similarity)    
            if len(similar_strings) > 0:
                found.add(input_string)
                similar_strings[input_string] = similar_substrings

        input_list = utils.remove_items(input_list, found)
        found.clear()

        for search_string in search_list:
            similar_substrings = utils.find_substrings(search_string, input_list, self.get_similarity)
            for string in similar_substrings:
                found.add(string)
                similar_strings[string] = [search_string]

        return similar_strings                       
