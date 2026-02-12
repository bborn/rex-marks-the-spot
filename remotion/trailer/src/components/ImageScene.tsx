import {Img, interpolate, useCurrentFrame} from 'remotion';
import type {CSSProperties} from 'react';
import {fullScreen} from '../styles';

type Props = {
  src: string;
  fit?: 'cover' | 'contain';
  zoom?: boolean;
  panDirection?: 'left' | 'right' | 'none';
  durationInFrames: number;
  backgroundColor?: string;
};

export const ImageScene: React.FC<Props> = ({
  src,
  fit = 'cover',
  zoom = false,
  panDirection = 'none',
  durationInFrames,
  backgroundColor = '#0a0a1a',
}) => {
  const frame = useCurrentFrame();

  const scale = zoom
    ? interpolate(frame, [0, durationInFrames], [1, 1.15], {
        extrapolateRight: 'clamp',
      })
    : 1;

  const translateX =
    panDirection === 'left'
      ? interpolate(frame, [0, durationInFrames], [5, -5])
      : panDirection === 'right'
        ? interpolate(frame, [0, durationInFrames], [-5, 5])
        : 0;

  const containerStyle: CSSProperties = {
    ...fullScreen,
    backgroundColor,
    overflow: 'hidden',
  };

  const imgStyle: CSSProperties = {
    width: '100%',
    height: '100%',
    objectFit: fit,
    transform: `scale(${scale}) translateX(${translateX}%)`,
  };

  return (
    <div style={containerStyle}>
      <Img src={src} style={imgStyle} />
    </div>
  );
};
