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

  // Which panel is currently showing
  const activeIndex = Math.min(
    Math.floor(frame / framesPerPanel),
    panels.length - 1,
  );

  // Progress within current panel for transition
  const panelFrame = frame - activeIndex * framesPerPanel;
  const opacity = interpolate(panelFrame, [0, 6], [0, 1], {
    extrapolateRight: 'clamp',
  });

  // Gentle zoom on current panel
  const scale = interpolate(
    panelFrame,
    [0, framesPerPanel],
    [1, 1.06],
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
    transform: `scale(${scale})`,
  };

  // Film strip border effect
  const stripStyle: CSSProperties = {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    borderTop: '6px solid rgba(255,215,0,0.3)',
    borderBottom: '6px solid rgba(255,215,0,0.3)',
    pointerEvents: 'none',
    zIndex: 2,
  };

  return (
    <div style={containerStyle}>
      <Img src={panels[activeIndex]} style={imgStyle} />
      <div style={stripStyle} />
    </div>
  );
};
