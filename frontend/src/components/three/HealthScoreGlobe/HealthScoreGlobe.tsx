'use client';

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sphere, Html, Float, MeshDistortMaterial } from '@react-three/drei';
import * as THREE from 'three';
import { Scene } from '../shared/Scene';
import { getGrade, getScoreColor } from '@/lib/utils';

interface HealthScoreGlobeProps {
  score: number;
  components?: Array<{
    name: string;
    score: number;
    weight: number;
  }>;
  size?: number;
  interactive?: boolean;
  className?: string;
}

// Orbiting particles showing component scores
function ComponentOrbit({
  components,
  radius,
}: {
  components: HealthScoreGlobeProps['components'];
  radius: number;
}) {
  const groupRef = useRef<THREE.Group>(null);

  useFrame(({ clock }) => {
    if (groupRef.current) {
      groupRef.current.rotation.y = clock.getElapsedTime() * 0.1;
    }
  });

  if (!components) return null;

  return (
    <group ref={groupRef}>
      {components.map((component, i) => {
        const angle = (i / components.length) * Math.PI * 2;
        const x = Math.cos(angle) * radius;
        const z = Math.sin(angle) * radius;
        const y = Math.sin(angle * 2) * 0.3;
        const componentColor = getScoreColor(component.score);

        return (
          <group key={component.name} position={[x, y, z]}>
            {/* Glowing orb */}
            <mesh>
              <sphereGeometry args={[0.12, 16, 16]} />
              <meshStandardMaterial
                color={componentColor}
                emissive={componentColor}
                emissiveIntensity={0.5}
              />
            </mesh>

            {/* Label */}
            <Html
              position={[0, 0.3, 0]}
              center
              distanceFactor={8}
              style={{ pointerEvents: 'none' }}
            >
              <div className="bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm rounded-lg px-2 py-1 shadow-lg text-xs whitespace-nowrap border border-gray-200 dark:border-gray-700">
                <div className="font-medium text-gray-900 dark:text-gray-100">{component.name}</div>
                <div className="text-gray-500 dark:text-gray-400">{component.score}%</div>
              </div>
            </Html>
          </group>
        );
      })}
    </group>
  );
}

// Particle field around the globe
function ParticleField({ count = 400, color }: { count?: number; color: string }) {
  const particlesRef = useRef<THREE.Points>(null);

  const positions = useMemo(() => {
    const pos = new Float32Array(count * 3);
    for (let i = 0; i < count; i++) {
      const theta = Math.random() * Math.PI * 2;
      const phi = Math.acos(2 * Math.random() - 1);
      const r = 2 + Math.random() * 1;

      pos[i * 3] = r * Math.sin(phi) * Math.cos(theta);
      pos[i * 3 + 1] = r * Math.sin(phi) * Math.sin(theta);
      pos[i * 3 + 2] = r * Math.cos(phi);
    }
    return pos;
  }, [count]);

  useFrame(({ clock }) => {
    if (particlesRef.current) {
      particlesRef.current.rotation.y = clock.getElapsedTime() * 0.02;
      particlesRef.current.rotation.x = Math.sin(clock.getElapsedTime() * 0.1) * 0.1;
    }
  });

  return (
    <points ref={particlesRef}>
      <bufferGeometry>
        <bufferAttribute
          attach="attributes-position"
          args={[positions, 3]}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.02}
        color={color}
        transparent
        opacity={0.6}
        sizeAttenuation
        blending={THREE.AdditiveBlending}
      />
    </points>
  );
}

// Main globe component
function Globe({
  score,
  components,
}: Omit<HealthScoreGlobeProps, 'className' | 'size' | 'interactive'>) {
  const meshRef = useRef<THREE.Mesh>(null);
  const color = getScoreColor(score);
  const grade = getGrade(score);

  // Gentle rotation and pulse
  useFrame(({ clock }) => {
    if (meshRef.current) {
      meshRef.current.rotation.y = clock.getElapsedTime() * 0.1;
      // Subtle breathing effect
      const scale = 1 + Math.sin(clock.getElapsedTime() * 2) * 0.02;
      meshRef.current.scale.setScalar(scale);
    }
  });

  return (
    <group>
      {/* Main sphere with distortion */}
      <Float speed={2} rotationIntensity={0.2} floatIntensity={0.3}>
        <Sphere ref={meshRef} args={[1.2, 64, 64]}>
          <MeshDistortMaterial
            color={color}
            metalness={0.4}
            roughness={0.3}
            emissive={color}
            emissiveIntensity={0.15}
            distort={0.2}
            speed={2}
          />
        </Sphere>
      </Float>

      {/* Inner glow sphere */}
      <Sphere args={[1.15, 32, 32]}>
        <meshStandardMaterial
          color={color}
          transparent
          opacity={0.3}
          emissive={color}
          emissiveIntensity={0.5}
        />
      </Sphere>

      {/* Particle field */}
      <ParticleField color={color} />

      {/* Component orbits */}
      <ComponentOrbit components={components} radius={2.2} />

      {/* Center score display */}
      <Html center position={[0, 0, 0]} style={{ pointerEvents: 'none' }}>
        <div className="text-center select-none">
          <div
            className="text-7xl font-bold drop-shadow-[0_2px_10px_rgba(0,0,0,0.3)]"
            style={{ color: '#ffffff' }}
          >
            {score}
          </div>
          <div
            className="text-2xl font-semibold drop-shadow-md"
            style={{ color }}
          >
            Grade {grade}
          </div>
        </div>
      </Html>
    </group>
  );
}

export function HealthScoreGlobe({
  score,
  components,
  size = 400,
  className,
}: HealthScoreGlobeProps) {
  return (
    <div className={className} style={{ width: size, height: size }}>
      <Scene
        className="w-full h-full"
        camera={{ position: [0, 0, 5], fov: 45 }}
        bloom
      >
        <Globe score={score} components={components} />
      </Scene>
    </div>
  );
}
