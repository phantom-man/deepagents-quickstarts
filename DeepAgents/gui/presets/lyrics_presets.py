"""
Lyrics Presets - Curated song lyrics with structure markers.

Each preset includes:
- Proper [Verse], [Chorus], [Bridge] markers
- Character count for model filtering
- Genre tags for categorization
- Compatible model flags

Music-1.5 limit: 600 chars
ACE-Step limit: 3000 chars
"""

from dataclasses import dataclass, field
from typing import List


@dataclass
class LyricsPreset:
    """A curated lyrics preset."""

    id: str
    name: str
    content: str
    genre: str
    mood: str
    tags: List[str] = field(default_factory=list)
    description: str = ""

    @property
    def char_count(self) -> int:
        """Return the character count of the lyrics content."""
        return len(self.content)

    @property
    def fits_music15(self) -> bool:
        """Fits within Minimax Music-1.5 600 char limit."""
        return self.char_count <= 600

    @property
    def fits_ace_step(self) -> bool:
        """Fits within ACE-Step 3000 char limit."""
        return self.char_count <= 3000


# =============================================================================
# LYRICS PRESETS (20)
# =============================================================================

LYRICS_PRESETS: List[LyricsPreset] = [
    # 1. Rock/Anthem - 580 chars
    LyricsPreset(
        id="rock_rise_up",
        name="Rise Up (Rock Anthem)",
        genre="Rock",
        mood="Empowering",
        tags=["anthem", "motivational", "power"],
        description="Classic rock anthem about overcoming obstacles",
        content="""[Verse 1]
Standing at the edge of tomorrow
Every scar tells a story of survival
Through the fire, through the pain and sorrow
We found the strength for our revival

[Chorus]
Rise up, rise up from the ashes
Break the chains that held us down
Rise up, rise up, nothing stops us
We wear our scars like a crown

[Verse 2]
Every fall just made us stronger
Every storm revealed our light
We won't wait around much longer
Tonight we take back the night

[Chorus]
Rise up, rise up from the ashes
Break the chains that held us down
Rise up, rise up, nothing stops us
We wear our scars like a crown""",
    ),
    # 2. Pop/Love - 520 chars
    LyricsPreset(
        id="pop_electric_hearts",
        name="Electric Hearts (Pop Love)",
        genre="Pop",
        mood="Romantic",
        tags=["love", "upbeat", "dance"],
        description="Upbeat pop love song",
        content="""[Verse 1]
Caught your eyes across the room
Electricity cutting through the gloom
Your smile lit up my universe
Now I'm caught up in this beautiful curse

[Chorus]
Electric hearts beating as one
Dancing under neon sun
You and me, we've just begun
Electric hearts, never come undone

[Verse 2]
Every touch sends sparks through my soul
With you I finally feel whole
No more searching, found my home
With you I'll never be alone

[Chorus]
Electric hearts beating as one
Dancing under neon sun
You and me, we've just begun
Electric hearts, never come undone""",
    ),
    # 3. Country - 550 chars
    LyricsPreset(
        id="country_backroads",
        name="Backroads and Bonfires",
        genre="Country",
        mood="Nostalgic",
        tags=["summer", "friends", "memories"],
        description="Country song about summer memories",
        content="""[Verse 1]
Dusty roads and firefly nights
Tailgate down under starry lights
Cold drinks and old guitar songs
Those summer days felt so long

[Chorus]
Backroads and bonfires
Old friends and heart's desires
Nothing but time on our hands
Living life with no plans
Just backroads and bonfires

[Verse 2]
Radio playing our favorite tune
Swimming holes under the moon
We were young and wild and free
That's how it was meant to be

[Chorus]
Backroads and bonfires
Old friends and heart's desires
Nothing but time on our hands
Living life with no plans
Just backroads and bonfires""",
    ),
    # 4. Hip-Hop - 590 chars
    LyricsPreset(
        id="hiphop_grind",
        name="The Grind (Hip-Hop)",
        genre="Hip-Hop",
        mood="Determined",
        tags=["hustle", "motivation", "success"],
        description="Motivational hip-hop about hard work",
        content="""[Verse 1]
Started from the bottom, now we climbing
Perfect timing, always grinding
They said we'd never make it this far
But look at us now, we shooting stars
Every setback was a setup
For the comeback, never let up

[Chorus]
This is the grind, we don't stop
Started from nothing, now we at the top
Put in the work, paid the cost
Everything we got, we never lost

[Verse 2]
Late nights and early mornings
Ignored all the warnings
They doubted, we proved them wrong
This is our victory song
Building empires brick by brick
Success don't come quick

[Chorus]
This is the grind, we don't stop
Started from nothing, now we at the top""",
    ),
    # 5. EDM/Dance - 480 chars
    LyricsPreset(
        id="edm_tonight",
        name="Feel Tonight (EDM)",
        genre="EDM",
        mood="Euphoric",
        tags=["dance", "party", "energy"],
        description="High-energy EDM anthem",
        content="""[Verse 1]
Lights are flashing, bass is pumping
Hearts are racing, bodies jumping
Leave your worries at the door
Tonight we're living like never before

[Chorus]
Can you feel it tonight
We're burning so bright
Hands up to the sky
We're ready to fly
Feel it tonight

[Verse 2]
Music takes us higher
We're dancing through the fire
Nothing's gonna bring us down
Best night in this whole town

[Chorus]
Can you feel it tonight
We're burning so bright
Hands up to the sky
We're ready to fly
Feel it tonight""",
    ),
    # 6. R&B/Soul - 570 chars
    LyricsPreset(
        id="rnb_stay",
        name="Stay With Me (R&B)",
        genre="R&B",
        mood="Romantic",
        tags=["love", "soulful", "slow"],
        description="Smooth R&B love ballad",
        content="""[Verse 1]
Candlelight dancing on the walls
Your whisper echoes through the halls
Time stands still when you're near
Everything becomes so clear

[Chorus]
Stay with me through the night
Hold me close, hold me tight
In your arms I found my peace
A love that will never cease
Stay with me

[Verse 2]
Your touch is like a gentle rain
Washing away all the pain
In your eyes I see forever
A bond that nothing could sever

[Bridge]
We don't need words to say
What our hearts feel today
Just stay

[Chorus]
Stay with me through the night
Hold me close, hold me tight
In your arms I found my peace
A love that will never cease""",
    ),
    # 7. Indie/Alternative - 540 chars
    LyricsPreset(
        id="indie_wanderer",
        name="The Wanderer (Indie)",
        genre="Indie",
        mood="Reflective",
        tags=["introspective", "journey", "searching"],
        description="Introspective indie song about finding oneself",
        content="""[Verse 1]
Walking down these empty streets
Searching for the missing piece
City lights blur into one
Another day nearly done

[Chorus]
I'm just a wanderer
Looking for where I belong
A searcher in the dark
Following an unknown song
Just a wanderer

[Verse 2]
Faces pass like fleeting dreams
Nothing is quite what it seems
But somewhere out there waits a home
A place to call my own

[Chorus]
I'm just a wanderer
Looking for where I belong
A searcher in the dark
Following an unknown song

[Outro]
Keep walking, keep searching
The answer's just around the bend""",
    ),
    # 8. Metal/Hard Rock - 585 chars
    LyricsPreset(
        id="metal_unbreakable",
        name="Unbreakable (Metal)",
        genre="Metal",
        mood="Aggressive",
        tags=["power", "defiant", "intense"],
        description="Heavy metal anthem of defiance",
        content="""[Verse 1]
They tried to break us, tear us down
Tried to bury us underground
But we rose from the depths below
Stronger than they'll ever know

[Chorus]
Unbreakable, we stand our ground
Unshakeable, we won't back down
Through the fire we will rise
Unstoppable, we never die
Unbreakable

[Verse 2]
Scars of battle mark our skin
Every war we fought to win
Forged in flames of sacrifice
We've paid the ultimate price

[Chorus]
Unbreakable, we stand our ground
Unshakeable, we won't back down
Through the fire we will rise
Unstoppable, we never die
Unbreakable

[Bridge]
Nothing breaks these chains
Victory runs through our veins""",
    ),
    # 9. Folk/Acoustic - 530 chars
    LyricsPreset(
        id="folk_seasons",
        name="Seasons Change (Folk)",
        genre="Folk",
        mood="Peaceful",
        tags=["nature", "life", "acoustic"],
        description="Gentle folk song about life's cycles",
        content="""[Verse 1]
Leaves are falling from the trees
Dancing gently in the breeze
Summer fades to autumn gold
Stories waiting to be told

[Chorus]
Seasons change and so do we
Growing into who we'll be
Nothing stays the same for long
Life keeps moving, moving on

[Verse 2]
Winter snow will melt away
Making room for brighter days
Spring will bring new life again
Flowers blooming in the rain

[Chorus]
Seasons change and so do we
Growing into who we'll be
Nothing stays the same for long
Life keeps moving, moving on

[Outro]
Round and round the world turns
Every ending, something learns""",
    ),
    # 10. Blues - 560 chars
    LyricsPreset(
        id="blues_midnight",
        name="Midnight Blues",
        genre="Blues",
        mood="Melancholy",
        tags=["sad", "soulful", "late night"],
        description="Classic blues about heartache",
        content="""[Verse 1]
It's three AM and I can't sleep
These memories cut so deep
Empty bottle by my side
Nowhere left for me to hide

[Chorus]
Got the midnight blues again
Drowning in the might-have-beens
Heart's been broken, soul's been torn
Feeling tired, feeling worn
These midnight blues

[Verse 2]
Your picture fading on the wall
I still remember when we had it all
Now all that's left is this old song
Wondering where it all went wrong

[Chorus]
Got the midnight blues again
Drowning in the might-have-beens
Heart's been broken, soul's been torn
Feeling tired, feeling worn
These midnight blues""",
    ),
    # 11. Reggae - 510 chars
    LyricsPreset(
        id="reggae_sunshine",
        name="Island Sunshine (Reggae)",
        genre="Reggae",
        mood="Happy",
        tags=["chill", "positive", "summer"],
        description="Feel-good reggae vibes",
        content="""[Verse 1]
Wake up to the morning sun
Brand new day has just begun
Feel the rhythm in my soul
Music making me feel whole

[Chorus]
Island sunshine on my face
Everything falls into place
No worries, no stress today
Reggae music leads the way
Island sunshine

[Verse 2]
Palm trees swaying in the breeze
Living life with so much ease
Good vibrations all around
Peace and love is what we found

[Chorus]
Island sunshine on my face
Everything falls into place
No worries, no stress today
Reggae music leads the way""",
    ),
    # 12. Punk - 490 chars
    LyricsPreset(
        id="punk_rebel",
        name="Rebel Heart (Punk)",
        genre="Punk",
        mood="Rebellious",
        tags=["angry", "fast", "youth"],
        description="Fast punk rock rebellion",
        content="""[Verse 1]
Don't tell me what to think
Don't tell me what to say
I'm sick of playing by your rules
I'm doing it my way

[Chorus]
Rebel heart won't be contained
Breaking free from every chain
Scream it loud, let them hear
Rebel hearts feel no fear

[Verse 2]
The system tries to hold us down
But we won't fade into the crowd
Stand up tall and raise your voice
Revolution is our choice

[Chorus]
Rebel heart won't be contained
Breaking free from every chain
Scream it loud, let them hear
Rebel hearts feel no fear""",
    ),
    # 13. Jazz/Swing - 545 chars
    LyricsPreset(
        id="jazz_night",
        name="One More Night (Jazz)",
        genre="Jazz",
        mood="Romantic",
        tags=["smooth", "classic", "nightclub"],
        description="Smooth jazz standard",
        content="""[Verse 1]
Smoke fills the room so low
Piano plays soft and slow
Your eyes meet mine across the floor
I've never felt this way before

[Chorus]
Give me one more night with you
Swaying to a song so true
Let the music hold us tight
Just give me one more night

[Verse 2]
The trumpet cries a lonely note
Words I've left there in my throat
But in this moment, nothing else
Just you and I and no one else

[Chorus]
Give me one more night with you
Swaying to a song so true
Let the music hold us tight
Just give me one more night

[Outro]
One more night, that's all I need
One more night with you""",
    ),
    # 14. Electronic/Synthwave - 500 chars
    LyricsPreset(
        id="synth_neon",
        name="Neon Dreams (Synthwave)",
        genre="Electronic",
        mood="Dreamy",
        tags=["retro", "80s", "atmospheric"],
        description="Retro synthwave aesthetic",
        content="""[Verse 1]
Neon lights paint the sky
Electric dreams passing by
Chrome and steel, endless night
Chasing that synthetic light

[Chorus]
Neon dreams in the dark
Digital fire, electric spark
Running through the city glow
Everywhere we want to go
Neon dreams

[Verse 2]
Pixel hearts beat in time
Future past, yours and mine
Synthesizers fill the air
We could be anywhere

[Chorus]
Neon dreams in the dark
Digital fire, electric spark
Running through the city glow
Everywhere we want to go""",
    ),
    # 15. Gospel/Inspirational - 580 chars
    LyricsPreset(
        id="gospel_grace",
        name="Amazing Grace (Modern)",
        genre="Gospel",
        mood="Uplifting",
        tags=["spiritual", "hope", "faith"],
        description="Modern inspirational gospel",
        content="""[Verse 1]
When I was lost and couldn't see
A light came down and rescued me
Through darkest nights and troubled days
Guided by amazing grace

[Chorus]
Lift me up when I am weak
Give me words when I can't speak
Carry me through the storm
In Your love I am reborn
Amazing grace

[Verse 2]
Every step You walk with me
Opening eyes so I can see
The beauty in each dawn that breaks
With every breath my spirit wakes

[Chorus]
Lift me up when I am weak
Give me words when I can't speak
Carry me through the storm
In Your love I am reborn
Amazing grace

[Outro]
Grace that saved a soul like me
Grace that set my spirit free""",
    ),
    # 16. Latin/Salsa - 520 chars
    LyricsPreset(
        id="latin_fuego",
        name="Fuego (Latin Pop)",
        genre="Latin",
        mood="Passionate",
        tags=["dance", "hot", "rhythm"],
        description="Hot Latin dance track",
        content="""[Verse 1]
Feel the heat rising tonight
Bodies moving, holding tight
Rhythm takes control of me
Dancing wild and feeling free

[Chorus]
Fuego, fuego in my heart
You set my world apart
Fuego burning in my soul
You make me lose control
Fuego

[Verse 2]
Your eyes speak a thousand words
Sweetest melody I've heard
Move with me until the dawn
Keep the fire burning on

[Chorus]
Fuego, fuego in my heart
You set my world apart
Fuego burning in my soul
You make me lose control
Fuego

[Outro]
Light the fire, feel the flame
Nothing ever stays the same""",
    ),
    # 17. Acoustic Ballad - 590 chars
    LyricsPreset(
        id="ballad_remember",
        name="Remember When (Ballad)",
        genre="Ballad",
        mood="Nostalgic",
        tags=["emotional", "memories", "slow"],
        description="Emotional acoustic ballad",
        content="""[Verse 1]
Old photographs spread on the floor
Memories of days before
Your handwriting on faded pages
Love letters from different ages

[Chorus]
Remember when we had forever
Remember when we'd last together
Time moves on but my heart stays
Frozen in those golden days
Remember when

[Verse 2]
The coffee shop where first we met
A moment I will not forget
Your laugh still echoes in my mind
A treasure I will always find

[Chorus]
Remember when we had forever
Remember when we'd last together
Time moves on but my heart stays
Frozen in those golden days

[Bridge]
Though years have passed us by
Some loves will never die
Remember when""",
    ),
    # 18. Disco/Funk - 510 chars
    LyricsPreset(
        id="disco_groove",
        name="Get Your Groove (Disco)",
        genre="Disco",
        mood="Fun",
        tags=["party", "dance", "retro"],
        description="Classic disco fun",
        content="""[Verse 1]
Disco ball is spinning round
Funky bass is shaking ground
Put your dancing shoes on tight
We're gonna party all night

[Chorus]
Get your groove on, move your feet
Feel the rhythm, feel the beat
Nothing's gonna bring us down
Funkiest night in this town
Get your groove

[Verse 2]
Sequins shining, lights so bright
Everybody feels alright
Let the music set you free
This is where you want to be

[Chorus]
Get your groove on, move your feet
Feel the rhythm, feel the beat
Nothing's gonna bring us down
Funkiest night in this town""",
    ),
    # 19. Singer-Songwriter - 570 chars
    LyricsPreset(
        id="acoustic_honest",
        name="Honest Words (Acoustic)",
        genre="Singer-Songwriter",
        mood="Vulnerable",
        tags=["personal", "raw", "acoustic"],
        description="Raw, personal acoustic piece",
        content="""[Verse 1]
I've been writing honest words
Hoping somehow to be heard
Every scar becomes a song
Trying to figure where I belong

[Chorus]
These are my honest words
Imperfect as they may be
These are my honest words
The only truth I can see
Honest words

[Verse 2]
No more hiding what I feel
Time to show the wounds that heal
In the silence I found my voice
Singing was my only choice

[Chorus]
These are my honest words
Imperfect as they may be
These are my honest words
The only truth I can see

[Bridge]
Strip away the pretense
What remains makes sense
Just honest words, nothing less""",
    ),
    # 20. Epic/Cinematic - 595 chars
    LyricsPreset(
        id="epic_heroes",
        name="Heroes Rise (Epic)",
        genre="Epic",
        mood="Triumphant",
        tags=["cinematic", "powerful", "orchestral"],
        description="Epic cinematic anthem",
        content="""[Verse 1]
Through the darkness we have walked
When the world said all was lost
We held onto hope so tight
Waiting for the morning light

[Chorus]
Heroes rise when hope seems gone
Finding strength to carry on
Against the odds we take our stand
Victory within our hands
Heroes rise

[Verse 2]
Armies fall and empires fade
But the legends that we made
Echo through eternity
The brave will always be free

[Chorus]
Heroes rise when hope seems gone
Finding strength to carry on
Against the odds we take our stand
Victory within our hands
Heroes rise

[Bridge]
From the ashes we are born
Every battle we have worn
Like armor on our souls
Makes us forever whole""",
    ),
    # =========================================================================
    # ADDITIONAL LYRICS PRESETS (21-100)
    # =========================================================================
    # 21. Alternative Rock - 575 chars
    LyricsPreset(
        id="alt_broken_mirror",
        name="Broken Mirror (Alternative)",
        genre="Alternative",
        mood="Introspective",
        tags=["reflection", "identity", "dark"],
        description="Alternative rock about self-discovery",
        content="""[Verse 1]
Staring at a broken mirror
Trying to find the pieces of who I was
The reflection getting clearer
But I don't recognize because

[Chorus]
I'm not who I used to be
Shattered glass won't set me free
Looking for the missing parts
Scattered pieces of my heart

[Verse 2]
Every crack tells a story
Of the times I fell apart
Searching for former glory
In the chambers of my heart

[Chorus]
I'm not who I used to be
Shattered glass won't set me free
Looking for the missing parts
Scattered pieces of my heart""",
    ),
    # 22. Acoustic Folk - 540 chars
    LyricsPreset(
        id="folk_river_song",
        name="River Song (Folk)",
        genre="Folk",
        mood="Serene",
        tags=["nature", "peaceful", "journey"],
        description="Peaceful folk song about nature",
        content="""[Verse 1]
Down by the river where willows weep
The water whispers secrets deep
I lay my troubles on the shore
And watch them drift forevermore

[Chorus]
Sing me a river song tonight
Where the water meets the light
Carry my worries out to sea
Let the current set me free

[Verse 2]
The moon reflects upon the stream
Like silver threads in a dream
I find my peace in nature's arms
Safe from the world and all its harms

[Chorus]
Sing me a river song tonight
Where the water meets the light""",
    ),
    # 23. Soul/R&B - 565 chars
    LyricsPreset(
        id="soul_one_more_chance",
        name="One More Chance (Soul)",
        genre="Soul",
        mood="Pleading",
        tags=["love", "redemption", "emotional"],
        description="Soulful plea for second chances",
        content="""[Verse 1]
I know I let you down before
Said things I can't take back no more
But standing here with empty hands
I'm hoping that you'll understand

[Chorus]
Give me one more chance to prove
That my heart beats just for you
I'll spend forever making right
All the wrongs of every night
One more chance

[Verse 2]
The tears I've cried could fill the sea
For all the pain I caused you and me
But love like ours don't come around
Without a fight to hold our ground

[Chorus]
Give me one more chance to prove
That my heart beats just for you""",
    ),
    # 24. Pop Rock - 550 chars
    LyricsPreset(
        id="pop_rock_unstoppable",
        name="Unstoppable (Pop Rock)",
        genre="Pop Rock",
        mood="Confident",
        tags=["empowerment", "energy", "anthemic"],
        description="High-energy confidence anthem",
        content="""[Verse 1]
They said I couldn't make it here
Tried to fill my head with fear
But I've got fire in my soul
And nothing's gonna take control

[Chorus]
I'm unstoppable tonight
Burning brighter than the light
Nothing's gonna hold me back
I'm on the attack
Unstoppable

[Verse 2]
Every wall they tried to build
Just made my determination filled
I turned their doubts into my fuel
Breaking every single rule

[Chorus]
I'm unstoppable tonight
Burning brighter than the light
Nothing's gonna hold me back
I'm on the attack""",
    ),
    # 25. Country Pop - 560 chars
    LyricsPreset(
        id="country_small_town",
        name="Small Town Dreams",
        genre="Country",
        mood="Hopeful",
        tags=["hometown", "dreams", "nostalgia"],
        description="Country song about chasing dreams",
        content="""[Verse 1]
Grew up on a dirt road outside of town
Where Friday nights were all we had around
But I had bigger dreams inside my head
Than anything those cornfields ever said

[Chorus]
Small town dreams and big city lights
I'm chasing stars on endless nights
Don't know where this road will lead
But I've got faith and that's all I need
Small town dreams

[Verse 2]
Mama said to follow what feels right
Daddy said to never lose the fight
So I packed my bags and hit the road
With nothing but a heart of gold

[Chorus]
Small town dreams and big city lights""",
    ),
    # 26. Indie Pop - 530 chars
    LyricsPreset(
        id="indie_paper_planes",
        name="Paper Planes (Indie Pop)",
        genre="Indie Pop",
        mood="Whimsical",
        tags=["dreams", "childhood", "light"],
        description="Whimsical indie pop about innocence",
        content="""[Verse 1]
We used to throw our wishes to the sky
On paper planes that learned to fly
Each one a hope, each one a dream
Things aren't always what they seem

[Chorus]
Paper planes and childhood games
Nothing ever stays the same
But somewhere up above the clouds
Our dreams are flying proud

[Verse 2]
Remember when the world was small
And we could have it all
The magic hasn't gone away
It lives in us today

[Chorus]
Paper planes and childhood games
Nothing ever stays the same
But somewhere up above the clouds
Our dreams are flying proud""",
    ),
    # 27. Hard Rock - 580 chars
    LyricsPreset(
        id="hard_rock_thunder",
        name="Thunder Road (Hard Rock)",
        genre="Hard Rock",
        mood="Fierce",
        tags=["power", "rebellion", "freedom"],
        description="Hard-driving rock about freedom",
        content="""[Verse 1]
Engine roaring down the line
Leaving everything behind
Chrome and steel beneath my hands
Racing through the promised lands

[Chorus]
Thunder road, take me home
Where the wild ones always roam
Burn the night with gasoline
Living fast, living mean
Thunder road

[Verse 2]
They can't catch what they can't see
Born to ride, born to be free
Every mile a victory
This is where I'm meant to be

[Bridge]
No chains can hold me down
No walls around this town

[Chorus]
Thunder road, take me home
Where the wild ones always roam
Burn the night with gasoline
Living fast, living mean""",
    ),
    # 28. Dance Pop - 490 chars
    LyricsPreset(
        id="dance_all_night",
        name="Dance All Night (Dance Pop)",
        genre="Dance",
        mood="Euphoric",
        tags=["party", "club", "energy"],
        description="Club anthem for dancing",
        content="""[Verse 1]
The beat drops and we come alive
Hands up high, we're feeling the vibe
Forget tomorrow, forget the past
This moment's made to last

[Chorus]
Dance all night until the sun
We're just getting started, having fun
Let the music take control
Feel it deep inside your soul
Dance all night

[Verse 2]
Strobe lights flash like shooting stars
We're living life without the scars
Move your body, lose your mind
Leave your worries far behind

[Chorus]
Dance all night until the sun""",
    ),
    # 29. Acoustic Ballad - 570 chars
    LyricsPreset(
        id="acoustic_goodbye",
        name="Goodbye For Now (Acoustic)",
        genre="Acoustic",
        mood="Bittersweet",
        tags=["farewell", "love", "hope"],
        description="Tender farewell song",
        content="""[Verse 1]
The morning light is breaking through
As I write these words to you
This isn't where the story ends
Just where our paths diverge, my friend

[Chorus]
Goodbye for now, but not forever
Our hearts are tied by more than weather
Though miles may come between us two
I'll always find my way to you
Goodbye for now

[Verse 2]
Take the memories we've made
Let them guide you, unafraid
Every moment that we shared
Showed me how much someone cared

[Chorus]
Goodbye for now, but not forever
Our hearts are tied by more than weather
Though miles may come between us two
I'll always find my way to you""",
    ),
    # 30. Emo/Post-Punk - 575 chars
    LyricsPreset(
        id="emo_black_roses",
        name="Black Roses (Emo)",
        genre="Emo",
        mood="Melancholic",
        tags=["heartbreak", "dark", "emotional"],
        description="Emotional song about heartbreak",
        content="""[Verse 1]
You left black roses on my door
A symbol of what we had before
The petals falling one by one
Like all the damage you have done

[Chorus]
Black roses in the rain
Reminders of the pain
You painted love in shades of gray
Then slowly walked away
Black roses

[Verse 2]
The thorns still dig into my skin
A memory of where we've been
I kept them pressed inside a book
Every time I take a look

[Bridge]
They say time heals everything
But these wounds still burn and sting

[Chorus]
Black roses in the rain
Reminders of the pain
You painted love in shades of gray""",
    ),
    # 31. Tropical House - 500 chars
    LyricsPreset(
        id="tropical_paradise",
        name="Paradise Found (Tropical)",
        genre="Tropical House",
        mood="Blissful",
        tags=["summer", "beach", "chill"],
        description="Tropical vibes and beach life",
        content="""[Verse 1]
Sand between my toes tonight
Palm trees swaying left and right
The ocean calling out my name
Nothing here is ever the same

[Chorus]
Found my paradise at last
Leaving all my worries past
Sun is setting, gold and red
Dancing thoughts inside my head
Paradise found

[Verse 2]
Cocktail colors paint the sky
As seabirds gently fly by
This is where I'm meant to stay
In paradise each and every day

[Chorus]
Found my paradise at last
Leaving all my worries past""",
    ),
    # 32. Progressive Rock - 590 chars
    LyricsPreset(
        id="prog_time_machine",
        name="Time Machine (Prog Rock)",
        genre="Progressive Rock",
        mood="Epic",
        tags=["sci-fi", "journey", "complex"],
        description="Epic prog rock concept piece",
        content="""[Verse 1]
Spinning through the cosmic void
Futures built and then destroyed
Every choice a different path
Feel the universe's wrath

[Chorus]
In my time machine I ride
Through dimensions far and wide
Past and future intertwine
Everything is by design
Time machine

[Verse 2]
Paradoxes twist and turn
Lessons that we'll never learn
History repeats its song
Have we been here all along

[Bridge]
The clock strikes midnight once again
Beginning where we should have end

[Chorus]
In my time machine I ride
Through dimensions far and wide
Past and future intertwine
Everything is by design""",
    ),
    # 33. Nu Metal - 565 chars
    LyricsPreset(
        id="nu_metal_break",
        name="Break The Silence (Nu Metal)",
        genre="Nu Metal",
        mood="Angry",
        tags=["rage", "catharsis", "heavy"],
        description="Heavy cathartic release",
        content="""[Verse 1]
Pressure building up inside
All the feelings that I hide
Can't contain it anymore
Gotta settle every score

[Chorus]
Break the silence, hear me scream
Nothing's ever what it seems
Tear it down and start again
Break the silence in the end

[Verse 2]
They won't listen, they don't care
Voices lost into the air
But tonight I make my stand
Take control with my own hands

[Bridge]
Louder, louder, can you hear
Every doubt and every fear

[Chorus]
Break the silence, hear me scream
Nothing's ever what it seems
Tear it down and start again""",
    ),
    # 34. Soft Rock - 545 chars
    LyricsPreset(
        id="soft_rock_seasons",
        name="Seasons of Love (Soft Rock)",
        genre="Soft Rock",
        mood="Tender",
        tags=["romance", "gentle", "timeless"],
        description="Gentle love song through seasons",
        content="""[Verse 1]
In the spring we fell in love
Under stars that shone above
Summer brought us closer still
Every moment such a thrill

[Chorus]
Through all the seasons of our love
You're everything I'm dreaming of
Winter, spring, or summer rain
I'd fall for you again and again
Seasons of love

[Verse 2]
Autumn leaves began to fall
As we built our love so tall
Winter came with snow so white
Holding close through every night

[Chorus]
Through all the seasons of our love
You're everything I'm dreaming of""",
    ),
    # 35. Funk - 520 chars
    LyricsPreset(
        id="funk_groove_thing",
        name="Groove Thing (Funk)",
        genre="Funk",
        mood="Groovy",
        tags=["dance", "funky", "bass"],
        description="Funky groove for the dancefloor",
        content="""[Verse 1]
Bass is thumping, feel that beat
Get up on your funky feet
Hips are swaying side to side
Come on baby, take this ride

[Chorus]
You got that groove thing going on
Keep on dancing till the dawn
Shake it left, shake it right
Gonna funk it up tonight
Groove thing

[Verse 2]
Horns are blasting, drums are tight
Everything is feeling right
Don't you stop, keep it going
Let that funky feeling keep on flowing

[Chorus]
You got that groove thing going on
Keep on dancing till the dawn""",
    ),
    # 36. Power Pop - 510 chars
    LyricsPreset(
        id="power_pop_summer",
        name="Summer Crush (Power Pop)",
        genre="Power Pop",
        mood="Excited",
        tags=["crush", "summer", "catchy"],
        description="Catchy summer love song",
        content="""[Verse 1]
Saw you walking by the beach
Something special within reach
Heart was racing, palms were sweating
A moment I won't be forgetting

[Chorus]
Summer crush under the sun
Feels like love has just begun
Every day with you is gold
A story waiting to be told
Summer crush

[Verse 2]
Ice cream dates and boardwalk nights
Ferris wheels and city lights
This summer's gonna be the best
Better than all the rest

[Chorus]
Summer crush under the sun
Feels like love has just begun""",
    ),
    # 37. Grunge - 570 chars
    LyricsPreset(
        id="grunge_torn_jeans",
        name="Torn Jeans (Grunge)",
        genre="Grunge",
        mood="Disenchanted",
        tags=["90s", "angst", "raw"],
        description="Raw 90s grunge energy",
        content="""[Verse 1]
Sitting on my bedroom floor
Don't know what I'm living for
Radio plays the same old songs
Everything feels so wrong

[Chorus]
Torn jeans and faded dreams
Life is harder than it seems
Lost somewhere in between
The person that I could have been
Torn jeans

[Verse 2]
Parents yelling down the hall
Posters peeling off the wall
Just a kid trying to survive
Barely feeling alive

[Bridge]
Maybe someday things will change
Until then I'll stay estranged

[Chorus]
Torn jeans and faded dreams
Life is harder than it seems
Lost somewhere in between""",
    ),
    # 38. Ska Punk - 530 chars
    LyricsPreset(
        id="ska_friday_night",
        name="Friday Night (Ska Punk)",
        genre="Ska",
        mood="Energetic",
        tags=["party", "horns", "upbeat"],
        description="Upbeat ska punk party anthem",
        content="""[Verse 1]
Clock strikes five, I'm out the door
Can't take this working anymore
Gonna meet my friends downtown
Best crew that's ever been around

[Chorus]
It's Friday night and we're alive
Dancing like we're twenty-five
Horns are blasting, drums are loud
We're the craziest ones in the crowd
Friday night

[Verse 2]
Problems wait until Monday
Tonight we're doing things our way
Jump around and start to skank
Got the weekend in the bank

[Chorus]
It's Friday night and we're alive
Dancing like we're twenty-five""",
    ),
    # 39. Electro Pop - 485 chars
    LyricsPreset(
        id="electro_digital_love",
        name="Digital Love (Electro Pop)",
        genre="Electro Pop",
        mood="Futuristic",
        tags=["synth", "modern", "love"],
        description="Modern electronic love song",
        content="""[Verse 1]
Pixels form your perfect face
In this digital embrace
Ones and zeros spell your name
Nothing here is ever the same

[Chorus]
Digital love across the wire
Binary code and pure desire
Connected through the endless night
Our love is programmed just right
Digital love

[Verse 2]
Screens glow soft in the dark
You've become my missing spark
Virtual but feeling real
Nothing's changed the way I feel

[Chorus]
Digital love across the wire
Binary code and pure desire""",
    ),
    # 40. Psychedelic - 555 chars
    LyricsPreset(
        id="psych_kaleidoscope",
        name="Kaleidoscope Eyes (Psych)",
        genre="Psychedelic",
        mood="Trippy",
        tags=["colorful", "surreal", "dreamy"],
        description="Trippy psychedelic journey",
        content="""[Verse 1]
Colors swirling all around
Floating high above the ground
Everything begins to melt
Feelings I have never felt

[Chorus]
Kaleidoscope eyes see the truth
Visions of eternal youth
Spinning through the cosmic night
Bathed in multicolored light
Kaleidoscope eyes

[Verse 2]
Time becomes a twisted stream
Is this real or just a dream
Boundaries begin to fade
In this world that we have made

[Bridge]
Let go of all you know
And watch the colors flow

[Chorus]
Kaleidoscope eyes see the truth
Visions of eternal youth""",
    ),
    # 41. Christian Rock - 560 chars
    LyricsPreset(
        id="christian_light",
        name="Walk In Light (Christian)",
        genre="Christian",
        mood="Uplifting",
        tags=["faith", "hope", "spiritual"],
        description="Uplifting faith-based rock",
        content="""[Verse 1]
When the darkness closes in
And I'm drowning in my sin
A voice calls from above
Reminding me of endless love

[Chorus]
Walk in light, walk in grace
Feel the warmth of His embrace
Every step along the way
He guides me through each day
Walk in light

[Verse 2]
Though the path is hard to see
His love will set me free
I put my trust in higher hands
Following His perfect plans

[Chorus]
Walk in light, walk in grace
Feel the warmth of His embrace
Every step along the way
He guides me through each day""",
    ),
    # 42. Classic Rock - 575 chars
    LyricsPreset(
        id="classic_highway",
        name="Highway Riders (Classic Rock)",
        genre="Classic Rock",
        mood="Adventurous",
        tags=["road", "freedom", "classic"],
        description="Classic rock road trip anthem",
        content="""[Verse 1]
Chrome exhaust and open road
Carrying a heavy load
The radio plays our song
As we ride the night along

[Chorus]
Highway riders, born to roam
Every mile becomes our home
Wind in hair and sun on face
We're the kings of endless space
Highway riders

[Verse 2]
From coast to coast we make our way
Living for another day
The journey is the destination
A beautiful hallucination

[Bridge]
They can't understand our way
We live and ride, come what may

[Chorus]
Highway riders, born to roam
Every mile becomes our home""",
    ),
    # 43. New Wave - 505 chars
    LyricsPreset(
        id="new_wave_midnight",
        name="Midnight Radio (New Wave)",
        genre="New Wave",
        mood="Atmospheric",
        tags=["80s", "synth", "moody"],
        description="Atmospheric 80s new wave",
        content="""[Verse 1]
Static crackles through the night
Neon signs provide the light
DJ plays our favorite song
Where do broken hearts belong

[Chorus]
Midnight radio calling out
Spinning records filled with doubt
Lonely hearts connect tonight
Through the airwaves burning bright
Midnight radio

[Verse 2]
Dial in to frequency
The soundtrack of our misery
But somehow through the pain
We dance like we're insane

[Chorus]
Midnight radio calling out
Spinning records filled with doubt""",
    ),
    # 44. Indie Folk - 545 chars
    LyricsPreset(
        id="indie_folk_cabin",
        name="Cabin In The Woods",
        genre="Indie Folk",
        mood="Cozy",
        tags=["rustic", "simple", "nature"],
        description="Cozy cabin retreat song",
        content="""[Verse 1]
Wood smoke rising to the sky
As the autumn days go by
A cabin hidden in the trees
Living life just as I please

[Chorus]
In my cabin in the woods
Living simply, living good
Far from chaos, far from noise
Finding peace and simple joys
Cabin in the woods

[Verse 2]
Coffee brewing on the stove
Reading books of treasure troves
The forest is my only friend
Peace that never has to end

[Chorus]
In my cabin in the woods
Living simply, living good
Far from chaos, far from noise
Finding peace and simple joys""",
    ),
    # 45. Hardcore Punk - 480 chars
    LyricsPreset(
        id="hardcore_no_future",
        name="No Future (Hardcore)",
        genre="Hardcore",
        mood="Defiant",
        tags=["fast", "angry", "punk"],
        description="Fast hardcore punk defiance",
        content="""[Verse 1]
System's broken from the start
Tearing this whole world apart
They don't care about our lives
Just surviving to survive

[Chorus]
No future, that's what they say
But we're gonna find a way
Burn it down and start anew
That's what we were born to do
No future

[Verse 2]
Rise up from the underground
Make some noise, make some sound
United we will never fall
Together we can have it all

[Chorus]
No future, that's what they say
But we're gonna find a way""",
    ),
    # 46. Synthpop - 510 chars
    LyricsPreset(
        id="synthpop_electric",
        name="Electric Dreams (Synthpop)",
        genre="Synthpop",
        mood="Nostalgic",
        tags=["retro", "electronic", "80s"],
        description="Nostalgic synthpop vibes",
        content="""[Verse 1]
Fluorescent lights and arcade games
Nothing here was ever the same
Before the world became so gray
When we believed we'd find a way

[Chorus]
Electric dreams of you and me
A future that we'd never see
But in my mind it still remains
Those synth-soaked summer evening rains
Electric dreams

[Verse 2]
VHS and cassette tapes
Memories that never escape
We were young and full of hope
Learning how to cope

[Chorus]
Electric dreams of you and me
A future that we'd never see""",
    ),
    # 47. Americana - 565 chars
    LyricsPreset(
        id="americana_crossroads",
        name="Crossroads (Americana)",
        genre="Americana",
        mood="Contemplative",
        tags=["roots", "heartland", "journey"],
        description="Americana crossroads reflection",
        content="""[Verse 1]
Standing at the crossroads now
Trying to figure out somehow
Which road will lead me home
Or if I'm meant to always roam

[Chorus]
At the crossroads of my life
Cut through the doubt like a knife
Every choice will shape my fate
Hope it's never too late
Crossroads

[Verse 2]
Dusty boots and worn-out soul
Searching for a way to feel whole
The signs all point different ways
Lost in a endless maze

[Bridge]
Maybe there's no right or wrong
Just different verses of the same song

[Chorus]
At the crossroads of my life
Cut through the doubt like a knife""",
    ),
    # 48. Shoegaze - 540 chars
    LyricsPreset(
        id="shoegaze_waves",
        name="Waves of Static (Shoegaze)",
        genre="Shoegaze",
        mood="Hazy",
        tags=["reverb", "dreamy", "wash"],
        description="Dreamy shoegaze soundscape",
        content="""[Verse 1]
Lost inside a wall of sound
Floating high above the ground
Colors blur and blend as one
Staring straight into the sun

[Chorus]
Waves of static fill my ears
Washing away all my fears
Drifting through this endless sea
Finding where I'm meant to be
Waves of static

[Verse 2]
Feedback hums a lullaby
As the world goes drifting by
Nothing matters anymore
Lost on this distorted shore

[Chorus]
Waves of static fill my ears
Washing away all my fears
Drifting through this endless sea""",
    ),
    # 49. Southern Rock - 570 chars
    LyricsPreset(
        id="southern_whiskey",
        name="Whiskey River (Southern Rock)",
        genre="Southern Rock",
        mood="Wild",
        tags=["rebel", "country", "rock"],
        description="Wild southern rock anthem",
        content="""[Verse 1]
Down in Georgia where I was raised
Spent my youth in a whiskey haze
Learned to play guitar at ten
Never looked back since then

[Chorus]
Whiskey river running wild
Been this way since I was a child
Southern blood runs through my veins
Breaking hearts and raising canes
Whiskey river

[Verse 2]
Honky tonks and neon signs
Living life between the lines
A rebel till my dying day
Wouldn't have it any other way

[Bridge]
Pour another round for me
Living fast and living free

[Chorus]
Whiskey river running wild
Been this way since I was a child""",
    ),
    # 50. Trip Hop - 515 chars
    LyricsPreset(
        id="trip_hop_shadows",
        name="City Shadows (Trip Hop)",
        genre="Trip Hop",
        mood="Mysterious",
        tags=["urban", "dark", "beats"],
        description="Dark urban trip hop vibes",
        content="""[Verse 1]
Street lights flicker down below
Secrets that the city knows
Shadows dance on broken walls
As the rain begins to fall

[Chorus]
City shadows come alive
In the darkness we survive
Beat drops low and bass runs deep
Secrets that we'll always keep
City shadows

[Verse 2]
Smoke rises from the grates
We're the ones who tempt the fates
Underground we make our stand
A world you'll never understand

[Chorus]
City shadows come alive
In the darkness we survive""",
    ),
    # 51. Dream Pop - 525 chars
    LyricsPreset(
        id="dream_pop_stardust",
        name="Stardust (Dream Pop)",
        genre="Dream Pop",
        mood="Ethereal",
        tags=["cosmic", "soft", "floating"],
        description="Ethereal cosmic dream pop",
        content="""[Verse 1]
Floating through the atmosphere
Everything becomes so clear
Stars align to guide my way
Night transforms into day

[Chorus]
We are stardust, you and I
Scattered across the evening sky
Infinite and undefined
Two souls perfectly combined
Stardust

[Verse 2]
Galaxies spin slow and bright
In the velvet cloak of night
We're connected by the light
Of a billion stars tonight

[Chorus]
We are stardust, you and I
Scattered across the evening sky
Infinite and undefined""",
    ),
    # 52. Post-Rock - 555 chars
    LyricsPreset(
        id="post_rock_horizons",
        name="Distant Horizons (Post-Rock)",
        genre="Post-Rock",
        mood="Expansive",
        tags=["instrumental", "building", "epic"],
        description="Epic post-rock journey",
        content="""[Verse 1]
The silence breaks with trembling sound
As guitars begin to pound
Building slowly toward the light
From the depths of endless night

[Chorus]
Distant horizons call to me
A world of possibility
Every note a step ahead
Following where angels led
Distant horizons

[Verse 2]
Crescendo rising like the tide
With nowhere left for us to hide
The wall of sound will set us free
This is who we're meant to be

[Chorus]
Distant horizons call to me
A world of possibility
Every note a step ahead""",
    ),
    # 53. Glam Rock - 540 chars
    LyricsPreset(
        id="glam_superstar",
        name="Superstar (Glam Rock)",
        genre="Glam Rock",
        mood="Flamboyant",
        tags=["sparkle", "fame", "theatrical"],
        description="Theatrical glam rock anthem",
        content="""[Verse 1]
Sequins sparkle, platforms tall
Tonight I'm gonna have it all
The spotlight follows where I go
Time to put on quite a show

[Chorus]
I'm a superstar tonight
Burning brighter than the light
Glitter falling like the rain
Rock and roll runs through my veins
Superstar

[Verse 2]
Make-up on and hair teased high
Gonna light up the sky
Every move is choreographed
On this stage I was meant to have

[Chorus]
I'm a superstar tonight
Burning brighter than the light
Glitter falling like the rain""",
    ),
    # 54. Britpop - 520 chars
    LyricsPreset(
        id="britpop_london",
        name="London Calling Me (Britpop)",
        genre="Britpop",
        mood="Nostalgic",
        tags=["90s", "british", "youth"],
        description="90s Britpop nostalgia",
        content="""[Verse 1]
Camden Town on Saturday night
Everything is feeling right
Pint in hand and friends around
Best mates that I've ever found

[Chorus]
London's calling me tonight
Through the rain and neon lights
This is where I want to be
London's calling out to me
Calling me

[Verse 2]
Down the tube to Leicester Square
Britpop playing everywhere
This is what we're living for
Always wanting something more

[Chorus]
London's calling me tonight
Through the rain and neon lights""",
    ),
    # 55. Industrial - 510 chars
    LyricsPreset(
        id="industrial_machine",
        name="Machine Heart (Industrial)",
        genre="Industrial",
        mood="Mechanical",
        tags=["dark", "electronic", "harsh"],
        description="Dark industrial machine anthem",
        content="""[Verse 1]
Gears are grinding, sparks fly free
This machine is all of me
Flesh and metal intertwined
Leave your humanity behind

[Chorus]
Machine heart beats in my chest
Put your weakness to the test
Cold and chrome, no room for fear
The future is already here
Machine heart

[Verse 2]
Production line of broken souls
Automation takes its toll
But we adapt, we overcome
This is what we have become

[Chorus]
Machine heart beats in my chest
Put your weakness to the test""",
    ),
    # 56. Celtic Rock - 565 chars
    LyricsPreset(
        id="celtic_emerald",
        name="Emerald Isle (Celtic Rock)",
        genre="Celtic",
        mood="Spirited",
        tags=["irish", "folk", "festive"],
        description="Spirited Celtic rock celebration",
        content="""[Verse 1]
Across the rolling hills so green
The finest land I've ever seen
Where fiddles play and people sing
And joy is the only thing

[Chorus]
Emerald isle, my heart's true home
No matter how far I may roam
The music calls me back again
To dance among my countrymen
Emerald isle

[Verse 2]
Raise your glass up to the sky
As the night goes flying by
Stories told around the fire
Our spirits rising ever higher

[Bridge]
The pipes are calling, can you hear
The sound that washes away fear

[Chorus]
Emerald isle, my heart's true home""",
    ),
    # 57. Garage Rock - 490 chars
    LyricsPreset(
        id="garage_loud",
        name="Loud and Proud (Garage Rock)",
        genre="Garage Rock",
        mood="Raw",
        tags=["lo-fi", "punk", "energetic"],
        description="Raw garage rock energy",
        content="""[Verse 1]
Four chords and the truth
Taking me back to my youth
Amp turned up to eleven
This basement is our heaven

[Chorus]
Loud and proud, that's our way
Got something real to say
Don't need no fancy gear
Just rock and roll and beer
Loud and proud

[Verse 2]
Sweat drips on the floor
The neighbors banging on the door
Don't care what they think
Playing our songs on the brink

[Chorus]
Loud and proud, that's our way
Got something real to say""",
    ),
    # 58. Melodic Hardcore - 545 chars
    LyricsPreset(
        id="melodic_hc_burning",
        name="Burning Bridges (Melodic HC)",
        genre="Melodic Hardcore",
        mood="Passionate",
        tags=["intense", "emotional", "punk"],
        description="Passionate melodic hardcore",
        content="""[Verse 1]
Every word you said was lies
Looking past your disguise
Trusted you with everything
Now I feel the poison sting

[Chorus]
Burning bridges as I go
Leaving everything I know
Can't go back to what we had
The good times turned to bad
Burning bridges

[Verse 2]
The flames light up the night
As I finally see the light
Moving forward, looking back
Everything has turned to black

[Chorus]
Burning bridges as I go
Leaving everything I know
Can't go back to what we had""",
    ),
    # 59. Math Rock - 535 chars
    LyricsPreset(
        id="math_rock_patterns",
        name="Patterns (Math Rock)",
        genre="Math Rock",
        mood="Complex",
        tags=["technical", "odd-time", "intricate"],
        description="Complex math rock patterns",
        content="""[Verse 1]
Seven beats then five again
Trying to figure out the plan
Every note a puzzle piece
A complexity that won't cease

[Chorus]
Patterns weaving through my mind
Rhythms of a different kind
Count along if you can try
Numbers dancing through the sky
Patterns

[Verse 2]
Change the time, shift the groove
Find the pattern, find the move
Nothing simple, nothing plain
Beauty found in the arcane

[Chorus]
Patterns weaving through my mind
Rhythms of a different kind""",
    ),
    # 60. Gothic Metal - 580 chars
    LyricsPreset(
        id="gothic_eternal",
        name="Eternal Night (Gothic Metal)",
        genre="Gothic Metal",
        mood="Dark",
        tags=["dramatic", "orchestral", "heavy"],
        description="Dark gothic metal drama",
        content="""[Verse 1]
Candlelight flickers on the walls
As darkness comes and silence falls
The moon ascends her throne on high
A witness to my mournful cry

[Chorus]
In eternal night I dwell
Between the realms of heaven and hell
My soul forever bound in chains
Beauty born from endless pain
Eternal night

[Verse 2]
Velvet curtains hide the sun
My lonely journey's just begun
Orchestras of doom do play
As night devours another day

[Bridge]
I embrace the dark within
Where salvation meets the sin

[Chorus]
In eternal night I dwell
Between the realms of heaven and hell""",
    ),
    # 61. Reggaeton - 495 chars
    LyricsPreset(
        id="reggaeton_fuego",
        name="Puro Fuego (Reggaeton)",
        genre="Reggaeton",
        mood="Hot",
        tags=["latin", "dance", "club"],
        description="Hot reggaeton club track",
        content="""[Verse 1]
El ritmo me lleva a bailar
Tonight we're gonna raise the bar
The beat drops and we ignite
Burning up the floor tonight

[Chorus]
Puro fuego when we dance
Give me just one more chance
Move your body side to side
Feel the fire deep inside
Puro fuego

[Verse 2]
La música in my veins
Breaking through all the chains
Everybody feeling right
This is gonna be our night

[Chorus]
Puro fuego when we dance
Give me just one more chance""",
    ),
    # 62. Metalcore - 555 chars
    LyricsPreset(
        id="metalcore_awakening",
        name="The Awakening (Metalcore)",
        genre="Metalcore",
        mood="Intense",
        tags=["breakdown", "screams", "heavy"],
        description="Intense metalcore awakening",
        content="""[Verse 1]
Open your eyes and finally see
Everything they claimed you'd be
Was nothing but a pack of lies
Time to claim your rightful prize

[Chorus]
This is the awakening
The moment we've been waiting
Rise up from the ashes now
Take a stand, make a vow
Awakening

[Verse 2]
The breakdown hits, the pit explodes
Releasing all our heavy loads
Together we will start anew
The only way we're getting through

[Breakdown]
Wake up, wake up, open your eyes
See through all their lies

[Chorus]
This is the awakening
The moment we've been waiting""",
    ),
    # 63. Chillwave - 505 chars
    LyricsPreset(
        id="chillwave_sunset",
        name="Sunset Drive (Chillwave)",
        genre="Chillwave",
        mood="Relaxed",
        tags=["lo-fi", "nostalgic", "summer"],
        description="Relaxed chillwave vibes",
        content="""[Verse 1]
Windows down, the warm breeze flows
Heading where nobody knows
The sunset paints the sky in gold
A moment precious to behold

[Chorus]
Sunset drive along the coast
With the one I love the most
Let the moment slip away
Nothing left that I can say
Sunset drive

[Verse 2]
Synths wash over like the tide
With you here right by my side
The world outside just fades away
Wish that we could always stay

[Chorus]
Sunset drive along the coast
With the one I love the most""",
    ),
    # 64. Screamo - 520 chars
    LyricsPreset(
        id="screamo_silence",
        name="Silence Screaming (Screamo)",
        genre="Screamo",
        mood="Anguished",
        tags=["raw", "emotional", "chaotic"],
        description="Raw emotional screamo",
        content="""[Verse 1]
Every word gets stuck inside
Emotions that I try to hide
The pressure building up so fast
I know this feeling cannot last

[Chorus]
Silence screaming in my head
All the words I should have said
Let it out, let it go
Feel the pain, feel it flow
Silence screaming

[Verse 2]
Tears streaming down my face
Lost in this chaotic space
But the scream will set me free
Finally becoming me

[Chorus]
Silence screaming in my head
All the words I should have said""",
    ),
    # 65. Blues Rock - 560 chars
    LyricsPreset(
        id="blues_rock_devil",
        name="Devil's Highway (Blues Rock)",
        genre="Blues Rock",
        mood="Gritty",
        tags=["guitar", "soul", "raw"],
        description="Gritty blues rock tale",
        content="""[Verse 1]
Met the devil on a dusty road
Tried to buy my soul
He said boy, what's your price
I said you ain't that nice

[Chorus]
On the devil's highway I ride
Got nothing left to hide
My guitar is all I need
To plant that rock and roll seed
Devil's highway

[Verse 2]
Bent the strings until they cried
Played until my fingers fried
The devil said you got the touch
I said that ain't saying much

[Bridge]
Trade my soul? I'd rather not
I'll keep what I already got

[Chorus]
On the devil's highway I ride
Got nothing left to hide""",
    ),
    # 66. Afrobeat - 530 chars
    LyricsPreset(
        id="afrobeat_rhythm",
        name="Rhythm of Life (Afrobeat)",
        genre="Afrobeat",
        mood="Joyful",
        tags=["african", "groove", "world"],
        description="Joyful Afrobeat celebration",
        content="""[Verse 1]
The drums are calling out tonight
Under African starlight
Move your body, feel the beat
Dancing with a thousand feet

[Chorus]
This is the rhythm of life
Cutting through the darkness like a knife
From the village to the city streets
Where the ancient and the modern meets
Rhythm of life

[Verse 2]
Horns blast like elephants call
United standing tall
The groove will set your spirit free
This is our destiny

[Chorus]
This is the rhythm of life
Cutting through the darkness like a knife""",
    ),
    # 67. Stoner Rock - 555 chars
    LyricsPreset(
        id="stoner_desert",
        name="Desert Fuzz (Stoner Rock)",
        genre="Stoner Rock",
        mood="Heavy",
        tags=["fuzz", "slow", "psychedelic"],
        description="Heavy desert stoner rock",
        content="""[Verse 1]
Sun is blazing overhead
Another day among the dead
Cactus shadows stretch so long
As we play another song

[Chorus]
Desert fuzz surrounds us now
Don't ask why, don't ask how
The riff is heavy, deep and slow
Let the distortion flow
Desert fuzz

[Verse 2]
Miles of nothing all around
Just the groove and the sound
Lost in haze of smoke and tone
Out here we're never alone

[Bridge]
The amp feeds back and screams
Reality bursts at the seams

[Chorus]
Desert fuzz surrounds us now
Don't ask why, don't ask how""",
    ),
    # 68. Dancehall - 490 chars
    LyricsPreset(
        id="dancehall_island",
        name="Island Vibes (Dancehall)",
        genre="Dancehall",
        mood="Party",
        tags=["caribbean", "dance", "tropical"],
        description="Caribbean dancehall party",
        content="""[Verse 1]
Pull up selecta, drop the beat
Everybody move your feet
Caribbean sun is shining bright
We gonna party through the night

[Chorus]
Island vibes are what we bring
Come on everybody swing
Wave your hands up in the air
Good vibes everywhere
Island vibes

[Verse 2]
The bass is pumping loud and strong
Sing along to our song
From Kingston town we spread the love
Blessings from the sky above

[Chorus]
Island vibes are what we bring
Come on everybody swing""",
    ),
    # 69. Post-Punk - 535 chars
    LyricsPreset(
        id="post_punk_grey",
        name="Grey Days (Post-Punk)",
        genre="Post-Punk",
        mood="Cold",
        tags=["angular", "dark", "80s"],
        description="Cold angular post-punk",
        content="""[Verse 1]
Factory smoke fills the sky
Another grey day passing by
The city breathes its toxic air
A world beyond repair

[Chorus]
Grey days, grey nights
Lost in industrial lights
The rhythm pounds like machinery
This is our modern destiny
Grey days

[Verse 2]
Concrete jungle, steel and stone
In this city, we're alone
Dancing to the factory beat
On cold and empty streets

[Chorus]
Grey days, grey nights
Lost in industrial lights
The rhythm pounds like machinery""",
    ),
    # 70. Pop Punk - 510 chars
    LyricsPreset(
        id="pop_punk_summer",
        name="Last Summer (Pop Punk)",
        genre="Pop Punk",
        mood="Nostalgic",
        tags=["youth", "summer", "fun"],
        description="Nostalgic pop punk summer",
        content="""[Verse 1]
Backyard parties every night
Everything was feeling right
You and me against the world
When our whole lives unfurled

[Chorus]
Last summer changed everything
Still hear the phone when it rings
We were young and stupid then
Wish we could go back again
Last summer

[Verse 2]
Sneaking out past midnight hours
Singing songs under the towers
Nothing mattered except right now
Made it through, don't ask how

[Chorus]
Last summer changed everything
Still hear the phone when it rings""",
    ),
    # 71. Art Rock - 570 chars
    LyricsPreset(
        id="art_rock_museum",
        name="Museum Piece (Art Rock)",
        genre="Art Rock",
        mood="Theatrical",
        tags=["avant-garde", "theatrical", "complex"],
        description="Theatrical art rock piece",
        content="""[Verse 1]
Hanging on a gallery wall
Watching as the people fall
For the illusion that they see
What is art, what is me

[Chorus]
I'm a museum piece on display
People staring every day
Looking for meaning in my eyes
Behind the frame my spirit dies
Museum piece

[Verse 2]
The critics write their fancy words
As meaningful as flocks of birds
They see whatever they want to see
But never really notice me

[Bridge]
Am I the art or am I real
Tell me how I'm supposed to feel

[Chorus]
I'm a museum piece on display
People staring every day""",
    ),
    # 72. Oi Punk - 485 chars
    LyricsPreset(
        id="oi_working",
        name="Working Class (Oi)",
        genre="Oi",
        mood="Defiant",
        tags=["street", "punk", "unity"],
        description="Working class punk anthem",
        content="""[Verse 1]
Up at five to start the day
Barely making any pay
The bosses live in luxury
While we fight for dignity

[Chorus]
Working class and proud to be
Fighting for our liberty
Stand together, side by side
Working class and unified
Oi, oi, oi

[Verse 2]
They look down from up above
But we've got something they don't have
Solidarity and pride
And that can never be denied

[Chorus]
Working class and proud to be
Fighting for our liberty""",
    ),
    # 73. Darkwave - 525 chars
    LyricsPreset(
        id="darkwave_velvet",
        name="Velvet Shadows (Darkwave)",
        genre="Darkwave",
        mood="Haunting",
        tags=["gothic", "synth", "mysterious"],
        description="Haunting darkwave atmosphere",
        content="""[Verse 1]
Candles flicker in the gloom
Inside this velvet-draped room
Synths wash over like a tide
Of memories I try to hide

[Chorus]
Velvet shadows on the wall
Hear the darkness when it calls
Lost in beauty and despair
Tangled in the midnight air
Velvet shadows

[Verse 2]
The bass pulse like a heart
As the night begins to start
Dance among the mourning souls
Where the music takes control

[Chorus]
Velvet shadows on the wall
Hear the darkness when it calls""",
    ),
    # 74. Surf Rock - 505 chars
    LyricsPreset(
        id="surf_endless",
        name="Endless Waves (Surf Rock)",
        genre="Surf",
        mood="Carefree",
        tags=["beach", "summer", "guitar"],
        description="Carefree surf rock vibes",
        content="""[Verse 1]
Wax the board at break of day
Another perfect surf today
The waves are calling out my name
Every day is not the same

[Chorus]
Endless waves roll to the shore
That's what we're living for
Salt and sun and sand between our toes
Living the life that everyone knows
Endless waves

[Verse 2]
Hanging ten under blue skies
Ocean sparkles in my eyes
This is where I'm meant to be
Forever young, forever free

[Chorus]
Endless waves roll to the shore
That's what we're living for""",
    ),
    # 75. Doom Metal - 565 chars
    LyricsPreset(
        id="doom_funeral",
        name="Funeral March (Doom Metal)",
        genre="Doom Metal",
        mood="Crushing",
        tags=["heavy", "slow", "dark"],
        description="Crushing doom metal dirge",
        content="""[Verse 1]
Slow and heavy, the riff descends
Into the void where nothing ends
The weight of ages on my back
The world dissolves to endless black

[Chorus]
Funeral march plays on and on
Until all hope is finally gone
The doom is coming, feel the weight
Bow before your crushing fate
Funeral march

[Verse 2]
Feedback wails like tortured souls
As the bell of ending tolls
Each note drags through thick despair
Suffocating in the air

[Bridge]
Slower, heavier, we descend
Journey to the bitter end

[Chorus]
Funeral march plays on and on""",
    ),
    # 76. Eurodance - 480 chars
    LyricsPreset(
        id="eurodance_night",
        name="Into The Night (Eurodance)",
        genre="Eurodance",
        mood="Energetic",
        tags=["90s", "club", "europop"],
        description="High-energy 90s eurodance",
        content="""[Verse 1]
DJ spin that record round
Feel the bass beneath the ground
Laser lights across the floor
Come on give me something more

[Chorus]
Into the night we fly
Hands up reaching to the sky
Feel the beat go through your soul
Eurodance is in control
Into the night

[Verse 2]
Happy people all around
This is the ultimate sound
Europe style from east to west
This music is the best

[Chorus]
Into the night we fly
Hands up reaching to the sky""",
    ),
    # 77. Thrash Metal - 555 chars
    LyricsPreset(
        id="thrash_war",
        name="War Machine (Thrash Metal)",
        genre="Thrash Metal",
        mood="Aggressive",
        tags=["fast", "heavy", "political"],
        description="Aggressive thrash metal attack",
        content="""[Verse 1]
Sirens wail across the land
Destruction by the human hand
The war machine keeps rolling on
Until everything is gone

[Chorus]
War machine, war machine
Crushing everything between
The gears of death keep turning round
Hear the apocalypse sound
War machine

[Verse 2]
Politicians play their games
While the cities burn in flames
The profit made from blood and tears
Exploiting all our deepest fears

[Bridge]
Who will stop this endless war
What are we fighting for

[Chorus]
War machine, war machine
Crushing everything between""",
    ),
    # 78. Lo-Fi Hip Hop - 495 chars
    LyricsPreset(
        id="lofi_midnight",
        name="Midnight Study (Lo-Fi)",
        genre="Lo-Fi",
        mood="Chill",
        tags=["study", "relax", "beats"],
        description="Chill lo-fi study vibes",
        content="""[Verse 1]
Lamp light glowing soft and low
Vinyl crackles in the flow
Coffee steam rises up high
Another sleepless night goes by

[Chorus]
Midnight study, beats so low
Thoughts drift by and come and go
In this moment, time stands still
Lost in vibes, I always will
Midnight study

[Verse 2]
Pages turn but I don't read
Lost in thoughts I didn't need
The beat keeps going, soft and slow
Nowhere else I'd rather go

[Chorus]
Midnight study, beats so low""",
    ),
    # 79. Viking Metal - 580 chars
    LyricsPreset(
        id="viking_valhalla",
        name="Shores of Valhalla (Viking)",
        genre="Viking Metal",
        mood="Epic",
        tags=["norse", "epic", "battle"],
        description="Epic Viking metal saga",
        content="""[Verse 1]
Longships sail across the sea
Warriors born to be free
Odin guides us through the storm
To Valhalla, golden and warm

[Chorus]
On the shores of Valhalla we stand
Sword and shield within our hand
The Valkyries come to take us home
No more will we ever roam
Valhalla

[Verse 2]
Battle cries ring through the night
Axes gleaming in firelight
We will feast in Odin's hall
Legends that will never fall

[Bridge]
Mjolnir strikes and thunder roars
Our blood runs from ancient wars

[Chorus]
On the shores of Valhalla we stand
Sword and shield within our hand""",
    ),
    # 80. Bubblegum Pop - 475 chars
    LyricsPreset(
        id="bubble_crush",
        name="Crush On You (Bubblegum)",
        genre="Bubblegum Pop",
        mood="Sweet",
        tags=["cute", "fun", "teenage"],
        description="Sweet teen pop crush song",
        content="""[Verse 1]
Every time you walk on by
Butterflies begin to fly
Can't stop thinking about you
Everything you say and do

[Chorus]
I've got a crush, crush on you
Everything you do is true
My heart goes boom, boom, boom
Whenever you walk in the room
Crush on you

[Verse 2]
Write your name a thousand times
In my notebook, in my rhymes
Hope one day you'll notice me
And see the way it's meant to be

[Chorus]
I've got a crush, crush on you
Everything you do is true""",
    ),
    # 81. Deathcore - 540 chars
    LyricsPreset(
        id="deathcore_abyss",
        name="Into The Abyss (Deathcore)",
        genre="Deathcore",
        mood="Brutal",
        tags=["heavy", "breakdown", "extreme"],
        description="Brutal deathcore descent",
        content="""[Verse 1]
Descending into endless black
There's no way of coming back
The breakdown hits like hammer blows
Into the abyss it goes

[Chorus]
Into the abyss we fall
The darkness swallows all
No light will ever reach this deep
Eternal nightmare, endless sleep
Into the abyss

[Verse 2]
Guttural screams fill the void
Everything will be destroyed
The blast beats never cease
There will be no peace

[Breakdown]
Bow down, bow down to the void
Everything will be destroyed

[Chorus]
Into the abyss we fall""",
    ),
    # 82. K-Pop Style - 510 chars
    LyricsPreset(
        id="kpop_shine",
        name="Shine Tonight (K-Pop Style)",
        genre="K-Pop",
        mood="Bright",
        tags=["dance", "catchy", "modern"],
        description="Bright K-Pop dance track",
        content="""[Verse 1]
Camera flashes everywhere
Perfect moves without a care
Every step choreographed
Living for the aftermath

[Chorus]
Shine tonight like a star
Showing the world who we are
Light it up, make it bright
This is our time to shine tonight
Shine tonight

[Verse 2]
Practice makes us who we are
Reaching for the stars so far
The stage is where we come alive
Together we will always thrive

[Chorus]
Shine tonight like a star
Showing the world who we are""",
    ),
    # 83. Emo Pop - 530 chars
    LyricsPreset(
        id="emo_pop_diary",
        name="Dear Diary (Emo Pop)",
        genre="Emo Pop",
        mood="Confessional",
        tags=["personal", "emotional", "youth"],
        description="Confessional emo pop",
        content="""[Verse 1]
Dear diary, today was rough
Feel like I'm never good enough
The kids at school don't understand
This life wasn't what I planned

[Chorus]
Dear diary, can you hear me cry
Another lonely night goes by
These pages hold my deepest fears
Soaked with all these teenage tears
Dear diary

[Verse 2]
Headphones on, I fade away
Music helps me through each day
Maybe someday they will see
The person I was meant to be

[Chorus]
Dear diary, can you hear me cry
Another lonely night goes by""",
    ),
    # 84. Power Metal - 565 chars
    LyricsPreset(
        id="power_metal_dragon",
        name="Dragonfire (Power Metal)",
        genre="Power Metal",
        mood="Triumphant",
        tags=["fantasy", "epic", "soaring"],
        description="Epic fantasy power metal",
        content="""[Verse 1]
In the kingdom far away
The dragon wakes to start the day
Fire burning in its eyes
Underneath the crimson skies

[Chorus]
Dragonfire lights the night
Warriors ready for the fight
Swords are drawn and shields are high
Tonight is when the dragon dies
Dragonfire

[Verse 2]
The chosen one will rise to fame
Calling out the dragon's name
Steel meets scales in epic clash
Turning legends into ash

[Bridge]
Soaring high above the clouds
Hero standing tall and proud

[Chorus]
Dragonfire lights the night
Warriors ready for the fight""",
    ),
    # 85. Bedroom Pop - 490 chars
    LyricsPreset(
        id="bedroom_lonely",
        name="Lonely Nights (Bedroom Pop)",
        genre="Bedroom Pop",
        mood="Intimate",
        tags=["lo-fi", "personal", "soft"],
        description="Intimate bedroom pop",
        content="""[Verse 1]
Four walls and a guitar
Singing to the distant stars
Recording on my phone tonight
Hoping someone feels it right

[Chorus]
Lonely nights in my room
Singing songs into the gloom
Maybe someone out there hears
These melodies through all my tears
Lonely nights

[Verse 2]
Autotune my broken heart
This is how I make my art
Upload it to the cloud
Hope it makes somebody proud

[Chorus]
Lonely nights in my room
Singing songs into the gloom""",
    ),
    # 86. Symphonic Metal - 575 chars
    LyricsPreset(
        id="symphonic_dark_queen",
        name="Dark Queen (Symphonic Metal)",
        genre="Symphonic Metal",
        mood="Majestic",
        tags=["orchestral", "operatic", "dramatic"],
        description="Majestic symphonic metal",
        content="""[Verse 1]
The orchestra begins to play
As darkness steals the light of day
Upon her throne of ice and bone
The dark queen rules this land alone

[Chorus]
Dark queen of the frozen north
Lead your armies ever forth
Symphonies of doom resound
As winter claims the battleground
Dark queen

[Verse 2]
Her voice rings out like crystal clear
Striking hope into hearts with fear
The strings crescendo to the sky
As mortals bow their heads and die

[Bridge]
The opera of destruction plays
Through endless nights and frozen days

[Chorus]
Dark queen of the frozen north""",
    ),
    # 87. Trap Soul - 505 chars
    LyricsPreset(
        id="trap_soul_late",
        name="Late Night Texts (Trap Soul)",
        genre="Trap Soul",
        mood="Longing",
        tags=["r&b", "trap", "romantic"],
        description="Moody trap soul vibes",
        content="""[Verse 1]
3 AM and you on my mind
Scrolling through our texts to find
A sign that you still feel the same
Playing your heart like a game

[Chorus]
Late night texts, I can't sleep
These feelings running way too deep
Notification lights my screen
You know exactly what I mean
Late night texts

[Verse 2]
Blue ticks but you don't reply
Leaving me to wonder why
The typing stops and starts again
Where do we even begin

[Chorus]
Late night texts, I can't sleep""",
    ),
    # 88. Melodic Death Metal - 555 chars
    LyricsPreset(
        id="melodeath_fallen",
        name="The Fallen (Melodic Death)",
        genre="Melodic Death",
        mood="Sorrowful",
        tags=["swedish", "melodic", "heavy"],
        description="Swedish melodeath sorrow",
        content="""[Verse 1]
Across the fields of endless grey
Where fallen heroes slowly decay
The melodies of death arise
Beneath the cold and weeping skies

[Chorus]
We are the fallen, hear our cry
Beneath the Scandinavian sky
In death we find our harmony
A melancholy melody
The fallen

[Verse 2]
Twin guitars weep in the night
As blast beats thunder with all their might
The growls tell stories of the past
Of glory that was never meant to last

[Chorus]
We are the fallen, hear our cry
Beneath the Scandinavian sky""",
    ),
    # 89. Hyperpop - 475 chars
    LyricsPreset(
        id="hyperpop_glitch",
        name="Glitch In The System (Hyperpop)",
        genre="Hyperpop",
        mood="Chaotic",
        tags=["distorted", "digital", "experimental"],
        description="Chaotic hyperpop explosion",
        content="""[Verse 1]
Error codes running through my brain
Processing love but feeling pain
Distorted bass hits different now
Breaking all the rules somehow

[Chorus]
I'm a glitch in the system
Digital kisses missed em
Pitch-shifted tears fall down
The weirdest sound in town
Glitch glitch glitch

[Verse 2]
Auto-tuned to the extreme
Living in a fever dream
Nothing sounds like it should
And that's exactly good

[Chorus]
I'm a glitch in the system""",
    ),
    # 90. Neo Soul - 545 chars
    LyricsPreset(
        id="neo_soul_morning",
        name="Sunday Morning (Neo Soul)",
        genre="Neo Soul",
        mood="Warm",
        tags=["soulful", "jazzy", "smooth"],
        description="Warm neo soul morning vibes",
        content="""[Verse 1]
Coffee brewing, sun streams in
Another beautiful day begins
Your head upon my shoulder rests
Of all the moments, this the best

[Chorus]
Sunday morning, take it slow
Nowhere that we need to go
Your love wraps around me tight
Everything is feeling right
Sunday morning

[Verse 2]
Records playing soft and low
That organic vinyl flow
These moments that we share
Show me how much you care

[Chorus]
Sunday morning, take it slow
Nowhere that we need to go
Your love wraps around me tight""",
    ),
    # 91. Noise Rock - 510 chars
    LyricsPreset(
        id="noise_static",
        name="Static Minds (Noise Rock)",
        genre="Noise Rock",
        mood="Chaotic",
        tags=["experimental", "harsh", "avant-garde"],
        description="Chaotic noise rock assault",
        content="""[Verse 1]
Feedback howls like wolves at night
Nothing here is ever right
The noise consumes my every thought
Finding peace that can't be bought

[Chorus]
Static minds and broken dreams
Nothing's ever what it seems
Distortion is our lullaby
Screeching sounds into the sky
Static minds

[Verse 2]
Volume up until it hurts
Finding beauty in the dirt
The chaos makes a twisted sense
Building walls without a fence

[Chorus]
Static minds and broken dreams""",
    ),
    # 92. Yacht Rock - 530 chars
    LyricsPreset(
        id="yacht_smooth",
        name="Smooth Sailing (Yacht Rock)",
        genre="Yacht Rock",
        mood="Breezy",
        tags=["70s", "smooth", "sophisticated"],
        description="Smooth 70s yacht rock",
        content="""[Verse 1]
Sunset on the horizon line
Everything is feeling fine
The ocean breeze blows through my hair
Without a worry, without a care

[Chorus]
Smooth sailing, that's the life
Leave behind the stress and strife
Champagne sparkles in the light
Everything is just right
Smooth sailing

[Verse 2]
The captain says we're good to go
Cruising fast or cruising slow
This yacht is our escape
From everything that makes us ache

[Chorus]
Smooth sailing, that's the life
Leave behind the stress and strife""",
    ),
    # 93. Crunk - 480 chars
    LyricsPreset(
        id="crunk_party",
        name="Get Crunk (Crunk)",
        genre="Crunk",
        mood="Hype",
        tags=["party", "southern", "energy"],
        description="High-energy crunk party",
        content="""[Verse 1]
DJ turn it up right now
Getting crunk, show 'em how
Hands up if you feel alive
This party gonna thrive

[Chorus]
Get crunk, get crunk tonight
Everybody feeling right
Wave your hands from side to side
Let the bass be your guide
Get crunk

[Verse 2]
From the A to the world
Boys and girls get unfurled
Bounce, bounce, to the beat
Feeling hot from the heat

[Chorus]
Get crunk, get crunk tonight
Everybody feeling right""",
    ),
    # 94. Slowcore - 540 chars
    LyricsPreset(
        id="slowcore_empty",
        name="Empty Rooms (Slowcore)",
        genre="Slowcore",
        mood="Desolate",
        tags=["minimal", "slow", "sad"],
        description="Desolate slowcore atmosphere",
        content="""[Verse 1]
The clock ticks slow upon the wall
In empty rooms where shadows fall
Each minute feels like hours pass
Looking through the fogging glass

[Chorus]
Empty rooms and hollow hearts
Falling slowly, falling apart
Time means nothing anymore
Just staring at the floor
Empty rooms

[Verse 2]
Dust collects on photographs
Memories of former laughs
Now only silence fills this space
Forgotten time, forgotten place

[Chorus]
Empty rooms and hollow hearts
Falling slowly, falling apart""",
    ),
    # 95. Bounce - 490 chars
    LyricsPreset(
        id="bounce_nola",
        name="NOLA Bounce (Bounce)",
        genre="Bounce",
        mood="Party",
        tags=["new orleans", "dance", "call-response"],
        description="New Orleans bounce party",
        content="""[Verse 1]
Down in the N-O-L-A
We do it different every day
The twerk team's in the building now
Shake it fast, show 'em how

[Chorus]
Bounce to the left, bounce to the right
Shake that thing with all your might
From the ward to across the globe
Bounce music is our mode
Bounce it

[Verse 2]
Call and response, that's our style
Been doing this for quite a while
Big Freedia showed the way
New Orleans bounce is here to stay

[Chorus]
Bounce to the left, bounce to the right""",
    ),
    # 96. Math Pop - 525 chars
    LyricsPreset(
        id="math_pop_counting",
        name="Counting Stars (Math Pop)",
        genre="Math Pop",
        mood="Upbeat",
        tags=["complex", "catchy", "quirky"],
        description="Quirky math pop rhythms",
        content="""[Verse 1]
One two three then five six seven
Skipping four feels just like heaven
The time signature keeps changing round
But somehow it's a catchy sound

[Chorus]
Counting stars in odd time
Seven beats then switch to nine
It shouldn't work but somehow does
Creating all this rhythmic buzz
Counting stars

[Verse 2]
Tapping feet in strange patterns
As the complex rhythm scatters
But the melody stays true
Carrying me straight to you

[Chorus]
Counting stars in odd time
Seven beats then switch to nine""",
    ),
    # 97. Space Rock - 565 chars
    LyricsPreset(
        id="space_rock_cosmos",
        name="Across The Cosmos (Space Rock)",
        genre="Space Rock",
        mood="Cosmic",
        tags=["psychedelic", "atmospheric", "sci-fi"],
        description="Cosmic space rock journey",
        content="""[Verse 1]
Thrusters fire, we leave the ground
Silence where there is no sound
Stars streak by like lines of light
Into the eternal night

[Chorus]
Across the cosmos we will fly
Beyond the reach of mortal eye
The universe spreads out before
Infinite, forever more
Across the cosmos

[Verse 2]
Nebulas of purple haze
Lost within the stellar maze
Time dilates, the years compress
Finding peace in emptiness

[Bridge]
The ship hums a gentle song
As we drift the stars among

[Chorus]
Across the cosmos we will fly
Beyond the reach of mortal eye""",
    ),
    # 98. Sadcore - 535 chars
    LyricsPreset(
        id="sadcore_rain",
        name="It Always Rains (Sadcore)",
        genre="Sadcore",
        mood="Depressed",
        tags=["slow", "melancholic", "introspective"],
        description="Deeply melancholic sadcore",
        content="""[Verse 1]
Grey skies every single day
Can't seem to find another way
The rain keeps falling on my face
Stuck inside this lonely place

[Chorus]
It always rains when you're not here
Every day throughout the year
The clouds won't ever go away
It always rains, what can I say
It always rains

[Verse 2]
Watching droplets on the glass
Counting seconds as they pass
The weatherman says sun tomorrow
But I know there's only sorrow

[Chorus]
It always rains when you're not here
Every day throughout the year""",
    ),
    # 99. Electronic Body Music - 520 chars
    LyricsPreset(
        id="ebm_control",
        name="Total Control (EBM)",
        genre="EBM",
        mood="Commanding",
        tags=["industrial", "dance", "dark"],
        description="Commanding industrial dance",
        content="""[Verse 1]
Sequence running through the night
Strobe flashing black and white
The rhythm pounds into your head
Dancing with the living dead

[Chorus]
Total control is what we seek
The strong will dominate the weak
The beat commands you to obey
Surrender to the EBM way
Total control

[Verse 2]
Synthesizers pulsing hard
Every sense on full guard
Move your body, lose your mind
Leave your former self behind

[Chorus]
Total control is what we seek
The strong will dominate the weak""",
    ),
    # 100. Midwest Emo - 560 chars
    LyricsPreset(
        id="midwest_emo_home",
        name="Never Going Home (Midwest Emo)",
        genre="Midwest Emo",
        mood="Wistful",
        tags=["twinkly", "emotional", "nostalgic"],
        description="Twinkly midwest emo nostalgia",
        content="""[Verse 1]
Driving past my childhood home
Through the streets I used to roam
Everything looks so much smaller now
Changed so much, I don't know how

[Chorus]
Never going home again
Back to where it all began
The memories are all that's left
Of the places I know best
Never going home

[Verse 2]
Twinkly guitars play our song
Wondering where it all went wrong
The basement shows and first heartbreaks
Learning from our past mistakes

[Bridge]
Some things are better left behind
But still they linger in my mind

[Chorus]
Never going home again
Back to where it all began""",
    ),
]


def get_lyrics_by_genre(genre: str) -> List[LyricsPreset]:
    """Get all lyrics presets matching a genre."""
    genre_lower = genre.lower()
    return [p for p in LYRICS_PRESETS if p.genre.lower() == genre_lower]


def get_lyrics_by_mood(mood: str) -> List[LyricsPreset]:
    """Get all lyrics presets matching a mood."""
    mood_lower = mood.lower()
    return [p for p in LYRICS_PRESETS if p.mood.lower() == mood_lower]


def get_lyrics_for_model(model_id: str) -> List[LyricsPreset]:
    """Get lyrics presets that fit within a model's character limit."""
    if "music-1.5" in model_id or "music-01" in model_id:
        return [p for p in LYRICS_PRESETS if p.fits_music15]
    elif "ace-step" in model_id:
        return [p for p in LYRICS_PRESETS if p.fits_ace_step]
    return LYRICS_PRESETS


def get_all_genres() -> List[str]:
    """Get unique list of all genres."""
    return sorted(set(p.genre for p in LYRICS_PRESETS))


def get_all_moods() -> List[str]:
    """Get unique list of all moods."""
    return sorted(set(p.mood for p in LYRICS_PRESETS))
