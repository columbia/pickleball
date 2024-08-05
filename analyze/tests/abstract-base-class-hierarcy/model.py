"""
SequenceTagger:
- Allowed globals: {SequenceTagger, Sentence, DataPoint}
- Allowed callables: {}
"""

from abc import ABC, abstractmethod
import typing

class DataPoint:
    pass


class Sentence(DataPoint):

    def __init__(self, words: str):
        self.words = words


DT = typing.TypeVar("DT", bound=DataPoint)


class Model(typing.Generic[DT], ABC):

    model_card = None

    @abstractmethod
    def forward_loss(self, data_points: typing.List[DT]) -> int:
        raise NotImplementedError

    def set_model_card(self, card: DataPoint):
        self.model_card = card


class Classifier(Model[DT], typing.Generic[DT], ABC):

    pass


class SequenceTagger(Classifier[Sentence]):

    def forward_loss(self, sentences: typing.List[Sentence]) -> int:
        return len(sentences)
