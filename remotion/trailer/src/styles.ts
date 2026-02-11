import type {CSSProperties} from 'react';

export const fullScreen: CSSProperties = {
  width: '100%',
  height: '100%',
  position: 'absolute',
  top: 0,
  left: 0,
};

export const centered: CSSProperties = {
  display: 'flex',
  justifyContent: 'center',
  alignItems: 'center',
  width: '100%',
  height: '100%',
};

export const overlayText: CSSProperties = {
  fontFamily: "'Arial Black', 'Helvetica Neue', Arial, sans-serif",
  color: 'white',
  textShadow: '0 4px 20px rgba(0,0,0,0.8), 0 2px 4px rgba(0,0,0,0.6)',
  textAlign: 'center' as const,
  lineHeight: 1.2,
};

export const COLORS = {
  deepPurple: '#1a0a2e',
  magicBlue: '#4a90d9',
  fairyPink: '#e91e8c',
  dinoGreen: '#4caf50',
  warmGold: '#ffd700',
  white: '#ffffff',
  softBlack: '#1a1a2e',
};
