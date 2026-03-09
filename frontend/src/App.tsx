import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Search, Anchor, Euro, Calendar, TrendingUp, TrendingDown, ChevronRight, BarChart2, Sun, Moon, AlertTriangle, MapPin, Ruler, Activity, Droplets, Zap, Download, ShieldCheck, FileText } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';

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
import html2canvas from 'html2canvas';
import { jsPDF } from 'jspdf';

const API_BASE_URL = 'http://127.0.0.1:8000';

function App() {
  const [searchQuery, setSearchQuery] = useState('');
  const [year, setYear] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const [carouselImages, setCarouselImages] = useState<string[]>([]);
  const [totalBoatsDB, setTotalBoatsDB] = useState<number>(0);
  
  useEffect(() => {
    // Fetch system status and total boats
    axios.get(`${API_BASE_URL}/`)
      .then(res => {
        if (res.data && res.data.total_boats) {
          setTotalBoatsDB(res.data.total_boats);
        }
      })
      .catch(err => console.error("Error fetching system info", err));

    // Fetch random carousel images from DB on mount
    axios.get(`${API_BASE_URL}/carousel-images`)
      .then(res => {
        if(res.data && res.data.length > 0) {
          setCarouselImages(res.data);
        }
      })
      .catch(err => console.error("Error fetching carousel images", err));
  }, []);

  // Sticky bar e PDF
  const [isSticky, setIsSticky] = useState(false);
  const [generatingPDF, setGeneratingPDF] = useState(false);
  const reportRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleScroll = () => {
      setIsSticky(window.scrollY > 150);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const generatePDF = () => {
    window.print();
  };
  
  // Autocompletamento
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const searchContainerRef = useRef<HTMLDivElement>(null);

  // Tema Chiaro/Scuro
  const [isDark, setIsDark] = useState(false);
  const toggleTheme = () => setIsDark(!isDark);

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
          setSuggestions(res.data);
          // Mostra i suggerimenti solo se l'input è l'elemento attualmente a fuoco
          if (document.activeElement && document.activeElement.tagName === 'INPUT') {
            setShowSuggestions(res.data.length > 0);
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
    setShowSuggestions(false); // Chiudi suggerimenti

    setLoading(true);
    setError('');

    try {
      let url = `${API_BASE_URL}/evaluate?q=${encodeURIComponent(queryToUse)}`;
      if (year && !directQuery) url += `&year=${year}`;

      const res = await axios.get(url);
      setResult(res.data);
    } catch (err: any) {
      setResult(null);
      setError(err.response?.data?.detail || 'Errore durante la valutazione.');
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    setSearchQuery(suggestion);
    handleEvaluate(undefined, suggestion);
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(price);
  };

  // Classi dinamiche basate sul tema
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
    tooltipText: isDark ? '#f8fafc' : '#0f172a'
  };

  // Colori liquidità
  const liquidityColors: Record<string, string> = {
    red: "text-red-500 bg-red-500/10 border-red-500/20",
    yellow: "text-yellow-500 bg-yellow-500/10 border-yellow-500/20",
    green: "text-emerald-500 bg-emerald-500/10 border-emerald-500/20",
    blue: "text-blue-500 bg-blue-500/10 border-blue-500/20",
  };

  return (
    <div className={`min-h-screen ${themeClasses.bgApp} ${themeClasses.textMain} font-bricolage relative flex flex-col overflow-x-clip transition-colors duration-500`}>
      
      {/* Sfondo dinamico */}
      <div 
        className={`absolute inset-0 z-0 bg-cover bg-center bg-no-repeat transition-all duration-1000 ease-out ${result ? 'opacity-10 scale-105' : 'opacity-40 scale-100'}`}
        style={{ backgroundImage: "url('https://images.unsplash.com/photo-1559253664-ca2fa90a1845?ixlib=rb-4.0.3&auto=format&fit=crop&w=2500&q=80')" }}
      />
      <div className={`absolute inset-0 bg-gradient-to-b ${themeClasses.overlay} z-0 pointer-events-none transition-colors duration-500`}></div>

      {/* Pulsante Tema */}
      <button 
        onClick={toggleTheme}
        className={`absolute top-6 right-6 z-50 p-3 rounded-full backdrop-blur-xl border transition-all duration-300 ${isDark ? 'bg-slate-800/80 border-slate-700 text-yellow-400 hover:bg-slate-700' : 'bg-white border-slate-200 text-indigo-600 hover:bg-slate-50 shadow-md'}`}
      >
        {isDark ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
      </button>

      {/* Area Contenuto Principale */}
      <main className={`relative z-10 flex-1 flex flex-col items-center px-4 sm:px-6 lg:px-8 w-full transition-all duration-700 ease-in-out ${result ? 'justify-start pt-8 pb-20' : 'justify-center'}`}>
        
        {/* Titolo e Logo */}
        <div className={`text-center transition-all duration-700 ease-[cubic-bezier(0.2,0.8,0.2,1)] ${result ? 'mb-6 transform scale-75 origin-top' : 'mb-12'}`}>
          <div className="flex flex-col items-center justify-center mb-4">
            <img 
              src="https://batoo.it/icons/batoo-logo-dark.svg?dpl=dpl_9aCViBvDC47Q54fZ2iSr4nXE9S5q" 
              alt="Batoo Logo" 
              className={`h-16 md:h-20 mb-2 ${isDark && 'invert'}`} 
            />
            <h1 className="text-4xl md:text-5xl font-black tracking-tighter">
              Price <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-cyan-400">Engine</span>
            </h1>
          </div>
          {!result && (
            <div className="animate-[fadeInUp_0.5s_ease-out]">
              <div className="inline-flex flex-col items-center justify-center mb-6 py-2 px-6 rounded-2xl bg-blue-500/10 border border-blue-500/20 backdrop-blur-sm">
                <span className={`text-xs font-bold uppercase tracking-widest ${themeClasses.textSubtle} mb-1`}>Database Aggiornato</span>
                <div className="flex items-baseline space-x-2">
                  <span className="text-3xl md:text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-300">
                    {totalBoatsDB > 0 ? <AnimatedCounter end={totalBoatsDB} duration={2500} /> : <span className="opacity-50">...</span>}
                  </span>
                  <span className={`text-sm font-semibold ${themeClasses.textMuted}`}>+ barche analizzate</span>
                </div>
              </div>
              <p className={`text-lg md:text-xl ${themeClasses.textMuted} max-w-xl mx-auto font-light leading-relaxed`}>
                L'intelligenza artificiale per il mercato nautico.<br className="hidden md:block"/> 
                Scopri il valore reale di qualsiasi barca istantaneamente.
              </p>
            </div>
          )}
        </div>

        {/* Barra di Ricerca */}
        <div className={`transition-all duration-700 z-40 flex flex-col items-center w-full ${result ? 'max-w-6xl' : 'max-w-3xl'} ${isSticky && result ? 'fixed top-0 left-0 right-0 !max-w-none px-4 sm:px-6 lg:px-8 py-3 bg-slate-900/95 backdrop-blur-2xl border-b border-slate-700/50 shadow-2xl' : 'relative'}`}>
           <div className={`w-full ${isSticky && result ? 'max-w-6xl mx-auto' : ''}`}>
             <form onSubmit={(e) => handleEvaluate(e)} className="relative flex flex-col md:flex-row items-center w-full gap-3">
                <div className="relative w-full" ref={searchContainerRef}>
                  <div className={`relative shadow-lg rounded-2xl md:rounded-full ${themeClasses.inputBg} border ${themeClasses.inputBorder} z-20`}>
                  <div className="absolute inset-y-0 left-0 pl-6 flex items-center pointer-events-none">
                    <Search className={`w-6 h-6 transition-colors duration-300 ${searchQuery ? 'text-blue-500' : themeClasses.textSubtle}`} />
                  </div>
                  <input 
                    type="text"
                    placeholder="Es: Axopar 37, Beneteau Oceanis 41..."
                    className={`w-full bg-transparent ${themeClasses.textMain} placeholder-${isDark ? 'slate-400' : 'slate-500'} rounded-2xl md:rounded-full py-4 pl-14 pr-4 md:pr-48 text-lg focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all`}
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
                        className={`px-6 py-3 cursor-pointer flex items-center ${themeClasses.hoverBg} transition-colors`}
                      >
                        <Search className={`w-4 h-4 mr-3 ${themeClasses.textSubtle}`} />
                        <span className="font-medium">{suggestion}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
              
              <div className="md:absolute md:inset-y-1.5 md:right-2 flex space-x-2 w-full md:w-auto z-20">
                <input 
                  type="number"
                  placeholder="Anno (Opz.)"
                  className={`w-1/3 md:w-28 ${themeClasses.inputBg} border ${themeClasses.inputBorder} ${themeClasses.textMain} rounded-xl md:rounded-full px-3 py-3 md:py-2.5 text-center focus:outline-none focus:ring-2 focus:ring-blue-400 transition-all`}
                  value={year}
                  onChange={(e) => setYear(e.target.value)}
                />
                <button 
                  type="submit"
                  disabled={loading || !searchQuery}
                  className="w-2/3 md:w-auto bg-blue-600 hover:bg-blue-500 text-white rounded-xl md:rounded-full px-6 py-3 md:py-2.5 font-bold shadow-md hover:shadow-lg transition-all duration-300 disabled:opacity-50 flex items-center justify-center min-w-[110px]"
                >
                  {loading ? <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div> : 'Valuta'}
                </button>
              </div>
           </form>
           </div>

           {/* Quick Links */}
           {!result && !loading && (
             <>
               <div className="mt-8 flex flex-wrap justify-center gap-3 animate-[fadeInUp_0.8s_ease-out]">
                 <button onClick={() => handleEvaluate(undefined, "Axopar 37")} className={`px-4 py-2 rounded-full text-sm font-medium border ${themeClasses.cardBorder} ${themeClasses.cardBg} hover:border-blue-500 hover:text-blue-500 transition-colors flex items-center shadow-sm`}>
                   <Zap className="w-4 h-4 mr-1.5 text-yellow-500" /> Analizza Axopar 37
                 </button>
                 <button onClick={() => handleEvaluate(undefined, "Beneteau Oceanis 41")} className={`px-4 py-2 rounded-full text-sm font-medium border ${themeClasses.cardBorder} ${themeClasses.cardBg} hover:border-blue-500 hover:text-blue-500 transition-colors flex items-center shadow-sm`}>
                   <Zap className="w-4 h-4 mr-1.5 text-blue-400" /> Beneteau Oceanis 41
                 </button>
                 <button onClick={() => handleEvaluate(undefined, "Pershing 62")} className={`px-4 py-2 rounded-full text-sm font-medium border ${themeClasses.cardBorder} ${themeClasses.cardBg} hover:border-blue-500 hover:text-blue-500 transition-colors flex items-center shadow-sm`}>
                   <Zap className="w-4 h-4 mr-1.5 text-purple-500" /> Pershing 62
                 </button>
               </div>

               {/* Portals & Scrolling Carousel */}
               <div className="mt-16 w-full max-w-5xl mx-auto animate-[fadeInUp_1s_ease-out]">
                 <p className={`text-center text-xs md:text-sm uppercase tracking-widest font-semibold mb-6 ${themeClasses.textSubtle}`}>
                   Dati in tempo reale aggregati da
                 </p>
                 <div className="flex flex-wrap justify-center items-center gap-8 md:gap-16 mb-10 opacity-70 hover:opacity-100 transition-opacity duration-500">
                   <span className="text-xl md:text-2xl font-black text-slate-400 tracking-tight">Boat24</span>
                   <span className="text-xl md:text-2xl font-black text-slate-400 tracking-tight">Yachtall</span>
                   <span className="text-xl md:text-2xl font-black text-slate-400 tracking-tight">Mondial Broker</span>
                   <span className="text-xl md:text-2xl font-black text-slate-400 tracking-tight">iNautia</span>
                 </div>
                 
                 <div className="relative w-full overflow-hidden h-32 md:h-40 rounded-2xl mask-image-gradient">
                   <div className="flex w-max animate-[scroll_40s_linear_infinite] space-x-4 hover:[animation-play-state:paused]">
                     {(carouselImages.length > 0 ? [...carouselImages, ...carouselImages] : []).map((src, i) => (
                       <img key={i} src={src} alt="boat" className={`h-full w-48 md:w-64 object-cover rounded-xl shadow-lg border ${themeClasses.cardBorder} hover:scale-105 transition-transform duration-500`} />
                     ))}
                   </div>
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
          <div id="report-container" ref={reportRef} className="w-full max-w-6xl mt-8 space-y-6 animate-[fadeInUp_0.5s_ease-out] relative print-area">
            
              {/* Box Intestazione & Market Share */}
            <div className={`grid grid-cols-1 md:grid-cols-3 gap-6`}>
              <div className={`md:col-span-2 flex flex-col justify-center ${themeClasses.cardBg} backdrop-blur-xl border ${themeClasses.cardBorder} p-6 md:p-8 rounded-3xl shadow-lg relative overflow-hidden`}>
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <p className={`${themeClasses.textSubtle} font-medium text-xs mb-1 uppercase tracking-widest`}>Analisi di Mercato B2B</p>
                    <h2 className="text-3xl md:text-4xl font-bold capitalize">{result.query}</h2>
                  </div>
                  <button 
                    onClick={generatePDF}
                    disabled={generatingPDF}
                    className={`flex items-center px-4 py-2 rounded-xl text-xs font-bold transition-all shadow-sm no-print ${isDark ? 'bg-slate-700 text-white hover:bg-slate-600' : 'bg-slate-100 text-slate-700 hover:bg-slate-200'}`}
                  >
                    {generatingPDF ? <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-current mr-2"></div> : <Download className="w-3.5 h-3.5 mr-2" />}
                    {generatingPDF ? 'Generando...' : 'Esporta PDF Report'}
                  </button>
                </div>
                
                <div className="flex flex-col sm:flex-row sm:items-center justify-between mt-2">
                <div className="flex flex-wrap gap-2">
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold ${isDark ? 'bg-blue-900/40 text-blue-400 border border-blue-500/20' : 'bg-blue-50 text-blue-700 border border-blue-100'}`}>
                    <Anchor className="w-3 h-3 mr-1.5" /> {result.identified_builder}
                  </span>
                  <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold border ${liquidityColors[result.valuation.liquidity_color]}`}>
                    <Droplets className="w-3 h-3 mr-1.5" /> Liquidità: {result.valuation.liquidity_status}
                  </span>
                  {result.valuation.sold_last_week !== undefined && (
                    <span className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-bold border ${isDark ? 'bg-indigo-900/40 text-indigo-400 border-indigo-500/20' : 'bg-indigo-50 text-indigo-700 border-indigo-100'}`}>
                      <TrendingUp className="w-3 h-3 mr-1.5" /> Vendite/Rimosse 7gg: {result.valuation.sold_last_week}
                    </span>
                  )}
                </div>
                  {/* Confidence Score Widget */}
                  <div className="mt-4 sm:mt-0 flex flex-col items-start sm:items-end">
                     <div className="flex items-center space-x-2">
                        <span className={`text-[10px] font-bold uppercase tracking-tighter ${themeClasses.textSubtle}`}>Affidabilità Dato:</span>
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
                      <p className="text-sm font-semibold mb-1 text-blue-500">Arbitraggio (Market Insight):</p>
                      <p className={`text-xs leading-relaxed ${themeClasses.textMuted}`}>
                        {(() => {
                          const countries = result.valuation.market_share_countries;
                          const cheaper = countries.reduce((prev: any, curr: any) => prev.avg_price < curr.avg_price ? prev : curr);
                          const expensive = countries.reduce((prev: any, curr: any) => prev.avg_price > curr.avg_price ? prev : curr);
                          const diff = ((expensive.avg_price - cheaper.avg_price) / cheaper.avg_price * 100).toFixed(0);
                          
                          if (parseFloat(diff) > 10) {
                            return `Opportunità di arbitraggio tra ${cheaper.name.toUpperCase()} e ${expensive.name.toUpperCase()}. Acquistare in ${cheaper.name} potrebbe far risparmiare circa il ${diff}% rispetto ai prezzi in ${expensive.name}.`;
                          } else {
                            return `Mercato europeo stabile e bilanciato tra i vari paesi analizzati (${countries.map((c:any) => c.name).join(', ')}).`;
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
                   <MapPin className="w-3.5 h-3.5 mr-1.5"/> Arbitraggio per Nazione
                </p>
                {result.valuation.market_share_countries?.length > 0 ? (
                  <div className="flex-1 w-full relative flex flex-col min-h-0">
                    <div className="flex-1 w-full rounded-xl overflow-hidden mb-3 shadow-inner border border-slate-500/20 bg-slate-200 min-h-0">
                       <EuropeMap countriesData={result.valuation.market_share_countries} isDark={isDark} />
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
                    <span className="text-sm text-slate-500">Dati geografici non disponibili</span>
                  </div>
                )}
              </div>
            </div>

            {/* Metriche Principali (Broker Dashboard) */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              
              <div className={`md:col-span-2 bg-gradient-to-br ${themeClasses.gradientCard} border ${isDark ? 'border-blue-500/30' : 'border-blue-200'} p-8 rounded-3xl shadow-lg relative overflow-hidden group`}>
                <div className="absolute -top-4 -right-4 opacity-10 group-hover:scale-110 transition-transform duration-500">
                  <TrendingUp className="w-40 h-40 text-blue-500" />
                </div>
                <p className={`${isDark ? 'text-blue-400' : 'text-blue-700'} font-bold text-xs flex items-center uppercase tracking-widest mb-2`}>
                  <Euro className="w-4 h-4 mr-2"/> Valore di Mercato Medio
                </p>
                <div className="text-5xl md:text-6xl font-black mb-3 relative z-10 tracking-tight">
                  {formatPrice(result.valuation.average_price_eur)}
                </div>
                <div className={`inline-flex items-center space-x-2 text-xs font-medium px-3 py-1.5 rounded-lg ${isDark ? 'bg-slate-900/50 text-slate-300' : 'bg-white/80 text-slate-600'}`}>
                   <span>Su <strong className={isDark ? 'text-white' : 'text-slate-900'}>{result.total_results_found}</strong> annunci totali</span>
                   <span className="text-slate-500">|</span>
                   <span>Min: <strong>{formatPrice(result.valuation.min_price_eur)}</strong></span>
                   <span className="text-slate-500">|</span>
                   <span>Max: <strong>{formatPrice(result.valuation.max_price_eur)}</strong></span>
                </div>
              </div>

              <div className={`${themeClasses.cardBg} border ${themeClasses.cardBorder} p-6 rounded-3xl shadow-lg flex flex-col justify-center`}>
                <p className={`${themeClasses.textSubtle} font-bold text-xs uppercase tracking-widest mb-2 flex items-center`}>
                  <TrendingDown className="w-4 h-4 mr-2 text-red-500"/> Perdita Valore Annua
                </p>
                {result.valuation.has_depreciation ? (
                  <>
                    <div className="text-4xl md:text-5xl font-black text-red-500 mb-1 tracking-tighter">
                      -{result.valuation.depreciation_percent}%
                    </div>
                    <div className={`text-sm font-medium ${themeClasses.textMuted}`}>
                      circa {formatPrice(result.valuation.depreciation_value_eur)} / anno
                    </div>
                  </>
                ) : (
                  <div className={`text-sm ${themeClasses.textSubtle}`}>Dati storici insufficienti</div>
                )}
              </div>

              <div className="grid grid-cols-1 gap-4">
                <div className={`${themeClasses.cardBg} border ${themeClasses.cardBorder} p-5 rounded-3xl shadow-sm flex flex-col justify-center`}>
                  <p className={`${themeClasses.textSubtle} font-medium text-xs uppercase tracking-widest mb-1 flex items-center`}><Calendar className="w-3.5 h-3.5 mr-1.5"/> Età Media Modello</p>
                  <div className="text-3xl font-bold">{result.valuation.median_age_years} <span className="text-sm text-slate-500 font-normal">anni</span></div>
                </div>
                <div className={`${themeClasses.cardBg} border ${themeClasses.cardBorder} p-5 rounded-3xl shadow-sm flex flex-col justify-center`}>
                  <p className={`${themeClasses.textSubtle} font-medium text-xs uppercase tracking-widest mb-1 flex items-center`}><Ruler className="w-3.5 h-3.5 mr-1.5"/> Prezzo al Metro</p>
                  <div className="text-2xl font-bold">{result.valuation.average_price_per_meter > 0 ? formatPrice(result.valuation.average_price_per_meter) : 'N/D'}</div>
                </div>
              </div>

            </div>

            {/* Grafico Trend e Lista Ottimizzata */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              <div className={`${themeClasses.cardBg} border ${themeClasses.cardBorder} p-6 md:p-8 rounded-3xl shadow-lg`}>
                <h3 className="text-base font-semibold mb-6 flex items-center tracking-wide">
                  <Activity className="w-5 h-5 mr-3 text-blue-500" /> Andamento Storico Prezzi (Trend)
                </h3>
                <div className="h-[350px] w-full">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={result.valuation.price_trend?.length > 0 ? result.valuation.price_trend : []} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke={isDark ? "rgba(255,255,255,0.05)" : "rgba(0,0,0,0.05)"} vertical={false} />
                      <XAxis dataKey="year" stroke={themeClasses.chartAxis} fontSize={12} tickLine={false} axisLine={false} dy={10} />
                      <YAxis tickFormatter={(val) => `€${val/1000}k`} stroke={themeClasses.chartAxis} fontSize={12} tickLine={false} axisLine={false} dx={-5} />
                      <Tooltip 
                        formatter={(value: number) => [formatPrice(value), "Prezzo Medio"]}
                        labelFormatter={(label) => `Costruzione: ${label}`}
                        contentStyle={{ backgroundColor: themeClasses.tooltipBg, border: `1px solid ${themeClasses.cardBorder}`, borderRadius: '12px', color: themeClasses.tooltipText, boxShadow: '0 4px 15px rgba(0,0,0,0.1)' }}
                        itemStyle={{ color: '#3b82f6', fontWeight: 'bold' }}
                      />
                      <Line 
                        type="monotone" 
                        dataKey="avg_price" 
                        stroke="#3b82f6" 
                        strokeWidth={4} 
                        dot={{ r: 5, fill: '#3b82f6', stroke: isDark ? '#1e293b' : '#fff', strokeWidth: 2 }} 
                        activeDot={{ r: 8, stroke: '#60a5fa', strokeWidth: 2 }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className={`${themeClasses.cardBg} border ${themeClasses.cardBorder} rounded-3xl shadow-lg flex flex-col h-[420px] md:h-[460px] overflow-hidden`}>
                <div className={`px-6 py-5 border-b ${themeClasses.cardBorder} flex justify-between items-center bg-black/5`}>
                  <h3 className="font-semibold flex items-center text-sm uppercase tracking-widest text-slate-400">
                    Campione (Top {result.comparables.length} recenti)
                  </h3>
                </div>
                
                <div className="overflow-y-auto flex-1 p-3 style-scrollbar">
                  <div className="space-y-2">
                    {result.comparables.map((boat: any, idx: number) => (
                      <a 
                        key={idx} 
                        href={boat.url} 
                        target="_blank" 
                        rel="noreferrer" 
                        className={`flex items-center p-3 rounded-xl border border-transparent ${themeClasses.hoverBg} transition-colors group cursor-pointer`}
                      >
                        {boat.image_url ? (
                          <img src={boat.image_url} loading="lazy" alt="boat" className={`w-16 h-12 object-cover rounded-lg shadow-sm border ${themeClasses.cardBorder} opacity-90 group-hover:opacity-100 transition-opacity`} />
                        ) : (
                          <div className={`w-16 h-12 ${isDark ? 'bg-slate-800' : 'bg-slate-200'} rounded-lg border ${themeClasses.cardBorder} flex items-center justify-center text-slate-500`}>
                            <Anchor className="w-4 h-4"/>
                          </div>
                        )}
                        <div className="ml-4 flex-1 min-w-0">
                          <div className={`font-semibold truncate text-sm ${themeClasses.textMain} ${boat.status === false ? 'opacity-50 line-through' : ''}`}>
                            {boat.builder} {boat.model}
                          </div>
                          <div className="flex items-center mt-1 space-x-3 text-xs">
                            <span className={`flex items-center ${themeClasses.textSubtle}`}><Calendar className="w-3 h-3 mr-1"/>{boat.year_built}</span>
                            {boat.length > 0 && <span className={`flex items-center ${themeClasses.textSubtle}`}><Ruler className="w-3 h-3 mr-1"/>{boat.length}m</span>}
                            {boat.country && <span className={`flex items-center ${themeClasses.textSubtle} truncate max-w-[80px]`}><MapPin className="w-3 h-3 mr-1"/>{boat.country}</span>}
                          </div>
                        </div>
                        <div className="ml-2 flex flex-col items-end whitespace-nowrap">
                          <div className={`font-bold text-sm ${boat.status === false ? 'text-slate-400 line-through' : 'text-blue-500'}`}>
                            {formatPrice(boat.price_eur)}
                          </div>
                          {boat.status === false ? (
                            <span className="text-[10px] font-semibold text-red-500 bg-red-500/10 px-1.5 py-0.5 rounded mt-1">VENDUTO</span>
                          ) : (
                            boat.updated_at && boat.first_seen_at && boat.updated_at.split(' ')[0] !== boat.first_seen_at.split(' ')[0] ? (
                              <span className="text-[10px] font-semibold text-amber-500 bg-amber-500/10 px-1.5 py-0.5 rounded mt-1">AGGIORNATO</span>
                            ) : null
                          )}
                        </div>
                      </a>
                    ))}
                  </div>
                </div>
              </div>

            </div>
          </div>
        )}
      </main>

      {/* Footer Istituzionale */}
      <footer className={`relative z-10 w-full py-6 mt-auto border-t ${isDark ? 'border-white/10 bg-slate-950/80 text-slate-400' : 'border-slate-200 bg-slate-100/80 text-slate-500'} backdrop-blur-md`}>
        <div className="max-w-6xl mx-auto px-4 flex flex-col md:flex-row items-center justify-between text-xs">
          <div className="flex items-center mb-2 md:mb-0">
            <img 
              src="https://batoo.it/icons/batoo-logo-dark.svg?dpl=dpl_9aCViBvDC47Q54fZ2iSr4nXE9S5q" 
              alt="Batoo Logo" 
              className={`h-4 mr-2 ${isDark && 'invert'}`} 
            />
            <span>Price Engine B2B</span>
          </div>
          <div className="text-center md:text-right">
            <p>Algoritmo proprietario alimentato da oltre <strong className={isDark ? 'text-white' : 'text-slate-700'}>{totalBoatsDB > 0 ? (Math.floor(totalBoatsDB/100)*100).toLocaleString('it-IT') + '+' : '...'}</strong> annunci reali in Europa.</p>
            <p className="mt-1 opacity-75">I dati forniti sono stime statistiche basate sull'analisi predittiva del mercato nautico.</p>
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

        @media print {
          body { 
            visibility: hidden; 
            background: white !important; 
            color: black !important; 
          }
          #report-container, #report-container * { 
            visibility: visible; 
          }
          #report-container { 
            position: absolute; 
            left: 0; 
            top: 0; 
            width: 100%; 
            margin: 0; 
            padding: 0; 
          }
          .no-print { display: none !important; }
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
