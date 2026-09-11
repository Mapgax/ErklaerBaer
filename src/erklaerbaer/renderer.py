from __future__ import annotations

import hashlib
import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont

from .audio import audio_envelope
from .config import Settings
from .mascot_library import MascotLibrary, rig_root
from .mechanisms import BeatState, ScienceStage, beat_at
from .models import Scene, ScenePrimitive, Storyboard
from .visuals import canonical_visual_token

Color = tuple[int, int, int]


@dataclass(frozen=True)
class Palette:
    cream: Color = (248, 239, 216)
    brown: Color = (157, 91, 39)
    brown_dark: Color = (82, 48, 31)
    muzzle: Color = (238, 203, 139)
    teal: Color = (24, 137, 126)
    coral: Color = (238, 102, 76)
    yellow: Color = (244, 181, 38)
    blue: Color = (72, 164, 207)
    ink: Color = (42, 53, 52)
    white: Color = (255, 252, 243)


CATEGORY_ACCENTS: dict[str, tuple[Color, Color]] = {
    "kuechenchemie": ((238, 102, 76), (244, 181, 38)),
    "physik": ((72, 164, 207), (24, 137, 126)),
    "weltraum-physik": ((72, 164, 207), (142, 105, 174)),
    "biologie": ((92, 154, 92), (244, 181, 38)),
    "natur-tiere": ((92, 154, 92), (244, 181, 38)),
    "technik": ((93, 113, 151), (238, 102, 76)),
    "mathematik": ((142, 105, 174), (72, 164, 207)),
    "astronomie": ((68, 75, 125), (244, 181, 38)),
}


class PaperCutRenderer:
    """Deterministic scene renderer made only from reusable drawing primitives."""

    def __init__(
        self,
        settings: Settings,
        *,
        width: int | None = None,
        height: int | None = None,
        fps: int | None = None,
    ) -> None:
        render = settings.section("render")
        self.width = width or int(render["width"])
        self.height = height or int(render["height"])
        self.fps = fps or int(render["fps"])
        self.safe = float(render["safe_margin_fraction"])
        self.palette = Palette()
        self._backgrounds: dict[str, Image.Image] = {}
        self._grain_layers: dict[str, Image.Image] = {}
        self.project_root = settings.project_root
        self.library_root = settings.project_root / "assets/mascot/rig/v2"
        self._library = None

    def render_video(
        self,
        storyboard: Storyboard,
        scene_durations: Sequence[float],
        output_path: Path,
        *,
        audio_path: Path | None = None,
        segments: Sequence[dict] = (),
    ) -> float:
        if len(scene_durations) != len(storyboard.scenes):
            raise ValueError("One duration is required per scene")
        total_seconds = sum(scene_durations)
        frame_count = max(1, round(total_seconds * self.fps))
        envelope = (
            audio_envelope(audio_path, self.fps, frame_count)
            if audio_path is not None
            else np.zeros(frame_count, dtype=np.float32)
        )
        output_path.parent.mkdir(parents=True, exist_ok=True)
        writer = imageio.get_writer(
            output_path,
            fps=self.fps,
            codec="libx264",
            format="FFMPEG",
            pixelformat="yuv420p",
            macro_block_size=1,
            ffmpeg_params=["-crf", "20", "-preset", "medium", "-movflags", "+faststart"],
        )
        try:
            for frame_index in range(frame_count):
                moment = frame_index / self.fps
                scene_index, scene_start = _scene_at(moment, scene_durations)
                scene = storyboard.scenes[scene_index]
                duration = scene_durations[scene_index]
                progress = min(1.0, max(0.0, (moment - scene_start) / duration))
                frame = self.render_frame(
                    storyboard,
                    scene,
                    progress=progress,
                    mouth=float(envelope[frame_index]),
                    scene_seconds=moment - scene_start,
                    global_seconds=moment,
                    segments=segments,
                )
                fade_seconds = 0.42
                if scene_index > 0 and moment - scene_start < fade_seconds:
                    prior = self.render_frame(
                        storyboard,
                        storyboard.scenes[scene_index - 1],
                        progress=1.0,
                        mouth=float(envelope[frame_index]),
                        scene_seconds=scene_durations[scene_index - 1],
                        global_seconds=moment,
                        segments=segments,
                    )
                    alpha = (moment - scene_start) / fade_seconds
                    blank = self.render_background(storyboard, progress=alpha)
                    frame = _fade_through_blank(prior, frame, blank, alpha)
                writer.append_data(np.asarray(frame, dtype=np.uint8))
        finally:
            writer.close()
        return total_seconds

    def _render_collage(
        self, image, storyboard, scene, progress, scene_seconds, global_seconds, segments
    ):
        from .collage_coin import draw as draw_coin
        from .collage_guitar import draw as draw_guitar

        if scene.shot is None or scene.mechanism is None:
            raise ValueError("V3 requires an explicit supported shot and mechanism")
        draw_template = {"guitar-collage": draw_guitar, "coin-collage": draw_coin}[
            scene.shot.template_id
        ]
        seconds = (
            scene_seconds if scene_seconds is not None else progress * scene.duration_hint_seconds
        )
        state = (
            beat_at(scene, seconds, list(segments)) if segments else BeatState("vibrate", seconds)
        )
        if scene_seconds is not None and not segments:
            raise ValueError("V3 requires measured speech timing")
        canvas = ImageChops.multiply(image, self._grain_layer(storyboard.source_hash)).convert(
            "RGBA"
        )
        draw_template(
            canvas,
            scene,
            seconds,
            state,
            font=school_font(46),
            small_font=school_font(32),
        )
        if scene.mascot.visible and seconds >= scene.mascot.start_seconds:
            library_root = rig_root(self.project_root)
            if self._library is None or self._library.root != library_root.resolve():
                self._library = MascotLibrary(library_root)
            clock = (
                (global_seconds if global_seconds is not None else seconds)
                if scene.mascot.action.value == "neutral"
                else seconds - scene.mascot.start_seconds
            )
            h = round(scene.mascot.height_fraction * self.height)
            clip = self._library.frame(scene.mascot.action.value, clock, h)
            x = (
                round(0.12 * self.width)
                if scene.shot.framing in {"establish", "reaction"}
                else round(0.1 * self.width)
            )
            canvas.alpha_composite(clip, (x, round(0.86 * self.height) - clip.height))
        draw = ImageDraw.Draw(canvas)
        _centered_multiline(
            draw,
            " / ".join(scene.on_screen_words),
            (0.1 * self.width, 0.10 * self.height, 0.9 * self.width, 0.23 * self.height),
            school_font(round(0.049 * self.height)),
            self.palette.ink,
            spacing=4,
            stroke=1,
        )
        return canvas.convert("RGB")

    def render_frame(
        self,
        storyboard: Storyboard,
        scene: Scene,
        *,
        progress: float,
        mouth: float = 0.0,
        scene_seconds: float | None = None,
        global_seconds: float | None = None,
        segments: Sequence[dict] = (),
    ) -> Image.Image:
        key = f"{storyboard.source_hash}:{storyboard.category}"
        image = self._paper_background(key).copy()
        draw = ImageDraw.Draw(image)
        accent, secondary = CATEGORY_ACCENTS.get(
            storyboard.category.lower(), (self.palette.teal, self.palette.yellow)
        )
        self._corner_shapes(draw, accent, secondary, progress)
        if storyboard.schema_version == "3":
            return self._render_collage(
                image, storyboard, scene, progress, scene_seconds, global_seconds, segments
            )
        if storyboard.schema_version == "2":
            if scene.mechanism is None:
                raise ValueError("Production scene needs an explicit science mechanism")
            seconds = (
                scene_seconds
                if scene_seconds is not None
                else progress * scene.duration_hint_seconds
            )
            if segments:
                state = beat_at(scene, seconds, list(segments))
            elif scene_seconds is not None:
                raise ValueError("Production video requires measured narration timing")
            else:
                # Still previews select a beat, never claim measured speech alignment.
                index = min(
                    len(scene.mechanism.beats) - 1, int(progress * len(scene.mechanism.beats))
                )
                state = BeatState(scene.mechanism.beats[index].action, 1.0)
            visible = scene.mascot.visible and seconds >= scene.mascot.start_seconds
            left, right = self.safe * self.width, (1 - self.safe) * self.width
            usable = right - left
            if visible:
                if scene.mascot.placement == "left":
                    left += 0.29 * usable
                else:
                    right -= 0.29 * usable
            ScienceStage(draw, (left, 0.25 * self.height, right, 0.86 * self.height)).render(
                scene.mechanism.kind, state
            )
            label_box = (
                self.safe * self.width,
                0.105 * self.height,
                (1 - self.safe) * self.width,
                0.22 * self.height,
            )
            font = _font(round(self.height * 0.041), bold=True)
            _centered_multiline(
                draw,
                " / ".join(scene.on_screen_words).replace("→", ":").replace("·", "/"),
                label_box,
                font,
                self.palette.ink,
                spacing=4,
            )
            image = ImageChops.multiply(image, self._grain_layer(key))
            if visible:
                if self._library is None:
                    self._library = MascotLibrary(self.library_root)
                local = seconds - scene.mascot.start_seconds
                clock = (
                    (global_seconds if global_seconds is not None else seconds)
                    if scene.mascot.action.value == "neutral"
                    else local
                )
                clip = self._library.frame(
                    scene.mascot.action.value,
                    clock,
                    round(scene.mascot.height_fraction * self.height),
                )
                # Scale down again if needed to stay inside the 29% mascot allocation.
                max_width = round(0.27 * usable)
                if clip.width > max_width:
                    clip = clip.resize(
                        (max_width, round(clip.height * max_width / clip.width)),
                        Image.Resampling.LANCZOS,
                    )
                x = (
                    round(self.safe * self.width)
                    if scene.mascot.placement == "left"
                    else round((1 - self.safe) * self.width - clip.width)
                )
                y = round(0.86 * self.height - clip.height)
                image.paste(clip, (x, y), clip)
            return image
        pose = _bear_pose(scene)
        bear_x = self.width * (0.235 if pose == "discover" else 0.205)
        bear_y = self.height * 0.62 + math.sin(progress * math.tau) * self.height * 0.006
        self._draw_bear(
            draw,
            bear_x,
            bear_y,
            self.height * 0.66,
            mouth,
            pose=pose,
            progress=progress,
        )
        self._draw_primitive(draw, scene, progress, accent, secondary)
        self._draw_scene_label(draw, scene, accent)
        return ImageChops.multiply(image, self._grain_layer(key))

    def render_background(self, storyboard: Storyboard, *, progress: float) -> Image.Image:
        """Render a text-free bridge frame so adjacent labels can never overlap."""
        key = f"{storyboard.source_hash}:{storyboard.category}"
        image = self._paper_background(key).copy()
        draw = ImageDraw.Draw(image)
        accent, secondary = CATEGORY_ACCENTS.get(
            storyboard.category.lower(), (self.palette.teal, self.palette.yellow)
        )
        self._corner_shapes(draw, accent, secondary, progress)
        return ImageChops.multiply(image, self._grain_layer(key))

    def render_thumbnail(self, storyboard: Storyboard, output_path: Path) -> None:
        scene = storyboard.scenes[min(2, len(storyboard.scenes) - 1)]
        frame = self.render_frame(storyboard, scene, progress=0.62, mouth=0.1)
        frame = frame.resize((1280, 720), Image.Resampling.LANCZOS)
        draw = ImageDraw.Draw(frame)
        banner = (445, 442, 1215, 674)
        _rounded_with_shadow(draw, banner, 30, self.palette.white, shadow=12)
        font = _font(62, bold=True)
        text = _fit_text(
            storyboard.youtube.thumbnail_text,
            font,
            max_width=banner[2] - banner[0] - 70,
            max_lines=2,
        )
        _centered_multiline(draw, text, banner, font, self.palette.ink, spacing=8)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        frame.save(output_path, format="JPEG", quality=92, optimize=True)

    def _paper_background(self, key: str) -> Image.Image:
        cached = self._backgrounds.get(key)
        if cached is not None:
            return cached
        seed = int(hashlib.sha256(key.encode()).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        base = np.empty((self.height, self.width, 3), dtype=np.int16)
        base[:] = self.palette.cream
        noise = rng.normal(0, 2.1, (self.height, self.width, 1))
        base = np.clip(base + noise, 0, 255).astype(np.uint8)
        image = Image.fromarray(base, mode="RGB")
        draw = ImageDraw.Draw(image)
        for _ in range(max(80, self.width // 8)):
            x = int(rng.integers(0, self.width))
            y = int(rng.integers(0, self.height))
            length = int(rng.integers(2, max(3, self.width // 300)))
            draw.line((x, y, x + length, y), fill=(223, 210, 184), width=1)
        self._backgrounds[key] = image
        return image

    def _grain_layer(self, key: str) -> Image.Image:
        cached = self._grain_layers.get(key)
        if cached is not None:
            return cached
        seed = int(hashlib.sha256(f"grain:{key}".encode()).hexdigest()[:8], 16)
        rng = np.random.default_rng(seed)
        grain = rng.integers(247, 256, (self.height, self.width, 1), dtype=np.uint8)
        image = Image.fromarray(np.repeat(grain, 3, axis=2), mode="RGB")
        self._grain_layers[key] = image
        return image

    def _corner_shapes(
        self,
        draw: ImageDraw.ImageDraw,
        accent: Color,
        secondary: Color,
        progress: float,
    ) -> None:
        scale = self.height / 1080
        drift = math.sin(progress * math.tau) * 5 * scale
        for index, radius in enumerate((155, 125, 96)):
            r = round(radius * scale)
            x = round((-20 + index * 90) * scale + drift * (index + 1) / 3)
            y = round((-45 + (index % 2) * 35) * scale)
            draw.ellipse((x - r, y - r, x + r, y + r), fill=_mix(accent, (0, 0, 0), 0.08))
        r = round(100 * scale)
        draw.ellipse(
            (self.width - r, self.height - r, self.width + r, self.height + r), fill=secondary
        )

    def _draw_bear(
        self,
        draw: ImageDraw.ImageDraw,
        center_x: float,
        center_y: float,
        size: float,
        mouth: float,
        *,
        pose: str,
        progress: float,
    ) -> None:
        s = size / 560
        cx, cy = int(center_x), int(center_y)
        brown = (168, 96, 38)
        brown_light = (185, 111, 50)
        dark, muzzle = self.palette.brown_dark, (241, 207, 145)

        # Layered shadows and asymmetry make the mascot read as tactile paper, not a flat icon.
        for leg_x in (-72, 72):
            draw.rounded_rectangle(
                _box(
                    cx + (leg_x - 39) * s,
                    cy + 105 * s,
                    cx + (leg_x + 39) * s,
                    cy + 220 * s,
                ),
                radius=max(4, round(28 * s)),
                fill=brown,
            )
        _ellipse_shadow(
            draw, _box(cx - 116 * s, cy - 122 * s, cx + 116 * s, cy + 170 * s), brown, 14 * s
        )
        draw.ellipse(
            _box(cx - 96 * s, cy - 98 * s, cx + 86 * s, cy + 148 * s),
            fill=brown_light,
        )
        draw.ellipse(_box(cx - 135 * s, cy - 242 * s, cx + 135 * s, cy + 35 * s), fill=brown)
        draw.ellipse(_box(cx - 104 * s, cy - 223 * s, cx + 80 * s, cy + 18 * s), fill=brown_light)
        self._draw_bear_fibers(draw, cx, cy, s, brown, dark)
        for offset in (-92, 92):
            draw.ellipse(
                _box(cx + (offset - 48) * s, cy - 270 * s, cx + (offset + 48) * s, cy - 174 * s),
                fill=brown,
            )
            draw.ellipse(
                _box(cx + (offset - 25) * s, cy - 247 * s, cx + (offset + 25) * s, cy - 197 * s),
                fill=dark,
            )

        gaze = 5 * s if pose in {"discover", "explain"} else 0
        draw.ellipse(_box(cx - 80 * s, cy - 115 * s, cx + 80 * s, cy + 27 * s), fill=muzzle)
        for offset in (-47, 47):
            draw.ellipse(
                _box(cx + (offset - 21) * s, cy - 154 * s, cx + (offset + 21) * s, cy - 105 * s),
                fill=self.palette.white,
            )
            draw.ellipse(
                _box(
                    cx + (offset - 7) * s + gaze,
                    cy - 139 * s,
                    cx + (offset + 7) * s + gaze,
                    cy - 116 * s,
                ),
                fill=dark,
            )
            brow_y = cy - 171 * s
            draw.arc(
                _box(
                    cx + (offset - 30) * s,
                    brow_y - 10 * s,
                    cx + (offset + 30) * s,
                    brow_y + 24 * s,
                ),
                start=195,
                end=340,
                fill=dark,
                width=max(2, round(7 * s)),
            )
        draw.ellipse(_box(cx - 25 * s, cy - 95 * s, cx + 25 * s, cy - 58 * s), fill=dark)
        mouth_height = max(5, 5 + mouth * 18) * s
        if mouth > 0.12:
            draw.ellipse(
                _box(cx - 21 * s, cy - 45 * s, cx + 21 * s, cy - 45 * s + mouth_height),
                fill=dark,
            )
        else:
            draw.arc(
                _box(cx - 27 * s, cy - 57 * s, cx + 27 * s, cy - 25 * s),
                start=20,
                end=160,
                fill=dark,
                width=max(2, round(5 * s)),
            )

        # Pose-specific arms make the bear participate in the explanation.
        arm_width = max(10, round(66 * s))
        if pose == "discover":
            reach = math.sin(min(1.0, progress * 1.6) * math.pi / 2)
            right_hand = (cx + (150 + 48 * reach) * s, cy + (10 - 50 * reach) * s)
            draw.line(
                ((cx + 90 * s, cy - 5 * s), (cx + 135 * s, cy + 35 * s), right_hand),
                fill=brown,
                width=arm_width,
                joint="curve",
            )
            draw.ellipse(
                _box(
                    right_hand[0] - 38 * s,
                    right_hand[1] - 34 * s,
                    right_hand[0] + 38 * s,
                    right_hand[1] + 34 * s,
                ),
                fill=brown_light,
            )
            left_hand = (cx - 142 * s, cy - 28 * s)
            draw.line(
                ((cx - 90 * s, cy - 5 * s), left_hand),
                fill=brown,
                width=arm_width,
            )
            self._draw_magnifier(draw, left_hand, (cx - 164 * s, cy - 142 * s), s)
        elif pose == "think":
            chin = (cx + 62 * s, cy - 35 * s)
            draw.line(
                ((cx + 95 * s, cy + 30 * s), (cx + 96 * s, cy - 5 * s), chin),
                fill=brown,
                width=arm_width,
                joint="curve",
            )
            draw.ellipse(
                _box(
                    chin[0] - 31 * s,
                    chin[1] - 27 * s,
                    chin[0] + 31 * s,
                    chin[1] + 27 * s,
                ),
                fill=brown_light,
            )
            lowered = (cx - 145 * s, cy + 70 * s)
            draw.line(((cx - 95 * s, cy + 20 * s), lowered), fill=brown, width=arm_width)
            self._draw_magnifier(draw, lowered, (cx - 185 * s, cy + 145 * s), s)
        elif pose == "explain":
            point = (cx + (184 + 8 * math.sin(progress * math.tau)) * s, cy - 35 * s)
            draw.line(
                ((cx + 90 * s, cy + 5 * s), (cx + 135 * s, cy - 18 * s), point),
                fill=brown,
                width=arm_width,
                joint="curve",
            )
            draw.ellipse(
                _box(
                    point[0] - 30 * s,
                    point[1] - 28 * s,
                    point[0] + 30 * s,
                    point[1] + 28 * s,
                ),
                fill=brown_light,
            )
            relaxed = (cx - 137 * s, cy + 45 * s)
            draw.line(((cx - 90 * s, cy + 5 * s), relaxed), fill=brown, width=arm_width)
            self._draw_magnifier(draw, relaxed, (cx - 165 * s, cy - 86 * s), s)
        else:
            left_hand = (cx - 140 * s, cy + 40 * s)
            right_hand = (cx + 137 * s, cy + 18 * s)
            draw.line(((cx - 90 * s, cy), left_hand), fill=brown, width=arm_width)
            draw.line(((cx + 90 * s, cy), right_hand), fill=brown, width=arm_width)
            self._draw_magnifier(draw, right_hand, (cx + 166 * s, cy - 105 * s), s)

        # Teal explorer neckerchief, layered after the arms.
        draw.rounded_rectangle(
            _box(cx - 111 * s, cy + 4 * s, cx + 111 * s, cy + 48 * s),
            radius=max(3, round(19 * s)),
            fill=_mix(self.palette.teal, dark, 0.08),
        )
        draw.polygon(
            [
                (cx - 8 * s, cy + 41 * s),
                (cx - 72 * s, cy + 118 * s),
                (cx - 20 * s, cy + 102 * s),
                (cx + 2 * s, cy + 55 * s),
            ],
            fill=self.palette.teal,
        )
        draw.polygon(
            [
                (cx + 8 * s, cy + 41 * s),
                (cx + 73 * s, cy + 110 * s),
                (cx + 22 * s, cy + 99 * s),
                (cx - 2 * s, cy + 55 * s),
            ],
            fill=_mix(self.palette.teal, self.palette.blue, 0.12),
        )
        draw.ellipse(
            _box(cx - 25 * s, cy + 27 * s, cx + 25 * s, cy + 77 * s),
            fill=_mix(self.palette.teal, self.palette.white, 0.18),
        )
        for foot in (-73, 73):
            draw.ellipse(
                _box(cx + (foot - 51) * s, cy + 187 * s, cx + (foot + 51) * s, cy + 235 * s),
                fill=brown,
            )
            for toe in (-20, 4, 28):
                toe_x = cx + (foot + toe) * s
                draw.line(
                    (toe_x, cy + 210 * s, toe_x - 4 * s, cy + 231 * s),
                    fill=_mix(brown, dark, 0.35),
                    width=max(1, round(3 * s)),
                )

        # Small cut-paper/fur marks keep large brown surfaces visually alive.
        for dx, dy, tilt in ((-62, 84, 1), (38, 108, -1), (-45, -198, -1), (48, -188, 1)):
            draw.line(
                (
                    cx + dx * s,
                    cy + dy * s,
                    cx + (dx + 11 * tilt) * s,
                    cy + (dy + 4) * s,
                ),
                fill=_mix(brown, dark, 0.18),
                width=max(1, round(3 * s)),
            )

    @staticmethod
    def _draw_bear_fibers(
        draw: ImageDraw.ImageDraw,
        cx: int,
        cy: int,
        scale: float,
        brown: Color,
        dark: Color,
    ) -> None:
        fiber = _mix(brown, dark, 0.16)
        for row in range(-210, 150, 25):
            for column in range(-95, 100, 28):
                in_head = (column / 130) ** 2 + ((row + 105) / 138) ** 2 < 0.86
                in_body = (column / 110) ** 2 + ((row - 25) / 145) ** 2 < 0.82
                if not (in_head or in_body):
                    continue
                wobble = ((row + column) // 7) % 7 - 3
                x = cx + (column + wobble) * scale
                y = cy + row * scale
                draw.line(
                    (x, y, x + (7 + wobble * 0.5) * scale, y + 2 * scale),
                    fill=fiber,
                    width=max(1, round(scale)),
                )

    def _draw_magnifier(
        self,
        draw: ImageDraw.ImageDraw,
        handle_start: tuple[float, float],
        glass_center: tuple[float, float],
        scale: float,
    ) -> None:
        glass_x, glass_y = glass_center
        draw.line(
            (handle_start[0], handle_start[1], glass_x, glass_y + 42 * scale),
            fill=self.palette.brown_dark,
            width=max(3, round(14 * scale)),
        )
        _ellipse_shadow(
            draw,
            _box(
                glass_x - 50 * scale,
                glass_y - 50 * scale,
                glass_x + 50 * scale,
                glass_y + 50 * scale,
            ),
            (220, 247, 244),
            6 * scale,
        )
        draw.ellipse(
            _box(
                glass_x - 50 * scale,
                glass_y - 50 * scale,
                glass_x + 50 * scale,
                glass_y + 50 * scale,
            ),
            outline=self.palette.teal,
            width=max(3, round(12 * scale)),
        )
        draw.arc(
            _box(
                glass_x - 31 * scale,
                glass_y - 31 * scale,
                glass_x + 31 * scale,
                glass_y + 31 * scale,
            ),
            start=205,
            end=285,
            fill=(255, 255, 255),
            width=max(2, round(8 * scale)),
        )

    def _draw_primitive(
        self,
        draw: ImageDraw.ImageDraw,
        scene: Scene,
        progress: float,
        accent: Color,
        secondary: Color,
    ) -> None:
        area = (
            int(self.width * 0.43),
            int(self.height * 0.24),
            int(self.width * (1 - self.safe)),
            int(self.height * 0.84),
        )
        dispatch = {
            ScenePrimitive.QUESTION: self._question,
            ScenePrimitive.MACRO_TO_MICRO: self._macro_to_micro,
            ScenePrimitive.PARTICLES: self._particles,
            ScenePrimitive.CAUSE_EFFECT: self._cause_effect,
            ScenePrimitive.FLOW: self._flow,
            ScenePrimitive.COMPARISON: self._comparison,
            ScenePrimitive.PREDICTION: self._prediction,
            ScenePrimitive.RECAP: self._recap,
        }
        seed = f"{scene.scene_id}:{'|'.join(scene.visual_tokens)}"
        dispatch[scene.primitive](draw, area, progress, accent, secondary, seed)

    def _draw_scene_label(self, draw: ImageDraw.ImageDraw, scene: Scene, accent: Color) -> None:
        if not scene.on_screen_words:
            return
        text = "  •  ".join(scene.on_screen_words)
        font = _font(round(self.height * 0.052), bold=True)
        max_width = int(self.width * 0.54)
        fitted = _fit_text(text, font, max_width=max_width, max_lines=2)
        box = (
            int(self.width * 0.42),
            int(self.height * 0.08),
            int(self.width * 0.91),
            int(self.height * 0.22),
        )
        _rounded_with_shadow(draw, box, int(self.height * 0.025), self.palette.white, shadow=8)
        _centered_multiline(
            draw, fitted, box, font, _mix(accent, self.palette.ink, 0.38), spacing=5
        )

    def _question(
        self,
        draw: ImageDraw.ImageDraw,
        box: tuple[int, int, int, int],
        progress: float,
        accent: Color,
        secondary: Color,
        seed: str,
    ) -> None:
        cx, cy = _center(box)
        radius = min(box[2] - box[0], box[3] - box[1]) * (
            0.31 + 0.025 * math.sin(progress * math.pi)
        )
        tokens = _tokens_from_seed(seed)
        token = _meaningful_token(tokens, fallback="question")
        if _semantic_kind(token) in {"stone", "lifted-stone"}:
            cx = box[0] + (box[2] - box[0]) * 0.04
            lift = _ease_out(min(1.0, progress * 1.35))
            ground_y = cy + radius * 0.72
            draw.rounded_rectangle(
                _box(cx - radius * 1.05, ground_y, cx + radius * 1.05, ground_y + radius * 0.16),
                radius=max(2, round(radius * 0.06)),
                fill=(126, 91, 55),
            )
            stone_y = ground_y - radius * (0.30 + 0.68 * lift)
            _draw_semantic_icon(
                draw,
                (cx, stone_y),
                radius * 1.45,
                "stone",
                (131, 125, 108),
                self.palette.ink,
                progress,
            )
            paw = (cx - radius * 0.70, stone_y + radius * 0.28)
            draw.ellipse(
                _box(
                    paw[0] - radius * 0.18,
                    paw[1] - radius * 0.15,
                    paw[0] + radius * 0.18,
                    paw[1] + radius * 0.15,
                ),
                fill=(185, 111, 50),
            )
            reveal = _ease_out(max(0.0, min(1.0, (progress - 0.20) / 0.42)))
            if reveal > 0:
                animal_tokens = ("woodlouse", "beetle", "worm")
                for index, animal in enumerate(animal_tokens):
                    offset = (-0.55 + index * 0.55) * radius
                    scurry = math.sin(progress * math.tau + index) * radius * 0.06
                    _draw_semantic_icon(
                        draw,
                        (cx + offset + scurry, ground_y - radius * 0.02),
                        radius * 0.36 * reveal,
                        animal,
                        accent if index != 1 else secondary,
                        self.palette.ink,
                        progress + index * 0.13,
                    )
            badge_radius = radius * 0.25
            badge_center = (cx + radius * 0.83, cy - radius * 0.77)
            _ellipse_shadow(
                draw,
                _box(
                    badge_center[0] - badge_radius,
                    badge_center[1] - badge_radius,
                    badge_center[0] + badge_radius,
                    badge_center[1] + badge_radius,
                ),
                secondary,
                5,
            )
            font = _font(round(badge_radius * 1.38), bold=True)
            _center_text(draw, "?", badge_center, font, self.palette.white)
            return
        _ellipse_shadow(
            draw, _box(cx - radius, cy - radius, cx + radius, cy + radius), self.palette.white, 12
        )
        draw.ellipse(
            _box(cx - radius, cy - radius, cx + radius, cy + radius),
            outline=accent,
            width=max(4, round(radius * 0.055)),
        )
        if token == "question":
            font = _font(round(radius * 1.28), bold=True)
            _center_text(draw, "?", (cx, cy - radius * 0.05), font, secondary)
        else:
            _draw_semantic_icon(
                draw,
                (cx, cy),
                radius * 1.18,
                token,
                accent,
                secondary,
                progress,
            )
            badge_radius = radius * 0.31
            badge_center = (cx + radius * 0.70, cy + radius * 0.68)
            _ellipse_shadow(
                draw,
                _box(
                    badge_center[0] - badge_radius,
                    badge_center[1] - badge_radius,
                    badge_center[0] + badge_radius,
                    badge_center[1] + badge_radius,
                ),
                secondary,
                5,
            )
            font = _font(round(badge_radius * 1.35), bold=True)
            _center_text(draw, "?", badge_center, font, self.palette.white)

    def _macro_to_micro(
        self,
        draw: ImageDraw.ImageDraw,
        box: tuple[int, int, int, int],
        progress: float,
        accent: Color,
        secondary: Color,
        seed: str,
    ) -> None:
        x1, y1, x2, y2 = box
        cx, cy = int(x1 + (x2 - x1) * 0.57), int((y1 + y2) / 2)
        radius = int(min(x2 - x1, y2 - y1) * 0.31)
        draw.line(
            (cx + radius * 0.72, cy + radius * 0.72, cx + radius * 1.25, cy + radius * 1.25),
            fill=self.palette.ink,
            width=max(8, radius // 8),
        )
        _ellipse_shadow(
            draw, (cx - radius, cy - radius, cx + radius, cy + radius), self.palette.white, 11
        )
        draw.ellipse(
            (cx - radius, cy - radius, cx + radius, cy + radius),
            outline=accent,
            width=max(6, radius // 14),
        )
        tokens = _tokens_from_seed(seed)
        meaningful = [token for token in tokens if _semantic_kind(token) != "generic"]
        if meaningful:
            shown = meaningful[1:5] if len(meaningful) > 1 else meaningful
            count = max(1, len(shown))
            layouts: dict[int, tuple[tuple[float, float], ...]] = {
                1: ((0.0, 0.0),),
                2: ((-0.34, 0.0), (0.34, 0.0)),
                3: ((-0.34, -0.22), (0.34, -0.22), (0.0, 0.34)),
                4: ((-0.34, -0.27), (0.34, -0.27), (-0.34, 0.31), (0.34, 0.31)),
            }
            for index, token in enumerate(shown):
                dx, dy = layouts[count][index]
                icon_x = cx + dx * radius
                icon_y = cy + dy * radius
                _draw_semantic_icon(
                    draw,
                    (icon_x, icon_y),
                    radius * (0.43 if count > 1 else 1.05),
                    token,
                    accent,
                    secondary,
                    progress + index * 0.11,
                )
        else:
            for px, py, pr in _particle_positions(seed, 9):
                x = cx + (px - 0.5) * radius * 1.35
                y = (
                    cy
                    + (py - 0.5) * radius * 1.35
                    + math.sin(progress * math.tau + pr * 8) * radius * 0.08
                )
                r = radius * (0.055 + pr * 0.035)
                draw.ellipse(
                    _box(x - r, y - r, x + r, y + r),
                    fill=secondary if pr > 0.5 else accent,
                )

    def _particles(
        self,
        draw: ImageDraw.ImageDraw,
        box: tuple[int, int, int, int],
        progress: float,
        accent: Color,
        secondary: Color,
        seed: str,
    ) -> None:
        x1, y1, x2, y2 = box
        _rounded_with_shadow(draw, box, 32, self.palette.white, shadow=10)
        tokens = _tokens_from_seed(seed)
        kinds = {_semantic_kind(token) for token in tokens}
        if "stone" in kinds and {"darkness", "water-drop", "shelter"} & kinds:
            ground_y = y1 + (y2 - y1) * 0.69
            draw.rounded_rectangle(
                (x1 + 45, round(ground_y), x2 - 45, round(ground_y + 70)),
                radius=24,
                fill=(131, 91, 54),
            )
            shade = (x1 + 120, y1 + 155, x2 - 150, round(ground_y + 8))
            draw.rounded_rectangle(shade, radius=38, fill=(67, 83, 72))
            rock_center = (x1 + (x2 - x1) * 0.53, y1 + (y2 - y1) * 0.35)
            _draw_semantic_icon(
                draw,
                rock_center,
                min(x2 - x1, y2 - y1) * 0.54,
                "stone",
                (139, 133, 115),
                self.palette.ink,
                progress,
            )
            for index, x_fraction in enumerate((0.32, 0.70)):
                _draw_semantic_icon(
                    draw,
                    (x1 + (x2 - x1) * x_fraction, ground_y - 40),
                    min(x2 - x1, y2 - y1) * 0.14,
                    "water-drop",
                    self.palette.blue,
                    self.palette.white,
                    progress + index * 0.1,
                )
            _draw_semantic_icon(
                draw,
                (x1 + (x2 - x1) * 0.53, ground_y - 40),
                min(x2 - x1, y2 - y1) * 0.18,
                "woodlouse",
                accent,
                self.palette.white,
                progress,
            )
            return
        if tokens:
            visible = tokens[:8]
            columns = min(4, len(visible))
            rows = math.ceil(len(visible) / columns)
            for index, token in enumerate(visible):
                column = index % columns
                row = index // columns
                icon_x = x1 + (column + 0.5) * (x2 - x1) / columns
                icon_y = y1 + (row + 0.5) * (y2 - y1) / rows
                _draw_semantic_icon(
                    draw,
                    (icon_x, icon_y),
                    min((x2 - x1) / columns, (y2 - y1) / rows) * 0.46,
                    token,
                    accent if index % 2 == 0 else secondary,
                    self.palette.ink,
                    progress + index * 0.08,
                )
            return
        for px, py, pr in _particle_positions(seed, 16):
            x = x1 + 45 + px * (x2 - x1 - 90)
            wrapped = (py - progress * (0.25 + pr * 0.25)) % 1.0
            y = y1 + 40 + wrapped * (y2 - y1 - 80)
            radius = 10 + pr * 22
            draw.ellipse(
                _box(x - radius, y - radius, x + radius, y + radius),
                fill=accent if pr < 0.55 else secondary,
            )
            draw.ellipse(
                _box(x - radius * 0.35, y - radius * 0.5, x - radius * 0.05, y - radius * 0.2),
                fill=self.palette.white,
            )

    def _cause_effect(
        self,
        draw: ImageDraw.ImageDraw,
        box: tuple[int, int, int, int],
        progress: float,
        accent: Color,
        secondary: Color,
        seed: str,
    ) -> None:
        x1, y1, x2, y2 = box
        gap = int((x2 - x1) * 0.18)
        card_width = int((x2 - x1 - gap) / 2)
        left = (x1, y1 + 50, x1 + card_width, y2 - 50)
        right = (x2 - card_width, y1 + 50, x2, y2 - 50)
        _rounded_with_shadow(draw, left, 28, self.palette.white, shadow=9)
        _rounded_with_shadow(draw, right, 28, self.palette.white, shadow=9)
        lc = _center(left)
        rc = _center(right)
        tokens = _tokens_from_seed(seed)
        left_token = tokens[0] if tokens else "question"
        right_token = tokens[-1] if len(tokens) > 1 else left_token
        _draw_semantic_icon(draw, lc, card_width * 0.52, left_token, accent, secondary, progress)
        _draw_semantic_icon(
            draw, rc, card_width * 0.52, right_token, secondary, accent, progress + 0.2
        )
        if len(tokens) > 2:
            _draw_semantic_icon(
                draw,
                ((lc[0] + rc[0]) / 2, lc[1] - card_width * 0.27),
                card_width * 0.20,
                tokens[1],
                self.palette.blue,
                secondary,
                progress,
            )
        _arrow(
            draw,
            (left[2] + 18, (y1 + y2) // 2),
            (right[0] - 18, (y1 + y2) // 2),
            self.palette.coral,
            18,
        )

    def _flow(
        self,
        draw: ImageDraw.ImageDraw,
        box: tuple[int, int, int, int],
        progress: float,
        accent: Color,
        secondary: Color,
        seed: str,
    ) -> None:
        x1, y1, x2, y2 = box
        centers = [
            (x1 + (x2 - x1) * 0.16, y1 + (y2 - y1) * 0.54),
            (x1 + (x2 - x1) * 0.50, y1 + (y2 - y1) * 0.54),
            (x1 + (x2 - x1) * 0.84, y1 + (y2 - y1) * 0.54),
        ]
        radius = min(x2 - x1, y2 - y1) * 0.125
        tokens = _tokens_from_seed(seed)
        for start, end in zip(centers, centers[1:], strict=False):
            _arrow(
                draw,
                (start[0] + radius * 1.16, start[1]),
                (end[0] - radius * 1.16, end[1]),
                self.palette.coral,
                max(8, int(radius * 0.12)),
            )
        for index, center in enumerate(centers):
            color = accent if index != 1 else secondary
            entrance = _ease_out(max(0.0, min(1.0, progress * 2.1 - index * 0.28)))
            animated_center = (center[0], center[1] + (1 - entrance) * radius * 0.45)
            card = _box(
                animated_center[0] - radius * 1.18,
                animated_center[1] - radius * 1.34,
                animated_center[0] + radius * 1.18,
                animated_center[1] + radius * 1.34,
            )
            _rounded_with_shadow(
                draw,
                tuple(round(value) for value in card),
                max(8, round(radius * 0.22)),
                _mix(color, self.palette.white, 0.82),
                shadow=8,
            )
            _draw_semantic_icon(
                draw,
                animated_center,
                radius * 1.46 * max(0.25, entrance),
                tokens[index] if index < len(tokens) else (tokens[-1] if tokens else "question"),
                color,
                self.palette.ink,
                progress + index * 0.12,
            )

    def _comparison(
        self,
        draw: ImageDraw.ImageDraw,
        box: tuple[int, int, int, int],
        progress: float,
        accent: Color,
        secondary: Color,
        seed: str,
    ) -> None:
        x1, y1, x2, y2 = box
        tokens = _tokens_from_seed(seed)
        density_comparison = {_semantic_kind(token) for token in tokens} == {
            "stone",
            "zoo-enclosure",
        }
        count = min(3, max(2, len(tokens)))
        gap = 24
        card_width = (x2 - x1 - gap * (count - 1)) / count
        for index in range(count):
            left = x1 + index * (card_width + gap)
            entrance = _ease_out(max(0.0, min(1.0, progress * 2.0 - index * 0.22)))
            drop = round((1 - entrance) * (y2 - y1) * 0.10)
            target = (round(left), y1 + 30 + drop, round(left + card_width), y2 - 30 + drop)
            color = accent if index % 2 == 0 else secondary
            _rounded_with_shadow(
                draw,
                target,
                26,
                _mix(color, self.palette.white, 0.76),
                shadow=8,
            )
            kind = _semantic_kind(tokens[index]) if index < len(tokens) else ""
            icon_center = (
                _center(target)[0],
                _center(target)[1]
                - (target[3] - target[1]) * (0.16 if density_comparison else 0.07),
            )
            _draw_semantic_icon(
                draw,
                icon_center,
                min(card_width, target[3] - target[1]) * 0.50,
                tokens[index] if index < len(tokens) else (tokens[-1] if tokens else "question"),
                color,
                self.palette.ink,
                progress + index * 0.12,
            )
            if density_comparison and kind == "stone":
                for animal_index, animal in enumerate(("woodlouse", "beetle", "worm", "millipede")):
                    animal_x = target[0] + (animal_index + 0.65) * (target[2] - target[0]) / 4.3
                    _draw_semantic_icon(
                        draw,
                        (animal_x, target[3] - (target[3] - target[1]) * 0.16),
                        card_width * 0.15,
                        animal,
                        accent if animal_index % 2 == 0 else secondary,
                        self.palette.ink,
                        progress + animal_index * 0.08,
                    )
            elif density_comparison and kind == "zoo-enclosure":
                _draw_semantic_icon(
                    draw,
                    (_center(target)[0], target[3] - (target[3] - target[1]) * 0.16),
                    card_width * 0.16,
                    "beetle",
                    secondary,
                    self.palette.ink,
                    progress,
                )
            leg_count = {"insect": "6", "beetle": "6", "spider": "8", "woodlouse": "14"}.get(kind)
            if leg_count:
                font = _font(round((target[3] - target[1]) * 0.12), bold=True)
                _center_text(
                    draw,
                    leg_count,
                    (_center(target)[0], target[3] - (target[3] - target[1]) * 0.12),
                    font,
                    self.palette.ink,
                )

    def _prediction(
        self,
        draw: ImageDraw.ImageDraw,
        box: tuple[int, int, int, int],
        progress: float,
        accent: Color,
        secondary: Color,
        seed: str,
    ) -> None:
        cx, cy = _center(box)
        radius = min(box[2] - box[0], box[3] - box[1]) * (
            0.23 + 0.012 * math.sin(progress * math.tau)
        )
        _ellipse_shadow(
            draw, _box(cx - radius, cy - radius, cx + radius, cy + radius), secondary, 11
        )
        bar_width = radius * 0.28
        for offset in (-bar_width * 0.72, bar_width * 0.72):
            draw.rounded_rectangle(
                _box(
                    cx + offset - bar_width / 2,
                    cy - radius * 0.48,
                    cx + offset + bar_width / 2,
                    cy + radius * 0.48,
                ),
                radius=max(3, int(bar_width * 0.22)),
                fill=self.palette.white,
            )
        tokens = _tokens_from_seed(seed)
        meaningful = [token for token in tokens if _semantic_kind(token) != "question"]
        if meaningful:
            object_center = (cx, cy - radius * 1.40)
            reveal = _ease_out(max(0.0, min(1.0, (progress - 0.52) / 0.20)))
            if reveal > 0:
                _draw_semantic_icon(
                    draw,
                    object_center,
                    radius * 0.78 * reveal,
                    meaningful[0],
                    accent,
                    self.palette.ink,
                    progress,
                )
        # No decorative orbiting dots: they previously crossed the pictured object.

    def _recap(
        self,
        draw: ImageDraw.ImageDraw,
        box: tuple[int, int, int, int],
        progress: float,
        accent: Color,
        secondary: Color,
        seed: str,
    ) -> None:
        x1, y1, x2, y2 = box
        centers = [
            (x1 + (x2 - x1) * 0.16, (y1 + y2) / 2),
            (x1 + (x2 - x1) * 0.50, (y1 + y2) / 2),
            (x1 + (x2 - x1) * 0.84, (y1 + y2) / 2),
        ]
        radius = min(x2 - x1, y2 - y1) * 0.10
        tokens = _tokens_from_seed(seed)
        for start, end in zip(centers, centers[1:], strict=False):
            _arrow(
                draw,
                (start[0] + radius, start[1]),
                (end[0] - radius, end[1]),
                self.palette.coral,
                14,
            )
        for index, center in enumerate(centers):
            color = (accent, secondary, self.palette.teal)[index]
            entrance = _ease_out(max(0.0, min(1.0, progress * 2.0 - index * 0.20)))
            card_radius = radius * 1.22
            _rounded_with_shadow(
                draw,
                tuple(
                    round(value)
                    for value in _box(
                        center[0] - card_radius,
                        center[1] - card_radius,
                        center[0] + card_radius,
                        center[1] + card_radius,
                    )
                ),
                max(8, round(radius * 0.28)),
                _mix(color, self.palette.white, 0.80),
                shadow=9,
            )
            _draw_semantic_icon(
                draw,
                center,
                radius * 1.45 * max(0.25, entrance),
                tokens[index] if index < len(tokens) else (tokens[-1] if tokens else "question"),
                color,
                self.palette.ink,
                progress + index * 0.1,
            )


def _tokens_from_seed(seed: str) -> list[str]:
    _, separator, raw_tokens = seed.partition(":")
    if not separator:
        return []
    return [token.strip() for token in raw_tokens.split("|") if token.strip()]


def _meaningful_token(tokens: Sequence[str], *, fallback: str) -> str:
    for token in tokens:
        lowered = token.lower()
        if "question" not in lowered and "thought" not in lowered:
            return token
    return fallback


def _semantic_kind(token: str) -> str:
    return canonical_visual_token(token) or "generic"


def _leg_pair_count(kind: str) -> int:
    return {"insect": 3, "beetle": 3, "spider": 4, "woodlouse": 7}.get(kind, 0)


def _draw_semantic_icon(
    draw: ImageDraw.ImageDraw,
    center: tuple[float, float],
    size: float,
    token: str,
    primary: Color,
    secondary: Color,
    progress: float,
) -> None:
    kind = _semantic_kind(token)
    cx, cy = center
    pulse = 1.0 + 0.035 * math.sin(progress * math.tau)
    s = max(8.0, size * pulse)
    outline = secondary
    highlight = _mix(primary, (255, 255, 255), 0.42)
    shadow = _mix(primary, (35, 35, 30), 0.30)

    if kind in {"stone", "lifted-stone"}:
        points = [
            (cx - s * 0.50, cy + s * 0.28),
            (cx - s * 0.37, cy - s * 0.18),
            (cx - s * 0.08, cy - s * 0.43),
            (cx + s * 0.35, cy - s * 0.24),
            (cx + s * 0.50, cy + s * 0.28),
        ]
        draw.polygon([(x + s * 0.05, y + s * 0.07) for x, y in points], fill=shadow)
        draw.polygon(points, fill=_mix(primary, (132, 116, 93), 0.38))
        draw.line(
            (cx - s * 0.20, cy - s * 0.14, cx + s * 0.18, cy - s * 0.27),
            fill=highlight,
            width=max(2, round(s * 0.06)),
        )
        if "life" in token.lower() or "teeming" in token.lower():
            for offset in (-0.22, 0.02, 0.25):
                draw.ellipse(
                    _box(
                        cx + offset * s - s * 0.055,
                        cy + s * 0.20,
                        cx + offset * s + s * 0.055,
                        cy + s * 0.31,
                    ),
                    fill=outline,
                )
        return

    if kind in {"insect", "beetle", "woodlouse", "spider"}:
        leg_pairs = _leg_pair_count(kind)
        long_body = kind == "woodlouse"
        body_half_width = s * (0.18 if long_body else 0.22)
        body_half_height = s * (0.48 if long_body else 0.34)
        body_fill = primary if not long_body else _mix(primary, outline, 0.22)
        for index in range(leg_pairs):
            offset = (index - (leg_pairs - 1) / 2) * (
                body_half_height * 1.45 / max(1, leg_pairs - 1)
            )
            sweep = (index - (leg_pairs - 1) / 2) / max(1, leg_pairs - 1)
            draw.line(
                (
                    cx - body_half_width * 0.75,
                    cy + offset,
                    cx - s * (0.46 if long_body else 0.48),
                    cy + offset + sweep * s * 0.16,
                ),
                fill=outline,
                width=max(2, round(s * (0.032 if long_body else 0.045))),
            )
            draw.line(
                (
                    cx + body_half_width * 0.75,
                    cy + offset,
                    cx + s * (0.46 if long_body else 0.48),
                    cy + offset + sweep * s * 0.16,
                ),
                fill=outline,
                width=max(2, round(s * (0.032 if long_body else 0.045))),
            )
        draw.rounded_rectangle(
            _box(
                cx - body_half_width,
                cy - body_half_height,
                cx + body_half_width,
                cy + body_half_height,
            ),
            radius=max(3, round(body_half_width * 0.95)),
            fill=body_fill,
        )
        head_y = cy - body_half_height * 0.88
        head_radius = s * (0.13 if long_body else 0.18)
        draw.ellipse(
            _box(
                cx - head_radius,
                head_y - head_radius,
                cx + head_radius,
                head_y + head_radius,
            ),
            fill=outline,
        )
        if kind == "woodlouse":
            for index in range(1, 7):
                y = cy - body_half_height + index * (body_half_height * 2 / 7)
                draw.line(
                    (cx - body_half_width * 0.84, y, cx + body_half_width * 0.84, y),
                    fill=highlight,
                    width=max(1, round(s * 0.025)),
                )
            for direction in (-1, 1):
                draw.arc(
                    _box(
                        cx + direction * s * 0.02 - s * 0.22,
                        head_y - s * 0.31,
                        cx + direction * s * 0.02 + s * 0.22,
                        head_y + s * 0.05,
                    ),
                    start=210 if direction < 0 else 320,
                    end=275 if direction < 0 else 385,
                    fill=outline,
                    width=max(1, round(s * 0.025)),
                )
        elif kind == "beetle":
            draw.line(
                (cx, cy - body_half_height * 0.85, cx, cy + body_half_height * 0.88),
                fill=highlight,
                width=max(1, round(s * 0.025)),
            )
        elif kind == "spider":
            draw.ellipse(
                _box(cx - s * 0.27, cy + s * 0.02, cx + s * 0.27, cy + s * 0.42),
                fill=body_fill,
            )
        return

    if kind == "millipede":
        segments = 9
        for index in range(segments):
            x = cx - s * 0.40 + index * s * 0.10
            y = cy + math.sin(progress * math.tau + index * 0.45) * s * 0.035
            draw.ellipse(
                _box(x - s * 0.075, y - s * 0.12, x + s * 0.075, y + s * 0.12),
                fill=primary,
            )
            for direction in (-1, 1):
                draw.line(
                    (x, y + direction * s * 0.07, x - s * 0.02, y + direction * s * 0.22),
                    fill=outline,
                    width=max(1, round(s * 0.025)),
                )
        draw.ellipse(
            _box(cx - s * 0.53, cy - s * 0.13, cx - s * 0.31, cy + s * 0.13),
            fill=outline,
        )
        return

    if kind == "worm":
        points = []
        for index in range(16):
            x = cx - s * 0.48 + index * s * 0.064
            y = cy + math.sin(index / 15 * math.tau * 1.4 + progress) * s * 0.19
            points.append((x, y))
        draw.line(points, fill=primary, width=max(5, round(s * 0.18)), joint="curve")
        draw.ellipse(
            _box(
                points[-1][0] - s * 0.08,
                points[-1][1] - s * 0.08,
                points[-1][0] + s * 0.08,
                points[-1][1] + s * 0.08,
            ),
            fill=highlight,
        )
        return

    if kind == "water-drop":
        draw.polygon(
            [(cx, cy - s * 0.50), (cx - s * 0.30, cy + s * 0.10), (cx + s * 0.30, cy + s * 0.10)],
            fill=primary,
        )
        draw.ellipse(_box(cx - s * 0.30, cy - s * 0.08, cx + s * 0.30, cy + s * 0.45), fill=primary)
        draw.ellipse(
            _box(cx - s * 0.13, cy - s * 0.05, cx - s * 0.03, cy + s * 0.10), fill=highlight
        )
        return

    if kind == "darkness":
        draw.ellipse(_box(cx - s * 0.42, cy - s * 0.42, cx + s * 0.42, cy + s * 0.42), fill=outline)
        draw.ellipse(
            _box(cx - s * 0.10, cy - s * 0.50, cx + s * 0.48, cy + s * 0.17),
            fill=_mix(primary, (255, 255, 255), 0.80),
        )
        return

    if kind == "shelter":
        _draw_semantic_icon(
            draw,
            (cx, cy - s * 0.10),
            s * 0.98,
            "stone",
            primary,
            outline,
            progress,
        )
        _draw_semantic_icon(
            draw,
            (cx, cy + s * 0.32),
            s * 0.34,
            "woodlouse",
            _mix(primary, (74, 123, 77), 0.55),
            outline,
            progress,
        )
        return

    if kind == "leaf":
        draw.ellipse(_box(cx - s * 0.46, cy - s * 0.30, cx + s * 0.42, cy + s * 0.30), fill=primary)
        draw.line(
            (cx - s * 0.39, cy + s * 0.25, cx + s * 0.38, cy - s * 0.24),
            fill=outline,
            width=max(2, round(s * 0.045)),
        )
        return

    if kind == "soil":
        earth = _mix(primary, (111, 67, 38), 0.58)
        draw.rounded_rectangle(
            _box(cx - s * 0.48, cy - s * 0.05, cx + s * 0.48, cy + s * 0.44),
            radius=max(3, round(s * 0.08)),
            fill=earth,
        )
        draw.ellipse(_box(cx - s * 0.48, cy - s * 0.20, cx + s * 0.48, cy + s * 0.13), fill=earth)
        for dx, dy in ((-0.25, 0.09), (0.02, 0.24), (0.29, 0.05)):
            draw.ellipse(
                _box(
                    cx + dx * s - s * 0.04,
                    cy + dy * s - s * 0.04,
                    cx + dx * s + s * 0.04,
                    cy + dy * s + s * 0.04,
                ),
                fill=highlight,
            )
        green = (75, 139, 72)
        draw.line(
            (cx, cy - s * 0.08, cx, cy - s * 0.42),
            fill=green,
            width=max(2, round(s * 0.055)),
        )
        draw.ellipse(_box(cx - s * 0.30, cy - s * 0.45, cx, cy - s * 0.20), fill=green)
        draw.ellipse(
            _box(cx, cy - s * 0.52, cx + s * 0.31, cy - s * 0.25),
            fill=_mix(green, (255, 255, 255), 0.12),
        )
        return

    if kind == "sprout":
        draw.line(
            (cx, cy + s * 0.45, cx, cy - s * 0.18), fill=outline, width=max(3, round(s * 0.07))
        )
        draw.ellipse(_box(cx - s * 0.42, cy - s * 0.34, cx, cy + s * 0.02), fill=primary)
        draw.ellipse(
            _box(cx, cy - s * 0.45, cx + s * 0.42, cy - s * 0.06),
            fill=_mix(primary, highlight, 0.18),
        )
        draw.arc(
            _box(cx - s * 0.50, cy + s * 0.14, cx + s * 0.50, cy + s * 0.65),
            185,
            355,
            fill=_mix(primary, (119, 72, 38), 0.45),
            width=max(4, round(s * 0.13)),
        )
        return

    if kind == "zoo-enclosure":
        for offset in (-0.34, 0.0, 0.34):
            draw.rounded_rectangle(
                _box(
                    cx + offset * s - s * 0.07,
                    cy - s * 0.45,
                    cx + offset * s + s * 0.07,
                    cy + s * 0.45,
                ),
                radius=max(2, round(s * 0.03)),
                fill=primary,
            )
        for offset in (-0.20, 0.18):
            draw.rounded_rectangle(
                _box(
                    cx - s * 0.48,
                    cy + offset * s - s * 0.06,
                    cx + s * 0.48,
                    cy + offset * s + s * 0.06,
                ),
                radius=max(2, round(s * 0.03)),
                fill=outline,
            )
        return

    if kind == "coin":
        _ellipse_shadow(
            draw,
            _box(cx - s * 0.43, cy - s * 0.43, cx + s * 0.43, cy + s * 0.43),
            primary,
            s * 0.06,
        )
        draw.ellipse(
            _box(cx - s * 0.29, cy - s * 0.29, cx + s * 0.29, cy + s * 0.29),
            outline=highlight,
            width=max(2, round(s * 0.06)),
        )
        return

    if kind == "bottle":
        draw.rounded_rectangle(
            _box(cx - s * 0.30, cy - s * 0.25, cx + s * 0.30, cy + s * 0.48),
            radius=max(4, round(s * 0.12)),
            fill=primary,
            outline=outline,
            width=max(2, round(s * 0.04)),
        )
        draw.rectangle(
            _box(cx - s * 0.14, cy - s * 0.47, cx + s * 0.14, cy - s * 0.22),
            fill=primary,
            outline=outline,
            width=max(2, round(s * 0.04)),
        )
        return

    if kind == "bubble":
        draw.ellipse(
            _box(cx - s * 0.43, cy - s * 0.43, cx + s * 0.43, cy + s * 0.43),
            fill=_mix(primary, (255, 255, 255), 0.72),
            outline=outline,
            width=max(2, round(s * 0.045)),
        )
        draw.arc(
            _box(cx - s * 0.29, cy - s * 0.30, cx + s * 0.07, cy + s * 0.05),
            190,
            285,
            fill=(255, 255, 255),
            width=max(2, round(s * 0.055)),
        )
        return

    if kind == "water":
        for index in range(3):
            y = cy - s * 0.20 + index * s * 0.20
            points = [
                (
                    cx - s * 0.48 + step * s * 0.08,
                    y + math.sin(step * 0.85 + progress * math.tau) * s * 0.045,
                )
                for step in range(13)
            ]
            draw.line(points, fill=primary, width=max(2, round(s * 0.065)), joint="curve")
        return

    if kind == "heat":
        draw.ellipse(_box(cx - s * 0.25, cy + s * 0.22, cx + s * 0.25, cy + s * 0.62), fill=primary)
        draw.rounded_rectangle(
            _box(cx - s * 0.12, cy - s * 0.48, cx + s * 0.12, cy + s * 0.39),
            radius=max(3, round(s * 0.09)),
            fill=(255, 252, 243),
            outline=outline,
            width=max(2, round(s * 0.045)),
        )
        draw.rounded_rectangle(
            _box(cx - s * 0.045, cy - s * 0.19, cx + s * 0.045, cy + s * 0.38),
            radius=max(2, round(s * 0.04)),
            fill=primary,
        )
        return

    if kind == "pressure":
        draw.ellipse(_box(cx - s * 0.15, cy - s * 0.15, cx + s * 0.15, cy + s * 0.15), fill=primary)
        for angle in (0, math.pi / 2, math.pi, math.pi * 1.5):
            start = (cx + math.cos(angle) * s * 0.48, cy + math.sin(angle) * s * 0.48)
            end = (cx + math.cos(angle) * s * 0.24, cy + math.sin(angle) * s * 0.24)
            _arrow(draw, start, end, outline, max(2, round(s * 0.045)))
        return

    if kind == "air":
        for index, offset in enumerate((-0.25, 0.0, 0.25)):
            y = cy + offset * s
            drift = math.sin(progress * math.tau + index) * s * 0.08
            draw.arc(
                _box(cx - s * 0.46 + drift, y - s * 0.16, cx + s * 0.44 + drift, y + s * 0.16),
                185,
                350,
                fill=primary,
                width=max(3, round(s * 0.07)),
            )
        return

    if kind == "glass":
        vessel = [
            (cx - s * 0.36, cy - s * 0.44),
            (cx + s * 0.36, cy - s * 0.44),
            (cx + s * 0.29, cy + s * 0.46),
            (cx - s * 0.29, cy + s * 0.46),
        ]
        draw.polygon(vessel, fill=_mix((255, 255, 255), primary, 0.18))
        draw.line(vessel + [vessel[0]], fill=outline, width=max(2, round(s * 0.04)), joint="curve")
        draw.polygon(
            [
                (cx - s * 0.31, cy + s * 0.05),
                (cx + s * 0.31, cy + s * 0.05),
                (cx + s * 0.29, cy + s * 0.42),
                (cx - s * 0.29, cy + s * 0.42),
            ],
            fill=primary,
        )
        return

    if kind == "paper":
        _rounded_with_shadow(
            draw,
            _box(cx - s * 0.42, cy - s * 0.45, cx + s * 0.42, cy + s * 0.45),
            max(3, round(s * 0.06)),
            (255, 252, 243),
            shadow=max(2, round(s * 0.05)),
        )
        draw.line(
            (cx - s * 0.25, cy - s * 0.16, cx + s * 0.24, cy - s * 0.16),
            fill=primary,
            width=max(2, round(s * 0.05)),
        )
        draw.line(
            (cx - s * 0.25, cy + s * 0.04, cx + s * 0.12, cy + s * 0.04),
            fill=secondary,
            width=max(2, round(s * 0.05)),
        )
        return

    if kind == "color":
        for index, color in enumerate((primary, secondary, (238, 102, 76))):
            angle = index * math.tau / 3 + progress * 0.2
            x = cx + math.cos(angle) * s * 0.25
            y = cy + math.sin(angle) * s * 0.25
            draw.ellipse(_box(x - s * 0.19, y - s * 0.19, x + s * 0.19, y + s * 0.19), fill=color)
        return

    if kind == "guitar":
        draw.ellipse(_box(cx - s * 0.45, cy - s * 0.16, cx + s * 0.08, cy + s * 0.42), fill=primary)
        draw.ellipse(_box(cx - s * 0.33, cy - s * 0.42, cx + s * 0.11, cy + s * 0.08), fill=primary)
        draw.ellipse(_box(cx - s * 0.18, cy - s * 0.16, cx + s * 0.02, cy + s * 0.04), fill=outline)
        draw.line(
            (cx, cy - s * 0.12, cx + s * 0.48, cy - s * 0.48),
            fill=outline,
            width=max(5, round(s * 0.13)),
        )
        draw.line(
            (cx - s * 0.03, cy - s * 0.08, cx + s * 0.47, cy - s * 0.45),
            fill=highlight,
            width=max(1, round(s * 0.025)),
        )
        return

    if kind == "sound-wave":
        baseline = cy
        points = []
        for index in range(31):
            x = cx - s * 0.48 + index * s * 0.032
            amplitude = math.sin(index / 30 * math.pi) * s * 0.30
            y = baseline + math.sin(index * 0.95 + progress * math.tau) * amplitude
            points.append((x, y))
        draw.line(points, fill=primary, width=max(3, round(s * 0.07)), joint="curve")
        return

    if kind == "wind":
        for offset in (-0.22, 0.05, 0.30):
            draw.arc(
                _box(
                    cx - s * 0.48,
                    cy + offset * s - s * 0.18,
                    cx + s * 0.45,
                    cy + offset * s + s * 0.18,
                ),
                180,
                345,
                fill=primary,
                width=max(3, round(s * 0.065)),
            )
        return

    if kind == "question":
        font = _font(round(s * 0.90), bold=True)
        _center_text(draw, "?", (cx, cy), font, primary)
        return

    raise ValueError(f"Unsupported visual token: {token}")


def _bear_pose(scene: Scene) -> str:
    kinds = {_semantic_kind(token) for token in scene.visual_tokens}
    if scene.primitive is ScenePrimitive.QUESTION and kinds & {"stone", "lifted-stone"}:
        return "discover"
    if scene.primitive is ScenePrimitive.PREDICTION:
        return "think"
    if scene.primitive in {ScenePrimitive.CAUSE_EFFECT, ScenePrimitive.FLOW, ScenePrimitive.RECAP}:
        return "explain"
    return "inspect"


def _fade_through_blank(
    prior: Image.Image,
    current: Image.Image,
    blank: Image.Image,
    progress: float,
) -> Image.Image:
    progress = max(0.0, min(1.0, progress))
    if progress <= 0.5:
        return Image.blend(prior, blank, _ease_out(progress * 2))
    return Image.blend(blank, current, _ease_out((progress - 0.5) * 2))


def _ease_out(value: float) -> float:
    value = max(0.0, min(1.0, value))
    return 1 - (1 - value) ** 3


def _scene_at(moment: float, durations: Sequence[float]) -> tuple[int, float]:
    start = 0.0
    for index, duration in enumerate(durations):
        if moment < start + duration or index == len(durations) - 1:
            return index, start
        start += duration
    return len(durations) - 1, start - durations[-1]


def _particle_positions(seed: str, count: int) -> list[tuple[float, float, float]]:
    value = int(hashlib.sha256(seed.encode()).hexdigest()[:8], 16)
    rng = np.random.default_rng(value)
    return [tuple(float(item) for item in rng.random(3)) for _ in range(count)]


def _font(size: int, *, bold: bool) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = (
        [
            "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        ]
        if bold
        else [
            "/System/Library/Fonts/Avenir Next.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]
    )
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, max(10, size))
    return ImageFont.load_default(size=max(10, size))


SCHOOL_FONT = (
    Path(__file__).resolve().parents[2]
    / "assets/fonts/berner-basisschrift/berner-basisschrift.basisschrift1.ttf"
)


def school_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Deutschschweizer Basisschrift for child-facing words: unjoined, curved l.

    It has a single weight, so callers ask for a larger size than they would of
    the bold brand face. The brand wordmark deliberately keeps its own font.
    """
    if SCHOOL_FONT.exists():
        return ImageFont.truetype(str(SCHOOL_FONT), max(10, size))
    return _font(size, bold=True)


def available_font_paths() -> tuple[Path | None, Path | None]:
    regular_candidates = (
        Path("/System/Library/Fonts/Avenir Next.ttc"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
    )
    bold_candidates = (
        Path("/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf"),
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"),
    )
    regular = next((path for path in regular_candidates if path.exists()), None)
    bold = next((path for path in bold_candidates if path.exists()), None)
    return regular, bold


def _fit_text(text: str, font: ImageFont.ImageFont, *, max_width: int, max_lines: int) -> str:
    words = text.split()
    if not words:
        return ""
    probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if probe.textbbox((0, 0), candidate, font=font)[2] <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    if len(lines) > max_lines:
        retained = lines[: max_lines - 1]
        retained.append(" ".join(lines[max_lines - 1 :]))
        lines = retained
    return "\n".join(lines)


def _centered_multiline(
    draw: ImageDraw.ImageDraw,
    text: str,
    box: tuple[int, int, int, int],
    font: ImageFont.ImageFont,
    fill: Color,
    *,
    spacing: int,
    stroke: int = 0,
) -> None:
    """`stroke` thickens the pen without distorting the letterform, for single-weight faces."""
    bounds = draw.multiline_textbbox(
        (0, 0), text, font=font, align="center", spacing=spacing, stroke_width=stroke
    )
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    x = box[0] + (box[2] - box[0] - width) / 2
    y = box[1] + (box[3] - box[1] - height) / 2 - bounds[1]
    draw.multiline_text(
        (x, y),
        text,
        font=font,
        fill=fill,
        align="center",
        spacing=spacing,
        stroke_width=stroke,
        stroke_fill=fill,
    )


def _center_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    center: tuple[float, float],
    font: ImageFont.ImageFont,
    fill: Color,
) -> None:
    bounds = draw.textbbox((0, 0), text, font=font)
    width = bounds[2] - bounds[0]
    height = bounds[3] - bounds[1]
    draw.text(
        (center[0] - width / 2, center[1] - height / 2 - bounds[1]), text, font=font, fill=fill
    )


def _rounded_with_shadow(
    draw: ImageDraw.ImageDraw,
    box: tuple[int, int, int, int],
    radius: int,
    fill: Color,
    *,
    shadow: int,
) -> None:
    shadow_box = (box[0] + shadow, box[1] + shadow, box[2] + shadow, box[3] + shadow)
    draw.rounded_rectangle(shadow_box, radius=radius, fill=(197, 180, 151))
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def _ellipse_shadow(
    draw: ImageDraw.ImageDraw, box: tuple[int, int, int, int], fill: Color, shadow: float
) -> None:
    offset = int(shadow)
    draw.ellipse(
        (box[0] + offset, box[1] + offset, box[2] + offset, box[3] + offset), fill=(197, 180, 151)
    )
    draw.ellipse(box, fill=fill)


def _arrow(
    draw: ImageDraw.ImageDraw,
    start: tuple[float, float],
    end: tuple[float, float],
    color: Color,
    width: int,
) -> None:
    draw.line((start, end), fill=color, width=width)
    angle = math.atan2(end[1] - start[1], end[0] - start[0])
    head = width * 2.1
    points = [
        end,
        (end[0] - head * math.cos(angle - 0.65), end[1] - head * math.sin(angle - 0.65)),
        (end[0] - head * math.cos(angle + 0.65), end[1] - head * math.sin(angle + 0.65)),
    ]
    draw.polygon(points, fill=color)


def _mix(first: Color, second: Color, ratio: float) -> Color:
    return tuple(round(a * (1 - ratio) + b * ratio) for a, b in zip(first, second, strict=True))


def _box(x1: float, y1: float, x2: float, y2: float) -> tuple[int, int, int, int]:
    return round(x1), round(y1), round(x2), round(y2)


def _center(box: tuple[int, int, int, int]) -> tuple[float, float]:
    return (box[0] + box[2]) / 2, (box[1] + box[3]) / 2
