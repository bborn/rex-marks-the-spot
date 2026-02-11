import {interpolate, useCurrentFrame, spring, useVideoConfig} from 'remotion';
import type {CSSProperties} from 'react';
import {COLORS, TYPE_SCALE, FONTS} from '../styles';

type TextStyle = 'heading' | 'subheading' | 'body' | 'label' | 'hero';

type Props = {
  text: string;
  fontSize?: number;
  color?: string;
  position?: 'center' | 'bottom' | 'top';
  delay?: number;
  subtitle?: string;
  textStyle?: TextStyle;
};

export const TextOverlay: React.FC<Props> = ({
  text,
  fontSize,
  color = COLORS.white,
  position = 'center',
  delay = 0,
  subtitle,
  textStyle = 'heading',
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

  const typeStyle = TYPE_SCALE[textStyle];

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
          fontFamily: typeStyle.fontFamily,
          fontWeight: typeStyle.fontWeight,
          letterSpacing: typeStyle.letterSpacing,
          fontSize: fontSize ?? typeStyle.fontSize,
          color,
          textShadow: '0 4px 20px rgba(0,0,0,0.8), 0 2px 4px rgba(0,0,0,0.6)',
          textAlign: 'center' as const,
          lineHeight: typeStyle.lineHeight,
          whiteSpace: 'nowrap',
        }}
      >
        {text}
      </div>
      {subtitle && (
        <div
          style={{
            fontFamily: FONTS.body,
            fontWeight: 500,
            letterSpacing: '0.08em',
            fontSize: (fontSize ?? typeStyle.fontSize) * 0.45,
            color: COLORS.warmGold,
            textShadow: '0 2px 10px rgba(0,0,0,0.6)',
            textAlign: 'center' as const,
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
