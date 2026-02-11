import {
  interpolate,
  useCurrentFrame,
  spring,
  useVideoConfig,
  Img,
} from 'remotion';
import type {CSSProperties} from 'react';
import {COLORS, overlayText} from '../styles';
import {PROMO} from '../assets';

type Props = {
  showLogo?: boolean;
};

export const TitleCard: React.FC<Props> = ({showLogo = true}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const titleScale = spring({
    frame,
    fps,
    config: {damping: 10, stiffness: 120, mass: 0.8},
  });

  const subtitleOpacity = interpolate(frame, [15, 30], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const glowIntensity = interpolate(
    Math.sin(frame * 0.1),
    [-1, 1],
    [20, 40],
  );

  const containerStyle: CSSProperties = {
    width: '100%',
    height: '100%',
    position: 'absolute',
    background: `radial-gradient(ellipse at center, ${COLORS.deepPurple} 0%, #000 80%)`,
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
  };

  return (
    <div style={containerStyle}>
      {showLogo && (
        <Img
          src={PROMO.titleCard}
          style={{
            width: 800,
            objectFit: 'contain',
            transform: `scale(${titleScale})`,
            filter: `drop-shadow(0 0 ${glowIntensity}px ${COLORS.warmGold})`,
            marginBottom: 20,
          }}
        />
      )}
      <div
        style={{
          ...overlayText,
          fontSize: 96,
          fontWeight: 900,
          color: COLORS.white,
          transform: `scale(${titleScale})`,
          textShadow: `0 0 ${glowIntensity}px ${COLORS.fairyPink}, 0 4px 20px rgba(0,0,0,0.8)`,
          display: showLogo ? 'none' : 'block',
        }}
      >
        Fairy Dinosaur Date Night
      </div>
      <div
        style={{
          ...overlayText,
          fontSize: 36,
          color: COLORS.warmGold,
          opacity: subtitleOpacity,
          marginTop: 10,
        }}
      >
        An AI-Animated Movie
      </div>
    </div>
  );
};
