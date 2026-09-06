"""Gated finding 2026-09-05 (colibri review of DeepAgents/services/schema_service.py, HIGH):
the file-keyword heuristic in `_infer_control_type` ran before the type checks, so
the file's OWN first-party schemas misrendered: Veo's `generate_audio` (boolean)
became an AUDIO_FILE picker with a bogus audio AssetRequirement, and Imagen's
`number_of_images` (integer 1-4) became an IMAGE_FILE upload instead of a slider.
"""

import pytest

from DeepAgents.services.schema_service import (
    ControlType,
    SchemaService,
    VertexAISchemaProvider,
)


@pytest.fixture
def svc(tmp_path, monkeypatch):
    monkeypatch.delenv("REPLICATE_API_TOKEN", raising=False)
    return SchemaService(cache_dir=str(tmp_path))


class TestTypedParamsWinOverFileKeywords:
    def test_a_boolean_named_generate_audio_is_a_checkbox(self, svc):
        ctype, content = svc._infer_control_type(
            "generate_audio",
            {"type": "boolean", "description": "Generate synchronized audio track.", "default": False},
        )
        assert (ctype, content) == (ControlType.CHECKBOX, None)

    def test_an_integer_named_number_of_images_is_a_slider(self, svc):
        ctype, _ = svc._infer_control_type(
            "number_of_images",
            {"type": "integer", "description": "How many images to generate (1-4).", "minimum": 1, "maximum": 4},
        )
        assert ctype == ControlType.SLIDER


class TestRealFileParamsStillRender:
    @pytest.mark.parametrize(
        "name,prop,expected",
        [
            ("image", {"type": "string", "format": "uri"}, ControlType.IMAGE_FILE),
            ("audio", {"type": "string", "description": "Reference audio"}, ControlType.AUDIO_FILE),
            ("video_input", {"type": "string"}, ControlType.VIDEO_FILE),
            ("input_file", {"description": "URL of the file to process"}, ControlType.FILE),
            # Regression pin (passed before the fix too): list-of-uri params stay files.
            ("images", {"type": "array", "items": {"type": "string", "format": "uri"}}, ControlType.IMAGE_FILE),
        ],
    )
    def test_string_file_params(self, svc, name, prop, expected):
        ctype, _ = svc._infer_control_type(name, prop)
        assert ctype == expected


class TestFirstPartySchemasRenderThemselves:
    def test_veo_generate_audio_is_not_an_asset_requirement(self, svc):
        info = VertexAISchemaProvider().fetch_schema("veo-3.1-generate-001")
        schema = svc._parse_openapi_schema("veo-3.1-generate-001", info, "vertex")
        by_name = {c.name: c for c in schema.controls}
        assert by_name["generate_audio"].control_type == ControlType.CHECKBOX
        assert all(r.param_name != "generate_audio" for r in schema.asset_requirements)

    def test_imagen_number_of_images_is_a_slider(self, svc):
        info = VertexAISchemaProvider().fetch_schema("imagen-3.0-generate-002")
        schema = svc._parse_openapi_schema("imagen-3.0-generate-002", info, "vertex")
        by_name = {c.name: c for c in schema.controls}
        assert by_name["number_of_images"].control_type == ControlType.SLIDER
        assert all(r.param_name != "number_of_images" for r in schema.asset_requirements)
