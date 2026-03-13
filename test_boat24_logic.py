import re

test_locations = [
    "Manfredonia(FG)-Porto turistico Marina del Gargano",
    "Germania»Waren Müritz",
    "Croazia»Novi Vinodolski",
    "Sardegna»Lomar Marine International srl Olbia (SS)",
    "Spagna»Baleares»Ibiza",
    "Mar Tirreno",
    "Lago di Garda»Moniga del Garda",
    "Francia",
    "Marseille (F)",
    "Bodensee (D)"
]

known_countries = {
    'germania', 'francia', 'spagna', 'croazia', 'grecia', 'olanda',
    'svizzera', 'austria', 'turchia', 'belgio', 'danimarca', 
    'svezia', 'norvegia', 'regno unito', 'gran bretagna', 'portogallo', 
    'polonia', 'malta', 'cipro', 'monaco', 'montenegro', 'slovenia'
}

country_map = {
    'D': 'germania', 'F': 'francia', 'E': 'spagna', 'HR': 'croazia', 
    'CH': 'svizzera', 'GR': 'grecia', 'NL': 'olanda', 'TR': 'turchia', 
    'AT': 'austria', 'BE': 'belgio', 'DK': 'danimarca', 'SE': 'svezia', 
    'NO': 'norvegia', 'UK': 'regno-unito', 'GB': 'regno-unito',
    'PT': 'portogallo', 'PL': 'polonia', 'SI': 'slovenia', 'MT': 'malta', 
    'CY': 'cipro', 'MC': 'monaco', 'ME': 'montenegro'
}

for location in test_locations:
    country = "italia"
    loc_lower = location.lower()
    
    first_part = loc_lower.split('»')[0].strip()
    if first_part in known_countries:
        country = first_part
    else:
        for kc in known_countries:
            if kc in loc_lower:
                if loc_lower.startswith(kc):
                    country = kc
                    break
                
    code_match = re.search(r'\( ([A-Z]{1,3}) \)', location) or re.search(r'\(([A-Z]{1,3})\)', location)
    if code_match and country == "italia":
        code = code_match.group(1).upper()
        if code in country_map:
            country = country_map[code]
            
    print(f"{location:<55} -> {country}")
