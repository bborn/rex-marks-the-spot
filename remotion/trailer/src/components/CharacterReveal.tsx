import {Img, interpolate, useCurrentFrame, spring, useVideoConfig} from 'remotion';
import type {CSSProperties} from 'react';
import {COLORS, overlayText} from '../styles';

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

        const cardStyle: CSSProperties = {
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          opacity,
          transform: `translateY(${translateY}px)`,
          flex: 1,
          maxWidth: 280,
        };

        const imgStyle: CSSProperties = {
          width: '100%',
          height: 400,
          objectFit: 'contain',
          borderRadius: 16,
          filter: 'drop-shadow(0 8px 32px rgba(0,0,0,0.5))',
        };

        return (
          <div key={char.name} style={cardStyle}>
            <Img src={char.src} style={imgStyle} />
            <div
              style={{
                ...overlayText,
                fontSize: 28,
                marginTop: 16,
                color: COLORS.warmGold,
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
