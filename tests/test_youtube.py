from erklaerbaer.models import Language
from erklaerbaer.youtube import content_marker, update_env_file

from .factories import sample_storyboard


def test_content_marker_is_deterministic_and_language_specific():
    german = content_marker(sample_storyboard(Language.GERMAN))
    dutch = content_marker(sample_storyboard(Language.DUTCH))
    assert german == content_marker(sample_storyboard(Language.GERMAN))
    assert german != dutch
    assert german.startswith("[ERKLAERBAER:")


def test_setup_updates_env_without_removing_other_values(tmp_path):
    path = tmp_path / ".env"
    path.write_text("UNCHANGED=yes\nSECRET=old\n", encoding="utf-8")
    update_env_file(path, {"SECRET": "new-value", "GENERATED": "abc"})
    text = path.read_text(encoding="utf-8")
    assert "UNCHANGED=yes" in text
    assert 'SECRET="new-value"' in text
    assert 'GENERATED="abc"' in text


def test_description_states_the_voice_disclosure_exactly_once():
    from erklaerbaer.youtube import build_description

    board = sample_storyboard(Language.DUTCH)
    board.youtube.description = "Een uitleg. De stem is gemaakt met tekst-naar-spraak."
    disclosure = "De stem in deze video is gemaakt met tekst-naar-spraak."
    text = build_description(board, disclosure, "[MARKER]", "tekst-naar-spraak")
    assert text.lower().count("tekst-naar-spraak") == 1
    assert text.endswith("[MARKER]")

    board.youtube.description = "Een uitleg van de waargenomen verschijnselen."
    text = build_description(board, disclosure, "[MARKER]", "tekst-naar-spraak")
    assert disclosure in text
    assert text.lower().count("tekst-naar-spraak") == 1
