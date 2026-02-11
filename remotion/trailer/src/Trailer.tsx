import {AbsoluteFill, Sequence} from 'remotion';
import {FadeTransition} from './components/FadeTransition';
import {ImageScene} from './components/ImageScene';
import {TextOverlay} from './components/TextOverlay';
import {CharacterReveal} from './components/CharacterReveal';
import {StoryboardMontage} from './components/StoryboardMontage';
import {TitleCard} from './components/TitleCard';
import {ModelShowcase} from './components/ModelShowcase';
import {CallToAction} from './components/CallToAction';
import {PROMO, CHARACTERS, MODELS_3D, STORYBOARDS} from './assets';
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
  return (
    <AbsoluteFill style={{backgroundColor: '#000'}}>
      {/* === HOOK: Family portrait + question === */}
      <Sequence from={0} durationInFrames={90}>
        <FadeTransition durationInFrames={90} fadeIn={12} fadeOut={8}>
          <ImageScene
            src={PROMO.familyPortrait}
            zoom
            durationInFrames={90}
          />
          <TextOverlay
            text="What if date night..."
            fontSize={56}
            position="bottom"
            delay={15}
          />
        </FadeTransition>
      </Sequence>

      {/* === HOOK pt2: Storyboard tease === */}
      <Sequence from={70} durationInFrames={50}>
        <FadeTransition durationInFrames={50} fadeIn={8} fadeOut={8}>
          <ImageScene
            src={STORYBOARDS.s05p01}
            zoom
            durationInFrames={50}
            backgroundColor="#1a0a2e"
          />
          <TextOverlay
            text="...went VERY wrong?"
            fontSize={64}
            color={COLORS.fairyPink}
            position="bottom"
            delay={5}
          />
        </FadeTransition>
      </Sequence>

      {/* === TITLE CARD === */}
      <Sequence from={120} durationInFrames={120}>
        <FadeTransition durationInFrames={120} fadeIn={10} fadeOut={10}>
          <TitleCard showLogo />
        </FadeTransition>
      </Sequence>

      {/* === MEET THE CAST === */}
      <Sequence from={230} durationInFrames={150}>
        <FadeTransition durationInFrames={150} fadeIn={10} fadeOut={10}>
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
            fontSize={42}
            position="top"
            delay={0}
          />
        </FadeTransition>
      </Sequence>

      {/* === STORYBOARD MONTAGE: The setup === */}
      <Sequence from={370} durationInFrames={180}>
        <FadeTransition durationInFrames={180} fadeIn={8} fadeOut={8}>
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
            fontSize={40}
            position="top"
            delay={5}
          />
        </FadeTransition>
      </Sequence>

      {/* === THE TWIST: Adventure panels === */}
      <Sequence from={540} durationInFrames={160}>
        <FadeTransition durationInFrames={160} fadeIn={8} fadeOut={8}>
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
            fontSize={44}
            color={COLORS.dinoGreen}
            position="top"
            delay={5}
          />
        </FadeTransition>
      </Sequence>

      {/* === 3D MODEL SHOWCASE === */}
      <Sequence from={690} durationInFrames={190}>
        <FadeTransition durationInFrames={190} fadeIn={10} fadeOut={10}>
          <ModelShowcase
            durationInFrames={190}
            models={[
              {src: MODELS_3D.gabeFront, label: 'Gabe - 3D Model'},
              {src: MODELS_3D.ninaFront, label: 'Nina - 3D Model'},
              {src: MODELS_3D.miaFront, label: 'Mia - 3D Model'},
              {src: MODELS_3D.leoFront, label: 'Leo - 3D Model'},
            ]}
          />
        </FadeTransition>
      </Sequence>

      {/* === AI PIPELINE TEXT === */}
      <Sequence from={870} durationInFrames={160}>
        <FadeTransition durationInFrames={160} fadeIn={10} fadeOut={10}>
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
              fontSize={72}
              position="top"
              delay={0}
              subtitle="Gemini | Remotion | Blender | Meshy"
            />
            <TextOverlay
              text="Every frame. Every model. Every scene."
              fontSize={36}
              color={COLORS.magicBlue}
              position="bottom"
              delay={20}
            />
          </AbsoluteFill>
        </FadeTransition>
      </Sequence>

      {/* === RUBEN + JETPLANE REVEAL === */}
      <Sequence from={1020} durationInFrames={160}>
        <FadeTransition durationInFrames={160} fadeIn={10} fadeOut={10}>
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
            fontSize={42}
            position="top"
            delay={5}
          />
        </FadeTransition>
      </Sequence>

      {/* === CALL TO ACTION === */}
      <Sequence from={1170} durationInFrames={180}>
        <FadeTransition durationInFrames={180} fadeIn={12} fadeOut={0}>
          <CallToAction />
        </FadeTransition>
      </Sequence>
    </AbsoluteFill>
  );
};
