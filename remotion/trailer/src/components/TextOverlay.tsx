import {interpolate, useCurrentFrame, spring, useVideoConfig} from 'remotion';
import type {CSSProperties} from 'react';
import {overlayText, COLORS} from '../styles';

type Props = {
  text: string;
  fontSize?: number;
  color?: string;
  position?: 'center' | 'bottom' | 'top';
  delay?: number;
  subtitle?: string;
};

export const TextOverlay: React.FC<Props> = ({
  text,
  fontSize = 72,
  color = COLORS.white,
  position = 'center',
  delay = 0,
  subtitle,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const scale = spring({
    frame: frame - delay,
    fps,
    config: {damping: 12, stiffness: 200},
  });

  const opacity = interpolate(frame - delay, [0, 8], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const positionStyles: Record<string, CSSProperties> = {
    center: {
      top: '50%',
      left: '50%',
      transform: `translate(-50%, -50%) scale(${scale})`,
    },
    bottom: {
      bottom: '12%',
      left: '50%',
      transform: `translateX(-50%) scale(${scale})`,
    },
    top: {
      top: '12%',
      left: '50%',
      transform: `translateX(-50%) scale(${scale})`,
    },
  };

  return (
    <div
      style={{
        position: 'absolute',
        ...positionStyles[position],
        opacity,
        zIndex: 10,
      }}
    >
      <div
        style={{
          ...overlayText,
          fontSize,
          color,
          whiteSpace: 'nowrap',
        }}
      >
        {text}
      </div>
      {subtitle && (
        <div
          style={{
            ...overlayText,
            fontSize: fontSize * 0.45,
            color: COLORS.warmGold,
            marginTop: 12,
            whiteSpace: 'nowrap',
          }}
        >
          {subtitle}
        </div>
      )}
    </div>
  );
};
