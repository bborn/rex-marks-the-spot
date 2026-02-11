import {
  interpolate,
  useCurrentFrame,
  spring,
  useVideoConfig,
  Img,
} from 'remotion';
import type {CSSProperties} from 'react';
import {COLORS, TYPE_SCALE, FONTS} from '../styles';
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

  // Subtle particle/shimmer effect
  const shimmerX = Math.sin(frame * 0.05) * 100;
  const shimmerY = Math.cos(frame * 0.07) * 50;

  const containerStyle: CSSProperties = {
    width: '100%',
    height: '100%',
    position: 'absolute',
    background: `radial-gradient(ellipse at center, ${COLORS.deepPurple} 0%, #000 80%)`,
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
  };

  return (
    <div style={containerStyle}>
      {/* Animated shimmer background */}
      <div
        style={{
          position: 'absolute',
          width: 600,
          height: 600,
          borderRadius: '50%',
          background: `radial-gradient(circle, rgba(233,30,140,0.12) 0%, transparent 70%)`,
          transform: `translate(${shimmerX}px, ${shimmerY}px)`,
          filter: 'blur(60px)',
        }}
      />
      {showLogo && (
        <Img
          src={PROMO.titleCard}
          style={{
            width: 800,
            objectFit: 'contain',
            transform: `scale(${titleScale})`,
            filter: `drop-shadow(0 0 ${glowIntensity}px ${COLORS.warmGold})`,
            marginBottom: 20,
            position: 'relative',
            zIndex: 1,
          }}
        />
      )}
      <div
        style={{
          ...TYPE_SCALE.hero,
          color: COLORS.white,
          transform: `scale(${titleScale})`,
          textShadow: `0 0 ${glowIntensity}px ${COLORS.fairyPink}, 0 4px 20px rgba(0,0,0,0.8)`,
          display: showLogo ? 'none' : 'block',
          position: 'relative',
          zIndex: 1,
        }}
      >
        Fairy Dinosaur Date Night
      </div>
      <div
        style={{
          ...TYPE_SCALE.body,
          fontFamily: FONTS.subheading,
          color: COLORS.warmGold,
          opacity: subtitleOpacity,
          marginTop: 10,
          position: 'relative',
          zIndex: 1,
          textShadow: '0 2px 10px rgba(0,0,0,0.6)',
        }}
      >
        An AI-Animated Movie
      </div>
    </div>
  );
};
