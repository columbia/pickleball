from flair.data import Sentence
from flair.models import SequenceTagger

tagger = SequenceTagger.load("flair/chunk-english")
sentence = Sentence("The happy man has been eating at the diner")

tagger.predict(sentence)

print(sentence)

for entity in sentence.get_spans('np'):
    print(entity)
