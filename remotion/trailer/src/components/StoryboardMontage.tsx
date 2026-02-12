import {Img, interpolate, useCurrentFrame} from 'remotion';
import type {CSSProperties} from 'react';
import {COLORS} from '../styles';

type Props = {
  panels: string[];
  durationInFrames: number;
};

export const StoryboardMontage: React.FC<Props> = ({
  panels,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const framesPerPanel = Math.floor(durationInFrames / panels.length);

  const activeIndex = Math.min(
    Math.floor(frame / framesPerPanel),
    panels.length - 1,
  );

  const panelFrame = frame - activeIndex * framesPerPanel;

  // Slide-in from right with slight rotation
  const slideX = interpolate(panelFrame, [0, 8], [60, 0], {
    extrapolateRight: 'clamp',
  });

  const opacity = interpolate(panelFrame, [0, 6], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Ken Burns: gentle zoom + subtle pan
  const scale = interpolate(
    panelFrame,
    [0, framesPerPanel],
    [1.02, 1.1],
    {extrapolateRight: 'clamp'},
  );

  const panX = interpolate(
    panelFrame,
    [0, framesPerPanel],
    [0, -1.5],
    {extrapolateRight: 'clamp'},
  );

  const containerStyle: CSSProperties = {
    width: '100%',
    height: '100%',
    position: 'absolute',
    backgroundColor: COLORS.softBlack,
    overflow: 'hidden',
  };

  const imgStyle: CSSProperties = {
    width: '100%',
    height: '100%',
    objectFit: 'contain',
    opacity,
    transform: `scale(${scale}) translateX(${slideX + panX}px)`,
  };

  // Panel counter dots
  const dotsStyle: CSSProperties = {
    position: 'absolute',
    bottom: 24,
    left: '50%',
    transform: 'translateX(-50%)',
    display: 'flex',
    gap: 8,
    zIndex: 3,
  };

  return (
    <div style={containerStyle}>
      <Img src={panels[activeIndex]} style={imgStyle} />
      {/* Vignette overlay for visual cohesion */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          background: 'radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.5) 100%)',
          pointerEvents: 'none',
          zIndex: 1,
        }}
      />
      {/* Film strip border */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          borderTop: `4px solid ${COLORS.warmGold}50`,
          borderBottom: `4px solid ${COLORS.warmGold}50`,
          pointerEvents: 'none',
          zIndex: 2,
        }}
      />
      {/* Panel indicator dots */}
      <div style={dotsStyle}>
        {panels.map((_, i) => (
          <div
            key={i}
            style={{
              width: i === activeIndex ? 12 : 6,
              height: 6,
              borderRadius: 3,
              backgroundColor: i === activeIndex ? COLORS.warmGold : 'rgba(255,255,255,0.3)',
              transition: 'width 0.2s',
            }}
          />
        ))}
      </div>
    </div>
  );
};
