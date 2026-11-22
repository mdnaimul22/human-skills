"""
Pydantic models for all job types across the 6 services.
This is the single source of truth for request/response contracts.
"""

from __future__ import annotations

import enum
import uuid
from datetime import datetime
from typing import Optional, Any

from pydantic import BaseModel, Field, field_validator
from src.helpers import ValidationError


# ─── Enums ───────────────────────────────────────────────────────────

class JobStatus(str, enum.Enum):
    RECEIVED = "received"
    VALIDATED = "validated"
    QUEUED = "queued"
    LEASING = "leasing"
    PROCESSING = "processing"
    DRAINING = "draining"
    COMMITTING = "committing"
    COMPLETE = "complete"
    FAILED = "failed"
    TIMEOUT = "timeout"
    TOMBSTONE = "tombstone"
    PURGED = "purged"


class VideoFormat(str, enum.Enum):
    MP4_H264 = "mp4"
    MP4_H265 = "mp4_h265"
    WEBM = "webm"
    MOV = "mov"
    MKV = "mkv"
    AVI = "avi"


class AudioFormat(str, enum.Enum):
    WAV = "wav"
    WAV_24 = "wav_24"
    WAV_32 = "wav_32"
    FLAC = "flac"
    FLAC_24 = "flac_24"
    MP3_320 = "mp3"
    OGG = "ogg"
    OPUS = "opus"
    M4A = "m4a"


class VideoQuality(str, enum.Enum):
    Q360 = "360"
    Q720 = "720"
    Q1080 = "1080"
    Q4K = "2160"


class CropMode(str, enum.Enum):
    CENTER = "center"
    FACE = "face"


class SubtitleFormat(str, enum.Enum):
    NONE = "none"
    SRT = "srt"
    VTT = "vtt"


# ─── Shared ──────────────────────────────────────────────────────────

def _gen_job_id() -> str:
    return uuid.uuid4().hex[:12]


class JobResponse(BaseModel):
    """Standard response returned when a job is submitted."""
    job_id: str
    status: JobStatus = JobStatus.RECEIVED
    message: str = "Job received"


class JobProgress(BaseModel):
    job_id: str
    status: JobStatus
    progress: int = Field(default=0, ge=0, le=100)
    message: str = ""
    download_url: Optional[str] = None
    error: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None
    tombstone_until: Optional[float] = None
    generation_id: int = 0


class HealthResponse(BaseModel):
    status: str = "ok"
    active_jobs: int = 0
    version: str = "1.0.0"


# ─── Service 1: Time-range Download ─────────────────────────────────

class TimeCut(BaseModel):
    start_time: str
    end_time: str

class TimeRangeRequest(BaseModel):
    url: str
    cuts: list[TimeCut] | None = None
    start_time: str | None = None
    end_time: str | None = None
    format: VideoFormat = VideoFormat.MP4_H264
    quality: VideoQuality = VideoQuality.Q1080
    aspect_ratio: str = "original"
    subtitles: SubtitleFormat = SubtitleFormat.NONE

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValidationError("URL cannot be empty")
        return v

    @field_validator("start_time", "end_time", mode="before")
    @classmethod
    def normalize_empty_time(cls, v: Any) -> str | None:
        if isinstance(v, str):
            clean = v.strip()
            return clean if clean else None
        return v


# ─── Service 2: Lossless Audio Extract ──────────────────────────────

class AudioExtractRequest(BaseModel):
    url: str
    format: AudioFormat = AudioFormat.FLAC

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValidationError("URL cannot be empty")
        return v


class AudioExtractResponse(JobResponse):
    estimated_size_mb: Optional[float] = None
    waveform_url: Optional[str] = None


class AudioPreviewRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValidationError("URL cannot be empty")
        return v


class AudioStreamInfo(BaseModel):
    format_id: str
    codec: str
    ext: str
    bitrate_kbps: Optional[int] = None
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    filesize_mb: Optional[float] = None


class AudioPreviewResponse(BaseModel):
    title: str
    url: str
    duration_seconds: float
    quality_rating: str
    best_audio: Optional[AudioStreamInfo] = None
    available_streams: list[AudioStreamInfo]
    recommendation: str


# ─── Service 7: Format Check ────────────────────────────────────────

class FormatCheckRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValidationError("URL cannot be empty")
        return v


class FormatRecommendation(BaseModel):
    video: Optional[str] = None
    reason: str
    codec: Optional[str] = None
    resolution: Optional[str] = None


class StreamFormatInfo(BaseModel):
    format_id: str
    ext: str
    resolution: str
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    vcodec: Optional[str] = None
    acodec: Optional[str] = None
    filesize_mb: Optional[float] = None
    tbr_kbps: Optional[int] = None
    nle_support: list[str]


class FormatCheckResponse(BaseModel):
    title: str
    url: str
    duration_seconds: float
    total_formats: int
    recommendation: FormatRecommendation
    combined: list[StreamFormatInfo]
    video_streams: list[StreamFormatInfo]
    audio_streams: list[StreamFormatInfo]


# ─── Service 3: Chapter-wise Download ───────────────────────────────

class ChapterInfo(BaseModel):
    title: str
    start_time: float
    end_time: float
    duration: float


class ChapterInfoRequest(BaseModel):
    url: str

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValidationError("URL cannot be empty")
        return v


class ChapterInfoResponse(BaseModel):
    url: str
    title: str
    chapters: list[ChapterInfo]
    total_duration: float


class ChapterDownloadRequest(BaseModel):
    url: str
    chapter_indices: list[int] = Field(min_length=1)
    format: VideoFormat = VideoFormat.MP4_H264
    quality: VideoQuality = VideoQuality.Q1080

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValidationError("URL cannot be empty")
        return v


# ─── Service 4: Batch Download ──────────────────────────────────────

class BatchDownloadRequest(BaseModel):
    urls: list[str] = Field(min_length=1, max_length=20)
    format: VideoFormat = VideoFormat.MP4_H264
    quality: VideoQuality = VideoQuality.Q1080

    @field_validator("urls")
    @classmethod
    def validate_urls(cls, v: list[str]) -> list[str]:
        return [u.strip() for u in v if u.strip()]


class BatchValidationResult(BaseModel):
    valid_urls: list[str]
    invalid_urls: list[str]


# ─── Service 5: Thumbnail Gallery ───────────────────────────────────

class ThumbnailRequest(BaseModel):
    channel_url: str

    @field_validator("channel_url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValidationError("Channel URL cannot be empty")
        return v


class ThumbnailEntry(BaseModel):
    video_id: str
    title: str
    view_count: int = 0
    upload_date: Optional[str] = None
    thumbnail_url: str
    video_url: str


class ThumbnailResponse(BaseModel):
    channel_name: str
    channel_url: str
    total_videos: int
    thumbnails: list[ThumbnailEntry]


# ─── Service 6: Shorts-ready Crop ───────────────────────────────────

class ShortsCropRequest(BaseModel):
    url: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    crop_mode: CropMode = CropMode.CENTER
    crop_x_offset: float = Field(default=0.0, ge=-1.0, le=1.0)
    aspect_ratio: str = Field(default="9:16")
    smoothing_algorithm: str = Field(default="kalman")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValidationError("URL cannot be empty")
        return v

    @field_validator("aspect_ratio")
    @classmethod
    def validate_aspect_ratio(cls, v: str) -> str:
        if v not in ["9:16", "1:1", "4:5"]:
            raise ValidationError("aspect_ratio must be one of '9:16', '1:1', '4:5'")
        return v

    @field_validator("smoothing_algorithm")
    @classmethod
    def validate_smoothing_algorithm(cls, v: str) -> str:
        if v not in ["kalman", "moving_average"]:
            raise ValidationError("smoothing_algorithm must be one of 'kalman', 'moving_average'")
        return v


class ShortsCropPreviewRequest(BaseModel):
    """Request a quick ~4s animated preview of the crop result."""
    url: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    crop_mode: CropMode = CropMode.CENTER
    crop_x_offset: float = Field(default=0.0, ge=-1.0, le=1.0)
    aspect_ratio: str = Field(default="9:16")
    smoothing_algorithm: str = Field(default="kalman")

    @field_validator("url")
    @classmethod
    def validate_url(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValidationError("URL cannot be empty")
        return v

    @field_validator("aspect_ratio")
    @classmethod
    def validate_aspect_ratio(cls, v: str) -> str:
        if v not in ["9:16", "1:1", "4:5"]:
            raise ValidationError("aspect_ratio must be one of '9:16', '1:1', '4:5'")
        return v

    @field_validator("smoothing_algorithm")
    @classmethod
    def validate_smoothing_algorithm(cls, v: str) -> str:
        if v not in ["kalman", "moving_average"]:
            raise ValidationError("smoothing_algorithm must be one of 'kalman', 'moving_average'")
        return v
