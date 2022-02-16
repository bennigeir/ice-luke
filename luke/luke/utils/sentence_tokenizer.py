from typing import List, Tuple
import pkg_resources


class SentenceTokenizer:
    """ Base class for all sentence tokenizers in this project."""

    def span_tokenize(self, text: str) -> List[Tuple[int, int]]:
        raise NotImplementedError

    @classmethod
    def from_name(cls, name: str):

        if name == "opennlp":
            return OpenNLPSentenceTokenizer()
        else:
            # return ICUSentenceTokenizer(name)
            return ICUSentenceTokenizer("en")


class ICUSentenceTokenizer:
    """ Segment text to sentences. """

    def __init__(self, locale="en"):
        self.locale = locale
        self.breaker = None

    def span_tokenize(self, text: str):
        from icu import Locale, BreakIterator

        locale="en"

        if self.breaker is None:
            if locale in {"en", "de", "es", "it", "pt"}:
                locale += "@ss=standard"
            self.locale = Locale(locale)
            self.breaker = BreakIterator.createSentenceInstance(self.locale)

        self.breaker.setText(text)
        start_idx = 0
        spans = []
        for end_idx in self.breaker:
            spans.append((start_idx, end_idx))
            start_idx = end_idx
        return spans
    


        text = "".join(c if c <= "\uFFFF" else " " for c in text)


class OpenNLPSentenceTokenizer(SentenceTokenizer):
    _java_initialized = False

    def __init__(self):
        self._initialized = False

    def __reduce__(self):
        return self.__class__, tuple()

    def initialize(self):
        # we need to delay the initialization of Java in order for this class to
        # properly work with multiprocessing
        if not OpenNLPSentenceTokenizer._java_initialized:
            import jnius_config

            jnius_config.add_options("-Xrs")
            jnius_config.set_classpath(pkg_resources.resource_filename(__name__, "/resources/opennlp-tools-1.5.3.jar"))
            OpenNLPSentenceTokenizer._java_initialized = True

        from jnius import autoclass

        File = autoclass("java.io.File")
        SentenceModel = autoclass("opennlp.tools.sentdetect.SentenceModel")
        SentenceDetectorME = autoclass("opennlp.tools.sentdetect.SentenceDetectorME")

        sentence_model_file = pkg_resources.resource_filename(__name__, "resources/en-sent.bin")
        sentence_model = SentenceModel(File(sentence_model_file))
        self._tokenizer = SentenceDetectorME(sentence_model)

        self._initialized = True

    def span_tokenize(self, text: str) -> List[Tuple[int, int]]:
        if not self._initialized:
            self.initialize()

        # replace non-BMP characters with a whitespace
        # (https://stackoverflow.com/questions/36283818/remove-characters-outside-of-the-bmp-emojis-in-python-3)
        text = "".join(c if c <= "\uFFFF" else " " for c in text)

        return [(span.getStart(), span.getEnd()) for span in self._tokenizer.sentPosDetect(text)]
