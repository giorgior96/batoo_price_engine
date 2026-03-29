import React, { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import axios from 'axios';
import { Search, Anchor, Euro, Calendar, TrendingUp, TrendingDown, ChevronRight, Sun, Moon, AlertTriangle, MapPin, Ruler, Activity, Droplets, Zap, Download, ShieldCheck, FileText, Filter, Clock, X, Check, BarChart2, SlidersHorizontal, ChevronDown, ChevronUp, Star, ExternalLink, Maximize, Minimize, Sailboat } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ComposedChart, Area, BarChart, Bar, Cell } from 'recharts';
import { mp } from './analytics';

const AnimatedCounter = ({ end, duration = 2000 }: { end: number, duration?: number }) => {
  const [count, setCount] = useState(0);

  useEffect(() => {
    let startTime: number | null = null;
    const animate = (currentTime: number) => {
      if (!startTime) startTime = currentTime;
      const progress = Math.min((currentTime - startTime) / duration, 1);
      
      // Easing function for smoother slowdown
      const easeOutQuart = 1 - Math.pow(1 - progress, 4);
      setCount(Math.floor(easeOutQuart * end));

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    };
    requestAnimationFrame(animate);
  }, [end, duration]);

  return <>{count.toLocaleString('it-IT')}</>;
};
import EuropeMap from './EuropeMap';

// --- Types ---
type SortOrder = 'year_desc' | 'price_asc' | 'price_desc';
type Toast = { id: string; message: string; type: 'success' | 'error' | 'info' };

// --- Constants ---
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

const RECENT_SEARCHES_KEY = 'batoo_recent_searches';
const SOURCE_COLORS: Record<string, string> = {
  boat24: '#3b82f6', yachtall: '#8b5cf6', mondialbroker: '#10b981',
  inautia: '#f59e0b', navisnet: '#ef4444',
};
const getSourceColor = (s: string) => {
  const l = s.toLowerCase();
  const key = Object.keys(SOURCE_COLORS).find(k => l.includes(k));
  return key ? SOURCE_COLORS[key] : '#64748b';
};

// --- ToastContainer ---
const ToastContainer = ({ toasts, remove }: { toasts: Toast[]; remove: (id: string) => void }) => (
  <div className="fixed bottom-6 right-6 z-[100] space-y-2 pointer-events-none">
    {toasts.map(t => (
      <div key={t.id} className={`pointer-events-auto flex items-center gap-3 px-4 py-3 rounded-2xl shadow-2xl border backdrop-blur-xl animate-[fadeInUp_0.3s_ease-out] ${
        t.type === 'success' ? 'bg-emerald-900/90 border-emerald-500/30 text-emerald-300' :
        t.type === 'error'   ? 'bg-red-900/90 border-red-500/30 text-red-300' :
        'bg-slate-900/90 border-slate-700/50 text-slate-300'}`}>
        {t.type === 'success' ? <Check className="w-4 h-4"/> : t.type === 'error' ? <AlertTriangle className="w-4 h-4"/> : <Zap className="w-4 h-4"/>}
        <span className="text-sm font-medium">{t.message}</span>
        <button onClick={() => remove(t.id)} className="ml-1 opacity-60 hover:opacity-100"><X className="w-3 h-3"/></button>
      </div>
    ))}
  </div>
);


function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [year, setYear] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');

  const [totalBoatsDB, setTotalBoatsDB] = useState<number>(0);

  // --- Broker / Advanced filters ---
  const [activeTab, setActiveTab] = useState<'model' | 'broker'>('model');
  const [showFilters, setShowFilters] = useState(false);
  const [filterSource, setFilterSource] = useState('');
  const [filterCountry, setFilterCountry] = useState('');
  const [priceMin, setPriceMin] = useState('');
  const [priceMax, setPriceMax] = useState('');
  
  // --- Advanced filters ---
  const [sources, setSources] = useState<{name: string; count: number}[]>([]);
  const [countries, setCountries] = useState<{name: string; count: number}[]>([]);
  // Legacy platform/country broker state (kept for compatibility)
  const [brokerSource, setBrokerSource] = useState('');
  const [brokerCountry, setBrokerCountry] = useState('');
  const [brokerResult, setBrokerResult] = useState<any>(null);
  const [brokerLoading, setBrokerLoading] = useState(false);

  // --- Seller/Agenzia search ---
  const [sellerQuery, setSellerQuery] = useState('');
  const [sellerSuggestions, setSellerSuggestions] = useState<{name: string; count: number}[]>([]);
  const [sellerResult, setSellerResult] = useState<any>(null);
  const [sellerLoading, setSellerLoading] = useState(false);
  const [showSellerSuggestions, setShowSellerSuggestions] = useState(false);
  // Seller listings pagination
  const [sellerListings, setSellerListings] = useState<any>(null);
  const [sellerListingsPage, setSellerListingsPage] = useState(1);
  const [sellerListingsSort, setSellerListingsSort] = useState('year_desc');
  const [sellerListingsSourceFilter, setSellerListingsSourceFilter] = useState('');
  const [sellerListingsLoading, setSellerListingsLoading] = useState(false);

  // Evaluate (model search) listings pagination
  const [evaluateListings, setEvaluateListings] = useState<any>(null);
  const [evaluateListingsPage, setEvaluateListingsPage] = useState(1);
  const [evaluateListingsSort, setEvaluateListingsSort] = useState('year_desc');
  const [evaluateListingsLoading, setEvaluateListingsLoading] = useState(false);

  // --- Map ---
  const [isMapExpanded, setIsMapExpanded] = useState(false);

  // --- Sort & personal valuation ---
  const [sortOrder, setSortOrder] = useState<SortOrder>('year_desc');
  const [personalYear, setPersonalYear] = useState('');

  // --- Recent searches ---
  const [recentSearches, setRecentSearches] = useState<string[]>([]);

  // --- Toast ---
  const [toasts, setToasts] = useState<Toast[]>([]);
  const addToast = useCallback((message: string, type: Toast['type'] = 'info') => {
    const id = Date.now().toString();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => setToasts(prev => prev.filter(t => t.id !== id)), 3500);
  }, []);
  const removeToast = useCallback((id: string) => setToasts(prev => prev.filter(t => t.id !== id)), []);

  // --- Recent searches helper ---
  const addRecentSearch = useCallback((q: string) => {
    setRecentSearches(prev => {
      const updated = [q, ...prev.filter(s => s !== q)].slice(0, 5);
      try { localStorage.setItem(RECENT_SEARCHES_KEY, JSON.stringify(updated)); } catch {}
      return updated;
    });
  }, []);

  // --- Sorted & filtered comparables ---
  const sortedComparables = useMemo(() => {
    if (!result?.comparables) return [];
    let arr = [...result.comparables];
    if (priceMin) arr = arr.filter((b: any) => b.price_eur >= parseFloat(priceMin));
    if (priceMax) arr = arr.filter((b: any) => b.price_eur <= parseFloat(priceMax));
    if (sortOrder === 'price_asc') return arr.sort((a: any, b: any) => a.price_eur - b.price_eur);
    if (sortOrder === 'price_desc') return arr.sort((a: any, b: any) => b.price_eur - a.price_eur);
    return arr.sort((a: any, b: any) => (b.year_built || 0) - (a.year_built || 0));
  }, [result, sortOrder, priceMin, priceMax]);

  // --- Personal estimate ---
  const personalEstimate = useMemo(() => {
    if (!result?.valuation?.price_trend?.length || !personalYear) return null;
    const yr = parseInt(personalYear);
    if (isNaN(yr)) return null;
    const sorted = [...result.valuation.price_trend].sort((a: any, b: any) => Math.abs(a.year - yr) - Math.abs(b.year - yr));
    return sorted[0]?.avg_price ?? null;
  }, [result, personalYear]);

  // Main data loading effect
  useEffect(() => {
    axios.get(`${API_BASE_URL}/`).then(res => {
      if (res.data?.total_boats) setTotalBoatsDB(res.data.total_boats);
    }).catch(console.error);

    axios.get(`${API_BASE_URL}/sources`).then(res => setSources(res.data)).catch(console.error);
    axios.get(`${API_BASE_URL}/countries`).then(res => setCountries(res.data)).catch(console.error);

    try {
      const stored = localStorage.getItem(RECENT_SEARCHES_KEY);
      if (stored) setRecentSearches(JSON.parse(stored));
    } catch {}
  }, []);

  // PDF
  const [generatingPDF] = useState(false);
  const reportRef = useRef<HTMLDivElement>(null);



  // Autocompletamento
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const searchContainerRef = useRef<HTMLDivElement>(null);

  // Tema Chiaro/Scuro
  const [isDark, setIsDark] = useState(false);
  const [lang, setLang] = useState<"it" | "en">("it");
  const toggleLang = () => {
    const next = lang === 'it' ? 'en' : 'it';
    mp.trackLangSwitch(next);
    setLang(next);
  };
  const toggleTheme = () => {
    mp.trackThemeSwitch(!isDark ? 'dark' : 'light');
    setIsDark(!isDark);
  };

  // Chiude i suggerimenti se si clicca fuori
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (searchContainerRef.current && !searchContainerRef.current.contains(event.target as Node)) {
        setShowSuggestions(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Fetch dei suggerimenti mentre si digita
  useEffect(() => {
    if (searchQuery.length < 2) {
      setSuggestions([]);
      return;
    }
    
    const timeoutId = setTimeout(() => {
      axios.get(`${API_BASE_URL}/suggestions?q=${encodeURIComponent(searchQuery)}`)
        .then(res => {
          const newSuggestions = [`${searchQuery} (${lang === 'it' ? 'cerca tutti' : 'search all'})`, ...res.data];
          setSuggestions(newSuggestions);
          // Mostra i suggerimenti solo se l'input è l'elemento attualmente a fuoco
          if (document.activeElement && document.activeElement.tagName === 'INPUT') {
            setShowSuggestions(newSuggestions.length > 0);
          }
        })
        .catch(err => console.error("Errore autocompletamento", err));
    }, 200); // Debounce di 200ms

    return () => clearTimeout(timeoutId);
  }, [searchQuery]);

  const handleEvaluate = async (e?: React.FormEvent, directQuery?: string) => {
    if (e) e.preventDefault();
    const queryToUse = directQuery || searchQuery;
    if (!queryToUse) return;
    if (directQuery) setSearchQuery(directQuery);
    setShowSuggestions(false);
    setBrokerResult(null);
    setLoading(true);
    setError('');
    mp.trackSearch(queryToUse, year, lang);
    try {
      let url = `${API_BASE_URL}/evaluate?q=${encodeURIComponent(queryToUse)}&lang=${lang}`;
      if (year && !directQuery) url += `&year=${year}`;
      if (filterSource) url += `&source_filter=${encodeURIComponent(filterSource)}`;
      if (filterCountry) url += `&country_filter=${encodeURIComponent(filterCountry)}`;
      const res = await axios.get(url);
      setResult(res.data);
      setEvaluateListings(null);
      setEvaluateListingsPage(1);
      setEvaluateListingsSort('year_desc');
      addRecentSearch(queryToUse);
      mp.trackSearchResult(queryToUse, res.data.total_results_found, res.data.valuation?.average_price_eur, lang);
      addToast(`${res.data.total_results_found} annunci trovati`, 'success');
      // Load paginata in background
      loadEvaluateListings(queryToUse, year ? parseInt(year) : undefined, filterSource, filterCountry, 1, 'year_desc');
    } catch (err: any) {
      setResult(null);
      setError(err.response?.data?.detail || 'Errore durante la valutazione.');
      addToast(lang === 'it' ? 'Errore nella ricerca' : 'Search error', 'error');
    } finally {
      setLoading(false);
    }
  };

  const handleBrokerSearch = async () => {
    if (!brokerSource && !brokerCountry) return;
    setBrokerLoading(true);
    setResult(null);
    setError('');
    try {
      let url = `${API_BASE_URL}/broker-stats?lang=${lang}`;
      if (brokerSource) url += `&source=${encodeURIComponent(brokerSource)}`;
      if (brokerCountry) url += `&country=${encodeURIComponent(brokerCountry)}`;
      const res = await axios.get(url);
      setBrokerResult(res.data);
      addToast(`${res.data.total_listings} annunci trovati per questa fonte`, 'success');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Errore ricerca broker.');
      addToast(lang === 'it' ? 'Errore nella ricerca broker' : 'Broker search error', 'error');
    } finally {
      setBrokerLoading(false);
    }
  };

  const handleSellerSearch = async (sellerName?: string) => {
    const name = sellerName || sellerQuery;
    if (!name.trim()) return;
    setSellerLoading(true);
    setResult(null);
    setBrokerResult(null);
    setError('');
    mp.trackSellerSearch(name, lang);
    try {
      const res = await axios.get(`${API_BASE_URL}/seller-stats?seller=${encodeURIComponent(name)}&lang=${lang}`);
      setSellerResult(res.data);
      setShowSellerSuggestions(false);
      setSellerListingsPage(1);
      setSellerListingsSort('year_desc');
      setSellerListingsSourceFilter('');
      // Load first page of full listings
      loadSellerListings(name, 1, 'year_desc', '');
      addToast(`${res.data.total_listings} annunci trovati per "${res.data.seller}"`, 'success');
    } catch (err: any) {
      setError(err.response?.data?.detail || `Nessun dato per "${name}"`);
      addToast(lang === 'it' ? 'Agenzia non trovata nel database' : 'Agency not found in database', 'error');
    } finally {
      setSellerLoading(false);
    }
  };

  const loadEvaluateListings = async (
    query: string,
    yearVal: number | undefined,
    srcFilter: string,
    ctrFilter: string,
    page: number,
    sort: string,
  ) => {
    setEvaluateListingsLoading(true);
    try {
      let url = `${API_BASE_URL}/evaluate-listings?q=${encodeURIComponent(query)}&page=${page}&per_page=20&sort=${sort}`;
      if (yearVal) url += `&year=${yearVal}`;
      if (srcFilter) url += `&source_filter=${encodeURIComponent(srcFilter)}`;
      if (ctrFilter) url += `&country_filter=${encodeURIComponent(ctrFilter)}`;
      const res = await axios.get(url);
      setEvaluateListings(res.data);
      setEvaluateListingsPage(page);
    } catch {
      setEvaluateListings(null);
    } finally {
      setEvaluateListingsLoading(false);
    }
  };

  const loadSellerListings = async (
    sellerName: string,
    page: number,
    sort: string,
    sourceFilter: string,
  ) => {
    setSellerListingsLoading(true);
    try {
      let url = `${API_BASE_URL}/seller-listings?seller=${encodeURIComponent(sellerName)}&page=${page}&per_page=20&sort=${sort}`;
      if (sourceFilter) url += `&source_filter=${encodeURIComponent(sourceFilter)}`;
      const res = await axios.get(url);
      setSellerListings(res.data);
      setSellerListingsPage(page);
    } catch {
      setSellerListings(null);
    } finally {
      setSellerListingsLoading(false);
    }
  };



  const handleSuggestionClick = (suggestion: string) => {
    const query = suggestion.endsWith(` (${lang === 'it' ? 'cerca tutti' : 'search all'})`) ? suggestion.replace(` (${lang === 'it' ? 'cerca tutti' : 'search all'})`, '') : suggestion;
    setSearchQuery(query);
    handleEvaluate(undefined, query);
  };

  const formatPrice = (price: number) =>
    new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(price);

  const generatePDF = () => {
    const printConfig = document.title;
    document.title = `Batoo-Report-${result.query.replace(/\s+/g, '-')}`;
    mp.trackPDFExport(result.query);
    window.print();
    document.title = printConfig;
    addToast(lang === 'it' ? 'Report PDF in elaborazione...' : 'Processing PDF report...', 'info');
  };


  const themeClasses = {
    bgApp: isDark ? 'bg-slate-900' : 'bg-slate-50',
    textMain: isDark ? 'text-white' : 'text-slate-900',
    textMuted: isDark ? 'text-slate-300' : 'text-slate-600',
    textSubtle: isDark ? 'text-slate-400' : 'text-slate-500',
    overlay: isDark ? 'from-slate-950/80 via-slate-900/95 to-slate-950' : 'from-slate-100/80 via-white/95 to-slate-50',
    inputBg: isDark ? 'bg-slate-800/80' : 'bg-white',
    inputBorder: isDark ? 'border-slate-700' : 'border-slate-200',
    cardBg: isDark ? 'bg-slate-800/60' : 'bg-white',
    cardBorder: isDark ? 'border-slate-700/50' : 'border-slate-200',
    hoverBg: isDark ? 'hover:bg-slate-700/50' : 'hover:bg-slate-50',
    gradientCard: isDark ? 'from-blue-900/40 to-slate-800/60' : 'from-blue-50 to-white',
    chartAxis: isDark ? '#64748b' : '#94a3b8',
    tooltipBg: isDark ? '#1e293b' : '#ffffff',
    tooltipText: isDark ? '#f8fafc' : '#0f172a',
    inputSelect: isDark ? 'bg-slate-800 border-slate-700 text-white' : 'bg-white border-slate-200 text-slate-800',
  };

  const liquidityColors: Record<string, string> = {
    red: "text-red-500 bg-red-500/10 border-red-500/20",
    yellow: "text-yellow-500 bg-yellow-500/10 border-yellow-500/20",
    green: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20",
    blue: "text-blue-500 bg-blue-500/10 border-blue-500/20",
  };


  return (
    <div className={`min-h-screen ${themeClasses.bgApp} ${themeClasses.textMain} font-bricolage relative flex flex-col overflow-x-clip transition-colors duration-500`}>

      {/* Toast notifications */}
      <ToastContainer toasts={toasts} remove={removeToast} />

      {/* Sfondo dinamico */}
      <div className={`no-print absolute inset-0 z-0 bg-cover bg-center bg-no-repeat transition-all duration-1000 ease-out ${result ? 'opacity-10 scale-105' : 'opacity-40 scale-100'}`} style={{ backgroundImage: "url('https://images.unsplash.com/photo-1559253664-ca2fa90a1845?ixlib=rb-4.0.3&auto=format&fit=crop&w=2500&q=80')" }} />
      <div className={`no-print absolute inset-0 bg-gradient-to-b ${themeClasses.overlay} z-0 pointer-events-none transition-colors duration-500`}></div>

      {/* Global Animated Yacht */}
      {!result && !sellerResult && (
        <div className="no-print absolute inset-0 overflow-hidden pointer-events-none opacity-40 z-[1] mix-blend-overlay">
           <div className="animate-sail-everywhere absolute w-32 h-12 md:w-48 md:h-16">
              <img src="/yacht-top-view.svg" alt="yacht" className={`w-full h-full ${isDark ? 'brightness-75' : 'brightness-110 grayscale opacity-80'}`} />
           </div>
        </div>
      )}

      {/* Pulsante Tema e Lingua */}
      <div className="no-print fixed top-3 right-3 sm:top-6 sm:right-6 z-50 flex gap-1.5 sm:gap-2">
        <button
          onClick={toggleLang}
          className={`p-2 sm:p-3 rounded-full backdrop-blur-xl border transition-all duration-300 font-bold text-xs sm:text-sm flex items-center justify-center min-w-[36px] sm:min-w-[46px] ${isDark ? 'bg-slate-800/80 border-slate-700 text-slate-300 hover:bg-slate-700' : 'bg-white/90 border-slate-200 text-slate-600 hover:bg-slate-50 shadow-md'}`}
          title={lang === "it" ? "Passa a Inglese" : "Switch to Italian"}
        >
          {lang.toUpperCase()}
        </button>
        <button
          onClick={toggleTheme}
          className={`p-2 sm:p-3 rounded-full backdrop-blur-xl border transition-all duration-300 ${isDark ? 'bg-slate-800/80 border-slate-700 text-yellow-400 hover:bg-slate-700' : 'bg-white/90 border-slate-200 text-indigo-600 hover:bg-slate-50 shadow-md'}`}
        >
          {isDark ? <Sun className="w-4 h-4 sm:w-5 sm:h-5" /> : <Moon className="w-4 h-4 sm:w-5 sm:h-5" />}
        </button>
      </div>
      {/* Area Contenuto Principale */}
      <main className={`relative z-10 flex-1 flex flex-col items-center px-3 sm:px-6 lg:px-8 w-full transition-all duration-700 ease-in-out ${result ? 'justify-start pt-6 pb-20' : 'justify-center pt-24 sm:pt-20'}`}>
        
        {/* Titolo e Logo */}
        <div className={`no-print text-center transition-all duration-700 ease-[cubic-bezier(0.2,0.8,0.2,1)] ${result ? 'mb-4 mt-6 sm:mt-8 transform scale-[0.8] origin-top cursor-pointer hover:opacity-80' : 'mb-8 sm:mb-12'}`} onClick={() => { if (result) { setResult(null); setSearchQuery(''); } }}>
          <div className="flex flex-col items-center justify-center mb-3 sm:mb-4">
            <img 
              src="https://batoo.it/icons/batoo-logo-dark.svg?dpl=dpl_9aCViBvDC47Q54fZ2iSr4nXE9S5q" 
              alt="Batoo Logo" 
              className={`h-12 sm:h-16 md:h-20 mb-2 ${isDark && 'invert'}`} 
            />
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-black tracking-tighter">
              Price <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-cyan-400">Engine</span>
            </h1>
          </div>
          {result && (
            <div className="flex justify-center -mt-2 mb-2">
              <span className={`text-[10px] font-bold uppercase tracking-widest ${themeClasses.textSubtle} bg-slate-500/10 px-3 py-1 rounded-full flex items-center gap-1`}>
                <ChevronRight className="w-3 h-3 rotate-180" /> {lang === 'it' ? 'Torna alla Home' : 'Back to Home'}
              </span>
            </div>
          )}
          {!result && (
            <div className="animate-[fadeInUp_0.5s_ease-out]">
              <div className="inline-flex flex-col items-center justify-center mb-4 sm:mb-6 py-2 px-4 sm:px-6 rounded-2xl bg-blue-500/10 border border-blue-500/20 backdrop-blur-sm">
                <span className={`text-xs font-bold uppercase tracking-widest ${themeClasses.textSubtle} mb-1`}>{lang === 'it' ? 'Database Aggiornato' : 'Database Updated'}</span>
                <div className="flex items-baseline space-x-2">
                  <span className="text-2xl sm:text-3xl md:text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-300">
                    {totalBoatsDB > 0 ? <AnimatedCounter end={totalBoatsDB} duration={2500} /> : <span className="opacity-50">...</span>}
                  </span>
                  <span className={`text-sm font-semibold ${themeClasses.textMuted}`}>{lang === 'it' ? '+ barche analizzate' : '+ boats analyzed'}</span>
                </div>
              </div>
              <p className={`text-base sm:text-lg md:text-xl ${themeClasses.textMuted} max-w-xl mx-auto font-light leading-relaxed px-2`}>
                {lang === 'it' ? "L'intelligenza artificiale per il mercato nautico." : "Artificial intelligence for the nautical market."}<br className="hidden md:block"/> 
                {lang === 'it' ? "Scopri il valore reale di qualsiasi barca istantaneamente." : "Discover the real value of any boat instantly."}
              </p>
            </div>
          )}
        </div>

        {/* Tab switcher Modello / Broker — visibile solo in home */}
        {!result && !sellerResult && (
          <div className="no-print flex gap-2 mb-5 justify-center animate-[fadeInUp_0.4s_ease-out]">
            <button
              onClick={() => { setActiveTab('model'); setSellerResult(null); setBrokerResult(null); }}
              className={`px-5 py-2 rounded-full text-sm font-bold transition-all shadow-sm ${
                activeTab === 'model'
                  ? 'bg-blue-600 text-white shadow-blue-500/30'
                  : `${themeClasses.cardBg} border ${themeClasses.cardBorder} ${themeClasses.textMuted} hover:border-blue-500`}`}>
              🚤 {lang === 'it' ? 'Cerca Modello' : 'Search Model'}
            </button>
            <button
              onClick={() => { setActiveTab('broker'); setResult(null); }}
              className={`px-5 py-2 rounded-full text-sm font-bold transition-all shadow-sm ${
                activeTab === 'broker'
                  ? 'bg-indigo-600 text-white shadow-indigo-500/30'
                  : `${themeClasses.cardBg} border ${themeClasses.cardBorder} ${themeClasses.textMuted} hover:border-indigo-500`}`}>
              🏢 {lang === 'it' ? 'Cerca per Agenzia' : 'Search by Agency'}
            </button>
          </div>
        )}

        {/* ===== SELLER / AGENZIA SEARCH PANEL ===== */}
        {activeTab === 'broker' && !result && !sellerResult && (
          <div className="no-print w-full max-w-2xl animate-[fadeInUp_0.5s_ease-out]">
            <div className={`${themeClasses.cardBg} border ${themeClasses.cardBorder} p-8 rounded-3xl shadow-xl`}>
              <h3 className="font-bold text-xl mb-2">🏢 {lang === 'it' ? 'Cerca per Agenzia / Broker' : 'Search by Agency / Broker'}</h3>
              <p className={`text-sm ${themeClasses.textMuted} mb-6`}>
                {lang === 'it'
                  ? 'Digita il nome di un\'agenzia nautica per scoprirne l\'inventario e il posizionamento sul mercato.'
                  : 'Type an agency name to discover their inventory and market positioning.'}
              </p>
              <div className="relative">
                <div className={`flex items-center gap-3 ${themeClasses.inputBg} border ${themeClasses.inputBorder} rounded-2xl px-4 shadow`}>
                  <Search className={`w-5 h-5 shrink-0 ${themeClasses.textSubtle}`} />
                  <input
                    type="text"
                    placeholder={lang === 'it' ? 'Es: Timone Yachts (ricerca tutti i nomi simili)' : 'E.g.: Ocean Blue Yachts (finds all variations)'}
                    value={sellerQuery}
                    onChange={async e => {
                      setSellerQuery(e.target.value);
                      setShowSellerSuggestions(true);
                      if (e.target.value.length >= 2) {
                        try {
                          const r = await axios.get(`${API_BASE_URL}/sellers?q=${encodeURIComponent(e.target.value)}`);
                          setSellerSuggestions(r.data);
                        } catch { setSellerSuggestions([]); }
                      } else { setSellerSuggestions([]); }
                    }}
                    onKeyDown={e => { if (e.key === 'Enter') { e.preventDefault(); handleSellerSearch(); } }}
                    className={`flex-1 bg-transparent py-4 text-base focus:outline-none ${themeClasses.textMain}`}
                    autoComplete="off"
                  />
                  {sellerQuery && (
                    <button onClick={() => { setSellerQuery(''); setSellerSuggestions([]); }} className={themeClasses.textSubtle}>
                      <X className="w-4 h-4" />
                    </button>
                  )}
                </div>
                {/* Autocomplete dropdown — z-[9999] per non essere coperto da nulla */}
                {showSellerSuggestions && sellerSuggestions.length > 0 && (
                  <div className={`absolute z-[9999] top-full left-0 right-0 mt-2 rounded-2xl shadow-2xl border ${themeClasses.cardBorder} ${isDark ? 'bg-slate-800' : 'bg-white'} overflow-hidden animate-[fadeInUp_0.15s_ease-out]`}
                    style={{ boxShadow: '0 20px 40px rgba(0,0,0,0.35)' }}>
                    {/* Bottone principale "Cerca tutte le varianti" */}
                    <button
                      className="w-full flex items-center gap-3 px-4 py-3.5 bg-indigo-600 hover:bg-indigo-500 text-white transition-colors"
                      onClick={() => { setShowSellerSuggestions(false); handleSellerSearch(); }}>
                      <Search className="w-4 h-4 shrink-0" />
                      <div className="text-left">
                        <p className="text-sm font-bold">Cerca tutte le varianti di "{sellerQuery}"</p>
                        <p className="text-xs text-indigo-200">{sellerSuggestions.length} agenzie raggruppate insieme</p>
                      </div>
                    </button>
                    {/* Divider con label */}
                    <p className={`px-4 py-2 text-[10px] font-bold uppercase tracking-widest ${themeClasses.textSubtle} border-b ${themeClasses.cardBorder}`}>
                      {lang === 'it' ? "Oppure scegli un'agenzia specifica:" : "Or choose a specific agency:"}
                    </p>
                    {/* Lista singole agenzie */}
                    {sellerSuggestions.map((s, i) => (
                      <button key={i} className={`w-full text-left px-5 py-3 flex items-center justify-between ${themeClasses.hoverBg} transition-colors`}
                        onClick={() => { setSellerQuery(s.name); setShowSellerSuggestions(false); handleSellerSearch(s.name); }}>
                        <span className="font-medium text-sm">{s.name}</span>
                        <span className={`text-xs px-2 py-0.5 rounded-full font-semibold ${themeClasses.textSubtle} ${isDark ? 'bg-slate-700' : 'bg-slate-100'}`}>{s.count.toLocaleString('it-IT')} {lang === 'it' ? 'annunci' : 'listings'}</span>
                      </button>
                    ))}
                  </div>
                )}

              </div>
              <button onClick={() => handleSellerSearch()} disabled={sellerLoading || !sellerQuery.trim()}
                className="mt-4 w-full bg-indigo-600 hover:bg-indigo-500 text-white rounded-xl py-3.5 font-bold shadow-lg transition-all disabled:opacity-50 flex items-center justify-center gap-2">
                {sellerLoading
                  ? <div className="animate-spin h-5 w-5 border-b-2 border-white rounded-full" />
                  : <><Search className="w-4 h-4" /> {lang === 'it' ? 'Analizza Agenzia' : 'Analyze Agency'}</>}
              </button>
            </div>
          </div>
        )}

        {/* ===== SELLER RESULTS ===== */}
        {sellerResult && !sellerLoading && (
          <div className="w-full max-w-6xl mt-8 space-y-6 animate-[fadeInUp_0.5s_ease-out]">

            {/* Header card */}
            <div className={`${themeClasses.cardBg} border ${themeClasses.cardBorder} p-6 md:p-8 rounded-3xl shadow-lg`}>
              <div className="flex items-start justify-between gap-4 mb-6">
                <div className="flex-1 min-w-0">
                  <p className={`${themeClasses.textSubtle} text-xs font-bold uppercase tracking-widest mb-1`}>🏢 {lang === 'it' ? 'Profilo Agenzia' : 'Agency Profile'}</p>
                  <h2 className="text-2xl font-bold truncate">{sellerResult.seller}</h2>
                  {/* Varianti nome trovate nel DB */}
                  {sellerResult.matched_names?.length > 1 && (
                    <div className="mt-2">
                      <p className={`text-xs ${themeClasses.textSubtle} mb-1`}>{lang === 'it' ? 'Varianti nome trovate nel database:' : 'Name variations found in the database:'}</p>
                      <div className="flex flex-wrap gap-1.5">
                        {sellerResult.matched_names.map((n: string) => (
                          <span key={n} className={`text-xs px-2.5 py-1 rounded-full font-medium ${isDark ? 'bg-indigo-900/40 text-indigo-300 border border-indigo-700/50' : 'bg-indigo-50 text-indigo-700 border border-indigo-200'}`}>{n}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
                <button onClick={() => { setSellerResult(null); setSellerListings(null); setSellerQuery(''); }}
                  className={`shrink-0 px-4 py-2 rounded-xl text-xs font-bold ${isDark ? 'bg-slate-700 hover:bg-slate-600' : 'bg-slate-100 hover:bg-slate-200'} transition-all flex items-center gap-1`}>
                  <X className="w-3 h-3" /> {lang === 'it' ? 'Nuova ricerca' : 'New search'}
                </button>
              </div>

              {/* Metriche */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                {[
                  {label: lang==='it'?'Annunci totali':'Total listings', val: sellerResult.total_listings.toLocaleString('it-IT'), color:'text-blue-500'},
                  {label: lang==='it'?'Prezzo Medio':'Avg Price', val: formatPrice(sellerResult.avg_price), color:'text-emerald-500'},
                  {label: lang === 'it' ? 'Valore Centrale' : 'Central Val', val: formatPrice(sellerResult.median_price), color:'text-purple-500'},
                  {label: lang === 'it' ? 'Range prezzi' : 'Price range', val: `${formatPrice(sellerResult.min_price)} – ${formatPrice(sellerResult.max_price)}`, color:'text-amber-500'},
                ].map((m, i) => (
                  <div key={i} className={`${themeClasses.cardBg} border ${themeClasses.cardBorder} p-4 rounded-2xl`}>
                    <p className={`text-xs font-bold uppercase tracking-widest ${themeClasses.textSubtle} mb-1`}>{m.label}</p>
                    <p className={`text-xl font-black ${m.color}`}>{m.val}</p>
                  </div>
                ))}
              </div>

              {/* Split per portale — barre proporzionali */}
              {sellerResult.sources?.length > 0 && (
                <div className="mb-6">
                  <p className={`text-xs font-bold uppercase tracking-widest ${themeClasses.textSubtle} mb-3`}>
                    📊 {lang === 'it' ? 'Distribuzione per Portale' : 'Portal Distribution'}
                  </p>
                  <div className="space-y-3">
                    {(() => {
                      const maxCount = Math.max(...sellerResult.sources.map((s: any) => s.count));
                      return sellerResult.sources.map((s: any) => (
                        <button key={s.name} onClick={() => {
                          const newFilter = sellerListingsSourceFilter === s.name ? '' : s.name;
                          setSellerListingsSourceFilter(newFilter);
                          loadSellerListings(sellerResult.seller, 1, sellerListingsSort, newFilter);
                        }} className={`w-full text-left group transition-all`}>
                          <div className="flex items-center justify-between mb-1">
                            <div className="flex items-center gap-2">
                              <span className={`w-2.5 h-2.5 rounded-full`} style={{ backgroundColor: getSourceColor(s.name) }} />
                              <span className={`text-sm font-semibold ${sellerListingsSourceFilter === s.name ? 'text-blue-500' : ''}`}>{s.name}</span>
                              {sellerListingsSourceFilter === s.name && <span className="text-xs text-blue-500 font-bold">({lang === 'it' ? 'filtro attivo' : 'active filter'})</span>}
                            </div>
                            <span className={`text-sm font-bold ${themeClasses.textSubtle}`}>{s.count.toLocaleString('it-IT')} {lang === 'it' ? 'annunci' : 'listings'}</span>
                          </div>
                          <div className={`h-2 rounded-full ${isDark ? 'bg-slate-700' : 'bg-slate-100'} overflow-hidden`}>
                            <div className="h-full rounded-full transition-all duration-500 group-hover:opacity-80"
                              style={{ width: `${(s.count / maxCount) * 100}%`, backgroundColor: getSourceColor(s.name) }} />
                          </div>
                        </button>
                      ));
                    })()}
                  </div>
                </div>
              )}

              {/* Top modelli cliccabili */}
              {sellerResult.top_models?.length > 0 && (
                <div>
                  <p className={`text-xs font-bold uppercase tracking-widest ${themeClasses.textSubtle} mb-3`}>{lang==='it'?'Top Modelli':'Top Models'}</p>
                  <div className="flex flex-wrap gap-2">
                    {sellerResult.top_models.map((m: any, i: number) => (
                      <button key={i} onClick={() => { setActiveTab('model'); handleEvaluate(undefined, m.name); }}
                        className={`px-3 py-1.5 rounded-full text-xs font-semibold border ${themeClasses.cardBorder} ${themeClasses.cardBg} hover:border-blue-500 hover:text-blue-500 transition-colors`}>
                        {m.name} <span className={`ml-1 ${themeClasses.textSubtle}`}>({m.count})</span>
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Lista completa paginata */}
            <div className={`${themeClasses.cardBg} border ${themeClasses.cardBorder} rounded-3xl shadow-lg overflow-hidden`}>
              {/* Header con controlli */}
              <div className={`px-6 py-4 border-b ${themeClasses.cardBorder} flex flex-wrap items-center justify-between gap-3 bg-black/5`}>
                <div>
                  <h3 className="font-semibold text-sm">
                    {sellerListings ? `${sellerListings.total.toLocaleString('it-IT')} ${lang === 'it' ? 'annunci totali' : 'total listings'}${sellerListingsSourceFilter ? ` · ${sellerListingsSourceFilter}` : ''}` : lang === 'it' ? 'Tutti gli annunci' : 'All listings'}
                  </h3>
                  {sellerListings && <p className={`text-xs ${themeClasses.textSubtle}`}>{lang === 'it' ? 'Pagina' : 'Page'} {sellerListings.page} {lang === 'it' ? 'di' : 'of'} {sellerListings.total_pages}</p>}
                </div>
                <div className="flex items-center gap-2 flex-wrap">
                  {sellerListingsSourceFilter && (
                    <button onClick={() => { setSellerListingsSourceFilter(''); loadSellerListings(sellerResult.seller, 1, sellerListingsSort, ''); }}
                      className="text-xs px-3 py-1.5 rounded-full bg-blue-500/10 text-blue-500 border border-blue-500/30 flex items-center gap-1 font-semibold">
                      <X className="w-3 h-3" /> {sellerListingsSourceFilter}
                    </button>
                  )}
                  <select value={sellerListingsSort} onChange={e => {
                    setSellerListingsSort(e.target.value);
                    loadSellerListings(sellerResult.seller, 1, e.target.value, sellerListingsSourceFilter);
                  }} className={`text-xs ${themeClasses.inputSelect} border rounded-lg px-2 py-1.5 focus:outline-none`}>
                    <option value="year_desc">{lang === 'it' ? 'Anno ↓' : 'Year ↓'}</option>
                    <option value="year_asc">{lang === 'it' ? 'Anno ↑' : 'Year ↑'}</option>
                    <option value="price_desc">{lang === 'it' ? 'Prezzo ↓' : 'Price ↓'}</option>
                    <option value="price_asc">{lang === 'it' ? 'Prezzo ↑' : 'Price ↑'}</option>
                  </select>
                </div>
              </div>

              {/* Lista annunci */}
              {sellerListingsLoading ? (
                <div className="flex items-center justify-center py-16">
                  <div className="animate-spin h-8 w-8 border-b-2 border-blue-500 rounded-full" />
                </div>
              ) : sellerListings?.listings?.length > 0 ? (
                <div className="divide-y divide-slate-700/20">
                  {sellerListings.listings.map((boat: any, i: number) => (
                    <div key={i} className={`flex flex-col border-b last:border-b-0 ${isDark ? 'border-slate-800' : 'border-slate-100'} ${themeClasses.hoverBg} transition-colors`}>
                      <div onClick={() => window.open(boat.url, '_blank', 'noreferrer')} className="flex items-center gap-4 px-5 py-3.5 cursor-pointer group">
                        {boat.image_url ? (
                          <img src={`${API_BASE_URL}/proxy-image?url=${encodeURIComponent(boat.image_url)}`} alt=""
                            className="w-16 h-11 object-cover rounded-xl shrink-0" />
                        ) : (
                          <div className={`w-16 h-11 rounded-xl shrink-0 ${isDark ? 'bg-slate-700' : 'bg-slate-100'} flex items-center justify-center`}>
                            <span className="text-xl">🚤</span>
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-sm truncate">{boat.builder} {boat.model}</p>
                          <div className={`flex items-center gap-2 text-xs ${themeClasses.textSubtle} mt-0.5`}>
                            <span>{boat.year_built || '—'}</span>
                            {boat.length && <span>· {boat.length}m</span>}
                            {boat.country && <span>· {boat.country}</span>}
                            {boat.source && (
                              <span className="px-1.5 py-0.5 rounded-full text-[10px] font-bold" style={{ backgroundColor: getSourceColor(boat.source) + '22', color: getSourceColor(boat.source) }}>
                                {boat.source}
                              </span>
                            )}
                            {boat.is_duplicate && (
                              <span title={lang === 'it' ? 'Escluso dalle medie: stessa barca rilevata su altro portale/broker' : 'Excluded from averages: same boat detected on another portal/broker'}
                                className={`px-1.5 py-0.5 rounded-md text-[9px] uppercase font-extrabold tracking-wider border border-dashed cursor-help ${isDark ? 'text-slate-500 border-slate-600 bg-slate-800/40' : 'text-slate-400 border-slate-300 bg-slate-50'}`}>
                                ⊘ {lang === 'it' ? 'duplicato' : 'duplicate'}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="shrink-0 text-right flex flex-col items-end justify-center">
                          <div className={`font-bold text-sm ${boat.status === false ? 'line-through text-slate-400' : 'text-blue-500'}`}>
                            {boat.price_eur ? formatPrice(boat.price_eur) : '—'}
                          </div>
                          {boat.market_alignment_percent !== null && boat.market_alignment_percent !== undefined && (
                            <div className="mt-0.5" title={lang === 'it' ? `Valore di mercato stimato: ${formatPrice(boat.market_median_price)}` : `Estimated market value: ${formatPrice(boat.market_median_price)}`}>
                              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded-md ${
                                boat.market_alignment_percent < -5 ? 'bg-emerald-500/10 text-emerald-600 border border-emerald-500/20' :
                                boat.market_alignment_percent > 5 ? 'bg-red-500/10 text-red-600 border border-red-500/20' :
                                'bg-slate-500/10 text-slate-500 border border-slate-500/20'
                              }`}>
                                {boat.market_alignment_percent > 0 ? '+' : ''}{boat.market_alignment_percent}% {lang === 'it' ? 'vs mercato' : 'vs market'}
                              </span>
                            </div>
                          )}
                          {boat.status === false && <span className="text-[10px] font-bold text-red-500 mt-0.5">{lang === 'it' ? 'RIMOSSO' : 'REMOVED'}</span>}
                        </div>
                        <a href={boat.url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()} className="ml-2 p-2 rounded-lg hover:bg-blue-500/10 text-slate-400 hover:text-blue-500 transition-colors">
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className={`text-center py-12 ${themeClasses.textSubtle}`}>{lang === 'it' ? 'Nessun annuncio trovato' : 'No listings found'}</div>
              )}

              {/* Paginazione */}
              {sellerListings && sellerListings.total_pages > 1 && (
                <div className={`px-6 py-4 border-t ${themeClasses.cardBorder} flex items-center justify-center gap-2 flex-wrap`}>
                  <button disabled={sellerListings.page <= 1} onClick={() => loadSellerListings(sellerResult.seller, sellerListings.page - 1, sellerListingsSort, sellerListingsSourceFilter)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-semibold transition-all ${sellerListings.page <= 1 ? 'opacity-30 cursor-not-allowed' : `${themeClasses.cardBg} border ${themeClasses.cardBorder} hover:border-blue-500`}`}>
                    {lang === 'it' ? '← Prec' : '← Prev'}
                  </button>
                  {Array.from({ length: Math.min(sellerListings.total_pages, 7) }, (_, i) => {
                    const p = sellerListings.total_pages <= 7 ? i + 1 :
                      sellerListings.page <= 4 ? i + 1 :
                      sellerListings.page >= sellerListings.total_pages - 3 ? sellerListings.total_pages - 6 + i :
                      sellerListings.page - 3 + i;
                    return (
                      <button key={p} onClick={() => loadSellerListings(sellerResult.seller, p, sellerListingsSort, sellerListingsSourceFilter)}
                        className={`w-9 h-9 rounded-lg text-sm font-bold transition-all ${p === sellerListings.page ? 'bg-blue-600 text-white shadow-blue-500/30 shadow-md' : `${themeClasses.cardBg} border ${themeClasses.cardBorder} hover:border-blue-500`}`}>
                        {p}
                      </button>
                    );
                  })}
                  <button disabled={sellerListings.page >= sellerListings.total_pages} onClick={() => loadSellerListings(sellerResult.seller, sellerListings.page + 1, sellerListingsSort, sellerListingsSourceFilter)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-semibold transition-all ${sellerListings.page >= sellerListings.total_pages ? 'opacity-30 cursor-not-allowed' : `${themeClasses.cardBg} border ${themeClasses.cardBorder} hover:border-blue-500`}`}>
                    {lang === 'it' ? 'Succ →' : 'Next →'}
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ===== SEARCH BAR (only for model tab) ===== */}
        {activeTab === 'model' && (
        <div className={`no-print transition-all duration-700 z-40 flex flex-col items-center w-full relative ${result ? 'max-w-6xl' : 'max-w-3xl'}`}>
           <div className="w-full">
             <form onSubmit={(e) => handleEvaluate(e)} className="relative flex flex-col w-full gap-2 sm:gap-3">
                <div className="relative w-full" ref={searchContainerRef}>
                  <div className={`relative shadow-lg rounded-2xl ${themeClasses.inputBg} border ${themeClasses.inputBorder} z-20`}>
                  <div className="absolute inset-y-0 left-0 pl-4 sm:pl-6 flex items-center pointer-events-none">
                    <Search className={`w-5 h-5 sm:w-6 sm:h-6 transition-colors duration-300 ${searchQuery ? 'text-blue-500' : themeClasses.textSubtle}`} />
                  </div>
                  <input 
                    type="text"
                    placeholder={lang === 'it' ? "Es: Axopar 37, Beneteau Oceanis 41..." : "E.g.: Axopar 37, Beneteau Oceanis 41..."}
                    className={`w-full bg-transparent ${themeClasses.textMain} rounded-2xl py-3.5 sm:py-4 pl-11 sm:pl-14 pr-4 text-base sm:text-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all`}
                    value={searchQuery}
                    onChange={(e) => {
                      setSearchQuery(e.target.value);
                      setShowSuggestions(true);
                    }}
                    onFocus={() => {if (suggestions.length > 0) setShowSuggestions(true);}}
                    required
                    autoComplete="off"
                  />
                </div>
                
                {/* Menu a tendina Suggerimenti */}
                {showSuggestions && suggestions.length > 0 && (
                  <div className={`absolute top-full left-0 right-0 mt-2 py-2 rounded-2xl shadow-2xl border ${themeClasses.cardBorder} ${isDark ? 'bg-slate-800' : 'bg-white'} overflow-hidden z-50 animate-[fadeInUp_0.2s_ease-out]`}>
                    {suggestions.map((suggestion, idx) => (
                      <div 
                        key={idx} 
                        onClick={() => handleSuggestionClick(suggestion)}
                        className={`px-4 sm:px-6 py-3 cursor-pointer flex items-center ${themeClasses.hoverBg} transition-colors`}
                      >
                        <Search className={`w-4 h-4 mr-3 shrink-0 ${themeClasses.textSubtle}`} />
                        <span className="font-medium text-sm sm:text-base truncate">{suggestion}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              
              {/* Anno + Valuta — affiancati su mobile */}
              <div className="flex gap-2 sm:gap-3 w-full">
                <div className={`relative shrink-0 w-32 sm:w-40 shadow-md sm:shadow-lg rounded-2xl ${themeClasses.inputBg} border ${themeClasses.inputBorder} z-20`}>
                  <div className="absolute inset-y-0 left-0 pl-3 sm:pl-4 flex items-center pointer-events-none">
                    <Calendar className={`w-4 h-4 sm:w-5 sm:h-5 transition-colors duration-300 ${year ? 'text-blue-500' : themeClasses.textSubtle}`} />
                  </div>
                  <input 
                    type="number"
                    placeholder={lang === 'it' ? "Anno (Opz.)" : "Year (Opt.)"}
                    className={`w-full bg-transparent ${themeClasses.textMain} rounded-2xl py-3.5 sm:py-4 pl-9 sm:pl-11 pr-3 text-sm sm:text-base focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all`}
                    value={year}
                    onChange={(e) => setYear(e.target.value)}
                  />
                </div>
                <button 
                  type="submit"
                  disabled={loading || !searchQuery}
                  className="flex-1 bg-blue-600 hover:bg-blue-500 text-white rounded-2xl px-6 py-3.5 sm:py-4 font-bold shadow-md hover:shadow-lg transition-all duration-300 disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {loading ? <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div> : <><Search className="w-4 h-4 sm:w-5 sm:h-5" /> <span className="text-sm sm:text-base">{lang === 'it' ? 'Valuta' : 'Evaluate'}</span></>}
                </button>
              </div>
           </form>

           {/* Advanced Filters Toggle */}
           <div className="mt-3 flex justify-center">
             <button onClick={() => { if (!showFilters) mp.trackFiltersOpen(); setShowFilters(!showFilters); }}
               className={`flex items-center gap-2 px-4 py-1.5 rounded-full text-xs font-semibold border transition-all ${showFilters ? 'bg-blue-600 text-white border-blue-600' : `${themeClasses.cardBg} ${themeClasses.cardBorder} ${themeClasses.textMuted} hover:border-blue-500`}`}>
               <Filter className="w-3 h-3" />
               {lang === 'it' ? 'Filtri Avanzati' : 'Advanced Filters'}
               {showFilters ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
               {(filterSource || filterCountry || priceMin || priceMax) && <span className="w-1.5 h-1.5 rounded-full bg-blue-400 ml-1" />}
             </button>
           </div>
           {showFilters && (
             <div className={`mt-3 p-4 rounded-2xl border ${themeClasses.cardBorder} ${themeClasses.cardBg} grid grid-cols-2 md:grid-cols-4 gap-3 animate-[fadeInUp_0.2s_ease-out]`}>
               <div>
                 <label className={`text-[10px] font-bold uppercase tracking-widest ${themeClasses.textSubtle} mb-1 block`}>{lang === 'it' ? 'Fonte' : 'Source'}</label>
                 <select value={filterSource} onChange={e => setFilterSource(e.target.value)}
                   className={`w-full text-xs ${themeClasses.inputSelect} border rounded-lg px-2 py-2 focus:outline-none focus:ring-1 focus:ring-blue-500`}>
                   <option value="">{lang === 'it' ? 'Tutte' : 'All'}</option>
                   {sources.map(s => <option key={s.name} value={s.name}>{s.name}</option>)}
                 </select>
               </div>
               <div>
                 <label className={`text-[10px] font-bold uppercase tracking-widest ${themeClasses.textSubtle} mb-1 block`}>{lang === 'it' ? 'Paese' : 'Country'}</label>
                 <select value={filterCountry} onChange={e => setFilterCountry(e.target.value)}
                   className={`w-full text-xs ${themeClasses.inputSelect} border rounded-lg px-2 py-2 focus:outline-none focus:ring-1 focus:ring-blue-500`}>
                   <option value="">{lang === 'it' ? 'Tutti' : 'All'}</option>
                   {countries.map(c => <option key={c.name} value={c.name}>{c.name}</option>)}
                 </select>
               </div>
               <div>
                 <label className={`text-[10px] font-bold uppercase tracking-widest ${themeClasses.textSubtle} mb-1 block`}>Min €</label>
                 <input type="number" placeholder="0" value={priceMin} onChange={e => setPriceMin(e.target.value)}
                   className={`w-full text-xs ${themeClasses.inputSelect} border rounded-lg px-2 py-2 focus:outline-none focus:ring-1 focus:ring-blue-500`} />
               </div>
               <div>
                 <label className={`text-[10px] font-bold uppercase tracking-widest ${themeClasses.textSubtle} mb-1 block`}>Max €</label>
                 <input type="number" placeholder="∞" value={priceMax} onChange={e => setPriceMax(e.target.value)}
                   className={`w-full text-xs ${themeClasses.inputSelect} border rounded-lg px-2 py-2 focus:outline-none focus:ring-1 focus:ring-blue-500`} />
               </div>
             </div>
           )}

           {/* Recent Searches */}
           {!result && !loading && recentSearches.length > 0 && (
             <div className="mt-4 flex flex-wrap gap-2 justify-center animate-[fadeInUp_0.6s_ease-out]">
               <span className={`text-xs ${themeClasses.textSubtle} flex items-center self-center`}><Clock className="w-3 h-3 mr-1" /> {lang === 'it' ? 'Recenti:' : 'Recent:'}</span>
               {recentSearches.map((s, i) => (
                 <button key={i} onClick={() => handleEvaluate(undefined, s)}
                   className={`px-3 py-1.5 rounded-full text-xs font-medium border ${themeClasses.cardBorder} ${themeClasses.cardBg} hover:border-blue-500 hover:text-blue-500 transition-colors flex items-center gap-1`}>
                   <Search className="w-2.5 h-2.5 opacity-60" />{s}
                 </button>
               ))}
             </div>
           )}
           </div>

           {/* Quick Links */}
           {!result && !loading && (
             <>
               <div className="mt-8 flex flex-wrap justify-center gap-3 animate-[fadeInUp_0.8s_ease-out]">
                 <button onClick={() => { mp.trackQuickLink("Axopar 37"); handleEvaluate(undefined, "Axopar 37"); }} className={`px-4 py-2 rounded-full text-sm font-medium border ${themeClasses.cardBorder} ${themeClasses.cardBg} hover:border-blue-500 hover:text-blue-500 transition-colors flex items-center shadow-sm`}>
                   <Zap className="w-4 h-4 mr-1.5 text-yellow-500" /> {lang === 'it' ? 'Analizza' : 'Analyze'} Axopar 37
                 </button>
                 <button onClick={() => { mp.trackQuickLink("Beneteau Oceanis 41"); handleEvaluate(undefined, "Beneteau Oceanis 41"); }} className={`px-4 py-2 rounded-full text-sm font-medium border ${themeClasses.cardBorder} ${themeClasses.cardBg} hover:border-blue-500 hover:text-blue-500 transition-colors flex items-center shadow-sm`}>
                   <Zap className="w-4 h-4 mr-1.5 text-blue-400" /> Beneteau Oceanis 41
                 </button>
                 <button onClick={() => { mp.trackQuickLink("Pershing 62"); handleEvaluate(undefined, "Pershing 62"); }} className={`px-4 py-2 rounded-full text-sm font-medium border ${themeClasses.cardBorder} ${themeClasses.cardBg} hover:border-blue-500 hover:text-blue-500 transition-colors flex items-center shadow-sm`}>
                   <Zap className="w-4 h-4 mr-1.5 text-purple-500" /> Pershing 62
                 </button>
               </div>

               {/* Portals & Animated Boat */}
               <div className="mt-auto pt-16 w-full max-w-5xl mx-auto animate-[fadeInUp_1s_ease-out] relative h-40">
                 <p className={`text-center text-xs md:text-sm uppercase tracking-widest font-semibold mb-6 ${themeClasses.textSubtle} relative z-10`}>
                   {lang === 'it' ? 'Dati in tempo reale aggregati da' : 'Real-time data aggregated from'}
                 </p>
                 <div className="flex flex-wrap justify-center items-center gap-8 md:gap-16 mb-10 opacity-70 hover:opacity-100 transition-opacity duration-500 relative z-10">
                   <span className="text-xl md:text-2xl font-black text-slate-400 tracking-tight">Boat24</span>
                   <span className="text-xl md:text-2xl font-black text-slate-400 tracking-tight">Yachtall</span>
                   <span className="text-xl md:text-2xl font-black text-slate-400 tracking-tight">Mondial Broker</span>
                   <span className="text-xl md:text-2xl font-black text-slate-400 tracking-tight">iNautia</span>
                 </div>
               </div>
             </>
           )}

           {error && (
             <div className={`mt-4 p-4 ${isDark ? 'bg-red-500/10 border-red-500/30' : 'bg-red-50 border-red-200'} border rounded-2xl text-red-500 font-medium text-center flex items-center justify-center shadow-sm w-full`}>
               <AlertTriangle className="w-5 h-5 mr-2" /> <span>{error}</span>
             </div>
           )}
        </div>
        )} {/* end activeTab==='model' */}

        {/* Skeleton Loaders durante il caricamento */}
        {loading && (
          <div className="w-full max-w-6xl mt-8 space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-pulse">
              <div className="md:col-span-2 h-64 bg-slate-800/40 rounded-3xl border border-slate-700/50"></div>
              <div className="h-64 bg-slate-800/40 rounded-3xl border border-slate-700/50"></div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 animate-pulse">
              <div className="md:col-span-2 h-40 bg-slate-800/40 rounded-3xl border border-slate-700/50"></div>
              <div className="h-40 bg-slate-800/40 rounded-3xl border border-slate-700/50"></div>
              <div className="h-40 bg-slate-800/40 rounded-3xl border border-slate-700/50"></div>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 animate-pulse">
              <div className="h-96 bg-slate-800/40 rounded-3xl border border-slate-700/50"></div>
              <div className="h-96 bg-slate-800/40 rounded-3xl border border-slate-700/50"></div>
            </div>
          </div>
        )}

        {/* Risultati */}
        {result && !loading && (
          <div id="report-container" ref={reportRef} className="no-print w-full max-w-6xl mt-8 space-y-6 animate-[fadeInUp_0.5s_ease-out] relative">
            
              {/* Box Intestazione & Market Share */}
            <div className={`grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-6`}>
              <div className={`md:col-span-2 flex flex-col justify-center ${themeClasses.cardBg} backdrop-blur-xl border ${themeClasses.cardBorder} p-4 sm:p-6 md:p-8 rounded-3xl shadow-lg relative overflow-hidden`}>
                {/* Header: immagine + titolo + pdf button */}
                <div className="flex flex-col gap-3 mb-4">
                  <div className="flex items-center justify-between gap-2">
                    <div className="flex items-center gap-3 min-w-0">
                      {result.comparables?.[0]?.image_url && (
                        <div className="relative group shrink-0">
                          <img 
                            src={`${API_BASE_URL}/proxy-image?url=${encodeURIComponent(result.comparables[0].image_url)}`} 
                            crossOrigin="anonymous"
                            alt="boat preview" 
                            className="w-14 h-14 sm:w-16 sm:h-16 md:w-24 md:h-24 object-cover rounded-2xl shadow-md border border-slate-500/20 shrink-0" 
                          />
                        </div>
                      )}
                      <div className="min-w-0">
                        <p className={`${themeClasses.textSubtle} font-medium text-[10px] sm:text-xs mb-1 uppercase tracking-widest`}>{lang === 'it' ? 'Analisi di Mercato B2B' : 'B2B Market Analysis'}</p>
                        <h2 className="text-xl sm:text-2xl md:text-4xl font-bold capitalize truncate">{result.query}</h2>
                      </div>
                    </div>
                    <button 
                      onClick={generatePDF}
                      disabled={generatingPDF}
                      className={`no-print shrink-0 flex items-center gap-1.5 px-2.5 sm:px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-sm ${isDark ? 'bg-slate-700 text-white hover:bg-slate-600' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'}`}
                    >
                      {generatingPDF ? <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-current"></div> : <Download className="w-3.5 h-3.5" />}
                      <span className="hidden sm:inline">{generatingPDF ? (lang === 'it' ? 'Generando...' : 'Generating...') : (lang === 'it' ? 'Esporta PDF Report' : 'Export PDF Report')}</span>
                      <span className="sm:hidden">PDF</span>
                    </button>
                  </div>
                </div>
                
                <div className="flex flex-col sm:flex-row sm:items-center justify-between mt-2">
                <div className="flex flex-wrap gap-2">
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold ${isDark ? 'bg-blue-900/40 text-blue-400 border border-blue-500/20' : 'bg-blue-50 text-blue-700 border border-blue-100'}`}>
                    <Anchor className="w-3 h-3 mr-1.5" /> {result.identified_builder}
                  </span>
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold border ${liquidityColors[result.valuation.liquidity_color]}`}>
                    <Droplets className="w-3 h-3 mr-1.5" /> {lang === 'it' ? 'Liquidità:' : 'Liquidity:'} {result.valuation.liquidity_status}
                  </span>
                  {result.valuation.sold_last_week !== undefined && (
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold border ${isDark ? 'bg-indigo-900/40 text-indigo-400 border-indigo-500/20' : 'bg-indigo-50 text-indigo-700 border-indigo-100'}`}>
                      <TrendingUp className="w-3 h-3 mr-1.5" /> {lang === 'it' ? 'Vendite/Rimosse 7gg:' : 'Sold/Removed 7d:'} {result.valuation.sold_last_week}
                    </span>
                  )}
                </div>
                  {/* Confidence Score Widget */}
                  <div className="mt-4 sm:mt-0 flex flex-col items-start sm:items-end">
                     <div className="flex items-center space-x-2">
                        <span className={`text-[10px] font-bold uppercase tracking-tighter ${themeClasses.textSubtle}`}>{lang === 'it' ? 'Affidabilità Dato:' : 'Data Reliability:'}</span>
                        <div className="flex space-x-0.5">
                           {[1, 2, 3].map((step) => (
                             <div key={step} className={`h-1.5 w-6 rounded-full ${
                               result.valuation.confidence_label === 'Bassa' && step === 1 ? 'bg-red-500' :
                               result.valuation.confidence_label === 'Media' && step <= 2 ? 'bg-yellow-500' :
                               result.valuation.confidence_label === 'Alta' ? 'bg-emerald-500' : 'bg-slate-700'
                             }`} />
                           ))}
                        </div>
                        <span className={`text-xs font-black ${
                          result.valuation.confidence_label === 'Bassa' ? 'text-red-500' :
                          result.valuation.confidence_label === 'Media' ? 'text-yellow-500' : 'text-emerald-500'
                        }`}>{result.valuation.confidence_label}</span>
                     </div>
                  </div>
                </div>

                {/* Arbitrage Insight Text */}
                {result.valuation.market_share_countries?.length > 1 && (
                  <div className={`mt-6 p-4 rounded-2xl ${isDark ? 'bg-blue-500/5 border border-blue-500/10' : 'bg-blue-50 border border-blue-100'} flex items-start`}>
                    <ShieldCheck className="w-5 h-5 mr-3 text-blue-500 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-semibold mb-1 text-blue-500">{lang === 'it' ? 'Arbitraggio (Market Insight)' : 'Arbitrage (Market Insight)'}:</p>
                      <p className={`text-xs leading-relaxed ${themeClasses.textMuted}`}>
                        {(() => {
                          const countries = result.valuation.market_share_countries;
                          const cheaper = countries.reduce((prev: any, curr: any) => prev.avg_price < curr.avg_price ? prev : curr);
                          const expensive = countries.reduce((prev: any, curr: any) => prev.avg_price > curr.avg_price ? prev : curr);
                          const diff = ((expensive.avg_price - cheaper.avg_price) / cheaper.avg_price * 100).toFixed(0);
                          
                          if (parseFloat(diff) > 10) {
                            return lang === 'it' 
                              ? `Opportunità di arbitraggio tra ${cheaper.name.toUpperCase()} e ${expensive.name.toUpperCase()}. Acquistare in ${cheaper.name} potrebbe far risparmiare circa il ${diff}% rispetto ai prezzi in ${expensive.name}.`
                              : `Arbitrage opportunity between ${cheaper.name.toUpperCase()} and ${expensive.name.toUpperCase()}. Buying in ${cheaper.name} could save about ${diff}% compared to prices in ${expensive.name}.`;
                          } else {
                            return lang === 'it'
                              ? `Mercato europeo stabile e bilanciato tra i vari paesi analizzati (${countries.map((c:any) => c.name).join(', ')}).`
                              : `Stable and balanced European market across the analyzed countries (${countries.map((c:any) => c.name).join(', ')}).`;
                          }
                        })()}
                      </p>
                    </div>
                  </div>
                )}

                {/* AI Insight Text */}
                {result.ai_insight && (
                  <div className={`mt-3 p-4 rounded-2xl ${isDark ? 'bg-purple-500/5 border border-purple-500/10' : 'bg-purple-50 border border-purple-100'} flex items-start`}>
                    <Zap className="w-5 h-5 mr-3 text-purple-500 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm font-semibold mb-1 text-purple-500">AI Batoo Insight:</p>
                      <p className={`text-xs leading-relaxed ${themeClasses.textMuted}`}>
                        {result.ai_insight}
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* Box Nazioni con Mappa (Leaflet) */}
              <div className={`${themeClasses.cardBg} backdrop-blur-xl border ${themeClasses.cardBorder} p-6 rounded-3xl shadow-lg flex flex-col h-[380px] md:h-[420px] overflow-hidden`}>
                <p className={`${themeClasses.textSubtle} font-medium text-xs mb-3 uppercase tracking-widest flex items-center shrink-0`}>
                   <MapPin className="w-3.5 h-3.5 mr-1.5"/> {lang === 'it' ? 'Arbitraggio per Nazione' : 'Arbitrage by Country'}
                </p>
                {result.valuation.market_share_countries?.length > 0 ? (
                  <div className="flex-1 w-full relative flex flex-col min-h-0">
                    <div className="flex-1 w-full rounded-xl overflow-hidden mb-3 shadow-inner border border-slate-500/20 bg-slate-200 min-h-0 relative group">
                       <EuropeMap countriesData={result.valuation.market_share_countries} listings={result.comparables} isDark={isDark} lang={lang} />
                       <button 
                         onClick={() => setIsMapExpanded(true)} 
                         className="absolute top-2 right-2 p-2 bg-white/90 dark:bg-slate-800/90 rounded-lg shadow-md opacity-0 group-hover:opacity-100 transition-opacity z-[400] text-slate-800 dark:text-slate-200 hover:scale-105"
                         title={lang === 'it' ? 'Espandi Mappa' : 'Expand Map'}
                       >
                         <Maximize className="w-4 h-4" />
                       </button>
                    </div>
                    
                    {/* Legenda con Prezzi Medi per Nazione */}
                    <div className="shrink-0 pt-2 border-t border-slate-500/20 space-y-1.5 bg-transparent overflow-y-auto max-h-[100px] style-scrollbar">
                      {result.valuation.market_share_countries.slice(0, 4).map((c:any, i:number) => {
                        const isCheaper = c.avg_price < result.valuation.average_price_eur;
                        const priceDiff = Math.abs(c.avg_price - result.valuation.average_price_eur);
                        const diffPerc = ((priceDiff / result.valuation.average_price_eur) * 100).toFixed(0);
                        
                        return (
                          <div key={i} className="flex justify-between items-center text-xs">
                            <div className="flex items-center">
                              <span className={`w-2 h-2 rounded-full mr-2 ${isCheaper ? 'bg-emerald-500' : 'bg-red-500'}`}></span>
                              <span className={`${themeClasses.textMuted} font-semibold w-16 truncate`}>{c.name}</span>
                              <span className="text-[10px] text-slate-500 ml-1">({c.percentage}%)</span>
                            </div>
                            <div className="flex items-center space-x-2">
                              <span className="font-bold">{formatPrice(c.avg_price)}</span>
                              {c.avg_price > 0 && priceDiff > 100 && (
                                <span className={`text-[10px] font-bold ${isCheaper ? 'text-emerald-500' : 'text-red-500'}`}>
                                  {isCheaper ? '-' : '+'}{diffPerc}%
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ) : (
                  <div className="flex-1 flex items-center justify-center">
                    <span className="text-sm text-slate-500">{lang === 'it' ? 'Dati geografici non disponibili' : 'Geographical data not available'}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Metriche Principali (Broker Dashboard) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6">
              
              <div className={`sm:col-span-2 md:col-span-2 bg-gradient-to-br ${themeClasses.gradientCard} border ${isDark ? 'border-blue-500/30' : 'border-blue-200'} p-5 sm:p-8 rounded-3xl shadow-lg relative overflow-hidden group`}>
                <div className="absolute -top-4 -right-4 opacity-10 group-hover:scale-110 transition-transform duration-500">
                  <TrendingUp className="w-32 h-32 sm:w-40 sm:h-40 text-blue-500" />
                </div>
                <p className={`${isDark ? 'text-blue-400' : 'text-blue-700'} font-bold text-xs flex items-center uppercase tracking-widest mb-2`}>
                  <Euro className="w-4 h-4 mr-2"/> {lang === 'it' ? 'Valore di Mercato Medio' : 'Average Market Value'}
                </p>
                <div className="text-3xl sm:text-4xl md:text-5xl lg:text-6xl font-black mb-2 relative z-10 tracking-tight">
                  {formatPrice(result.valuation.average_price_eur)}
                </div>
                {result.valuation.median_price_eur && (
                  <div className="flex flex-wrap items-center gap-2 mb-3">
                    <span className={`text-xs ${themeClasses.textMuted} flex items-center gap-1`}>
                      <SlidersHorizontal className="w-3 h-3" /> {lang === 'it' ? 'Valore Centrale:' : 'Central Val:'}
                    </span>
                    <span className="text-sm font-bold">{formatPrice(result.valuation.median_price_eur)}</span>
                    {Math.abs(result.valuation.average_price_eur - result.valuation.median_price_eur) / result.valuation.average_price_eur > 0.1 && (
                      <span className="text-[10px] font-bold text-amber-500 bg-amber-500/10 border border-amber-500/20 px-1.5 py-0.5 rounded-full">{lang === 'it' ? 'Mercato asimmetrico' : 'Asymmetric market'}</span>
                    )}
                  </div>
                )}
                <div className={`flex flex-wrap gap-x-3 gap-y-1 text-xs font-medium px-3 py-1.5 rounded-lg w-fit ${isDark ? 'bg-slate-900/50 text-slate-300' : 'bg-white/80 text-slate-600'}`}>
                   <span>{lang === 'it' ? 'Su' : 'On'} <strong className={isDark ? 'text-white' : 'text-slate-900'}>{result.total_results_found}</strong> {lang === 'it' ? 'annunci unici' : 'unique listings'}</span>
                   <span className="hidden sm:inline text-slate-500">|</span>
                   <span>Min: <strong>{formatPrice(result.valuation.min_price_eur)}</strong></span>
                   <span className="hidden sm:inline text-slate-500">|</span>
                   <span>Max: <strong>{formatPrice(result.valuation.max_price_eur)}</strong></span>
                </div>
                {result.duplicates_removed > 0 && (
                  <div className={`flex items-center gap-1.5 text-[10px] font-semibold mt-1.5 px-2 py-1 rounded-lg w-fit ${
                    isDark ? 'bg-amber-500/10 text-amber-400 border border-amber-500/20' : 'bg-amber-50 text-amber-600 border border-amber-200'
                  }`}>
                    <span>⚡</span>
                    <span>
                      {lang === 'it'
                        ? `${result.duplicates_removed} duplicati cross-portale esclusi dalle medie`
                        : `${result.duplicates_removed} cross-portal duplicates excluded from averages`
                      }
                    </span>
                  </div>
                )}
              </div>

              <div className={`${themeClasses.cardBg} border ${themeClasses.cardBorder} p-4 sm:p-6 rounded-3xl shadow-lg flex flex-col justify-center`}>
                <p className={`${themeClasses.textSubtle} font-bold text-xs uppercase tracking-widest mb-2 flex items-center`}>
                  <TrendingDown className="w-4 h-4 mr-2 text-red-500"/> {lang === 'it' ? 'Perdita Valore Annua' : 'Annual Value Loss'}
                </p>
                {result.valuation.has_depreciation ? (
                  <>
                    <div className="text-3xl sm:text-4xl font-black text-red-500 mb-1 tracking-tighter">
                      -{result.valuation.depreciation_percent}%
                    </div>
                    <div className={`text-sm font-medium ${themeClasses.textMuted}`}>
                      {lang === 'it' ? 'circa' : 'approx'} {formatPrice(result.valuation.depreciation_value_eur)} / {lang === 'it' ? 'anno' : 'year'}
                    </div>
                  </>
                ) : (
                  <div className={`text-sm ${themeClasses.textSubtle}`}>{lang === 'it' ? 'Dati storici insufficienti' : 'Insufficient historical data'}</div>
                )}
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-1 gap-3 sm:gap-4">
                <div className={`${themeClasses.cardBg} border ${themeClasses.cardBorder} p-4 sm:p-5 rounded-3xl shadow-sm flex flex-col justify-center`}>
                  <p className={`${themeClasses.textSubtle} font-medium text-xs uppercase tracking-widest mb-1 flex items-center`}><Calendar className="w-3.5 h-3.5 mr-1.5"/> {lang === 'it' ? 'Età Media' : 'Average Age'}</p>
                  <div className="text-2xl sm:text-3xl font-bold">{result.valuation.median_age_years} <span className="text-sm text-slate-500 font-normal">{lang === 'it' ? 'anni' : 'years'}</span></div>
                </div>
                <div className={`${themeClasses.cardBg} border ${themeClasses.cardBorder} p-4 sm:p-5 rounded-3xl shadow-sm flex flex-col justify-center`}>
                  <p className={`${themeClasses.textSubtle} font-medium text-xs uppercase tracking-widest mb-1 flex items-center`}><Ruler className="w-3.5 h-3.5 mr-1.5"/> {lang === 'it' ? 'Prezzo/Metro' : 'Price/Meter'}</p>
                  <div className="text-xl sm:text-2xl font-bold">{result.valuation.average_price_per_meter > 0 ? formatPrice(result.valuation.average_price_per_meter) : 'N/D'}</div>
                </div>
              </div>

            </div>

            {/* Grafico Trend e Lista Ottimizzata */}
            <div className="w-full gap-4 sm:gap-6 mb-4">
              
              <div className={`${themeClasses.cardBg} border ${themeClasses.cardBorder} p-4 sm:p-6 md:p-8 rounded-3xl shadow-lg`}>
                <h3 className="text-sm sm:text-base font-semibold mb-1 flex items-center tracking-wide">
                  <Activity className="w-4 h-4 sm:w-5 sm:h-5 mr-2 sm:mr-3 text-blue-500" /> {lang === 'it' ? 'Andamento Storico Prezzi' : 'Historical Price Trend'}
                </h3>
                <p className={`text-xs ${themeClasses.textSubtle} mb-4 sm:mb-5`}>{lang === 'it' ? 'Banda grigia = fascia di mercato principale' : 'Gray band = main market range'}</p>
                <div className="h-[260px] sm:h-[330px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart data={result.valuation.price_trend?.length > 0 ? result.valuation.price_trend : []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke={isDark ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)"} vertical={false} />
                      <XAxis dataKey="year" stroke={themeClasses.chartAxis} fontSize={12} tickLine={false} axisLine={false} dy={10} />
                      <YAxis tickFormatter={(val: number) => `€${val/1000}k`} stroke={themeClasses.chartAxis} fontSize={12} tickLine={false} axisLine={false} dx={-5} />
                      <Tooltip
                        formatter={(value: any, name: string | undefined) => [
                          formatPrice(Number(value)),
                          name === 'avg_price' ? (lang === 'it' ? 'Valore Centrale' : 'Central Val') : name === 'q75' ? (lang === 'it' ? 'Fascia Alta' : 'High Range') : name === 'q25' ? (lang === 'it' ? 'Fascia Bassa' : 'Low Range') : (name ?? '')
                        ]}
                        labelFormatter={(label) => `${lang === 'it' ? 'Anno costruzione:' : 'Build year:'} ${label}`}
                        contentStyle={{ backgroundColor: themeClasses.tooltipBg, border: `1px solid ${isDark ? '#334155' : '#e2e8f0'}`, borderRadius: '12px', color: themeClasses.tooltipText, boxShadow: '0 4px 15px rgba(0,0,0,0.1)' }}
                      />
                      {/* IQR band */}
                      <Area type="monotone" dataKey="q75" stroke="none" fill="#3b82f6" fillOpacity={0.12} legendType="none" />
                      <Area type="monotone" dataKey="q25" stroke="none" fill={isDark ? '#0f172a' : '#f8fafc'} fillOpacity={1} legendType="none" />
                      {/* Q25/Q75 dashed lines */}
                      <Line type="monotone" dataKey="q75" stroke="#64748b" strokeDasharray="4 4" strokeWidth={1.5} dot={false} name="q75" />
                      <Line type="monotone" dataKey="q25" stroke="#64748b" strokeDasharray="4 4" strokeWidth={1.5} dot={false} name="q25" />
                      {/* Main median line */}
                      <Line type="monotone" dataKey="avg_price" stroke="#3b82f6" strokeWidth={4} dot={{ r: 5, fill: '#3b82f6', stroke: isDark ? '#1e293b' : '#fff', strokeWidth: 2 }} activeDot={{ r: 8, stroke: '#60a5fa', strokeWidth: 2 }} name="avg_price" />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              </div>

            </div>

            {/* Lista paginata completa annunci */}
            <div className={`${themeClasses.cardBg} border ${themeClasses.cardBorder} rounded-3xl shadow-lg overflow-hidden`}>
              {/* Header con controlli */}
              <div className={`px-6 py-4 border-b ${themeClasses.cardBorder} flex flex-wrap items-center justify-between gap-3 bg-black/5`}>
                <div>
                  <h3 className="font-semibold text-sm">
                    {evaluateListings
                      ? `${evaluateListings.total.toLocaleString('it-IT')} ${lang === 'it' ? 'annunci trovati' : 'listings found'} (${lang === 'it' ? 'tutti i portali' : 'all portals'})`
                      : (lang === 'it' ? 'Caricamento annunci...' : 'Loading listings...')}
                  </h3>
                  {evaluateListings && (
                    <p className={`text-xs ${themeClasses.textSubtle}`}>
                      {lang === 'it' ? 'Pagina' : 'Page'} {evaluateListings.page} {lang === 'it' ? 'di' : 'of'} {evaluateListings.total_pages}
                      {evaluateListings.outlier_range && (
                        <span className="ml-2 text-amber-500">
                          · {lang === 'it' ? 'range di mercato' : 'market range'}: {formatPrice(evaluateListings.outlier_range.p5)}–{formatPrice(evaluateListings.outlier_range.p95)}
                        </span>
                      )}
                      {result?.duplicates_removed > 0 && (
                        <span className={`ml-2 font-semibold ${isDark ? 'text-amber-400' : 'text-amber-600'}`}>
                          · {lang === 'it'
                              ? `medie calcolate su ${result.deduped_sample_size} barche uniche`
                              : `averages based on ${result.deduped_sample_size} unique boats`
                            }
                        </span>
                      )}
                    </p>
                  )}
                </div>
                <select value={evaluateListingsSort} onChange={e => {
                  const newSort = e.target.value;
                  setEvaluateListingsSort(newSort);
                  loadEvaluateListings(
                    searchQuery,
                    year ? parseInt(year) : undefined,
                    filterSource,
                    filterCountry,
                    1,
                    newSort
                  );
                }} className={`text-xs ${themeClasses.inputSelect} border rounded-lg px-2 py-1.5 focus:outline-none`}>
                  <option value="year_desc">{lang === 'it' ? 'Anno ↓' : 'Year ↓'}</option>
                  <option value="year_asc">{lang === 'it' ? 'Anno ↑' : 'Year ↑'}</option>
                  <option value="price_desc">{lang === 'it' ? 'Prezzo ↓' : 'Price ↓'}</option>
                  <option value="price_asc">{lang === 'it' ? 'Prezzo ↑' : 'Price ↑'}</option>
                </select>
              </div>

              {/* Lista annunci */}
              {evaluateListingsLoading ? (
                <div className="flex items-center justify-center py-16">
                  <div className="animate-spin h-8 w-8 border-b-2 border-blue-500 rounded-full" />
                </div>
              ) : evaluateListings?.listings?.length > 0 ? (
                <div className="divide-y divide-slate-700/20">
                  {evaluateListings.listings.map((boat: any, i: number) => (
                    <div key={i} className={`flex flex-col border-b last:border-b-0 ${isDark ? 'border-slate-800' : 'border-slate-100'} ${themeClasses.hoverBg} transition-colors`}>
                      <div onClick={() => window.open(boat.url, '_blank', 'noreferrer')} className="flex items-center gap-4 px-5 py-3.5 cursor-pointer group">
                        {boat.image_url ? (
                          <img src={`${API_BASE_URL}/proxy-image?url=${encodeURIComponent(boat.image_url)}`} alt=""
                            className="w-16 h-11 object-cover rounded-xl shrink-0" loading="lazy" />
                        ) : (
                          <div className={`w-16 h-11 rounded-xl shrink-0 ${isDark ? 'bg-slate-700' : 'bg-slate-100'} flex items-center justify-center`}>
                            <span className="text-xl">🚤</span>
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <p className="font-semibold text-sm truncate">{boat.builder} {boat.model}</p>
                          <div className={`flex items-center gap-2 text-xs ${themeClasses.textSubtle} mt-0.5 flex-wrap`}>
                            <span>{boat.year_built || '—'}</span>
                            {boat.length && <span>· {boat.length}m</span>}
                            {boat.country && <span>· {boat.country}</span>}
                            {boat.source && (
                              <span className="px-1.5 py-0.5 rounded-full text-[10px] font-bold" style={{ backgroundColor: getSourceColor(boat.source) + '22', color: getSourceColor(boat.source) }}>
                                {boat.source}
                              </span>
                            )}
                            {boat.is_outlier && (
                              <span className="px-1.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-500/10 text-amber-500 border border-amber-500/20">
                                ⚠ {lang === 'it' ? 'fuori mercato' : 'out of market'}
                              </span>
                            )}
                            {boat.is_duplicate && (
                              <span title={lang === 'it' ? 'Escluso dalle medie: stessa barca rilevata su altro portale/broker' : 'Excluded from averages: same boat detected on another portal/broker'}
                                className={`px-1.5 py-0.5 rounded-md text-[9px] uppercase font-extrabold tracking-wider border border-dashed cursor-help ${isDark ? 'text-slate-500 border-slate-600 bg-slate-800/40' : 'text-slate-400 border-slate-300 bg-slate-50'}`}>
                                ⊘ {lang === 'it' ? 'duplicato' : 'duplicate'}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="shrink-0 text-right">
                          <div className={`font-bold text-sm ${
                            boat.status === false ? 'line-through text-slate-400' :
                            boat.is_outlier ? 'text-amber-500' : 'text-blue-500'
                          }`}>
                            {boat.price_eur ? formatPrice(boat.price_eur) : '—'}
                          </div>
                          {boat.price_percentile !== null && boat.price_percentile !== undefined && !boat.is_outlier && (
                            <span className={`text-[10px] font-bold ${
                              boat.price_percentile < 30 ? 'text-emerald-500' :
                              boat.price_percentile > 70 ? 'text-red-500' : 'text-amber-500'
                            }`}>{boat.price_percentile < 30 ? (lang === 'it' ? 'Prezzo Ottimo' : 'Great Price') :
                                 boat.price_percentile > 70 ? (lang === 'it' ? 'Prezzo Alto' : 'High Price') :
                                 (lang === 'it' ? 'In Linea' : 'In Line')}</span>
                          )}
                          {boat.status === false && <span className="block text-[10px] font-bold text-red-500">{lang === 'it' ? 'RIMOSSO' : 'REMOVED'}</span>}
                        </div>
                        <a href={boat.url} target="_blank" rel="noreferrer" onClick={e => e.stopPropagation()} className="ml-2 p-2 rounded-lg hover:bg-blue-500/10 text-slate-400 hover:text-blue-500 transition-colors">
                          <ExternalLink className="w-4 h-4" />
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className={`text-center py-12 ${themeClasses.textSubtle}`}>{lang === 'it' ? 'Nessun annuncio trovato' : 'No listings found'}</div>
              )}

              {/* Paginazione */}
              {evaluateListings && evaluateListings.total_pages > 1 && (
                <div className={`px-6 py-4 border-t ${themeClasses.cardBorder} flex items-center justify-center gap-2 flex-wrap`}>
                  <button
                    disabled={evaluateListings.page <= 1}
                    onClick={() => loadEvaluateListings(searchQuery, year ? parseInt(year) : undefined, filterSource, filterCountry, evaluateListings.page - 1, evaluateListingsSort)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-semibold transition-all ${evaluateListings.page <= 1 ? 'opacity-30 cursor-not-allowed' : `${themeClasses.cardBg} border ${themeClasses.cardBorder} hover:border-blue-500`}`}>
                    {lang === 'it' ? '← Prec' : '← Prev'}
                  </button>
                  {Array.from({ length: Math.min(evaluateListings.total_pages, 7) }, (_, i) => {
                    const p = evaluateListings.total_pages <= 7 ? i + 1 :
                      evaluateListings.page <= 4 ? i + 1 :
                      evaluateListings.page >= evaluateListings.total_pages - 3 ? evaluateListings.total_pages - 6 + i :
                      evaluateListings.page - 3 + i;
                    return (
                      <button key={p}
                        onClick={() => loadEvaluateListings(searchQuery, year ? parseInt(year) : undefined, filterSource, filterCountry, p, evaluateListingsSort)}
                        className={`w-9 h-9 rounded-lg text-sm font-bold transition-all ${p === evaluateListings.page ? 'bg-blue-600 text-white shadow-blue-500/30 shadow-md' : `${themeClasses.cardBg} border ${themeClasses.cardBorder} hover:border-blue-500`}`}>
                        {p}
                      </button>
                    );
                  })}
                  <button
                    disabled={evaluateListings.page >= evaluateListings.total_pages}
                    onClick={() => loadEvaluateListings(searchQuery, year ? parseInt(year) : undefined, filterSource, filterCountry, evaluateListings.page + 1, evaluateListingsSort)}
                    className={`px-3 py-1.5 rounded-lg text-sm font-semibold transition-all ${evaluateListings.page >= evaluateListings.total_pages ? 'opacity-30 cursor-not-allowed' : `${themeClasses.cardBg} border ${themeClasses.cardBorder} hover:border-blue-500`}`}>
                    {lang === 'it' ? 'Succ →' : 'Next →'}
                  </button>
                </div>
              )}
            </div>

            {/* Source Breakdown + Personal Valuation (appended after results) */}
            {result && !loading && (
              <div className="w-full max-w-6xl grid grid-cols-1 lg:grid-cols-2 gap-6 mt-0">
                {result.valuation.source_breakdown?.length > 0 && (
                  <div className={`${themeClasses.cardBg} border ${themeClasses.cardBorder} p-6 rounded-3xl shadow-lg`}>
                    <h3 className="text-sm font-semibold mb-4 flex items-center">
                      <BarChart2 className="w-4 h-4 mr-2 text-indigo-500" /> {lang === 'it' ? 'Distribuzione per Fonte' : 'Distribution by Source'}
                    </h3>
                    <div className="h-[180px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={result.valuation.source_breakdown} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
                          <XAxis dataKey="source" stroke={themeClasses.chartAxis} fontSize={11} tickLine={false} axisLine={false} />
                          <YAxis stroke={themeClasses.chartAxis} fontSize={11} tickLine={false} axisLine={false} />
                          <Tooltip formatter={(value: any, _: any, props: any) => [`${value} (${props.payload.percentage}%) · avg ${formatPrice(props.payload.avg_price)}`, props.payload.source]}
                            contentStyle={{ backgroundColor: themeClasses.tooltipBg, border: `1px solid ${isDark ? '#334155' : '#e2e8f0'}`, borderRadius: '12px', color: themeClasses.tooltipText }} />
                          <Bar dataKey="count" radius={[6, 6, 0, 0]}>
                            {result.valuation.source_breakdown.map((_: any, i: number) => (
                              <Cell key={i} fill={getSourceColor(result.valuation.source_breakdown[i].source)} />
                            ))}
                          </Bar>
                        </BarChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                )}
                {result.valuation.price_trend?.length > 0 && (
                  <div className={`${themeClasses.cardBg} border ${themeClasses.cardBorder} p-6 rounded-3xl shadow-lg`}>
                    <h3 className="text-sm font-semibold mb-2 flex items-center">
                      <Star className="w-4 h-4 mr-2 text-amber-500" /> {lang === 'it' ? 'Stima Valore del Tuo Esemplare' : 'Estimate Your Boat Value'}
                    </h3>
                    <p className={`text-xs ${themeClasses.textSubtle} mb-4`}>{lang === 'it' ? "Inserisci l'anno di costruzione per una stima personalizzata." : 'Enter the build year for a personalized estimate.'}</p>
                    <input type="number" placeholder={lang === 'it' ? 'Anno (es. 2018)' : 'Year (e.g. 2018)'} value={personalYear} onChange={e => setPersonalYear(e.target.value)}
                      className={`w-full ${themeClasses.inputSelect} border rounded-xl px-4 py-3 focus:outline-none focus:ring-2 focus:ring-amber-500 text-sm`} />
                    {personalEstimate && (
                      <div className="mt-4 p-4 rounded-2xl bg-amber-500/10 border border-amber-500/20 animate-[fadeInUp_0.3s_ease-out]">
                        <p className="text-xs text-amber-500 font-bold uppercase tracking-widest mb-1">{lang === 'it' ? 'Stima di mercato' : 'Market estimate'}</p>
                        <p className="text-3xl font-black text-amber-500">{formatPrice(personalEstimate)}</p>
                        <p className={`text-xs ${themeClasses.textSubtle} mt-1`}>{lang === 'it' ? 'Basata sul trend storico — valore indicativo' : 'Based on historical trend — indicative value'}</p>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Fullscreen Map Modal */}
        {isMapExpanded && result && result.valuation.market_share_countries?.length > 0 && (
          <div className="fixed inset-0 z-[9999] bg-slate-900/95 backdrop-blur-md p-4 sm:p-8 flex flex-col animate-[fadeInUp_0.2s_ease-out]">
            <div className="flex justify-between items-center mb-4 max-w-6xl mx-auto w-full">
              <h2 className="text-xl sm:text-2xl font-bold text-white flex items-center">
                <MapPin className="w-6 h-6 mr-2 text-blue-500" />
                {lang === 'it' ? 'Mappa delle Imbarcazioni' : 'Boats Map'} - {result.query.toUpperCase()}
              </h2>
              <button 
                onClick={() => setIsMapExpanded(false)}
                className="p-2 sm:px-4 sm:py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white transition-colors flex items-center gap-2"
              >
                <Minimize className="w-5 h-5" />
                <span className="hidden sm:inline font-medium">{lang === 'it' ? 'Chiudi' : 'Close'}</span>
              </button>
            </div>
            <div className="flex-1 w-full max-w-6xl mx-auto bg-slate-200 dark:bg-slate-900 rounded-3xl overflow-hidden border border-slate-700/50 shadow-2xl relative">
               <EuropeMap countriesData={result.valuation.market_share_countries} listings={result.comparables} isDark={isDark} lang={lang} />
            </div>
          </div>
        )}

        {/* --- CUSTOM PDF PRINT LAYOUT --- */}
        {result && !loading && (
          <div id="pdf-exclusive-layout" className="hidden w-full font-sans text-black">
            {/* Intestazione */}
            <div className="flex justify-between items-center mb-6 border-b-2 border-slate-200 pb-4">
              <div className="flex items-center">
                <img src="https://batoo.it/icons/batoo-logo-dark.svg?dpl=dpl_9aCViBvDC47Q54fZ2iSr4nXE9S5q" alt="Batoo Logo" className="h-6 opacity-30 invert" />
                <h1 className="text-2xl font-black text-slate-800 ml-3">{lang === 'it' ? 'Report di Mercato:' : 'Market Report:'} {result.query.toUpperCase()}</h1>
              </div>
              <div className="text-right text-xs text-slate-500 font-medium">
                {lang === 'it' ? 'Data Elaborazione:' : 'Processing Date:'} {new Date().toLocaleDateString('it-IT')}
              </div>
            </div>

            {/* Dati Principali */}
            <div className="flex gap-6 mb-6">
              {/* Foto Auto-selezionata */}
              <div className="w-1/3 shrink-0">
                {result.comparables?.[0]?.image_url ? (
                  <img 
                    src={`${API_BASE_URL}/proxy-image?url=${encodeURIComponent(result.comparables[0].image_url)}`} 
                    alt="boat" 
                    crossOrigin="anonymous"
                    className="w-full h-48 object-cover rounded-xl border-2 border-slate-100"
                  />
                ) : (
                  <div className="w-full h-48 bg-slate-100 rounded-xl flex items-center justify-center text-slate-300 border-2 border-slate-100">
                    <Anchor className="w-10 h-10" />
                  </div>
                )}
              </div>
              
              {/* Box Numerici */}
              <div className="flex-1 flex flex-col justify-center space-y-4">
                <div className="bg-blue-50/50 rounded-xl p-5 border border-blue-100">
                  <p className="text-[10px] text-blue-600 uppercase font-bold tracking-widest mb-1">{lang === 'it' ? 'Prezzo Medio Stimato' : 'Estimated Average Price'}</p>
                  <div className="text-4xl font-black text-slate-800 tracking-tight">{formatPrice(result.valuation.average_price_eur)}</div>
                  <p className="text-xs text-slate-500 mt-1 font-medium bg-white px-2 py-1 inline-block rounded border border-slate-100">
                    Min: {formatPrice(result.valuation.min_price_eur)} - Max: {formatPrice(result.valuation.max_price_eur)}
                  </p>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                    <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mb-0.5">{lang === "it" ? "Età Media" : "Average Age"}</p>
                    <div className="text-xl font-bold text-slate-700">{result.valuation.median_age_years} <span className="text-sm font-medium">{lang === "it" ? "anni" : "years"}</span></div>
                  </div>
                  <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
                    <p className="text-[10px] text-slate-500 uppercase font-bold tracking-widest mb-0.5">{lang === "it" ? "Prezzo al Metro" : "Price per Meter"}</p>
                    <div className="text-xl font-bold text-slate-700">{result.valuation.average_price_per_meter > 0 ? formatPrice(result.valuation.average_price_per_meter) : 'N/D'}</div>
                  </div>
                </div>
              </div>
            </div>

            {/* AI Insight */}
            <div className="mb-6">
              <h3 className="text-[10px] uppercase font-bold tracking-widest text-slate-400 mb-2">Batoo AI Insight</h3>
              <p className="text-sm leading-relaxed text-slate-700 border-l-4 border-blue-500 pl-4 py-1">
                {result.ai_insight}
              </p>
            </div>

            {/* Arbitraggio Geografico */}
            {result.valuation.market_share_countries?.length > 1 && (
              <div className="mb-6">
                <h3 className="text-[10px] uppercase font-bold tracking-widest text-slate-400 mb-2">Arbitraggio (Market Insight)</h3>
                <p className="text-sm leading-relaxed text-slate-700 border-l-4 border-emerald-500 pl-4 py-1 bg-emerald-50/30">
                  {(() => {
                    const countries = result.valuation.market_share_countries;
                    const cheaper = countries.reduce((prev: any, curr: any) => prev.avg_price < curr.avg_price ? prev : curr);
                    const expensive = countries.reduce((prev: any, curr: any) => prev.avg_price > curr.avg_price ? prev : curr);
                    const diff = ((expensive.avg_price - cheaper.avg_price) / cheaper.avg_price * 100).toFixed(0);
                    
                    if (parseFloat(diff) > 10) {
                      return lang === 'it' 
                        ? `Opportunità di arbitraggio tra ${cheaper.name.toUpperCase()} e ${expensive.name.toUpperCase()}. Acquistare in ${cheaper.name} potrebbe far risparmiare circa il ${diff}% rispetto ai prezzi in ${expensive.name}.`
                        : `Arbitrage opportunity between ${cheaper.name.toUpperCase()} and ${expensive.name.toUpperCase()}. Buying in ${cheaper.name} could save about ${diff}% compared to prices in ${expensive.name}.`;
                    } else {
                      return lang === 'it'
                        ? `Mercato europeo stabile e bilanciato tra i vari paesi analizzati (${countries.map((c:any) => c.name).join(', ')}).`
                        : `Stable and balanced European market across the analyzed countries (${countries.map((c:any) => c.name).join(', ')}).`;
                    }
                  })()}
                </p>
              </div>
            )}

            {/* Trend Chart (Shrunk down for PDF) */}
            {result.valuation.price_trend?.length > 0 && (
              <div className="mb-6 h-[180px] w-full border border-slate-100 rounded-xl p-4 bg-slate-50/50 overflow-hidden">
                <h3 className="text-[10px] uppercase font-bold tracking-widest text-slate-400 mb-2">{lang === "it" ? "Andamento Storico" : "Historical Trend"}</h3>
                <div style={{ width: '650px', height: '130px' }}>
                  <LineChart width={650} height={130} data={result.valuation.price_trend} margin={{ top: 5, right: 20, left: 20, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                    <XAxis dataKey="year" stroke="#94a3b8" fontSize={9} tickLine={false} axisLine={false} />
                    <YAxis tickFormatter={(val) => `€${val/1000}k`} stroke="#94a3b8" fontSize={9} tickLine={false} axisLine={false} width={50} />
                    <Line type="monotone" dataKey="avg_price" stroke="#3b82f6" strokeWidth={2} dot={{ r: 3, fill: '#3b82f6', stroke: '#fff', strokeWidth: 1.5 }} isAnimationActive={false} />
                  </LineChart>
                </div>
              </div>
            )}

            {/* Comparabili Recenti */}
            <div>
              <h3 className="text-[10px] uppercase font-bold tracking-widest text-slate-400 mb-3 border-b border-slate-200 pb-2">{lang === "it" ? "Top 5 Annunci Recenti Rilevati" : "Top 5 Recent Listings Detected"}</h3>
              <div className="space-y-2">
                {result.comparables.slice(0, 5).map((boat: any, idx: number) => (
                  <div key={idx} className="flex justify-between items-center py-2 border-b border-slate-100 last:border-0">
                    <div className="flex items-center space-x-4">
                       {boat.image_url ? (
                         <img src={`${API_BASE_URL}/proxy-image?url=${encodeURIComponent(boat.image_url)}`} crossOrigin="anonymous" className="w-14 h-10 object-cover rounded shadow-sm border border-slate-200" />
                       ) : (
                         <div className="w-14 h-10 bg-slate-100 rounded border border-slate-200 flex items-center justify-center"><Anchor className="w-3 h-3 text-slate-300" /></div>
                       )}
                       <div>
                         <p className={`font-bold text-xs text-slate-800 ${boat.status === false ? 'line-through opacity-60' : ''}`}>{boat.builder} {boat.model}</p>
                         <p className="text-[10px] text-slate-500 mt-0.5 font-medium">{lang === "it" ? "Anno" : "Year"}: {boat.year_built} &bull; {lang === "it" ? "Luogo" : "Location"}: {boat.country || "N/D"} {boat.status === false ? (lang === "it" ? "(Rimosso)" : "(Removed)") : ""} {boat.source && `• ${lang === "it" ? "Fonte" : "Source"}: ${boat.source}`}</p>
                       </div>
                    </div>
                    <div className={`font-black text-sm ${boat.status === false ? 'text-slate-400 line-through' : 'text-blue-600'}`}>
                      {formatPrice(boat.price_eur)}
                    </div>
                  </div>
                ))}
              </div>
            </div>
            
            <div className="mt-6 text-center text-[9px] text-slate-400 uppercase font-bold tracking-widest pt-4 border-t border-slate-200">
               {lang === "it" ? "Generato tramite Batoo Price Engine B2B. I dati riportati rappresentano stime correnti di mercato." : "Generated via Batoo Price Engine B2B. Data reported represent current market estimates."}
            </div>

            {/* SECONDA PAGINA: Lista Completa */}
            {result.comparables.length > 5 && (
              <div style={{ pageBreakBefore: 'always' }} className="pt-8">
                 <div className="flex justify-between items-center mb-6 border-b-2 border-slate-200 pb-4">
                  <div className="flex items-center">
                    <h2 className="text-xl font-black text-slate-800">{lang === "it" ? "Lista Completa Imbarcazioni Rilevate" : "Complete List of Detected Listings"}</h2>
                  </div>
                  <div className="text-right text-xs text-slate-500 font-medium">
                    {result.comparables.length} {lang === "it" ? "Annunci" : "Listings"}
                  </div>
                </div>

                <div className="space-y-4">
                  {result.comparables.map((boat: any, idx: number) => (
                    <div key={`full-${idx}`} className="flex justify-between items-center py-3 border-b border-slate-100 last:border-0">
                      <div className="flex items-center space-x-4">
                         {boat.image_url ? (
                           <img src={`${API_BASE_URL}/proxy-image?url=${encodeURIComponent(boat.image_url)}`} crossOrigin="anonymous" className="w-20 h-14 object-cover rounded shadow-sm border border-slate-200" />
                         ) : (
                           <div className="w-20 h-14 bg-slate-100 rounded border border-slate-200 flex items-center justify-center"><Anchor className="w-5 h-5 text-slate-300" /></div>
                         )}
                         <div className="flex flex-col">
                           <p className={`font-bold text-sm text-slate-800 ${boat.status === false ? 'line-through opacity-60' : ''}`}>{boat.builder} {boat.model}</p>
                           <p className="text-xs text-slate-500 mt-0.5 font-medium">{lang === "it" ? "Anno" : "Year"}: {boat.year_built} &bull; {lang === "it" ? "Luogo" : "Location"}: {boat.country || "N/D"} {boat.status === false ? (lang === "it" ? "(Rimosso)" : "(Removed)") : ""} {boat.source && `• ${lang === "it" ? "Fonte" : "Source"}: ${boat.source}`}</p>
                           <a href={boat.url} target="_blank" rel="noreferrer" className="text-[10px] text-blue-500 hover:text-blue-700 underline mt-1 font-semibold flex items-center gap-1">
                             {lang === "it" ? "Clicca qui per visionare" : "Click here to view"} <ChevronRight className="w-3 h-3" />
                           </a>
                         </div>
                      </div>
                      <div className={`font-black text-lg ${boat.status === false ? 'text-slate-400 line-through' : 'text-blue-600'}`}>
                        {formatPrice(boat.price_eur)}
                      </div>
                    </div>
                  ))}
                </div>
                
                <div className="mt-6 text-center text-[9px] text-slate-400 uppercase font-bold tracking-widest pt-4 border-t border-slate-200 break-inside-avoid">
                   {lang === "it" ? "Documento Integrativo - Batoo Price Engine B2B. I link originali sono esterni al sistema." : "Supplementary Document - Batoo Price Engine B2B. Original links are external to the system."}
                </div>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Footer Istituzionale */}
      <footer className={`no-print relative z-10 w-full py-4 sm:py-6 mt-auto border-t ${isDark ? 'border-white/10 bg-slate-950/80 text-slate-400' : 'border-slate-200 bg-slate-100/80 text-slate-500'} backdrop-blur-md`}>
        <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2 text-xs">
          <div className="flex items-center">
            <img 
              src="https://batoo.it/icons/batoo-logo-dark.svg?dpl=dpl_9aCViBvDC47Q54fZ2iSr4nXE9S5q" 
              alt="Batoo Logo" 
              className={`h-4 mr-2 ${isDark && 'invert'}`} 
            />
            <span>Price Engine B2B</span>
          </div>
          <div className="text-center sm:text-right">
            <p>{lang === 'it' ? 'Algoritmo proprietario' : 'Proprietary algorithm'} · <strong className={isDark ? 'text-white' : 'text-slate-700'}>{totalBoatsDB > 0 ? (Math.floor(totalBoatsDB/100)*100).toLocaleString('it-IT') + '+' : '...'}</strong> {lang === 'it' ? 'annunci in Europa' : 'listings in Europe'}.</p>
            <p className="mt-0.5 opacity-75 hidden sm:block">{lang === 'it' ? "I dati forniti sono valutazioni basate sull'andamento in tempo reale del mercato nautico." : "The provided data are valuations based on real-time nautical market trends."}</p>
          </div>
        </div>
      </footer>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,200..800&display=swap');
        
        .font-bricolage {
          font-family: 'Bricolage Grotesque', sans-serif;
        }
        
        @keyframes fadeInUp {
          from { opacity: 0; transform: translateY(20px); }
          to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes scroll {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        
        .mask-image-gradient {
          mask-image: linear-gradient(to right, transparent, black 10%, black 90%, transparent);
          -webkit-mask-image: linear-gradient(to right, transparent, black 10%, black 90%, transparent);
        }
        
        .style-scrollbar::-webkit-scrollbar { width: 6px; }
        .style-scrollbar::-webkit-scrollbar-track { background: transparent; }
        .style-scrollbar::-webkit-scrollbar-thumb { background-color: ${isDark ? '#334155' : '#cbd5e1'}; border-radius: 10px; }

        @media screen {
          #pdf-exclusive-layout { display: none !important; }
        }

        @media print {
          body, html { 
            background: white !important; 
            margin: 0 !important;
            padding: 0 !important;
          }
          .no-print { display: none !important; }
          
          #pdf-exclusive-layout {
            display: block !important;
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            padding: 2cm; /* Margine A4 Standard ridotto per fare spazio */
            background: white !important;
            box-sizing: border-box;
            zoom: 0.70; /* Ulteriore riduzione per sicurezza su multi-pagina */
            page-break-inside: avoid;
          }
          
          * { 
            -webkit-print-color-adjust: exact !important; 
            print-color-adjust: exact !important; 
          }
        }
      `}</style>
    </div>
  );
}

export default App;
