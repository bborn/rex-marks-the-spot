#!/usr/bin/env python3
"""
Regenerate Act 2 storyboard images in pencil sketch style.
Uses gemini-2.5-flash-preview-04-17 for image generation.
"""

import os
import sys
import time
from pathlib import Path

from google import genai
from google.genai import types

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Output directory - same as original to replace images
OUTPUT_DIR = Path(__file__).parent.parent / "docs" / "storyboards" / "act2" / "panels"

# Pencil sketch style prefix for all panels
SKETCH_STYLE = """Traditional animation storyboard sketch, rough pencil drawing style,
hand-drawn look with visible pencil strokes and construction lines,
loose gestural drawing, minimal shading with cross-hatching,
sketchy line work like Pixar pre-production storyboards,
professional storyboard artist style, not polished final art,
grayscale pencil on paper texture, 16:9 aspect ratio,"""

# Character descriptions for consistency
CHARACTERS = {
    "gabe": "Late 30s father, rectangular glasses, short dark brown hair with gray temples, stubble, torn dirty tuxedo (disheveled from survival)",
    "nina": "Late 30s mother, shoulder-length dark brown wavy hair, hazel-green eyes, ruined cocktail dress, barefoot",
    "mia": "8-year-old girl, brown hair in ponytail, big expressive eyes, determined expression",
    "leo": "5-year-old boy, blonde/light brown hair, dinosaur pajamas, round face, innocent, carrying snack backpack",
    "ruben": "Fairy godfather, wild gray Einstein-like hair, tired baggy eyes, janitor coveralls, droopy iridescent wings, uses mop as magic wand",
    "mcnattin": "Middle-aged detective, rumpled suit, tired weathered face, professional demeanor",
    "jenny": "15-year-old babysitter, blonde ponytail, nervous teen"
}

# All Act 2 panels with sketch-style prompts
ACT2_SKETCH_PANELS = [
    # Scene 11: House Morning (3 panels)
    {
        "filename": "scene-11-panel-01.png",
        "prompt": f"""{SKETCH_STYLE}
wide establishing shot, suburban house exterior morning after,
multiple police cars in driveway, yellow caution tape,
morning light, police officers near cars and on porch,
kids bikes visible in yard, investigation underway"""
    },
    {
        "filename": "scene-11-panel-02.png",
        "prompt": f"""{SKETCH_STYLE}
medium shot, plain clothes detective on phone outdoors,
professional attire suit, notepad in hand, concerned expression,
badge visible, police activity blurred in background,
morning light, coordinating investigation"""
    },
    {
        "filename": "scene-11-panel-03.png",
        "prompt": f"""{SKETCH_STYLE}
medium insert shot, nosy neighbor in bathrobe getting newspaper,
coffee mug in hand, newspaper held but forgotten,
openly staring at police activity next door,
small dog at feet also looking, suburban curiosity, comedy relief moment"""
    },

    # Scene 12: Jenny Interview (4 panels)
    {
        "filename": "scene-12-panel-01.png",
        "prompt": f"""{SKETCH_STYLE}
two-shot, detective and teenage babysitter at dining table interview,
{CHARACTERS['mcnattin']}, {CHARACTERS['jenny']},
morning light through window, coffee cups on table, notepad visible"""
    },
    {
        "filename": "scene-12-panel-02.png",
        "prompt": f"""{SKETCH_STYLE}
close-up, nervous teenage girl face recalling memory,
{CHARACTERS['jenny']}, eyes looking up remembering,
young face slightly stressed, fidgeting visible"""
    },
    {
        "filename": "scene-12-panel-03.png",
        "prompt": f"""{SKETCH_STYLE}
close-up, middle-aged detective face interest piqued,
weathered experienced face, eyes narrowing slightly,
pen paused mid-write, subtle forward lean"""
    },
    {
        "filename": "scene-12-panel-04.png",
        "prompt": f"""{SKETCH_STYLE}
insert close-up, detective notepad with handwriting,
worn notepad many pages used, messy handwriting,
key phrases visible: running late, arguing, hesitated to promise underlined"""
    },

    # Scene 13: Kids Breakfast (7 panels)
    {
        "filename": "scene-13-panel-01.png",
        "prompt": f"""{SKETCH_STYLE}
wide shot, kitchen breakfast table with two children and social worker,
{CHARACTERS['leo']} surrounded by colorful cereal mess,
{CHARACTERS['mia']} more composed, social worker across table,
detective visible in background doorway"""
    },
    {
        "filename": "scene-13-panel-02.png",
        "prompt": f"""{SKETCH_STYLE}
close-up insert, 5-year-old boy face eating cereal messily,
colorful cereal on face and table, milk mustache,
completely content unbothered expression,
dinosaur pajamas visible, spoon overloaded"""
    },
    {
        "filename": "scene-13-panel-03.png",
        "prompt": f"""{SKETCH_STYLE}
close-up, 8-year-old girl face serious and intuitive,
{CHARACTERS['mia']}, big worried eyes,
more composed than her age should allow"""
    },
    {
        "filename": "scene-13-panel-04.png",
        "prompt": f"""{SKETCH_STYLE}
medium shot, 5-year-old boy demonstrating explosion with wild arm gestures,
{CHARACTERS['leo']} arms spread wide for explosion gesture,
cereal bowl being knocked over by elbow,
milk spreading across table, genuine childhood enthusiasm"""
    },
    {
        "filename": "scene-13-panel-05.png",
        "prompt": f"""{SKETCH_STYLE}
medium shot, overwhelmed social worker watching cereal spill,
kind but pained expression, professional facade slipping,
reaching for napkins, notepad forgotten"""
    },
    {
        "filename": "scene-13-panel-06.png",
        "prompt": f"""{SKETCH_STYLE}
two-shot, two siblings at breakfast table telling story together,
{CHARACTERS['mia']} cleaning with paper towels but talking,
{CHARACTERS['leo']} with fresh cereal already eating again,
sibling teamwork visible"""
    },
    {
        "filename": "scene-13-panel-07.png",
        "prompt": f"""{SKETCH_STYLE}
medium to insert shot, detective entering frame taking phone as evidence,
{CHARACTERS['mcnattin']} picking up smartphone carefully,
evidence bag visible, phone with faint glow,
kids watching with concern from table"""
    },

    # Scene 14: Cave Connection (5 panels)
    {
        "filename": "scene-14-panel-01.png",
        "prompt": f"""{SKETCH_STYLE}
wide shot, Jurassic cave interior lit by daylight from entrance,
{CHARACTERS['gabe']} and {CHARACTERS['nina']} huddled together,
T-Rex shadow silhouette visible at cave entrance,
rough damp cave walls, exhausted body language"""
    },
    {
        "filename": "scene-14-panel-02.png",
        "prompt": f"""{SKETCH_STYLE}
insert close-up, smartphone screen frozen and glitched,
cracked screen, static lines rolling through,
faint glow at edges portal energy,
woman hands holding phone"""
    },
    {
        "filename": "scene-14-panel-03.png",
        "prompt": f"""{SKETCH_STYLE}
extreme close-up, phone battery indicator showing 65 percent,
battery icon, time display frozen wrong,
ticking clock introduced, lifeline resource"""
    },
    {
        "filename": "scene-14-panel-04.png",
        "prompt": f"""{SKETCH_STYLE}
medium shot, disheveled mother holding phone thinking,
{CHARACTERS['nina']} hair wild makeup smeared,
concentration on face despite exhaustion,
phone reflecting faintly on face, husband watching in background"""
    },
    {
        "filename": "scene-14-panel-05.png",
        "prompt": f"""{SKETCH_STYLE}
close-up, desperate mother face calling into phone,
{CHARACTERS['nina']} tears forming in eyes,
phone held close to mouth, raw maternal desperation"""
    },

    # Scene 15: Police Car Kids (3 panels)
    {
        "filename": "scene-15-panel-01.png",
        "prompt": f"""{SKETCH_STYLE}
wide interior shot, two children in police car back seat behind barrier,
{CHARACTERS['mia']} looking forward alert,
{CHARACTERS['leo']} looking at sister,
clear mesh barrier prominent, phone visible on passenger seat"""
    },
    {
        "filename": "scene-15-panel-02.png",
        "prompt": f"""{SKETCH_STYLE}
insert close-up, smartphone on car passenger seat crackling,
phone in evidence bag partially open,
screen flickering faint glow, static visible"""
    },
    {
        "filename": "scene-15-panel-03.png",
        "prompt": f"""{SKETCH_STYLE}
two-shot close-up, two children faces reacting recognizing voice,
{CHARACTERS['mia']} eyes widening alert,
{CHARACTERS['leo']} confused then recognizing,
hope dawning on both faces"""
    },

    # Scene 16: Cave Intercut (3 panels)
    {
        "filename": "scene-16-panel-01.png",
        "prompt": f"""{SKETCH_STYLE}
medium shot handheld, desperate mother on knees calling into phone,
{CHARACTERS['nina']} hunched over phone like precious object,
tears on cheeks, voice cracking with emotion,
cave shadows around her, kneeling supplicant pose"""
    },
    {
        "filename": "scene-16-panel-02.png",
        "prompt": f"""{SKETCH_STYLE}
close-up to medium pull back, disheveled father face in cave darkness finding tunnel,
{CHARACTERS['gabe']} squinting at light,
tunnel opening revealed with distant daylight,
hope on face, rough cave walls"""
    },
    {
        "filename": "scene-16-panel-03.png",
        "prompt": f"""{SKETCH_STYLE}
two-shot, two parents quick decision moment in cave,
{CHARACTERS['nina']} still kneeling tear-streaked,
{CHARACTERS['gabe']} gesturing toward tunnel exit,
phone visible between them as priority"""
    },

    # Scene 17: Car Frustration (4 panels)
    {
        "filename": "scene-17-panel-01.png",
        "prompt": f"""{SKETCH_STYLE}
medium shot handheld, two children pressing against car barrier screaming,
{CHARACTERS['mia']} hands on barrier desperate,
{CHARACTERS['leo']} face pressed to barrier,
tears forming on both faces, phone visible but untouchable"""
    },
    {
        "filename": "scene-17-panel-02.png",
        "prompt": f"""{SKETCH_STYLE}
insert close-up, police car barrier with small hands pressed against it,
child handprints on plexiglass,
phone visible beyond still crackling,
cruel physical separation metaphor"""
    },
    {
        "filename": "scene-17-panel-03.png",
        "prompt": f"""{SKETCH_STYLE}
insert shot, detective sliding into driver seat of police car,
{CHARACTERS['mcnattin']} getting in unaware,
keys in hand, professional demeanor"""
    },
    {
        "filename": "scene-17-panel-04.png",
        "prompt": f"""{SKETCH_STYLE}
wide interior shot, police car interior detective front kids back defeated,
{CHARACTERS['mcnattin']} starting car focused on driving,
{CHARACTERS['mia']} slumping in back left,
{CHARACTERS['leo']} crying quietly back right"""
    },

    # Scene 18: Cave Tunnel (3 panels)
    {
        "filename": "scene-18-panel-01.png",
        "prompt": f"""{SKETCH_STYLE}
tracking medium shot, two parents moving through narrow cave tunnel single file,
{CHARACTERS['nina']} leading with phone held like torch,
{CHARACTERS['gabe']} following close behind,
light visible ahead getting brighter"""
    },
    {
        "filename": "scene-18-panel-02.png",
        "prompt": f"""{SKETCH_STYLE}
insert close-up, phone screen showing signal bars dropping,
signal bars going from 2 to 1 bar flickering,
static increasing on screen, battery showing 60 percent"""
    },
    {
        "filename": "scene-18-panel-03.png",
        "prompt": f"""{SKETCH_STYLE}
medium shot, devastated mother paused in tunnel looking at phone,
{CHARACTERS['nina']} stopped phone screen mostly static,
{CHARACTERS['gabe']} behind reaching supportively,
tunnel exit golden light visible behind them"""
    },

    # Scene 19: Montage (6 panels)
    {
        "filename": "scene-19-panel-01.png",
        "prompt": f"""{SKETCH_STYLE}
montage shot, two parents exiting cave into blinding Jurassic jungle light,
{CHARACTERS['gabe']} and {CHARACTERS['nina']} emerging from cave,
squinting in light, hostile but beautiful jungle"""
    },
    {
        "filename": "scene-19-panel-02.png",
        "prompt": f"""{SKETCH_STYLE}
montage shot, two children in institutional settings being processed,
{CHARACTERS['mia']} and {CHARACTERS['leo']} in plastic chairs,
fluorescent lighting cold institutional,
kids look small against adult spaces"""
    },
    {
        "filename": "scene-19-panel-03.png",
        "prompt": f"""{SKETCH_STYLE}
epic wide shot, two tiny parent figures in massive Jurassic landscape,
{CHARACTERS['gabe']} and {CHARACTERS['nina']} small determined figures,
giant ferns cycads primitive trees, steam mist in air"""
    },
    {
        "filename": "scene-19-panel-04.png",
        "prompt": f"""{SKETCH_STYLE}
insert shot, child snack backpack open showing colorful contents,
dinosaur design backpack, candy juice boxes snacks visible,
small child hands reaching"""
    },
    {
        "filename": "scene-19-panel-05.png",
        "prompt": f"""{SKETCH_STYLE}
stunning wide shot, epic Jurassic sunset with parent silhouettes on ridge,
gorgeous sunset oranges pinks purples,
prehistoric landscape silhouette,
{CHARACTERS['gabe']} and {CHARACTERS['nina']} as small figures against sky"""
    },
    {
        "filename": "scene-19-panel-06.png",
        "prompt": f"""{SKETCH_STYLE}
wide shot, police station exterior or interior at night,
{CHARACTERS['mia']} and {CHARACTERS['leo']} visible being settled,
tired expressions, glimpse of janitor with mop watching in shadows"""
    },

    # Scene 20: Police Station Ruben Reveal (11 panels)
    {
        "filename": "scene-20-panel-01.png",
        "prompt": f"""{SKETCH_STYLE}
wide establishing shot, police station conference room with sleeping bags on floor,
{CHARACTERS['mia']} sitting on sleeping bag alert,
{CHARACTERS['leo']} lying down but not asleep,
snack backpack nearby"""
    },
    {
        "filename": "scene-20-panel-02.png",
        "prompt": f"""{SKETCH_STYLE}
medium tracking shot, detective leading two children into conference room,
{CHARACTERS['mcnattin']} gesturing to sleeping bags awkwardly kind,
{CHARACTERS['mia']} following skeptical, {CHARACTERS['leo']} dragging feet"""
    },
    {
        "filename": "scene-20-panel-03.png",
        "prompt": f"""{SKETCH_STYLE}
medium shot, mysterious janitor appearing in doorway with mop and bucket,
{CHARACTERS['ruben']} wild gray hair tired eyes,
janitor coveralls slightly too big, mop held oddly like wand"""
    },
    {
        "filename": "scene-20-panel-04.png",
        "prompt": f"""{SKETCH_STYLE}
close-up, fairy godfather face giving knowing wink,
{CHARACTERS['ruben']} tired eyes sparkling with secret,
exaggerated wink, slight smile, wild gray hair"""
    },
    {
        "filename": "scene-20-panel-05.png",
        "prompt": f"""{SKETCH_STYLE}
two-shot expanding, fairy godfather crouching to kid level explaining,
{CHARACTERS['ruben']} down at kid height,
{CHARACTERS['mia']} skeptical but listening,
{CHARACTERS['leo']} increasingly excited"""
    },
    {
        "filename": "scene-20-panel-06.png",
        "prompt": f"""{SKETCH_STYLE}
close-up, droopy iridescent fairy wings revealed,
purple-blue iridescent wings droopy slightly tattered,
glowing faintly, peeking from janitor coveralls"""
    },
    {
        "filename": "scene-20-panel-07.png",
        "prompt": f"""{SKETCH_STYLE}
two-shot, two children faces pure wonder at fairy reveal,
{CHARACTERS['leo']} hands over mouth trying not to scream,
{CHARACTERS['mia']} eyes wide mouth open skepticism melting"""
    },
    {
        "filename": "scene-20-panel-08.png",
        "prompt": f"""{SKETCH_STYLE}
insert medium shot, fairy godfather demonstrating weak magic with mop wand,
{CHARACTERS['ruben']} wielding mop tip glowing faintly,
dim uneven sparkles, pencil barely levitating wobbly"""
    },
    {
        "filename": "scene-20-panel-09.png",
        "prompt": f"""{SKETCH_STYLE}
insert shot, mop propping door open as visual metaphor,
door propped open by mop, light through gap,
fairy godfather pointing explaining portal concept"""
    },
    {
        "filename": "scene-20-panel-10.png",
        "prompt": f"""{SKETCH_STYLE}
wide shot, detective returning fairy quickly hiding wings,
{CHARACTERS['mcnattin']} in doorway suspicious but tired,
{CHARACTERS['ruben']} furiously mopping overacting innocent"""
    },
    {
        "filename": "scene-20-panel-11.png",
        "prompt": f"""{SKETCH_STYLE}
close-up, two children settling in sleeping bags eyes open planning,
{CHARACTERS['mia']} in sleeping bag alert determined,
{CHARACTERS['leo']} excited clutching snack backpack"""
    },

    # Scene 21: Jurassic Tree Emotional (8 panels)
    {
        "filename": "scene-21-panel-01.png",
        "prompt": f"""{SKETCH_STYLE}
wide establishing crane up shot, massive prehistoric tree with two small parent figures on branch,
giant ancient tree dominating frame,
{CHARACTERS['gabe']} and {CHARACTERS['nina']} small on thick branch high up,
Jurassic night sky stars visible through canopy"""
    },
    {
        "filename": "scene-21-panel-02.png",
        "prompt": f"""{SKETCH_STYLE}
insert shot, ruined elegant heels being removed from blistered feet,
elegant destroyed shoes one heel broken,
blisters visible on feet, woman hands removing shoes"""
    },
    {
        "filename": "scene-21-panel-03.png",
        "prompt": f"""{SKETCH_STYLE}
two-shot, two exhausted parents settling on wide tree branch for night,
{CHARACTERS['nina']} leaning against trunk,
{CHARACTERS['gabe']} tuxedo jacket placed as cushion for wife"""
    },
    {
        "filename": "scene-21-panel-04.png",
        "prompt": f"""{SKETCH_STYLE}
close-up slow push, mother face emotional confession beginning,
{CHARACTERS['nina']} makeup gone smeared hair wild,
vulnerable raw expression, eyes glistening"""
    },
    {
        "filename": "scene-21-panel-05.png",
        "prompt": f"""{SKETCH_STYLE}
close-up, mother fully crying releasing held back fear,
{CHARACTERS['nina']} tears streaming face crumpling,
hand to mouth trying to hold it in"""
    },
    {
        "filename": "scene-21-panel-06.png",
        "prompt": f"""{SKETCH_STYLE}
wide shot, beautiful Jurassic night sky through ancient trees,
prehistoric sky same stars different era,
giant tree silhouettes, moon full"""
    },
    {
        "filename": "scene-21-panel-07.png",
        "prompt": f"""{SKETCH_STYLE}
two-shot, husband holding wife on tree branch both fragile together,
{CHARACTERS['gabe']} arm around {CHARACTERS['nina']},
head on shoulder, unity against the night"""
    },
    {
        "filename": "scene-21-panel-08.png",
        "prompt": f"""{SKETCH_STYLE}
insert shot, phone screen battery indicator ticking down,
battery dropped to 50 percent from 65,
screen still frozen glitchy, time stamp wrong"""
    },

    # Scene 22: Station Escape Comedy (14 panels)
    {
        "filename": "scene-22-panel-01.png",
        "prompt": f"""{SKETCH_STYLE}
tracking medium shot, fairy godfather pushing squeaky mop bucket down dark hallway,
{CHARACTERS['ruben']} wincing at every squeak,
dim hallway lighting, office doors visible"""
    },
    {
        "filename": "scene-22-panel-02.png",
        "prompt": f"""{SKETCH_STYLE}
insert shot, mop wand aimed at squeaky wheel magic misfire,
mop tip glowing faintly purple-blue weak sparkles,
wheel disappearing entirely instead of oiling"""
    },
    {
        "filename": "scene-22-panel-03.png",
        "prompt": f"""{SKETCH_STYLE}
wide shot, fairy godfather trying to magically move office chair,
{CHARACTERS['ruben']} concentrating straining,
rolling office chair with dim purple sparkles barely moving"""
    },
    {
        "filename": "scene-22-panel-04.png",
        "prompt": f"""{SKETCH_STYLE}
insert shot, magic blast accidentally hitting ceiling creating hole,
mop tip glowing too bright, purple-blue energy blast,
ceiling tile exploding upward, debris falling"""
    },
    {
        "filename": "scene-22-panel-05.png",
        "prompt": f"""{SKETCH_STYLE}
POV shot, view through conference room window at kids pretending sleep,
kids visible in sleeping bags eyes slightly open,
locked door handle visible, snack backpack ready"""
    },
    {
        "filename": "scene-22-panel-06.png",
        "prompt": f"""{SKETCH_STYLE}
medium shot, two children waking up hearing commotion,
{CHARACTERS['mia']} sitting up alert,
{CHARACTERS['leo']} already up excited with backpack"""
    },
    {
        "filename": "scene-22-panel-07.png",
        "prompt": f"""{SKETCH_STYLE}
wide shot, two children using rolling chair as battering ram on door,
{CHARACTERS['mia']} pushing rolling chair,
{CHARACTERS['leo']} helping push, door beginning to give"""
    },
    {
        "filename": "scene-22-panel-08.png",
        "prompt": f"""{SKETCH_STYLE}
close-up, detective sleeping at desk head on arms,
{CHARACTERS['mcnattin']} slumped asleep snoring,
empty coffee cup papers scattered"""
    },
    {
        "filename": "scene-22-panel-09.png",
        "prompt": f"""{SKETCH_STYLE}
insert shot, evidence cabinet with phone visible inside locked,
metal evidence cabinet mesh door,
phone visible through mesh slightly glowing"""
    },
    {
        "filename": "scene-22-panel-10.png",
        "prompt": f"""{SKETCH_STYLE}
wide shot, fairy godfather magic misfiring toward sleeping detective,
{CHARACTERS['ruben']} aiming mop at cabinet,
purple magic beam curving wrong direction"""
    },
    {
        "filename": "scene-22-panel-11.png",
        "prompt": f"""{SKETCH_STYLE}
close-up, detective frozen mid-yawn by fairy freeze spell,
{CHARACTERS['mcnattin']} frozen mid-expression yawn,
frost shimmer effect on him, eyes open not blinking"""
    },
    {
        "filename": "scene-22-panel-12.png",
        "prompt": f"""{SKETCH_STYLE}
insert shot, child finger poking frozen detective face curious,
{CHARACTERS['leo']} small finger approaching frozen face,
frozen expression slight frost, fascinated expression"""
    },
    {
        "filename": "scene-22-panel-13.png",
        "prompt": f"""{SKETCH_STYLE}
medium tracking shot, retrieving phone from evidence cabinet triumph,
keys removed from frozen detective belt,
{CHARACTERS['mia']} at cabinet getting phone still slightly glowing"""
    },
    {
        "filename": "scene-22-panel-14.png",
        "prompt": f"""{SKETCH_STYLE}
wide shot, group rushing to elevator escape achieved,
all three piling into elevator,
empty night shift station behind them"""
    },

    # Scene 23: Car Chase (8 panels)
    {
        "filename": "scene-23-panel-01.png",
        "prompt": f"""{SKETCH_STYLE}
wide tracking shot, group bursting out of police station into parking lot,
{CHARACTERS['mia']} leading, {CHARACTERS['leo']} following close,
{CHARACTERS['ruben']} behind wings slightly visible"""
    },
    {
        "filename": "scene-23-panel-02.png",
        "prompt": f"""{SKETCH_STYLE}
insert shot, girl checking phone using it like compass navigation,
phone screen glowing signal visible,
direction indicator, determined grip"""
    },
    {
        "filename": "scene-23-panel-03.png",
        "prompt": f"""{SKETCH_STYLE}
wide shot, group piling into police car kids in driver area,
{CHARACTERS['ruben']} getting in passenger side,
{CHARACTERS['mia']} opening driver door on tiptoe"""
    },
    {
        "filename": "scene-23-panel-04.png",
        "prompt": f"""{SKETCH_STYLE}
interior medium shot with shakes, absurd image girl driving barely seeing over wheel,
{CHARACTERS['mia']} in driver seat straining to see,
{CHARACTERS['leo']} on her lap holding wheel with her,
{CHARACTERS['ruben']} passenger seat white-knuckled horrified"""
    },
    {
        "filename": "scene-23-panel-05.png",
        "prompt": f"""{SKETCH_STYLE}
insert shot, mop wand touching car ignition magical glow starting car,
mop tip glowing purple-blue,
ignition keyhole sparking, dashboard lighting up"""
    },
    {
        "filename": "scene-23-panel-06.png",
        "prompt": f"""{SKETCH_STYLE}
wide tracking shot, comedy car chase police car racing through night streets,
stolen car weaving not smoothly,
pursuing police cars behind sirens"""
    },
    {
        "filename": "scene-23-panel-07.png",
        "prompt": f"""{SKETCH_STYLE}
insert shot, phone screen signal bars increasing getting closer,
signal bars going up 2 to 3 bars,
screen less glitchy static clearing"""
    },
    {
        "filename": "scene-23-panel-08.png",
        "prompt": f"""{SKETCH_STYLE}
medium interior shot, car interior everyone listening parents voices through phone,
{CHARACTERS['mia']} driving but emotional tears forming,
{CHARACTERS['leo']} gasping wonder,
{CHARACTERS['ruben']} relieved, phone glowing brighter"""
    },

    # Scene 24: Tree Wake (3 panels)
    {
        "filename": "scene-24-panel-01.png",
        "prompt": f"""{SKETCH_STYLE}
close-up, father face waking in Jurassic tree at dawn,
{CHARACTERS['gabe']} face dirty tired eyes opening,
dawn golden-pink light on face"""
    },
    {
        "filename": "scene-24-panel-02.png",
        "prompt": f"""{SKETCH_STYLE}
insert close-up slight shake, phone in mother hands crackling to life with kids voices,
phone screen more active flickering,
static visible but clearing, sound coming through"""
    },
    {
        "filename": "scene-24-panel-03.png",
        "prompt": f"""{SKETCH_STYLE}
two-shot, both parents clutching phone tears joy dawn breaking behind,
{CHARACTERS['nina']} holding phone, {CHARACTERS['gabe']} leaning in,
dawn sky golden-pink behind through trees"""
    },

    # Scene 25: Portal Jump Climax (7 panels)
    {
        "filename": "scene-25-panel-01.png",
        "prompt": f"""{SKETCH_STYLE}
wide tracking then static shot, police car coming to abrupt stop crashed into curb,
car front wheel on curb steam from engine,
kids visible inside, pursuing cars approaching behind"""
    },
    {
        "filename": "scene-25-panel-02.png",
        "prompt": f"""{SKETCH_STYLE}
medium tracking shot, kids and fairy running from car phone guiding them,
{CHARACTERS['mia']} leading phone held out compass,
{CHARACTERS['leo']} running close determined,
{CHARACTERS['ruben']} behind wings now visible"""
    },
    {
        "filename": "scene-25-panel-03.png",
        "prompt": f"""{SKETCH_STYLE}
close-up handheld running, girl face phone to ear running clear conversation with parents,
{CHARACTERS['mia']} determined face phone pressed to ear,
motion blur at edges tears and wind"""
    },
    {
        "filename": "scene-25-panel-04.png",
        "prompt": f"""{SKETCH_STYLE}
close-up, 5-year-old boy excited grabbing phone proud announcement,
{CHARACTERS['leo']} excited face talking into phone,
huge inappropriate smile given situation"""
    },
    {
        "filename": "scene-25-panel-05.png",
        "prompt": f"""{SKETCH_STYLE}
POV wide push shot, TIME WARP PORTAL visible ahead,
bright swirling vortex, electrical discharge at edges,
smaller than before closing slowly,
floating at eye level, beautiful and terrifying"""
    },
    {
        "filename": "scene-25-panel-06.png",
        "prompt": f"""{SKETCH_STYLE}
insert shot, girl hiding phone in bushes near portal must stay as doorstop,
phone being placed carefully in bushes,
still glowing, protected spot,
reluctant hands"""
    },
    {
        "filename": "scene-25-panel-07.png",
        "prompt": f"""{SKETCH_STYLE}
wide static to push shot, THE JUMP into portal climax all three running leaping,
{CHARACTERS['mia']} leading the jump courageously,
{CHARACTERS['leo']} hand in hers trusting,
{CHARACTERS['ruben']} behind wings spread,
bright portal swirling swallowing them,
silhouettes against glow, iconic hero shot Act 2 climax"""
    },
]


def generate_image(prompt: str, filename: str, force: bool = False) -> bool:
    """Generate a single sketch image using Gemini 2.5 Flash Preview."""
    output_path = OUTPUT_DIR / filename

    # Skip if already exists and not forcing regeneration
    if output_path.exists() and not force:
        print(f"  ⊘ Skipping (exists): {filename}")
        return True

    print(f"Generating: {filename}")
    print(f"  Prompt: {prompt[:80]}...")

    try:
        # Use Gemini 2.5 Flash Preview with image generation
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-04-17",
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
    """Generate Act 2 storyboard panels in pencil sketch style."""
    print("=" * 60)
    print("Generating Act 2 Storyboard Panels - PENCIL SKETCH STYLE")
    print("Using model: gemini-2.5-flash-preview-04-17")
    print("=" * 60)
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Total panels: {len(ACT2_SKETCH_PANELS)}")
    print()

    # Check for API key
    if not os.environ.get("GEMINI_API_KEY"):
        print("ERROR: GEMINI_API_KEY environment variable not set")
        return 1

    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Parse command line arguments
    force = "--force" in sys.argv or "-f" in sys.argv

    # Filter out flags from arguments
    args = [a for a in sys.argv[1:] if not a.startswith("-")]

    start_idx = 0
    end_idx = len(ACT2_SKETCH_PANELS)

    if len(args) > 0:
        start_idx = int(args[0])
    if len(args) > 1:
        end_idx = int(args[1])

    panels_to_generate = ACT2_SKETCH_PANELS[start_idx:end_idx]

    if force:
        print("Force mode: regenerating all panels even if they exist")

    success_count = 0
    total = len(panels_to_generate)

    for i, panel in enumerate(panels_to_generate, start_idx + 1):
        print(f"\n[{i}/{len(ACT2_SKETCH_PANELS)}] ", end="")
        if generate_image(panel["prompt"], panel["filename"], force=force):
            success_count += 1

        # Small delay between requests to avoid rate limiting
        if i < end_idx:
            time.sleep(2)

    print("\n" + "=" * 60)
    print(f"Complete: {success_count}/{total} images generated")
    print("=" * 60)

    return 0 if success_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
