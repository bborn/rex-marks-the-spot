import {interpolate, useCurrentFrame} from 'remotion';
import type {CSSProperties, ReactNode} from 'react';

type SlideDirection = 'left' | 'right' | 'up' | 'down';

type Props = {
  children: ReactNode;
  durationInFrames: number;
  fadeIn?: number;
  fadeOut?: number;
  direction?: SlideDirection;
  distance?: number;
};

export const SlideTransition: React.FC<Props> = ({
  children,
  durationInFrames,
  fadeIn = 12,
  fadeOut = 12,
  direction = 'left',
  distance = 80,
}) => {
  const frame = useCurrentFrame();

  const opacityIn = interpolate(frame, [0, fadeIn], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const opacityOut = fadeOut > 0
    ? interpolate(frame, [durationInFrames - fadeOut, durationInFrames], [1, 0], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 1;
  const opacity = Math.min(opacityIn, opacityOut);

  // Slide entrance
  const slideIn = interpolate(frame, [0, fadeIn], [distance, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const slideOut = fadeOut > 0
    ? interpolate(frame, [durationInFrames - fadeOut, durationInFrames], [0, -distance], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 0;

  const slideAmount = frame < fadeIn ? slideIn : slideOut;

  const translateMap: Record<SlideDirection, string> = {
    left: `translateX(${slideAmount}px)`,
    right: `translateX(${-slideAmount}px)`,
    up: `translateY(${slideAmount}px)`,
    down: `translateY(${-slideAmount}px)`,
  };

  const style: CSSProperties = {
    opacity,
    transform: translateMap[direction],
    width: '100%',
    height: '100%',
    position: 'absolute',
    top: 0,
    left: 0,
  };

  return <div style={style}>{children}</div>;
};
