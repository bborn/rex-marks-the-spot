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

  // Build input/output ranges, ensuring strictly monotonically increasing values
  const inputRange: number[] = [0, fadeIn];
  const outputRange: number[] = [0, 1];

  if (fadeOut > 0) {
    inputRange.push(durationInFrames - fadeOut, durationInFrames);
    outputRange.push(1, 0);
  }

  const opacity = interpolate(frame, inputRange, outputRange, {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

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
