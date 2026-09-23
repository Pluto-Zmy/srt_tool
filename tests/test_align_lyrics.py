import json
from pathlib import Path

import pytest

from align_lyrics import (
    audio_key, choose_language, index_audio, main, make_parser, resolve_audio,
    run_alignment, validate_alignment,
)
from srt_tool import SubtitleCue, parse_srt, srt_tool


def segment(text, start, end, probability=0.9):
    return {"text": text, "start": start, "end": end,
            "words": [{"word": text, "start": start, "end": end, "probability": probability}]}


@pytest.mark.parametrize("name", ["2-1 - Artist - Song.wav", "[9]Artist - Song.mp3", "Artist-Song.FLAC"])
def test_numbered_and_different_audio_extensions(name):
    assert audio_key(name) == audio_key("Artist - Song.mp3")


def test_audio_search_excludes_apple_resource_forks_and_venv(tmp_path):
    (tmp_path / "._Artist-Song.wav").touch()
    (tmp_path / ".venv-align").mkdir()
    (tmp_path / ".venv-align" / "Artist-Song.wav").touch()
    nested = tmp_path / "nested"
    nested.mkdir()
    song = nested / "[1]Artist-Song.wav"
    song.touch()
    assert index_audio(tmp_path) == [song]
    assert resolve_audio("Artist - Song.mp3", index_audio(tmp_path)) == song


def test_ambiguous_match_never_selects_arbitrary_copy():
    with pytest.raises(ValueError, match="Ambiguous"):
        resolve_audio("Artist-Song.mp3", [Path("a/Artist-Song.mp3"), Path("b/Artist-Song.mp3")])


@pytest.mark.parametrize(("text", "language"), [("你好", "zh"), ("花簪の美しゅうて", "ja"),
                                               ("안녕하세요", "ko"), ("Hello", "en")])
def test_multilingual_defaults(text, language):
    assert choose_language(text) == language


def test_unknown_script_requires_explicit_language():
    with pytest.raises(ValueError, match="language"):
        choose_language("Раде Раде")


def test_alignment_can_correct_nonuniform_drift_without_rewriting_words():
    cues = [SubtitleCue(10000, 12000, ["你好"]), SubtitleCue(20000, 24000, ["世界"])]
    result = {"segments": [segment("你好", 1, 3), segment("世界", 5, 8, 0.2)]}
    aligned, rows = validate_alignment(cues, ["你好", "世界"], result, 10)
    assert [(cue.start_ms, cue.end_ms, cue.lines) for cue in aligned] == [
        (1000, 3000, ["你好"]), (5000, 8000, ["世界"])]
    assert cues[0].start_ms == 10000
    assert "large_timestamp_change" in rows[0]["review_reasons"]
    assert "low_word_probability" in rows[1]["review_reasons"]


@pytest.mark.parametrize("segments", [[], [segment("wrong", 1, 2)], [segment("hello", 1, 1)],
    [segment("hello", -1, 1)], [segment("hello", 1, 11)], [segment("hello", float("nan"), 2)]])
def test_bad_alignment_is_not_applied(segments):
    with pytest.raises(ValueError):
        validate_alignment([SubtitleCue(0, 2000, ["hello"])], ["hello"], {"segments": segments}, 10)


def test_overlapping_lines_are_rejected_instead_of_clamped():
    with pytest.raises(ValueError, match="overlapping"):
        validate_alignment([SubtitleCue(0, 1, ["a"]), SubtitleCue(2, 3, ["b"])], ["a", "b"],
                           {"segments": [segment("a", 1, 3), segment("b", 2, 4)]}, 10)


def test_repeated_chorus_lines_keep_sequence():
    cues = [SubtitleCue(1000, 2000, ["hello"]), SubtitleCue(3000, 4000, ["hello"])]
    aligned, _ = validate_alignment(cues, ["hello", "hello"],
                                   {"segments": [segment("hello", 5, 7), segment("hello", 20, 22)]}, 25)
    assert [cue.start_ms for cue in aligned] == [5000, 20000]


def test_partial_word_failure_is_flagged():
    item = segment("hello world", 1, 3)
    item["words"].append({"word": "world", "start": 3, "end": 3})
    _, rows = validate_alignment([SubtitleCue(1000, 3000, ["hello world"])], ["hello world"],
                                {"segments": [item]}, 10)
    assert "unaligned_word" in rows[0]["review_reasons"]
    assert "missing_word_probability" in rows[0]["review_reasons"]


@pytest.fixture
def project(tmp_path):
    (tmp_path / "srts").mkdir()
    (tmp_path / "audio").mkdir()
    (tmp_path / "audio" / "[1]Artist-Song.mp3").touch()
    (tmp_path / "raw.txt").write_text("音频 1 : Artist-Song.mp3 : 100\n", encoding="utf-8")
    (tmp_path / "configV2.json").write_text(json.dumps({"srt_list": [
        {"file_name": "1.srt", "time_offset": "100"}]}), encoding="utf-8")
    (tmp_path / "srts" / "1.srt").write_text("1\n00:00:10,000 --> 00:00:12,000\nHello world\n", encoding="utf-8")
    (tmp_path / "srts" / "1_ts.srt").write_text("1\n00:00:10,000 --> 00:00:12,000\n你好世界\n", encoding="utf-8")
    return ["--config", str(tmp_path / "configV2.json"), "--raw", str(tmp_path / "raw.txt"),
            "--audio-root", str(tmp_path / "audio"), "--output-dir", str(tmp_path / "out")]


class FakeAligner:
    calls = []

    def __init__(self, *args):
        pass

    def align(self, path, texts, language):
        self.calls.append((path, texts, language))
        return {"segments": [segment(" Hello world", 2, 4)]}, 20


def test_translation_follows_original_and_global_offset_is_applied_once(project, tmp_path):
    original = (tmp_path / "srts" / "1.srt").read_bytes()
    report = run_alignment(make_parser().parse_args(project), FakeAligner)
    assert report["tracks"][0]["status"] == "needs_review"
    assert FakeAligner.calls[-1][1:] == (["Hello world"], "en")
    out = tmp_path / "out"
    cues = parse_srt(out / "1.srt")
    assert cues == [SubtitleCue(2000, 4000, ["Hello world", "你好世界"])]
    assert not (out / "1_ts.srt").exists()
    assert (tmp_path / "srts" / "1.srt").read_bytes() == original
    srt_tool(out / "configV2.json", out / "preview.srt", out)
    assert parse_srt(out / "preview.srt")[0] == SubtitleCue(102000, 104000, ["Hello world", "你好世界"])


def test_dry_run_does_not_load_model(project, tmp_path):
    def forbidden(*args):
        pytest.fail("dry-run loaded a model")
    args = make_parser().parse_args(project + ["--dry-run"])
    assert run_alignment(args, forbidden)["summary"] == {"ready": 1}
    assert not (tmp_path / "out" / "1.srt").exists()


def test_failed_alignment_does_not_export_old_timing(project, tmp_path):
    class Broken(FakeAligner):
        def align(self, *args):
            return {"segments": []}, 20
    report = run_alignment(make_parser().parse_args(project), Broken)
    assert report["summary"] == {"failed": 1}
    assert not (tmp_path / "out" / "1.srt").exists()
    assert json.loads((tmp_path / "out" / "configV2.json").read_text())["srt_list"] == []
    assert (tmp_path / "out" / "1.alignment.json").exists()


def test_a_failed_song_does_not_stop_later_songs(project, tmp_path):
    config = tmp_path / "configV2.json"
    data = json.loads(config.read_text())
    data["srt_list"].append({"file_name": "2.srt", "time_offset": 200})
    config.write_text(json.dumps(data))
    (tmp_path / "srts" / "2.srt").write_bytes((tmp_path / "srts" / "1.srt").read_bytes())
    with (tmp_path / "raw.txt").open("a", encoding="utf-8") as file:
        file.write("音频 2 : Artist-Song.mp3 : 200\n")

    class OnceBroken(FakeAligner):
        count = 0

        def align(self, *args):
            self.count += 1
            if self.count == 1:
                raise RuntimeError("inference failed")
            return super().align(*args)

    report = run_alignment(make_parser().parse_args(project), OnceBroken)
    assert [job["status"] for job in report["tracks"]] == ["failed", "needs_review"]
    assert not (tmp_path / "out" / "1.srt").exists()
    assert (tmp_path / "out" / "2.srt").exists()


def test_refuses_overwriting_source_or_stale_outputs(project, tmp_path):
    with pytest.raises(ValueError, match="differ"):
        run_alignment(make_parser().parse_args(project + ["--output-dir", str(tmp_path / "srts")]))
    (tmp_path / "out").mkdir()
    (tmp_path / "out" / "old.srt").touch()
    with pytest.raises(ValueError, match="empty"):
        run_alignment(make_parser().parse_args(project))


def test_overrides_resolve_relative_to_override_file(project, tmp_path):
    (tmp_path / "options").mkdir()
    override = tmp_path / "options" / "overrides.json"
    override.write_text(json.dumps({"1.srt": {"audio_file": "../audio/[1]Artist-Song.mp3", "language": "bg"}}))
    args = make_parser().parse_args(project + ["--dry-run", "--overrides", str(override)])
    report = run_alignment(args)
    assert report["tracks"][0]["language"] == "bg"


def test_unknown_track_fails_before_model_load(project):
    with pytest.raises(ValueError, match="Unknown"):
        run_alignment(make_parser().parse_args(project + ["--tracks", "999"]))


def test_backend_startup_error_is_reported(project, tmp_path):
    def unavailable(*args):
        raise RuntimeError("dependency missing")
    with pytest.raises(RuntimeError, match="dependency missing"):
        run_alignment(make_parser().parse_args(project), unavailable)
    report = json.loads((tmp_path / "out" / "alignment_report.json").read_text(encoding="utf-8"))
    assert "dependency missing" in report["fatal_error"]


def test_invalid_thresholds_rejected(project):
    with pytest.raises(SystemExit):
        main(project + ["--min-probability", "nan"])


def test_split_chinese_cues_receive_independent_audio_timings(project, tmp_path):
    path = tmp_path / "srts" / "1.srt"
    original = "1\n00:00:10,000 --> 00:00:12,000\n天空中的星星啊 照亮回家的路啊\n"
    path.write_text(original, encoding="utf-8")

    class ChineseAligner(FakeAligner):
        def align(self, audio, texts, language):
            assert language == "zh"
            assert texts == ["天空中的星星啊", "照亮回家的路啊"]
            return {"segments": [segment(texts[0], 2, 2.5), segment(texts[1], 7, 9)]}, 20

    report = run_alignment(make_parser().parse_args(project), ChineseAligner)
    job = report["tracks"][0]
    assert (job["source_cue_count"], job["cue_count"], job["split_source_cues"]) == (1, 2, 1)
    assert [row["source_line"] for row in job["lines"]] == [1, 1]
    assert all(row["split_from_source"] for row in job["lines"])
    assert all("shared_translation_after_split" in row["review_reasons"] for row in job["lines"])
    cues = parse_srt(tmp_path / "out" / "1.srt")
    assert cues == [SubtitleCue(2000, 2500, ["天空中的星星啊", "你好世界"]),
                    SubtitleCue(7000, 9000, ["照亮回家的路啊", "你好世界"])]
    assert path.read_text(encoding="utf-8") == original
    srt_tool(tmp_path / "out" / "configV2.json", tmp_path / "preview.srt", tmp_path / "out")
    assert [(cue.start_ms, cue.end_ms) for cue in parse_srt(tmp_path / "preview.srt")] == [
        (102000, 102500), (107000, 109000)]


@pytest.mark.parametrize("disabled, expected_count", [(False, 2), (True, 1)])
def test_dry_run_reports_split_counts_and_opt_out(project, tmp_path, disabled, expected_count):
    (tmp_path / "srts" / "1.srt").write_text(
        "1\n00:00:10,000 --> 00:00:12,000\n天空中的星星啊 照亮回家的路啊\n", encoding="utf-8")
    options = ["--no-split-long-lyrics"] if disabled else []
    args = make_parser().parse_args(project + ["--dry-run"] + options)
    report = run_alignment(args)
    assert report["tracks"][0]["cue_count"] == expected_count
    assert report["split_long_chinese_lyrics"] == (not disabled)


def test_split_shortening_is_not_reported_as_large_timing_drift():
    sources = [SubtitleCue(0, 30000, ["hello"]), SubtitleCue(0, 30000, ["world"])]
    result = {"segments": [segment("hello", 2, 5), segment("world", 20, 25)]}
    _, rows = validate_alignment(sources, ["hello", "world"], result, 40, split_flags=[True, True])
    assert all(not row["review_reasons"] for row in rows)
    result["segments"][1] = segment("world", 32, 38)
    _, rows = validate_alignment(sources, ["hello", "world"], result, 40, split_flags=[True, True])
    assert rows[1]["review_reasons"] == ["large_timestamp_change"]
