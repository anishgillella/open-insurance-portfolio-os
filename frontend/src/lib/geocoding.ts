// Simple geocoding utility for Indiana properties
// This provides approximate coordinates based on city/zip code

interface CityCoordinates {
  lat: number;
  lng: number;
}

// Indiana city coordinates (approximate center points)
const INDIANA_CITIES: Record<string, CityCoordinates> = {
  'fort wayne': { lat: 41.0793, lng: -85.1394 },
  'indianapolis': { lat: 39.7684, lng: -86.1581 },
  'carmel': { lat: 39.9784, lng: -86.1180 },
  'fishers': { lat: 39.9568, lng: -86.0139 },
  'bloomington': { lat: 39.1653, lng: -86.5264 },
  'south bend': { lat: 41.6764, lng: -86.2520 },
  'evansville': { lat: 37.9716, lng: -87.5711 },
  'hammond': { lat: 41.5833, lng: -87.5000 },
  'gary': { lat: 41.5934, lng: -87.3465 },
  'lafayette': { lat: 40.4167, lng: -86.8753 },
  'muncie': { lat: 40.1934, lng: -85.3864 },
  'terre haute': { lat: 39.4667, lng: -87.4139 },
  'kokomo': { lat: 40.4864, lng: -86.1336 },
  'noblesville': { lat: 40.0456, lng: -86.0086 },
  'anderson': { lat: 40.1053, lng: -85.6803 },
  'greenwood': { lat: 39.6136, lng: -86.1067 },
  'new albany': { lat: 38.2856, lng: -85.8241 },
  'elkhart': { lat: 41.6820, lng: -85.9767 },
  'mishawaka': { lat: 41.6620, lng: -86.1586 },
  'lawrence': { lat: 39.8386, lng: -86.0253 },
};

// ZIP code to approximate coordinates (for more precision)
const ZIP_COORDINATES: Record<string, CityCoordinates> = {
  // Fort Wayne area
  '46802': { lat: 41.0793, lng: -85.1394 },
  '46804': { lat: 41.0534, lng: -85.2012 },
  '46815': { lat: 41.0891, lng: -85.0523 },
  '46816': { lat: 41.0456, lng: -85.0678 },
  '46825': { lat: 41.1178, lng: -85.1047 },
  // Indianapolis area
  '46202': { lat: 39.7784, lng: -86.1621 },
  '46204': { lat: 39.7684, lng: -86.1581 },
  '46220': { lat: 39.8686, lng: -86.1067 },
  '46240': { lat: 39.9086, lng: -86.1267 },
  // Carmel area
  '46032': { lat: 39.9784, lng: -86.1180 },
  '46033': { lat: 39.9684, lng: -86.0980 },
  // Add more as needed
};

export interface GeocodedProperty {
  latitude: number;
  longitude: number;
  isApproximate: boolean;
}

/**
 * Get coordinates for a property based on its address
 * Returns approximate coordinates based on city or ZIP code
 */
export function geocodeAddress(address: {
  street?: string;
  city?: string;
  state?: string;
  zip?: string;
}): GeocodedProperty | null {
  // First try ZIP code (more precise)
  if (address.zip && ZIP_COORDINATES[address.zip]) {
    const coords = ZIP_COORDINATES[address.zip];
    // Add small random offset to prevent marker overlap
    return {
      latitude: coords.lat + (Math.random() - 0.5) * 0.01,
      longitude: coords.lng + (Math.random() - 0.5) * 0.01,
      isApproximate: true,
    };
  }

  // Fall back to city name
  if (address.city) {
    const cityKey = address.city.toLowerCase().trim();
    if (INDIANA_CITIES[cityKey]) {
      const coords = INDIANA_CITIES[cityKey];
      // Add small random offset to prevent marker overlap
      return {
        latitude: coords.lat + (Math.random() - 0.5) * 0.02,
        longitude: coords.lng + (Math.random() - 0.5) * 0.02,
        isApproximate: true,
      };
    }
  }

  // Default to Indianapolis center if nothing matches
  if (address.state?.toLowerCase() === 'in' || address.state?.toLowerCase() === 'indiana') {
    return {
      latitude: 39.7684 + (Math.random() - 0.5) * 0.05,
      longitude: -86.1581 + (Math.random() - 0.5) * 0.05,
      isApproximate: true,
    };
  }

  return null;
}

/**
 * Add coordinates to properties that don't have them
 */
export function enrichPropertiesWithCoordinates<T extends {
  latitude?: number;
  longitude?: number;
  address: {
    street?: string;
    city?: string;
    state?: string;
    zip?: string;
  };
}>(properties: T[]): (T & { latitude: number; longitude: number })[] {
  return properties.map((property) => {
    // If property already has coordinates, use them
    if (property.latitude !== undefined && property.longitude !== undefined) {
      return property as T & { latitude: number; longitude: number };
    }

    // Try to geocode
    const geocoded = geocodeAddress(property.address);
    if (geocoded) {
      return {
        ...property,
        latitude: geocoded.latitude,
        longitude: geocoded.longitude,
      };
    }

    // Return property without coordinates if geocoding fails
    return property as T & { latitude: number; longitude: number };
  }).filter((p) => p.latitude !== undefined && p.longitude !== undefined);
}
