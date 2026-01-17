# Active Context

## Current Focus

**Schema-Driven Dynamic UI System - IMPLEMENTED**

- Status: **New Architecture Complete** - Services package created with schema fetching, dynamic UI, validation.
- Objective: Zero-touch configuration where UI auto-generates from model OpenAPI schemas.
- GUI: Cinematographer and Composer sections with active checkboxes, model selectors, dynamic parameters.

## Recent Changes

- **Schema-Driven UI Architecture (2026-01-17)**:
  - **Requirement**: User requested Agency page with Cinematographer/Composer sections that dynamically populate controls from model schemas.
  - **Philosophy**: Zero-Touch (UI auto-configures) + Fail-Fast (errors surface immediately).
  - **Solution**: Created new `DeepAgents/services/` package with four modules.

- **New Files Created**:
  - `services/schema_service.py` - Fetches OpenAPI schemas from Replicate API, parses to `ControlDefinition` objects.
  - `services/ui_generator.py` - `DynamicUIGenerator` creates Streamlit widgets from schemas.
  - `services/asset_validator.py` - Validates uploaded files (MIME type, size, duration).
  - `services/model_registry.py` - Curated catalog of 15 AI models (video, music, voice, image).
  - `gui/agency_sections.py` - `render_cinematographer_section()`, `render_composer_section()`.

- **Key Features**:
  - Active checkboxes to enable/disable Cinematographer and Composer agents.
  - Model dropdown populated from registry with tier/capability info.
  - Dynamic parameter expanders that auto-generate sliders, selects, checkboxes from schema.
  - Storyboard generation option with image model selector.
  - Voice dependency resolution - detects if music model needs voice, offers generate/upload/select.
  - Green/red validation indicators for uploaded files.
  - Config pass-through: GUI -> AgentRunner -> Graph -> Agent nodes.

- **Modified Files**:
  - `gui/app.py` - Integrated agency sections into Agency tab.
  - `gui/agent_runner.py` - `stream_agency_graph()` accepts and passes agency_config.
  - `graphs/agency_graph.py` - Cinematographer/Composer nodes read config, skip if inactive.
  - `CommercialAgents/cinematographer_agent/agent.py` - `run_cinematographer_task()` accepts model params.
  - `CommercialAgents/composer_agent/agent.py` - `run_composer_task()` accepts model + voice params.

- **Pylint Score**: 9.82/10 after trailing whitespace cleanup.

## Architecture Notes

### Schema Service Flow

1. GUI selects model from registry
2. `SchemaService.get_schema(model_id)` fetches from Replicate API
3. Schema parsed to `ControlDefinition` list with type, min/max, options
4. `DynamicUIGenerator.render_controls()` creates Streamlit widgets
5. Values collected and passed through `agency_config` dict

### Model Registry Categories

- VIDEO: Wan 2.5 Fast, Luma Ray Flash 2, Minimax Video-01
- AUDIO_MUSIC: Lyria-002, ACE-Step, Minimax Music-01, MusicGen
- AUDIO_VOICE: Minimax Speech-01, XTTS-v2, Kokoro
- IMAGE: FLUX Schnell/Pro, SDXL, SDXL Lightning, Imagen 3

### Caching Strategy

- Memory cache: In-process dict, instant lookup
- Disk cache: JSON files in `.cache/schemas/`, 24-hour TTL
- Fail-fast: If schema fetch fails, raise immediately

## Active Questions / Issues

- TODO: Actually wire model_id/params to underlying Replicate calls in agents.
- TODO: Implement voice generation chain when composer needs voice reference.

## Next Steps

1. **Test New UI**: Launch Streamlit, verify sections render correctly.
2. **Commit & Push**: Save all changes to remote.
3. **Wire Model Params**: Complete integration so selected model actually gets used.
