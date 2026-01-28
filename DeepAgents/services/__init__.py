"""
DeepAgents Services Package.

This package provides core services for the DeepAgents system:
- SchemaService: Fetch and parse model schemas from Replicate
- DynamicUIGenerator: Generate Streamlit controls from schemas
- AssetValidator: Validate uploaded files against requirements
- ModelRegistry: Curated catalog of AI models
"""

from DeepAgents.services.asset_validator import (
    AssetValidator,
    ValidationResult,
    ValidationStatus,
    get_asset_validator,
    validate_upload,
)
from DeepAgents.services.file_analyzer import (
    AudioMetadata,
    FileAnalyzer,
    ImageMetadata,
    VideoMetadata,
    calculate_video_segments,
    format_file_size,
)
from DeepAgents.services.input_schema import (
    InputFieldDefinition,
    InputType,
    filter_presets_by_char_limit,
    get_fields_supporting_presets,
    get_input_fields_for_model,
    get_max_chars_for_field,
    validate_input,
)
from DeepAgents.services.model_registry import (
    InputRequirement,
    ModelCategory,
    ModelInfo,
    ModelRegistry,
    OutputType,
    get_image_model_options,
    get_model_registry,
    get_music_model_options,
    get_video_model_options,
    get_voice_model_options,
    model_requires_voice,
)
from DeepAgents.services.schema_service import (
    AssetRequirement,
    ControlDefinition,
    ControlType,
    ModelSchema,
    SchemaService,
    get_schema_service,
)
from DeepAgents.services.ui_generator import (
    DynamicUIGenerator,
    render_model_config_panel,
)

__all__ = [
    # Schema Service
    "SchemaService",
    "ControlDefinition",
    "ControlType",
    "ModelSchema",
    "AssetRequirement",
    "get_schema_service",
    # UI Generator
    "DynamicUIGenerator",
    "render_model_config_panel",
    # Asset Validator
    "AssetValidator",
    "ValidationResult",
    "ValidationStatus",
    "get_asset_validator",
    "validate_upload",
    # Model Registry
    "ModelRegistry",
    "ModelInfo",
    "ModelCategory",
    "OutputType",
    "InputRequirement",
    "get_model_registry",
    "get_video_model_options",
    "get_music_model_options",
    "get_voice_model_options",
    "get_image_model_options",
    "model_requires_voice",
    # Input Schema
    "InputType",
    "InputFieldDefinition",
    "get_input_fields_for_model",
    "get_max_chars_for_field",
    "validate_input",
    "filter_presets_by_char_limit",
    "get_fields_supporting_presets",
    # File Analyzer
    "FileAnalyzer",
    "AudioMetadata",
    "VideoMetadata",
    "ImageMetadata",
    "calculate_video_segments",
    "format_file_size",
]
