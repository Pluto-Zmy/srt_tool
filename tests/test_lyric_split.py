import pytest

from lyric_split import count_han, split_long_lyric_line
from align_lyrics import prepare_alignment
from srt_tool import SubtitleCue


@pytest.mark.parametrize("line", [
    "春风明月 照亮回家路",  # exactly 9 Han characters
    "你好 世界", "这是一句没有空格但是超过十二个汉字的长歌词",
    "  这是一句只有首尾空格但没有句间空格的长歌词  ",
    "你好，world! 123 世界。", "Never split these English words by their length", "",
])
def test_lines_not_meeting_both_conditions_are_unchanged(line):
    assert split_long_lyric_line(line) == [line]


@pytest.mark.parametrize("line, expected", [
    ("天空的星星 照亮回家路", ["天空的星星", "照亮回家路"]),  # exactly 10
    ("没有人曾体会 照亮回家路", ["没有人曾体会", "照亮回家路"]),  # 11
    ("没有人曾体会 没有人曾了解", ["没有人曾体会", "没有人曾了解"]),  # 12
])
def test_ten_or_more_han_characters_trigger_split(line, expected):
    assert split_long_lyric_line(line) == expected


def test_punctuation_and_digits_do_not_push_nine_han_to_threshold():
    line = "春风明月！ ABC123 照亮回家路。"
    assert count_han(line) == 9
    assert split_long_lyric_line(line) == [line]


def test_pack_whole_phrases_and_preserve_internal_spacing():
    assert split_long_lyric_line("人们路过  笑过 骂过 不留一声抱歉") == [
        "人们路过  笑过 骂过", "不留一声抱歉"]


def test_han_count_excludes_punctuation_digits_and_latin_and_covers_extensions():
    assert count_han("中文，繁體！ABC 123\t\U00020000\uf900") == 6


@pytest.mark.parametrize("space", [" ", "   ", "\t", "\u3000", "\u00a0"])
def test_different_phrase_whitespace(space):
    assert split_long_lyric_line("天空中的星星啊" + space + "照亮回家的路啊") == [
        "天空中的星星啊", "照亮回家的路啊"]


def test_never_cut_inside_a_long_phrase_and_preserve_all_characters():
    long_phrase = "这是一句没有空格但是超过十二个汉字的长歌词"
    assert split_long_lyric_line(long_phrase + " 归去") == [long_phrase, "归去"]


def test_multiple_groups_and_reapplying_split_is_stable():
    line = "春风明月 夜雨星光 山川湖海 天涯故乡 你我同行 梦中回望 不负韶光"
    groups = split_long_lyric_line(line)
    assert groups == ["春风明月 夜雨星光", "山川湖海 天涯故乡", "你我同行 梦中回望", "不负韶光"]
    assert [part for group in groups for part in split_long_lyric_line(group)] == groups


@pytest.mark.parametrize("language", ["ja", "en", "ko"])
def test_non_chinese_tracks_are_not_split(language):
    cue = SubtitleCue(0, 10000, ["天空中的星星啊 照亮回家的路啊"])
    cues, texts, parents = prepare_alignment([cue], language)
    assert cues == [cue]
    assert texts == [cue.lines[0]]
    assert parents == [0]


def test_multiple_source_lines_keep_their_order_and_source_ownership():
    original = SubtitleCue(0, 10000, ["天空中的星星啊 照亮回家的路啊", "再见"])
    cues, texts, parents = prepare_alignment([original], "zh")
    assert texts == ["天空中的星星啊", "照亮回家的路啊", "再见"]
    assert parents == [0, 0, 0]
    assert [cue.lines for cue in cues] == [[text] for text in texts]
    assert original.lines == ["天空中的星星啊 照亮回家的路啊", "再见"]
