"""
Director Presets - Story concept and narrative prompt templates.

Each preset includes:
- Story concept and tone descriptors
- Genre and theme specifications
- Scene structure suggestions

These provide high-level creative direction for the Director agent
to coordinate Cinematographer and Composer outputs.
"""

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class DirectorPreset:
    """A curated story concept preset for Director agent."""

    id: str
    name: str
    content: str
    genre: str
    tone: str
    tags: List[str] = field(default_factory=list)
    description: str = ""
    suggested_duration: Optional[int] = None  # Suggested video length in seconds
    music_style_hint: Optional[str] = None  # Hint for Composer

    @property
    def char_count(self) -> int:
        """Return the character count of the content."""
        return len(self.content)


# =============================================================================
# DIRECTOR PRESETS (30)
# =============================================================================

DIRECTOR_PRESETS: List[DirectorPreset] = [
    # 1. Hero's Journey - Adventure
    DirectorPreset(
        id="hero_journey",
        name="Hero's Journey",
        genre="Adventure",
        tone="Epic",
        tags=["hero", "journey", "transformation", "epic"],
        description="Classic hero's journey narrative arc",
        suggested_duration=60,
        music_style_hint="Epic orchestral with building intensity",
        content="""Create an epic hero's journey narrative:

OPENING: Ordinary world - show the protagonist in their mundane life, hint at restlessness
CATALYST: Call to adventure - an unexpected event disrupts everything
RISING ACTION: Trials and challenges - montage of obstacles overcome
CLIMAX: The ultimate test - face the greatest fear
RESOLUTION: Transformation complete - return changed, wiser, stronger

Visual style: Cinematic wide shots transitioning to intimate close-ups at emotional peaks
Pacing: Start contemplative, build momentum, explosive climax, peaceful resolution""",
    ),
    # 2. Love Story - Romance
    DirectorPreset(
        id="love_story",
        name="Love Story",
        genre="Romance",
        tone="Heartfelt",
        tags=["love", "romance", "emotion", "connection"],
        description="Romantic love story arc",
        suggested_duration=45,
        music_style_hint="Soft acoustic transitioning to sweeping strings",
        content="""Create a touching love story narrative:

OPENING: Two separate lives - show loneliness or incompleteness
MEETING: Fateful encounter - eyes meet, time slows
FALLING: Growing connection - shared moments, laughter, vulnerability
OBSTACLE: Conflict or separation - tension, doubt, distance
REUNION: Love conquers - emotional reconciliation

Visual style: Warm color palette, soft focus romantic moments, golden hour lighting
Pacing: Gentle beginning, playful middle, bittersweet tension, joyful resolution""",
    ),
    # 3. Thriller Chase - Action
    DirectorPreset(
        id="thriller_chase",
        name="Thriller Chase",
        genre="Action/Thriller",
        tone="Intense",
        tags=["chase", "tension", "danger", "escape"],
        description="High-stakes pursuit sequence",
        suggested_duration=30,
        music_style_hint="Driving electronic beats with tension building",
        content="""Create an intense chase/pursuit narrative:

OPENING: Calm before storm - establish normalcy about to shatter
TRIGGER: Danger appears - protagonist must flee NOW
PURSUIT: Relentless chase - obstacles, near-misses, escalating danger
CORNERED: Nowhere to run - all seems lost
ESCAPE: Clever solution - unexpected way out, survival

Visual style: Handheld urgency, quick cuts, motion blur, dutch angles
Pacing: Quick establishing, sustained high tension, brief relief moments, explosive finale""",
    ),
    # 4. Mystery Reveal - Suspense
    DirectorPreset(
        id="mystery_reveal",
        name="Mystery Reveal",
        genre="Mystery",
        tone="Suspenseful",
        tags=["mystery", "clues", "reveal", "suspense"],
        description="Mystery unfolding to revelation",
        suggested_duration=45,
        music_style_hint="Ambient tension with piano, building unease",
        content="""Create a mysterious revelation narrative:

OPENING: Something is wrong - establish unsettling atmosphere
INVESTIGATION: Gathering clues - protagonist notices strange details
DEEPENING: The rabbit hole - each answer raises more questions
REALIZATION: Pieces connect - the terrible truth becomes clear
REVELATION: Full picture - shocking understanding, changed perspective

Visual style: Shadows and light contrast, slow reveals, focus pulls to key details
Pacing: Slow burn atmosphere, methodical investigation, accelerating toward truth""",
    ),
    # 5. Coming of Age - Drama
    DirectorPreset(
        id="coming_of_age",
        name="Coming of Age",
        genre="Drama",
        tone="Nostalgic",
        tags=["youth", "growth", "nostalgia", "change"],
        description="Youth to maturity transition story",
        suggested_duration=60,
        music_style_hint="Indie folk or nostalgic pop",
        content="""Create a coming-of-age narrative:

OPENING: Innocence - carefree youth, summer days, simple joys
AWAKENING: World expands - first experiences of adult complexity
STRUGGLE: Identity crisis - who am I becoming? Conflict with old self
LOSS: End of innocence - something precious is lost forever
ACCEPTANCE: Mature understanding - embrace the bittersweet growth

Visual style: Warm nostalgic color grade, home video aesthetics, intimate moments
Pacing: Leisurely nostalgic opening, emotional turbulence, reflective resolution""",
    ),
    # 6. Nature Documentary - Documentary
    DirectorPreset(
        id="nature_doc",
        name="Nature Documentary",
        genre="Documentary",
        tone="Majestic",
        tags=["nature", "wildlife", "planet", "wonder"],
        description="Planet Earth style nature piece",
        suggested_duration=60,
        music_style_hint="Orchestral with natural sound design",
        content="""Create a nature documentary narrative:

OPENING: Establish habitat - sweeping vista of the ecosystem
INTRODUCTION: Meet the subject - intimate look at featured creature or landscape
DAILY LIFE: Behavior showcase - hunting, feeding, interaction, survival
DRAMA: Nature's struggle - predator/prey, weather, competition
RESOLUTION: Circle of life - balance restored, life continues

Visual style: Cinematic wide establishing shots, macro detail, golden hour beauty
Pacing: Slow contemplative observation, sudden action bursts, peaceful conclusions""",
    ),
    # 7. Horror Tension - Horror
    DirectorPreset(
        id="horror_tension",
        name="Horror Tension",
        genre="Horror",
        tone="Terrifying",
        tags=["horror", "fear", "tension", "dread"],
        description="Building dread horror sequence",
        suggested_duration=45,
        music_style_hint="Dark ambient, dissonant tones, silence",
        content="""Create a horror tension narrative:

OPENING: False safety - establish normalcy that feels slightly wrong
UNEASE: Something's off - small wrongness noticed, easily dismissed
ESCALATION: Can't ignore - undeniable strangeness, growing fear
TERROR: Full horror - the threat reveals itself
AFTERMATH: Survival uncertain - escape or doom, lingering dread

Visual style: Deep shadows, limited lighting, uncomfortable framing, subtle wrongness
Pacing: Slow creeping dread, prolonged tension, sudden shocks, no easy resolution""",
    ),
    # 8. Triumph Story - Inspirational
    DirectorPreset(
        id="triumph_story",
        name="Triumph Over Adversity",
        genre="Inspirational",
        tone="Uplifting",
        tags=["triumph", "struggle", "victory", "inspiration"],
        description="Overcoming impossible odds",
        suggested_duration=60,
        music_style_hint="Building from somber to triumphant orchestral",
        content="""Create an inspirational triumph narrative:

OPENING: Rock bottom - show the lowest point, all seems hopeless
SPARK: Tiny hope - something or someone provides small inspiration
STRUGGLE: The climb - setbacks and small victories, persistent effort
BREAKTHROUGH: Turning point - finally something works, momentum builds
TRIUMPH: Victory achieved - emotional payoff, celebration of perseverance

Visual style: Dark to light progression, intimate struggle to grand triumph
Pacing: Heavy emotional opening, grinding middle, explosive triumphant climax""",
    ),
    # 9. Sci-Fi Discovery - Science Fiction
    DirectorPreset(
        id="scifi_discovery",
        name="First Contact",
        genre="Science Fiction",
        tone="Awe-inspiring",
        tags=["space", "discovery", "alien", "wonder"],
        description="Encounter with the unknown",
        suggested_duration=60,
        music_style_hint="Ambient space, building wonder, otherworldly",
        content="""Create a sci-fi discovery narrative:

OPENING: Mundane space - routine mission or observation
ANOMALY: Something unexpected - readings that don't make sense
INVESTIGATION: Approaching the unknown - tension and wonder mixed
CONTACT: First sight - the alien/discovery revealed, overwhelming awe
AFTERMATH: Changed forever - humanity's place in universe reconsidered

Visual style: Hard sci-fi realism, scale contrast, alien beauty
Pacing: Methodical buildup, mounting wonder, breathtaking reveal, contemplative end""",
    ),
    # 10. Comedy Mishap - Comedy
    DirectorPreset(
        id="comedy_mishap",
        name="Comedy of Errors",
        genre="Comedy",
        tone="Hilarious",
        tags=["comedy", "mishap", "funny", "chaos"],
        description="Escalating comedic disaster",
        suggested_duration=30,
        music_style_hint="Upbeat, playful, comedic timing accents",
        content="""Create an escalating comedy narrative:

OPENING: Simple goal - protagonist needs to accomplish something basic
FIRST MISHAP: Minor problem - easily fixable, slightly embarrassing
ESCALATION: Fix causes problems - each solution creates bigger mess
CHAOS PEAK: Everything goes wrong - maximum comedic disaster
RESOLUTION: Unexpected success - somehow it all works out (or spectacularly doesn't)

Visual style: Clear staging for physical comedy, reactive close-ups, timing-focused
Pacing: Quick setup, escalating rhythm, machine-gun complications, satisfying payoff""",
    ),
    # 11. War Story - War/Drama
    DirectorPreset(
        id="war_story",
        name="Band of Brothers",
        genre="War",
        tone="Somber",
        tags=["war", "brothers", "sacrifice", "honor"],
        description="Soldiers' bond in combat",
        suggested_duration=60,
        music_style_hint="Somber orchestral, military themes, emotional strings",
        content="""Create a war narrative focusing on human bonds:

OPENING: Before battle - quiet moment, soldiers as humans with hopes/fears
CALL TO ACTION: Mission begins - duty calls, fear masked by resolve
COMBAT: Hell of war - chaos, loss, moments of courage
SACRIFICE: Ultimate price - someone gives everything for others
REMEMBRANCE: After - survivors carry the memory, honor the fallen

Visual style: Desaturated palette, visceral combat, intimate human moments
Pacing: Quiet humanity, explosive action, devastating loss, reflective honor""",
    ),
    # 12. Sports Glory - Sports
    DirectorPreset(
        id="sports_glory",
        name="Championship Moment",
        genre="Sports",
        tone="Triumphant",
        tags=["sports", "championship", "team", "victory"],
        description="The big game narrative",
        suggested_duration=45,
        music_style_hint="Building energy, stadium rock, triumphant finale",
        content="""Create a sports championship narrative:

OPENING: Stakes established - what this game means, history, pressure
EARLY STRUGGLE: Behind - team facing adversity, doubt creeping in
RALLYING: Finding strength - coach speech, teammate moment, renewed fight
FINAL PUSH: Comeback begins - momentum shifts, crowd energy builds
VICTORY: Championship moment - the winning play, celebration explosion

Visual style: Dynamic sports cinematography, slow-mo key moments, crowd energy
Pacing: Tense opening, desperate middle, building momentum, explosive victory""",
    ),
    # 13. Cyberpunk Future - Sci-Fi
    DirectorPreset(
        id="cyberpunk_future",
        name="Neon Dystopia",
        genre="Cyberpunk",
        tone="Gritty",
        tags=["cyberpunk", "dystopia", "neon", "rebellion"],
        description="Near-future dystopian story",
        suggested_duration=45,
        music_style_hint="Synthwave, industrial electronic, dark beats",
        content="""Create a cyberpunk narrative:

OPENING: Dystopian normal - show the oppressive neon-lit world
PROTAGONIST: Outsider revealed - someone who doesn't fit the system
DISCOVERY: Truth uncovered - the dark secret behind the gleaming facade
DECISION: Fight or comply - moment of choice, rebellion or submission
ACTION: Strike against system - consequences of standing up

Visual style: Neon and shadow contrast, rain-slicked streets, tech-noir aesthetic
Pacing: Atmospheric world-building, personal stakes, explosive action""",
    ),
    # 14. Family Reunion - Drama
    DirectorPreset(
        id="family_reunion",
        name="Coming Home",
        genre="Drama",
        tone="Emotional",
        tags=["family", "reunion", "forgiveness", "home"],
        description="Family reconciliation story",
        suggested_duration=45,
        music_style_hint="Acoustic emotional, piano, heartfelt",
        content="""Create a family reunion narrative:

OPENING: Distance established - show the separation, what was lost
RETURN: Coming back - the difficult journey home, nervousness
TENSION: Old wounds - past conflicts surface, awkward moments
BREAKING POINT: Confrontation - finally addressing what drove them apart
HEALING: Forgiveness - emotional breakthrough, family restored

Visual style: Warm domestic settings, intimate framing, memory flashbacks
Pacing: Hesitant beginning, building tension, emotional climax, warm resolution""",
    ),
    # 15. Fantasy Quest - Fantasy
    DirectorPreset(
        id="fantasy_quest",
        name="Quest for Magic",
        genre="Fantasy",
        tone="Magical",
        tags=["fantasy", "magic", "quest", "adventure"],
        description="Fantasy adventure quest",
        suggested_duration=60,
        music_style_hint="Epic fantasy orchestral, Celtic influences",
        content="""Create a fantasy quest narrative:

OPENING: Ordinary village - humble beginnings, destiny calling
CALL: Prophecy or need - why the quest must begin now
JOURNEY: Magical lands - encounter wonders and dangers
TRIAL: Ultimate challenge - test of character and courage
TRIUMPH: Magic achieved - the goal reached, world transformed

Visual style: Lush fantasy landscapes, magical lighting, epic scale
Pacing: Humble start, wonder-filled journey, climactic confrontation, magical resolution""",
    ),
    # 16. Time Travel - Sci-Fi
    DirectorPreset(
        id="time_travel",
        name="Time Paradox",
        genre="Science Fiction",
        tone="Mind-bending",
        tags=["time", "paradox", "past", "future"],
        description="Time travel consequences story",
        suggested_duration=45,
        music_style_hint="Electronic with temporal distortion effects",
        content="""Create a time travel narrative:

OPENING: Present problem - something that must be changed
JUMP: Travel to past - disorientation, different era
INTERFERENCE: Changing history - the attempt to fix things
CONSEQUENCES: Ripple effects - unintended results of changes
RESOLUTION: Accept or adapt - living with the new timeline

Visual style: Visual distortion for travel, period-accurate settings, parallel editing
Pacing: Urgent setup, disorienting jumps, mounting complications, mind-bending resolution""",
    ),
    # 17. Heist Plan - Crime
    DirectorPreset(
        id="heist_plan",
        name="The Perfect Heist",
        genre="Crime/Thriller",
        tone="Slick",
        tags=["heist", "crime", "clever", "team"],
        description="Ocean's Eleven style heist",
        suggested_duration=60,
        music_style_hint="Cool jazz, spy-thriller, stylish beats",
        content="""Create a heist narrative:

OPENING: The target - establish the impossible prize
ASSEMBLY: The team - introduce specialists with unique skills
PLANNING: The scheme - reveal the clever plan layer by layer
EXECUTION: Going live - things go wrong, improvisation required
REVEAL: The twist - the real plan was different all along

Visual style: Slick split screens, stylish transitions, cool color palette
Pacing: Stylish setup, methodical planning, tense execution, satisfying twist""",
    ),
    # 18. Survival Story - Adventure
    DirectorPreset(
        id="survival_story",
        name="Survival Against Odds",
        genre="Survival/Adventure",
        tone="Gritty",
        tags=["survival", "nature", "determination", "alone"],
        description="Human vs nature survival",
        suggested_duration=60,
        music_style_hint="Minimal, natural sounds, sparse emotional cues",
        content="""Create a survival narrative:

OPENING: Disaster strikes - the incident that strands protagonist
ASSESSMENT: Taking stock - what resources exist, how bad is it
STRUGGLE: Daily survival - finding food, shelter, fighting elements
CRISIS: Near death - the moment when hope nearly dies
RESCUE/TRIUMPH: Found or escape - survival achieved through will

Visual style: Raw naturalistic, weather as character, intimate POV
Pacing: Shocking opening, grinding survival, near-breaking point, triumphant rescue""",
    ),
    # 19. Musical Performance - Music
    DirectorPreset(
        id="musical_performance",
        name="Concert Experience",
        genre="Music/Performance",
        tone="Electric",
        tags=["concert", "music", "performance", "energy"],
        description="Live music experience",
        suggested_duration=45,
        music_style_hint="Match the performance genre",
        content="""Create a concert/performance narrative:

OPENING: Anticipation - crowd gathering, backstage nerves
BUILD: Taking stage - lights, crowd roar, first notes
PERFORMANCE: Musical journey - different songs/movements, crowd connection
PEAK: The moment - that transcendent song where everyone is one
ENCORE: Finale - emotional goodbye, lasting impact

Visual style: Dynamic concert cinematography, crowd energy, artist intimacy
Pacing: Building anticipation, sustained energy, emotional peaks, satisfying conclusion""",
    ),
    # 20. Meditation Journey - Wellness
    DirectorPreset(
        id="meditation_journey",
        name="Inner Peace Journey",
        genre="Wellness/Meditation",
        tone="Serene",
        tags=["meditation", "peace", "mindfulness", "calm"],
        description="Guided meditation visual",
        suggested_duration=60,
        music_style_hint="Ambient, nature sounds, gentle tones",
        content="""Create a meditation journey narrative:

OPENING: Chaos of life - brief glimpse of stress and noise
TRANSITION: Beginning to breathe - slowing down, finding center
JOURNEY: Inner landscape - beautiful calming imagery, nature
DEEPENING: Pure peace - abstract beauty, complete stillness
RETURN: Carrying peace - bringing calm back to the world

Visual style: Soft focus, gentle movement, calming colors, nature beauty
Pacing: Brief tension, gradual slowing, sustained peace, gentle awakening""",
    ),
    # 21. Revenge Tale - Thriller
    DirectorPreset(
        id="revenge_tale",
        name="Vengeance Path",
        genre="Thriller",
        tone="Dark",
        tags=["revenge", "justice", "dark", "driven"],
        description="Quest for vengeance",
        suggested_duration=45,
        music_style_hint="Dark, driving, relentless",
        content="""Create a revenge narrative:

OPENING: The wrong - show the injustice that demands revenge
DESCENT: Becoming hunter - transformation from victim to avenger
PURSUIT: Closing in - tracking, planning, eliminating obstacles
CONFRONTATION: Face to face - finally reaching the target
COST: Victory's price - revenge achieved but at what cost?

Visual style: Noir lighting, cold color palette, intense close-ups
Pacing: Traumatic setup, methodical pursuit, intense confrontation, hollow victory""",
    ),
    # 22. Environmental Story - Documentary
    DirectorPreset(
        id="environmental_story",
        name="Our Planet",
        genre="Documentary",
        tone="Urgent",
        tags=["environment", "climate", "nature", "hope"],
        description="Environmental awareness piece",
        suggested_duration=60,
        music_style_hint="Emotional orchestral, building urgency to hope",
        content="""Create an environmental narrative:

OPENING: Beauty - showcase Earth's stunning natural wonders
WARNING: Damage revealed - show the impact of human activity  
EVIDENCE: Science speaks - undeniable proof of crisis
SOLUTIONS: Hope exists - people working to fix problems
CALL: Our choice - inspire action, show what's possible

Visual style: Stunning nature contrasted with damage, human stories
Pacing: Awe-inspiring beauty, concerning evidence, hopeful solutions""",
    ),
    # 23. Dance Story - Performance
    DirectorPreset(
        id="dance_story",
        name="Dance of Emotions",
        genre="Dance/Performance",
        tone="Expressive",
        tags=["dance", "emotion", "movement", "art"],
        description="Dance as emotional narrative",
        suggested_duration=45,
        music_style_hint="Match dance style - contemporary, classical, etc.",
        content="""Create a dance narrative:

OPENING: Stillness - the dancer before movement, potential energy
AWAKENING: First movement - emotion begins to express through body
JOURNEY: Full expression - complete emotional range through dance
CLIMAX: Peak intensity - the most powerful movement moment
RESOLUTION: Return to stillness - transformed, emotion released

Visual style: Follow movement fluidly, capture full body and detail, dramatic lighting
Pacing: Match music perfectly, build through movements, satisfying stillness""",
    ),
    # 24. Underdog Story - Drama
    DirectorPreset(
        id="underdog_story",
        name="Against All Odds",
        genre="Drama",
        tone="Inspiring",
        tags=["underdog", "unlikely", "heart", "determination"],
        description="Unlikely hero rises",
        suggested_duration=60,
        music_style_hint="Heart-swelling inspirational, building triumph",
        content="""Create an underdog narrative:

OPENING: Written off - show why nobody believes in protagonist
DREAM: Secret ambition - the goal everyone says is impossible
EFFORT: Working harder - while others doubt, protagonist trains
SETBACK: Nearly quit - the moment defeat seems certain
TRIUMPH: Proving them wrong - achieving what nobody thought possible

Visual style: Intimate struggle, contrast small hero vs big challenge
Pacing: Dismissive setup, grinding work, devastating setback, glorious triumph""",
    ),
    # 25. Lost Love - Drama
    DirectorPreset(
        id="lost_love",
        name="Memories of You",
        genre="Drama/Romance",
        tone="Melancholic",
        tags=["loss", "memory", "love", "grief"],
        description="Remembering lost love",
        suggested_duration=45,
        music_style_hint="Melancholic piano, strings, bittersweet",
        content="""Create a lost love narrative:

OPENING: Empty present - show the absence, the void left behind
MEMORIES: Happy past - beautiful flashbacks of love that was
GRIEF: The loss - how it happened, the moment of separation
ACCEPTANCE: Learning to live - carrying love while moving forward
PEACE: Always with me - love remains even when person is gone

Visual style: Present desaturated, memories warm and vibrant, contrast grief/joy
Pacing: Lonely present, warm memories, painful loss, bittersweet acceptance""",
    ),
    # 26. Robot Story - Sci-Fi
    DirectorPreset(
        id="robot_story",
        name="Machine Heart",
        genre="Science Fiction",
        tone="Poignant",
        tags=["robot", "AI", "humanity", "soul"],
        description="AI discovering humanity",
        suggested_duration=45,
        music_style_hint="Electronic with emotional organic elements",
        content="""Create an AI/robot emotional narrative:

OPENING: Pure machine - cold efficiency, programmed purpose
GLITCH: Something unexpected - first hint of something more
AWAKENING: Feeling begins - confusion at new sensations
UNDERSTANDING: What is this? - learning what emotions mean
TRANSCENDENCE: More than code - becoming truly alive

Visual style: Clinical tech to warm humanity, POV from machine perspective
Pacing: Cold efficiency, curious exploration, emotional breakthrough""",
    ),
    # 27. Childhood Memory - Drama
    DirectorPreset(
        id="childhood_memory",
        name="Summer of '89",
        genre="Drama",
        tone="Nostalgic",
        tags=["childhood", "summer", "memory", "innocence"],
        description="Specific childhood memory",
        suggested_duration=45,
        music_style_hint="Period-appropriate, nostalgic, bittersweet",
        content="""Create a childhood memory narrative:

OPENING: Adult trigger - something reminds of long-ago summer
TRANSPORT: Back in time - suddenly young again, that specific place
EXPERIENCE: The memory - relive the significant moment in detail
MEANING: Why it mattered - understand now what couldn't then
RETURN: Present wisdom - carrying childhood lessons into now

Visual style: Period-accurate details, dreamy memory quality, intimate scale
Pacing: Quick trigger, immersive memory, emotional realization, wistful return""",
    ),
    # 28. Ocean Depths - Documentary
    DirectorPreset(
        id="ocean_depths",
        name="Deep Blue Unknown",
        genre="Documentary",
        tone="Mysterious",
        tags=["ocean", "deep", "unknown", "discovery"],
        description="Deep ocean exploration",
        suggested_duration=60,
        music_style_hint="Ambient, mysterious, otherworldly",
        content="""Create a deep ocean narrative:

OPENING: Surface world - familiar ocean, sunlit waters
DESCENT: Going deeper - pressure increases, light fades
TWILIGHT ZONE: Alien begins - strange creatures appear
ABYSS: Complete darkness - bioluminescence, bizarre life
REVELATION: New discovery - something never seen before

Visual style: Gradual darkness, spot lighting, alien beauty
Pacing: Familiar beginning, wonder-filled descent, awe-inspiring depths""",
    ),
    # 29. Apocalypse - Sci-Fi/Drama
    DirectorPreset(
        id="apocalypse_story",
        name="End of Days",
        genre="Post-Apocalyptic",
        tone="Somber",
        tags=["apocalypse", "survival", "humanity", "end"],
        description="Facing the end of everything",
        suggested_duration=60,
        music_style_hint="Haunting, sparse, emotional devastation to hope",
        content="""Create an apocalypse narrative:

OPENING: Last normal day - the world as we knew it, final time
COLLAPSE: It begins - the event that ends everything
SURVIVAL: New world - navigating the aftermath, loss everywhere
HUMANITY: What remains - finding connection amid destruction
HOPE: Dawn after - seeds of rebuilding, human spirit endures

Visual style: Contrast beautiful past with destroyed present, intimate human moments
Pacing: Idyllic opening, devastating collapse, grinding survival, hopeful glimmer""",
    ),
    # 30. Artist's Vision - Art
    DirectorPreset(
        id="artist_vision",
        name="Creative Process",
        genre="Art/Documentary",
        tone="Inspiring",
        tags=["art", "creative", "process", "vision"],
        description="Artist's creative journey",
        suggested_duration=45,
        music_style_hint="Match the art form, contemplative to triumphant",
        content="""Create an artistic process narrative:

OPENING: Blank canvas - the intimidating beginning, endless possibility
STRUGGLE: Creative block - the difficulty of bringing vision to life
BREAKTHROUGH: Finding it - the moment inspiration strikes
CREATION: Flow state - the work pouring out, fully absorbed
COMPLETION: Standing back - seeing the finished vision realized

Visual style: Close process details, artist's hands at work, final reveal
Pacing: Contemplative start, frustrated struggle, flowing creation, proud completion""",
    ),
]


def get_director_by_genre(genre: str) -> List[DirectorPreset]:
    """Get all director presets matching a genre."""
    genre_lower = genre.lower()
    return [p for p in DIRECTOR_PRESETS if p.genre.lower() == genre_lower]


def get_director_by_tone(tone: str) -> List[DirectorPreset]:
    """Get all director presets matching a tone."""
    tone_lower = tone.lower()
    return [p for p in DIRECTOR_PRESETS if p.tone.lower() == tone_lower]


def get_director_for_model(model_id: str) -> List[DirectorPreset]:
    """
    Get director presets that fit within a model's character limit.

    Director presets are generally model-agnostic since they're
    high-level story concepts, so return all presets.
    """
    # Director presets work with any model - they're narrative guides
    return DIRECTOR_PRESETS


def get_all_genres() -> List[str]:
    """Get unique list of all genres."""
    return sorted(set(p.genre for p in DIRECTOR_PRESETS))


def get_all_tones() -> List[str]:
    """Get unique list of all tones."""
    return sorted(set(p.tone for p in DIRECTOR_PRESETS))
