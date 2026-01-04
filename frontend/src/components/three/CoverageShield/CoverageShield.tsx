'use client';

import { useRef, useMemo } from 'react';
import { useFrame } from '@react-three/fiber';
import { Float, Html, Ring, Torus } from '@react-three/drei';
import * as THREE from 'three';
import { Scene } from '../shared/Scene';

interface CoverageType {
  name: string;
  color: string;
  adequacy: number; // 0-100
}

interface CoverageShieldProps {
  coverages: CoverageType[];
  size?: number;
  interactive?: boolean;
  className?: string;
  showLabels?: boolean;
}

// Shield segment representing a coverage type
function ShieldSegment({
  coverage,
  index,
  total,
  radius,
}: {
  coverage: CoverageType;
  index: number;
  total: number;
  radius: number;
}) {
  const meshRef = useRef<THREE.Mesh>(null);
  const segmentAngle = (Math.PI * 2) / total;
  const startAngle = index * segmentAngle - Math.PI / 2;
  const endAngle = startAngle + segmentAngle;

  // Create arc geometry for the segment
  const geometry = useMemo(() => {
    const shape = new THREE.Shape();
    const outerRadius = radius;
    const innerRadius = radius * 0.5;
    const segments = 32;

    // Start at inner radius
    shape.moveTo(
      Math.cos(startAngle) * innerRadius,
      Math.sin(startAngle) * innerRadius
    );

    // Draw outer arc
    for (let i = 0; i <= segments; i++) {
      const angle = startAngle + (endAngle - startAngle) * (i / segments);
      shape.lineTo(
        Math.cos(angle) * outerRadius,
        Math.sin(angle) * outerRadius
      );
    }

    // Draw inner arc (reverse)
    for (let i = segments; i >= 0; i--) {
      const angle = startAngle + (endAngle - startAngle) * (i / segments);
      shape.lineTo(
        Math.cos(angle) * innerRadius,
        Math.sin(angle) * innerRadius
      );
    }

    shape.closePath();

    const extrudeSettings = {
      depth: 0.15,
      bevelEnabled: true,
      bevelThickness: 0.02,
      bevelSize: 0.02,
      bevelSegments: 3,
    };

    return new THREE.ExtrudeGeometry(shape, extrudeSettings);
  }, [startAngle, endAngle, radius]);

  // Calculate color based on adequacy
  const color = useMemo(() => {
    if (coverage.adequacy >= 90) return '#22c55e'; // green
    if (coverage.adequacy >= 70) return '#eab308'; // yellow
    if (coverage.adequacy >= 50) return '#f97316'; // orange
    return '#ef4444'; // red
  }, [coverage.adequacy]);

  // Calculate opacity based on adequacy (lower adequacy = more transparent = gap visible)
  const opacity = Math.max(0.3, coverage.adequacy / 100);

  useFrame(({ clock }) => {
    if (meshRef.current) {
      // Subtle pulse effect for low adequacy segments
      if (coverage.adequacy < 70) {
        const pulse = Math.sin(clock.getElapsedTime() * 2) * 0.1 + 0.9;
        meshRef.current.scale.z = pulse;
      }
    }
  });

  // Calculate label position (middle of the segment arc)
  const midAngle = (startAngle + endAngle) / 2;
  const labelRadius = radius * 0.75;
  const labelX = Math.cos(midAngle) * labelRadius;
  const labelY = Math.sin(midAngle) * labelRadius;

  return (
    <group>
      <mesh ref={meshRef} geometry={geometry} rotation={[Math.PI / 2, 0, 0]}>
        <meshStandardMaterial
          color={color}
          transparent
          opacity={opacity}
          metalness={0.3}
          roughness={0.4}
          emissive={color}
          emissiveIntensity={0.15}
        />
      </mesh>

      {/* Label */}
      <Html
        position={[labelX, labelY, 0.2]}
        center
        distanceFactor={6}
        style={{ pointerEvents: 'none' }}
      >
        <div className="bg-white/95 dark:bg-gray-900/95 backdrop-blur-sm rounded-lg px-2 py-1 shadow-lg text-xs whitespace-nowrap border border-gray-200 dark:border-gray-700">
          <div className="font-medium text-gray-900 dark:text-gray-100">{coverage.name}</div>
          <div className="flex items-center gap-1">
            <div
              className="w-2 h-2 rounded-full"
              style={{ backgroundColor: color }}
            />
            <span className="text-gray-500 dark:text-gray-400">{coverage.adequacy}%</span>
          </div>
        </div>
      </Html>
    </group>
  );
}

// Gap indicator - shows where coverage is insufficient
function GapIndicator({ angle, radius }: { angle: number; radius: number }) {
  const meshRef = useRef<THREE.Mesh>(null);

  useFrame(({ clock }) => {
    if (meshRef.current) {
      const pulse = Math.sin(clock.getElapsedTime() * 3) * 0.5 + 0.5;
      meshRef.current.scale.setScalar(0.5 + pulse * 0.5);
    }
  });

  const x = Math.cos(angle) * radius;
  const y = Math.sin(angle) * radius;

  return (
    <mesh ref={meshRef} position={[x, y, 0.3]}>
      <ringGeometry args={[0.08, 0.15, 32]} />
      <meshStandardMaterial
        color="#ef4444"
        emissive="#ef4444"
        emissiveIntensity={0.5}
        transparent
        opacity={0.8}
      />
    </mesh>
  );
}

// Main shield component
function Shield({ coverages }: { coverages: CoverageType[] }) {
  const groupRef = useRef<THREE.Group>(null);
  const radius = 1.5;

  useFrame(({ clock }) => {
    if (groupRef.current) {
      groupRef.current.rotation.z = Math.sin(clock.getElapsedTime() * 0.2) * 0.05;
    }
  });

  // Find gaps (coverages with adequacy < 50)
  const gaps = coverages
    .map((c, i) => ({ coverage: c, index: i }))
    .filter((item) => item.coverage.adequacy < 50);

  return (
    <group ref={groupRef}>
      <Float speed={2} rotationIntensity={0.1} floatIntensity={0.2}>
        {/* Shield segments */}
        {coverages.map((coverage, index) => (
          <ShieldSegment
            key={coverage.name}
            coverage={coverage}
            index={index}
            total={coverages.length}
            radius={radius}
          />
        ))}

        {/* Gap indicators */}
        {gaps.map((item) => {
          const segmentAngle = (Math.PI * 2) / coverages.length;
          const midAngle = item.index * segmentAngle - Math.PI / 2 + segmentAngle / 2;
          return (
            <GapIndicator
              key={`gap-${item.index}`}
              angle={midAngle}
              radius={radius * 0.75}
            />
          );
        })}

        {/* Center circle with overall score */}
        <mesh position={[0, 0, 0]}>
          <circleGeometry args={[radius * 0.45, 64]} />
          <meshStandardMaterial
            color="#1e293b"
            metalness={0.5}
            roughness={0.3}
          />
        </mesh>

        {/* Inner ring decoration */}
        <Ring args={[radius * 0.48, radius * 0.5, 64]} position={[0, 0, 0.01]}>
          <meshStandardMaterial
            color="#3b82f6"
            emissive="#3b82f6"
            emissiveIntensity={0.3}
          />
        </Ring>

        {/* Outer ring decoration */}
        <Ring args={[radius * 1.02, radius * 1.05, 64]} position={[0, 0, 0.01]}>
          <meshStandardMaterial
            color="#6366f1"
            emissive="#6366f1"
            emissiveIntensity={0.2}
          />
        </Ring>

        {/* Center score display */}
        <Html center position={[0, 0, 0.1]} style={{ pointerEvents: 'none' }}>
          <div className="text-center select-none">
            <div className="text-3xl font-bold text-white drop-shadow-lg">
              {Math.round(
                coverages.reduce((sum, c) => sum + c.adequacy, 0) / coverages.length
              )}%
            </div>
            <div className="text-sm text-gray-300">Coverage</div>
          </div>
        </Html>
      </Float>
    </group>
  );
}

export function CoverageShield({
  coverages,
  size = 400,
  className,
}: CoverageShieldProps) {
  return (
    <div className={className} style={{ width: size, height: size }}>
      <Scene
        className="w-full h-full"
        camera={{ position: [0, 0, 4], fov: 50 }}
        bloom
      >
        <Shield coverages={coverages} />
      </Scene>
    </div>
  );
}
