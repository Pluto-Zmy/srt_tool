"""Split long Chinese lyric lines only at existing phrase whitespace."""

import re
import unicodedata


SPLIT_HAN_THRESHOLD = 10


def count_han(text: str) -> int:
    """Count unified/compatibility Han characters, including extension blocks."""
    return sum(unicodedata.name(char, "").startswith(
        ("CJK UNIFIED IDEOGRAPH-", "CJK COMPATIBILITY IDEOGRAPH-")
    ) for char in text)


def split_long_lyric_line(line: str) -> list[str]:
    """Split spaced lines with >=10 Han characters; never cut inside a phrase.

    Combined groups stay below the threshold. A single phrase may exceed it.

    Untouched lines and whitespace inside retained groups are preserved verbatim.
    Whitespace used as a split boundary is removed.
    """
    phrases = list(re.finditer(r"\S+", line))
    if len(phrases) < 2 or count_han(line) < SPLIT_HAN_THRESHOLD:
        return [line]

    groups = []
    start = phrases[0].start()
    end = phrases[0].end()
    size = count_han(phrases[0].group())
    for phrase in phrases[1:]:
        next_size = count_han(phrase.group())
        if size + next_size >= SPLIT_HAN_THRESHOLD:
            groups.append(line[start:end])
            start = phrase.start()
            size = next_size
        else:
            size += next_size
        end = phrase.end()
    groups.append(line[start:end])
    return groups
