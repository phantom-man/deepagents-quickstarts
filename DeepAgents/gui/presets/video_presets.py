"""
Video Presets - Cinematographer visual prompt templates.

Each preset includes:
- Scene type and camera movement descriptors
- Lighting and mood specifications
- Character count for model filtering

Wan 2.5 prompt limit: ~500 chars recommended
Veo 3.1 prompt limit: ~1000 chars
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class VideoPreset:
    """A curated video prompt preset for Cinematographer."""
    id: str
    name: str
    content: str
    category: str  # aerial, action, portrait, nature, urban, etc.
    mood: str
    tags: List[str] = field(default_factory=list)
    description: str = ""
    camera_movement: Optional[str] = None  # pan, tilt, tracking, static, etc.
    lighting: Optional[str] = None  # natural, dramatic, neon, soft, etc.

    @property
    def char_count(self) -> int:
        """Return the character count of the prompt content."""
        return len(self.content)

    @property
    def fits_wan(self) -> bool:
        """Fits within Wan 2.5 ~500 char recommendation."""
        return self.char_count <= 500

    @property
    def fits_veo(self) -> bool:
        """Fits within Veo 3.1 ~1000 char limit."""
        return self.char_count <= 1000


# =============================================================================
# VIDEO PRESETS (50)
# =============================================================================

VIDEO_PRESETS: List[VideoPreset] = [
    # 1. Aerial City - 485 chars
    VideoPreset(
        id="aerial_city_night",
        name="Neon City Aerial",
        category="Aerial",
        mood="Cyberpunk",
        tags=["city", "night", "neon", "flying"],
        camera_movement="Descending",
        lighting="Neon",
        description="Cyberpunk city flyover at night",
        content="Cinematic aerial shot descending through a neon-lit cyberpunk metropolis at night, rain falling through colorful holographic billboards, flying cars streak past camera, reflections on wet streets below, camera slowly spiraling down between towering skyscrapers, atmospheric fog catching neon lights, high detail futuristic architecture"
    ),

    # 2. Nature Sunrise - 450 chars
    VideoPreset(
        id="nature_sunrise",
        name="Mountain Sunrise",
        category="Nature",
        mood="Majestic",
        tags=["mountains", "sunrise", "epic", "landscape"],
        camera_movement="Slow pan",
        lighting="Golden hour",
        description="Epic mountain sunrise landscape",
        content="Breathtaking slow pan across snow-capped mountain peaks at sunrise, golden light breaking through clouds, mist rolling through valleys below, dramatic shadows across rocky faces, cinematic wide angle establishing shot, pristine natural beauty, lens flare from rising sun, 8K quality"
    ),

    # 3. Action Chase - 475 chars
    VideoPreset(
        id="action_chase",
        name="Car Chase Pursuit",
        category="Action",
        mood="Intense",
        tags=["car", "chase", "speed", "urban"],
        camera_movement="Tracking",
        lighting="Night streetlights",
        description="High-speed chase sequence",
        content="Fast-paced tracking shot following a sleek sports car racing through city streets at night, camera mounted low to ground, sparks flying from wheels, streetlights streaking past, reflections on wet asphalt, sharp turns through narrow alleys, intense motion blur on background, cinematic action movie quality"
    ),

    # 4. Portrait Dramatic - 420 chars
    VideoPreset(
        id="portrait_dramatic",
        name="Dramatic Portrait",
        category="Portrait",
        mood="Intense",
        tags=["face", "emotion", "close-up", "drama"],
        camera_movement="Slow zoom",
        lighting="Dramatic",
        description="Emotional close-up portrait",
        content="Slow zoom into dramatic close-up of a weathered face, deep expressive eyes telling a story, single shaft of light cutting through darkness, dust particles floating in beam, subtle facial movements, raw emotional intensity, cinematic shallow depth of field, film grain texture"
    ),

    # 5. Ocean Wave - 460 chars
    VideoPreset(
        id="ocean_wave",
        name="Crashing Wave",
        category="Nature",
        mood="Powerful",
        tags=["ocean", "wave", "water", "slow-motion"],
        camera_movement="Static underwater",
        lighting="Natural sunlight",
        description="Powerful wave crashing in slow motion",
        content="Massive ocean wave curling and crashing in slow motion, camera half submerged showing above and below waterline, sunlight piercing through translucent water, foam and spray frozen in time, underwater bubbles rising, powerful natural force captured in cinematic detail, crystal clear water quality"
    ),

    # 6. Forest Walk - 440 chars
    VideoPreset(
        id="forest_walk",
        name="Enchanted Forest Path",
        category="Nature",
        mood="Mystical",
        tags=["forest", "path", "magical", "atmosphere"],
        camera_movement="Forward tracking",
        lighting="Dappled sunlight",
        description="Walking through magical forest",
        content="First-person walking through an enchanted forest, sunbeams filtering through ancient tree canopy, floating particles of light like fireflies, moss-covered stones along the path, mysterious fog in the distance, otherworldly atmosphere, nature documentary quality cinematography"
    ),

    # 7. Space Station - 490 chars
    VideoPreset(
        id="space_station",
        name="Orbital Station View",
        category="Sci-Fi",
        mood="Awe-inspiring",
        tags=["space", "station", "earth", "orbit"],
        camera_movement="Slow orbit",
        lighting="Earth glow",
        description="Space station with Earth view",
        content="Slow orbit around a massive space station, curved Earth horizon filling background with blue glow, solar panels glinting in sunlight, astronauts visible through windows, stars wheeling slowly past, realistic zero-gravity movement, hard science fiction aesthetic, NASA documentary cinematography style"
    ),

    # 8. Urban Street - 430 chars
    VideoPreset(
        id="urban_street",
        name="Busy City Street",
        category="Urban",
        mood="Vibrant",
        tags=["city", "crowd", "day", "movement"],
        camera_movement="Dolly through",
        lighting="Overcast daylight",
        description="Bustling city street life",
        content="Smooth dolly shot moving through crowded city street at walking pace, diverse pedestrians passing both directions, shop fronts and street vendors, natural everyday activity, urban documentary style, shallow depth creating bokeh background, authentic metropolitan atmosphere"
    ),

    # 9. Desert Dunes - 455 chars
    VideoPreset(
        id="desert_dunes",
        name="Sahara Dunes",
        category="Nature",
        mood="Serene",
        tags=["desert", "dunes", "sand", "minimalist"],
        camera_movement="Slow ascending",
        lighting="Sunset",
        description="Vast desert landscape at sunset",
        content="Slow ascending aerial view over endless golden sand dunes at sunset, long shadows creating patterns, wind lifting fine sand particles, pristine untouched wilderness, vast scale and emptiness, warm orange and purple sky gradient, Planet Earth documentary cinematography"
    ),

    # 10. Rain Window - 400 chars
    VideoPreset(
        id="rain_window",
        name="Rainy Window View",
        category="Atmospheric",
        mood="Melancholic",
        tags=["rain", "window", "mood", "indoor"],
        camera_movement="Static",
        lighting="Overcast gray",
        description="Rain droplets on window",
        content="Close-up of rain droplets running down glass window, blurred city lights visible through distortion, interior warmth contrasting with gray outside, contemplative mood, shallow focus on water rivulets, cinematic color grade, ASMR visual quality"
    ),

    # 11. Concert Stage - 480 chars
    VideoPreset(
        id="concert_stage",
        name="Rock Concert Stage",
        category="Performance",
        mood="Electric",
        tags=["concert", "stage", "lights", "music"],
        camera_movement="Dynamic crane",
        lighting="Stage lights",
        description="Epic concert performance",
        content="Dynamic crane shot sweeping across massive concert stage, colorful laser beams cutting through fog, stadium crowd with sea of phone lights, spotlights sweeping, confetti cannons firing, silhouette of performer against bright backlights, live music event energy, concert film quality"
    ),

    # 12. Underwater Coral - 465 chars
    VideoPreset(
        id="underwater_coral",
        name="Coral Reef Dive",
        category="Nature",
        mood="Peaceful",
        tags=["underwater", "coral", "fish", "diving"],
        camera_movement="Smooth glide",
        lighting="Filtered sunlight",
        description="Vibrant coral reef exploration",
        content="Smooth underwater glide through vibrant coral reef, schools of colorful tropical fish parting for camera, shafts of sunlight dancing through crystal clear water, sea turtles swimming past, delicate coral formations in vivid colors, Blue Planet documentary style, professional underwater cinematography"
    ),

    # 13. Thunderstorm - 440 chars
    VideoPreset(
        id="thunderstorm_field",
        name="Prairie Thunderstorm",
        category="Weather",
        mood="Dramatic",
        tags=["storm", "lightning", "weather", "dramatic"],
        camera_movement="Time-lapse",
        lighting="Storm light",
        description="Approaching thunderstorm",
        content="Time-lapse of massive thunderstorm cell approaching across open prairie, multiple lightning strikes illuminating roiling clouds, dark wall cloud advancing, golden wheat field in foreground, storm chaser documentary style, dramatic atmospheric phenomena"
    ),

    # 14. Food Close-up - 380 chars
    VideoPreset(
        id="food_closeup",
        name="Gourmet Food Reveal",
        category="Product",
        mood="Appetizing",
        tags=["food", "cooking", "detail", "luxury"],
        camera_movement="Slow reveal",
        lighting="Soft studio",
        description="Luxurious food cinematography",
        content="Slow cinematic reveal of gourmet dish, steam rising elegantly, sauce drizzling in slow motion, fresh ingredients glistening, shallow depth highlighting textures, professional food photography lighting, commercial advertising quality"
    ),

    # 15. Snowfall Night - 425 chars
    VideoPreset(
        id="snowfall_night",
        name="Snowy Night Street",
        category="Atmospheric",
        mood="Cozy",
        tags=["snow", "night", "winter", "peaceful"],
        camera_movement="Static with snow",
        lighting="Warm streetlamps",
        description="Peaceful snowy night scene",
        content="Heavy snowflakes falling slowly through warm streetlight glow, quiet empty street at night, fresh snow accumulating on surfaces, cozy windows with soft light, winter wonderland atmosphere, magical holiday feeling, high frame rate capturing individual flakes"
    ),

    # 16. Explosion Action - 470 chars
    VideoPreset(
        id="explosion_action",
        name="Action Explosion",
        category="Action",
        mood="Intense",
        tags=["explosion", "action", "fire", "dramatic"],
        camera_movement="Slow-motion tracking",
        lighting="Fire light",
        description="Dramatic explosion sequence",
        content="Slow-motion explosion with camera tracking debris, fireball expanding with shockwave distortion, protagonist walking away in silhouette, smoke and flames billowing, sparks and embers flying past camera, blockbuster action movie cinematography, VFX quality pyrotechnics"
    ),

    # 17. Ballet Dance - 445 chars
    VideoPreset(
        id="ballet_dance",
        name="Ballet Performance",
        category="Performance",
        mood="Elegant",
        tags=["ballet", "dance", "grace", "art"],
        camera_movement="Smooth arc",
        lighting="Stage spotlight",
        description="Graceful ballet dancer",
        content="Elegant smooth arc around ballet dancer in mid-pirouette, fabric flowing in slow motion, spotlight creating dramatic shadows on stage, dust particles visible in light beam, perfect athletic form, classical performance cinematography, high speed camera capturing every detail"
    ),

    # 18. Volcano Lava - 485 chars
    VideoPreset(
        id="volcano_lava",
        name="Flowing Lava",
        category="Nature",
        mood="Primal",
        tags=["volcano", "lava", "fire", "power"],
        camera_movement="Tracking alongside",
        lighting="Lava glow",
        description="Molten lava river flow",
        content="Close tracking shot alongside flowing river of molten lava, intense orange and red glow illuminating volcanic landscape, surface crusting and cracking to reveal fire beneath, heat shimmer distorting air above, primordial earth forces on display, National Geographic documentary quality"
    ),

    # 19. Vintage Film - 420 chars
    VideoPreset(
        id="vintage_film",
        name="1920s Silent Film",
        category="Stylized",
        mood="Nostalgic",
        tags=["vintage", "film", "retro", "artistic"],
        camera_movement="Classic crane",
        lighting="Black and white",
        description="Silent film era aesthetic",
        content="Classic Hollywood crane shot in authentic 1920s silent film style, black and white with film grain and scratches, slightly overcranked for period-accurate movement, art deco architecture, dramatic theatrical lighting, vintage iris transitions"
    ),

    # 20. Parkour Action - 460 chars
    VideoPreset(
        id="parkour_action",
        name="Urban Parkour Run",
        category="Action",
        mood="Energetic",
        tags=["parkour", "urban", "athletic", "POV"],
        camera_movement="POV handheld",
        lighting="Daylight",
        description="First-person parkour sequence",
        content="Heart-pounding first-person POV parkour run across urban rooftops, hands reaching for ledges, feet landing on narrow walls, gaps leaping over busy streets below, athletic precision movements, GoPro style dynamic handheld footage, extreme sports cinematography"
    ),

    # 21. Aurora Borealis - 450 chars
    VideoPreset(
        id="aurora_night",
        name="Northern Lights",
        category="Nature",
        mood="Magical",
        tags=["aurora", "night", "sky", "wonder"],
        camera_movement="Time-lapse pan",
        lighting="Natural aurora",
        description="Dancing northern lights",
        content="Time-lapse of aurora borealis dancing across Arctic night sky, green and purple curtains of light rippling like fabric, stars wheeling overhead, snow-covered landscape reflecting colors below, pristine Scandinavian wilderness, astrophotography quality"
    ),

    # 22. Steampunk City - 475 chars
    VideoPreset(
        id="steampunk_city",
        name="Steampunk Metropolis",
        category="Fantasy",
        mood="Industrial",
        tags=["steampunk", "city", "gears", "victorian"],
        camera_movement="Ascending through",
        lighting="Gas lamp amber",
        description="Victorian steampunk cityscape",
        content="Ascending through steampunk metropolis, massive brass gears and clockwork visible on buildings, steam venting from pipes, airships floating past Victorian architecture, gas lamps casting amber glow, detailed mechanical aesthetics, fantasy world-building cinematography"
    ),

    # 23. Meditation Space - 400 chars
    VideoPreset(
        id="meditation_zen",
        name="Zen Garden Meditation",
        category="Atmospheric",
        mood="Peaceful",
        tags=["zen", "meditation", "calm", "mindful"],
        camera_movement="Slow drift",
        lighting="Soft natural",
        description="Tranquil zen atmosphere",
        content="Slow drifting shot over perfect zen garden, raked sand patterns, carefully placed stones, gentle water feature trickling, morning mist, cherry blossoms floating down, profound stillness and tranquility, wellness and meditation visual"
    ),

    # 24. Sports Stadium - 490 chars
    VideoPreset(
        id="sports_stadium",
        name="Stadium Crowd Wave",
        category="Sports",
        mood="Exciting",
        tags=["stadium", "crowd", "sports", "energy"],
        camera_movement="Crane sweep",
        lighting="Stadium floods",
        description="Massive stadium atmosphere",
        content="Epic crane shot sweeping across packed sports stadium during championship moment, crowd rising in wave, colorful fan sections, massive LED screens showing replays, confetti raining down, raw emotional energy of sports spectacle, ESPN broadcast quality cinematography"
    ),

    # 25. Haunted House - 440 chars
    VideoPreset(
        id="haunted_house",
        name="Gothic Haunted Manor",
        category="Horror",
        mood="Eerie",
        tags=["haunted", "gothic", "dark", "spooky"],
        camera_movement="Slow push in",
        lighting="Lightning flashes",
        description="Creepy haunted atmosphere",
        content="Slow ominous push toward abandoned Gothic manor at night, dead trees with twisted branches, lightning flashes revealing broken windows, fog rolling across overgrown grounds, ravens taking flight, classic horror movie atmosphere, tension building cinematography"
    ),

    # 26. Factory Robotics - 465 chars
    VideoPreset(
        id="factory_robots",
        name="Robot Assembly Line",
        category="Industrial",
        mood="Futuristic",
        tags=["robots", "factory", "technology", "precision"],
        camera_movement="Tracking through",
        lighting="Industrial white",
        description="Automated manufacturing",
        content="Smooth tracking shot through advanced robotics factory floor, dozens of robotic arms working in perfect synchronization, sparks from welding, assembly with precision movements, futuristic automated manufacturing, clean industrial aesthetic, corporate documentary quality"
    ),

    # 27. Romantic Sunset - 425 chars
    VideoPreset(
        id="romantic_sunset",
        name="Beach Sunset Romance",
        category="Romantic",
        mood="Warm",
        tags=["sunset", "beach", "romance", "couple"],
        camera_movement="Slow orbit",
        lighting="Golden hour",
        description="Romantic sunset moment",
        content="Slow orbit around silhouetted couple on beach at golden hour, sun setting over calm ocean, warm colors painting sky, waves gently lapping shore, intimate romantic moment, wedding video style cinematography, soft focus dreamy quality"
    ),

    # 28. Cyberpunk Alley - 480 chars
    VideoPreset(
        id="cyberpunk_alley",
        name="Neon Back Alley",
        category="Sci-Fi",
        mood="Gritty",
        tags=["cyberpunk", "alley", "neon", "gritty"],
        camera_movement="Forward dolly",
        lighting="Mixed neon",
        description="Gritty cyberpunk atmosphere",
        content="Slow forward dolly through narrow cyberpunk back alley, neon signs in multiple languages, steam rising from grates, rain puddles reflecting colors, hooded figures in shadows, cluttered market stalls, Blade Runner inspired atmosphere, high detail world-building"
    ),

    # 29. Waterfall - 445 chars
    VideoPreset(
        id="waterfall_jungle",
        name="Jungle Waterfall",
        category="Nature",
        mood="Majestic",
        tags=["waterfall", "jungle", "tropical", "beauty"],
        camera_movement="Ascending reveal",
        lighting="Dappled forest light",
        description="Hidden tropical waterfall",
        content="Ascending reveal shot up hidden jungle waterfall, mist rising from pool below, lush green vegetation surrounding, rainbow in spray, exotic birds flying past, pristine untouched paradise, National Geographic documentary quality, breathtaking natural wonder"
    ),

    # 30. Time Square - 460 chars
    VideoPreset(
        id="times_square",
        name="Times Square Energy",
        category="Urban",
        mood="Electric",
        tags=["city", "times square", "billboards", "energy"],
        camera_movement="360 spin",
        lighting="LED billboards",
        description="NYC Times Square vibrancy",
        content="Dynamic 360-degree spinning shot in heart of Times Square at night, massive LED billboards overwhelming with color and movement, crowds flowing in all directions, yellow taxis, urban sensory overload, New York City energy captured, commercial quality cityscape"
    ),

    # 31. Medieval Battle - 490 chars
    VideoPreset(
        id="medieval_battle",
        name="Epic Battle Charge",
        category="Historical",
        mood="Epic",
        tags=["medieval", "battle", "horses", "war"],
        camera_movement="Tracking cavalry",
        lighting="Overcast dramatic",
        description="Medieval army charge",
        content="Low tracking shot alongside charging medieval cavalry, horses thundering past camera, knights with banners flying, mud and dirt kicked up, enemy army visible in distance, arrows filling the sky, epic scale warfare, Lord of the Rings style battle cinematography"
    ),

    # 32. Abstract Flow - 380 chars
    VideoPreset(
        id="abstract_flow",
        name="Flowing Abstract",
        category="Abstract",
        mood="Hypnotic",
        tags=["abstract", "art", "fluid", "colors"],
        camera_movement="Macro drift",
        lighting="Mixed colors",
        description="Abstract fluid art motion",
        content="Mesmerizing macro footage of flowing abstract fluid art, paint colors mixing and separating, organic patterns forming, oil and water dynamics, hypnotic slow movement, satisfying visual texture, high-end motion graphics aesthetic"
    ),

    # 33. Subway Train - 440 chars
    VideoPreset(
        id="subway_train",
        name="Subway Ride",
        category="Urban",
        mood="Contemplative",
        tags=["subway", "train", "urban", "movement"],
        camera_movement="Interior static",
        lighting="Mixed transit",
        description="Underground train experience",
        content="Static shot inside subway car, passengers in various states, tunnel lights streaking past windows, gentle rocking motion, urban life documentary moment, diverse humanity in transit, authentic metropolitan atmosphere, A24 indie film aesthetic"
    ),

    # 34. Hot Air Balloons - 455 chars
    VideoPreset(
        id="hot_air_balloons",
        name="Cappadocia Balloons",
        category="Aerial",
        mood="Dreamy",
        tags=["balloons", "sunrise", "aerial", "travel"],
        camera_movement="Floating alongside",
        lighting="Sunrise golden",
        description="Hot air balloon sunrise",
        content="Floating alongside dozens of colorful hot air balloons at sunrise, unique rock formations of Cappadocia below, soft morning light, gentle upward motion, fairytale travel destination, Instagram-worthy visual, premium travel documentary cinematography"
    ),

    # 35. Samurai Duel - 475 chars
    VideoPreset(
        id="samurai_duel",
        name="Samurai Showdown",
        category="Action",
        mood="Tense",
        tags=["samurai", "duel", "japan", "tension"],
        camera_movement="Slow push between",
        lighting="Overcast dramatic",
        description="Samurai face-off moment",
        content="Slow push between two samurai facing off in bamboo grove, wind rustling leaves, hands hovering over sword hilts, intense eye contact, cherry blossoms falling between them, extreme tension before clash, Kurosawa inspired framing and composition"
    ),

    # 36. Deep Sea Creature - 450 chars
    VideoPreset(
        id="deep_sea",
        name="Bioluminescent Deep",
        category="Nature",
        mood="Alien",
        tags=["deep sea", "bioluminescence", "alien", "dark"],
        camera_movement="Slow discovery",
        lighting="Bioluminescent",
        description="Deep ocean creatures",
        content="Slow discovery approach to bioluminescent deep sea creatures, pulsing lights in absolute darkness, alien-like jellyfish and anglerfish, ethereal floating movement, extreme deep ocean environment, Blue Planet deep sea sequence quality"
    ),

    # 37. Fashion Runway - 430 chars
    VideoPreset(
        id="fashion_runway",
        name="Fashion Week Runway",
        category="Fashion",
        mood="Glamorous",
        tags=["fashion", "runway", "model", "luxury"],
        camera_movement="Low angle tracking",
        lighting="Dramatic runway",
        description="High fashion runway moment",
        content="Low angle tracking shot of model walking haute couture runway, dramatic lighting from above, flowing fabric in motion, camera flash reflections, confident powerful stride, fashion week atmosphere, Vogue documentary quality"
    ),

    # 38. Drone Race - 465 chars
    VideoPreset(
        id="drone_race",
        name="FPV Drone Race",
        category="Sports",
        mood="Thrilling",
        tags=["drone", "fpv", "racing", "speed"],
        camera_movement="FPV following",
        lighting="Mixed obstacles",
        description="First-person drone racing",
        content="Heart-pounding FPV drone racing footage, weaving through obstacles at high speed, near misses with gates and structures, quick direction changes, motion blur on edges, competitor drones visible ahead, extreme sports energy, professional drone racing coverage"
    ),

    # 39. Glacier Collapse - 480 chars
    VideoPreset(
        id="glacier_collapse",
        name="Calving Glacier",
        category="Nature",
        mood="Powerful",
        tags=["glacier", "ice", "climate", "dramatic"],
        camera_movement="Wide then tightening",
        lighting="Arctic daylight",
        description="Massive glacier calving",
        content="Massive glacier calving event in slow motion, enormous ice chunk separating and crashing into arctic waters, spray shooting skyward, deafening silence before impact, climate documentation, raw power of nature, environmental documentary quality cinematography"
    ),

    # 40. Wine Pour - 360 chars
    VideoPreset(
        id="wine_pour",
        name="Wine Pour Elegance",
        category="Product",
        mood="Sophisticated",
        tags=["wine", "luxury", "product", "elegant"],
        camera_movement="Static macro",
        lighting="Soft studio",
        description="Elegant wine pour",
        content="Slow motion macro shot of red wine pouring into crystal glass, liquid swirling elegantly, light refracting through, legs forming on glass, sophisticated luxury product cinematography, commercial advertising quality"
    ),

    # 41. Carnival Night - 470 chars
    VideoPreset(
        id="carnival_night",
        name="Neon Carnival",
        category="Event",
        mood="Festive",
        tags=["carnival", "fair", "lights", "fun"],
        camera_movement="Tilt up Ferris wheel",
        lighting="Neon carnival",
        description="Colorful carnival atmosphere",
        content="Dramatic tilt up from carnival crowd to towering Ferris wheel against night sky, neon lights spinning and flashing, cotton candy and game stalls, joyful atmosphere, families enjoying rides, nostalgic summer fair feeling, cinematic night photography"
    ),

    # 42. Library Ancient - 410 chars
    VideoPreset(
        id="library_ancient",
        name="Grand Library",
        category="Interior",
        mood="Scholarly",
        tags=["library", "books", "ancient", "wisdom"],
        camera_movement="Ascending through",
        lighting="Warm candlelight",
        description="Majestic ancient library",
        content="Ascending through towering ancient library, endless shelves of leather-bound books, dust motes in candlelight, ornate wooden ladders, scholarly atmosphere, Beauty and the Beast library fantasy, cinematic architectural wonder"
    ),

    # 43. Soccer Goal - 455 chars
    VideoPreset(
        id="soccer_goal",
        name="Championship Goal",
        category="Sports",
        mood="Triumphant",
        tags=["soccer", "goal", "sports", "celebration"],
        camera_movement="Multi-angle replay",
        lighting="Stadium floods",
        description="Winning goal celebration",
        content="Championship-winning goal from multiple angles, ball hitting net in slow motion, keeper diving, striker's emotional celebration, teammates rushing in, crowd exploding, confetti falling, peak sports emotion captured, broadcast quality multi-camera coverage"
    ),

    # 44. Crystal Cave - 445 chars
    VideoPreset(
        id="crystal_cave",
        name="Crystal Cavern",
        category="Fantasy",
        mood="Mystical",
        tags=["crystal", "cave", "magical", "sparkle"],
        camera_movement="Push through",
        lighting="Refracted light",
        description="Magical crystal cavern",
        content="Pushing through massive crystal cavern, giant formations refracting prismatic light, sparkling reflections dancing on walls, ethereal magical atmosphere, fantasy world exploration, geological wonder meets fairy tale, high fantasy production quality"
    ),

    # 45. Protest March - 435 chars
    VideoPreset(
        id="protest_march",
        name="People's March",
        category="Documentary",
        mood="Powerful",
        tags=["protest", "crowd", "movement", "social"],
        camera_movement="Elevated tracking",
        lighting="Natural daylight",
        description="Mass demonstration movement",
        content="Elevated tracking shot over massive peaceful protest march, sea of signs and banners, unified chanting, diverse crowd stretching to horizon, social movement energy, documentary journalism cinematography, powerful collective humanity"
    ),

    # 46. Luxury Car - 420 chars
    VideoPreset(
        id="luxury_car",
        name="Luxury Car Commercial",
        category="Product",
        mood="Premium",
        tags=["car", "luxury", "commercial", "sleek"],
        camera_movement="Slow orbit",
        lighting="Studio dramatic",
        description="Premium car showcase",
        content="Slow cinematic orbit around luxury sports car in dark studio, dramatic lighting highlighting curves, reflections sliding across paint, premium materials visible through windows, automotive commercial quality, high-end brand aesthetic"
    ),

    # 47. Jungle Rain - 460 chars
    VideoPreset(
        id="jungle_rain",
        name="Tropical Rainstorm",
        category="Nature",
        mood="Immersive",
        tags=["jungle", "rain", "tropical", "atmosphere"],
        camera_movement="Static with movement",
        lighting="Overcast green",
        description="Rainforest downpour",
        content="Heavy tropical rain falling through dense jungle canopy, leaves bouncing with impact, steam rising from forest floor, exotic birds taking shelter, immersive ASMR quality sound design potential, nature documentary atmosphere, rich green color palette"
    ),

    # 48. Comic Book Style - 395 chars
    VideoPreset(
        id="comic_style",
        name="Comic Book Action",
        category="Stylized",
        mood="Dynamic",
        tags=["comic", "stylized", "action", "pop"],
        camera_movement="Dutch angles",
        lighting="High contrast",
        description="Comic book visual style",
        content="Dynamic action sequence in comic book visual style, bold outlines, halftone dots, POW/BAM text graphics, Dutch angle camera work, high contrast colors, Sin City and Spider-Verse inspired aesthetic, motion graphic quality"
    ),

    # 49. Tea Ceremony - 385 chars
    VideoPreset(
        id="tea_ceremony",
        name="Japanese Tea Ceremony",
        category="Cultural",
        mood="Serene",
        tags=["tea", "japanese", "ritual", "peaceful"],
        camera_movement="Minimal subtle",
        lighting="Soft natural",
        description="Traditional tea ritual",
        content="Intimate view of Japanese tea ceremony, graceful hand movements, matcha being whisked, steam rising from bowl, tatami mat setting, wabi-sabi aesthetic, meditative ritual precision, cultural documentary quality"
    ),

    # 50. Comet Approach - 475 chars
    VideoPreset(
        id="comet_space",
        name="Comet Tail",
        category="Sci-Fi",
        mood="Cosmic",
        tags=["comet", "space", "tail", "cosmic"],
        camera_movement="Flying alongside",
        lighting="Starfield",
        description="Space comet journey",
        content="Flying alongside magnificent comet through deep space, brilliant ice tail streaming for millions of miles, rocky nucleus tumbling slowly, stars wheeling past in background, scientific accuracy meets cinematic beauty, interstellar exploration wonder"
    ),
]


def get_video_by_category(category: str) -> List[VideoPreset]:
    """Get all video presets matching a category."""
    category_lower = category.lower()
    return [p for p in VIDEO_PRESETS if p.category.lower() == category_lower]


def get_video_by_mood(mood: str) -> List[VideoPreset]:
    """Get all video presets matching a mood."""
    mood_lower = mood.lower()
    return [p for p in VIDEO_PRESETS if p.mood.lower() == mood_lower]


def get_video_for_model(model_id: str) -> List[VideoPreset]:
    """Get video presets that fit within a model's character limit."""
    if "wan" in model_id.lower():
        return [p for p in VIDEO_PRESETS if p.fits_wan]
    # Most models support longer prompts
    return VIDEO_PRESETS


def get_all_categories() -> List[str]:
    """Get unique list of all categories."""
    return sorted(set(p.category for p in VIDEO_PRESETS))


def get_all_moods() -> List[str]:
    """Get unique list of all moods."""
    return sorted(set(p.mood for p in VIDEO_PRESETS))
