'use client';

import { useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import Link from 'next/link';
import type { Property } from '@/lib/api';
import 'leaflet/dist/leaflet.css';

// Custom marker icon - clean green circle with white building icon
const createMarkerIcon = (healthScore: number, isSelected: boolean = false) => {
  // Determine color based on health score
  let color = '#10b981'; // emerald-500 for good (80+)
  if (healthScore < 80 && healthScore >= 60) {
    color = '#f59e0b'; // amber-500 for warning
  } else if (healthScore < 60) {
    color = '#ef4444'; // red-500 for critical
  }

  return L.divIcon({
    className: 'custom-marker',
    html: `
      <div style="
        width: ${isSelected ? '40px' : '36px'};
        height: ${isSelected ? '40px' : '36px'};
        background-color: ${color};
        border-radius: 50%;
        border: 3px solid white;
        box-shadow: 0 2px 8px rgba(0,0,0,0.25);
        display: flex;
        align-items: center;
        justify-content: center;
        transition: all 0.2s ease;
        ${isSelected ? 'transform: scale(1.1);' : ''}
      ">
        <svg width="18" height="18" viewBox="0 0 24 24" fill="white" stroke="white" stroke-width="1.5">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>
          <polyline points="9 22 9 12 15 12 15 22"/>
        </svg>
      </div>
    `,
    iconSize: [isSelected ? 40 : 36, isSelected ? 40 : 36],
    iconAnchor: [isSelected ? 20 : 18, isSelected ? 40 : 36],
    popupAnchor: [0, -36],
  });
};

// Component to fit map bounds to all markers
function FitBounds({ properties }: { properties: Property[] }) {
  const map = useMap();

  useEffect(() => {
    if (properties.length === 0) return;

    const validProperties = properties.filter(
      (p) => p.latitude !== undefined && p.longitude !== undefined
    );

    if (validProperties.length === 0) return;

    const bounds = L.latLngBounds(
      validProperties.map((p) => [p.latitude!, p.longitude!] as [number, number])
    );

    map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
  }, [map, properties]);

  return null;
}

interface PropertyMapProps {
  properties: Property[];
  onPropertySelect?: (property: Property) => void;
  height?: number | string;
  selectedPropertyId?: string;
}

export function PropertyMap({
  properties,
  onPropertySelect,
  height = 400,
  selectedPropertyId,
}: PropertyMapProps) {
  // Filter properties with valid coordinates
  const validProperties = useMemo(
    () =>
      properties.filter(
        (p) => p.latitude !== undefined && p.longitude !== undefined
      ),
    [properties]
  );

  // Calculate center from properties or default to NYC
  const center = useMemo(() => {
    if (validProperties.length === 0) {
      return [40.7128, -74.006] as [number, number]; // NYC default
    }
    const avgLat =
      validProperties.reduce((sum, p) => sum + p.latitude!, 0) /
      validProperties.length;
    const avgLng =
      validProperties.reduce((sum, p) => sum + p.longitude!, 0) /
      validProperties.length;
    return [avgLat, avgLng] as [number, number];
  }, [validProperties]);

  const formatCurrency = (value: number | string) => {
    const num = typeof value === 'string' ? parseFloat(value) : value;
    if (num >= 1000000) {
      return `$${(num / 1000000).toFixed(1)}M`;
    }
    return `$${num.toLocaleString()}`;
  };

  // Count properties by health score for legend
  const goodCount = validProperties.filter((p) => p.health_score >= 80).length;
  const warningCount = validProperties.filter((p) => p.health_score >= 60 && p.health_score < 80).length;
  const criticalCount = validProperties.filter((p) => p.health_score < 60).length;

  return (
    <div style={{ height, width: '100%' }} className="rounded-lg overflow-hidden relative">
      <MapContainer
        center={center}
        zoom={12}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
        zoomControl={true}
      >
        {/* Using CartoDB Positron for a cleaner, lighter map style */}
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        />
        <FitBounds properties={validProperties} />
        {validProperties.map((property) => (
          <Marker
            key={property.id}
            position={[property.latitude!, property.longitude!]}
            icon={createMarkerIcon(property.health_score, property.id === selectedPropertyId)}
            eventHandlers={{
              click: () => onPropertySelect?.(property),
            }}
          >
            <Popup className="property-popup">
              <div className="min-w-[240px] p-1">
                {/* Property Name */}
                <h3 className="font-semibold text-gray-900 text-base mb-1">
                  {property.name}
                </h3>

                {/* Address */}
                <p className="text-sm text-gray-600 mb-3">
                  {property.address.street}, {property.address.city}, {property.address.state} {property.address.zip}
                </p>

                {/* Premium and Claims */}
                <div className="space-y-1 mb-3">
                  <p className="text-sm text-gray-700">
                    <span className="text-gray-500">Premium:</span>{' '}
                    <span className="font-medium">{formatCurrency(property.total_premium)}</span>
                  </p>
                  <p className="text-sm text-gray-700">
                    <span className="text-gray-500">Claims:</span>{' '}
                    <span className="font-medium">{property.days_until_expiration !== null ? Math.floor(property.days_until_expiration / 30) : 0}</span>
                  </p>
                </div>

                {/* Property ID */}
                <p className="text-xs text-gray-400 mb-4 font-mono">
                  {property.id}
                </p>

                {/* Action Buttons */}
                <div className="flex gap-3">
                  <Link
                    href={`/properties/${property.id}`}
                    className="text-sm text-teal-600 hover:text-teal-700 font-medium"
                  >
                    View
                  </Link>
                  <Link
                    href={`/documents?property=${property.id}`}
                    className="text-sm text-teal-600 hover:text-teal-700 font-medium"
                  >
                    Upload
                  </Link>
                </div>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>

      {/* Map Legend */}
      <div className="absolute bottom-4 left-4 z-[1000] bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-3">
        <p className="text-xs font-semibold text-gray-700 dark:text-gray-200 mb-2">Property Health</p>
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-emerald-500 border-2 border-white shadow-sm" />
            <span className="text-xs text-gray-600 dark:text-gray-300">Good (80+)</span>
            <span className="text-xs font-medium text-gray-800 dark:text-gray-100 ml-auto">{goodCount}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-amber-500 border-2 border-white shadow-sm" />
            <span className="text-xs text-gray-600 dark:text-gray-300">Warning (60-79)</span>
            <span className="text-xs font-medium text-gray-800 dark:text-gray-100 ml-auto">{warningCount}</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-red-500 border-2 border-white shadow-sm" />
            <span className="text-xs text-gray-600 dark:text-gray-300">Critical (&lt;60)</span>
            <span className="text-xs font-medium text-gray-800 dark:text-gray-100 ml-auto">{criticalCount}</span>
          </div>
        </div>
        <div className="mt-2 pt-2 border-t border-gray-200 dark:border-gray-600">
          <p className="text-xs text-gray-500 dark:text-gray-400">
            {validProperties.length} properties shown
          </p>
        </div>
      </div>

      <style jsx global>{`
        .leaflet-popup-content-wrapper {
          border-radius: 12px;
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
          padding: 0;
        }
        .leaflet-popup-content {
          margin: 14px 16px;
        }
        .leaflet-popup-tip {
          box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }
        .leaflet-container {
          font-family: inherit;
        }
        .custom-marker {
          background: transparent !important;
          border: none !important;
        }
      `}</style>
    </div>
  );
}

export default PropertyMap;
