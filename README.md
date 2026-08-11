# Baśka — generator diagramów

Osobny projekt (niezależny od silnika w `kod/`). Generuje PNG ze stanami gry do przykładów w tłumaczeniach.

## Co widać na obrazku

- 4 gracze: południe / zachód / północ / wschód
- ręce **0–4** kart
- karty **odsłonięte** (`Ah`, `10c`…) albo **zasłonięte** (`?` / `face_up: false`)
- na środku **stos bitki 0–3** kart

Karty Baśki: `A`, `10`, `Q`, `J` × `h`♥ `d`♦ `c`♣ `s`♠.

## Uruchomienie (bez konsoli)

Najprościej kliknij dwukrotnie:

- **`BaskaDiagramy.exe`** — okno z listą JSON, edycją, generowaniem i podglądem  
- albo **`Uruchom.bat`** — to samo przez lokalne `uv` / `.venv`

PNG lądują w `output/`. Pliki stanów trzymaj w `examples/` (albo otwórz dowolny JSON w oknie).

## Uruchomienie z konsoli

```powershell
cd C:\Users\kajte\Desktop\baśka\diagramy
uv run python -m baska_diagramy
```

Albo konkretny plik:

```powershell
uv run python -m baska_diagramy examples\przyklad2_bitka.json -o output
```

Wyniki lądują w `output/`.

## Format JSON

```json
{
  "title": "Nagłówek",
  "subtitle": "Podpis",
  "output": "nazwa.png",
  "players": [
    {
      "name": "Ty",
      "position": "south",
      "face_up": true,
      "cards": ["Ah", "10h", "Qc", "Js"]
    },
    {
      "name": "Zachód",
      "position": "west",
      "face_up": false,
      "cards": 4
    },
    { "name": "Północ", "position": "north", "cards": ["?", "10s", "?"] },
    { "name": "Wschód", "position": "east", "cards": ["As"] }
  ],
  "trick": ["Ah", "10d", "Qs"]
}
```

Skróty:

| Zapis | Znaczenie |
|-------|-----------|
| `"cards": 3` + `"face_up": false` | 3 rewersy |
| `"?"` / `"back"` | jedna zasłonięta |
| `"Ah"`, `"10♣"` | odsłonięta |
| `"trick": []` | pusty środek |
| `"highlight": [0, 2]` | podświetl karty o tych indeksach (0 = pierwsza) |
| `{"card": "Ah", "highlight": true}` | to samo przy pojedynczej karcie |

Podświetlone karty dostają zieloną ramkę; pozostałe w tej samej ręce są przygaszone — wygodne do pokazywania legalnych zagrań.
