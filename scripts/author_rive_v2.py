"""One-time authoring recipe; reads approved v1 and writes only the v2 duplicate."""

import json
from pathlib import Path

from rive_mcp import call, connect

LOG = Path("build/rive-mcp")


def checked(name, args):
    result = call(name, args)
    text = result["content"][0]["text"]
    payload = json.loads(text)
    if not payload.get("success") or payload.get("errors"):
        raise RuntimeError(text)
    return payload


def main():
    connect()
    assert checked("session_info", {})["activeFileId"] == 2561970
    for pose, image in [("surprise", "0-621"), ("aha", "0-622")]:
        log = LOG / f"mesh-{pose}.json"
        if log.exists():
            continue
        mesh = checked(
            "mesh_rigging_tool",
            {
                "command": "generateMesh",
                "data": {"imageId": image, "trace": True, "subdivisions": 1, "detail": 0.5},
            },
        )
        log.write_text(json.dumps(mesh))
        for command, data in [
            ("bindBones", {"targetId": mesh["meshId"], "boneIds": ["0-259", "0-260", "0-261"]}),
            ("autoWeight", {"targetId": mesh["meshId"], "blend": 0.4, "maxInfluences": 2}),
        ]:
            checked("mesh_rigging_tool", {"command": command, "data": data})
    current = checked("animation_editor", {"command": "listLinearAnimations"})
    by_name = {a["name"]: a["id"] for a in current["linearAnimations"]}
    specs = [
        ("think", 2.5, "0-620"),
        ("surprise", 1.5, "0-621"),
        ("aha", 1.8, "0-622"),
        ("explain", 2.0, "0-27"),
        ("lift", 2.0, "0-28"),
    ]
    for action, duration, _pose in specs:
        name = f"{action}_v2"
        if name not in by_name:
            created = checked(
                "animation_editor",
                {
                    "command": "createLinearAnimations",
                    "data": {"linearAnimations": [{"name": name, "duration": duration}]},
                },
            )
            print(json.dumps(created))
    current = checked("animation_editor", {"command": "listLinearAnimations"})
    by_name = {a["name"]: a["id"] for a in current["linearAnimations"]}
    (LOG / "v2-timelines.json").write_text(json.dumps(by_name, indent=2))
    for action, duration, pose in specs:
        animation = by_name[f"{action}_v2"]
        end = round(duration * 60)
        checked(
            "set_property_values", {"propertyValues": {animation: {"56": 60, "59": 0, "57": end}}}
        )
        keys = []

        def key(obj, prop, frame, value, target=keys):
            target.append(
                {
                    "objectId": obj,
                    "propertyKey": prop,
                    "frame": frame,
                    "value": value,
                    "interpolationType": "hold" if isinstance(value, str) else "cubic",
                    **(
                        {}
                        if isinstance(value, str)
                        else {"cubicParams": {"x1": 0.42, "y1": 0, "x2": 0.58, "y2": 1}}
                    ),
                }
            )

        key("0-30", 296, 0, pose)
        for prop, value in [(13, 600), (14, 800), (15, 0), (16, 100), (17, 100)]:
            key("0-31", prop, 0, value)
            key("0-31", prop, end, value)
        key("0-415", 18, 0, 0)
        key("0-415", 18, end, 0)
        head = -0.10641551025538434
        key("0-261", 15, 0, head)
        if action == "think":
            for f, v in [(36, 1.8), (end, 1.8)]:
                key("0-261", 15, f, v)
        elif action == "surprise":
            for f, v in [(12, -1.8), (48, -1.8), (end, head)]:
                key("0-261", 15, f, v)
        elif action == "aha":
            for f, v in [(21, 2.0), (45, head), (72, head), (end, head)]:
                key("0-261", 15, f, v)
        else:
            key("0-261", 15, end, head)
            key("0-31", 15, 24, -0.6 if action == "explain" else 0.3)
            key("0-31", 15, 65, 0)
        result = checked(
            "animation_editor",
            {"command": "modifyKeyFrames", "data": {"animationId": animation, "add": keys}},
        )
        (LOG / f"authored-{action}.json").write_text(json.dumps(result, indent=2))
        print("Authored", action)
    # Embed all image assets so runtime baking has no CDN dependency.
    ids = ["0-17", "0-420", "0-422", "0-617", "0-618", "0-619"]
    checked("set_property_values", {"propertyValues": {i: {"358": 0, "801": True} for i in ids}})
    # The editor can simulate an unbound view model, but Full runtime optimization removes it.
    checked(
        "viewmodel_editor",
        {
            "command": "bindViewModelToArtboard",
            "data": {
                "bindViewModelToArtboard": {
                    "artboardId": "0-2",
                    "viewModelId": "0-14",
                    "viewModelInstanceId": "0-15",
                }
            },
        },
    )


if __name__ == "__main__":
    main()
