import {interpolate, useCurrentFrame, spring, useVideoConfig} from 'remotion';
import type {CSSProperties} from 'react';
import {COLORS, TYPE_SCALE, FONTS} from '../styles';

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

  // Animated gradient background
  const gradientAngle = 135 + Math.sin(frame * 0.02) * 15;

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
    overflow: 'hidden',
  };

  return (
    <div style={containerStyle}>
      {/* Animated glow orbs in background */}
      <div
        style={{
          position: 'absolute',
          width: 400,
          height: 400,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${COLORS.fairyPink}15, transparent 70%)`,
          transform: `translate(${Math.sin(frame * 0.03) * 80}px, ${Math.cos(frame * 0.04) * 60}px)`,
          filter: 'blur(40px)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          width: 300,
          height: 300,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${COLORS.magicBlue}15, transparent 70%)`,
          transform: `translate(${Math.cos(frame * 0.025) * 100}px, ${Math.sin(frame * 0.035) * 80}px)`,
          filter: 'blur(40px)',
        }}
      />
      <div
        style={{
          ...TYPE_SCALE.heading,
          color: COLORS.white,
          transform: `scale(${mainScale})`,
          textShadow: '0 4px 20px rgba(0,0,0,0.8)',
          position: 'relative',
          zIndex: 1,
        }}
      >
        Follow the Journey
      </div>
      <div
        style={{
          ...TYPE_SCALE.body,
          fontFamily: FONTS.subheading,
          color: COLORS.warmGold,
          opacity: buttonOpacity,
          textShadow: '0 2px 10px rgba(0,0,0,0.6)',
          position: 'relative',
          zIndex: 1,
        }}
      >
        Made entirely with AI
      </div>
      <div
        style={{
          opacity: buttonOpacity,
          transform: `scale(${pulseScale})`,
          padding: '16px 56px',
          borderRadius: 50,
          background: `linear-gradient(${gradientAngle}deg, ${COLORS.fairyPink}, ${COLORS.magicBlue})`,
          marginTop: 20,
          boxShadow: `0 0 30px ${COLORS.fairyPink}40, 0 0 60px ${COLORS.magicBlue}20`,
          position: 'relative',
          zIndex: 1,
        }}
      >
        <div
          style={{
            ...TYPE_SCALE.button,
            color: COLORS.white,
            textShadow: '0 2px 8px rgba(0,0,0,0.4)',
          }}
        >
          SUBSCRIBE
        </div>
      </div>
      <div
        style={{
          ...TYPE_SCALE.caption,
          color: 'rgba(255,255,255,0.6)',
          opacity: buttonOpacity,
          marginTop: 10,
          position: 'relative',
          zIndex: 1,
        }}
      >
        rexmarksthespot.com
      </div>
    </div>
  );
};
