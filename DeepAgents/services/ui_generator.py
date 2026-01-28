"""
Dynamic UI Generator - Creates Streamlit controls from model schemas.

This module generates Streamlit UI components dynamically based on
parsed OpenAPI schemas from the SchemaService.

Philosophy: Zero-Touch - UI auto-configures from model schemas.
"""

import logging
from typing import Any, Callable, Dict, List, Optional, Tuple

import streamlit as st

from DeepAgents.services.schema_service import (
    AssetRequirement,
    ControlDefinition,
    ControlType,
    ModelSchema,
    get_schema_service,
)

logger = logging.getLogger(__name__)


class DynamicUIGenerator:
    """
    Generates Streamlit UI controls from model schemas.

    Each control type maps to a specific Streamlit widget with
    appropriate configuration from the schema.
    """

    def __init__(self, key_prefix: str = "dynamic"):
        """
        Initialize UI generator.

        Args:
            key_prefix: Prefix for Streamlit widget keys to avoid conflicts
        """
        self.key_prefix = key_prefix
        self.schema_service = get_schema_service()

    def _make_key(self, control_name: str) -> str:
        """Generate unique key for a control."""
        return f"{self.key_prefix}_{control_name}"

    def render_control(
        self, control: ControlDefinition, current_value: Any = None
    ) -> Any:
        """
        Render a single control and return its value.

        Args:
            control: Control definition from schema
            current_value: Current value (for preserving state)

        Returns:
            Current value of the control
        """
        key = self._make_key(control.name)

        # Use current_value or default
        default = current_value if current_value is not None else control.default

        # Add help text if available
        help_text = control.description if control.description else None

        if control.control_type == ControlType.TEXT:
            return st.text_input(
                control.label, value=default or "", key=key, help=help_text
            )

        elif control.control_type == ControlType.TEXT_AREA:
            return st.text_area(
                control.label, value=default or "", key=key, help=help_text, height=100
            )

        elif control.control_type == ControlType.NUMBER:
            # Determine if integer or float based on step and bounds
            # Must ensure ALL numeric args are same type (int or float)
            step_val = control.step if control.step is not None else 1
            is_int = (
                isinstance(step_val, int) or step_val == int(step_val)
            ) and step_val >= 1

            if is_int:
                # All values must be int
                val = int(default) if default is not None else 0
                min_v = int(control.minimum) if control.minimum is not None else None
                max_v = int(control.maximum) if control.maximum is not None else None
                step_v = int(step_val)
            else:
                # All values must be float
                val = float(default) if default is not None else 0.0
                min_v = float(control.minimum) if control.minimum is not None else None
                max_v = float(control.maximum) if control.maximum is not None else None
                step_v = float(step_val)

            return st.number_input(
                control.label,
                value=val,
                min_value=min_v,
                max_value=max_v,
                step=step_v,
                key=key,
                help=help_text,
            )

        elif control.control_type == ControlType.SLIDER:
            # Get raw values with defaults
            raw_min = control.minimum if control.minimum is not None else 0
            raw_max = control.maximum if control.maximum is not None else 100
            raw_default = default if default is not None else raw_min
            raw_step = control.step if control.step is not None else 1

            # Determine if integer based on step
            is_int = (
                isinstance(raw_step, int) or raw_step == int(raw_step)
            ) and raw_step >= 1

            if is_int:
                # All values must be int
                min_val = int(raw_min)
                max_val = int(raw_max)
                step_val = int(raw_step)
                default_val = int(max(min_val, min(max_val, raw_default)))
            else:
                # All values must be float
                min_val = float(raw_min)
                max_val = float(raw_max)
                step_val = float(raw_step)
                default_val = float(max(min_val, min(max_val, raw_default)))

            return st.slider(
                control.label,
                min_value=min_val,
                max_value=max_val,
                value=default_val,
                step=step_val,
                key=key,
                help=help_text,
            )

        elif control.control_type == ControlType.CHECKBOX:
            return st.checkbox(
                control.label,
                value=bool(default) if default is not None else False,
                key=key,
                help=help_text,
            )

        elif control.control_type == ControlType.SELECT:
            options = control.options or []
            if not options:
                return st.text_input(control.label, key=key, help=help_text)

            # Find default index
            default_idx = 0
            if default in options:
                default_idx = options.index(default)

            return st.selectbox(
                control.label,
                options=options,
                index=default_idx,
                key=key,
                help=help_text,
            )

        elif control.control_type in (
            ControlType.FILE,
            ControlType.AUDIO_FILE,
            ControlType.VIDEO_FILE,
            ControlType.IMAGE_FILE,
        ):
            # File uploader with type hints
            type_map = {
                ControlType.AUDIO_FILE: ["wav", "mp3", "flac", "ogg", "m4a"],
                ControlType.VIDEO_FILE: ["mp4", "mov", "avi", "webm"],
                ControlType.IMAGE_FILE: ["png", "jpg", "jpeg", "webp", "gif"],
                ControlType.FILE: None,  # Accept all
            }

            accepted = control.accepted_types or type_map.get(control.control_type)

            uploaded = st.file_uploader(
                control.label, type=accepted, key=key, help=help_text
            )

            return uploaded

        else:
            # Fallback to text input
            return st.text_input(
                control.label,
                value=str(default) if default else "",
                key=key,
                help=help_text,
            )

    def render_controls(
        self,
        schema: ModelSchema,
        current_values: Optional[Dict[str, Any]] = None,
        exclude_params: Optional[List[str]] = None,
        columns: int = 1,
    ) -> Dict[str, Any]:
        """
        Render all controls for a model schema.

        Args:
            schema: Model schema with controls
            current_values: Current values dict for state preservation
            exclude_params: Parameter names to exclude
            columns: Number of columns for layout

        Returns:
            Dict of parameter name -> value
        """
        current_values = current_values or {}
        excluded: set = set(exclude_params or [])

        # Filter controls
        visible_controls = [
            c
            for c in schema.controls
            if c.control_type != ControlType.HIDDEN and c.name not in excluded
        ]

        if not visible_controls:
            st.info("No configurable parameters for this model.")
            return {}

        values = {}

        if columns > 1:
            # Multi-column layout
            cols = st.columns(columns)
            for idx, control in enumerate(visible_controls):
                with cols[idx % columns]:
                    values[control.name] = self.render_control(
                        control, current_values.get(control.name)
                    )
        else:
            # Single column
            for control in visible_controls:
                values[control.name] = self.render_control(
                    control, current_values.get(control.name)
                )

        return values

    def render_asset_requirement(
        self,
        requirement: AssetRequirement,
        compatible_models: Optional[List[Dict[str, str]]] = None,
        on_generate: Optional[Callable] = None,
        local_files: Optional[List[str]] = None,
    ) -> Tuple[Optional[str], Optional[Any], bool]:
        """
        Render UI for an asset requirement with generate/select options.

        Args:
            requirement: Asset requirement from schema
            compatible_models: List of models that can generate this asset
                               Each dict has 'id', 'name', 'output_type'
            on_generate: Callback when generate is clicked
            local_files: List of local file paths to choose from

        Returns:
            Tuple of (source_type, value, is_valid)
            - source_type: 'generate', 'upload', 'local', or None
            - value: model_id, uploaded file, or local path
            - is_valid: Whether the selection meets requirements
        """
        key_base = self._make_key(f"asset_{requirement.param_name}")

        st.markdown(f"**{requirement.param_name.replace('_', ' ').title()}**")
        if requirement.description:
            st.caption(requirement.description)

        # Source selection
        source_options = ["Upload File"]
        if compatible_models:
            source_options.insert(0, "Generate with AI")
        if local_files:
            source_options.append("Select from Library")

        source = st.radio(
            "Source", options=source_options, key=f"{key_base}_source", horizontal=True
        )

        is_valid = False
        value = None
        source_type = None

        if source == "Generate with AI" and compatible_models:
            source_type = "generate"
            model_options = {m["name"]: m["id"] for m in compatible_models}
            selected_name = st.selectbox(
                "Generator Model",
                options=list(model_options.keys()),
                key=f"{key_base}_model",
            )
            value = model_options.get(selected_name)

            # Show constraints
            constraints = []
            if requirement.max_duration:
                constraints.append(f"Max duration: {requirement.max_duration}s")
            if requirement.min_duration:
                constraints.append(f"Min duration: {requirement.min_duration}s")
            if requirement.content_type:
                constraints.append(f"Content: {requirement.content_type}")

            if constraints:
                st.caption(" | ".join(constraints))

            is_valid = value is not None

            # Show green check if valid selection
            if is_valid:
                st.success("✓ Model selected")

        elif source == "Upload File":
            source_type = "upload"
            type_map = {
                "audio": ["wav", "mp3", "flac", "ogg", "m4a"],
                "video": ["mp4", "mov", "avi", "webm"],
                "image": ["png", "jpg", "jpeg", "webp"],
            }
            accepted = type_map.get(requirement.asset_type, None)

            uploaded = st.file_uploader(
                f"Upload {requirement.asset_type}",
                type=accepted,
                key=f"{key_base}_upload",
            )

            if uploaded:
                value = uploaded
                # Validate file (basic check - full validation in AssetValidator)
                is_valid = True

                # TODO: Add duration check for audio/video
                # For now, show green check
                st.success(f"✓ File uploaded: {uploaded.name}")
            else:
                if requirement.required:
                    st.warning("⚠ Required file not provided")

        elif source == "Select from Library" and local_files:
            source_type = "local"
            selected_file = st.selectbox(
                "Select file", options=[""] + local_files, key=f"{key_base}_local"
            )

            if selected_file:
                value = selected_file
                # Validate would happen here
                is_valid = True
                st.success("✓ File selected")
            else:
                if requirement.required:
                    st.warning("⚠ Required file not selected")

        return source_type, value, is_valid


def render_model_config_panel(
    model_id: str,
    panel_key: str = "model_config",
    title: Optional[str] = None,
    exclude_params: Optional[List[str]] = None,
) -> Tuple[Optional[ModelSchema], Dict[str, Any]]:
    """
    Convenience function to render a complete model configuration panel.

    Args:
        model_id: Replicate model ID (owner/name)
        panel_key: Unique key prefix for this panel
        title: Optional title for the panel
        exclude_params: Parameters to hide

    Returns:
        Tuple of (schema or None, values dict)
    """
    generator = DynamicUIGenerator(key_prefix=panel_key)

    try:
        schema = generator.schema_service.get_schema(model_id)
    except ValueError as e:
        st.error(f"Failed to load model schema: {e}")
        return None, {}

    if title:
        st.subheader(title)
    else:
        st.subheader(schema.name)

    if schema.description:
        st.caption(
            schema.description[:200] + "..."
            if len(schema.description) > 200
            else schema.description
        )

    # Render controls
    values = generator.render_controls(schema, exclude_params=exclude_params)

    return schema, values
