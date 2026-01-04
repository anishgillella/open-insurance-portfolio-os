'use client';

import { useRef, useMemo } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { Scene } from './shared/Scene';

function GradientMesh() {
  const meshRef = useRef<THREE.Mesh>(null);
  const { pointer } = useThree();

  const shader = useMemo(
    () => ({
      uniforms: {
        uTime: { value: 0 },
        uMouse: { value: new THREE.Vector2(0, 0) },
        uColor1: { value: new THREE.Color('#1677FF') },
        uColor2: { value: new THREE.Color('#10B981') },
        uColor3: { value: new THREE.Color('#F59E0B') },
        uOpacity: { value: 0.06 },
      },
      vertexShader: `
        varying vec2 vUv;
        uniform float uTime;
        uniform vec2 uMouse;

        void main() {
          vUv = uv;
          vec3 pos = position;

          // Gentle wave distortion
          float wave = sin(pos.x * 1.5 + uTime * 0.3) * 0.15;
          wave += sin(pos.y * 1.5 + uTime * 0.2) * 0.15;
          wave += sin((pos.x + pos.y) * 1.0 + uTime * 0.4) * 0.1;
          pos.z += wave;

          // Mouse influence - subtle bulge
          float mouseDist = distance(uv, uMouse * 0.5 + 0.5);
          pos.z += (1.0 - smoothstep(0.0, 0.5, mouseDist)) * 0.3;

          gl_Position = projectionMatrix * modelViewMatrix * vec4(pos, 1.0);
        }
      `,
      fragmentShader: `
        varying vec2 vUv;
        uniform float uTime;
        uniform vec3 uColor1;
        uniform vec3 uColor2;
        uniform vec3 uColor3;
        uniform float uOpacity;

        void main() {
          // Animated gradient mixing
          float t1 = vUv.x + sin(vUv.y * 3.0 + uTime * 0.2) * 0.15;
          float t2 = vUv.y + cos(vUv.x * 2.0 + uTime * 0.15) * 0.1;

          vec3 color = mix(uColor1, uColor2, t1);
          color = mix(color, uColor3, t2 * 0.4);

          gl_FragColor = vec4(color, uOpacity);
        }
      `,
    }),
    []
  );

  useFrame(({ clock }) => {
    if (meshRef.current) {
      const material = meshRef.current.material as THREE.ShaderMaterial;
      material.uniforms.uTime.value = clock.getElapsedTime();
      material.uniforms.uMouse.value.set(pointer.x, pointer.y);
    }
  });

  return (
    <mesh ref={meshRef} position={[0, 0, -3]} scale={[20, 15, 1]}>
      <planeGeometry args={[1, 1, 64, 64]} />
      <shaderMaterial {...shader} transparent depthWrite={false} />
    </mesh>
  );
}

export function GradientMeshBg({ className }: { className?: string }) {
  return (
    <div
      className={className}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: -1,
        pointerEvents: 'none',
      }}
    >
      <Scene camera={{ position: [0, 0, 5] }}>
        <GradientMesh />
      </Scene>
    </div>
  );
}
