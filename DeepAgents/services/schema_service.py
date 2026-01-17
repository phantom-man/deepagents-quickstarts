"""
Schema Service - Fetches and parses model schemas from Replicate API.

This service provides zero-touch dynamic UI generation by:
1. Fetching OpenAPI schemas from Replicate models
2. Parsing them into UI-friendly control definitions
3. Caching schemas to avoid repeated API calls
4. Detecting asset requirements (voice files, music files, etc.)

Philosophy: Fail Fast - If schema fetch fails, raise immediately.
"""
import os
import json
import logging
import hashlib
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum

import requests

logger = logging.getLogger(__name__)


class ControlType(Enum):
    """UI Control types derived from OpenAPI schema types."""
    TEXT = "text"           # string without format
    TEXT_AREA = "textarea"  # string with multiline hint
    NUMBER = "number"       # integer or number
    SLIDER = "slider"       # number with min/max
    CHECKBOX = "checkbox"   # boolean
    SELECT = "select"       # enum values
    FILE = "file"           # format: uri, file input
    AUDIO_FILE = "audio"    # file with audio/* content type
    VIDEO_FILE = "video"    # file with video/* content type
    IMAGE_FILE = "image"    # file with image/* content type
    HIDDEN = "hidden"       # internal params to hide


@dataclass
class ControlDefinition:
    """Definition for a single UI control derived from schema."""
    name: str
    control_type: ControlType
    label: str
    description: str = ""
    required: bool = False
    default: Any = None
    # For numeric controls
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    step: Optional[float] = None
    # For select controls
    options: List[Any] = field(default_factory=list)
    # For file controls
    accepted_types: List[str] = field(default_factory=list)
    max_duration: Optional[float] = None  # seconds
    min_duration: Optional[float] = None  # seconds
    # Order in UI
    order: int = 0


@dataclass
class AssetRequirement:
    """Describes a required asset input for a model."""
    param_name: str
    asset_type: str  # 'audio', 'video', 'image'
    description: str
    required: bool = True
    # Constraints from schema
    accepted_formats: List[str] = field(default_factory=list)
    min_duration: Optional[float] = None
    max_duration: Optional[float] = None
    # Content hints
    content_type: Optional[str] = None  # 'voice', 'music', 'instrumental', etc.


@dataclass
class ModelSchema:
    """Parsed schema for a model with UI controls and asset requirements."""
    model_id: str
    name: str
    description: str
    controls: List[ControlDefinition] = field(default_factory=list)
    asset_requirements: List[AssetRequirement] = field(default_factory=list)
    output_type: str = "unknown"  # 'audio', 'video', 'image', 'text'
    # Raw schema for reference
    raw_schema: Dict[str, Any] = field(default_factory=dict)
    # Cache metadata
    fetched_at: float = 0
    version_id: Optional[str] = None


class SchemaService:
    """
    Service for fetching, parsing, and caching model schemas.

    Uses Replicate API to get OpenAPI schemas and converts them
    to UI control definitions for dynamic form generation.
    """

    # Parameters to hide from UI (internal/advanced)
    HIDDEN_PARAMS = {
        'seed', 'num_outputs', 'disable_safety_checker',
        'output_format', 'output_quality', 'webhook', 'webhook_events_filter'
    }

    # Keywords that indicate file inputs
    FILE_KEYWORDS = {'file', 'audio', 'image', 'video', 'voice', 'music', 'reference', 'input_'}

    # Keywords that indicate audio content types
    AUDIO_CONTENT_KEYWORDS = {
        'voice': 'voice',
        'vocal': 'voice',
        'speech': 'voice',
        'music': 'music',
        'song': 'music',
        'melody': 'music',
        'instrumental': 'instrumental',
        'reference_audio': 'voice',  # Usually voice reference
    }

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize schema service.

        Args:
            cache_dir: Directory for caching schemas. Defaults to DeepAgents/.cache/schemas/
        """
        self.api_token = os.environ.get("REPLICATE_API_TOKEN")
        if not self.api_token:
            raise ValueError("REPLICATE_API_TOKEN environment variable required")

        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            self.cache_dir = Path(__file__).parent.parent / ".cache" / "schemas"

        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._schema_cache: Dict[str, ModelSchema] = {}

        # Load cached schemas from disk
        self._load_disk_cache()

    def _load_disk_cache(self) -> None:
        """Load cached schemas from disk."""
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    schema = self._dict_to_schema(data)
                    self._schema_cache[schema.model_id] = schema
            except Exception as e:
                logger.warning(f"Failed to load cached schema {cache_file}: {e}")

    def _get_cache_path(self, model_id: str) -> Path:
        """Get cache file path for a model."""
        safe_name = hashlib.md5(model_id.encode()).hexdigest()
        return self.cache_dir / f"{safe_name}.json"

    def _dict_to_schema(self, data: Dict[str, Any]) -> ModelSchema:
        """Convert dict to ModelSchema."""
        controls = [
            ControlDefinition(
                name=c["name"],
                control_type=ControlType(c["control_type"]),
                label=c["label"],
                description=c.get("description", ""),
                required=c.get("required", False),
                default=c.get("default"),
                minimum=c.get("minimum"),
                maximum=c.get("maximum"),
                step=c.get("step"),
                options=c.get("options", []),
                accepted_types=c.get("accepted_types", []),
                max_duration=c.get("max_duration"),
                min_duration=c.get("min_duration"),
                order=c.get("order", 0)
            )
            for c in data.get("controls", [])
        ]

        requirements = [
            AssetRequirement(
                param_name=r["param_name"],
                asset_type=r["asset_type"],
                description=r.get("description", ""),
                required=r.get("required", True),
                accepted_formats=r.get("accepted_formats", []),
                min_duration=r.get("min_duration"),
                max_duration=r.get("max_duration"),
                content_type=r.get("content_type")
            )
            for r in data.get("asset_requirements", [])
        ]

        return ModelSchema(
            model_id=data["model_id"],
            name=data["name"],
            description=data.get("description", ""),
            controls=controls,
            asset_requirements=requirements,
            output_type=data.get("output_type", "unknown"),
            raw_schema=data.get("raw_schema", {}),
            fetched_at=data.get("fetched_at", 0),
            version_id=data.get("version_id")
        )

    def _schema_to_dict(self, schema: ModelSchema) -> Dict[str, Any]:
        """Convert ModelSchema to dict for caching."""
        return {
            "model_id": schema.model_id,
            "name": schema.name,
            "description": schema.description,
            "controls": [
                {
                    "name": c.name,
                    "control_type": c.control_type.value,
                    "label": c.label,
                    "description": c.description,
                    "required": c.required,
                    "default": c.default,
                    "minimum": c.minimum,
                    "maximum": c.maximum,
                    "step": c.step,
                    "options": c.options,
                    "accepted_types": c.accepted_types,
                    "max_duration": c.max_duration,
                    "min_duration": c.min_duration,
                    "order": c.order
                }
                for c in schema.controls
            ],
            "asset_requirements": [
                {
                    "param_name": r.param_name,
                    "asset_type": r.asset_type,
                    "description": r.description,
                    "required": r.required,
                    "accepted_formats": r.accepted_formats,
                    "min_duration": r.min_duration,
                    "max_duration": r.max_duration,
                    "content_type": r.content_type
                }
                for r in schema.asset_requirements
            ],
            "output_type": schema.output_type,
            "raw_schema": schema.raw_schema,
            "fetched_at": schema.fetched_at,
            "version_id": schema.version_id
        }

    def _fetch_model_info(self, model_id: str) -> Dict[str, Any]:
        """
        Fetch model info from Replicate API.

        Args:
            model_id: Model identifier (owner/name)

        Returns:
            Model info dict including openapi_schema

        Raises:
            ValueError: If API call fails (Fail Fast)
        """
        url = f"https://api.replicate.com/v1/models/{model_id}"
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }

        response = requests.get(url, headers=headers, timeout=30)

        if response.status_code != 200:
            # FAIL FAST: Don't silently fail, raise immediately
            raise ValueError(
                f"Failed to fetch schema for {model_id}: "
                f"HTTP {response.status_code} - {response.text}"
            )

        return response.json()

    def _infer_control_type(
        self,
        name: str,
        prop: Dict[str, Any]
    ) -> Tuple[ControlType, Optional[str]]:
        """
        Infer the UI control type from schema property.

        Returns:
            Tuple of (ControlType, asset_content_type or None)
        """
        prop_type = prop.get("type", "string")
        prop_format = prop.get("format", "")
        description = prop.get("description", "").lower()
        name_lower = name.lower()

        # Check if it should be hidden
        if name in self.HIDDEN_PARAMS:
            return ControlType.HIDDEN, None

        # Check for enum (select)
        if "enum" in prop or "allOf" in prop:
            return ControlType.SELECT, None

        # Check for file inputs
        is_file_param = any(kw in name_lower for kw in self.FILE_KEYWORDS)
        is_uri_format = prop_format == "uri" or "url" in description or "file" in description

        if is_file_param or is_uri_format:
            # Determine content type from name/description
            content_type = None
            for keyword, ctype in self.AUDIO_CONTENT_KEYWORDS.items():
                if keyword in name_lower or keyword in description:
                    content_type = ctype
                    break

            # Determine file type
            if "audio" in name_lower or "voice" in name_lower or "music" in name_lower or "song" in name_lower:
                return ControlType.AUDIO_FILE, content_type
            elif "video" in name_lower:
                return ControlType.VIDEO_FILE, None
            elif "image" in name_lower or "photo" in name_lower:
                return ControlType.IMAGE_FILE, None
            else:
                return ControlType.FILE, content_type

        # Boolean
        if prop_type == "boolean":
            return ControlType.CHECKBOX, None

        # Numbers with range
        if prop_type in ("integer", "number"):
            has_range = "minimum" in prop or "maximum" in prop
            if has_range:
                return ControlType.SLIDER, None
            return ControlType.NUMBER, None

        # Strings
        if prop_type == "string":
            # Long text (prompts, lyrics)
            if any(kw in name_lower for kw in ["prompt", "lyrics", "text", "description"]):
                return ControlType.TEXT_AREA, None
            return ControlType.TEXT, None

        return ControlType.TEXT, None

    def _parse_openapi_schema(
        self,
        model_id: str,
        model_info: Dict[str, Any]
    ) -> ModelSchema:
        """
        Parse OpenAPI schema into ModelSchema with controls.

        Args:
            model_id: Model identifier
            model_info: Full model info from API

        Returns:
            Parsed ModelSchema
        """
        name = model_info.get("name", model_id.split("/")[-1])
        description = model_info.get("description", "")

        # Get latest version schema
        latest_version = model_info.get("latest_version", {})
        version_id = latest_version.get("id")
        openapi_schema = latest_version.get("openapi_schema", {})

        # Get input schema
        components = openapi_schema.get("components", {})
        schemas = components.get("schemas", {})
        input_schema = schemas.get("Input", {})
        output_schema = schemas.get("Output", {})

        properties = input_schema.get("properties", {})
        required_fields = set(input_schema.get("required", []))

        controls: List[ControlDefinition] = []
        asset_requirements: List[AssetRequirement] = []

        for idx, (param_name, prop) in enumerate(properties.items()):
            control_type, content_type = self._infer_control_type(param_name, prop)

            # Skip hidden controls from the public list
            if control_type == ControlType.HIDDEN:
                continue

            # Create label from param name
            label = param_name.replace("_", " ").title()

            # Build control definition
            control = ControlDefinition(
                name=param_name,
                control_type=control_type,
                label=label,
                description=prop.get("description", ""),
                required=param_name in required_fields,
                default=prop.get("default"),
                minimum=prop.get("minimum"),
                maximum=prop.get("maximum"),
                order=prop.get("x-order", idx)
            )

            # Handle enums
            if "enum" in prop:
                control.options = prop["enum"]
            elif "allOf" in prop:
                # Handle allOf references
                for ref in prop.get("allOf", []):
                    if "$ref" in ref:
                        ref_name = ref["$ref"].split("/")[-1]
                        ref_schema = schemas.get(ref_name, {})
                        if "enum" in ref_schema:
                            control.options = ref_schema["enum"]

            # Handle numeric ranges
            if control_type == ControlType.SLIDER:
                # Infer step from type
                if prop.get("type") == "integer":
                    control.step = 1
                else:
                    # Estimate step from range
                    if control.minimum is not None and control.maximum is not None:
                        range_size = control.maximum - control.minimum
                        control.step = range_size / 100  # 100 steps

            controls.append(control)

            # Check if this is an asset requirement
            if control_type in (ControlType.AUDIO_FILE, ControlType.VIDEO_FILE,
                               ControlType.IMAGE_FILE, ControlType.FILE):
                asset_type_map = {
                    ControlType.AUDIO_FILE: "audio",
                    ControlType.VIDEO_FILE: "video",
                    ControlType.IMAGE_FILE: "image",
                    ControlType.FILE: "file"
                }

                asset_req = AssetRequirement(
                    param_name=param_name,
                    asset_type=asset_type_map[control_type],
                    description=prop.get("description", ""),
                    required=param_name in required_fields,
                    content_type=content_type
                )

                # Try to extract duration constraints from description
                desc_lower = prop.get("description", "").lower()
                if "second" in desc_lower or "duration" in desc_lower:
                    # Try to parse duration hints
                    import re
                    duration_match = re.search(r"(\d+)\s*(?:second|sec|s)", desc_lower)
                    if duration_match:
                        duration_val = int(duration_match.group(1))
                        # Heuristic: if mentioned as max, set as max
                        if "max" in desc_lower or "up to" in desc_lower:
                            asset_req.max_duration = float(duration_val)
                        elif "min" in desc_lower or "at least" in desc_lower:
                            asset_req.min_duration = float(duration_val)
                        else:
                            # Default: treat as target/max
                            asset_req.max_duration = float(duration_val)

                asset_requirements.append(asset_req)

        # Sort controls by order
        controls.sort(key=lambda c: c.order)

        # Infer output type from output schema or model category
        output_type = "unknown"
        output_schema_type = output_schema.get("type", "")
        if "items" in output_schema:
            items_format = output_schema.get("items", {}).get("format", "")
            if items_format == "uri":
                # Could be audio, video, or image - infer from model name
                model_lower = model_id.lower()
                if any(kw in model_lower for kw in ["music", "audio", "song", "voice", "speech"]):
                    output_type = "audio"
                elif any(kw in model_lower for kw in ["video", "film", "movie"]):
                    output_type = "video"
                elif any(kw in model_lower for kw in ["image", "picture", "photo", "flux", "sdxl", "stable"]):
                    output_type = "image"

        return ModelSchema(
            model_id=model_id,
            name=name,
            description=description,
            controls=controls,
            asset_requirements=asset_requirements,
            output_type=output_type,
            raw_schema=openapi_schema,
            fetched_at=time.time(),
            version_id=version_id
        )

    def get_schema(
        self,
        model_id: str,
        force_refresh: bool = False,
        cache_ttl: int = 86400  # 24 hours
    ) -> ModelSchema:
        """
        Get schema for a model, using cache if available.

        Args:
            model_id: Model identifier (owner/name)
            force_refresh: If True, bypass cache
            cache_ttl: Cache time-to-live in seconds

        Returns:
            Parsed ModelSchema

        Raises:
            ValueError: If schema fetch fails (Fail Fast)
        """
        # Check memory cache
        if not force_refresh and model_id in self._schema_cache:
            cached = self._schema_cache[model_id]
            if time.time() - cached.fetched_at < cache_ttl:
                logger.debug(f"Schema cache hit: {model_id}")
                return cached

        # Fetch from API
        logger.info(f"Fetching schema for: {model_id}")
        model_info = self._fetch_model_info(model_id)
        schema = self._parse_openapi_schema(model_id, model_info)

        # Cache to memory and disk
        self._schema_cache[model_id] = schema
        cache_path = self._get_cache_path(model_id)
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(self._schema_to_dict(schema), f, indent=2)

        logger.info(f"Schema cached: {model_id} ({len(schema.controls)} controls)")
        return schema

    def get_asset_requirements(self, model_id: str) -> List[AssetRequirement]:
        """Get asset requirements for a model."""
        schema = self.get_schema(model_id)
        return schema.asset_requirements

    def has_asset_requirements(self, model_id: str) -> bool:
        """Check if model requires any asset inputs."""
        requirements = self.get_asset_requirements(model_id)
        return any(r.required for r in requirements)

    def clear_cache(self, model_id: Optional[str] = None) -> None:
        """Clear cached schema(s)."""
        if model_id:
            self._schema_cache.pop(model_id, None)
            cache_path = self._get_cache_path(model_id)
            if cache_path.exists():
                cache_path.unlink()
        else:
            self._schema_cache.clear()
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()


# Singleton instance
_schema_service: Optional[SchemaService] = None


def get_schema_service() -> SchemaService:
    """Get singleton schema service instance."""
    global _schema_service
    if _schema_service is None:
        _schema_service = SchemaService()
    return _schema_service
