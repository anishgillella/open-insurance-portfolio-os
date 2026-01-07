'use client';

import dynamic from 'next/dynamic';
import { Loader2 } from 'lucide-react';
import type { Property } from '@/lib/api';

// Dynamic import to prevent SSR issues with Leaflet
const PropertyMap = dynamic(
  () => import('./PropertyMap').then((mod) => mod.PropertyMap),
  {
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center bg-[var(--color-surface-sunken)] rounded-lg" style={{ height: 400 }}>
        <Loader2 className="h-8 w-8 text-[var(--color-primary-500)] animate-spin" />
      </div>
    ),
  }
);

interface DynamicPropertyMapProps {
  properties: Property[];
  onPropertySelect?: (property: Property) => void;
  height?: number | string;
  selectedPropertyId?: string;
}

export function DynamicPropertyMap(props: DynamicPropertyMapProps) {
  return <PropertyMap {...props} />;
}

export default DynamicPropertyMap;
