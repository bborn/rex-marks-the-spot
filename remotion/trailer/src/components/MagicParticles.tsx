import {interpolate, useCurrentFrame} from 'remotion';
import type {CSSProperties} from 'react';
import {COLORS} from '../styles';

type Props = {
  count?: number;
  color?: string;
  durationInFrames: number;
};

// Deterministic pseudo-random based on seed
const seededRandom = (seed: number) => {
  const x = Math.sin(seed * 12.9898 + seed * 78.233) * 43758.5453;
  return x - Math.floor(x);
};

export const MagicParticles: React.FC<Props> = ({
  count = 20,
  color = COLORS.warmGold,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();

  const overallOpacity = interpolate(
    frame,
    [0, 10, durationInFrames - 10, durationInFrames],
    [0, 1, 1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );

  const particles = Array.from({length: count}, (_, i) => {
    const seed = i;
    const startX = seededRandom(seed) * 100;
    const startY = seededRandom(seed + 100) * 100;
    const size = 2 + seededRandom(seed + 200) * 4;
    const speed = 0.3 + seededRandom(seed + 300) * 0.7;
    const phase = seededRandom(seed + 400) * Math.PI * 2;

    const x = startX + Math.sin(frame * 0.02 * speed + phase) * 8;
    const y = startY - (frame * speed * 0.3) % 110;
    const particleOpacity = 0.3 + Math.sin(frame * 0.1 + phase) * 0.3;

    const style: CSSProperties = {
      position: 'absolute',
      left: `${x}%`,
      top: `${((y % 110) + 110) % 110}%`,
      width: size,
      height: size,
      borderRadius: '50%',
      backgroundColor: color,
      opacity: particleOpacity,
      boxShadow: `0 0 ${size * 2}px ${color}`,
      pointerEvents: 'none',
    };

    return <div key={i} style={style} />;
  });

  return (
    <div
      style={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        opacity: overallOpacity,
        pointerEvents: 'none',
        zIndex: 5,
        overflow: 'hidden',
      }}
    >
      {particles}
    </div>
  );
};
