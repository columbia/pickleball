from abc import ABC, abstractmethod
import typing

class DataPoint:
    pass

DT = typing.TypeVar("DT", bound=DataPoint)

class Sentence(DataPoint):
    pass

class Model(typing.Generic[DT], ABC):
    pass

class ReduceTransformerVocabMixin(ABC):
    pass

class Classifier(Model[DT], typing.Generic[DT], ReduceTransformerVocabMixin, ABC):
    pass

class SequenceTagger(Classifier[Sentence]):
    pass


