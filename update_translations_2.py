import re

with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

def repl(pattern, replacement):
    global content
    content = re.sub(pattern, replacement, content)

# Header texts
repl(r'>Analisi matematica in tempo reale<', r'>{lang === "it" ? "Analisi matematica in tempo reale" : "Real-time mathematical analysis"}<')
repl(r'placeholder="Cerca Cantiere e Modello\.\.\."', r'placeholder={lang === "it" ? "Cerca Cantiere e Modello..." : "Search Builder and Model..."}')
repl(r'placeholder="Anno \(opz\.\)"', r'placeholder={lang === "it" ? "Anno (opz.)" : "Year (opt.)"}')
repl(r'>Genera Analisi<', r'>{lang === "it" ? "Genera Analisi" : "Generate Analysis"}<')
repl(r'>Analisi di Mercato<', r'>{lang === "it" ? "Analisi di Mercato" : "Market Analysis"}<')
repl(r'>Valore Medio<', r'>{lang === "it" ? "Valore Medio" : "Average Value"}<')
repl(r'>Svalutazione Annua<', r'>{lang === "it" ? "Svalutazione Annua" : "Annual Depreciation"}<')
repl(r'>Liquidità<', r'>{lang === "it" ? "Liquidità" : "Liquidity"}<')
repl(r'>Prezzo/Metro<', r'>{lang === "it" ? "Prezzo/Metro" : "Price/Meter"}<')
repl(r'text-xs mt-1 \$\{themeClasses\.textSubtle\}">Stima prezzo richiesto', r'text-xs mt-1 ${themeClasses.textSubtle}">{lang === "it" ? "Stima prezzo richiesto" : "Estimated asking price"}')

# Trend
repl(r'>Andamento Storico<', r'>{lang === "it" ? "Andamento Storico" : "Historical Trend"}<')

# Geografica
repl(r'>Distribuzione Geografica<', r'>{lang === "it" ? "Distribuzione Geografica" : "Geographical Distribution"}<')

# Campione
repl(r'Campione \(Top \{result\.comparables\.length\} recenti\)', r'{lang === "it" ? `Campione (Top ${result.comparables.length} recenti)` : `Sample (Top ${result.comparables.length} recent)`}')
repl(r'>VENDUTO<', r'>{lang === "it" ? "VENDUTO" : "SOLD"}<')
repl(r'>AGGIORNATO<', r'>{lang === "it" ? "AGGIORNATO" : "UPDATED"}<')

# PDF Elements
repl(r'>Stampa PDF<', r'>{lang === "it" ? "Stampa PDF" : "Print PDF"}<')
repl(r'>Report Generato<', r'>{lang === "it" ? "Report Generato" : "Generated Report"}<')
repl(r'>Dati di Mercato<', r'>{lang === "it" ? "Dati di Mercato" : "Market Data"}<')
repl(r'>Prezzo Medio Richiesto<', r'>{lang === "it" ? "Prezzo Medio Richiesto" : "Average Asking Price"}<')
repl(r'>Range Prezzi<', r'>{lang === "it" ? "Range Prezzi" : "Price Range"}<')
repl(r'>Svalutazione Stimata<', r'>{lang === "it" ? "Svalutazione Stimata" : "Estimated Depreciation"}<')
repl(r'>Prezzo al Metro<', r'>{lang === "it" ? "Prezzo al Metro" : "Price per Meter"}<')
repl(r'>Dettagli Mercato<', r'>{lang === "it" ? "Dettagli Mercato" : "Market Details"}<')
repl(r'>Volume Analizzato<', r'>{lang === "it" ? "Volume Analizzato" : "Analyzed Volume"}<')
repl(r'Annunci Totali<', r'{lang === "it" ? "Annunci Totali" : "Total Listings"}<')
repl(r'>Affidabilità Dato<', r'>{lang === "it" ? "Affidabilità Dato" : "Data Reliability"}<')
repl(r'>Età Media Imbarcazioni<', r'>{lang === "it" ? "Età Media Imbarcazioni" : "Average Boat Age"}<')
repl(r'>Anni<', r'>{lang === "it" ? "Anni" : "Years"}<')
repl(r'>Distribuzione per Nazione \(Top 3\)<', r'>{lang === "it" ? "Distribuzione per Nazione (Top 3)" : "Distribution by Country (Top 3)"}<')
repl(r'>Analisi AI<', r'>{lang === "it" ? "Analisi AI" : "AI Analysis"}<')
repl(r'>Top 5 Annunci Recenti Rilevati<', r'>{lang === "it" ? "Top 5 Annunci Recenti Rilevati" : "Top 5 Recent Listings Detected"}<')
repl(r"Anno: \{boat\.year_built\} &bull; Luogo: \{boat\.country \|\| 'N/D'\} \{boat\.status === false \? '\(Venduto/Rimosso\)' : ''\}", r'{lang === "it" ? "Anno" : "Year"}: {boat.year_built} &bull; {lang === "it" ? "Luogo" : "Location"}: {boat.country || "N/D"} {boat.status === false ? (lang === "it" ? "(Venduto/Rimosso)" : "(Sold/Removed)") : ""}')
repl(r'Generato tramite Batoo Price Engine B2B\. I dati riportati sono frutto di analisi statistica\.', r'{lang === "it" ? "Generato tramite Batoo Price Engine B2B. I dati riportati sono frutto di analisi statistica." : "Generated via Batoo Price Engine B2B. The data reported are the result of statistical analysis."}')
repl(r'>Lista Completa Imbarcazioni Rilevate<', r'>{lang === "it" ? "Lista Completa Imbarcazioni Rilevate" : "Complete List of Detected Listings"}<')
repl(r'\{result\.comparables\.length\} Annunci', r'{result.comparables.length} {lang === "it" ? "Annunci" : "Listings"}')
repl(r'Clicca qui per visionare', r'{lang === "it" ? "Clicca qui per visionare" : "Click here to view"}')
repl(r'Documento Integrativo \- Batoo Price Engine B2B\. I link originali sono esterni al sistema\.', r'{lang === "it" ? "Documento Integrativo - Batoo Price Engine B2B. I link originali sono esterni al sistema." : "Supplementary Document - Batoo Price Engine B2B. Original links are external to the system."}')

with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
