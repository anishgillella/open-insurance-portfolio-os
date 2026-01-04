# Three.js Immersive Experiences

Complete guide to building stunning 3D visualizations using React Three Fiber that make Open Insurance feel like a next-generation product.

---

## Philosophy

The 3D elements in Open Insurance aren't decorative—they're **functional visualizations** that communicate complex insurance data in an intuitive, memorable way. Like Apple's product pages, 3D creates emotional impact and differentiates us from every other insurance tool.

### When to Use 3D

| Use Case | Why |
|----------|-----|
| Health Score Globe | The score is THE hero metric—it deserves a hero presentation |
| Property City | Spatial relationships help users understand their portfolio |
| Coverage Shield | Abstract concept (protection) becomes tangible |
| Renewal Timeline | Journey metaphor is more engaging than a list |
| Document Pipeline | Processing feels more real when visualized |

### When NOT to Use 3D

- Data tables (use standard tables)
- Forms and inputs (use standard forms)
- Text-heavy content (3D distracts from reading)
- Mobile-first views (simplify to 2D)

---

## Setup & Dependencies

### Installation

```bash
npm install three @react-three/fiber @react-three/drei @react-three/postprocessing
npm install maath leva # Utilities and dev tools
npm install -D @types/three
```

### Package Versions

```json
{
  "three": "^0.160.0",
  "@react-three/fiber": "^8.15.0",
  "@react-three/drei": "^9.92.0",
  "@react-three/postprocessing": "^2.15.0",
  "maath": "^0.10.0",
  "leva": "^0.9.35"
}
```

---

## Base Scene Component

Every 3D visualization uses this foundation:

```tsx
// components/three/shared/Scene.tsx
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
  controls?: boolean;
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
      <pointLight position={[-10, -10, -10]} intensity={0.3} color="#1677FF" />

      {/* Content */}
      {children}

      {/* Environment */}
      {environment && <Environment preset={environment} />}

      {/* Post-processing */}
      {(bloom || vignette) && (
        <EffectComposer>
          {bloom && (
            <Bloom
              luminanceThreshold={0.6}
              luminanceSmoothing={0.9}
              intensity={0.4}
            />
          )}
          {vignette && <Vignette offset={0.5} darkness={0.5} />}
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
  environment = 'studio',
  bloom = true,
  vignette = false,
  controls = false,
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
```

---

## Health Score Globe

The flagship 3D element. A pulsing sphere that communicates health at a glance.

```tsx
// components/three/HealthScoreGlobe/HealthScoreGlobe.tsx
'use client';

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Sphere, Html, Float, MeshDistortMaterial } from '@react-three/drei';
import * as THREE from 'three';
import { Scene } from '../shared/Scene';

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

// Color based on score
function getScoreColor(score: number): THREE.Color {
  if (score >= 90) return new THREE.Color('#10B981'); // Emerald
  if (score >= 80) return new THREE.Color('#14B8A6'); // Teal
  if (score >= 70) return new THREE.Color('#F59E0B'); // Amber
  if (score >= 60) return new THREE.Color('#F97316'); // Orange
  return new THREE.Color('#EF4444'); // Red
}

function getGrade(score: number): string {
  if (score >= 90) return 'A';
  if (score >= 80) return 'B';
  if (score >= 70) return 'C';
  if (score >= 60) return 'D';
  return 'F';
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
        const y = Math.sin(angle * 2) * 0.3; // Slight wave

        return (
          <group key={component.name} position={[x, y, z]}>
            {/* Glowing orb */}
            <mesh>
              <sphereGeometry args={[0.1, 16, 16]} />
              <meshStandardMaterial
                color={getScoreColor(component.score)}
                emissive={getScoreColor(component.score)}
                emissiveIntensity={0.5}
              />
            </mesh>

            {/* Label */}
            <Html
              position={[0, 0.25, 0]}
              center
              distanceFactor={8}
              style={{ pointerEvents: 'none' }}
            >
              <div className="bg-white/90 backdrop-blur-sm rounded-lg px-2 py-1 shadow-lg text-xs whitespace-nowrap">
                <div className="font-medium text-gray-900">{component.name}</div>
                <div className="text-gray-500">{component.score}%</div>
              </div>
            </Html>
          </group>
        );
      })}
    </group>
  );
}

// Particle field around the globe
function ParticleField({ count = 500, color }: { count?: number; color: THREE.Color }) {
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
          count={count}
          array={positions}
          itemSize={3}
        />
      </bufferGeometry>
      <pointsMaterial
        size={0.015}
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
  interactive,
}: Omit<HealthScoreGlobeProps, 'className' | 'size'>) {
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
          <div className="text-7xl font-bold text-white drop-shadow-[0_2px_10px_rgba(0,0,0,0.3)]">
            {score}
          </div>
          <div
            className="text-2xl font-semibold drop-shadow-md"
            style={{ color: `#${color.getHexString()}` }}
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
  interactive = true,
  className,
}: HealthScoreGlobeProps) {
  return (
    <Scene
      className={className}
      camera={{ position: [0, 0, 5], fov: 45 }}
      bloom
      style={{ width: size, height: size }}
    >
      <Globe score={score} components={components} interactive={interactive} />
    </Scene>
  );
}
```

---

## Property City Visualization

Your portfolio as a 3D cityscape:

```tsx
// components/three/PropertyCity/PropertyCity.tsx
'use client';

import { useRef, useState } from 'react';
import { useFrame, ThreeEvent } from '@react-three/fiber';
import { Html, Float, Text, RoundedBox } from '@react-three/drei';
import * as THREE from 'three';
import { Scene } from '../shared/Scene';

interface Property {
  id: string;
  name: string;
  tiv: number;
  healthScore: number;
  address: string;
}

interface PropertyCityProps {
  properties: Property[];
  onPropertyClick?: (propertyId: string) => void;
  className?: string;
}

function getScoreColor(score: number): string {
  if (score >= 90) return '#10B981';
  if (score >= 80) return '#14B8A6';
  if (score >= 70) return '#F59E0B';
  if (score >= 60) return '#F97316';
  return '#EF4444';
}

function Building({
  property,
  position,
  onClick,
}: {
  property: Property;
  position: [number, number, number];
  onClick?: () => void;
}) {
  const meshRef = useRef<THREE.Mesh>(null);
  const [hovered, setHovered] = useState(false);

  // Height based on TIV (normalized)
  const maxTiv = 50000000; // $50M
  const height = 0.5 + (property.tiv / maxTiv) * 2.5;

  // Color based on health score
  const color = getScoreColor(property.healthScore);

  useFrame(() => {
    if (meshRef.current) {
      // Subtle hover animation
      const targetScale = hovered ? 1.05 : 1;
      meshRef.current.scale.x = THREE.MathUtils.lerp(
        meshRef.current.scale.x,
        targetScale,
        0.1
      );
      meshRef.current.scale.z = THREE.MathUtils.lerp(
        meshRef.current.scale.z,
        targetScale,
        0.1
      );
    }
  });

  return (
    <group position={position}>
      {/* Building */}
      <RoundedBox
        ref={meshRef}
        args={[0.8, height, 0.8]}
        radius={0.05}
        position={[0, height / 2, 0]}
        onClick={onClick}
        onPointerOver={() => setHovered(true)}
        onPointerOut={() => setHovered(false)}
      >
        <meshStandardMaterial
          color={color}
          metalness={0.3}
          roughness={0.5}
          emissive={color}
          emissiveIntensity={hovered ? 0.3 : 0.1}
        />
      </RoundedBox>

      {/* Windows (instanced for performance) */}
      {Array.from({ length: Math.floor(height * 3) }).map((_, i) => (
        <group key={i} position={[0, 0.3 + i * 0.3, 0]}>
          {[-0.2, 0.2].map((x) => (
            <mesh key={x} position={[x, 0, 0.41]}>
              <planeGeometry args={[0.15, 0.15]} />
              <meshStandardMaterial
                color="#FEF3C7"
                emissive="#FEF3C7"
                emissiveIntensity={0.5}
              />
            </mesh>
          ))}
        </group>
      ))}

      {/* Hover label */}
      {hovered && (
        <Html position={[0, height + 0.5, 0]} center>
          <div className="bg-white rounded-xl shadow-xl p-3 min-w-[150px] animate-fade-in">
            <div className="font-semibold text-gray-900">{property.name}</div>
            <div className="text-sm text-gray-500">{property.address}</div>
            <div className="flex items-center justify-between mt-2 text-sm">
              <span className="text-gray-600">
                ${(property.tiv / 1000000).toFixed(1)}M TIV
              </span>
              <span
                className="font-medium"
                style={{ color }}
              >
                {property.healthScore}
              </span>
            </div>
          </div>
        </Html>
      )}
    </group>
  );
}

function Ground() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.01, 0]}>
      <planeGeometry args={[20, 20]} />
      <meshStandardMaterial color="#E5E7EB" />
    </mesh>
  );
}

function City({
  properties,
  onPropertyClick,
}: {
  properties: Property[];
  onPropertyClick?: (id: string) => void;
}) {
  // Arrange buildings in a grid
  const cols = Math.ceil(Math.sqrt(properties.length));

  return (
    <group>
      <Ground />

      {properties.map((property, i) => {
        const row = Math.floor(i / cols);
        const col = i % cols;
        const x = (col - cols / 2) * 1.5 + 0.75;
        const z = (row - Math.ceil(properties.length / cols) / 2) * 1.5 + 0.75;

        return (
          <Building
            key={property.id}
            property={property}
            position={[x, 0, z]}
            onClick={() => onPropertyClick?.(property.id)}
          />
        );
      })}
    </group>
  );
}

export function PropertyCity({
  properties,
  onPropertyClick,
  className,
}: PropertyCityProps) {
  return (
    <Scene
      className={className}
      camera={{ position: [5, 5, 5], fov: 50 }}
      bloom
      controls
    >
      <City properties={properties} onPropertyClick={onPropertyClick} />
    </Scene>
  );
}
```

---

## Coverage Shield Visualization

Abstract concept of protection made tangible:

```tsx
// components/three/CoverageShield/CoverageShield.tsx
'use client';

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html } from '@react-three/drei';
import * as THREE from 'three';
import { Scene } from '../shared/Scene';

interface Gap {
  id: string;
  type: string;
  severity: 'critical' | 'warning' | 'info';
  title: string;
}

interface CoverageShieldProps {
  coveragePercentage: number;
  gaps: Gap[];
  onGapClick?: (gapId: string) => void;
  className?: string;
}

function Shield({ coveragePercentage, gaps }: Omit<CoverageShieldProps, 'className' | 'onGapClick'>) {
  const shieldRef = useRef<THREE.Mesh>(null);
  const holesRef = useRef<THREE.Group>(null);

  // Shield color based on coverage
  const shieldColor = useMemo(() => {
    if (coveragePercentage >= 90) return '#10B981';
    if (coveragePercentage >= 70) return '#F59E0B';
    return '#EF4444';
  }, [coveragePercentage]);

  // Create shield shape
  const shieldShape = useMemo(() => {
    const shape = new THREE.Shape();
    shape.moveTo(0, 1.5);
    shape.bezierCurveTo(0.8, 1.5, 1.2, 1.2, 1.2, 0.5);
    shape.bezierCurveTo(1.2, -0.5, 0.8, -1.2, 0, -1.5);
    shape.bezierCurveTo(-0.8, -1.2, -1.2, -0.5, -1.2, 0.5);
    shape.bezierCurveTo(-1.2, 1.2, -0.8, 1.5, 0, 1.5);
    return shape;
  }, []);

  // Animate shield
  useFrame(({ clock }) => {
    if (shieldRef.current) {
      // Gentle rotation
      shieldRef.current.rotation.y = Math.sin(clock.getElapsedTime() * 0.5) * 0.1;
      // Subtle pulse
      const scale = 1 + Math.sin(clock.getElapsedTime() * 2) * 0.02;
      shieldRef.current.scale.setScalar(scale);
    }

    // Animate holes (pulsing for critical gaps)
    if (holesRef.current) {
      holesRef.current.children.forEach((hole, i) => {
        const gap = gaps[i];
        if (gap?.severity === 'critical') {
          const pulse = 1 + Math.sin(clock.getElapsedTime() * 4) * 0.1;
          hole.scale.setScalar(pulse);
        }
      });
    }
  });

  // Position gaps as "holes" in the shield
  const gapPositions = useMemo(() => {
    return gaps.map((_, i) => {
      const angle = (i / gaps.length) * Math.PI * 1.5 - Math.PI * 0.75;
      const radius = 0.5 + Math.random() * 0.4;
      return {
        x: Math.cos(angle) * radius,
        y: Math.sin(angle) * radius,
        size: 0.15 + Math.random() * 0.1,
      };
    });
  }, [gaps]);

  return (
    <group>
      {/* Main shield */}
      <mesh ref={shieldRef}>
        <extrudeGeometry
          args={[
            shieldShape,
            { depth: 0.2, bevelEnabled: true, bevelThickness: 0.05, bevelSize: 0.05 },
          ]}
        />
        <meshStandardMaterial
          color={shieldColor}
          metalness={0.6}
          roughness={0.3}
          emissive={shieldColor}
          emissiveIntensity={0.2}
        />
      </mesh>

      {/* Gap holes */}
      <group ref={holesRef}>
        {gaps.map((gap, i) => {
          const pos = gapPositions[i];
          const holeColor =
            gap.severity === 'critical' ? '#EF4444' :
            gap.severity === 'warning' ? '#F59E0B' : '#3B82F6';

          return (
            <group key={gap.id} position={[pos.x, pos.y, 0.15]}>
              {/* Hole indicator */}
              <mesh>
                <cylinderGeometry args={[pos.size, pos.size, 0.3, 32]} />
                <meshStandardMaterial
                  color={holeColor}
                  emissive={holeColor}
                  emissiveIntensity={0.5}
                  transparent
                  opacity={0.8}
                />
              </mesh>

              {/* Hole label */}
              <Html position={[0, pos.size + 0.2, 0]} center>
                <div
                  className="px-2 py-1 rounded text-xs font-medium text-white whitespace-nowrap"
                  style={{ backgroundColor: holeColor }}
                >
                  {gap.title}
                </div>
              </Html>
            </group>
          );
        })}
      </group>

      {/* Coverage percentage */}
      <Html position={[0, 0, 0.3]} center>
        <div className="text-center">
          <div className="text-4xl font-bold text-white drop-shadow-lg">
            {coveragePercentage}%
          </div>
          <div className="text-sm text-white/80">Protected</div>
        </div>
      </Html>
    </group>
  );
}

export function CoverageShield({
  coveragePercentage,
  gaps,
  onGapClick,
  className,
}: CoverageShieldProps) {
  return (
    <Scene
      className={className}
      camera={{ position: [0, 0, 4], fov: 45 }}
      bloom
    >
      <Shield coveragePercentage={coveragePercentage} gaps={gaps} />
    </Scene>
  );
}
```

---

## Renewal Timeline Path

A 3D journey visualization:

```tsx
// components/three/RenewalPath/RenewalPath.tsx
'use client';

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Html, Line, Sphere } from '@react-three/drei';
import * as THREE from 'three';
import { Scene } from '../shared/Scene';

interface Milestone {
  name: string;
  date: string;
  daysAway: number;
  status: 'completed' | 'in_progress' | 'upcoming';
}

interface RenewalPathProps {
  milestones: Milestone[];
  daysUntilExpiration: number;
  className?: string;
}

function Path({ milestones, daysUntilExpiration }: Omit<RenewalPathProps, 'className'>) {
  const particleRef = useRef<THREE.Mesh>(null);

  // Create curved path points
  const pathPoints = useMemo(() => {
    const points: THREE.Vector3[] = [];
    const segments = 50;
    for (let i = 0; i <= segments; i++) {
      const t = i / segments;
      const x = -4 + t * 8;
      const y = Math.sin(t * Math.PI * 2) * 0.3;
      const z = Math.cos(t * Math.PI) * 0.5;
      points.push(new THREE.Vector3(x, y, z));
    }
    return points;
  }, []);

  // Milestone positions along the path
  const milestonePositions = useMemo(() => {
    return milestones.map((_, i) => {
      const t = i / (milestones.length - 1);
      const idx = Math.floor(t * (pathPoints.length - 1));
      return pathPoints[idx];
    });
  }, [milestones, pathPoints]);

  // Animate particle flowing along path
  useFrame(({ clock }) => {
    if (particleRef.current) {
      const t = (clock.getElapsedTime() * 0.1) % 1;
      const idx = Math.floor(t * (pathPoints.length - 1));
      const point = pathPoints[idx];
      particleRef.current.position.copy(point);
    }
  });

  const getStatusColor = (status: Milestone['status']) => {
    if (status === 'completed') return '#10B981';
    if (status === 'in_progress') return '#1677FF';
    return '#9CA3AF';
  };

  return (
    <group>
      {/* Main path line */}
      <Line
        points={pathPoints}
        color="#E5E7EB"
        lineWidth={3}
        dashed={false}
      />

      {/* Glowing path overlay */}
      <Line
        points={pathPoints}
        color="#1677FF"
        lineWidth={2}
        transparent
        opacity={0.3}
      />

      {/* Animated particle */}
      <Sphere ref={particleRef} args={[0.08, 16, 16]}>
        <meshStandardMaterial
          color="#1677FF"
          emissive="#1677FF"
          emissiveIntensity={1}
        />
      </Sphere>

      {/* Milestones */}
      {milestones.map((milestone, i) => {
        const pos = milestonePositions[i];
        const color = getStatusColor(milestone.status);

        return (
          <group key={milestone.name} position={pos}>
            {/* Milestone sphere */}
            <Sphere args={[0.15, 16, 16]}>
              <meshStandardMaterial
                color={color}
                emissive={color}
                emissiveIntensity={milestone.status === 'in_progress' ? 0.5 : 0.2}
              />
            </Sphere>

            {/* Milestone label */}
            <Html position={[0, 0.4, 0]} center>
              <div className="text-center whitespace-nowrap">
                <div className="font-medium text-gray-900 text-sm">
                  {milestone.name}
                </div>
                <div className="text-xs text-gray-500">
                  {milestone.daysAway} days
                </div>
                <div
                  className="mt-1 text-xs font-medium capitalize"
                  style={{ color }}
                >
                  {milestone.status.replace('_', ' ')}
                </div>
              </div>
            </Html>

            {/* Checkmark for completed */}
            {milestone.status === 'completed' && (
              <Html position={[0.25, 0, 0]} center>
                <div className="text-success-500 text-lg">✓</div>
              </Html>
            )}
          </group>
        );
      })}

      {/* Days counter at end */}
      <Html position={[4, 0.5, 0]} center>
        <div className="bg-primary-500 text-white rounded-lg px-3 py-2 text-center">
          <div className="text-2xl font-bold">{daysUntilExpiration}</div>
          <div className="text-xs opacity-80">days left</div>
        </div>
      </Html>
    </group>
  );
}

export function RenewalPath({
  milestones,
  daysUntilExpiration,
  className,
}: RenewalPathProps) {
  return (
    <Scene
      className={className}
      camera={{ position: [0, 2, 6], fov: 50 }}
      bloom
    >
      <Path milestones={milestones} daysUntilExpiration={daysUntilExpiration} />
    </Scene>
  );
}
```

---

## Gradient Mesh Background

Subtle ambient 3D that makes the whole app feel alive:

```tsx
// components/three/GradientMeshBg/GradientMeshBg.tsx
'use client';

import { useRef, useMemo } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { Scene } from '../shared/Scene';

function GradientMesh() {
  const meshRef = useRef<THREE.Mesh>(null);
  const { mouse } = useThree();

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
      material.uniforms.uMouse.value.set(mouse.x, mouse.y);
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
      <Scene bloom={false} camera={{ position: [0, 0, 5] }}>
        <GradientMesh />
      </Scene>
    </div>
  );
}
```

---

## Performance Optimization

### Lazy Loading

```tsx
// components/three/index.ts
import dynamic from 'next/dynamic';

// Lazy load all 3D components with fallbacks
export const HealthScoreGlobe = dynamic(
  () => import('./HealthScoreGlobe').then((mod) => mod.HealthScoreGlobe),
  {
    ssr: false,
    loading: () => <div className="w-full h-full bg-gray-100 animate-pulse rounded-lg" />,
  }
);

export const PropertyCity = dynamic(
  () => import('./PropertyCity').then((mod) => mod.PropertyCity),
  { ssr: false }
);

export const CoverageShield = dynamic(
  () => import('./CoverageShield').then((mod) => mod.CoverageShield),
  { ssr: false }
);

export const RenewalPath = dynamic(
  () => import('./RenewalPath').then((mod) => mod.RenewalPath),
  { ssr: false }
);

export const GradientMeshBg = dynamic(
  () => import('./GradientMeshBg').then((mod) => mod.GradientMeshBg),
  { ssr: false }
);
```

### Mobile Fallbacks

```tsx
// components/three/HealthScoreGlobe/HealthScoreGlobeResponsive.tsx
'use client';

import { useMediaQuery } from '@/hooks/useMediaQuery';
import { HealthScoreGlobe } from './HealthScoreGlobe';
import { ScoreRing } from '@/components/patterns/ScoreRing';

interface Props {
  score: number;
  components?: Array<{ name: string; score: number; weight: number }>;
}

export function HealthScoreGlobeResponsive({ score, components }: Props) {
  const isMobile = useMediaQuery('(max-width: 768px)');
  const prefersReducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)');

  // Use 2D on mobile or when reduced motion is preferred
  if (isMobile || prefersReducedMotion) {
    return <ScoreRing score={score} size={200} animated={!prefersReducedMotion} />;
  }

  return <HealthScoreGlobe score={score} components={components} />;
}
```

### Performance Tips

1. **Use instancing** for repeated geometry (particles, windows)
2. **Limit draw calls** by merging geometries where possible
3. **Use LOD** (Level of Detail) for complex models
4. **Dispose properly** - clean up geometries and materials
5. **Limit post-processing** on mobile
6. **Use `AdaptiveDpr`** to reduce resolution on slow devices
7. **Cache geometries** with `useMemo`

---

## Next Steps

Continue to [07-implementation-phases.md](./07-implementation-phases.md) for the phased rollout plan.
