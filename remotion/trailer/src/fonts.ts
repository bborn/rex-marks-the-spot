import {continueRender, delayRender} from 'remotion';

// Load Google Fonts for the trailer
// Bangers: Fun, bold heading font (movie poster style)
// Quicksand: Rounded, friendly subheading font
// Inter: Clean body/label font
export const loadFont = () => {
  const fonts = [
    {
      family: 'Bangers',
      url: 'https://fonts.googleapis.com/css2?family=Bangers&display=swap',
    },
    {
      family: 'Quicksand',
      url: 'https://fonts.googleapis.com/css2?family=Quicksand:wght@500;600;700&display=swap',
    },
    {
      family: 'Inter',
      url: 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap',
    },
  ];

  for (const font of fonts) {
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = font.url;
    document.head.appendChild(link);

    const waitHandle = delayRender(`Loading font: ${font.family}`);
    const checkFont = () => {
      if (document.fonts.check(`16px "${font.family}"`)) {
        continueRender(waitHandle);
      } else {
        requestAnimationFrame(checkFont);
      }
    };
    checkFont();
  }
};
