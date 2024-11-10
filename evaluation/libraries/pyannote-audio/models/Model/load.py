from pyannote.audio import Model, Inference
from scipy.spatial.distance import cdist
from pyannote.core import Segment

model = Model.from_pretrained("pyannote/wespeaker-voxceleb-resnet34-LM")

inference = Inference(model, window="whole")
embedding1 = inference("speaker1.wav")
embedding2 = inference("speaker2.wav")
# `embeddingX` is (1 x D) numpy array extracted from the file as a whole.

distance = cdist(embedding1, embedding2, metric="cosine")[0,0]
# `distance` is a `float` describing how dissimilar speakers 1 and 2 are.

# Extract embedding from an excerpt
inference = Inference(model, window="whole")
excerpt = Segment(13.37, 19.81)
embedding = inference.crop("audio.wav", excerpt)
# `embedding` is (1 x D) numpy array extracted from the file excerpt.

# Extract embeddings using a sliding window
inference = Inference(model, window="sliding",
                      duration=3.0, step=1.0)
embeddings = inference("audio.wav")
# `embeddings` is a (N x D) pyannote.core.SlidingWindowFeature
# `embeddings[i]` is the embedding of the ith position of the
# sliding window, i.e. from [i * step, i * step + duration].
