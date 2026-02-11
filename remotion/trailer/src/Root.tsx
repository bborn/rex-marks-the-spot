import {Composition} from 'remotion';
import {Trailer} from './Trailer';

// 45 seconds at 30fps = 1350 frames
const FPS = 30;
const DURATION_SECONDS = 45;

export const Root: React.FC = () => {
  return (
    <>
      <Composition
        id="Trailer"
        component={Trailer}
        durationInFrames={FPS * DURATION_SECONDS}
        fps={FPS}
        width={1920}
        height={1080}
      />
    </>
  );
};
