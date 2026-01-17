"""
DeepAgents Services Package.

This package provides core services for the DeepAgents system:
- SchemaService: Fetch and parse model schemas from Replicate
- DynamicUIGenerator: Generate Streamlit controls from schemas
- AssetValidator: Validate uploaded files against requirements
- ModelRegistry: Curated catalog of AI models
"""
from DeepAgents.services.schema_service import (
    SchemaService,
    ControlDefinition,
    ControlType,
    ModelSchema,
    AssetRequirement,
    get_schema_service
)

from DeepAgents.services.ui_generator import (
    DynamicUIGenerator,
    render_model_config_panel
)

from DeepAgents.services.asset_validator import (
    AssetValidator,
    ValidationResult,
    ValidationStatus,
    get_asset_validator,
    validate_upload
)

from DeepAgents.services.model_registry import (
    ModelRegistry,
    ModelInfo,
    ModelCategory,
    OutputType,
    InputRequirement,
    get_model_registry,
    get_video_model_options,
    get_music_model_options,
    get_voice_model_options,
    get_image_model_options,
    model_requires_voice
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
    "model_requires_voice"
]
