import {Img, interpolate, useCurrentFrame, spring, useVideoConfig} from 'remotion';
import type {CSSProperties} from 'react';
import {COLORS, TYPE_SCALE} from '../styles';

type ModelImage = {
  src: string;
  label: string;
};

type Props = {
  models: ModelImage[];
  durationInFrames: number;
};

export const ModelShowcase: React.FC<Props> = ({models, durationInFrames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const framesPerModel = Math.floor(durationInFrames / models.length);

  const activeIndex = Math.min(
    Math.floor(frame / framesPerModel),
    models.length - 1,
  );
  const modelFrame = frame - activeIndex * framesPerModel;

  const entryScale = spring({
    frame: modelFrame,
    fps,
    config: {damping: 12, stiffness: 160},
  });

  const opacity = interpolate(modelFrame, [0, 6], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  // Subtle rotation for 3D feel
  const rotateY = interpolate(modelFrame, [0, framesPerModel], [-3, 3]);

  const containerStyle: CSSProperties = {
    width: '100%',
    height: '100%',
    position: 'absolute',
    background: `linear-gradient(180deg, #0d0d2b 0%, #1a0a3e 50%, #0d0d2b 100%)`,
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
    overflow: 'hidden',
  };

  return (
    <div style={containerStyle}>
      {/* Rotating glow ring behind model */}
      <div
        style={{
          position: 'absolute',
          width: 500,
          height: 500,
          borderRadius: '50%',
          border: `2px solid ${COLORS.magicBlue}30`,
          transform: `rotate(${frame * 0.5}deg)`,
          opacity: 0.3,
        }}
      />
      <div
        style={{
          ...TYPE_SCALE.body,
          color: COLORS.magicBlue,
          marginBottom: 20,
          opacity: 0.8,
          position: 'relative',
          zIndex: 1,
        }}
      >
        From 2D to 3D
      </div>
      <Img
        src={models[activeIndex].src}
        style={{
          maxWidth: 700,
          maxHeight: 600,
          objectFit: 'contain',
          transform: `scale(${entryScale}) perspective(800px) rotateY(${rotateY}deg)`,
          opacity,
          filter: 'drop-shadow(0 8px 40px rgba(74,144,217,0.3))',
          borderRadius: 12,
          position: 'relative',
          zIndex: 1,
        }}
      />
      <div
        style={{
          ...TYPE_SCALE.label,
          color: COLORS.warmGold,
          marginTop: 20,
          opacity,
          textShadow: '0 2px 10px rgba(0,0,0,0.6)',
          position: 'relative',
          zIndex: 1,
        }}
      >
        {models[activeIndex].label}
      </div>
    </div>
  );
};
