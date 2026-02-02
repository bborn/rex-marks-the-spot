#!/usr/bin/env python3
"""Generate Act 3 storyboard images using Gemini API - ROUGH SKETCH STYLE."""

import os
import sys
import time
import re
from pathlib import Path

from google import genai
from google.genai import types

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Output directory
OUTPUT_DIR = Path(__file__).parent.parent / "storyboards" / "act3" / "panels"

# Rough sketch style prefix for all panels
STYLE_PREFIX = """Rough storyboard sketch, simple black and white pencil drawing,
loose gestural lines, basic shapes for characters, professional animation thumbnail style,
focus on composition and camera angle, NOT detailed or polished,
quick sketch like Pixar story artist thumbnails, grayscale only,
stick figures or simple silhouettes acceptable, 16:9 aspect ratio."""

# Character reference for consistency
CHARACTER_REF = """
Characters (use simple shapes):
- Gabe (Father): Man with rectangular glasses, stubble, torn tuxedo
- Nina (Mother): Woman with shoulder-length wavy hair, ruined black dress
- Mia (Daughter, 8): Girl with brown hair, determined expression
- Leo (Son, 5): Small boy in dinosaur pajamas, round face
- Ruben (Fairy): Old man with wild gray hair, janitor coveralls, small wings, mop
- Jetplane (Creature): Small chicken-lizard hybrid, cute, iridescent
- T-Rex: Massive predatory dinosaur
"""

# All Act 3 panels organized by scene
ACT3_PANELS = [
    # ============= SCENE 26: Swamp Arrival & Meeting Jetplane =============
    {"filename": "scene-26-panel-01.png", "prompt": "Wide shot, low angle. Blue swirling portal energy dissipates as two kids (Mia, Leo) and old fairy (Ruben) materialize in prehistoric swamp. Dawn light, misty, lush vegetation. Portal center-left, characters emerging."},
    {"filename": "scene-26-panel-02.png", "prompt": "Medium shot, gentle pan. Mia and Leo look around in wonder and fear. Leo clutches backpack straps. Ruben steadies himself on mop. Exotic plants and steam in background."},
    {"filename": "scene-26-panel-03.png", "prompt": "Medium-close shot. Small cute chicken-lizard creature (Jetplane) pokes head out from behind foliage, curious. Tilts head chicken-like. Partially obscured by large leaf."},
    {"filename": "scene-26-panel-04.png", "prompt": "Over-the-shoulder shot from behind Leo. Leo spots the creature, gasps with delight. Push in slowly."},
    {"filename": "scene-26-panel-05.png", "prompt": "Close-up of Mia. She squints at the creature, unimpressed. Raised eyebrow, slight grimace."},
    {"filename": "scene-26-panel-06.png", "prompt": "Low angle medium shot. Jetplane cautiously emerges from foliage, moving in halting chicken-steps toward Leo. Shot from ground level."},
    {"filename": "scene-26-panel-07.png", "prompt": "Two-shot of Leo and Jetplane. Leo kneels down reaching out hand. Jetplane sniffs it tentatively then warms up."},
    {"filename": "scene-26-panel-08.png", "prompt": "Close-up of Ruben. He cocks head, considering the creature with surprised appreciation."},
    {"filename": "scene-26-panel-09.png", "prompt": "Close-up of Mia. She wrinkles nose, slightly repulsed but curious expression."},
    {"filename": "scene-26-panel-10.png", "prompt": "Medium shot, slight push in. Jetplane nuzzles Leo's hand. Leo looks triumphant, naming his new friend."},
    {"filename": "scene-26-panel-11.png", "prompt": "Two-shot of Mia and Ruben. They exchange a look of shared bemusement."},
    {"filename": "scene-26-panel-12.png", "prompt": "Wide establishing shot, slow pan right. Group walks toward crashed car. Reveals crushed vehicle with vines growing over it and LARGE NEST of branches on top."},
    {"filename": "scene-26-panel-13.png", "prompt": "Medium shot of Leo. He points at the destruction, shocked but not scared."},
    {"filename": "scene-26-panel-14.png", "prompt": "Close-up of Ruben. He examines damage, touches bent metal. Worried realization on face."},
    {"filename": "scene-26-panel-15.png", "prompt": "Low angle tracking shot. Mia climbs onto crumpled car hood to examine strange nest structure. Focused concentration."},
    {"filename": "scene-26-panel-16.png", "prompt": "Insert shot. Jetplane starts agitated barking/squawking, backing away nervously. Eyes darting skyward, body tense."},
    {"filename": "scene-26-panel-17.png", "prompt": "Close-up of Leo. He looks at Jetplane with concern."},
    {"filename": "scene-26-panel-18.png", "prompt": "POV shot from Mia. Looking down into nest at ENORMOUS EGG, mottled and leathery. Steam rises, eerie atmosphere."},
    {"filename": "scene-26-panel-19.png", "prompt": "Close-up of Mia. Expression shifts from curiosity to dawning horror. Eyes widening."},
    {"filename": "scene-26-panel-20.png", "prompt": "Medium shot from below. Ruben looks up at Mia, scans sky nervously. Urgent concern."},
    {"filename": "scene-26-panel-21.png", "prompt": "Wide EPIC reveal shot, fast whip pan upward. Massive PTERODACTYL descends from clouds, wingspan dominating frame, silhouetted against dawn sky."},
    {"filename": "scene-26-panel-22.png", "prompt": "Wide dynamic shot. Mia leaps off car hood as pterodactyl CRASHES into nest. Diagonal composition - Mia jumping left, pterodactyl landing right."},
    {"filename": "scene-26-panel-23.png", "prompt": "Low angle threatening shot. Pterodactyl settles on nest, spreads wings protectively, stares down at group. Primal fury."},
    {"filename": "scene-26-panel-24.png", "prompt": "Medium shot, slow track back. Everyone backs away instinctively, hands up. Jetplane cowers behind Leo's leg. Group huddled in fear."},
    {"filename": "scene-26-panel-25.png", "prompt": "Wide high angle shot. Second pterodactyl appears circling to land. Two full creatures in frame."},
    {"filename": "scene-26-panel-26.png", "prompt": "Medium shot, quick pan. Jetplane darts toward tree line, turns back and barks urgently at group, wanting them to follow."},
    {"filename": "scene-26-panel-27.png", "prompt": "Tracking shot, steadicam following group. They turn and RUN following Jetplane into dense forest. Male pterodactyl swoops after them. Low camera racing through ferns."},
    {"filename": "scene-26-panel-28.png", "prompt": "Wide shot. Group disappears into dense canopy. Pterodactyl pulls up, unable to follow through thick vegetation."},
    {"filename": "scene-26-panel-29.png", "prompt": "Medium shot. Everyone stops, bent over gasping for breath. Jetplane pants happily, proud of himself. Relief and gratitude."},
    {"filename": "scene-26-panel-30.png", "prompt": "Close two-shot, gentle push in. Leo kneels and pets Jetplane who purrs contentedly. Warm lighting through canopy, intimate bonding moment."},
    {"filename": "scene-26-panel-31.png", "prompt": "Medium shot of Mia. She looks around at unfamiliar jungle. Pragmatic concern expression."},
    {"filename": "scene-26-panel-32.png", "prompt": "Insert shot. Jetplane's tongue lolls, clearly dehydrated from running."},
    {"filename": "scene-26-panel-33.png", "prompt": "Medium shot of Leo. He rummages in backpack, pulls out chocolate milk carton. Proud solution expression."},
    {"filename": "scene-26-panel-34.png", "prompt": "Close-up of Mia. She recoils in disgust. Big sister disdain expression."},
    {"filename": "scene-26-panel-35.png", "prompt": "Close-up of Leo. He unscrews cap, sniffs, RECOILS from spoiled smell but recovers. Defiant, hiding disgust."},
    {"filename": "scene-26-panel-36.png", "prompt": "Medium shot. Leo offers spoiled milk to Jetplane who tentatively laps at it then goes CRAZY for it, lapping greedily at curdled chunks. Gross-out comedy."},
    {"filename": "scene-26-panel-37.png", "prompt": "Two-shot of Mia and Ruben. They react with matching disgust expressions."},
    {"filename": "scene-26-panel-38.png", "prompt": "Insert shot. Jetplane sniffs at Leo's backpack, clearly wanting more."},
    {"filename": "scene-26-panel-39.png", "prompt": "Medium shot. Leo offers apple. Jetplane takes tiny bite then nearly vomits, coughing fit. Comedy beat."},
    {"filename": "scene-26-panel-40.png", "prompt": "Close-up, push in. Leo pulls out bag of sour patch kids, offers a blue one to Jetplane."},
    {"filename": "scene-26-panel-41.png", "prompt": "Wide shot with dynamic subject. Jetplane goes INSANE with delight, bouncing around, gargle-chirping happily. Pure sugar-rush joy."},
    {"filename": "scene-26-panel-42.png", "prompt": "Medium shot of Ruben. He watches Jetplane with growing concern. Wary expression."},
    {"filename": "scene-26-panel-43.png", "prompt": "Two-shot of Leo and Jetplane. Leo puts away candy, speaks to Jetplane. Hopeful, trusting expression."},
    {"filename": "scene-26-panel-44.png", "prompt": "Close-up of Jetplane. He purrs contentedly, rubs against Leo's leg. Gross gargling chicken sound."},
    {"filename": "scene-26-panel-45.png", "prompt": "Medium shot of Leo. He tries to communicate, speaking slowly and loudly. Kid logic comedy."},
    {"filename": "scene-26-panel-46.png", "prompt": "Close-up of Mia. She rolls her eyes at Leo's attempt."},
    {"filename": "scene-26-panel-47.png", "prompt": "Medium shot tracking Jetplane. He suddenly stiffens, sniffs air with purpose. Trots off in specific direction, looks back expectantly. Intelligent, purposeful."},
    {"filename": "scene-26-panel-48.png", "prompt": "Wide shot, characters moving away. Leo excitedly follows Jetplane, pulling Mia and Ruben along. Group follows into misty jungle."},

    # ============= SCENE 27: Colored Farts Signal Discovery =============
    {"filename": "scene-27-panel-01.png", "prompt": "Wide establishing shot. Group walks single file along narrow jungle path. Order: Ruben front, Mia, Leo, Jetplane rear. Dense ferns on either side, light shafts through canopy."},
    {"filename": "scene-27-panel-02.png", "prompt": "Close-up of Mia. Her face scrunches up in disgust, covers nose. Genuine revulsion."},
    {"filename": "scene-27-panel-03.png", "prompt": "Close-up of Leo. He turns, defensive. Innocent confusion expression."},
    {"filename": "scene-27-panel-04.png", "prompt": "Two-shot. Mia points at Leo accusingly. Classic sibling blame dynamic."},
    {"filename": "scene-27-panel-05.png", "prompt": "Close-up of Mia. She squints suspiciously. Big sister 'I know it was you' look."},
    {"filename": "scene-27-panel-06.png", "prompt": "Close-up of Leo. He crosses arms. Offended innocence expression."},
    {"filename": "scene-27-panel-07.png", "prompt": "Medium shot, Ruben foreground, kids arguing background. Ruben turns back, sees something off-screen, tries to interrupt."},
    {"filename": "scene-27-panel-08.png", "prompt": "Two-shot. Kids ignore Ruben, continue squabbling. Overlapping argument chaos."},
    {"filename": "scene-27-panel-09.png", "prompt": "Wide shot from behind group. THE REVEAL - Jetplane lets loose LOUD VISIBLE FART. Plume of vibrant BLUE smoke rises from hindquarters against green jungle."},
    {"filename": "scene-27-panel-10.png", "prompt": "Wide shot. Everyone turns around simultaneously to look at Jetplane. Universal shock expressions."},
    {"filename": "scene-27-panel-11.png", "prompt": "Wide shot, tilt up. Blue plume rises majestically above tree line, dissipating slowly into sky. Vertical composition."},
    {"filename": "scene-27-panel-12.png", "prompt": "Close-up of Leo. His face breaks into amazed grin. Pure childlike wonder at gross/amazing thing."},
    {"filename": "scene-27-panel-13.png", "prompt": "Close-up of Mia. Disgust replaced by reluctant fascination. Processing the impossible."},
    {"filename": "scene-27-panel-14.png", "prompt": "Close-up of Leo. He smirks at his sister. Smug satisfaction - vindicated."},
    {"filename": "scene-27-panel-15.png", "prompt": "Close-up of Mia. She imitates Leo in mocking tone, nose pinched. Classic sibling mockery."},
    {"filename": "scene-27-panel-16.png", "prompt": "Medium shot of Ruben. He stares up at dissipating plume, gears turning in head. Thoughtful realization dawning."},
    {"filename": "scene-27-panel-17.png", "prompt": "Two-shot of kids. They look up, annoyed at being told to look at more farts. Exasperation."},
    {"filename": "scene-27-panel-18.png", "prompt": "Medium shot of Ruben, slight push in. He looks from fading plume to Leo. Building excitement."},
    {"filename": "scene-27-panel-19.png", "prompt": "Close-up of Leo. He counts on fingers, remembering colors he fed Jetplane."},
    {"filename": "scene-27-panel-20.png", "prompt": "Wide shot. Jetplane farts again. This time vibrant RED plume rises. Different color, same dynamics."},
    {"filename": "scene-27-panel-21.png", "prompt": "Medium shot of Mia. She unpinches nose, points at rising plumes excitedly. Eureka moment."},
    {"filename": "scene-27-panel-22.png", "prompt": "Wide overhead crane shot. Group looks up as third BLUE plume rises to join others, creating visible trail pattern in sky."},
    {"filename": "scene-27-panel-23.png", "prompt": "Close-up of Jetplane. He puffs up proudly, pleased with himself."},
    {"filename": "scene-27-panel-24.png", "prompt": "Two-shot. Leo pats Jetplane affectionately. Proud of his pet's unique talent."},
    {"filename": "scene-27-panel-25.png", "prompt": "Close-up of Mia. Still somewhat disgusted but can't argue with results. Reluctant acceptance."},
    {"filename": "scene-27-panel-26.png", "prompt": "Close-up of Leo. He puts protective arm around Jetplane. Defensive of his friend."},
    {"filename": "scene-27-panel-27.png", "prompt": "Medium shot of Ruben, push in. He points excitedly from Jetplane to sky. Excited revelation."},
    {"filename": "scene-27-panel-28.png", "prompt": "Close-up of Leo. His eyes widen with understanding. Dawn of realization."},
    {"filename": "scene-27-panel-29.png", "prompt": "Medium shot of Ruben. He nods enthusiastically. Triumphant expression."},
    {"filename": "scene-27-panel-30.png", "prompt": "Close-up of Leo. He completes the thought about finding parents. Excitement, hope."},
    {"filename": "scene-27-panel-31.png", "prompt": "Close-up of Mia. She's still confused about the plan."},
    {"filename": "scene-27-panel-32.png", "prompt": "Two-shot of Leo and Mia. Leo turns to sister with patient explanation."},
    {"filename": "scene-27-panel-33.png", "prompt": "Same two-shot. Logic chain continues between siblings."},
    {"filename": "scene-27-panel-34.png", "prompt": "Same two-shot. Mia starts to understand the logic."},
    {"filename": "scene-27-panel-35.png", "prompt": "Same two-shot. Leo gestures to Jetplane proudly."},
    {"filename": "scene-27-panel-36.png", "prompt": "Close-up of Mia. She processes the plan - a trail of farts. Disbelief expression."},
    {"filename": "scene-27-panel-37.png", "prompt": "Insert shot of Jetplane. He tilts head, makes questioning sound. Even he's unsure about this plan."},
    {"filename": "scene-27-panel-38.png", "prompt": "Close-up of Ruben. He shrugs with 'what have we got to lose' expression."},
    {"filename": "scene-27-panel-39.png", "prompt": "Medium shot. Leo gets another candy from bag, offers to Jetplane."},
    {"filename": "scene-27-panel-40.png", "prompt": "Medium shot of Mia. She looks around at dangerous jungle. Worried, vigilant."},
    {"filename": "scene-27-panel-41.png", "prompt": "Close-up of Ruben. He nods, checking surroundings."},
    {"filename": "scene-27-panel-42.png", "prompt": "Medium shot of Mia. She turns to Ruben hopefully, asking about carriage/pumpkin."},
    {"filename": "scene-27-panel-43.png", "prompt": "Close-up of Ruben. He looks baffled at pumpkin suggestion. Complete confusion."},
    {"filename": "scene-27-panel-44.png", "prompt": "Close-up of Mia. She waves hand dismissively. Frustrated improvisation."},
    {"filename": "scene-27-panel-45.png", "prompt": "Wide shot, tracking group moving left to right. Jetplane farting again, colored plumes rising behind them. Group continues with renewed purpose, trail marking their path."},

    # ============= SCENE 28-29: Parents See Signal & Follow =============
    {"filename": "scene-28-panel-01.png", "prompt": "Wide establishing shot, slow push in. Parents sit on huge vine-covered branch of massive prehistoric tree. Morning mist below. Epic scale - tiny humans on massive tree."},
    {"filename": "scene-28-panel-02.png", "prompt": "Close-up of Gabe. He stares at nothing, face heavy with regret and self-blame. Despair."},
    {"filename": "scene-28-panel-03.png", "prompt": "Close-up of Nina. She looks at him sharply, challenging his framing."},
    {"filename": "scene-28-panel-04.png", "prompt": "Medium shot of Gabe. He gestures helplessly. Grasping for control that doesn't exist."},
    {"filename": "scene-28-panel-05.png", "prompt": "Close-up of Nina. She holds up frozen phone. Exasperated patience."},
    {"filename": "scene-28-panel-06.png", "prompt": "Close-up of Gabe. His jaw tightens. Frustrated, powerless."},
    {"filename": "scene-28-panel-07.png", "prompt": "Close-up of Nina. She doesn't follow his logic. Confusion."},
    {"filename": "scene-28-panel-08.png", "prompt": "Medium shot of Gabe, slight push in. He turns to face her fully, explaining dark logic. Conviction born of fear."},
    {"filename": "scene-28-panel-09.png", "prompt": "Close-up of Nina. Her face shows horror at suggestion. Disbelief."},
    {"filename": "scene-28-panel-10.png", "prompt": "Close-up of Gabe. He looks away, voice quiet. Resigned acceptance."},
    {"filename": "scene-28-panel-11.png", "prompt": "Close-up of Nina. She grabs his arm, forcing him to look at her. Fierce maternal instinct."},
    {"filename": "scene-28-panel-12.png", "prompt": "Medium shot of Gabe. He gestures at vast jungle. Despair, self-recrimination. Father's failure fear."},
    {"filename": "scene-28-panel-13.png", "prompt": "Wide shot, track with movement. Nina gets up abruptly, moves to stand against tree trunk. Can't accept defeat."},
    {"filename": "scene-28-panel-14.png", "prompt": "Medium shot of Nina. She turns, passionate. Fierce love expression."},
    {"filename": "scene-28-panel-15.png", "prompt": "Close-up of Nina, slight low angle, slow push in. Her voice breaks with emotion but holds firm. Pride through tears. Recognition of children's bravery."},
    {"filename": "scene-28-panel-16.png", "prompt": "Wide shot, Nina foreground, jungle behind. She gestures at vast dangerous landscape. Small human figure against overwhelming prehistoric world."},
    {"filename": "scene-28-panel-17.png", "prompt": "Close-up of Nina. She looks directly at Gabe, pleading, reminding him of his promise. Callback to Act 1."},
    {"filename": "scene-28-panel-18.png", "prompt": "Close-up of Gabe. His eyes go wide, looking past Nina. THE DISCOVERY. Sudden alertness."},
    {"filename": "scene-28-panel-19.png", "prompt": "Close-up of Nina. She trails off, interrupted."},
    {"filename": "scene-28-panel-20.png", "prompt": "Medium shot tracking Gabe's gesture. He points excitedly across the landscape. Hope breaking through."},
    {"filename": "scene-28-panel-21.png", "prompt": "Wide POV shot, slow zoom. THE COLORED PLUMES - In far distance across misty jungle, colored plumes rise - blue, red, blue - clearly visible against green. Epic landscape, small colored markers on horizon."},
    {"filename": "scene-28-panel-22.png", "prompt": "Two-shot of parents. Both lean forward squinting at distant plumes. Hope, disbelief."},
    {"filename": "scene-28-panel-23.png", "prompt": "Close-up of Nina. She stares, processing. Wonder, tentative hope."},
    {"filename": "scene-28-panel-24.png", "prompt": "Wide shot. Parents look at each other then back at plumes. Silent agreement. They start preparing to climb down. Transition from despair to action."},
    {"filename": "scene-29-panel-01.png", "prompt": "Wide tracking shot. Gabe and Nina move along high river bluff, misty river below. Moving with purpose, eyes checking distant plumes. Characters left-to-right, plumes on horizon."},
    {"filename": "scene-29-panel-02.png", "prompt": "Medium walking shot, track alongside. Gabe moves with determination. Convinced, energized."},
    {"filename": "scene-29-panel-03.png", "prompt": "Close-up of Nina. She glances at him. Hopeful but guarded."},
    {"filename": "scene-29-panel-04.png", "prompt": "Medium shot of Gabe. He gestures at plumes. Reasoned hope."},
    {"filename": "scene-29-panel-05.png", "prompt": "Close-up of Nina. She looks at plumes then at phone in hand. Pragmatic acceptance."},
    {"filename": "scene-29-panel-06.png", "prompt": "Insert shot of phone screen. Battery dropping - very low, maybe 15-20%. Phone dominates frame. TICKING CLOCK visual."},
    {"filename": "scene-29-panel-07.png", "prompt": "Two-shot, track with movement. Gabe sees battery, grabs Nina's hand. Urgent determination."},
    {"filename": "scene-29-panel-08.png", "prompt": "Wide helicopter/crane shot pulling up. Parents break into run along bluff toward plumes. Epic scale - tiny figures in massive prehistoric landscape toward distant colored markers."},

    # ============= SCENE 30-32: Canyon Crossing =============
    {"filename": "scene-30-panel-01.png", "prompt": "Wide EPIC establishing shot, crane rising. Group emerges from forest onto edge of MASSIVE CANYON. Overwhelming scale - chasm hundreds of feet deep and wide. Kids small in foreground."},
    {"filename": "scene-30-panel-02.png", "prompt": "Close-up of Mia. Her face falls at impossible obstacle. Defeated sarcasm masking fear."},
    {"filename": "scene-30-panel-03.png", "prompt": "Close-up of Ruben. He looks at her sideways. Wry humor in crisis."},
    {"filename": "scene-30-panel-04.png", "prompt": "POV shot from Leo with snap zoom across canyon. Leo squints then eyes go wide with recognition."},
    {"filename": "scene-30-panel-05.png", "prompt": "Wide POV shot, long lens. On far side of canyon, two small figures visible - Gabe and Nina arriving at their side. Canyon depth between, both parties tiny against scale."},
    {"filename": "scene-30-panel-06.png", "prompt": "Medium shot of Mia. She runs to edge, waves frantically. Desperate joy."},
    {"filename": "scene-30-panel-07.png", "prompt": "Wide shot across canyon. Distant figures stop, look toward them, wave back. Two groups mirroring each other across void."},
    {"filename": "scene-31-panel-01.png", "prompt": "Two-shot of parents. Nina grabs Gabe's arm, pointing excitedly. Overwhelming relief."},
    {"filename": "scene-31-panel-02.png", "prompt": "Close-up of Gabe. He stares, tears forming. Emotional breakthrough. Father's relief."},
    {"filename": "scene-31-panel-03.png", "prompt": "Close-up of Nina. She looks at canyon then kids. Relief becoming worry about logistics."},
    {"filename": "scene-31-panel-04.png", "prompt": "POV shot with squint, long lens. Gabe notices strange creature with kids. Confused concern."},
    {"filename": "scene-31-panel-05.png", "prompt": "Close-up of Nina. She thinks back, trying to process impossible information."},
    {"filename": "scene-31-panel-06.png", "prompt": "Close-up of Gabe. He points more specifically at the chicken-y creature. Focused on truly inexplicable."},
    {"filename": "scene-32-panel-01.png", "prompt": "Close-up of Mia. She turns to Ruben, looking for leadership."},
    {"filename": "scene-32-panel-02.png", "prompt": "Close-up of Leo. He looks at canyon. Simple child logic."},
    {"filename": "scene-32-panel-03.png", "prompt": "Two-shot. Mia turns on Leo with sibling exasperation."},
    {"filename": "scene-32-panel-04.png", "prompt": "Close-up of Leo. He perks up with flying idea. Hopeful."},
    {"filename": "scene-32-panel-05.png", "prompt": "Close-up of Ruben. He waves hands dismissively about flying. Apologetic but firm."},
    {"filename": "scene-32-panel-06.png", "prompt": "Close-up of Leo. He tries super-jumping suggestion. Grasping."},
    {"filename": "scene-32-panel-07.png", "prompt": "Close-up of Mia. She jumps in with pumpkin helicopter idea. Desperate creativity."},
    {"filename": "scene-32-panel-08.png", "prompt": "Close-up of Ruben. He looks genuinely baffled at pumpkin reference. Completely lost."},
    {"filename": "scene-32-panel-09.png", "prompt": "Medium shot of Ruben. He looks at Leo's backpack, gears turning."},
    {"filename": "scene-32-panel-10.png", "prompt": "Insert montage shot. Backpack contents laid out: candy, chocolate milk carton, BOX OF CRAYONS."},
    {"filename": "scene-32-panel-11.png", "prompt": "Close-up. Ruben snatches up crayon box. Building plan expression."},
    {"filename": "scene-32-panel-12.png", "prompt": "Medium shot of Mia. She pulls hair tie from ponytail. Offering what she has."},
    {"filename": "scene-32-panel-13.png", "prompt": "Close-up of Ruben. He takes hair tie. Pieces coming together expression."},
    {"filename": "scene-32-panel-14.png", "prompt": "Wide shot. Ruben arranges items, raises mop. Concentrating on spell."},
    {"filename": "scene-32-panel-15.png", "prompt": "Wide EPIC shot, track magic energy. Ruben waves mop in elaborate pattern. Magic sparkles envelop crayons and hair tie, float, multiply, transform - shooting across canyon."},
    {"filename": "scene-32-panel-16.png", "prompt": "Wide establishing crane shot. COLORFUL CRAYON BRIDGE spans canyon - giant crayons in various colors form walking surface, connected by stretched hair-tie rope network. Epic rainbow against prehistoric landscape."},
    {"filename": "scene-32-panel-17.png", "prompt": "Close-up of Leo. His jaw drops in pure amazement."},
    {"filename": "scene-32-panel-18.png", "prompt": "Close-up of Ruben. He tugs suspenders proudly. Satisfied with himself."},
    {"filename": "scene-32-panel-19.png", "prompt": "Insert shot. Few crayon slats crack and crumble, falling into void. Instability emphasized."},
    {"filename": "scene-32-panel-20.png", "prompt": "Close-up of Leo. Excitement vanishes. Genuine fear."},
    {"filename": "scene-32-panel-21.png", "prompt": "Medium shot. Mia puts hand on Leo's shoulder. Brave older sister masking own fear."},
    {"filename": "scene-32-panel-22.png", "prompt": "Wide shot, track with Mia. She carefully edges onto bridge. Crayons creak, rope sways. Slow deliberate steps. Mia small against vast canyon drop."},
    {"filename": "scene-32-panel-23.png", "prompt": "Medium tracking shot. Ruben follows, admiring handiwork despite creaking danger. Oblivious pride, ironic."},
    {"filename": "scene-32-panel-24.png", "prompt": "Wide tracking shot. Jetplane CHARGES ahead completely unafraid, scooting past Mia and Ruben. Blissfully ignorant of danger."},
    {"filename": "scene-32-panel-25.png", "prompt": "Over-shoulder shot from Mia looking back at Leo. She calls encouragement."},
    {"filename": "scene-32-panel-26.png", "prompt": "Medium shot. Leo finally musters courage, steps onto bridge far behind others. Terrified but determined."},
    {"filename": "scene-32-panel-27.png", "prompt": "Wide overhead crane shot. Jetplane reaches other side, then Mia, then Ruben. Leo trails far behind moving slowly. Bridge spans frame diagonally."},
    {"filename": "scene-32-panel-28.png", "prompt": "Medium shot. On far side, Gabe and Nina wait with arms outstretched as Mia arrives. Family embracing on edge. Relief, joy."},
    {"filename": "scene-32-panel-29.png", "prompt": "Medium tracking shot with Leo. He's near end of bridge, can see family waiting. Just a few more steps. Focused, almost relieved."},
    {"filename": "scene-32-panel-30.png", "prompt": "Wide shot. HUGE GUST OF WIND hits canyon. Bridge sways violently. Leo loses footing, arms pinwheeling."},
    {"filename": "scene-32-panel-31.png", "prompt": "Insert quick close-up. Crayon under Leo's feet CRACKS, spider-webbing pattern spreading."},
    {"filename": "scene-32-panel-32.png", "prompt": "Wide shot tracking fall. Crayon BREAKS. Leo FALLS THROUGH grabbing rope at last second. He dangles over abyss."},
    {"filename": "scene-32-panel-33.png", "prompt": "Quick cuts reaction montage. Mia screams. Nina screams. Gabe lunges forward. Jetplane squawks. Pure terror expressions."},
    {"filename": "scene-32-panel-34.png", "prompt": "Close-up. Rope Leo is holding STRETCHES, FRAYS. His grip slipping. White-knuckled hands, rope fibers snapping."},
    {"filename": "scene-32-panel-35.png", "prompt": "Wide tracking shot. Rope BREAKS. Leo FALLS into canyon. Echo of screams."},
    {"filename": "scene-32-panel-36.png", "prompt": "Wide shot. Before Leo falls far, Ruben THRUSTS mop toward him, eyes squeezed shut in concentration. Magic beam shoots out connecting mop to Leo."},
    {"filename": "scene-32-panel-37.png", "prompt": "Wide side view. Leo FROZEN in mid-air, suspended by magic. He floats near cliff wall, out of reach. Magic glow around him."},
    {"filename": "scene-32-panel-38.png", "prompt": "Close-up of Mia. She looks desperately at Ruben. Pleading expression."},
    {"filename": "scene-32-panel-39.png", "prompt": "Close-up of Ruben. He's shaking with effort, sweat on brow. Maximum exertion."},
    {"filename": "scene-32-panel-40.png", "prompt": "Close-up of Ruben. His arms shake. Desperation - can't hold much longer. TENSION PEAK."},
    {"filename": "scene-32-panel-41.png", "prompt": "Wide shot with sudden action. Jetplane steps to edge, opens mouth, SHOOTS OUT hideously long tongue toward Leo. Grotesque but heroic."},
    {"filename": "scene-32-panel-42.png", "prompt": "Close-up. Slobbery slimy tongue wraps around Leo's arm. He grimaces. Gross but grabbing on anyway."},
    {"filename": "scene-32-panel-43.png", "prompt": "Close-up. Leo grabs tongue with both hands. Pure 'gross but I want to live' expression."},
    {"filename": "scene-32-panel-44.png", "prompt": "Wide tracking shot. Leo's weight pulls Jetplane forward. Creature slides toward cliff edge, mouth forced wide open. Comic but tense."},
    {"filename": "scene-32-panel-45.png", "prompt": "Wide shot. Ruben and Mia grab Jetplane. Nina and Gabe grab onto them. Human chain forms. Everyone straining."},
    {"filename": "scene-32-panel-46.png", "prompt": "Wide tracking shot. Everyone PULLS together. Leo rises slowly. Tongue retracts. Collective effort."},
    {"filename": "scene-32-panel-47.png", "prompt": "Medium shot. Leo's hand reaches cliff edge. Gabe GRABS it. Pulls him up final distance. Determined father, grateful son."},
    {"filename": "scene-32-panel-48.png", "prompt": "Wide shot. Leo collapses onto solid ground. Everyone exhales. Jetplane retracts tongue, looking proud. Everyone catching breath."},
    {"filename": "scene-32-panel-49.png", "prompt": "Medium intimate shot, slow push in. Nina pulls both kids into fierce hug. Gabe wraps arms around all three. FAMILY REUNION HUG. Overwhelming relief, love, tears."},
    {"filename": "scene-32-panel-50.png", "prompt": "Close-up of Mia. Face buried in Nina's shoulder. Vulnerable child again."},
    {"filename": "scene-32-panel-51.png", "prompt": "Close-up of Nina. She strokes Mia's hair. Maternal warmth."},
    {"filename": "scene-32-panel-52.png", "prompt": "Medium shot of Gabe. He looks at Leo then Ruben. Shaken but relieved."},
    {"filename": "scene-32-panel-53.png", "prompt": "Two-shot. Gabe extends hand to Ruben. Grateful expression."},
    {"filename": "scene-32-panel-54.png", "prompt": "Close-up of Ruben. He straightens up, formal. Professional pride despite chaos."},
    {"filename": "scene-32-panel-55.png", "prompt": "Insert shot. They shake hands. Odd moment of normalcy."},
    {"filename": "scene-32-panel-56.png", "prompt": "Medium shot of Nina. She looks at Jetplane with mix of gratitude and confusion. Processing the impossible."},
    {"filename": "scene-32-panel-57.png", "prompt": "Close-up of Leo. He puts protective arm around Jetplane. Proud ownership."},
    {"filename": "scene-32-panel-58.png", "prompt": "Close-up of Nina. She squints at creature questioningly."},
    {"filename": "scene-32-panel-59.png", "prompt": "Close-up of Mia. She shrugs. Beyond caring about taxonomy."},
    {"filename": "scene-32-panel-60.png", "prompt": "Close-up of Leo. He beams about Jetplane's colored farts. Proudest achievement."},
    {"filename": "scene-32-panel-61.png", "prompt": "Close-up of Gabe. His face lights up with understanding. Pieces coming together."},
    {"filename": "scene-32-panel-62.png", "prompt": "Close-up of Mia. She pinches nose. Sisterly disclaimer. Comedy end to intense sequence."},

    # ============= SCENE 33: T-Rex Climax =============
    {"filename": "scene-33-panel-01.png", "prompt": "Wide tracking shot, steadicam running with group. Reunited family runs through swamp toward portal. Evening light, long shadows. Everyone exhausted but determined."},
    {"filename": "scene-33-panel-02.png", "prompt": "Medium running shot, track. Mia runs alongside Nina. Urgent expression."},
    {"filename": "scene-33-panel-03.png", "prompt": "Insert close-up of phone. Nina checks while running. Battery CRITICALLY LOW - single digit, flashing red. Maximum urgency."},
    {"filename": "scene-33-panel-04.png", "prompt": "Wide shot, group running past. Ruben falls behind, older and tired. Wheezing but determined."},
    {"filename": "scene-33-panel-05.png", "prompt": "Medium tracking shot. Leo runs, looking back at Jetplane. Caring even under pressure."},
    {"filename": "scene-33-panel-06.png", "prompt": "Wide crane shot. Group STOPS SUDDENLY. Something is wrong. Frozen mid-run."},
    {"filename": "scene-33-panel-07.png", "prompt": "POV shot with finger point. Gabe points at portal visible in clearing ahead. Relief turning to..."},
    {"filename": "scene-33-panel-08.png", "prompt": "Wide establishing doom shot, slow push in. Portal swirls invitingly BUT BLOCKING IT is T-REX. She stands in front, surveying territory. T-Rex dominates frame, portal small behind."},
    {"filename": "scene-33-panel-09.png", "prompt": "Close-up of Nina. Recognition and dread. 'Of course it's her' expression."},
    {"filename": "scene-33-panel-10.png", "prompt": "Close-up of Mia. She looks between parents. Disbelief expression."},
    {"filename": "scene-33-panel-11.png", "prompt": "Close-up of Gabe. Deadpan dry humor masking fear."},
    {"filename": "scene-33-panel-12.png", "prompt": "Wide POV shot. T-Rex perfectly positioned between them and portal. Unmovable obstacle."},
    {"filename": "scene-33-panel-13.png", "prompt": "Close-up of Gabe. He looks left and right for alternatives. Tactical thinking."},
    {"filename": "scene-33-panel-14.png", "prompt": "Close-up of Nina. She gives him a look. 'That didn't work before' expression."},
    {"filename": "scene-33-panel-15.png", "prompt": "Close-up of Gabe. He bristles. Defensive expression."},
    {"filename": "scene-33-panel-16.png", "prompt": "Two-shot. Parents begin arguing, voices overlapping, gesturing at routes. Kids watching in background. Married couple bickers even in mortal danger."},
    {"filename": "scene-33-panel-17.png", "prompt": "Close-up of Leo. He tries to speak up, wanting to help."},
    {"filename": "scene-33-panel-18.png", "prompt": "Wide shot. Parents don't hear, continue arguing. Overlapping dialogue chaos."},
    {"filename": "scene-33-panel-19.png", "prompt": "Close-up of Leo. More forceful attempt. Frustration building."},
    {"filename": "scene-33-panel-20.png", "prompt": "Two-shot. Gabe glances at Leo but doesn't engage. Distracted dismissal."},
    {"filename": "scene-33-panel-21.png", "prompt": "Medium shot. Frustrated Leo pulls Mia aside. They huddle whispering, grab Ruben. Kids plotting while adults argue in background."},
    {"filename": "scene-33-panel-22.png", "prompt": "Medium shot of Mia. She steps forward, clears throat. Taking charge."},
    {"filename": "scene-33-panel-23.png", "prompt": "Wide shot. Parents still arguing. Argument continues."},
    {"filename": "scene-33-panel-24.png", "prompt": "Close-up of Mia. She raises voice. Commanding expression."},
    {"filename": "scene-33-panel-25.png", "prompt": "Two-shot. Gabe and Nina freeze, turn to look at her. T-Rex also starts looking for source of noise. Caught mid-argument."},
    {"filename": "scene-33-panel-26.png", "prompt": "Close-up of Gabe. He gestures urgently to be quiet. Fear of being heard."},
    {"filename": "scene-33-panel-27.png", "prompt": "Close-up of Nina. Confused concern."},
    {"filename": "scene-33-panel-28.png", "prompt": "Medium shot of Mia. She points at Leo. Confident, trusting her brother."},
    {"filename": "scene-33-panel-29.png", "prompt": "Wide tracking shot with Leo. He RUNS into clearing YELLING to draw attention. Jetplane follows loyally. Small boy running toward massive dinosaur."},
    {"filename": "scene-33-panel-30.png", "prompt": "Wide shot. T-Rex sees small figure, ROARS, begins moving toward Leo. Full creature animation, ground shake."},
    {"filename": "scene-33-panel-31.png", "prompt": "Two-shot. Gabe and Nina react with horror. Terror expressions."},
    {"filename": "scene-33-panel-32.png", "prompt": "Close-up of Mia. She holds up hand. Confident in the plan."},
    {"filename": "scene-33-panel-33.png", "prompt": "Insert quick shot. Phone shows battery critical warning. Red pulsing."},
    {"filename": "scene-33-panel-34.png", "prompt": "Wide tracking shot. Leo waves arms making himself target. T-Rex gets closer, ground shaking. David vs Goliath scale."},
    {"filename": "scene-33-panel-35.png", "prompt": "Close-up of Mia. She watches, waiting for right moment. Timing the plan."},
    {"filename": "scene-33-panel-36.png", "prompt": "Wide tracking shot. Gabe can't wait. He RUNS OUT putting himself between Leo and dinosaur. Overriding fear with paternal instinct."},
    {"filename": "scene-33-panel-37.png", "prompt": "Medium shot, low angle heroic. Gabe stands tall, arms wide, yelling at T-Rex. Fierce protection. GABE'S COMPLETE CHARACTER ARC."},
    {"filename": "scene-33-panel-38.png", "prompt": "Close-up T-Rex, low angle. She ROARS and begins CHARGING at Gabe. Full creature close-up, primal fury."},
    {"filename": "scene-33-panel-39.png", "prompt": "Wide shot. Gabe starts running TOWARD T-Rex. They close distance. Man and monster racing toward each other. MAXIMUM TENSION."},
    {"filename": "scene-33-panel-40.png", "prompt": "Close-up of Mia. She turns urgently to Ruben. It's time."},
    {"filename": "scene-33-panel-41.png", "prompt": "Wide tracking shot. Ruben points mop at Jetplane. Magic beam hits creature."},
    {"filename": "scene-33-panel-42.png", "prompt": "Medium shot. Instead of growing, Jetplane SHRINKS to HALF size. Confused and tiny. Sad deflating effect."},
    {"filename": "scene-33-panel-43.png", "prompt": "Close-up of Mia. Face contorts with frustration. 'Are you KIDDING me' expression."},
    {"filename": "scene-33-panel-44.png", "prompt": "Close-up of Ruben. He looks at mop in horror. Panicked confusion."},
    {"filename": "scene-33-panel-45.png", "prompt": "Close-up of Nina. Watching charging collision. Terror."},
    {"filename": "scene-33-panel-46.png", "prompt": "Wide cinematic shot, slow motion feel. Gabe and T-Rex about to collide. Certain death. Epic showdown framing."},
    {"filename": "scene-33-panel-47.png", "prompt": "Medium shot. Ruben desperate, aims again. Maximum effort."},
    {"filename": "scene-33-panel-48.png", "prompt": "Wide EPIC crane shot rising. Jetplane EXPLODES in size, growing BIGGER than T-Rex. Towers over clearing, massive and terrifying but cute. MAJOR VFX moment."},
    {"filename": "scene-33-panel-49.png", "prompt": "Wide shot. Everything stops. Gabe stops running. T-Rex stops. All eyes on GIANT JETPLANE dominating frame, everyone tiny below. Stunned silence."},
    {"filename": "scene-33-panel-50.png", "prompt": "Close-up of Gabe. He stares up, mouth agape. Complete disbelief."},
    {"filename": "scene-33-panel-51.png", "prompt": "Close-up of T-Rex. Expression shifts from predator to prey. Recognizes she's outmatched. Fear in eyes."},
    {"filename": "scene-33-panel-52.png", "prompt": "Close-up of Leo. He looks up at massive friend. Awe expression."},
    {"filename": "scene-33-panel-53.png", "prompt": "Close-up of Leo. He grins, raises arm to command. Empowered expression. LEO'S BOND PAYS OFF."},
    {"filename": "scene-33-panel-54.png", "prompt": "Wide action shot, track. Giant Jetplane makes MASSIVE gargle sound. Terrifying at this scale. He LASHES enormous tongue. Giant creature action."},
    {"filename": "scene-33-panel-55.png", "prompt": "Wide tracking shot. T-Rex BACKS AWAY then TURNS AND RUNS, crashing through jungle in retreat. Tables turned - predator fleeing."},
    {"filename": "scene-33-panel-56.png", "prompt": "Medium shot of Mia. She pumps fist. Triumphant."},
    {"filename": "scene-33-panel-57.png", "prompt": "Close-up of Ruben. He stares at mop. Shocked at own success."},
    {"filename": "scene-33-panel-58.png", "prompt": "Close-up of Leo. He beams. Proud expression."},
    {"filename": "scene-33-panel-59.png", "prompt": "Close-up of Ruben. He slowly smiles. Pride, redemption. RUBEN'S REDEMPTION ARC COMPLETE."},
    {"filename": "scene-33-panel-60.png", "prompt": "Insert shot. Phone screen countdown: 10, 9, 8... Red pulsing. Warning beeps."},
    {"filename": "scene-33-panel-61.png", "prompt": "Close-up of Nina. She holds up phone. Maximum urgency."},
    {"filename": "scene-33-panel-62.png", "prompt": "Wide tracking shot. Everyone RUNS toward portal. Gabe leads, gestures to Mia. Group sprinting, countdown continues."},
    {"filename": "scene-33-panel-63.png", "prompt": "Medium shot. Gabe reaches portal first but turns to usher Mia through. Father protecting family."},
    {"filename": "scene-33-panel-64.png", "prompt": "Close-up of Mia. She hesitates, worried about dad."},
    {"filename": "scene-33-panel-65.png", "prompt": "Close-up of Gabe. He looks her in eyes. Sincere promise - 'I'm right behind you.' CALLBACK - FINALLY KEEPING PROMISE."},
    {"filename": "scene-33-panel-66.png", "prompt": "Close-up of Leo. He looks at giant Jetplane. Worried for his friend."},
    {"filename": "scene-33-panel-67.png", "prompt": "Close-up of Ruben. He catches up wheezing. Confident about spell wearing off."},
    {"filename": "scene-33-panel-68.png", "prompt": "Close-up of Leo. He looks at Jetplane then small portal. He won't fit!"},
    {"filename": "scene-33-panel-69.png", "prompt": "Medium shot. Nina grabs Leo. Maternal urgency."},
    {"filename": "scene-33-panel-70.png", "prompt": "Close-up of Gabe. He looks at giant Jetplane then Leo. Pragmatic but gentle."},
    {"filename": "scene-33-panel-71.png", "prompt": "Wide tracking shot into portal. Gabe PUSHES kids through portal. They disappear into swirling blue energy. Portal entry effect."},
    {"filename": "scene-33-panel-72.png", "prompt": "Medium shot. Nina goes next, reaching back for Gabe. Portal transition effect."},
    {"filename": "scene-33-panel-73.png", "prompt": "Medium shot. Ruben jumps through with a whoop. Enjoying himself despite everything."},
    {"filename": "scene-33-panel-74.png", "prompt": "Insert shot. Phone countdown: 3... 2... Final warning beeps."},
    {"filename": "scene-33-panel-75.png", "prompt": "Medium shot. Gabe pauses at portal edge, takes last look at incredible prehistoric world. Then at giant Jetplane. Wonder, gratitude, determination."},
    {"filename": "scene-33-panel-76.png", "prompt": "Wide tracking shot. Gabe LEAPS into portal just as it begins collapsing. Portal destabilizing, barely making it."},
    {"filename": "scene-33-panel-77.png", "prompt": "Wide shot. Portal SNAPS shut. Jurassic swamp empty and quiet. Giant Jetplane stands alone. Prehistoric silence."},

    # ============= SCENE 34-37: Resolution & Epilogue =============
    {"filename": "scene-34-panel-01.png", "prompt": "Wide shot. TIME WARP opens in middle of quiet suburban street. Blue swirling energy illuminates night. Police tape visible, lone cruiser in background."},
    {"filename": "scene-34-panel-02.png", "prompt": "Medium shot. Bodies tumble out of portal - Mia, Leo, Nina, Ruben, then Gabe - landing in heap on asphalt. Tangled pile of people."},
    {"filename": "scene-34-panel-03.png", "prompt": "Close-up of Mia. She pushes herself up, looks around at familiar street. Overwhelming relief, joy."},
    {"filename": "scene-34-panel-04.png", "prompt": "Medium shot of Gabe. He stands, brushing prehistoric dirt off ruined formal attire. Shaken but relieved."},
    {"filename": "scene-34-panel-05.png", "prompt": "Two-shot. Gabe turns to Leo with serious expression. Leo braces for criticism. TENSION BEAT."},
    {"filename": "scene-34-panel-06.png", "prompt": "Close-up of Leo. He waits, holding breath. Nervous anticipation."},
    {"filename": "scene-34-panel-07.png", "prompt": "Two-shot, push in. Gabe's face breaks into proud grin. Pure fatherly pride. FATHER-SON PAYOFF."},
    {"filename": "scene-34-panel-08.png", "prompt": "Close-up of Leo. He beams with pride at father's approval. Glowing validation."},
    {"filename": "scene-34-panel-09.png", "prompt": "Wide shot, slow push in. Whole family group hug - Gabe, Nina, Mia, Leo embracing. Street lamp warm light above. COMPLETE FAMILY REUNION."},
    {"filename": "scene-35-panel-01.png", "prompt": "Interior car shot. OFFICER JACKSON shakes awake in cruiser, disturbed by portal noise/light. Startled, disoriented."},
    {"filename": "scene-35-panel-02.png", "prompt": "Insert shot. CB radio crackles with static."},
    {"filename": "scene-35-panel-03.png", "prompt": "Close-up of officer. He looks out windshield, sees family, does double-take. Confusion."},
    {"filename": "scene-35-panel-04.png", "prompt": "Medium shot. Officer grabs radio, speaks into it. Uncertain but reporting."},
    {"filename": "scene-35-panel-05.png", "prompt": "Insert on radio. Dispatch responds."},
    {"filename": "scene-35-panel-06.png", "prompt": "Close-up of officer. He counts heads, nods. Counting expression."},
    {"filename": "scene-35-panel-07.png", "prompt": "Insert on radio. Backup offer from dispatch."},
    {"filename": "scene-35-panel-08.png", "prompt": "POV through windshield. Officer starts to respond, then sees something that makes him trail off. Confusion becoming shock."},
    {"filename": "scene-35-panel-09.png", "prompt": "Wide shot. Officer opens door, stands, stares at something off-screen. Jaw dropping."},
    {"filename": "scene-36-panel-01.png", "prompt": "Wide EPIC shot. Just as portal about to collapse, GIANT JETPLANE comes BURSTING through. Portal SNAPS shut behind him. Maximum VFX - giant creature emerging. SURPRISE BEAT."},
    {"filename": "scene-36-panel-02.png", "prompt": "Medium shot. Family still hugging, hasn't seen Jetplane arrive behind them. Intimate moment foreground, massive creature background."},
    {"filename": "scene-36-panel-03.png", "prompt": "Wide tracking shot. Giant Jetplane walks up quietly behind family, casting massive shadow over them."},
    {"filename": "scene-36-panel-04.png", "prompt": "Medium handheld urgent shot. Officer grabs bullhorn from car, points. Panic expression."},
    {"filename": "scene-36-panel-05.png", "prompt": "Close-up of Gabe. He looks at officer, confused."},
    {"filename": "scene-36-panel-06.png", "prompt": "Close-up of Nina. She gestures at kids, trying to explain."},
    {"filename": "scene-36-panel-07.png", "prompt": "Close-up of Ruben. He steps aside from family. Clarifying he's not parent. Comedy beat."},
    {"filename": "scene-36-panel-08.png", "prompt": "Medium shot of officer. He points PAST them at the monster. Terrified."},
    {"filename": "scene-36-panel-09.png", "prompt": "Close-up of Ruben. He looks offended, thinking officer means him. Indignant comedy."},
    {"filename": "scene-36-panel-10.png", "prompt": "Wide shot. Officer turns on siren. Noise and lights JOLT Jetplane who WHIMPERS. Police siren, creature distress."},
    {"filename": "scene-36-panel-11.png", "prompt": "Wide shot. NOW family turns and sees giant Jetplane behind them. Collective surprise."},
    {"filename": "scene-36-panel-12.png", "prompt": "Close-up of Leo. His face lights up. Pure joy."},
    {"filename": "scene-36-panel-13.png", "prompt": "Wide shot. Leo runs to Jetplane and hugs his massive leg. Tiny boy against giant creature."},
    {"filename": "scene-36-panel-14.png", "prompt": "Close-up of Ruben. He stares up at still-giant Jetplane. Didn't wear off? confusion."},
    {"filename": "scene-36-panel-15.png", "prompt": "Wide panning shot. Multiple SQUAD CARS arrive, lights and sirens blazing. Officers take positions behind cars."},
    {"filename": "scene-36-panel-16.png", "prompt": "Medium shot. Detective MCNATTIN emerges, takes command. Taking control expression."},
    {"filename": "scene-36-panel-17.png", "prompt": "Close-up of Leo. He looks at agitated Jetplane then all lights. Protective concern."},
    {"filename": "scene-36-panel-18.png", "prompt": "Tracking shot following McNattin. He walks toward group with bullhorn. Attempting calm."},
    {"filename": "scene-36-panel-19.png", "prompt": "Wide shot. Sirens overwhelm Jetplane. He begins GARGLE-ROARING, rearing up, appearing menacing. Creature agitation."},
    {"filename": "scene-36-panel-20.png", "prompt": "Wide action shot. Jetplane LASHES enormous tongue, smashing lights on police car. McNattin knocked over. Tongue physics, car damage."},
    {"filename": "scene-36-panel-21.png", "prompt": "Close-up of McNattin. On ground, signals to other officers. Grim determination."},
    {"filename": "scene-36-panel-22.png", "prompt": "Wide shot. Officers ready weapons, taking aim at giant Jetplane. Gun barrels foreground, Jetplane background."},
    {"filename": "scene-36-panel-23.png", "prompt": "Medium shot of Gabe. He steps between guns and Jetplane, hands raised. Desperate to defuse."},
    {"filename": "scene-36-panel-24.png", "prompt": "Close-up of Leo. He reaches up to touch Jetplane's leg soothingly. Gentle, calming."},
    {"filename": "scene-36-panel-25.png", "prompt": "Close-up of Mia. She turns urgently to Ruben. Urgent expression."},
    {"filename": "scene-36-panel-26.png", "prompt": "Close-up of Ruben. He shakes head helplessly. Frustrated helplessness."},
    {"filename": "scene-36-panel-27.png", "prompt": "Close-up of Mia. She points at Jetplane. Solution dawning."},
    {"filename": "scene-36-panel-28.png", "prompt": "Close-up of Ruben. His face lights up remembering the shrink spell."},
    {"filename": "scene-36-panel-29.png", "prompt": "Medium shot. Ruben points mop at Jetplane just as officers about to fire. Magic beam."},
    {"filename": "scene-36-panel-30.png", "prompt": "Wide shot with VFX. In burst of magic, Jetplane SHRINKS from giant to CHIHUAHUA SIZE. Now tiny and adorable. Major shrinking effect."},
    {"filename": "scene-36-panel-31.png", "prompt": "Wide shot. Everyone freezes in confusion. Giant threat just gone. Tiny creature where monster was. Officers aiming at nothing."},
    {"filename": "scene-36-panel-32.png", "prompt": "Medium shot. Leo quickly SCOOPS UP tiny Jetplane and hides him in backpack, zipping mostly closed. Quick furtive movement."},
    {"filename": "scene-36-panel-33.png", "prompt": "Medium tracking shot. McNattin walks toward family bewildered, looking around for creature. Completely confused."},
    {"filename": "scene-36-panel-34.png", "prompt": "Close-up of Gabe. He shrugs innocently. Terrible liar but earnest."},
    {"filename": "scene-36-panel-35.png", "prompt": "Close-up of Nina. She nods along. Going with it."},
    {"filename": "scene-36-panel-36.png", "prompt": "Two-shot of kids. Mia and Leo nod vigorously. Overselling innocence."},
    {"filename": "scene-36-panel-37.png", "prompt": "Close-up of McNattin. He squints at them. Not buying it."},
    {"filename": "scene-36-panel-38.png", "prompt": "Close-up of Gabe. He gestures academically about time-warp terminology. Helpful pedantry."},
    {"filename": "scene-36-panel-39.png", "prompt": "Close-up of Leo. He chimes in about wormhole. Excited to contribute."},
    {"filename": "scene-36-panel-40.png", "prompt": "Close-up of Ruben. He offers 'singularity.' Trying to help."},
    {"filename": "scene-36-panel-41.png", "prompt": "Close-up of Mia. Dramatic flair about tear in spacetime. Enjoying herself."},
    {"filename": "scene-36-panel-42.png", "prompt": "Insert shot. From inside backpack, tiny Jetplane lets out distinctive gargle-chirp. Backpack twitching."},
    {"filename": "scene-36-panel-43.png", "prompt": "Wide shot. Whole family pretends they didn't hear it. Collective poker faces."},
    {"filename": "scene-36-panel-44.png", "prompt": "Close-up of McNattin. He stares at them, shakes head slowly. Too tired to pursue this."},
    {"filename": "scene-36-panel-45.png", "prompt": "Wide crane shot rising and pulling back. McNattin backs away. Family geeking about portal terminology. Police dispersing. Normal suburban night resumes, absurd scene."},
    {"filename": "scene-37-panel-01.png", "prompt": "Wide establishing shot. Sun streams through kitchen window of Bornsztein home. Everything warm and golden. Idyllic domestic scene."},
    {"filename": "scene-37-panel-02.png", "prompt": "Medium shot. Gabe in casual clothes (contrast to tuxedo) flips pancakes at stove. Content, relaxed - NEW GABE. Domestic, present."},
    {"filename": "scene-37-panel-03.png", "prompt": "Two-shot. Nina enters with coffee. Testing the waters about board meeting."},
    {"filename": "scene-37-panel-04.png", "prompt": "Close-up of Gabe. He shakes head casually, flipping pancake. Promised Mia lizard shop. PROMISE KEPT - GABE HAS CHANGED."},
    {"filename": "scene-37-panel-05.png", "prompt": "Medium tracking shot. Mia runs in excitedly. Normal kid excitement."},
    {"filename": "scene-37-panel-06.png", "prompt": "Close-up of Nina. Motherly hedging. Parental non-commitment."},
    {"filename": "scene-37-panel-07.png", "prompt": "Close-up of Mia. She pouts. Sibling rivalry - Leo got one."},
    {"filename": "scene-37-panel-08.png", "prompt": "Medium shot of Gabe. He puts pancakes on plates. Firm but warm."},
    {"filename": "scene-37-panel-09.png", "prompt": "Wide shot, pulling back through window. Leo arrives at table. Normal morning chaos."},
    {"filename": "scene-37-panel-10.png", "prompt": "Same wide shot, continuing pull back, now through window. Nina pours juice. Family framed in window, warm interior light."},
    {"filename": "scene-37-panel-11.png", "prompt": "Same continuing pull back. Mia asks for whipped cream."},
    {"filename": "scene-37-panel-12.png", "prompt": "Same continuing pull back, now outside rising. Gabe calls out playfully - asking about pancakes for 'little dude.' Implying Jetplane."},
    {"filename": "scene-37-panel-13.png", "prompt": "Wide aerial shot, crane rising to bird's eye. House from above, beautiful morning, neighborhood peaceful. Full house visible, chimney prominent."},
    {"filename": "scene-37-panel-14.png", "prompt": "Continue aerial shot. Distant dialogue - Leo protests 'Dad!!'"},
    {"filename": "scene-37-panel-15.png", "prompt": "Continue aerial shot. Gabe's innocent 'What?!'"},
    {"filename": "scene-37-panel-16.png", "prompt": "Wide aerial FINAL IMAGE shot. From chimney, COLORED PLUMES of smoke rise - blue, red, blue. Signature Jetplane farts. Idyllic house with magical colored smoke from chimney. FINAL PAYOFF - Jetplane is home."},
    {"filename": "scene-37-panel-17.png", "prompt": "Continue aerial shot. More plumes rise. Leo's voice: 'I already fed him!'"},
    {"filename": "scene-37-panel-18.png", "prompt": "Continue aerial shot, hold. Few more colorful plumes rise against blue sky. Warm conclusion."},
    {"filename": "scene-37-panel-19.png", "prompt": "Black frame. THE END. Fade to black."},
]


def generate_image(prompt: str, filename: str) -> bool:
    """Generate a single image using Gemini 2.0 Flash."""
    output_path = OUTPUT_DIR / filename

    # Skip if already exists
    if output_path.exists():
        print(f"  [SKIP] Already exists: {filename}")
        return True

    full_prompt = f"{STYLE_PREFIX}\n\n{CHARACTER_REF}\n\nScene: {prompt}"

    print(f"Generating: {filename}")
    print(f"  Prompt: {prompt[:60]}...")

    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash-exp-image-generation",
            contents=f"Generate an image: {full_prompt}",
            config=types.GenerateContentConfig(
                response_modalities=["IMAGE", "TEXT"],
            ),
        )

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
    """Generate all Act 3 storyboard panels."""
    print("=" * 70)
    print("Generating Act 3 Storyboard Panels - ROUGH SKETCH STYLE")
    print("=" * 70)
    print(f"Output directory: {OUTPUT_DIR}")
    print(f"Total panels to generate: {len(ACT3_PANELS)}")
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    success_count = 0
    skip_count = 0
    total = len(ACT3_PANELS)

    for i, panel in enumerate(ACT3_PANELS, 1):
        print(f"\n[{i}/{total}] ", end="")

        output_path = OUTPUT_DIR / panel["filename"]
        if output_path.exists():
            print(f"[SKIP] {panel['filename']} already exists")
            skip_count += 1
            success_count += 1
            continue

        if generate_image(panel["prompt"], panel["filename"]):
            success_count += 1

        # Rate limiting delay
        if i < total:
            time.sleep(2)

    print("\n" + "=" * 70)
    print(f"Complete: {success_count}/{total} images ({skip_count} skipped)")
    print("=" * 70)

    return 0 if success_count == total else 1


if __name__ == "__main__":
    sys.exit(main())
