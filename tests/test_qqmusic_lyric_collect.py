from pathlib import Path

from qqmusic_lyric_collect import (
    Track,
    artist_tokens,
    copy_lyrics,
    find_best_match,
    load_lyric_files,
    parse_lyric_file,
    parse_track_line,
)

DUMMY_SRT = "1\n00:00:01,000 --> 00:00:02,000\n有内容\n"


def test_artist_tokens_strips_parenthesized_reading():
    assert artist_tokens("立花理香 (たちばな りか)") == ["立花理香"]


def test_artist_tokens_strips_reading_but_keeps_every_artist():
    assert artist_tokens("澤野弘之 (さわの ひろゆき) _ naNami") == ["澤野弘之", "nanami"]


def test_match_accepts_track_artist_extending_lyric_artist():
    # 音频 1：raw 是「阿良良木健,洛天依Official」，缓存文件只挂了主唱「洛天依」
    track = Track(num=1, file_name="a.mp3", artist="阿良良木健,洛天依Official", title="绝体绝命", start=0.0)
    lyric = parse_lyric_file(Path("洛天依 - 绝体绝命-0.srt"))
    assert find_best_match(track, [lyric], "0") is lyric


def test_match_rejects_unrelated_artist():
    # 护栏：放开反向包含后，不相干的歌手依然不能命中
    track = Track(num=48, file_name="b.wav", artist="周华健", title="花簪 HANAKANZASHI", start=0.0)
    lyric = parse_lyric_file(Path("立花理香 - 花簪 HANAKANZASHI-0.srt"))
    assert find_best_match(track, [lyric], "0") is None


def test_parse_track_line_splits_on_last_dash_when_no_spaced_dash():
    # 音频 2：`-` 两侧无空格，且歌手本身就带 `-MSR` 后缀
    track = parse_track_line("音频 2 : 铁痕电台-MSR,SKa2or-洪炉.wav : 213.15")
    assert (track.artist, track.title) == ("铁痕电台-MSR,SKa2or", "洪炉")


def test_parse_track_line_prefers_spaced_dash():
    # 护栏：有 ` - ` 时仍按它切，贪婪匹配不能漏进来
    track = parse_track_line("音频 46 : 澤野弘之 (さわの ひろゆき) _ naNami - Next 2 U -eUC-.wav : 9733.7")
    assert (track.artist, track.title) == ("澤野弘之 (さわの ひろゆき) _ naNami", "Next 2 U -eUC-")


def test_translation_falls_back_to_non_empty_candidate(tmp_path):
    # 音频 1：得分最高的译文候选是 0 字节，应退而选有内容的那个
    cache = tmp_path / "cache"
    cache.mkdir()
    (cache / "阿良良木健,洛天依Official - 绝体绝命-0.srt").write_text(DUMMY_SRT, encoding="utf-8")
    (cache / "阿良良木健,洛天依Official - 绝体绝命-1.srt").write_text("", encoding="utf-8")
    (cache / "洛天依 - 绝体绝命-1.srt").write_text(DUMMY_SRT, encoding="utf-8")

    track = Track(num=1, file_name="a.mp3", artist="阿良良木健,洛天依Official", title="绝体绝命", start=0.0)
    copied, missing = copy_lyrics([track], load_lyric_files(cache), tmp_path / "out", dry_run=False)

    assert missing == []
    assert {kind: match.path.name for _, kind, match, _ in copied} == {
        "0": "阿良良木健,洛天依Official - 绝体绝命-0.srt",
        "1": "洛天依 - 绝体绝命-1.srt",
    }
