import {interpolate, useCurrentFrame} from 'remotion';
import type {CSSProperties, ReactNode} from 'react';

type Props = {
  children: ReactNode;
  durationInFrames: number;
  fadeIn?: number;
  fadeOut?: number;
};

export const FadeTransition: React.FC<Props> = ({
  children,
  durationInFrames,
  fadeIn = 10,
  fadeOut = 10,
}) => {
  const frame = useCurrentFrame();

  const opacity = interpolate(
    frame,
    [0, fadeIn, durationInFrames - fadeOut, durationInFrames],
    [0, 1, 1, 0],
    {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'},
  );

  const style: CSSProperties = {
    opacity,
    width: '100%',
    height: '100%',
    position: 'absolute',
    top: 0,
    left: 0,
  };

  return <div style={style}>{children}</div>;
};
