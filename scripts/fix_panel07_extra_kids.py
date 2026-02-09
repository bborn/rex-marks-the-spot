#!/usr/bin/env python3
"""Fix Scene 1 Panel 07 - Remove extra kids.

Director feedback: Panel 07 has random extra kids by the TV.
Should ONLY show Mia and Leo (2 kids total).
"""
import os
import sys
import time
import google.generativeai as genai
from PIL import Image
from pathlib import Path

genai.configure(api_key=os.environ['GEMINI_API_KEY'])
model = genai.GenerativeModel('gemini-3-pro-image-preview')

# Load character refs
mia_img = Image.open('tmp/char-refs/mia_turnaround_APPROVED.png')
leo_img = Image.open('tmp/char-refs/leo_turnaround_APPROVED.png')

prompt = """Create a cinematic storyboard panel matching these character designs EXACTLY.

SCENE: Panel 1G - Over-the-shoulder shot of TWO kids watching TV

CRITICAL - ONLY 2 CHILDREN VISIBLE (not 3, not 4, ONLY 2):
1. Mia (left side, OTS): Dark brown/black curly hair in HIGH PONYTAIL visible from behind
2. Leo (right side, OTS): BLONDE curly hair visible from behind, green dinosaur pajamas

COMPOSITION:
- Camera positioned behind/between the TWO kids
- Looking past them at TV screen showing colorful cartoon
- Parents visible in background (still preparing to leave for date)
- Kids' silhouettes against TV glow
- EXACTLY 2 KIDS ONLY - Mia on left, Leo on right

LIGHTING:
- TV glow illuminating kids from front
- Warm interior home lighting
- Hair colors MUST be clearly distinct (Mia's dark vs Leo's blonde)

CAMERA: Static, over-the-shoulder framing from behind

Style: Pixar/Dreamworks cinematic storyboard
Aspect ratio: 16:9 widescreen
Visual contrast between children's calm and parents' chaos in background."""

content = [mia_img, leo_img, prompt]

MAX_ATTEMPTS = 3
for attempt in range(1, MAX_ATTEMPTS + 1):
    print(f"Attempt {attempt}/{MAX_ATTEMPTS}...")
    try:
        resp = model.generate_content(
            content,
            generation_config={'temperature': 0.7, 'top_p': 0.9},
            safety_settings=[
                {'category': c, 'threshold': 'BLOCK_NONE'}
                for c in ['HARM_CATEGORY_HARASSMENT', 'HARM_CATEGORY_HATE_SPEECH',
                         'HARM_CATEGORY_SEXUALLY_EXPLICIT', 'HARM_CATEGORY_DANGEROUS_CONTENT']
            ]
        )

        for part in resp.candidates[0].content.parts:
            if part.inline_data:
                output = Path('assets/storyboards/act1/scene-01/scene-01-panel-07.png')
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_bytes(part.inline_data.data)
                print(f'Saved: {output}')
                print(f'Size: {output.stat().st_size} bytes')
                sys.exit(0)

        print("No image data in response, retrying...")
        if attempt < MAX_ATTEMPTS:
            time.sleep(10)

    except Exception as e:
        print(f"Error: {e}")
        if attempt < MAX_ATTEMPTS:
            time.sleep(10)

print("Failed to generate image after all attempts")
sys.exit(1)
