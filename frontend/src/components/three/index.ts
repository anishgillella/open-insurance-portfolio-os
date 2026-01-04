import dynamic from 'next/dynamic';

// Lazy load all 3D components
export const GradientMeshBg = dynamic(
  () => import('./GradientMeshBg').then((mod) => mod.GradientMeshBg),
  {
    ssr: false,
    loading: () => null,
  }
);

export { Scene } from './shared/Scene';
