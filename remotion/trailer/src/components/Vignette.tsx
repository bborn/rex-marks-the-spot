import type {CSSProperties} from 'react';

type Props = {
  intensity?: number; // 0-1
  color?: string;
};

export const Vignette: React.FC<Props> = ({
  intensity = 0.5,
  color = '#000',
}) => {
  const style: CSSProperties = {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    background: `radial-gradient(ellipse at center, transparent 40%, ${color} 100%)`,
    opacity: intensity,
    pointerEvents: 'none',
    zIndex: 4,
  };

  return <div style={style} />;
};
