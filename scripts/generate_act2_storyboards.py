#!/usr/bin/env python3
"""Generate Act 2 storyboard images using Gemini API."""

import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "storyboards" / "act2" / "panels"

# Style prefix for all panels
STYLE_PREFIX = """Storyboard panel, Pixar animation style, cinematic composition,
family adventure animation, professional animation production,
16:9 aspect ratio"""

# Character descriptions for consistency
CHARACTERS = {
    "gabe": "Late 30s father, rectangular glasses, short dark brown hair with gray temples, stubble, torn dirty black tuxedo (disheveled from survival)",
    "nina": "Late 30s mother, shoulder-length dark brown wavy hair, hazel-green eyes, ruined black cocktail dress, barefoot",
    "mia": "8-year-old girl, brown hair, big expressive eyes, determined expression, casual clothes",
    "leo": "5-year-old boy, blonde/light brown hair, dinosaur pajamas, round face, innocent, carrying snack backpack",
    "ruben": "Fairy godfather, wild gray Einstein-like hair, tired baggy blue-gray eyes, janitor coveralls, droopy iridescent purple-blue wings, uses mop as magic wand",
    "mcnattin": "Middle-aged detective, rumpled suit, tired weathered face, professional demeanor",
    "jenny": "15-year-old babysitter, blonde ponytail, nervous teen"
}

# All Act 2 panels organized by scene
ACT2_PANELS = [
    # Scene 11: House Morning (3 panels)
    {
        "filename": "scene-11-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, wide establishing shot,
suburban house exterior morning after,
multiple police cars in driveway, yellow caution tape,
morning golden sunlight, calm ironic contrast,
police officers near cars and on porch, official on phone,
kids bikes visible in yard, investigation underway,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-11-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, medium shot,
plain clothes detective on phone outdoors,
professional attire suit, notepad in hand, concerned expression,
badge visible, police activity blurred in background,
morning light, coordinating investigation,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-11-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, medium insert shot,
nosy neighbor in bathrobe getting newspaper,
coffee mug in hand, newspaper held but forgotten,
openly staring at police activity next door,
small dog at feet also looking, suburban curiosity,
comedy relief moment, morning light,
16:9 cinematic composition"""
    },

    # Scene 12: Jenny Interview (4 panels)
    {
        "filename": "scene-12-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, two-shot,
detective and teenage babysitter at dining table interview,
{CHARACTERS['mcnattin']}, {CHARACTERS['jenny']},
morning light through window, coffee cups on table, notepad visible,
family photos on walls, professional interview in domestic space,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-12-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
nervous teenage girl face recalling memory,
{CHARACTERS['jenny']}, eyes looking up remembering,
young face slightly stressed, fidgeting visible,
morning light on face, earnest expression,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-12-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
middle-aged detective face interest piqued,
weathered experienced face, eyes narrowing slightly,
pen paused mid-write, subtle forward lean,
professional poker face with visible interest,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-12-panel-04.png",
        "prompt": f"""{STYLE_PREFIX}, insert close-up,
detective notepad with handwriting,
worn notepad many pages used, messy handwriting,
key phrases visible: running late, arguing, hesitated to promise underlined,
pen underlining with emphasis,
16:9 cinematic composition"""
    },

    # Scene 13: Kids Breakfast (7 panels)
    {
        "filename": "scene-13-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, wide shot,
kitchen breakfast table with two children and social worker,
{CHARACTERS['leo']} surrounded by colorful cereal mess,
{CHARACTERS['mia']} more composed, social worker across table,
fluorescent morning light, domestic chaos,
detective visible in background doorway,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-13-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, close-up insert,
5-year-old boy face eating cereal messily,
colorful cereal on face and table, milk mustache,
completely content unbothered expression,
dinosaur pajamas visible, spoon overloaded,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-13-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
8-year-old girl face serious and intuitive,
{CHARACTERS['mia']}, big worried eyes,
more composed than her age should allow,
hair pulled back trying to be grown up,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-13-panel-04.png",
        "prompt": f"""{STYLE_PREFIX}, medium shot,
5-year-old boy demonstrating explosion with wild arm gestures,
{CHARACTERS['leo']} arms spread wide for explosion gesture,
cereal bowl being knocked over by elbow,
milk spreading across table, genuine childhood enthusiasm,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-13-panel-05.png",
        "prompt": f"""{STYLE_PREFIX}, medium shot,
overwhelmed social worker watching cereal spill,
kind but pained expression, professional facade slipping,
reaching for napkins, notepad forgotten,
kids at frame edges,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-13-panel-06.png",
        "prompt": f"""{STYLE_PREFIX}, two-shot,
two siblings at breakfast table telling story together,
{CHARACTERS['mia']} cleaning with paper towels but talking,
{CHARACTERS['leo']} with fresh cereal already eating again,
sibling teamwork visible, morning light on faces,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-13-panel-07.png",
        "prompt": f"""{STYLE_PREFIX}, medium to insert shot,
detective entering frame taking phone as evidence,
{CHARACTERS['mcnattin']} picking up smartphone carefully,
evidence bag visible, phone with faint blue glow,
kids watching with concern from table,
16:9 cinematic composition"""
    },

    # Scene 14: Cave Connection (5 panels)
    {
        "filename": "scene-14-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, wide shot,
Jurassic cave interior lit by daylight from entrance,
{CHARACTERS['gabe']} and {CHARACTERS['nina']} huddled together,
T-Rex shadow silhouette visible at cave entrance,
rough damp cave walls, exhausted body language,
parents formal wear destroyed and dirty,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-14-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, insert close-up,
smartphone screen frozen and glitched,
cracked screen, static lines rolling through,
faint blue glow at edges portal energy,
touch not responding, woman hands holding phone,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-14-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, extreme close-up,
phone battery indicator showing 65 percent,
green battery icon, time display frozen wrong,
ticking clock introduced, lifeline resource,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-14-panel-04.png",
        "prompt": f"""{STYLE_PREFIX}, medium shot,
disheveled mother holding phone thinking,
{CHARACTERS['nina']} hair wild makeup smeared,
concentration on face despite exhaustion,
phone reflecting faintly on face, husband watching in background,
cave interior setting,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-14-panel-05.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
desperate mother face calling into phone,
{CHARACTERS['nina']} tears forming in eyes,
phone held close to mouth, raw maternal desperation,
hope mixed with fear, every mother nightmare,
16:9 cinematic composition"""
    },

    # Scene 15: Police Car Kids (3 panels)
    {
        "filename": "scene-15-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, wide interior shot,
two children in police car back seat behind barrier,
{CHARACTERS['mia']} looking forward alert,
{CHARACTERS['leo']} looking at sister,
clear mesh barrier prominent, phone visible on passenger seat,
daylight through windows, isolated vulnerable,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-15-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, insert close-up,
smartphone on car passenger seat crackling,
phone in evidence bag partially open,
screen flickering faint blue glow,
static visible, barrier visible at frame edge,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-15-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, two-shot close-up,
two children faces reacting recognizing voice,
{CHARACTERS['mia']} eyes widening alert,
{CHARACTERS['leo']} confused then recognizing,
hope dawning on both faces, leaning toward barrier,
16:9 cinematic composition"""
    },

    # Scene 16: Cave Intercut (3 panels)
    {
        "filename": "scene-16-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, medium shot handheld,
desperate mother on knees calling into phone,
{CHARACTERS['nina']} hunched over phone like precious object,
tears on cheeks, voice cracking with emotion,
cave shadows around her, kneeling supplicant pose,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-16-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, close-up to medium pull back,
disheveled father face in cave darkness finding tunnel,
{CHARACTERS['gabe']} squinting at light,
tunnel opening revealed with distant daylight,
hope on face, rough cave walls,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-16-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, two-shot,
two parents quick decision moment in cave,
{CHARACTERS['nina']} still kneeling tear-streaked,
{CHARACTERS['gabe']} gesturing toward tunnel exit,
phone visible between them as priority,
tunnel entrance visible behind father,
16:9 cinematic composition"""
    },

    # Scene 17: Car Frustration (4 panels)
    {
        "filename": "scene-17-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, medium shot handheld,
two children pressing against car barrier screaming,
{CHARACTERS['mia']} hands on barrier desperate,
{CHARACTERS['leo']} face pressed to barrier,
tears forming on both faces, phone visible but untouchable,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-17-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, insert close-up,
police car barrier with small hands pressed against it,
child handprints on plexiglass,
phone visible beyond still crackling,
cruel physical separation metaphor,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-17-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
detective sliding into driver seat of police car,
{CHARACTERS['mcnattin']} getting in unaware,
keys in hand, professional demeanor,
kids commotion visible in rearview mirror ignored,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-17-panel-04.png",
        "prompt": f"""{STYLE_PREFIX}, wide interior shot,
police car interior detective front kids back defeated,
{CHARACTERS['mcnattin']} starting car focused on driving,
{CHARACTERS['mia']} slumping in back left,
{CHARACTERS['leo']} crying quietly back right,
phone on passenger seat glow diminishing,
16:9 cinematic composition"""
    },

    # Scene 18: Cave Tunnel (3 panels)
    {
        "filename": "scene-18-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, tracking medium shot,
two parents moving through narrow cave tunnel single file,
{CHARACTERS['nina']} leading with phone held like torch,
{CHARACTERS['gabe']} following close behind,
light visible ahead getting brighter,
ruined formal wear dragging, tight tunnel walls,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-18-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, insert close-up,
phone screen showing signal bars dropping,
signal bars going from 2 to 1 bar flickering,
static increasing on screen, battery showing 60 percent,
woman fingers gripping tightly,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-18-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, medium shot,
devastated mother paused in tunnel looking at phone,
{CHARACTERS['nina']} stopped phone screen mostly static,
{CHARACTERS['gabe']} behind reaching supportively,
tunnel exit golden light visible behind them,
transition from hope to determination,
16:9 cinematic composition"""
    },

    # Scene 19: Montage (6 panels)
    {
        "filename": "scene-19-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, multiple shots montage,
two parents exiting cave into blinding Jurassic jungle light,
{CHARACTERS['gabe']} and {CHARACTERS['nina']} emerging from cave,
squinting in light, hostile but beautiful jungle,
checking phone for signal, determination on faces,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-19-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, multiple shots montage,
two children in institutional settings being processed,
{CHARACTERS['mia']} and {CHARACTERS['leo']} in plastic chairs,
fluorescent lighting cold institutional,
kids look small against adult spaces,
{CHARACTERS['leo']} clutching snack backpack, holding hands,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-19-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, epic wide shot,
two tiny parent figures in massive Jurassic landscape,
{CHARACTERS['gabe']} and {CHARACTERS['nina']} small determined figures,
giant ferns cycads primitive trees, steam mist in air,
golden-green light filtering through, dangerous beauty,
distant dinosaur silhouette,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-19-panel-04.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
child snack backpack open showing colorful contents,
dinosaur design backpack, candy juice boxes snacks visible,
Sour Patch Kids chocolate visible, small child hands reaching,
sister visible in background waiting room,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-19-panel-05.png",
        "prompt": f"""{STYLE_PREFIX}, stunning wide shot,
epic Jurassic sunset with parent silhouettes on ridge,
gorgeous sunset oranges pinks purples,
prehistoric landscape silhouette,
{CHARACTERS['gabe']} and {CHARACTERS['nina']} as small figures against sky,
first stars appearing, primal beauty,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-19-panel-06.png",
        "prompt": f"""{STYLE_PREFIX}, wide shot,
police station exterior or interior at night,
{CHARACTERS['mia']} and {CHARACTERS['leo']} visible being settled,
tired expressions, city lights outside,
glimpse of janitor with mop watching in shadows,
contrast artificial light vs natural,
16:9 cinematic composition"""
    },

    # Scene 20: Police Station Ruben Reveal (11 panels)
    {
        "filename": "scene-20-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, wide establishing shot,
police station conference room with sleeping bags on floor,
{CHARACTERS['mia']} sitting on sleeping bag alert,
{CHARACTERS['leo']} lying down but not asleep,
fluorescent lights dimmed, clock showing late night,
snack backpack nearby, institutional but attempts at comfort,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-20-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, medium tracking shot,
detective leading two children into conference room,
{CHARACTERS['mcnattin']} gesturing to sleeping bags awkwardly kind,
{CHARACTERS['mia']} following skeptical, {CHARACTERS['leo']} dragging feet,
nighttime police station interior,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-20-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, medium shot,
mysterious janitor appearing in doorway with mop and bucket,
{CHARACTERS['ruben']} wild gray hair tired eyes,
janitor coveralls slightly too big, mop held oddly like wand,
something shimmering at back hidden wings,
kids looking up suspicious and curious,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-20-panel-04.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
fairy godfather face giving knowing wink,
{CHARACTERS['ruben']} tired eyes sparkling with secret,
exaggerated wink, slight smile, wild gray hair,
something slightly magical about features,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-20-panel-05.png",
        "prompt": f"""{STYLE_PREFIX}, two-shot expanding,
fairy godfather crouching to kid level explaining,
{CHARACTERS['ruben']} down at kid height,
{CHARACTERS['mia']} skeptical but listening,
{CHARACTERS['leo']} increasingly excited,
mop held meaningfully,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-20-panel-06.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
droopy iridescent fairy wings revealed,
purple-blue iridescent wings droopy slightly tattered,
glowing faintly, peeking from janitor coveralls,
kids reactions at frame edges amazed,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-20-panel-07.png",
        "prompt": f"""{STYLE_PREFIX}, two-shot,
two children faces pure wonder at fairy reveal,
{CHARACTERS['leo']} hands over mouth trying not to scream,
{CHARACTERS['mia']} eyes wide mouth open skepticism melting,
childhood belief activated,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-20-panel-08.png",
        "prompt": f"""{STYLE_PREFIX}, insert medium shot,
fairy godfather demonstrating weak magic with mop wand,
{CHARACTERS['ruben']} wielding mop tip glowing faintly,
dim uneven sparkles, pencil barely levitating wobbly,
kids watching impressed despite weakness,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-20-panel-09.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
mop propping door open as visual metaphor,
door propped open by mop, light through gap,
fairy godfather pointing explaining portal concept,
kids understanding dawning, doorstop metaphor,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-20-panel-10.png",
        "prompt": f"""{STYLE_PREFIX}, wide shot,
detective returning fairy quickly hiding wings,
{CHARACTERS['mcnattin']} in doorway suspicious but tired,
{CHARACTERS['ruben']} furiously mopping overacting innocent,
kids in sleeping bags eyes too wide overselling innocence,
comedy of almost caught,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-20-panel-11.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
two children settling in sleeping bags eyes open planning,
{CHARACTERS['mia']} in sleeping bag alert determined,
{CHARACTERS['leo']} excited clutching snack backpack,
fairy godfather subtle wave at door edge,
hope and plan established,
16:9 cinematic composition"""
    },

    # Scene 21: Jurassic Tree Emotional (8 panels)
    {
        "filename": "scene-21-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, wide establishing crane up shot,
massive prehistoric tree with two small parent figures on branch,
giant ancient tree dominating frame,
{CHARACTERS['gabe']} and {CHARACTERS['nina']} small on thick branch high up,
Jurassic night sky stars visible through canopy,
bioluminescent fungi subtle night light,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-21-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
ruined elegant heels being removed from blistered feet,
elegant destroyed shoes one heel broken,
blisters visible on feet, woman hands removing shoes,
dropping into darkness below,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-21-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, two-shot,
two exhausted parents settling on wide tree branch for night,
{CHARACTERS['nina']} leaning against trunk,
{CHARACTERS['gabe']} tuxedo jacket placed as cushion for wife,
intimate physical proximity, night sky through canopy gaps,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-21-panel-04.png",
        "prompt": f"""{STYLE_PREFIX}, close-up slow push,
mother face emotional confession beginning,
{CHARACTERS['nina']} makeup gone smeared hair wild,
vulnerable raw expression, eyes glistening,
moonlight on face, honest vulnerable moment,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-21-panel-05.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
mother fully crying releasing held back fear,
{CHARACTERS['nina']} tears streaming face crumpling,
hand to mouth trying to hold it in,
complete vulnerability mother deepest fear,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-21-panel-06.png",
        "prompt": f"""{STYLE_PREFIX}, wide shot,
beautiful Jurassic night sky through ancient trees,
prehistoric sky same stars different era,
giant tree silhouettes, moon full,
bioluminescence in forest below, timeless peace,
visual breathing room,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-21-panel-07.png",
        "prompt": f"""{STYLE_PREFIX}, two-shot,
husband holding wife on tree branch both fragile together,
{CHARACTERS['gabe']} arm around {CHARACTERS['nina']},
head on shoulder, unity against the night,
wedding rings catching moonlight,
branch solid beneath them,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-21-panel-08.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
phone screen battery indicator ticking down,
battery dropped to 50 percent from 65,
screen still frozen glitchy, time stamp wrong,
reminder of stakes urgency,
16:9 cinematic composition"""
    },

    # Scene 22: Station Escape Comedy (14 panels)
    {
        "filename": "scene-22-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, tracking medium shot,
fairy godfather pushing squeaky mop bucket down dark hallway,
{CHARACTERS['ruben']} wincing at every squeak,
dim hallway lighting, office doors visible,
comedic stealth attempt failing,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-22-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
mop wand aimed at squeaky wheel magic misfire,
mop tip glowing faintly purple-blue weak sparkles,
wheel disappearing entirely instead of oiling,
bucket now tilting three wheels,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-22-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, wide shot,
fairy godfather trying to magically move office chair,
{CHARACTERS['ruben']} concentrating straining,
rolling office chair with dim purple sparkles barely moving,
conference room door visible in background,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-22-panel-04.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
magic blast accidentally hitting ceiling creating hole,
mop tip glowing too bright, purple-blue energy blast,
ceiling tile exploding upward, debris falling,
overcompensated magic,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-22-panel-05.png",
        "prompt": f"""{STYLE_PREFIX}, POV shot,
view through conference room window at kids pretending sleep,
kids visible in sleeping bags eyes slightly open,
locked door handle visible, snack backpack ready,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-22-panel-06.png",
        "prompt": f"""{STYLE_PREFIX}, medium shot,
two children waking up hearing commotion,
{CHARACTERS['mia']} sitting up alert,
{CHARACTERS['leo']} already up excited with backpack,
shadows through door window,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-22-panel-07.png",
        "prompt": f"""{STYLE_PREFIX}, wide shot,
two children using rolling chair as battering ram on door,
{CHARACTERS['mia']} pushing rolling chair,
{CHARACTERS['leo']} helping push, door beginning to give,
conference table pushed aside, kid ingenuity,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-22-panel-08.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
detective sleeping at desk head on arms,
{CHARACTERS['mcnattin']} slumped asleep snoring,
empty coffee cup papers scattered,
completely oblivious to chaos,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-22-panel-09.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
evidence cabinet with phone visible inside locked,
metal evidence cabinet mesh door,
phone visible through mesh slightly glowing,
lock prominent, keys on detective desk visible,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-22-panel-10.png",
        "prompt": f"""{STYLE_PREFIX}, wide shot,
fairy godfather magic misfiring toward sleeping detective,
{CHARACTERS['ruben']} aiming mop at cabinet,
purple magic beam curving wrong direction,
{CHARACTERS['mcnattin']} beginning to stir,
kids horrified expressions,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-22-panel-11.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
detective frozen mid-yawn by fairy freeze spell,
{CHARACTERS['mcnattin']} frozen mid-expression yawn,
frost shimmer effect on him, eyes open not blinking,
one hand raised stretching, blue-white freeze effect,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-22-panel-12.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
child finger poking frozen detective face curious,
{CHARACTERS['leo']} small finger approaching frozen face,
frozen expression slight frost, fascinated expression at edge,
comedy testing if really frozen,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-22-panel-13.png",
        "prompt": f"""{STYLE_PREFIX}, medium tracking shot,
retrieving phone from evidence cabinet triumph,
keys removed from frozen detective belt,
{CHARACTERS['mia']} at cabinet getting phone still slightly glowing,
{CHARACTERS['ruben']} helping, relief and triumph on faces,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-22-panel-14.png",
        "prompt": f"""{STYLE_PREFIX}, wide shot,
group rushing to elevator escape achieved,
all three piling into elevator,
empty night shift station behind them,
elevator doors closing, relief as they escape,
16:9 cinematic composition"""
    },

    # Scene 23: Car Chase (8 panels)
    {
        "filename": "scene-23-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, wide tracking shot,
group bursting out of police station into parking lot,
{CHARACTERS['mia']} leading, {CHARACTERS['leo']} following close,
{CHARACTERS['ruben']} behind wings slightly visible forgot to hide,
police cars parked, night lighting,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-23-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
girl checking phone using it like compass navigation,
phone screen glowing signal visible,
direction indicator, determined grip,
following signal to portal,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-23-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, wide shot,
group piling into police car kids in driver area,
{CHARACTERS['ruben']} getting in passenger side,
{CHARACTERS['mia']} opening driver door on tiptoe,
{CHARACTERS['leo']} following excited, absurd setup,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-23-panel-04.png",
        "prompt": f"""{STYLE_PREFIX}, interior medium shot with shakes,
absurd image girl driving barely seeing over wheel,
{CHARACTERS['mia']} in driver seat straining to see,
{CHARACTERS['leo']} on her lap holding wheel with her,
{CHARACTERS['ruben']} passenger seat white-knuckled horrified,
seat pushed all forward,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-23-panel-05.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
mop wand touching car ignition magical glow starting car,
mop tip glowing purple-blue,
ignition keyhole sparking, dashboard lighting up,
fairy concentrated expression at edge,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-23-panel-06.png",
        "prompt": f"""{STYLE_PREFIX}, wide tracking shot,
comedy car chase police car racing through night streets,
stolen car weaving not smoothly,
pursuing police cars behind sirens,
kids steering badly visible through windshield,
near misses mailboxes trash cans,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-23-panel-07.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
phone screen signal bars increasing getting closer,
signal bars going up 2 to 3 bars,
screen less glitchy static clearing,
direction confirmed navigation success,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-23-panel-08.png",
        "prompt": f"""{STYLE_PREFIX}, medium interior shot,
car interior everyone listening parents voices through phone,
{CHARACTERS['mia']} driving but emotional tears forming,
{CHARACTERS['leo']} gasping wonder,
{CHARACTERS['ruben']} relieved, phone glowing brighter,
emotional payoff hearing parents,
16:9 cinematic composition"""
    },

    # Scene 24: Tree Wake (3 panels)
    {
        "filename": "scene-24-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
father face waking in Jurassic tree at dawn,
{CHARACTERS['gabe']} face dirty tired eyes opening,
dawn golden-pink light on face,
confusion turning to alertness recognition,
hearing something that doesn't belong,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-24-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, insert close-up slight shake,
phone in mother hands crackling to life with kids voices,
phone screen more active flickering,
static visible but clearing, sound coming through,
{CHARACTERS['nina']} hands gripping tight,
battery showing 40 percent lower now,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-24-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, two-shot,
both parents clutching phone tears joy dawn breaking behind,
{CHARACTERS['nina']} holding phone, {CHARACTERS['gabe']} leaning in,
dawn sky golden-pink behind through trees,
tears on both faces, hope renewed,
giant tree silhouette,
16:9 cinematic composition"""
    },

    # Scene 25: Portal Jump Climax (7 panels)
    {
        "filename": "scene-25-panel-01.png",
        "prompt": f"""{STYLE_PREFIX}, wide tracking then static shot,
police car coming to abrupt stop crashed into curb,
car front wheel on curb steam from engine,
kids visible inside, pursuing cars approaching behind,
sirens and lights, night isolated area near highway,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-25-panel-02.png",
        "prompt": f"""{STYLE_PREFIX}, medium tracking shot,
kids and fairy running from car phone guiding them,
{CHARACTERS['mia']} leading phone held out compass,
{CHARACTERS['leo']} running close determined,
{CHARACTERS['ruben']} behind wings now visible given up hiding,
abandoned industrial area, police lights behind,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-25-panel-03.png",
        "prompt": f"""{STYLE_PREFIX}, close-up handheld running,
girl face phone to ear running clear conversation with parents,
{CHARACTERS['mia']} determined face phone pressed to ear,
motion blur at edges tears and wind,
portal glow reflection in her eyes,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-25-panel-04.png",
        "prompt": f"""{STYLE_PREFIX}, close-up,
5-year-old boy excited grabbing phone proud announcement,
{CHARACTERS['leo']} excited face talking into phone,
huge inappropriate smile given situation,
sister trying to get phone back at edge,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-25-panel-05.png",
        "prompt": f"""{STYLE_PREFIX}, POV wide push shot,
TIME WARP PORTAL visible ahead bright blue swirling vortex,
bright blue portal color 0096FF, swirling clockwise,
electrical discharge at edges, smaller than before closing slowly,
floating at eye level, beautiful and terrifying,
night glow from center,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-25-panel-06.png",
        "prompt": f"""{STYLE_PREFIX}, insert shot,
girl hiding phone in bushes near portal must stay as doorstop,
phone being placed carefully in bushes,
still glowing, protected spot,
reluctant hands, fairy instructing at edge,
critical decision phone stays behind,
16:9 cinematic composition"""
    },
    {
        "filename": "scene-25-panel-07.png",
        "prompt": f"""{STYLE_PREFIX}, wide static to push shot,
THE JUMP into portal climax all three running leaping,
{CHARACTERS['mia']} leading the jump courageously,
{CHARACTERS['leo']} hand in hers trusting,
{CHARACTERS['ruben']} behind wings spread catching portal light,
bright blue portal swirling swallowing them,
silhouettes against blue glow, electrical discharge as they enter,
police lights arriving too late behind,
iconic hero shot Act 2 climax,
16:9 cinematic composition"""
    },
]


def generate_image(prompt: str, filename: str) -> bool:
    """Generate a single image using Gemini 2.0 Flash."""
    output_path = OUTPUT_DIR / filename

    # Skip if already exists
    if output_path.exists():
        print(f"  ⊘ Skipping (exists): {filename}")
        return True

    print(f"Generating: {filename}")
    print(f"  Prompt: {prompt[:100]}...")

    try:
        # Use Gemini 2.0 Flash with native image generation
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=f"Generate an image: {prompt}",
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

        # Extract and save the image from the response
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                image_data = part.inline_data.data
                with open(output_path, "wb") as f:
                    f.write(image_data)
                print(f"  ✓ Saved to {output_path}")
                return True

        print(f"  ✗ No image in response")
        return False

    except Exception as e:
        print(f"  ✗ Error: {e}")
        return False


def main():
    """Generate Act 2 storyboard panels."""
    print("=" * 60)
    print("Generating Act 2 Storyboard Panels")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Total panels: {len(ACT2_PANELS)}")
    print()

    # Check for API key
    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY environment variable not set")
        return 1

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    success_count = 0
    total = len(ACT2_PANELS)

    # Optional: specify scene range via command line args
    start_idx = 0
    end_idx = total
    if len(sys.argv) > 1:
        start_idx = int(sys.argv[1])
    if len(sys.argv) > 2:
        end_idx = int(sys.argv[2])

    panels_to_generate = ACT2_PANELS[start_idx:end_idx]

    for i, panel in enumerate(panels_to_generate, start_idx + 1):
        print(f"\n[{i}/{total}] ", end="")
        if generate_image(panel["prompt"], panel["filename"]):
            success_count += 1

        # Small delay between requests to avoid rate limiting
        if i < end_idx:
            time.sleep(2)

    print("\n" + "=" * 60)
    print(f"Complete: {success_count}/{len(panels_to_generate)} images generated")
    print("=" * 60)

    return 0 if success_count == len(panels_to_generate) else 1


if __name__ == "__main__":
    sys.exit(main())
