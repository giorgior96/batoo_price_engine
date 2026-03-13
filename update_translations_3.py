import re

with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

def repl(pattern, replacement):
    global content
    content = re.sub(pattern, replacement, content)

# Error messages
repl(r"setError\('Errore durante la valutazione\.'\);", r'setError(lang === "it" ? "Errore durante la valutazione." : "Error during evaluation.");')

# Some UI texts
repl(r'>Mercato Stabile<', r'>{lang === "it" ? "Mercato Stabile" : "Stable Market"}<')
repl(r'>In ribasso<', r'>{lang === "it" ? "In ribasso" : "Downtrend"}<')
repl(r'>In rialzo<', r'>{lang === "it" ? "In rialzo" : "Uptrend"}<')

repl(r'>Vendute di recente<', r'>{lang === "it" ? "Vendute di recente" : "Recently Sold"}<')
repl(r'>Annunci Attivi<', r'>{lang === "it" ? "Annunci Attivi" : "Active Listings"}<')

with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(content)
