import re

with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Add lang state
content = re.sub(
    r'(const \[isDark, setIsDark\] = useState\(false\);)',
    r'\1\n  const [lang, setLang] = useState<"it" | "en">("it");\n  const toggleLang = () => setLang(l => l === "it" ? "en" : "it");',
    content
)

# Pass lang to API
content = re.sub(
    r'(let url = `\$\{API_BASE_URL\}/evaluate\?q=\$\{encodeURIComponent\(queryToUse\)\}`;)',
    r'\1\n      url += `&lang=${lang}`;',
    content
)

# Add Toggle button next to dark mode toggle
toggle_btn = r'''
          <button 
            onClick={toggleLang} 
            className={`p-2 rounded-full transition-colors flex items-center justify-center font-bold text-sm ${isDark ? 'bg-slate-800 text-slate-300 hover:bg-slate-700' : 'bg-white text-slate-600 hover:bg-slate-100 shadow-sm'}`}
            title={lang === "it" ? "Passa a Inglese" : "Switch to Italian"}
          >
            {lang.toUpperCase()}
          </button>
'''
content = re.sub(
    r'(<button\s+onClick=\{toggleTheme\}\s+className=\{`[^`]+`\}\s+title="Cambia tema"\s*>\s*(?:\{isDark \? <Sun className="w-5 h-5"/> : <Moon className="w-5 h-5"/>\})\s*</button>)',
    toggle_btn.strip() + r'\n          \1',
    content
)

with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
