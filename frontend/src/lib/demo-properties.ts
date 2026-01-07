// Demo properties with NYC coordinates for map visualization
// These are used as fallback when no properties are returned from the API
// or when properties don't have coordinates

import type { Property } from '@/lib/api';

export const demoProperties: Property[] = [
  {
    id: 'demo-prop-1',
    name: 'Manhattan Tower',
    address: {
      street: '100 East St',
      city: 'New York',
      state: 'NY',
      zip: '10004',
    },
    latitude: 40.7580,  // Midtown Manhattan
    longitude: -73.9855,
    property_type: 'Commercial',
    total_units: 250,
    total_buildings: 1,
    year_built: 2015,
    total_insured_value: 85000000,
    total_premium: 140000,
    health_score: 92,
    health_grade: 'A',
    gaps_count: {
      critical: 0,
      warning: 1,
      info: 2,
    },
    next_expiration: '2026-03-15',
    days_until_expiration: 45,
    compliance_status: 'compliant',
    completeness_percentage: 98,
    created_at: '2024-01-15',
    updated_at: '2026-01-03',
  },
  {
    id: 'demo-prop-2',
    name: 'Brooklyn Heights Apartments',
    address: {
      street: '250 Court St',
      city: 'Brooklyn',
      state: 'NY',
      zip: '11201',
    },
    latitude: 40.6501,  // South Brooklyn
    longitude: -73.9496,
    property_type: 'Multi-Family',
    total_units: 180,
    total_buildings: 3,
    year_built: 2008,
    total_insured_value: 62000000,
    total_premium: 98000,
    health_score: 78,
    health_grade: 'C',
    gaps_count: {
      critical: 1,
      warning: 2,
      info: 1,
    },
    next_expiration: '2026-02-10',
    days_until_expiration: 22,
    compliance_status: 'non_compliant',
    completeness_percentage: 85,
    created_at: '2024-02-01',
    updated_at: '2026-01-02',
  },
  {
    id: 'demo-prop-3',
    name: 'Upper East Side Plaza',
    address: {
      street: '500 Park Ave',
      city: 'New York',
      state: 'NY',
      zip: '10022',
    },
    latitude: 40.7900,  // Upper East Side
    longitude: -73.9540,
    property_type: 'Mixed-Use',
    total_units: 320,
    total_buildings: 1,
    year_built: 2018,
    total_insured_value: 120000000,
    total_premium: 185000,
    health_score: 88,
    health_grade: 'B',
    gaps_count: {
      critical: 0,
      warning: 0,
      info: 3,
    },
    next_expiration: '2026-04-01',
    days_until_expiration: 60,
    compliance_status: 'compliant',
    completeness_percentage: 95,
    created_at: '2024-03-01',
    updated_at: '2025-12-28',
  },
  {
    id: 'demo-prop-4',
    name: 'Jersey City Waterfront',
    address: {
      street: '75 Hudson St',
      city: 'Jersey City',
      state: 'NJ',
      zip: '07302',
    },
    latitude: 40.7178,  // Jersey City (across Hudson)
    longitude: -74.0431,
    property_type: 'Multi-Family',
    total_units: 64,
    total_buildings: 1,
    year_built: 1920,
    total_insured_value: 45000000,
    total_premium: 72000,
    health_score: 55,
    health_grade: 'D',
    gaps_count: {
      critical: 2,
      warning: 3,
      info: 1,
    },
    next_expiration: '2026-01-20',
    days_until_expiration: 12,
    compliance_status: 'non_compliant',
    completeness_percentage: 68,
    created_at: '2024-01-10',
    updated_at: '2025-12-15',
  },
];

/**
 * Get demo properties to show on the map when real properties
 * don't have coordinates or when the API returns no data
 */
export function getDemoPropertiesForMap(realProperties: Property[]): Property[] {
  // Check if any real properties have valid coordinates
  const propertiesWithCoords = realProperties.filter(
    (p) => p.latitude !== undefined && p.longitude !== undefined
  );

  // If we have real properties with coordinates, use them
  if (propertiesWithCoords.length > 0) {
    return propertiesWithCoords;
  }

  // Otherwise, return demo properties
  return demoProperties;
}
