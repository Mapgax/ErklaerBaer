from pathlib import Path

import pytest
from PIL import Image

from erklaerbaer.asset_design import (
    _validate_bfl_url,
    generate_mascot_concept,
    prompt_for_pose,
)
from erklaerbaer.errors import ExternalServiceError

from .factories import make_settings


def _reference(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGBA", (64, 96), (130, 90, 50, 255)).save(path)


def test_mascot_dry_run_reserves_no_credits(tmp_path, monkeypatch):
    settings = make_settings(tmp_path)
    reference = tmp_path / "reference.png"
    _reference(reference)
    monkeypatch.setenv("DRY_RUN", "true")

    result = generate_mascot_concept(settings, "neutral", reference=reference)

    assert result.dry_run
    assert result.reserved_credits == 20
    assert not result.output.exists()
    assert not (tmp_path / "catalog" / "usage.json").exists()


def test_prompt_requires_complete_readable_anatomy():
    prompt = prompt_for_pose("lifting-stone")
    assert "Each complete\narm" in prompt
    assert "exactly two ears" in prompt
    assert "Both legs" in prompt
    assert "only the bear and one bare stone" in prompt
    assert "No written words" in prompt


def test_bfl_urls_reject_non_bfl_hosts():
    with pytest.raises(ExternalServiceError):
        _validate_bfl_url("https://example.com/result.png", purpose="download")
    with pytest.raises(ExternalServiceError):
        _validate_bfl_url(
            "https://delivery.bfl.ai/v1/submit", purpose="submission", allowed_api_only=True
        )
