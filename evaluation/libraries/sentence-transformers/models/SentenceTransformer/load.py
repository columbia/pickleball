import logging
import sys

from sentence_transformers import SentenceTransformer

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

sentences = ["안녕하세요?", "한국어 문장 임베딩을 위한 버트 모델입니다."]

model = SentenceTransformer('./ko-sroberta-multitask/')
embeddings = model.encode(sentences)
print(embeddings)
