import numpy as np
from PIL import Image

from erklaerbaer.rive_assets import _border_connected, prepare_rive_assets

from .factories import make_settings


def test_border_connected_does_not_enter_enclosed_foreground():
    eligible = np.ones((7, 7), dtype=bool)
    eligible[2:5, 2:5] = False
    eligible[3, 3] = True

    connected = _border_connected(eligible)

    assert connected[0, 0]
    assert not connected[3, 3]


def test_prepare_rive_assets_dry_run_requires_owner_approval(tmp_path, monkeypatch):
    settings = make_settings(tmp_path)
    version = settings.section("asset_design")["concept_version"]
    concept_dir = tmp_path / "assets" / "mascot" / "concepts" / str(version)
    concept_dir.mkdir(parents=True)
    outputs = {}
    for key, filename in {
        "neutral": "neutral.png",
        "lifting-stone-r3": "lifting-stone-r3.png",
        "explaining": "explaining.png",
    }.items():
        Image.new("RGB", (64, 96), (220, 215, 205)).save(concept_dir / filename)
        outputs[key] = {"review_status": "approved-by-owner"}
    (concept_dir / "manifest.json").write_text(
        __import__("json").dumps({"outputs": outputs}), encoding="utf-8"
    )
    monkeypatch.setenv("DRY_RUN", "true")

    result = prepare_rive_assets(settings)

    assert result.dry_run
    assert len(result.outputs) == 3
    assert not result.outputs[0].exists()


def test_rive_contract_uses_stable_runtime_names():
    import json
    from pathlib import Path

    contract_path = Path(__file__).parents[1] / "assets" / "mascot" / "rig" / "rig-contract.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))

    assert contract["artboard"]["name"] == "ErklaerBaer_Mascot"
    assert contract["state_machine"]["name"] == "State Machine 1"
    assert contract["state_machine"]["view_model"] == "ViewModel1"
    assert contract["state_machine"]["production_property"] == "action"
    assert contract["state_machine"]["range"] == [0, 5]
    assert {action["semantic_name"] for action in contract["actions"].values()} == {
        "neutral",
        "lift",
        "explain",
        "think",
        "surprise",
        "aha",
    }
