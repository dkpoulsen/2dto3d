"""Video metadata dataclass for storing extracted video information.

This module provides comprehensive metadata handling including:
- Basic video metadata (resolution, fps, codec, duration)
- EXIF metadata (camera settings, GPS, timestamps)
- IPTC metadata (title, description, keywords, copyright)
- XMP metadata (custom namespaces, Dublin Core)
- Custom fields (application-specific metadata)
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from video2d3d.utils.logger import get_logger


@dataclass
class VideoMetadata:
    """
    Metadata extracted from a video file.

    Contains all essential information about a video needed for processing,
    including resolution, frame rate, codec, duration, and file details.

    Attributes:
        file_path: Path to the video file.
        width: Video width in pixels.
        height: Video height in pixels.
        fps: Frames per second.
        frame_count: Total number of frames in the video.
        duration: Video duration in seconds.
        codec: Video codec name (e.g., 'h264', 'hevc').
        format: Container format (e.g., 'mp4', 'avi').
        bitrate: Video bitrate in bits per second.
        has_audio: Whether the video contains an audio stream.
        audio_codec: Audio codec name if audio is present.
        audio_sample_rate: Audio sample rate in Hz.
        audio_channels: Number of audio channels.
        file_size: File size in bytes.
        is_valid: Whether the video passed validation.
        validation_errors: List of validation errors if any.
    """

    file_path: Path
    width: int = 0
    height: int = 0
    fps: float = 0.0
    frame_count: int = 0
    duration: float = 0.0
    codec: str = ""
    format: str = ""
    bitrate: int = 0
    has_audio: bool = False
    audio_codec: str = ""
    audio_sample_rate: int = 0
    audio_channels: int = 0
    file_size: int = 0
    is_valid: bool = True
    validation_errors: list[str] = field(default_factory=list)

    @property
    def resolution(self) -> tuple[int, int]:
        """Return video resolution as (width, height) tuple."""
        return (self.width, self.height)

    @property
    def aspect_ratio(self) -> float:
        """Calculate and return the aspect ratio."""
        if self.height == 0:
            return 0.0
        return self.width / self.height

    @property
    def duration_formatted(self) -> str:
        """Return duration in HH:MM:SS format."""
        hours = int(self.duration // 3600)
        minutes = int((self.duration % 3600) // 60)
        seconds = int(self.duration % 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    @property
    def file_size_mb(self) -> float:
        """Return file size in megabytes."""
        return self.file_size / (1024 * 1024)

    @property
    def is_4k(self) -> bool:
        """Check if video is 4K resolution (3840x2160 or higher)."""
        return self.width >= 3840 and self.height >= 2160

    @property
    def is_hd(self) -> bool:
        """Check if video is HD resolution (1280x720 or higher)."""
        return self.width >= 1280 and self.height >= 720

    @property
    def is_full_hd(self) -> bool:
        """Check if video is Full HD resolution (1920x1080 or higher)."""
        return self.width >= 1920 and self.height >= 1080

    def __str__(self) -> str:
        """Return a human-readable string representation."""
        parts = [
            f"Video: {self.file_path.name}",
            f"Resolution: {self.width}x{self.height}",
            f"FPS: {self.fps:.2f}",
            f"Duration: {self.duration_formatted}",
            f"Codec: {self.codec or 'unknown'}",
            f"Format: {self.format or 'unknown'}",
        ]
        if self.has_audio:
            parts.append(f"Audio: {self.audio_codec or 'unknown'}")
        return " | ".join(parts)


def _get_video_metadata_logger():
    """Get the video metadata logger (lazy initialization)."""
    return get_logger("video.metadata")


@dataclass
class ExifMetadata:
    """EXIF metadata extracted from video or embedded images.

    EXIF (Exchangeable Image File Format) metadata contains camera
    settings, timestamps, and GPS information.

    Attributes:
        make: Camera/device manufacturer.
        model: Camera/device model.
        software: Software used to create/process the video.
        datetime_original: Original capture date/time.
        datetime_modified: Last modification date/time.
        exposure_time: Exposure time in seconds.
        f_number: F-number (aperture).
        iso_speed: ISO speed rating.
        focal_length: Focal length in mm.
        gps_latitude: GPS latitude coordinate.
        gps_longitude: GPS longitude coordinate.
        gps_altitude: GPS altitude in meters.
        orientation: Image orientation (1-8).
        x_resolution: Horizontal resolution in DPI.
        y_resolution: Vertical resolution in DPI.
        color_space: Color space identifier.
        custom_tags: Additional EXIF tags not covered by standard fields.
    """

    make: str = ""
    model: str = ""
    software: str = ""
    datetime_original: datetime | None = None
    datetime_modified: datetime | None = None
    exposure_time: float | None = None
    f_number: float | None = None
    iso_speed: int | None = None
    focal_length: float | None = None
    gps_latitude: float | None = None
    gps_longitude: float | None = None
    gps_altitude: float | None = None
    orientation: int = 1
    x_resolution: float | None = None
    y_resolution: float | None = None
    color_space: str = "sRGB"
    custom_tags: dict[str, Any] = field(default_factory=dict)

    @property
    def has_gps(self) -> bool:
        """Check if GPS coordinates are available."""
        return self.gps_latitude is not None and self.gps_longitude is not None

    @property
    def exposure_formatted(self) -> str:
        """Return formatted exposure time."""
        if self.exposure_time is None:
            return "unknown"
        if self.exposure_time >= 1:
            return f"{self.exposure_time:.1f}s"
        return f"1/{int(1/self.exposure_time)}s"

    @property
    def aperture_formatted(self) -> str:
        """Return formatted aperture value."""
        if self.f_number is None:
            return "unknown"
        return f"f/{self.f_number:.1f}"

    @property
    def gps_coordinates(self) -> tuple[float, float] | None:
        """Return GPS coordinates as (lat, lon) tuple."""
        if self.has_gps:
            return (self.gps_latitude, self.gps_longitude)
        return None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "make": self.make,
            "model": self.model,
            "software": self.software,
            "datetime_original": (
                self.datetime_original.isoformat() if self.datetime_original else None
            ),
            "datetime_modified": (
                self.datetime_modified.isoformat() if self.datetime_modified else None
            ),
            "exposure_time": self.exposure_time,
            "exposure_formatted": self.exposure_formatted,
            "f_number": self.f_number,
            "aperture_formatted": self.aperture_formatted,
            "iso_speed": self.iso_speed,
            "focal_length": self.focal_length,
            "gps_latitude": self.gps_latitude,
            "gps_longitude": self.gps_longitude,
            "gps_altitude": self.gps_altitude,
            "has_gps": self.has_gps,
            "gps_coordinates": self.gps_coordinates,
            "orientation": self.orientation,
            "x_resolution": self.x_resolution,
            "y_resolution": self.y_resolution,
            "color_space": self.color_space,
            "custom_tags": self.custom_tags,
        }


@dataclass
class IptcMetadata:
    """IPTC metadata for video content.

    IPTC (International Press Telecommunications Council) metadata
    contains descriptive information about the content.

    Attributes:
        title: Content title/headline.
        description: Content description/caption.
        keywords: List of keywords/tags.
        copyright: Copyright notice.
        creator: Creator/author name.
        credit: Credit line.
        source: Source of the content.
        city: City where content was created.
        country: Country where content was created.
        location: Full location string.
        date_created: Creation date.
        category: IPTC category code.
        supplemental_categories: Additional category codes.
        urgency: Editorial urgency (1-8).
        custom_fields: Additional IPTC fields.
    """

    title: str = ""
    description: str = ""
    keywords: list[str] = field(default_factory=list)
    copyright: str = ""
    creator: str = ""
    credit: str = ""
    source: str = ""
    city: str = ""
    country: str = ""
    location: str = ""
    date_created: datetime | None = None
    category: str = ""
    supplemental_categories: list[str] = field(default_factory=list)
    urgency: int = 5
    custom_fields: dict[str, str] = field(default_factory=dict)

    @property
    def has_keywords(self) -> bool:
        """Check if keywords are available."""
        return len(self.keywords) > 0

    @property
    def keywords_str(self) -> str:
        """Return keywords as comma-separated string."""
        return ", ".join(self.keywords)

    @property
    def has_location(self) -> bool:
        """Check if location information is available."""
        return bool(self.city or self.country or self.location)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "title": self.title,
            "description": self.description,
            "keywords": self.keywords,
            "keywords_str": self.keywords_str,
            "copyright": self.copyright,
            "creator": self.creator,
            "credit": self.credit,
            "source": self.source,
            "city": self.city,
            "country": self.country,
            "location": self.location,
            "has_location": self.has_location,
            "date_created": self.date_created.isoformat() if self.date_created else None,
            "category": self.category,
            "supplemental_categories": self.supplemental_categories,
            "urgency": self.urgency,
            "custom_fields": self.custom_fields,
        }


@dataclass
class XmpMetadata:
    """XMP (Extensible Metadata Platform) metadata.

    XMP is Adobe's standard for embedding metadata in files.
    It supports various namespaces including Dublin Core.

    Attributes:
        dc_title: Dublin Core title.
        dc_description: Dublin Core description.
        dc_creator: Dublin Core creator(s).
        dc_subject: Dublin Core subject(s)/keywords.
        dc_publisher: Dublin Core publisher.
        dc_date: Dublin Core date(s).
        dc_type: Dublin Core type.
        dc_format: Dublin Core format.
        dc_identifier: Dublin Core identifier.
        dc_source: Dublin Core source.
        dc_language: Dublin Core language.
        dc_rights: Dublin Core rights.
        rating: User rating (1-5).
        label: Color label.
        event: Event name.
        project: Project name.
        custom_namespaces: Custom XMP namespace data.
    """

    # Dublin Core elements
    dc_title: str = ""
    dc_description: str = ""
    dc_creator: list[str] = field(default_factory=list)
    dc_subject: list[str] = field(default_factory=list)
    dc_publisher: str = ""
    dc_date: datetime | None = None
    dc_type: str = ""
    dc_format: str = ""
    dc_identifier: str = ""
    dc_source: str = ""
    dc_language: str = ""
    dc_rights: str = ""

    # XMP specific
    rating: int | None = None
    label: str = ""
    event: str = ""
    project: str = ""

    # Custom namespaces
    custom_namespaces: dict[str, dict[str, Any]] = field(default_factory=dict)

    @property
    def has_rating(self) -> bool:
        """Check if rating is set."""
        return self.rating is not None and 1 <= self.rating <= 5

    @property
    def subject_str(self) -> str:
        """Return subjects as comma-separated string."""
        return ", ".join(self.dc_subject)

    @property
    def creator_str(self) -> str:
        """Return creators as comma-separated string."""
        return ", ".join(self.dc_creator)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dc_title": self.dc_title,
            "dc_description": self.dc_description,
            "dc_creator": self.dc_creator,
            "creator_str": self.creator_str,
            "dc_subject": self.dc_subject,
            "subject_str": self.subject_str,
            "dc_publisher": self.dc_publisher,
            "dc_date": self.dc_date.isoformat() if self.dc_date else None,
            "dc_type": self.dc_type,
            "dc_format": self.dc_format,
            "dc_identifier": self.dc_identifier,
            "dc_source": self.dc_source,
            "dc_language": self.dc_language,
            "dc_rights": self.dc_rights,
            "rating": self.rating,
            "has_rating": self.has_rating,
            "label": self.label,
            "event": self.event,
            "project": self.project,
            "custom_namespaces": self.custom_namespaces,
        }


@dataclass
class CustomMetadata:
    """Custom application-specific metadata.

    Stores arbitrary key-value pairs for application-specific use.

    Attributes:
        fields: Dictionary of custom field name to value.
        namespace: Optional namespace prefix for fields.
    """

    fields: dict[str, Any] = field(default_factory=dict)
    namespace: str = ""

    def get(self, key: str, default: Any = None) -> Any:
        """Get a custom field value."""
        return self.fields.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a custom field value."""
        self.fields[key] = value

    def remove(self, key: str) -> bool:
        """Remove a custom field. Returns True if key existed."""
        if key in self.fields:
            del self.fields[key]
            return True
        return False

    def keys(self) -> list[str]:
        """Get all field names."""
        return list(self.fields.keys())

    @property
    def count(self) -> int:
        """Get number of custom fields."""
        return len(self.fields)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "namespace": self.namespace,
            "fields": self.fields,
            "count": self.count,
        }


@dataclass
class ExtendedVideoMetadata:
    """Complete extended metadata for a video file.

    Combines all metadata types (basic, EXIF, IPTC, XMP, custom)
    into a single comprehensive metadata object.

    Attributes:
        basic: Basic video metadata.
        exif: EXIF metadata (camera settings, GPS).
        iptc: IPTC metadata (descriptive info).
        xmp: XMP metadata (Dublin Core, custom namespaces).
        custom: Custom application-specific metadata.
        raw_tags: Raw metadata tags from FFprobe.
    """

    basic: VideoMetadata
    exif: ExifMetadata = field(default_factory=ExifMetadata)
    iptc: IptcMetadata = field(default_factory=IptcMetadata)
    xmp: XmpMetadata = field(default_factory=XmpMetadata)
    custom: CustomMetadata = field(default_factory=CustomMetadata)
    raw_tags: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_video(cls, video_path: Path | str) -> ExtendedVideoMetadata:
        """Extract all metadata from a video file.

        Args:
            video_path: Path to the video file.

        Returns:
            ExtendedVideoMetadata with all available metadata.
        """
        file_path = Path(video_path).resolve()
        _get_video_metadata_logger()

        # Import here to avoid circular import
        from video2d3d.video.handler import VideoInputHandler

        # Extract basic metadata
        handler = VideoInputHandler()
        basic = handler.validate_and_extract(file_path)

        # Extract extended metadata using FFprobe
        extractor = VideoMetadataExtractor(file_path)

        return cls(
            basic=basic,
            exif=extractor.extract_exif(),
            iptc=extractor.extract_iptc(),
            xmp=extractor.extract_xmp(),
            custom=extractor.extract_custom(),
            raw_tags=extractor.raw_tags,
        )

    @property
    def has_extended_metadata(self) -> bool:
        """Check if any extended metadata is available."""
        return (
            bool(self.exif.make or self.exif.model)
            or bool(self.iptc.title or self.iptc.description)
            or bool(self.xmp.dc_title or self.xmp.dc_description)
            or self.custom.count > 0
        )

    def get_title(self) -> str:
        """Get title from any available metadata source."""
        return self.iptc.title or self.xmp.dc_title or self.basic.file_path.stem

    def get_description(self) -> str:
        """Get description from any available metadata source."""
        return self.iptc.description or self.xmp.dc_description

    def get_keywords(self) -> list[str]:
        """Get keywords from any available metadata source."""
        keywords = list(self.iptc.keywords)
        for subject in self.xmp.dc_subject:
            if subject not in keywords:
                keywords.append(subject)
        return keywords

    def get_creation_date(self) -> datetime | None:
        """Get creation date from any available metadata source."""
        return self.exif.datetime_original or self.iptc.date_created or self.xmp.dc_date

    def get_creator(self) -> str:
        """Get creator from any available metadata source."""
        return self.iptc.creator or self.xmp.creator_str or self.exif.make

    def to_ffmpeg_metadata(self) -> dict[str, str]:
        """Convert to FFmpeg-compatible metadata dictionary.

        Returns metadata in a format suitable for passing to FFmpeg's
        -metadata option.
        """
        metadata = {}

        # Standard metadata
        title = self.get_title()
        if title:
            metadata["title"] = title

        description = self.get_description()
        if description:
            metadata["description"] = description

        keywords = self.get_keywords()
        if keywords:
            metadata["keywords"] = ", ".join(keywords)

        creator = self.get_creator()
        if creator:
            metadata["artist"] = creator
            metadata["author"] = creator

        copyright_info = self.iptc.copyright or self.xmp.dc_rights
        if copyright_info:
            metadata["copyright"] = copyright_info

        # Date
        creation_date = self.get_creation_date()
        if creation_date:
            metadata["creation_time"] = creation_date.isoformat()

        # Camera info
        if self.exif.make:
            metadata["make"] = self.exif.make
        if self.exif.model:
            metadata["model"] = self.exif.model
        if self.exif.software:
            metadata["encoder"] = self.exif.software

        # Location
        if self.iptc.has_location:
            location_parts = []
            if self.iptc.city:
                location_parts.append(self.iptc.city)
            if self.iptc.country:
                location_parts.append(self.iptc.country)
            if location_parts:
                metadata["location"] = ", ".join(location_parts)

        # GPS
        if self.exif.has_gps:
            metadata["gps_latitude"] = str(self.exif.gps_latitude)
            metadata["gps_longitude"] = str(self.exif.gps_longitude)

        # Custom fields
        for key, value in self.custom.fields.items():
            prefixed_key = f"{self.custom.namespace}_{key}" if self.custom.namespace else key
            metadata[prefixed_key] = str(value)

        return metadata

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "basic": self.basic.to_dict(),
            "exif": self.exif.to_dict(),
            "iptc": self.iptc.to_dict(),
            "xmp": self.xmp.to_dict(),
            "custom": self.custom.to_dict(),
            "has_extended_metadata": self.has_extended_metadata,
            "title": self.get_title(),
            "description": self.get_description(),
            "keywords": self.get_keywords(),
            "creation_date": (
                self.get_creation_date().isoformat() if self.get_creation_date() else None
            ),
            "creator": self.get_creator(),
        }


class VideoMetadataExtractor:
    """Extract extended metadata from video files using FFprobe.

    This class extracts EXIF, IPTC, XMP, and custom metadata from
    video files using FFprobe and parses them into structured objects.

    Example usage:
        ```python
        extractor = VideoMetadataExtractor("video.mp4")
        exif = extractor.extract_exif()
        iptc = extractor.extract_iptc()
        xmp = extractor.extract_xmp()
        ```
    """

    def __init__(self, video_path: Path | str) -> None:
        """Initialize the metadata extractor.

        Args:
            video_path: Path to the video file.
        """
        self.video_path = Path(video_path).resolve()
        self._raw_data: dict[str, Any] | None = None
        self._tags: dict[str, Any] = {}

    @property
    def raw_tags(self) -> dict[str, Any]:
        """Get raw metadata tags."""
        if not self._tags:
            self._extract_raw_data()
        return self._tags

    def _extract_raw_data(self) -> dict[str, Any]:
        """Extract raw metadata using FFprobe."""
        if self._raw_data is not None:
            return self._raw_data

        logger = _get_video_metadata_logger()

        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "quiet",
                    "-print_format",
                    "json",
                    "-show_format",
                    "-show_streams",
                    str(self.video_path),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                logger.warning(f"FFprobe failed for {self.video_path}: {result.stderr}")
                self._raw_data = {}
                return self._raw_data

            self._raw_data = json.loads(result.stdout)

            # Extract tags from format and streams
            format_info = self._raw_data.get("format", {})
            self._tags = format_info.get("tags", {})

            # Also check video stream for tags
            for stream in self._raw_data.get("streams", []):
                if stream.get("codec_type") == "video":
                    stream_tags = stream.get("tags", {})
                    self._tags.update(stream_tags)
                    break

            return self._raw_data

        except FileNotFoundError:
            logger.warning("FFprobe not found. Extended metadata extraction unavailable.")
            self._raw_data = {}
            return self._raw_data
        except subprocess.TimeoutExpired:
            logger.warning(f"FFprobe timed out for {self.video_path}")
            self._raw_data = {}
            return self._raw_data
        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Failed to parse FFprobe output: {e}")
            self._raw_data = {}
            return self._raw_data

    def _parse_datetime(self, value: str | None) -> datetime | None:
        """Parse datetime from various formats."""
        if not value:
            return None

        # Common datetime formats in metadata
        formats = [
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%d %H:%M:%S",
            "%Y:%m:%d %H:%M:%S",  # EXIF format
            "%Y-%m-%d",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue

        return None

    def _get_tag(self, *keys: str) -> str | None:
        """Get tag value trying multiple possible key names."""
        for key in keys:
            value = self._tags.get(key)
            if value:
                return str(value)
        return None

    def extract_exif(self) -> ExifMetadata:
        """Extract EXIF metadata from the video."""
        self._extract_raw_data()

        return ExifMetadata(
            make=self._get_tag("make", "Make") or "",
            model=self._get_tag("model", "Model") or "",
            software=self._get_tag("software", "Software", "encoder", "Encoder") or "",
            datetime_original=self._parse_datetime(
                self._get_tag("creation_time", "DateTimeOriginal", "date_time_original")
            ),
            datetime_modified=self._parse_datetime(
                self._get_tag("modification_time", "DateTimeModified")
            ),
            exposure_time=self._try_float(self._get_tag("ExposureTime", "exposure_time")),
            f_number=self._try_float(self._get_tag("FNumber", "f_number", "Aperture")),
            iso_speed=self._try_int(self._get_tag("ISOSpeedRatings", "iso_speed", "ISO")),
            focal_length=self._try_float(self._get_tag("FocalLength", "focal_length")),
            gps_latitude=self._try_float(
                self._get_tag("GPSLatitude", "gps_latitude", "location_latitude")
            ),
            gps_longitude=self._try_float(
                self._get_tag("GPSLongitude", "gps_longitude", "location_longitude")
            ),
            gps_altitude=self._try_float(self._get_tag("GPSAltitude", "gps_altitude")),
            orientation=self._try_int(self._get_tag("Orientation", "orientation")) or 1,
            x_resolution=self._try_float(self._get_tag("XResolution", "x_resolution")),
            y_resolution=self._try_float(self._get_tag("YResolution", "y_resolution")),
        )

    def extract_iptc(self) -> IptcMetadata:
        """Extract IPTC metadata from the video."""
        self._extract_raw_data()

        keywords_str = self._get_tag("keywords", "Keywords", "subject") or ""
        keywords = [k.strip() for k in keywords_str.split(",") if k.strip()]

        supp_cat_str = self._get_tag("SupplementalCategories") or ""
        supp_cats = [c.strip() for c in supp_cat_str.split(",") if c.strip()]

        return IptcMetadata(
            title=self._get_tag("title", "Title", "headline") or "",
            description=self._get_tag("description", "Description", "caption", "comment") or "",
            keywords=keywords,
            copyright=self._get_tag("copyright", "Copyright", "rights") or "",
            creator=self._get_tag("creator", "Creator", "artist", "Artist", "author") or "",
            credit=self._get_tag("credit", "Credit") or "",
            source=self._get_tag("source", "Source") or "",
            city=self._get_tag("city", "City", "location_city") or "",
            country=self._get_tag("country", "Country", "location_country") or "",
            location=self._get_tag("location", "Location") or "",
            date_created=self._parse_datetime(self._get_tag("date_created", "DateCreated")),
            category=self._get_tag("category", "Category") or "",
            supplemental_categories=supp_cats,
            urgency=self._try_int(self._get_tag("urgency", "Urgency")) or 5,
        )

    def extract_xmp(self) -> XmpMetadata:
        """Extract XMP metadata from the video."""
        self._extract_raw_data()

        # Parse subjects/keywords
        subject_str = self._get_tag("subject", "Subject", "dc:subject") or ""
        subjects = [s.strip() for s in subject_str.split(",") if s.strip()]

        # Parse creators
        creator_str = self._get_tag("creator", "Creator", "dc:creator") or ""
        creators = [c.strip() for c in creator_str.split(";") if c.strip()]

        return XmpMetadata(
            dc_title=self._get_tag("dc:title", "title") or "",
            dc_description=self._get_tag("dc:description", "description") or "",
            dc_creator=creators,
            dc_subject=subjects,
            dc_publisher=self._get_tag("dc:publisher", "publisher") or "",
            dc_date=self._parse_datetime(self._get_tag("dc:date", "date", "creation_time")),
            dc_type=self._get_tag("dc:type") or "",
            dc_format=self._get_tag("dc:format", "format") or "",
            dc_identifier=self._get_tag("dc:identifier", "identifier") or "",
            dc_source=self._get_tag("dc:source", "source") or "",
            dc_language=self._get_tag("dc:language", "language") or "",
            dc_rights=self._get_tag("dc:rights", "copyright") or "",
            rating=self._try_int(self._get_tag("rating", "Rating")),
            label=self._get_tag("label", "Label") or "",
            event=self._get_tag("event", "Event") or "",
            project=self._get_tag("project", "Project") or "",
        )

    def extract_custom(self) -> CustomMetadata:
        """Extract custom metadata from the video.

        Collects any non-standard tags into a custom metadata object.
        """
        self._extract_raw_data()

        # Known standard tags to exclude
        standard_tags = {
            "title",
            "Title",
            "description",
            "Description",
            "comment",
            "copyright",
            "Copyright",
            "artist",
            "Artist",
            "author",
            "creation_time",
            "modification_time",
            "encoder",
            "Encoder",
            "make",
            "Make",
            "model",
            "Model",
            "software",
            "Software",
            "keywords",
            "Keywords",
            "subject",
            "Subject",
            "rating",
            "Rating",
            "genre",
            "Genre",
            "album",
            "Album",
            "track",
            "Track",
            "year",
            "Year",
            "language",
            "Language",
        }

        custom_fields = {}
        for key, value in self._tags.items():
            if key.lower() not in {t.lower() for t in standard_tags}:
                custom_fields[key] = value

        return CustomMetadata(fields=custom_fields)

    def _try_float(self, value: str | None) -> float | None:
        """Try to parse a float value."""
        if not value:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _try_int(self, value: str | None) -> int | None:
        """Try to parse an integer value."""
        if not value:
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None


def extract_extended_metadata(video_path: Path | str) -> ExtendedVideoMetadata:
    """Convenience function to extract all metadata from a video.

    Args:
        video_path: Path to the video file.

    Returns:
        ExtendedVideoMetadata with all available metadata.

    Example:
        ```python
        metadata = extract_extended_metadata("video.mp4")
        print(f"Title: {metadata.get_title()}")
        print(f"Keywords: {metadata.get_keywords()}")
        ```
    """
    return ExtendedVideoMetadata.from_video(video_path)
