'use client';

import { Canvas } from '@react-three/fiber';
import { Suspense, ReactNode } from 'react';
import {
  Environment,
  Preload,
  AdaptiveDpr,
  AdaptiveEvents,
  PerformanceMonitor,
} from '@react-three/drei';
import { EffectComposer, Bloom, Vignette } from '@react-three/postprocessing';

interface SceneProps {
  children: ReactNode;
  className?: string;
  camera?: {
    position?: [number, number, number];
    fov?: number;
  };
  environment?: 'studio' | 'sunset' | 'dawn' | 'night' | 'apartment';
  bloom?: boolean;
  vignette?: boolean;
  background?: string;
}

function SceneContent({
  children,
  environment,
  bloom,
  vignette,
}: Pick<SceneProps, 'children' | 'environment' | 'bloom' | 'vignette'>) {
  return (
    <>
      {/* Lighting */}
      <ambientLight intensity={0.4} />
      <pointLight position={[10, 10, 10]} intensity={0.8} />
      <pointLight position={[-10, -10, -10]} intensity={0.3} color="#14B8A6" />

      {/* Content */}
      {children}

      {/* Environment */}
      {environment && <Environment preset={environment} />}

      {/* Post-processing */}
      {bloom && !vignette && (
        <EffectComposer>
          <Bloom
            luminanceThreshold={0.6}
            luminanceSmoothing={0.9}
            intensity={0.4}
          />
        </EffectComposer>
      )}
      {vignette && !bloom && (
        <EffectComposer>
          <Vignette offset={0.5} darkness={0.5} />
        </EffectComposer>
      )}
      {bloom && vignette && (
        <EffectComposer>
          <Bloom
            luminanceThreshold={0.6}
            luminanceSmoothing={0.9}
            intensity={0.4}
          />
          <Vignette offset={0.5} darkness={0.5} />
        </EffectComposer>
      )}

      <Preload all />
    </>
  );
}

export function Scene({
  children,
  className,
  camera = { position: [0, 0, 5], fov: 50 },
  environment,
  bloom = false,
  vignette = false,
  background = 'transparent',
}: SceneProps) {
  return (
    <div className={className}>
      <Canvas
        camera={{ position: camera.position, fov: camera.fov }}
        dpr={[1, 2]}
        gl={{
          antialias: true,
          alpha: background === 'transparent',
          powerPreference: 'high-performance',
        }}
        style={{ background }}
      >
        <Suspense fallback={null}>
          <AdaptiveDpr pixelated />
          <AdaptiveEvents />
          <PerformanceMonitor>
            <SceneContent
              environment={environment}
              bloom={bloom}
              vignette={vignette}
            >
              {children}
            </SceneContent>
          </PerformanceMonitor>
        </Suspense>
      </Canvas>
    </div>
  );
}
