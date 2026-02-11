import {Img, interpolate, useCurrentFrame, spring, useVideoConfig} from 'remotion';
import type {CSSProperties} from 'react';
import {COLORS, overlayText} from '../styles';

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

  const containerStyle: CSSProperties = {
    width: '100%',
    height: '100%',
    position: 'absolute',
    background: `linear-gradient(180deg, #0d0d2b 0%, #1a0a3e 50%, #0d0d2b 100%)`,
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    alignItems: 'center',
  };

  return (
    <div style={containerStyle}>
      <div
        style={{
          ...overlayText,
          fontSize: 32,
          color: COLORS.magicBlue,
          marginBottom: 20,
          opacity: 0.8,
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
          transform: `scale(${entryScale})`,
          opacity,
          filter: 'drop-shadow(0 8px 40px rgba(74,144,217,0.3))',
          borderRadius: 12,
        }}
      />
      <div
        style={{
          ...overlayText,
          fontSize: 28,
          color: COLORS.warmGold,
          marginTop: 20,
          opacity,
        }}
      >
        {models[activeIndex].label}
      </div>
    </div>
  );
};
