import {AbsoluteFill, Audio, Sequence, interpolate, useCurrentFrame} from 'remotion';
import {FadeTransition} from './components/FadeTransition';
import {ScaleBlurTransition} from './components/ScaleBlurTransition';
import {SlideTransition} from './components/SlideTransition';
import {ImageScene} from './components/ImageScene';
import {TextOverlay} from './components/TextOverlay';
import {CharacterReveal} from './components/CharacterReveal';
import {StoryboardMontage} from './components/StoryboardMontage';
import {TitleCard} from './components/TitleCard';
import {ModelShowcase} from './components/ModelShowcase';
import {CallToAction} from './components/CallToAction';
import {MagicParticles} from './components/MagicParticles';
import {Vignette} from './components/Vignette';
import {PROMO, CHARACTERS, MODELS_3D, STORYBOARDS, AUDIO} from './assets';
import {COLORS} from './styles';

// 45 seconds at 30fps = 1350 frames
// Scene breakdown:
//   0-90     (0s-3s)    Hook - Family portrait with question
//   90-210   (3s-7s)    Title card reveal
//   210-360  (7s-12s)   Character introductions (meet the cast)
//   360-540  (12s-18s)  Storyboard montage (the story)
//   540-690  (18s-23s)  "But here's the twist" + adventure panels
//   690-870  (23s-29s)  3D model showcase (bringing to life)
//   870-1020 (29s-34s)  Behind the scenes - AI pipeline
//   1020-1170 (34s-39s) Ruben + Jetplane reveal
//   1170-1350 (39s-45s) CTA - Subscribe / follow the journey

export const Trailer: React.FC = () => {
  const frame = useCurrentFrame();

  // Music volume: plays full duration, fades out in last 2 seconds (60 frames)
  const musicVolume = interpolate(
    frame,
    [0, 15, 1290, 1350],
    [0, 0.3, 0.3, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  // Narration volume: starts at frame 0, fades in quickly
  const narrationVolume = interpolate(
    frame,
    [0, 10, 300, 330],
    [0, 0.85, 0.85, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'}
  );

  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      {/* === AUDIO TRACKS === */}
      <Audio src={AUDIO.trailerMusic} volume={musicVolume} />
      <Sequence from={0} durationInFrames={330}>
        <Audio src={AUDIO.trailerNarration} volume={narrationVolume} />
      </Sequence>

      {/* === HOOK: Family portrait + question === */}
      {/* Uses scale+blur transition for cinematic opener */}
      <Sequence from={0} durationInFrames={90}>
        <ScaleBlurTransition
          durationInFrames={90}
          fadeIn={15}
          fadeOut={10}
          scaleIn={1.05}
          scaleOut={0.97}
          blurIn={6}
          blurOut={3}
        >
          <ImageScene
            src={PROMO.familyPortrait}
            zoom
            durationInFrames={90}
          />
          <Vignette intensity={0.4} />
          <TextOverlay
            text="What if date night..."
            textStyle="subheading"
            fontSize={56}
            position="bottom"
            delay={15}
          />
        </ScaleBlurTransition>
      </Sequence>

      {/* === HOOK pt2: Storyboard tease === */}
      {/* Slides in from right for impact */}
      <Sequence from={70} durationInFrames={50}>
        <SlideTransition
          durationInFrames={50}
          fadeIn={8}
          fadeOut={8}
          direction="left"
          distance={100}
        >
          <ImageScene
            src={STORYBOARDS.s05p01}
            zoom
            durationInFrames={50}
            backgroundColor="#1a0a2e"
          />
          <Vignette intensity={0.5} />
          <TextOverlay
            text="...went VERY wrong?"
            textStyle="heading"
            fontSize={64}
            color={COLORS.fairyPink}
            position="bottom"
            delay={5}
          />
        </SlideTransition>
      </Sequence>

      {/* === TITLE CARD === */}
      {/* Scale+blur for dramatic reveal with magic particles */}
      <Sequence from={120} durationInFrames={120}>
        <ScaleBlurTransition
          durationInFrames={120}
          fadeIn={12}
          fadeOut={12}
          scaleIn={0.85}
          blurIn={12}
        >
          <TitleCard showLogo />
          <MagicParticles
            count={25}
            color={COLORS.warmGold}
            durationInFrames={120}
          />
        </ScaleBlurTransition>
      </Sequence>

      {/* === MEET THE CAST === */}
      {/* Slides up for character entrance */}
      <Sequence from={230} durationInFrames={150}>
        <SlideTransition
          durationInFrames={150}
          fadeIn={12}
          fadeOut={10}
          direction="up"
          distance={60}
        >
          <CharacterReveal
            durationInFrames={150}
            characters={[
              {name: 'gabe', src: CHARACTERS.gabe, label: 'Gabe (Dad)'},
              {name: 'nina', src: CHARACTERS.nina, label: 'Nina (Mom)'},
              {name: 'mia', src: CHARACTERS.mia, label: 'Mia (8)'},
              {name: 'leo', src: CHARACTERS.leo, label: 'Leo (5)'},
            ]}
          />
          <TextOverlay
            text="Meet the Family"
            textStyle="heading"
            fontSize={48}
            position="top"
            delay={0}
          />
        </SlideTransition>
      </Sequence>

      {/* === STORYBOARD MONTAGE: The setup === */}
      {/* Scale+blur for storytelling mood */}
      <Sequence from={370} durationInFrames={180}>
        <ScaleBlurTransition
          durationInFrames={180}
          fadeIn={10}
          fadeOut={10}
          scaleIn={0.95}
          blurIn={4}
        >
          <StoryboardMontage
            durationInFrames={180}
            panels={[
              STORYBOARDS.s01p01,
              STORYBOARDS.s01p03,
              STORYBOARDS.s01p05,
              STORYBOARDS.s02p01,
              STORYBOARDS.s03p01,
              STORYBOARDS.s03p03,
            ]}
          />
          <TextOverlay
            text="A simple date night..."
            textStyle="subheading"
            fontSize={40}
            position="top"
            delay={5}
          />
        </ScaleBlurTransition>
      </Sequence>

      {/* === THE TWIST: Adventure panels === */}
      {/* Slides in from left for contrast with previous montage */}
      <Sequence from={540} durationInFrames={160}>
        <SlideTransition
          durationInFrames={160}
          fadeIn={10}
          fadeOut={10}
          direction="right"
          distance={80}
        >
          <StoryboardMontage
            durationInFrames={160}
            panels={[
              STORYBOARDS.s05p01,
              STORYBOARDS.s08p01,
              STORYBOARDS.s04p01,
              STORYBOARDS.s09p01,
            ]}
          />
          <TextOverlay
            text="...becomes a Jurassic adventure"
            textStyle="subheading"
            fontSize={44}
            color={COLORS.dinoGreen}
            position="top"
            delay={5}
          />
        </SlideTransition>
      </Sequence>

      {/* === 3D MODEL SHOWCASE === */}
      {/* Scale+blur for tech showcase feel */}
      <Sequence from={690} durationInFrames={190}>
        <ScaleBlurTransition
          durationInFrames={190}
          fadeIn={12}
          fadeOut={12}
          scaleIn={0.9}
          blurIn={8}
        >
          <ModelShowcase
            durationInFrames={190}
            models={[
              {src: MODELS_3D.gabeFront, label: 'Gabe - 3D Model'},
              {src: MODELS_3D.ninaFront, label: 'Nina - 3D Model'},
              {src: MODELS_3D.miaFront, label: 'Mia - 3D Model'},
              {src: MODELS_3D.leoFront, label: 'Leo - 3D Model'},
            ]}
          />
          <MagicParticles
            count={12}
            color={COLORS.magicBlue}
            durationInFrames={190}
          />
        </ScaleBlurTransition>
      </Sequence>

      {/* === AI PIPELINE TEXT === */}
      {/* Slide up for tech section */}
      <Sequence from={870} durationInFrames={160}>
        <SlideTransition
          durationInFrames={160}
          fadeIn={12}
          fadeOut={12}
          direction="up"
          distance={50}
        >
          <AbsoluteFill
            style={{
              background: `linear-gradient(135deg, ${COLORS.deepPurple}, #000)`,
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'center',
              alignItems: 'center',
              gap: 30,
            }}
          >
            <TextOverlay
              text="Built with AI"
              textStyle="hero"
              fontSize={72}
              position="top"
              delay={0}
              subtitle="Gemini  |  Remotion  |  Blender  |  Meshy"
            />
            <TextOverlay
              text="Every frame. Every model. Every scene."
              textStyle="body"
              fontSize={36}
              color={COLORS.magicBlue}
              position="bottom"
              delay={20}
            />
          </AbsoluteFill>
          <MagicParticles
            count={15}
            color={COLORS.fairyPink}
            durationInFrames={160}
          />
        </SlideTransition>
      </Sequence>

      {/* === RUBEN + JETPLANE REVEAL === */}
      {/* Scale+blur for surprise character reveal */}
      <Sequence from={1020} durationInFrames={160}>
        <ScaleBlurTransition
          durationInFrames={160}
          fadeIn={12}
          fadeOut={12}
          scaleIn={0.85}
          blurIn={10}
        >
          <CharacterReveal
            durationInFrames={160}
            characters={[
              {
                name: 'ruben',
                src: CHARACTERS.ruben,
                label: 'Ruben - Fairy Godfather',
              },
              {
                name: 'jetplane',
                src: CHARACTERS.jetplane,
                label: 'Jetplane - Color-Farting Dino',
              },
            ]}
          />
          <TextOverlay
            text="And some unexpected friends..."
            textStyle="subheading"
            fontSize={42}
            position="top"
            delay={5}
          />
          <MagicParticles
            count={20}
            color={COLORS.warmGold}
            durationInFrames={160}
          />
        </ScaleBlurTransition>
      </Sequence>

      {/* === CALL TO ACTION === */}
      {/* Scale+blur for grand finale */}
      <Sequence from={1170} durationInFrames={180}>
        <ScaleBlurTransition
          durationInFrames={180}
          fadeIn={15}
          fadeOut={0}
          scaleIn={0.9}
          blurIn={6}
        >
          <CallToAction />
          <MagicParticles
            count={18}
            color={COLORS.warmGold}
            durationInFrames={180}
          />
        </ScaleBlurTransition>
      </Sequence>
    </AbsoluteFill>
  );
};
