"""How much evidence an item statistic needs before it says anything (learning-telemetry ADR-03, A-05).

A p-value from three answers is noise: below `MIN_OBSERVATIONS` graded answers a question reports "chưa đủ dữ liệu"
and no number at all. The key audit waits for the same amount of evidence before it doubts an answer key.
"""
MIN_OBSERVATIONS = 10


def enough(observations: int) -> bool:
    return observations >= MIN_OBSERVATIONS
