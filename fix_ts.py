import re

# App.tsx
with open('frontend/src/App.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# Fix unused BarChart2
content = re.sub(r'BarChart2,\s*', '', content)
# Fix unused setGeneratingPDF
content = re.sub(r'const \[generatingPDF, setGeneratingPDF\] = useState\(false\);', r'// const [generatingPDF, setGeneratingPDF] = useState(false);', content)
# Fix recharts tooltip formatter type
content = re.sub(r'formatter=\{\(value: number\) => \[formatPrice\(value\), "Prezzo Medio"\]\}', r'formatter={(value: any) => [formatPrice(Number(value)), "Prezzo Medio"]}', content)

with open('frontend/src/App.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

# EuropeMap.tsx
with open('frontend/src/EuropeMap.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

content = re.sub(r"import React, \{ useEffect, useState \} from 'react';", "import { useEffect, useState } from 'react';", content)
content = re.sub(r"center=\{mapCenter\}", r"center={mapCenter as any}", content)
content = re.sub(r"attribution='&copy; <a href=\"https://carto\.com/\">CARTO</a>'", r"attribution='&copy; <a href=\"https://carto.com/\">CARTO</a>' as any", content)
content = re.sub(r"radius=\{radius\}", r"radius={radius as any}", content)
content = re.sub(r'<Tooltip direction="top" offset=\{\[0, -10\]\} opacity=\{1\}>', r'<Tooltip direction="top" offset={[0, -10] as any} opacity={1} as any>', content)

with open('frontend/src/EuropeMap.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

