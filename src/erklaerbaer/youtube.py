from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import DEFAULT_ENV_PATH, Settings
from .errors import ConfigurationError, ExternalServiceError
from .models import Language, Storyboard

YOUTUBE_SCOPE = "https://www.googleapis.com/auth/youtube.force-ssl"
TOKEN_URI = "https://oauth2.googleapis.com/token"


@dataclass(frozen=True)
class UploadResult:
    youtube_id: str
    recovered: bool


def content_marker(storyboard: Storyboard, build: str | None = None) -> str:
    """Identify one uploaded cut. Recovery matches on it, so a new render needs a new marker.

    Without the build, two different renders of the same script share an identity and the
    second one silently recovers the first instead of uploading.
    """
    suffix = f"|{build}" if build else ""
    return (
        f"[ERKLAERBAER:{storyboard.experiment_id}|{storyboard.language.value}|"
        f"{storyboard.source_hash}|{storyboard.template_version}{suffix}]"
    )


def build_description(storyboard: Storyboard, disclosure: str, marker: str, phrase: str) -> str:
    """Script description, the voice disclosure and the recovery marker, each said once.

    The writer often discloses the synthetic voice in its own words, so matching the exact
    configured sentence is not enough; the phrase that carries the meaning is what counts.
    """
    body = storyboard.youtube.description.rstrip()
    parts = [body]
    if phrase.lower() not in body.lower():
        parts.append(disclosure)
    if marker:
        parts.append(marker)
    return "\n\n".join(parts)


def standard_snippet(settings: Settings, storyboard: Storyboard) -> dict[str, Any]:
    """Snippet fields every episode carries, so no upload depends on the Studio defaults."""
    youtube = settings.section("youtube")
    return {
        "categoryId": str(youtube["category_id"]),
        "defaultLanguage": storyboard.language.value,
        "defaultAudioLanguage": storyboard.language.value,
    }


def standard_status(settings: Settings) -> dict[str, Any]:
    youtube = settings.section("youtube")
    return {
        "selfDeclaredMadeForKids": bool(youtube["made_for_kids"]),
        "license": str(youtube["license"]),
        "embeddable": bool(youtube["embeddable"]),
        "containsSyntheticMedia": bool(youtube["contains_synthetic_media"]),
    }


class YouTubeClient:
    def __init__(self, settings: Settings, service: Any | None = None) -> None:
        self.settings = settings
        self._service = service
        self.thumbnail_error: str | None = None
        self.processing_status: str | None = None

    @property
    def service(self) -> Any:
        if self._service is None:
            self._service = _authenticated_service(self.settings)
        return self._service

    def own_channel(self) -> dict[str, Any]:
        response = (
            self.service.channels()
            .list(part="id,snippet,contentDetails", mine=True, maxResults=1)
            .execute()
        )
        items = response.get("items", [])
        if len(items) != 1:
            raise ExternalServiceError("OAuth account has no unambiguous YouTube channel")
        return items[0]

    def find_by_marker(self, marker: str) -> str | None:
        channel = self.own_channel()
        uploads_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]
        token: str | None = None
        inspected = 0
        while inspected < 250:
            response = (
                self.service.playlistItems()
                .list(
                    part="contentDetails",
                    playlistId=uploads_id,
                    maxResults=50,
                    pageToken=token,
                )
                .execute()
            )
            video_ids = [item["contentDetails"]["videoId"] for item in response.get("items", [])]
            inspected += len(video_ids)
            if video_ids:
                videos = (
                    self.service.videos()
                    .list(part="snippet", id=",".join(video_ids), maxResults=50)
                    .execute()
                )
                for video in videos.get("items", []):
                    if marker in video.get("snippet", {}).get("description", ""):
                        return str(video["id"])
            token = response.get("nextPageToken")
            if not token:
                return None
        return None

    def upload_private(
        self,
        storyboard: Storyboard,
        video_path: Path,
        captions_path: Path,
        thumbnail_path: Path,
        build: str | None = None,
    ) -> UploadResult:
        if self.settings.dry_run:
            raise ExternalServiceError("Dry run: upload validated; no YouTube call was made")
        marker = content_marker(storyboard, build)
        recovered_id = self.find_by_marker(marker)
        if recovered_id:
            self._ensure_post_upload_assets(
                recovered_id,
                storyboard,
                captions_path,
                thumbnail_path,
            )
            return UploadResult(youtube_id=recovered_id, recovered=True)

        try:
            from googleapiclient.http import MediaFileUpload
        except ImportError as exc:
            raise ExternalServiceError("Google API Python client is not installed") from exc
        youtube = self.settings.section("youtube")
        german = storyboard.language is Language.GERMAN
        description = build_description(
            storyboard,
            str(youtube["ai_voice_disclosure_de" if german else "ai_voice_disclosure_nl"]),
            marker,
            str(youtube["ai_voice_phrase_de" if german else "ai_voice_phrase_nl"]),
        )
        body = {
            "snippet": {
                "title": storyboard.youtube.title,
                "description": description,
                "tags": storyboard.youtube.tags,
                **standard_snippet(self.settings, storyboard),
            },
            "status": {
                "privacyStatus": "private",
                **standard_status(self.settings),
            },
        }
        try:
            response = (
                self.service.videos()
                .insert(
                    part="snippet,status",
                    body=body,
                    notifySubscribers=False,
                    media_body=MediaFileUpload(
                        str(video_path),
                        mimetype="video/mp4",
                        chunksize=8 * 1024 * 1024,
                        resumable=True,
                    ),
                )
                .execute()
            )
            youtube_id = str(response["id"])
            self.processing_status = self.wait_until_processed(youtube_id)
            self._ensure_post_upload_assets(
                youtube_id,
                storyboard,
                captions_path,
                thumbnail_path,
            )
        except Exception as exc:  # normalize provider and resumable-upload failures
            raise ExternalServiceError(f"YouTube upload failed: {type(exc).__name__}") from exc
        return UploadResult(youtube_id=youtube_id, recovered=False)

    def wait_until_processed(self, youtube_id: str, timeout: float = 900.0) -> str:
        """Block until YouTube has finished processing the upload.

        Captions and thumbnails are rejected with a not-found error while a fresh upload is
        still processing, which used to fail the run after the file was already on the
        channel.
        """
        deadline = time.monotonic() + timeout
        while True:
            response = self.service.videos().list(part="processingDetails", id=youtube_id).execute()
            items = response.get("items", [])
            if not items:
                raise ExternalServiceError(f"Video {youtube_id} not found on this account")
            status = items[0].get("processingDetails", {}).get("processingStatus", "unknown")
            if status != "processing" or time.monotonic() > deadline:
                return status
            time.sleep(15)

    def apply_standard_settings(self, youtube_id: str, storyboard: Storyboard) -> dict[str, Any]:
        """Bring an already uploaded video up to the standing settings, privacy untouched.

        `videos.update` replaces whole parts, so the current snippet and status are read
        first and only the fields this project owns are overwritten.
        """
        response = self.service.videos().list(part="snippet,status", id=youtube_id).execute()
        items = response.get("items", [])
        if len(items) != 1:
            raise ExternalServiceError(f"Video {youtube_id} not found on this account")
        snippet = dict(items[0]["snippet"])
        status = dict(items[0]["status"])
        marker = next(
            (
                line
                for line in snippet.get("description", "").splitlines()
                if line.startswith("[ERKLAERBAER:")
            ),
            "",
        )
        youtube = self.settings.section("youtube")
        german = storyboard.language is Language.GERMAN
        snippet["description"] = build_description(
            storyboard,
            str(youtube["ai_voice_disclosure_de" if german else "ai_voice_disclosure_nl"]),
            marker,
            str(youtube["ai_voice_phrase_de" if german else "ai_voice_phrase_nl"]),
        ).rstrip()
        snippet.update(standard_snippet(self.settings, storyboard))
        status.update(standard_status(self.settings))
        updated = (
            self.service.videos()
            .update(
                part="snippet,status", body={"id": youtube_id, "snippet": snippet, "status": status}
            )
            .execute()
        )
        return {
            "privacy": updated["status"]["privacyStatus"],
            "license": updated["status"].get("license"),
            "embeddable": updated["status"].get("embeddable"),
            "made_for_kids": updated["status"].get("madeForKids"),
            "category_id": updated["snippet"].get("categoryId"),
            "language": updated["snippet"].get("defaultLanguage"),
            "audio_language": updated["snippet"].get("defaultAudioLanguage"),
            "description": updated["snippet"].get("description"),
        }

    def privacy_status(self, youtube_id: str) -> str:
        response = self.service.videos().list(part="status", id=youtube_id).execute()
        items = response.get("items", [])
        if len(items) != 1:
            raise ExternalServiceError("YouTube video was not found")
        return str(items[0]["status"]["privacyStatus"])

    def make_public(self, youtube_id: str) -> None:
        if self.settings.dry_run:
            raise ExternalServiceError("Dry run: release validated; no YouTube call was made")
        if os.getenv("YOUTUBE_API_AUDIT_COMPLETE", "false").lower() != "true":
            raise ConfigurationError("YOUTUBE_API_AUDIT_COMPLETE must be true before release")
        self.service.videos().update(
            part="status",
            body={
                "id": youtube_id,
                "status": {
                    "privacyStatus": "public",
                    "selfDeclaredMadeForKids": True,
                },
            },
        ).execute()

    def _ensure_post_upload_assets(
        self,
        youtube_id: str,
        storyboard: Storyboard,
        captions_path: Path,
        thumbnail_path: Path,
    ) -> None:
        try:
            from googleapiclient.http import MediaFileUpload
        except ImportError as exc:
            raise ExternalServiceError("Google API Python client is not installed") from exc
        caption_name = f"ErklaerBaer {storyboard.language.value}"
        captions = self.service.captions().list(part="snippet", videoId=youtube_id).execute()
        has_caption = any(
            item.get("snippet", {}).get("language") == storyboard.language.value
            and item.get("snippet", {}).get("name") == caption_name
            for item in captions.get("items", [])
        )
        if not has_caption:
            self.service.captions().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": youtube_id,
                        "language": storyboard.language.value,
                        "name": caption_name,
                        "isDraft": False,
                    }
                },
                media_body=MediaFileUpload(str(captions_path), mimetype="application/x-subrip"),
            ).execute()
        try:
            self.service.thumbnails().set(
                videoId=youtube_id,
                media_body=MediaFileUpload(str(thumbnail_path), mimetype="image/jpeg"),
            ).execute()
        except Exception as exc:  # a channel without phone verification cannot set one
            self.thumbnail_error = f"{type(exc).__name__}"
        playlist_id = self._playlist_id(storyboard.language)
        if not self._playlist_contains(playlist_id, youtube_id):
            self.service.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {"kind": "youtube#video", "videoId": youtube_id},
                    }
                },
            ).execute()

    def _playlist_id(self, language: Language) -> str:
        variable = (
            "YOUTUBE_PLAYLIST_DE_ID" if language is Language.GERMAN else "YOUTUBE_PLAYLIST_NL_ID"
        )
        return self.settings.required_env(variable)[variable]

    def _playlist_contains(self, playlist_id: str, youtube_id: str) -> bool:
        token: str | None = None
        while True:
            response = (
                self.service.playlistItems()
                .list(
                    part="contentDetails",
                    playlistId=playlist_id,
                    videoId=youtube_id,
                    maxResults=50,
                    pageToken=token,
                )
                .execute()
            )
            if response.get("items"):
                return True
            token = response.get("nextPageToken")
            if not token:
                return False


def setup_youtube(settings: Settings, env_path: Path = DEFAULT_ENV_PATH) -> dict[str, str]:
    if settings.dry_run:
        raise ExternalServiceError("Set DRY_RUN=false before starting interactive OAuth")
    env = settings.required_env("YOUTUBE_CLIENT_ID", "YOUTUBE_CLIENT_SECRET")
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise ExternalServiceError("Google OAuth libraries are not installed") from exc
    client_config = {
        "installed": {
            "client_id": env["YOUTUBE_CLIENT_ID"],
            "client_secret": env["YOUTUBE_CLIENT_SECRET"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": TOKEN_URI,
            "redirect_uris": ["http://localhost"],
        }
    }
    flow = InstalledAppFlow.from_client_config(client_config, scopes=[YOUTUBE_SCOPE])
    credentials = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    if not credentials.refresh_token:
        raise ExternalServiceError("Google did not return a refresh token; revoke access and retry")
    service = build("youtube", "v3", credentials=credentials, cache_discovery=False)
    client = YouTubeClient(settings, service=service)
    channel = client.own_channel()
    channel_id = str(channel["id"])
    channel_title = str(channel.get("snippet", {}).get("title", channel_id))
    answer = input(f"Use YouTube channel '{channel_title}' ({channel_id})? Type YES: ").strip()
    if answer != "YES":
        raise ExternalServiceError("YouTube setup cancelled; .env was not changed")
    youtube_settings = settings.section("youtube")
    de_playlist = _find_or_create_playlist(
        service,
        str(youtube_settings["german_playlist_name"]),
        str(youtube_settings["playlist_privacy"]),
    )
    nl_playlist = _find_or_create_playlist(
        service,
        str(youtube_settings["dutch_playlist_name"]),
        str(youtube_settings["playlist_privacy"]),
    )
    values = {
        "YOUTUBE_REFRESH_TOKEN": credentials.refresh_token,
        "YOUTUBE_CHANNEL_ID": channel_id,
        "YOUTUBE_PLAYLIST_DE_ID": de_playlist,
        "YOUTUBE_PLAYLIST_NL_ID": nl_playlist,
    }
    update_env_file(env_path, values)
    return {key: "saved" for key in values}


def update_env_file(path: Path, values: dict[str, str]) -> None:
    """Persist setup output without returning or logging secret values."""
    if not path.exists():
        raise ConfigurationError(f"Environment file not found: {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    found: set[str] = set()
    updated: list[str] = []
    for line in lines:
        if "=" in line and not line.lstrip().startswith("#"):
            key = line.split("=", 1)[0].strip()
            if key in values:
                updated.append(f"{key}={json.dumps(values[key])}")
                found.add(key)
                continue
        updated.append(line)
    for key in values.keys() - found:
        updated.append(f"{key}={json.dumps(values[key])}")
    path.write_text("\n".join(updated) + "\n", encoding="utf-8")


def _authenticated_service(settings: Settings) -> Any:
    env = settings.required_env(
        "YOUTUBE_CLIENT_ID",
        "YOUTUBE_CLIENT_SECRET",
        "YOUTUBE_REFRESH_TOKEN",
    )
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
    except ImportError as exc:
        raise ExternalServiceError("Google YouTube client libraries are not installed") from exc
    credentials = Credentials(
        token=None,
        refresh_token=env["YOUTUBE_REFRESH_TOKEN"],
        token_uri=TOKEN_URI,
        client_id=env["YOUTUBE_CLIENT_ID"],
        client_secret=env["YOUTUBE_CLIENT_SECRET"],
        scopes=[YOUTUBE_SCOPE],
    )
    try:
        credentials.refresh(Request())
        return build("youtube", "v3", credentials=credentials, cache_discovery=False)
    except Exception as exc:  # normalize OAuth refresh and discovery failures
        raise ExternalServiceError(f"YouTube authentication failed: {type(exc).__name__}") from exc


def _find_or_create_playlist(service: Any, title: str, privacy: str) -> str:
    if privacy not in {"private", "unlisted", "public"}:
        raise ConfigurationError("Invalid playlist privacy")
    token: str | None = None
    while True:
        response = (
            service.playlists()
            .list(part="id,snippet", mine=True, maxResults=50, pageToken=token)
            .execute()
        )
        for item in response.get("items", []):
            if item.get("snippet", {}).get("title") == title:
                return str(item["id"])
        token = response.get("nextPageToken")
        if not token:
            break
    response = (
        service.playlists()
        .insert(
            part="snippet,status",
            body={
                "snippet": {"title": title, "description": "ErklaerBaer science explanations"},
                "status": {"privacyStatus": privacy},
            },
        )
        .execute()
    )
    return str(response["id"])
