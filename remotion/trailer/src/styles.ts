import type {CSSProperties} from 'react';

// Google Fonts loaded via loadFont() in Root.tsx
// Heading: Bangers - bold, fun, movie-poster feel
// Subheading: Quicksand - rounded, friendly, modern
// Body: Inter - clean, highly readable

export const FONTS = {
  heading: "'Bangers', 'Impact', sans-serif",
  subheading: "'Quicksand', 'Nunito', sans-serif",
  body: "'Inter', 'Helvetica Neue', Arial, sans-serif",
};

export const TYPE_SCALE = {
  // Hero titles (movie title, section headers)
  hero: {
    fontFamily: FONTS.heading,
    fontSize: 96,
    fontWeight: 400, // Bangers is already bold
    letterSpacing: '0.04em',
    lineHeight: 1.1,
  },
  // Section headings
  heading: {
    fontFamily: FONTS.heading,
    fontSize: 64,
    fontWeight: 400,
    letterSpacing: '0.03em',
    lineHeight: 1.15,
  },
  // Subheadings and scene text
  subheading: {
    fontFamily: FONTS.subheading,
    fontSize: 44,
    fontWeight: 700,
    letterSpacing: '0.01em',
    lineHeight: 1.2,
  },
  // Body text / descriptive
  body: {
    fontFamily: FONTS.subheading,
    fontSize: 36,
    fontWeight: 600,
    letterSpacing: '0.005em',
    lineHeight: 1.3,
  },
  // Labels (character names, small text)
  label: {
    fontFamily: FONTS.body,
    fontSize: 28,
    fontWeight: 600,
    letterSpacing: '0.02em',
    lineHeight: 1.2,
  },
  // Small / caption text
  caption: {
    fontFamily: FONTS.body,
    fontSize: 24,
    fontWeight: 500,
    letterSpacing: '0.01em',
    lineHeight: 1.3,
  },
  // Button text
  button: {
    fontFamily: FONTS.heading,
    fontSize: 40,
    fontWeight: 400,
    letterSpacing: '0.06em',
    lineHeight: 1,
  },
  // Subtitle (tool names, tech stack)
  techLabel: {
    fontFamily: FONTS.body,
    fontSize: 30,
    fontWeight: 500,
    letterSpacing: '0.08em',
    lineHeight: 1.2,
  },
} as const;

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
  fontFamily: FONTS.heading,
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
