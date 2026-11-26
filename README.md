# Legislație ISU / securitate la incendiu – index local

Texte oficiale de pe Portalul Legislativ (legislatie.just.ro), descărcate la 2026-11-26 și indexate pentru căutare și citare rapidă.

| Act | Formă | Index | Text integral |
|---|---|---|---|
| Legea nr. 307/2006 privind apărarea împotriva incendiilor (republicată) | consolidată la 08.05.2026 (OUG 17/2026, OUG 38/2026) | [INDEX.md](INDEX.md) · [INDEX-TEMATIC.md](INDEX-TEMATIC.md) | [legea-307-2006.md](legea-307-2006.md) |
| Normativ P 118/1-2025 (Ordinul MDLPA 267/2025, M.Of. 204 bis/10.03.2025) | forma publicată, fără modificări afișate pe portal | [p118/INDEX.md](p118/INDEX.md) · [p118/INDEX-TEMATIC.md](p118/INDEX-TEMATIC.md) · [p118/TABELE-SI-FIGURI.md](p118/TABELE-SI-FIGURI.md) | [p118/p118-1-2025.md](p118/p118-1-2025.md) |

## Structură (aceeași pentru fiecare act)

- `articole/` (și `anexe/` la P118) – un fișier markdown pe articol/anexă, cu frontmatter (citare, structură, tabele, figuri).
- `unitati.jsonl` – o linie JSON per articol/alineat/literă/punct, cu citarea canonică în câmpul `citare`.
- `index.json` – fișele (titlu, rezumat, cuvinte-cheie, valori), temele și întrebările frecvente.
- `p118/figuri/` – cele 417 figuri ale normativului; `sursa/` – HTML-ul original și rezultatul brut al indexării.

## Căutare

```
python tools/cauta.py aviz termen                      # în ambele acte
python tools/cauta.py --act p118 lățime ușă evacuare   # doar P118
python tools/cauta.py --act lege --art 30^1            # articol întreg din lege
python tools/cauta.py --act p118 --art 2.2.1.2         # articol întreg din P118
python tools/cauta.py --cit "art. 30 alin. (6)"        # citare exactă
python tools/cauta.py --tabel 4                        # unde este Tabelul 4 din P118
```

## Ce e text oficial și ce e generat

- Textul din `articole/`, `anexe/`, `unitati.jsonl` și fișierele integrale este extras mecanic din HTML-ul oficial (script: `tools/parse_portal.py`, `tools/parse_normativ.py`), fără reformulare.
- Titlurile scurte, rezumatele, cuvintele-cheie, indexul tematic și întrebările frecvente sunt generate de agenți AI și verificate de un al doilea agent; sunt un ajutor de navigare, nu text normativ. Pentru orice valoare, verifică articolul citat.
- Figurile nu au fost analizate; sunt indexate doar după legendă.
