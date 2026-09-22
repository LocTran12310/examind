"""Failures inside the pipeline. IngestError carries a message fit for the teacher; the others are raised by adapters
and turned into IngestError (or a fallback) by the stages."""


class IngestError(Exception):
    """A failure with a message fit for the teacher."""


class DocxError(Exception):
    pass


class OcrError(Exception):
    pass


class LlmError(Exception):
    pass
