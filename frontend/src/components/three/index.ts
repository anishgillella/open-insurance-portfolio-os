import dynamic from 'next/dynamic';

// Lazy load all 3D components
export const GradientMeshBg = dynamic(
  () => import('./GradientMeshBg').then((mod) => mod.GradientMeshBg),
  {
    ssr: false,
    loading: () => null,
  }
);

export const HealthScoreGlobe = dynamic(
  () => import('./HealthScoreGlobe').then((mod) => mod.HealthScoreGlobe),
  {
    ssr: false,
    loading: () => null,
  }
);

export const CoverageShield = dynamic(
  () => import('./CoverageShield').then((mod) => mod.CoverageShield),
  {
    ssr: false,
    loading: () => null,
  }
);

export { Scene } from './shared/Scene';
