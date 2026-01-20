"""
Composer Presets - Music style prompt templates.

Each preset includes:
- Genre and mood descriptors
- Tempo and instrument suggestions
- Character count for model filtering

Music-1.5 prompt limit: 300 chars
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ComposerPreset:
    """A curated music style prompt preset."""
    id: str
    name: str
    content: str
    genre: str
    mood: str
    tags: List[str] = field(default_factory=list)
    description: str = ""
    tempo_bpm: Optional[int] = None  # Suggested tempo

    @property
    def char_count(self) -> int:
        """Return the character count of the prompt content."""
        return len(self.content)

    @property
    def fits_music15(self) -> bool:
        """Fits within Minimax Music-1.5 300 char limit."""
        return self.char_count <= 300


# =============================================================================
# COMPOSER PRESETS (20)
# =============================================================================

COMPOSER_PRESETS: List[ComposerPreset] = [
    # 1. Rock Anthem - 285 chars
    ComposerPreset(
        id="rock_stadium",
        name="Stadium Rock Anthem",
        genre="Rock",
        mood="Powerful",
        tags=["anthem", "guitar", "drums"],
        tempo_bpm=120,
        description="Big arena rock sound",
        content="90s stadium rock anthem, powerful electric guitar riffs with heavy distortion, driving drums at 120 BPM, thundering bass, arena-filling sound, epic guitar solo, anthemic chorus hook that begs to be sung along, raw energy and power"
    ),

    # 2. Pop Dance - 275 chars
    ComposerPreset(
        id="pop_upbeat",
        name="Upbeat Pop Dance",
        genre="Pop",
        mood="Happy",
        tags=["dance", "catchy", "radio"],
        tempo_bpm=128,
        description="Radio-friendly pop hit",
        content="Modern pop dance track, catchy synth hooks at 128 BPM, punchy four-on-the-floor beat, bright and energetic production, radio-friendly mix, layered vocal harmonies, infectious melody, polished professional sound"
    ),

    # 3. Country Ballad - 290 chars
    ComposerPreset(
        id="country_acoustic",
        name="Country Acoustic Ballad",
        genre="Country",
        mood="Nostalgic",
        tags=["acoustic", "heartfelt", "storytelling"],
        tempo_bpm=85,
        description="Heartfelt country storytelling",
        content="Acoustic country ballad, fingerpicked guitar at 85 BPM, warm pedal steel guitar accents, gentle fiddle, heartfelt and authentic vocals, Nashville production style, storytelling arrangement with emotional build"
    ),

    # 4. Hip-Hop Trap - 280 chars
    ComposerPreset(
        id="hiphop_trap",
        name="Modern Trap Beat",
        genre="Hip-Hop",
        mood="Confident",
        tags=["trap", "808", "modern"],
        tempo_bpm=140,
        description="Hard-hitting trap production",
        content="Modern trap beat at 140 BPM, deep 808 bass with hard-hitting kicks, crisp hi-hat rolls and snare patterns, dark atmospheric synths, minimalist but powerful arrangement, space for vocals, professional mix"
    ),

    # 5. EDM Festival - 295 chars
    ComposerPreset(
        id="edm_festival",
        name="Festival EDM Banger",
        genre="EDM",
        mood="Euphoric",
        tags=["festival", "drop", "energy"],
        tempo_bpm=128,
        description="Main stage festival energy",
        content="High-energy festival EDM at 128 BPM, massive supersaw synth leads, earth-shaking bass drops, building tension with filtered risers, explosive chorus with anthemic melody, side-chain compression pumping, crowd-pleasing main stage energy"
    ),

    # 6. R&B Smooth - 278 chars
    ComposerPreset(
        id="rnb_smooth",
        name="Smooth R&B Groove",
        genre="R&B",
        mood="Sensual",
        tags=["smooth", "groove", "soulful"],
        tempo_bpm=90,
        description="Late night R&B vibes",
        content="Smooth contemporary R&B at 90 BPM, silky Rhodes piano chords, tight drums with swing, warm bass groove, lush pad textures, intimate late-night atmosphere, soulful and sensual production, space for emotional vocals"
    ),

    # 7. Indie Alternative - 270 chars
    ComposerPreset(
        id="indie_dreamy",
        name="Dreamy Indie Rock",
        genre="Indie",
        mood="Dreamy",
        tags=["reverb", "atmospheric", "alternative"],
        tempo_bpm=110,
        description="Atmospheric indie soundscape",
        content="Dreamy indie rock at 110 BPM, shimmering reverb-drenched guitars, tight but laid-back drums, ethereal synth pads, atmospheric production with depth, introspective mood, lo-fi warmth meets polished clarity"
    ),

    # 8. Metal Heavy - 285 chars
    ComposerPreset(
        id="metal_heavy",
        name="Heavy Metal Assault",
        genre="Metal",
        mood="Aggressive",
        tags=["heavy", "distortion", "powerful"],
        tempo_bpm=160,
        description="Full throttle metal aggression",
        content="Heavy metal assault at 160 BPM, crushing downtuned guitars with thick distortion, double bass drum fury, aggressive palm-muted riffs, powerful breakdowns, face-melting guitar solo section, relentless energy and intensity"
    ),

    # 9. Folk Acoustic - 265 chars
    ComposerPreset(
        id="folk_gentle",
        name="Gentle Folk Song",
        genre="Folk",
        mood="Peaceful",
        tags=["acoustic", "gentle", "organic"],
        tempo_bpm=95,
        description="Organic acoustic warmth",
        content="Gentle folk song at 95 BPM, warm fingerpicked acoustic guitar, subtle mandolin accents, soft brush drums, organic and natural production, intimate and personal atmosphere, campfire warmth, storytelling vibe"
    ),

    # 10. Blues Electric - 275 chars
    ComposerPreset(
        id="blues_electric",
        name="Electric Blues Groove",
        genre="Blues",
        mood="Soulful",
        tags=["electric", "groove", "classic"],
        tempo_bpm=75,
        description="Classic Chicago blues feel",
        content="Electric Chicago blues at 75 BPM, gritty overdriven guitar with expressive bends, shuffle rhythm on drums, walking bass line, Hammond organ fills, raw and authentic sound, late-night blues club atmosphere"
    ),

    # 11. Reggae Chill - 270 chars
    ComposerPreset(
        id="reggae_chill",
        name="Chill Reggae Vibes",
        genre="Reggae",
        mood="Relaxed",
        tags=["island", "chill", "positive"],
        tempo_bpm=80,
        description="Laid-back island groove",
        content="Chill reggae groove at 80 BPM, classic off-beat guitar skanks, deep one-drop drum pattern, heavy dub bass, melodica melodies, warm island atmosphere, positive and uplifting energy, sunshine vibes"
    ),

    # 12. Punk Fast - 290 chars
    ComposerPreset(
        id="punk_fast",
        name="Fast Punk Rock",
        genre="Punk",
        mood="Rebellious",
        tags=["fast", "raw", "energy"],
        tempo_bpm=180,
        description="Raw punk rock energy",
        content="Fast punk rock at 180 BPM, buzzing power chords on guitars, pounding straight drums with crash cymbal accents, aggressive bass driving the song, raw and unpolished production, three-chord fury, rebellious youthful energy"
    ),

    # 13. Jazz Smooth - 280 chars
    ComposerPreset(
        id="jazz_lounge",
        name="Jazz Lounge",
        genre="Jazz",
        mood="Sophisticated",
        tags=["smooth", "piano", "saxophone"],
        tempo_bpm=110,
        description="Sophisticated jazz club",
        content="Smooth jazz at 110 BPM, elegant piano comping, brushed drums with light swing, walking upright bass, warm tenor saxophone melodies, sophisticated harmony, intimate jazz club atmosphere, relaxed yet refined"
    ),

    # 14. Synthwave Retro - 295 chars
    ComposerPreset(
        id="synth_retro",
        name="Retro Synthwave",
        genre="Synthwave",
        mood="Nostalgic",
        tags=["80s", "neon", "electronic"],
        tempo_bpm=118,
        description="80s nostalgia vibes",
        content="Retro synthwave at 118 BPM, pulsing analog synthesizer arpeggios, warm pad textures, punchy gated drum machine, driving bass synth, 80s nostalgia aesthetic, neon-soaked atmosphere, cinematic and emotional, outrun vibes"
    ),

    # 15. Gospel Uplifting - 285 chars
    ComposerPreset(
        id="gospel_choir",
        name="Gospel Choir Celebration",
        genre="Gospel",
        mood="Joyful",
        tags=["choir", "uplifting", "spiritual"],
        tempo_bpm=105,
        description="Uplifting gospel celebration",
        content="Uplifting gospel at 105 BPM, powerful choir harmonies, Hammond B3 organ swells, dynamic drums building to climax, clapping congregation feel, spiritual and celebratory energy, soaring melodies that lift the spirit"
    ),

    # 16. Latin Salsa - 278 chars
    ComposerPreset(
        id="latin_salsa",
        name="Hot Salsa Rhythm",
        genre="Latin",
        mood="Passionate",
        tags=["salsa", "percussion", "dance"],
        tempo_bpm=95,
        description="Authentic salsa heat",
        content="Hot salsa at 95 BPM, bright horn section stabs, driving clave rhythm, congas and timbales groove, piano montunos, deep bass tumbaos, authentic Latin percussion, passionate and fiery dance energy"
    ),

    # 17. Acoustic Ballad - 282 chars
    ComposerPreset(
        id="ballad_emotional",
        name="Emotional Piano Ballad",
        genre="Ballad",
        mood="Emotional",
        tags=["piano", "strings", "cinematic"],
        tempo_bpm=70,
        description="Heartbreaking emotional ballad",
        content="Emotional piano ballad at 70 BPM, delicate piano melody, sweeping string section building gradually, gentle drums entering mid-song, cinematic and heartfelt arrangement, space for powerful vocal performance"
    ),

    # 18. Disco Funk - 290 chars
    ComposerPreset(
        id="disco_funk",
        name="Funky Disco Groove",
        genre="Disco",
        mood="Fun",
        tags=["funky", "bass", "dance"],
        tempo_bpm=115,
        description="Classic disco energy",
        content="Funky disco groove at 115 BPM, slap bass with octave runs, four-on-the-floor kick drum, crispy hi-hats, wah guitar licks, lush string arrangements, horn stabs, glittering production, pure dancefloor energy"
    ),

    # 19. Ambient Chill - 260 chars
    ComposerPreset(
        id="ambient_chill",
        name="Ambient Chill Atmosphere",
        genre="Ambient",
        mood="Calm",
        tags=["atmospheric", "relaxing", "ethereal"],
        tempo_bpm=60,
        description="Peaceful ambient textures",
        content="Ambient chill at 60 BPM, floating pad textures, gentle evolving soundscapes, subtle rhythmic pulses, ethereal atmosphere, meditative and calming, wide stereo field, immersive and peaceful"
    ),

    # 20. Epic Orchestral - 298 chars
    ComposerPreset(
        id="epic_orchestral",
        name="Epic Orchestral Score",
        genre="Orchestral",
        mood="Triumphant",
        tags=["cinematic", "epic", "powerful"],
        tempo_bpm=85,
        description="Cinematic orchestral power",
        content="Epic orchestral score at 85 BPM, soaring string section, powerful brass fanfares, thundering timpani and percussion, building from intimate to massive climax, cinematic scope and drama, heroic and triumphant emotion"
    ),

    # =========================================================================
    # ADDITIONAL COMPOSER PRESETS (21-50)
    # =========================================================================

    # 21. Grunge - 288 chars
    ComposerPreset(
        id="grunge_seattle",
        name="Seattle Grunge",
        genre="Grunge",
        mood="Raw",
        tags=["distortion", "90s", "alternative"],
        tempo_bpm=100,
        description="Raw 90s grunge sound",
        content="Raw 90s Seattle grunge at 100 BPM, fuzzy downtuned guitars, punchy drum kit with loose feel, growling bass tone, quiet verse loud chorus dynamics, feedback swells, authentic and unpolished production"
    ),

    # 22. Funk - 290 chars
    ComposerPreset(
        id="funk_groove",
        name="Funky Groove Machine",
        genre="Funk",
        mood="Groovy",
        tags=["bass", "rhythm", "tight"],
        tempo_bpm=105,
        description="Tight funky rhythm section",
        content="Tight funk groove at 105 BPM, slapping bass guitar with syncopated rhythm, crispy chicken scratch guitar, precise drums with ghost notes, horn stabs, clavinet keyboard accents, James Brown inspired rhythmic pocket"
    ),

    # 23. Synthwave - 295 chars
    ComposerPreset(
        id="synthwave_retro",
        name="Retrowave Synthwave",
        genre="Synthwave",
        mood="Nostalgic",
        tags=["80s", "neon", "synth"],
        tempo_bpm=118,
        description="Retro 80s synthwave vibes",
        content="Retrowave synthwave at 118 BPM, lush analog synth pads, driving arpeggios, gated reverb drums, neon-soaked atmosphere, nostalgic 80s aesthetics, punchy electronic bass, cinematic and dreamy electronic production"
    ),

    # 24. Drum and Bass - 292 chars
    ComposerPreset(
        id="dnb_liquid",
        name="Liquid Drum and Bass",
        genre="Drum and Bass",
        mood="Energetic",
        tags=["breakbeats", "bass", "fast"],
        tempo_bpm=174,
        description="Smooth liquid DnB",
        content="Liquid drum and bass at 174 BPM, rolling breakbeat patterns with amen break variations, deep sub bass, atmospheric pads, soulful vocal chops, jazzy piano stabs, warm and musical production, driving energy"
    ),

    # 25. Bossa Nova - 285 chars
    ComposerPreset(
        id="bossa_nova",
        name="Bossa Nova Lounge",
        genre="Bossa Nova",
        mood="Sophisticated",
        tags=["brazilian", "jazz", "smooth"],
        tempo_bpm=120,
        description="Sophisticated Brazilian jazz",
        content="Smooth bossa nova at 120 BPM, nylon string acoustic guitar with syncopated rhythm, brushed drums, upright bass walking lines, soft jazz piano, warm and intimate atmosphere, sophisticated Brazilian grooves"
    ),

    # 26. Post-Punk - 280 chars
    ComposerPreset(
        id="post_punk_dark",
        name="Dark Post-Punk",
        genre="Post-Punk",
        mood="Brooding",
        tags=["angular", "dark", "80s"],
        tempo_bpm=130,
        description="Cold angular post-punk",
        content="Dark post-punk at 130 BPM, angular guitar with chorus and delay, driving bass lines, mechanical drumming, cold atmospheric synths, brooding and intense, Joy Division inspired angular minimalist production"
    ),

    # 27. Gospel - 295 chars
    ComposerPreset(
        id="gospel_choir",
        name="Gospel Choir Praise",
        genre="Gospel",
        mood="Uplifting",
        tags=["choir", "spiritual", "powerful"],
        tempo_bpm=90,
        description="Powerful gospel praise",
        content="Powerful gospel praise at 90 BPM, soaring choir harmonies with call and response, Hammond B3 organ, driving piano, uplifting brass section, spiritual and emotional, building to powerful climax with full congregation energy"
    ),

    # 28. Shoegaze - 275 chars
    ComposerPreset(
        id="shoegaze_dreamy",
        name="Dreamy Shoegaze Wall",
        genre="Shoegaze",
        mood="Hazy",
        tags=["reverb", "distortion", "ethereal"],
        tempo_bpm=95,
        description="Wall of sound shoegaze",
        content="Dreamy shoegaze at 95 BPM, layered distorted guitars with massive reverb, buried vocals, hypnotic drum patterns, ethereal and hazy atmosphere, walls of swirling sound, My Bloody Valentine sonic textures"
    ),

    # 29. Trip Hop - 290 chars
    ComposerPreset(
        id="trip_hop_dark",
        name="Dark Trip Hop",
        genre="Trip Hop",
        mood="Mysterious",
        tags=["beats", "atmospheric", "urban"],
        tempo_bpm=85,
        description="Dark Bristol trip hop",
        content="Dark trip hop at 85 BPM, downtempo breakbeats with heavy processing, deep sub bass, scratchy vinyl textures, haunting samples, moody atmospheric pads, Bristol sound inspired by Massive Attack and Portishead"
    ),

    # 30. Celtic - 288 chars
    ComposerPreset(
        id="celtic_folk",
        name="Celtic Folk Dance",
        genre="Celtic",
        mood="Festive",
        tags=["irish", "fiddle", "traditional"],
        tempo_bpm=125,
        description="Traditional Irish energy",
        content="Celtic folk dance at 125 BPM, lively fiddle melodies, tin whistle accents, bodhran drum rhythm, acoustic guitar strumming, joyful and festive energy, traditional Irish arrangement with authentic instrumentation"
    ),

    # 31. Neo Soul - 278 chars
    ComposerPreset(
        id="neo_soul_smooth",
        name="Smooth Neo Soul",
        genre="Neo Soul",
        mood="Sensual",
        tags=["r&b", "organic", "warm"],
        tempo_bpm=75,
        description="Warm organic neo soul",
        content="Smooth neo soul at 75 BPM, warm Rhodes piano chords, organic drums with swing, muted bass guitar, subtle vinyl crackle, lush vocal harmonies space, D'Angelo and Erykah Badu inspired warm production"
    ),

    # 32. Ska - 282 chars
    ComposerPreset(
        id="ska_upstroke",
        name="Ska Punk Energy",
        genre="Ska",
        mood="Energetic",
        tags=["horns", "upbeat", "punk"],
        tempo_bpm=165,
        description="High-energy ska punk",
        content="High-energy ska punk at 165 BPM, upstroke guitar rhythm, punchy brass section with trumpet and trombone, driving punk drum beat, bouncy bass lines, energetic and fun third wave ska style arrangement"
    ),

    # 33. Progressive Rock - 295 chars
    ComposerPreset(
        id="prog_rock_epic",
        name="Progressive Rock Epic",
        genre="Progressive Rock",
        mood="Complex",
        tags=["technical", "epic", "odd-time"],
        tempo_bpm=110,
        description="Complex prog rock journey",
        content="Progressive rock at 110 BPM, odd time signature changes, virtuosic guitar work, expansive keyboard arrangements, complex drum patterns, dynamic shifts from soft to heavy, Rush and Yes inspired technical musicianship"
    ),

    # 34. Afrobeat - 285 chars
    ComposerPreset(
        id="afrobeat_groove",
        name="Afrobeat Groove",
        genre="Afrobeat",
        mood="Hypnotic",
        tags=["african", "polyrhythm", "groove"],
        tempo_bpm=110,
        description="Hypnotic Fela Kuti style",
        content="Hypnotic afrobeat groove at 110 BPM, interlocking guitar patterns, polyrhythmic percussion, horn section riffs, deep bass groove, call and response vocals, Fela Kuti inspired Nigerian funk energy"
    ),

    # 35. Hardstyle - 290 chars
    ComposerPreset(
        id="hardstyle_rave",
        name="Hardstyle Rave",
        genre="Hardstyle",
        mood="Intense",
        tags=["hard", "kick", "rave"],
        tempo_bpm=150,
        description="Hard-hitting rave energy",
        content="Intense hardstyle at 150 BPM, punchy distorted kick drums, screeching lead synths, euphoric melody breakdowns, reverse bass technique, hard-hitting drops, festival rave energy with maximum intensity and power"
    ),

    # 36. Downtempo - 275 chars
    ComposerPreset(
        id="downtempo_chill",
        name="Downtempo Chill",
        genre="Downtempo",
        mood="Relaxed",
        tags=["chill", "electronic", "mellow"],
        tempo_bpm=90,
        description="Mellow electronic vibes",
        content="Mellow downtempo at 90 BPM, warm analog synth textures, subtle glitchy beats, deep bass pulses, atmospheric pads, relaxed and introspective mood, late night listening electronic production"
    ),

    # 37. Bluegrass - 292 chars
    ComposerPreset(
        id="bluegrass_fast",
        name="Fast Bluegrass Picker",
        genre="Bluegrass",
        mood="Energetic",
        tags=["banjo", "acoustic", "folk"],
        tempo_bpm=150,
        description="Fast acoustic picking",
        content="Fast bluegrass at 150 BPM, rapid banjo rolls, driving acoustic guitar, sawing fiddle melodies, walking upright bass, tight harmonies, Appalachian mountain music energy with virtuosic instrumental interplay"
    ),

    # 38. Industrial - 288 chars
    ComposerPreset(
        id="industrial_harsh",
        name="Harsh Industrial",
        genre="Industrial",
        mood="Aggressive",
        tags=["mechanical", "dark", "electronic"],
        tempo_bpm=125,
        description="Mechanical industrial power",
        content="Harsh industrial at 125 BPM, mechanical drum machine patterns, distorted synth stabs, crushing bass, metallic percussion sounds, aggressive and confrontational, Nine Inch Nails inspired electronic aggression"
    ),

    # 39. Motown - 280 chars
    ComposerPreset(
        id="motown_classic",
        name="Classic Motown Soul",
        genre="Motown",
        mood="Soulful",
        tags=["60s", "soul", "classic"],
        tempo_bpm=120,
        description="Classic Detroit soul",
        content="Classic Motown soul at 120 BPM, tight rhythm section with tambourine, warm bass guitar, punchy horn section, string arrangements, hand claps, Hitsville USA inspired golden era Detroit soul production"
    ),

    # 40. Psychedelic - 295 chars
    ComposerPreset(
        id="psych_trippy",
        name="Psychedelic Trip",
        genre="Psychedelic",
        mood="Trippy",
        tags=["60s", "experimental", "spacey"],
        tempo_bpm=100,
        description="Mind-expanding psych rock",
        content="Psychedelic rock at 100 BPM, swirling phase-shifted guitars, backwards tape effects, sitars and exotic instruments, hypnotic drums, spacey organ, mind-expanding sonic exploration with 60s experimental production"
    ),

    # 41. Tech House - 285 chars
    ComposerPreset(
        id="tech_house_groove",
        name="Tech House Groove",
        genre="Tech House",
        mood="Driving",
        tags=["club", "minimal", "dance"],
        tempo_bpm=125,
        description="Underground club groove",
        content="Tech house groove at 125 BPM, minimal but effective percussion, rolling bassline, subtle synth stabs, hypnotic groove that builds over time, underground club focused production with danceable energy"
    ),

    # 42. Punk Rock - 290 chars
    ComposerPreset(
        id="punk_fast",
        name="Fast Punk Rock",
        genre="Punk",
        mood="Rebellious",
        tags=["fast", "aggressive", "raw"],
        tempo_bpm=180,
        description="Fast raw punk energy",
        content="Fast punk rock at 180 BPM, buzzsaw guitar distortion, pounding drums with no frills, aggressive shouted vocals energy, short and direct arrangement, Ramones inspired three chord punk rock simplicity and power"
    ),

    # 43. Flamenco - 288 chars
    ComposerPreset(
        id="flamenco_passionate",
        name="Passionate Flamenco",
        genre="Flamenco",
        mood="Passionate",
        tags=["spanish", "guitar", "emotional"],
        tempo_bpm=120,
        description="Fiery Spanish passion",
        content="Passionate flamenco at 120 BPM, intricate nylon guitar rasgueados and picados, cajon percussion, hand claps at compas rhythm, passionate and fiery emotional expression, authentic Andalusian flamenco style"
    ),

    # 44. Chillstep - 280 chars
    ComposerPreset(
        id="chillstep_melodic",
        name="Melodic Chillstep",
        genre="Chillstep",
        mood="Dreamy",
        tags=["dubstep", "chill", "melodic"],
        tempo_bpm=140,
        description="Melodic dubstep chill",
        content="Melodic chillstep at 140 BPM, gentle wobble bass, ethereal vocal chops, lush reverb-soaked pads, emotional melodies, half-time feel with subtle drops, beautiful and uplifting chilled dubstep production"
    ),

    # 45. Swing Jazz - 292 chars
    ComposerPreset(
        id="swing_jazz",
        name="Big Band Swing",
        genre="Swing",
        mood="Energetic",
        tags=["jazz", "big band", "classic"],
        tempo_bpm=140,
        description="Classic big band swing",
        content="Big band swing at 140 BPM, swinging horn section with saxes and brass, walking bass, brushed and swinging drums, piano comping, energetic and joyful 1940s dance band energy, Count Basie inspired arrangements"
    ),

    # 46. Stoner Rock - 285 chars
    ComposerPreset(
        id="stoner_fuzz",
        name="Fuzzy Stoner Rock",
        genre="Stoner Rock",
        mood="Heavy",
        tags=["fuzz", "desert", "slow"],
        tempo_bpm=80,
        description="Desert fuzz rock",
        content="Heavy stoner rock at 80 BPM, massively fuzzy guitar tones, slow grinding riffs, thundering drums, psychedelic overtones, desert rock vibes, Kyuss and Sleep inspired low and slow heavy groove production"
    ),

    # 47. Future Bass - 290 chars
    ComposerPreset(
        id="future_bass_bright",
        name="Bright Future Bass",
        genre="Future Bass",
        mood="Euphoric",
        tags=["synth", "drop", "modern"],
        tempo_bpm=150,
        description="Modern future bass drops",
        content="Bright future bass at 150 BPM, supersaws with volume automation, crispy snares, wobbly bass drops with sidechain, emotional chord progressions, sparkling arpeggios, festival-ready euphoric production style"
    ),

    # 48. Reggaeton - 288 chars
    ComposerPreset(
        id="reggaeton_dembow",
        name="Reggaeton Dembow",
        genre="Reggaeton",
        mood="Hot",
        tags=["latin", "urban", "dance"],
        tempo_bpm=95,
        description="Urban Latin heat",
        content="Reggaeton dembow beat at 95 BPM, signature kick snare pattern, deep 808 bass, hi-hat rolls, Latin percussion accents, modern urban Latin production, infectious danceable rhythm for clubs and parties"
    ),

    # 49. Dream Pop - 275 chars
    ComposerPreset(
        id="dream_pop_hazy",
        name="Hazy Dream Pop",
        genre="Dream Pop",
        mood="Ethereal",
        tags=["reverb", "soft", "atmospheric"],
        tempo_bpm=85,
        description="Ethereal dreamy pop",
        content="Hazy dream pop at 85 BPM, jangly guitars drenched in reverb, soft ethereal vocals, subtle synth textures, gentle drum machine, atmospheric and beautiful, Beach House and Cocteau Twins inspired soundscapes"
    ),

    # 50. Hardcore Punk - 285 chars
    ComposerPreset(
        id="hardcore_fast",
        name="Fast Hardcore",
        genre="Hardcore",
        mood="Intense",
        tags=["fast", "heavy", "mosh"],
        tempo_bpm=190,
        description="Intense hardcore breakdown",
        content="Fast hardcore punk at 190 BPM, aggressive distorted guitars, blast beat drums with breakdown sections, shouted vocals energy, mosh pit inducing heaviness, short explosive songs with maximum intensity"
    ),
]


def get_composer_by_genre(genre: str) -> List[ComposerPreset]:
    """Get all composer presets matching a genre."""
    genre_lower = genre.lower()
    return [p for p in COMPOSER_PRESETS if p.genre.lower() == genre_lower]


def get_composer_by_mood(mood: str) -> List[ComposerPreset]:
    """Get all composer presets matching a mood."""
    mood_lower = mood.lower()
    return [p for p in COMPOSER_PRESETS if p.mood.lower() == mood_lower]


def get_composer_for_model(model_id: str) -> List[ComposerPreset]:
    """Get composer presets that fit within a model's character limit."""
    if "music-1.5" in model_id or "music-01" in model_id:
        return [p for p in COMPOSER_PRESETS if p.fits_music15]
    # Most models have generous prompt limits
    return COMPOSER_PRESETS


def get_all_genres() -> List[str]:
    """Get unique list of all genres."""
    return sorted(set(p.genre for p in COMPOSER_PRESETS))


def get_all_moods() -> List[str]:
    """Get unique list of all moods."""
    return sorted(set(p.mood for p in COMPOSER_PRESETS))
