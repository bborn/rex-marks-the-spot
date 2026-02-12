import {interpolate, useCurrentFrame} from 'remotion';
import type {CSSProperties, ReactNode} from 'react';

type Props = {
  children: ReactNode;
  durationInFrames: number;
  fadeIn?: number;
  fadeOut?: number;
  // Scale from/to values for entrance/exit
  scaleIn?: number;
  scaleOut?: number;
  // Blur amount for entrance/exit (px)
  blurIn?: number;
  blurOut?: number;
};

export const ScaleBlurTransition: React.FC<Props> = ({
  children,
  durationInFrames,
  fadeIn = 12,
  fadeOut = 12,
  scaleIn = 0.92,
  scaleOut = 1.05,
  blurIn = 8,
  blurOut = 4,
}) => {
  const frame = useCurrentFrame();

  // Opacity
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

  // Scale: zoom in from scaleIn -> 1, then 1 -> scaleOut
  const scaleEntrance = interpolate(frame, [0, fadeIn], [scaleIn, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const scaleExit = fadeOut > 0
    ? interpolate(frame, [durationInFrames - fadeOut, durationInFrames], [1, scaleOut], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 1;
  const scale = frame < fadeIn ? scaleEntrance : scaleExit;

  // Blur: blurry -> clear on entrance, clear -> blurry on exit
  const blurEntrance = interpolate(frame, [0, fadeIn], [blurIn, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const blurExit = fadeOut > 0
    ? interpolate(frame, [durationInFrames - fadeOut, durationInFrames], [0, blurOut], {
        extrapolateLeft: 'clamp',
        extrapolateRight: 'clamp',
      })
    : 0;
  const blur = frame < fadeIn ? blurEntrance : blurExit;

  const style: CSSProperties = {
    opacity,
    transform: `scale(${scale})`,
    filter: blur > 0.1 ? `blur(${blur}px)` : undefined,
    width: '100%',
    height: '100%',
    position: 'absolute',
    top: 0,
    left: 0,
  };

  return <div style={style}>{children}</div>;
};
