"""
Multi-Configuration Component - Dynamic UI for generating multiple outputs.

This component renders N sets of configuration forms, allowing users to
specify independent parameters for each file to be generated.
"""
# pylint: disable=line-too-long
import streamlit as st
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from DeepAgents.services.ui_generator import ModelSchema

from DeepAgents.services.ui_generator import DynamicUIGenerator
from DeepAgents.gui.components.char_counter import text_area_with_counter


def render_multi_config_panel(
    agent_type: str,
    model_id: str,
    schema: "ModelSchema",
    count: int,
    key_prefix: str,
    current_configs: Optional[List[Dict[str, Any]]] = None,
    text_fields: Optional[List[str]] = None,
    exclude_params: Optional[List[str]] = None
) -> List[Dict[str, Any]]:
    """
    Render N configuration panels for multi-file generation.
    
    Args:
        agent_type: "cinematographer" or "composer"
        model_id: The selected model ID
        schema: The OpenAPI schema for the model
        count: Number of configurations to render
        key_prefix: Unique prefix for widget keys
        current_configs: Existing configurations to populate
        text_fields: List of text field names (e.g., ["prompt", "lyrics"])
        exclude_params: Schema parameters to exclude from UI
        
    Returns:
        List of N configuration dicts
    """
    if current_configs is None:
        current_configs = []
    if text_fields is None:
        text_fields = []
    if exclude_params is None:
        exclude_params = []
    
    # Ensure we have enough configs
    while len(current_configs) < count:
        current_configs.append({})
    
    # Trim excess configs if count decreased
    if len(current_configs) > count:
        current_configs = current_configs[:count]
    
    configs = []
    
    for idx in range(count):
        with st.expander(f"🎬 {agent_type.title()} #{idx + 1} Configuration", expanded=(idx == 0)):
            config = current_configs[idx] if idx < len(current_configs) else {}
            
            # Create unique UI generator for this config with indexed key_prefix
            ui_generator_indexed = DynamicUIGenerator(key_prefix=f"{key_prefix}_multi_{idx}")
            
            # Render text fields with character counters
            for field_name in text_fields:
                field_info = _get_field_info(field_name, agent_type, model_id)
                
                st.markdown(f"**{field_info['label']}**")
                
                # Get current value
                current_value = config.get(field_name, "")
                widget_key = f"{key_prefix}_multi_{idx}_{field_name}"
                
                # Render text area with counter
                value = text_area_with_counter(
                    label="",  # Label already shown above
                    key=widget_key,
                    max_chars=field_info['max_chars'],
                    height=field_info['height'],
                    default_value=current_value,
                    help_text=field_info['help']
                )
                
                config[field_name] = value
            
            # Render schema-based parameters (duration, guidance, etc.)
            st.markdown("---")
            st.markdown("**Model Parameters**")
            
            schema_params = ui_generator_indexed.render_controls(
                schema,
                current_values=config,
                exclude_params=exclude_params + text_fields,  # Exclude text fields already rendered
                columns=2
            )
            
            # Merge schema params into config
            config.update(schema_params)
            configs.append(config)
    
    return configs


def _get_field_info(field_name: str, agent_type: str, model_id: str) -> Dict[str, Any]:
    """Get metadata for text input fields."""
    defaults = {
        "prompt": {
            "label": "🎥 Video Prompt" if agent_type == "cinematographer" else "🎵 Music Style Prompt",
            "max_chars": 500,
            "height": 100,
            "help": "Describe the visual scene or music style"
        },
        "lyrics": {
            "label": "🎤 Lyrics",
            "max_chars": 600,
            "height": 150,
            "help": "Song lyrics (leave empty for instrumental)"
        }
    }
    
    # Model-specific overrides
    if "veo" in model_id.lower():
        defaults["prompt"]["max_chars"] = 1000
    elif "luma" in model_id.lower():
        defaults["prompt"]["max_chars"] = 700
    elif "music-1.5" in model_id.lower() or "music-01" in model_id.lower():
        defaults["lyrics"]["max_chars"] = 600
        defaults["prompt"]["max_chars"] = 300
    elif "ace-step" in model_id.lower():
        defaults["lyrics"]["max_chars"] = 3000
        defaults["prompt"]["max_chars"] = 500
    
    return defaults.get(field_name, {
        "label": field_name.replace("_", " ").title(),
        "max_chars": 500,
        "height": 100,
        "help": ""
    })
