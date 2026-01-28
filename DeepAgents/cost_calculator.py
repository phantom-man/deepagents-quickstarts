# pylint: disable=import-error
# pylint: disable=no-name-in-module
"""
Service to calculate estimated costs for agent operations.
Aggregates pricing data from ModelRegistry and applies logic based on configuration quotas.
"""

try:
    from DeepAgents.model_registry import get_model_info
except ImportError:
    # Fallback to local import if run as script in folder
    from model_registry import get_model_info

# Base Costs for LLMs (Approx per task wrapper)
LLM_BASE_COST = {
    "Google": 0.002,  # Gemini 1.5 approx input/output per turn
    "Anthropic": 0.01,  # Claude 3.5 Sonnet
}


def get_config_value(config, agent_name, key, default=None):
    """Helper to safely get nested config."""
    return config.get(agent_name, {}).get(key, default)


def _estimate_composer(config, total, details):
    """Estimates cost for Composer Agent."""
    agent_name = "Composer"
    # Check Audio Model
    model_key = get_config_value(config, agent_name, "model", "minimax/music-01")

    # Look up in registry
    info = get_model_info("audio", model_key)
    if info and "pricing" in info:
        pricing = info["pricing"]
        if isinstance(pricing, dict):
            cost = pricing.get("cost", 0)
            pricing_type = pricing.get("type", "run")
            if pricing_type == "run":
                total += cost
                details.append(f"Audio Gen ({info['name']}): ${cost:.4f} per run")
            elif pricing_type == "second":
                # Get duration
                duration = get_config_value(config, agent_name, "duration", 30)
                cost = duration * cost
                total += cost
                details.append(f"Audio Gen ({info['name']}): ${cost:.4f} ({duration}s)")
    else:
        # Default MusicGen Fallback
        cost = 30 * 0.001
        total += cost
        details.append(f"Audio Gen (Standard): ${cost:.4f}")
    return total


def _estimate_cinematographer(config, total, details):
    """Estimates cost for Cinematographer Agent."""
    agent_name = "Cinematographer"
    # Video Cost
    vid_prov = get_config_value(config, agent_name, "video_provider", "Google")
    vid_model = get_config_value(
        config, agent_name, "video_model", "veo-2.0-generate-001"
    )

    if vid_prov == "Replicate":
        info = get_model_info("video", vid_model)
        if info and "pricing" in info:
            pricing = info["pricing"]
            if isinstance(pricing, dict):
                pricing_type = pricing.get("type", "")
                if pricing_type == "second":
                    # Duration? Replicate models usually have `num_frames` / `fps`
                    fps = get_config_value(config, agent_name, "fps", 24)
                    frames = get_config_value(config, agent_name, "num_frames", 24)
                    duration = frames / fps
                    cost = duration * pricing.get("cost", 0)
                    total += cost
                    details.append(
                        f"Video Gen ({info['name']}): ${cost:.4f} (~{duration:.1f}s)"
                    )
    elif vid_prov == "Google":
        # Veo
        cost = 5.0 * 0.50  # Assume 5s * $0.50
        total += cost
        details.append(f"Video Gen (Veo): ${cost:.2f} (Est. 5s)")
    return total


def _estimate_director(config, total, details):
    """Estimates cost for Director Agent."""
    agent_name = "Director"
    # Director calls Research + Composite Production
    # Hard to predict exactly, but let's assume maximum quotas

    # 1. Research Call
    res_cost = 0.01  # Approx
    total += res_cost
    details.append(f"Research Sub-task: ${res_cost:.3f}")

    # 2. Composer Call (1 Song)
    # Recurse? Or just assume defaults
    comp_cost = 0.15  # Minimax + LLM
    total += comp_cost
    details.append(f"Music Production (Est): ${comp_cost:.3f}")

    # 3. Cinematographer Calls (Quota)
    max_shots = get_config_value(config, agent_name, "max_shots", 2)
    shot_duration = get_config_value(config, agent_name, "duration", 5)

    # We need to know WHICH model the Cinematographer is configured to use
    cine_vid_prov = get_config_value(
        config, "Cinematographer", "video_provider", "Google"
    )

    shot_cost = 0.0
    if cine_vid_prov == "Google":
        shot_cost = shot_duration * 0.50
    else:
        # Simplified estimate for others
        shot_cost = shot_duration * 0.05

    total_shots_cost = max_shots * shot_cost
    total += total_shots_cost
    details.append(
        f"Video Production (Max {max_shots} shots, {shot_duration}s ea): ${total_shots_cost:.2f}"
    )
    return total


def estimate_cost(agent_name, config):
    """
    Returns a dictionary with cost details:
    {
        "total_min": float,
        "total_max": float,
        "details": [str],
        "currency": "$"
    }
    """
    details = []
    total = 0.0

    # 1. Base Agent LLM Cost
    provider = get_config_value(config, agent_name, "provider", "Google")
    llm_cost = LLM_BASE_COST.get(provider, 0.002)
    total += llm_cost
    details.append(f"{agent_name} Logic (LLM): ${llm_cost:.4f}")

    # 2. Specific Agent Logic
    if agent_name == "Composer":
        total = _estimate_composer(config, total, details)
    elif agent_name == "Cinematographer":
        total = _estimate_cinematographer(config, total, details)
    elif agent_name == "Director":
        total = _estimate_director(config, total, details)

    return {"total_max": round(total, 4), "details": details, "currency": "$"}
