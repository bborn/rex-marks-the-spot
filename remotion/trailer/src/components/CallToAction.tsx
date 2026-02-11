import {interpolate, useCurrentFrame, spring, useVideoConfig} from 'remotion';
import type {CSSProperties} from 'react';
import {COLORS, overlayText} from '../styles';

export const CallToAction: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const mainScale = spring({
    frame,
    fps,
    config: {damping: 12, stiffness: 150},
  });

  const buttonOpacity = interpolate(frame, [20, 35], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const pulseScale = 1 + 0.03 * Math.sin(frame * 0.15);

  const containerStyle: CSSProperties = {
    width: '100%',
    height: '100%',
    position: 'absolute',
    background: `radial-gradient(ellipse at center, ${COLORS.deepPurple} 0%, #000 80%)`,
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 30,
  };

  return (
    <div style={containerStyle}>
      <div
        style={{
          ...overlayText,
          fontSize: 64,
          fontWeight: 900,
          color: COLORS.white,
          transform: `scale(${mainScale})`,
        }}
      >
        Follow the Journey
      </div>
      <div
        style={{
          ...overlayText,
          fontSize: 32,
          color: COLORS.warmGold,
          opacity: buttonOpacity,
        }}
      >
        Made entirely with AI
      </div>
      <div
        style={{
          opacity: buttonOpacity,
          transform: `scale(${pulseScale})`,
          padding: '16px 48px',
          borderRadius: 50,
          background: `linear-gradient(135deg, ${COLORS.fairyPink}, ${COLORS.magicBlue})`,
          marginTop: 20,
        }}
      >
        <div
          style={{
            ...overlayText,
            fontSize: 36,
            fontWeight: 700,
          }}
        >
          SUBSCRIBE
        </div>
      </div>
      <div
        style={{
          ...overlayText,
          fontSize: 24,
          color: 'rgba(255,255,255,0.6)',
          opacity: buttonOpacity,
          marginTop: 10,
        }}
      >
        rexmarksthespot.com
      </div>
    </div>
  );
};
