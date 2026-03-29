import mixpanel from 'mixpanel-browser';

const TOKEN = (import.meta.env.VITE_MIXPANEL_TOKEN as string | undefined) || '2bed4170bb9ff061f62da4289fd2ff71';

mixpanel.init(TOKEN, {
  track_pageview: true,
  persistence: 'localStorage',
  ignore_dnt: false,
  autocapture: true,
  record_sessions_percent: 100,
  api_host: 'https://api-eu.mixpanel.com',
});

// Profile anonymous visitors: identify with the auto-generated distinct_id
// so Mixpanel creates a People profile for every visitor.
const anonId = mixpanel.get_distinct_id();
mixpanel.identify(anonId);
mixpanel.people.set_once({
  $first_seen: new Date().toISOString(),
});

export const mp = {
  /** Ricerca modello barca */
  trackSearch: (query: string, year: string, lang: string) => {
    mixpanel.track('Search', { query, year: year || null, lang });
  },

  /** Risultati ricevuti */
  trackSearchResult: (query: string, totalResults: number, avgPrice: number, lang: string) => {
    mixpanel.track('Search Result', { query, total_results: totalResults, avg_price: avgPrice, lang });
  },

  /** Ricerca per agenzia/broker */
  trackSellerSearch: (seller: string, lang: string) => {
    mixpanel.track('Seller Search', { seller, lang });
  },

  /** Click su un comparable (link esterno) */
  trackComparableClick: (source: string, price: number, year: number | null) => {
    mixpanel.track('Comparable Click', { source, price, year });
  },

  /** Export PDF */
  trackPDFExport: (query: string) => {
    mixpanel.track('PDF Export', { query });
  },

  /** Switch lingua */
  trackLangSwitch: (to: 'it' | 'en') => {
    mixpanel.track('Language Switch', { to });
  },

  /** Switch tema */
  trackThemeSwitch: (to: 'dark' | 'light') => {
    mixpanel.track('Theme Switch', { to });
  },

  /** Click su un quick link (Axopar, Beneteau, ecc.) */
  trackQuickLink: (query: string) => {
    mixpanel.track('Quick Link Click', { query });
  },

  /** Apertura filtri avanzati */
  trackFiltersOpen: () => {
    mixpanel.track('Filters Opened');
  },

  /** Applicazione di un filtro */
  trackFilterApplied: (filterType: 'source' | 'country' | 'price_min' | 'price_max', value: string) => {
    mixpanel.track('Filter Applied', { filter_type: filterType, value });
  },

  /** Stima personalizzata usata */
  trackPersonalEstimate: (query: string, year: string, estimatedPrice: number) => {
    mixpanel.track('Personal Estimate', { query, year, estimated_price: estimatedPrice });
  },
};
