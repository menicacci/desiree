from transformers import AutoTokenizer, AutoModel
import torch
from sklearn.metrics.pairwise import cosine_similarity


def load(model_path: str):
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModel.from_pretrained(model_path)

    return tokenizer, model


def mean_pooling(model_output, attention_mask):
    token_embeddings = model_output[0]
    input_mask_expanded = attention_mask.unsqueeze(-1).expand(token_embeddings.size()).float()
    return torch.sum(token_embeddings * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)


def get_sentence_embedding(tokenizer, model, text):
    encoded_input = tokenizer(text, padding=True, truncation=True, return_tensors='pt')
    
    with torch.no_grad():
        model_output = model(**encoded_input)
    
    sentence_embedding = mean_pooling(model_output, encoded_input['attention_mask'])
    return sentence_embedding.numpy()


def compute_similarity(tokenizer, model, text_1, text_2):
    embedding1 = get_sentence_embedding(tokenizer, model, text_1)
    embedding2 = get_sentence_embedding(tokenizer, model, text_2)
    
    similarity = cosine_similarity(embedding1, embedding2)[0][0]
    return similarity
