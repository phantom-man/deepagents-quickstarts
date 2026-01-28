"""Preset creative directives for the Streamlit GUI."""

from typing import Dict, List

_DIRECTOR_PROMPT_PRESETS: List[Dict[str, object]] = [
    {
        "key": "multi_segment_product_launch",
        "title": "Product Launch Multi-Clip Campaign",
        "description": "Three hero clips highlighting a premium tech device, ideal for social cutdowns.",
        "video_models": ["veo-3.1-fast-generate-001", "wan-video/wan-2.5-t2v-fast"],
        "audio_models": ["minimax/music-1.5", "lucataco/ace-step"],
        "prompt": (
            "Director Goal: Deliver a 30-second campaign for the new Orion AR glasses.\n"
            "Cinematographer: Produce THREE distinct 8-second clips (Clip A/B/C) that can be delivered as separate video files.\n"
            " Clip A: cinematic macro shot of the glasses activating holographic UI.\n"
            " Clip B: lifestyle wide shot with a diverse creator using the glasses in a neon city.\n"
            " Clip C: energetic montage of quick cuts showing product features (battery, lenses, gesture control).\n"
            "Composer: Create an energetic synthwave track at 96 BPM with rising intensity to support product launches, export full mix and 10-second sting.\n"
            "Editor: Sequence clips A->B->C with quick glitch transitions and align beat drops to clip cuts."
        ),
    },
    {
        "key": "ecommerce_cosmetics_spot",
        "title": "E-commerce Beauty Spot",
        "description": "15s glossy promo for a cosmetics line with upbeat pop music.",
        "video_models": ["veo-3.1-fast-generate-001"],
        "audio_models": ["minimax/music-1.5"],
        "prompt": (
            "Create a 15-second commercial for the Solara Glow skincare collection.\n"
            "Cinematographer: one continuous 15s hero shot starting on product macro, transitioning to model application, ending on floating text CTA.\n"
            " Use warm golden hour lighting and subtle particle effects.\n"
            "Composer: deliver a 15s upbeat pop groove with light vocal chops and a clean button ending."
        ),
    },
    {
        "key": "music_video_alt_pop",
        "title": "Alt-Pop Music Video Concept",
        "description": "Visual and audio brief for a moody alt-pop single.",
        "video_models": ["wan-video/wan-2.5-t2v-fast"],
        "audio_models": ["lucataco/ace-step"],
        "prompt": (
            "Develop a 60-second alt-pop music video for the song 'Satellite Hearts'.\n"
            "Cinematographer: deliver a stylized visual arc with three scenes (verse rooftop night, chorus neon tunnel, bridge zero-gravity shot).\n"
            "Composer: produce a full 60-second arrangement at 82 BPM with airy female vocals, atmospheric pads, and a soaring chorus."
        ),
    },
    {
        "key": "youtube_explainer",
        "title": "YouTube Explainer Segment",
        "description": "Animated explainer for a consumer fintech product.",
        "video_models": ["veo-3.1-fast-generate-001"],
        "audio_models": ["minimax/music-1.5"],
        "prompt": (
            "Produce a 90-second YouTube explainer for 'Nimbus', a budgeting app.\n"
            "Cinematographer: generate animated UI walkthroughs, on-screen text, and B-roll of users managing finances. Keep graphics brand colors #2E7CFB and #F2F6FF.\n"
            "Composer: deliver an unobtrusive lo-fi background track at 92 BPM plus a 5-second logo sting."
        ),
    },
    {
        "key": "docu_brand_story",
        "title": "Documentary Brand Story",
        "description": "Mini-doc style narrative for a sustainable fashion label.",
        "video_models": ["veo-3.1-fast-generate-001"],
        "audio_models": ["lucataco/ace-step", "minimax/music-1.5"],
        "prompt": (
            "Craft a 2-minute documentary profile of 'Verdant Loom', a sustainable fashion collective.\n"
            "Cinematographer: combine interview-style shots, atelier b-roll, and location footage of reclaimed textile sourcing.\n"
            "Composer: produce an intimate acoustic underscore with piano, light percussion, and evolving textures."
        ),
    },
    {
        "key": "event_hype_reel",
        "title": "Conference Hype Reel",
        "description": "High-energy recap for a tech summit, optimized for vertical cuts.",
        "video_models": ["wan-video/wan-2.5-t2v-fast"],
        "audio_models": ["minimax/music-1.5"],
        "prompt": (
            "Assemble a 45-second hype reel for the 'FutureStack' developer summit.\n"
            "Cinematographer: capture crowd shots, keynote moments, expo booths, and night events with dynamic camera moves. Deliver both 16:9 master and 9:16 crops.\n"
            "Composer: create a hybrid electronic/rock score at 128 BPM with big risers and hits synchronized to key transitions."
        ),
    },
    {
        "key": "real_estate_walkthrough",
        "title": "Real Estate Walkthrough",
        "description": "Calm, detailed tour of a luxury property with narration bed.",
        "video_models": ["veo-3.1-fast-generate-001"],
        "audio_models": ["lucataco/ace-step"],
        "prompt": (
            "Produce a 3-minute guided walkthrough for the Azure Heights penthouse.\n"
            "Cinematographer: slow gimbal moves through foyer, living area, kitchen, bedrooms, rooftop. Highlight architectural details with callout overlays.\n"
            "Composer: score a relaxed piano and strings bed at 70 BPM, include a loopable 20-second ambient mix for narration."
        ),
    },
    {
        "key": "short_form_social_pack",
        "title": "Short-Form Social Pack",
        "description": "Five quick bursts optimized for TikTok/Reels challenges.",
        "video_models": ["wan-video/wan-2.5-t2v-fast", "veo-3.1-fast-generate-001"],
        "audio_models": ["minimax/music-1.5"],
        "prompt": (
            "Create a bundle of FIVE 6-second vertical clips promoting the #GlowUp fitness challenge.\n"
            "Cinematographer: each clip should feature a different workout move, bold typography, and swipe-up CTA. Export as separate assets labeled Clip1-Clip5.\n"
            "Composer: craft a 30-second high-energy beat with clap accents and provide a 6-second sting for transitions."
        ),
    },
    {
        "key": "podcast_intro_audio_first",
        "title": "Podcast Intro (Audio-First)",
        "description": "Audio identity package with minimal supporting visuals.",
        "video_models": ["veo-3.1-fast-generate-001"],
        "audio_models": ["lucataco/ace-step", "minimax/music-1.5"],
        "prompt": (
            "Develop branding for the 'Signal Shift' tech podcast.\n"
            "Composer: produce a 30-second intro theme, a 10-second bumper, and a 5-second outro, blending analog synth and modern percussion.\n"
            "Cinematographer: create a loopable waveform visualization and abstract tech background to accompany the intro."
        ),
    },
    {
        "key": "cinematic_trailer",
        "title": "Cinematic Trailer",
        "description": "Epic teaser for a sci-fi streaming series with dramatic score.",
        "video_models": ["veo-3.1-fast-generate-001"],
        "audio_models": ["lucataco/ace-step"],
        "prompt": (
            "Produce a 60-second teaser trailer for the sci-fi series 'Eclipse Frontier'.\n"
            "Cinematographer: deliver a three-act structure (setup, escalation, climax) with title cards and end slate. Include at least one cosmic exterior, one command center scene, and one hero close-up.\n"
            "Composer: score an epic hybrid orchestral track with braams, ticking percussion, and a climax at 55 seconds."
        ),
    },
]


def get_director_prompt_presets() -> List[Dict[str, object]]:
    """Return preset creative directives for the GUI."""
    return _DIRECTOR_PROMPT_PRESETS
