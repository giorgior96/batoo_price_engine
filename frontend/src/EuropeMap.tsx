/* eslint-disable @typescript-eslint/ban-ts-comment */
// @ts-nocheck
import { useEffect, useState, useMemo } from 'react';
import { MapContainer, TileLayer, CircleMarker, Tooltip } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

// Coordinate approssimative (Lat, Lng) per il centro delle nazioni Europee principali
const COUNTRY_COORDS: Record<string, [number, number]> = {
  // ISO-2
  'it': [41.8719, 12.5674],
  'fr': [46.2276, 2.2137],
  'es': [40.4637, -3.7492],
  'hr': [45.1, 15.2],
  'gr': [39.0742, 21.8243],
  'de': [51.1657, 10.4515],
  'nl': [52.1326, 5.2913],
  'gb': [55.3781, -3.4360],
  'uk': [55.3781, -3.4360],
  'tr': [38.9637, 35.2433],
  'ch': [46.8182, 8.2275],
  'pt': [39.3999, -8.2245],
  'mc': [43.7384, 7.4246],
  'me': [42.7087, 19.3744],
  'si': [46.1512, 14.9955],
  'mt': [35.9375, 14.3975],
  'cy': [35.9375, 33.3975],
  'us': [37.0902, -95.7129],
  
  // ISO-3
  'ita': [41.8719, 12.5674],
  'fra': [46.2276, 2.2137],
  'esp': [40.4637, -3.7492],
  'hrv': [45.1, 15.2],
  'grc': [39.0742, 21.8243],
  'deu': [51.1657, 10.4515],
  'nld': [52.1326, 5.2913],
  'gbr': [55.3781, -3.4360],
  'tur': [38.9637, 35.2433],
  'che': [46.8182, 8.2275],
  'prt': [39.3999, -8.2245],
  'mco': [43.7384, 7.4246],
  'mne': [42.7087, 19.3744],
  'svn': [46.1512, 14.9955],
  'mlt': [35.9375, 14.3975],
  'cyp': [35.9375, 33.3975],
  'usa': [37.0902, -95.7129],

  // Esteso
  'italia': [41.8719, 12.5674],
  'italy': [41.8719, 12.5674],
  'francia': [46.2276, 2.2137],
  'france': [46.2276, 2.2137],
  'spagna': [40.4637, -3.7492],
  'spain': [40.4637, -3.7492],
  'croazia': [45.1, 15.2],
  'croatia': [45.1, 15.2],
  'grecia': [39.0742, 21.8243],
  'greece': [39.0742, 21.8243],
  'germania': [51.1657, 10.4515],
  'germany': [51.1657, 10.4515],
  'olanda': [52.1326, 5.2913],
  'netherlands': [52.1326, 5.2913],
  'united kingdom': [55.3781, -3.4360],
  'regno unito': [55.3781, -3.4360],
  'regno-unito': [55.3781, -3.4360],
  'turchia': [38.9637, 35.2433],
  'turkey': [38.9637, 35.2433],
  'svizzera': [46.8182, 8.2275],
  'switzerland': [46.8182, 8.2275],
  'portogallo': [39.3999, -8.2245],
  'portugal': [39.3999, -8.2245],
  'monaco': [43.7384, 7.4246],
  'montenegro': [42.7087, 19.3744],
  'slovenia': [46.1512, 14.9955],
  'malta': [35.9375, 14.3975],
  'cipro': [35.9375, 33.3975],
  'cyprus': [35.9375, 33.3975],
  'stati-uniti': [37.0902, -95.7129],
  'stati uniti': [37.0902, -95.7129],
  'stati-uniti-d-america': [37.0902, -95.7129]
};

interface EuropeMapProps {
  countriesData: { name: string; count: number; percentage: number }[];
  listings?: any[];
  isDark: boolean;
  lang: 'it' | 'en';
}

export default function EuropeMap({ countriesData, listings, isDark, lang }: EuropeMapProps) {
  // Fix per un warning noto di React StrictMode con Leaflet che non re-renderizza bene la mappa se cambiano le dimensioni
  const [mapRendered, setMapRendered] = useState(false);

  useEffect(() => {
    // Piccolo delay per assicurarsi che il contenitore padre abbia le dimensioni finali
    const timer = setTimeout(() => setMapRendered(true), 100);
    return () => clearTimeout(timer);
  }, []);

  // Prepariamo i marker per le singole barche (scattered)
  const boatMarkers = useMemo(() => {
    if (!listings || listings.length === 0) return [];
    return listings.map((boat, i) => {
      const nameLower = (boat.country || '').toLowerCase();
      let coords = COUNTRY_COORDS[nameLower];
      if (!coords) {
        const foundKey = Object.keys(COUNTRY_COORDS).find(k => nameLower.includes(k) || k.includes(nameLower.replace('-', ' ')));
        coords = foundKey ? COUNTRY_COORDS[foundKey] : null as any;
      }
      if (!coords) {
         const noDash = nameLower.replace(/-/g, ' ');
         if (COUNTRY_COORDS[noDash]) coords = COUNTRY_COORDS[noDash];
      }
      
      // Fallback center se non trovato
      if (!coords) coords = [46.0, 9.0];

      // Jitter (sparpagliamento) per non sovrapporre le barche (circa +/- 2.5 gradi, dipende dalla nazione)
      // Generiamo un seed pseudo-casuale basato sul nome/id per mantenerlo stabile al re-render
      const seed = (boat.id ? boat.id.toString().charCodeAt(0) : i) + i;
      const random = () => {
         const x = Math.sin(seed * 9999) * 10000;
         return x - Math.floor(x);
      };
      
      const jLat = (Math.random() - 0.5) * 4.0;
      const jLng = (Math.random() - 0.5) * 4.0;

      return {
        ...boat,
        coords: [coords[0] + jLat, coords[1] + jLng]
      };
    });
  }, [listings]);

  if (!mapRendered) return <div className="w-full h-[250px] animate-pulse bg-slate-200/20 rounded-xl" />;

  // Prepariamo i marker aggregati (nazioni)
  let maxCount = 0;
  const aggregateMarkers = countriesData.map(c => {
    if (c.count > maxCount) maxCount = c.count;
    const nameLower = c.name.toLowerCase();
    
    let coords = COUNTRY_COORDS[nameLower];
    if (!coords) {
      const foundKey = Object.keys(COUNTRY_COORDS).find(k => nameLower.includes(k) || k.includes(nameLower.replace('-', ' ')));
      coords = foundKey ? COUNTRY_COORDS[foundKey] : null as any;
    }
    
    if (!coords) {
       const noDash = nameLower.replace(/-/g, ' ');
       if (COUNTRY_COORDS[noDash]) coords = COUNTRY_COORDS[noDash];
    }

    return {
      ...c,
      coords
    };
  }).filter(m => m.coords);

  // Centro la mappa in Europa (Nord Italia/Svizzera)
  const mapCenter: [number, number] = [46.0, 9.0]; 
  const zoomLevel = 4;

  const tileUrl = isDark 
    ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
    : 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';

  return (
    <div className="w-full h-full relative z-0">
      <MapContainer 
        center={mapCenter as any} 
        zoom={zoomLevel} 
        scrollWheelZoom={false}
        className="w-full h-full absolute inset-0"
        style={{ background: isDark ? '#1a1d24' : '#e5e7eb' }}
      >
        <TileLayer
          attribution='&copy; <a href=\"https://carto.com/\">CARTO</a>' as any
          url={tileUrl}
        />
        
        {/* Aggregated Markers (Big circles) - solo se non ci sono le singole barche o come sfondo */}
        {aggregateMarkers.map((marker, idx) => {
          const radius = 8 + (17 * (marker.count / (maxCount || 1)));
          return (
            <CircleMarker
              key={`agg-${idx}`}
              center={marker.coords}
              radius={radius as any}
              fillColor="#3b82f6" // Tailwind blue-500
              fillOpacity={listings?.length ? 0.2 : 0.7} // Più trasparente se ci sono barche singole
              color={isDark ? "#ffffff" : "#1e40af"}
              weight={listings?.length ? 1 : 2}
              interactive={!listings?.length} // Disabilita tooltip aggregato se ci sono i punti singoli
            >
              {!listings?.length && (
                <Tooltip direction="top" offset={[0, -10] as any} opacity={1} as any>
                  <div className="text-center font-sans">
                    <strong className="block text-sm">{marker.name}</strong>
                    <span className="text-blue-600 font-bold">{marker.percentage}%</span> 
                    <span className="text-slate-500 text-xs ml-1">({marker.count} {lang === 'it' ? 'barche' : 'boats'})</span>
                  </div>
                </Tooltip>
              )}
            </CircleMarker>
          );
        })}

        {/* Individual Boat Markers */}
        {boatMarkers.map((boat, idx) => (
          <CircleMarker
            key={`boat-${idx}`}
            center={boat.coords as any}
            radius={5}
            fillColor="#f59e0b" // Tailwind amber-500
            fillOpacity={0.9}
            color={isDark ? "#ffffff" : "#b45309"}
            weight={1.5}
          >
            <Tooltip direction="top" offset={[0, -5] as any} opacity={1} as any>
              <div className="text-center font-sans">
                <strong className="block text-sm">{boat.builder} {boat.model}</strong>
                <span className="text-amber-600 font-bold">{boat.price_eur ? new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(boat.price_eur) : 'N/D'}</span> 
                <span className="text-slate-500 text-xs ml-1">({boat.year_built || 'N/D'})</span>
                <span className="block text-xs mt-1 text-slate-400 capitalize">{boat.country || 'Sconosciuto'}</span>
              </div>
            </Tooltip>
          </CircleMarker>
        ))}

      </MapContainer>
    </div>
  );
}
