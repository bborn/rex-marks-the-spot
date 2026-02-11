import {Img, interpolate, useCurrentFrame, spring, useVideoConfig} from 'remotion';
import type {CSSProperties} from 'react';
import {COLORS, TYPE_SCALE} from '../styles';

type Character = {
  name: string;
  src: string;
  label: string;
};

type Props = {
  characters: Character[];
  durationInFrames: number;
};

export const CharacterReveal: React.FC<Props> = ({
  characters,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const framesPerChar = Math.floor(durationInFrames / characters.length);

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        position: 'absolute',
        background: `linear-gradient(135deg, ${COLORS.deepPurple} 0%, ${COLORS.softBlack} 100%)`,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        gap: 40,
        padding: '60px 80px',
      }}
    >
      {characters.map((char, i) => {
        const charFrame = frame - i * framesPerChar;
        const entered = charFrame > 0;

        const entryProgress = entered
          ? spring({
              frame: charFrame,
              fps,
              config: {damping: 14, stiffness: 180},
            })
          : 0;

        const opacity = interpolate(charFrame, [0, 8], [0, 1], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });

        const translateY = interpolate(entryProgress, [0, 1], [60, 0]);

        // Subtle glow behind each character
        const glowOpacity = interpolate(charFrame, [0, 20], [0, 0.4], {
          extrapolateLeft: 'clamp',
          extrapolateRight: 'clamp',
        });

        const cardStyle: CSSProperties = {
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          opacity,
          transform: `translateY(${translateY}px)`,
          flex: 1,
          maxWidth: 280,
          position: 'relative',
        };

        const imgStyle: CSSProperties = {
          width: '100%',
          height: 400,
          objectFit: 'contain',
          borderRadius: 16,
          filter: 'drop-shadow(0 8px 32px rgba(0,0,0,0.5))',
          position: 'relative',
          zIndex: 1,
        };

        return (
          <div key={char.name} style={cardStyle}>
            {/* Glow behind character */}
            <div
              style={{
                position: 'absolute',
                top: '30%',
                width: 200,
                height: 200,
                borderRadius: '50%',
                background: `radial-gradient(circle, ${COLORS.magicBlue}40, transparent 70%)`,
                opacity: glowOpacity,
                filter: 'blur(30px)',
                zIndex: 0,
              }}
            />
            <Img src={char.src} style={imgStyle} />
            <div
              style={{
                ...TYPE_SCALE.label,
                marginTop: 16,
                color: COLORS.warmGold,
                textShadow: '0 2px 10px rgba(0,0,0,0.6)',
                position: 'relative',
                zIndex: 1,
              }}
            >
              {char.label}
            </div>
          </div>
        );
      })}
    </div>
  );
};
