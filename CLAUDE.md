# CLAUDE.md

Corpus local de legislație de securitate la incendiu, pentru răspunsuri cu citare exactă:

| Act | Unde | Tag în căutare |
|---|---|---|
| Legea nr. 307/2006 (republicată), consolidată la 08.05.2026 | rădăcina repo-ului | `lege` / `[L307]` |
| Normativ P 118/1-2025 (Ordinul MDLPA 267/2025) | `p118/` | `p118` / `[P118]` |

Textele sunt cele de pe Portalul Legislativ (legislatie.just.ro), descărcate la 2026-11-26. Nu există alte acte în corpus: dacă o întrebare depinde de HG 571/2016, Ordinul 129/2016, P 118/2, P 118/3 etc., spune explicit că nu sunt aici.

## Fluxul de lucru pentru o întrebare

1. **Caută.** Pe Windows rulează cu `py`, altfel cu `python`:
   ```
   py tools/cauta.py lățime ușă evacuare             # toți termenii (AND), în ambele acte
   py tools/cauta.py --act p118 sarcina termica -n 40
   py tools/cauta.py --act lege aviz termen
   ```
   Căutarea nu ține cont de diacritice și majuscule. Termenii se caută ca subșiruri, deci folosește rădăcini scurte (`evacu`, `compartiment`, `spital`) și puțini termeni. Dacă nu ai rezultate, scoate termeni sau încearcă sinonime. Rezultatele marcate `fișă:` vin din titlul sau cuvintele-cheie generate. Celelalte vin din textul oficial al unui alineat, al unei litere sau al unui punct.
2. **Citește articolul întreg** înainte să răspunzi, nu doar fragmentul găsit:
   ```
   py tools/cauta.py --act lege --art 30^1
   py tools/cauta.py --act p118 --art 2.2.1.2
   ```
   Poți deschide și direct fișierul: `articole/art-030-1.md` (lege) sau `p118/articole/art-2.2.1.2.md`, `p118/anexe/anexa-N.md`.
3. **Verifică o citare** exactă: `py tools/cauta.py --cit "art. 30 alin. (6)"`.
4. **Tabele și figuri din P118**: `py tools/cauta.py --tabel 4` sau `--figura 3` îți arată articolul în care se află. Conținutul tabelului e în fișierul articolului și în `p118/tabele.json`. Imaginile sunt în `p118/figuri/` (deschide-le cu Read dacă figura contează).

## Puncte de intrare pentru navigare

- `INDEX.md`, `p118/INDEX.md`: cuprinsul, cu un titlu scurt și un rezumat pentru fiecare articol.
- `INDEX-TEMATIC.md`, `p118/INDEX-TEMATIC.md`: articolele grupate pe teme (aviz/autorizare, evacuare, compartimentare etc.).
- `index.json` → `intrebari_frecvente`: întrebări uzuale, cu citările relevante. E un bun punct de plecare pentru întrebări generale.
- `p118/TABELE-SI-FIGURI.md`: lista celor 174 de tabele și a figurilor, cu articolul în care apare fiecare.

## Reguli pentru răspuns

- **Citează exact** forma canonică din câmpul `citare` din `unitati.jsonl`, de exemplu `art. 30^1 alin. (1)` din Legea 307/2006 sau `art. 2.5.11.1 alin. (2)` din P 118/1-2025. Numește mereu actul. Literele art. 1 din lege se citează `art. 1 lit. b)`, fără alineat.
- **Valorile** (distanțe, lățimi, rezistențe la foc, praguri) se iau doar din textul oficial, din `articole/`, `p118/articole/`, `p118/anexe/` sau `unitati.jsonl`. Titlurile scurte, rezumatele, cuvintele-cheie, indexurile tematice și întrebările frecvente sunt generate de AI. Folosește-le doar pentru navigare, nu ca sursă.
- Când citezi conținutul, redă-l fidel (citat sau parafrază apropiată) și indică fișierul.
- Urmărește trimiterile interne (de ex. „conform art. 2.1.4”, „Tabelul 7”) și citește și acele articole când schimbă răspunsul.
- Pentru lege, frontmatter-ul (`modificat_prin`) și marcajul `*modificat` din rezultate arată textele modificate prin acte ulterioare. Corpusul poate fi depășit: pentru decizii reale, recomandă verificarea formei în vigoare pe legislatie.just.ro.

## Structura datelor (pentru scripturi)

- `unitati.jsonl` / `p118/unitati.jsonl`: o linie JSON per articol, alineat, literă sau punct. Câmpuri: `citare`, `tip`, `text`, `fisier`. Valorile pentru `tip` diferă între acte: în lege sunt `articol`, `alineat`, `litera`, `punct`, iar în P118 sunt `articol`, `alin`, `lit`, `pct`, `anexa`. Legea are și `capitol`, `sectiune`, `modificat`, iar P118 are `structura`.
- `index.json` / `p118/index.json`: `articole` (fișe: `titlu_scurt`, `rezumat`, `cuvinte_cheie`), `teme`, `intrebari_frecvente`, iar pentru P118 și `tabele`, `figuri`.
- `sursa/`, `p118/sursa/`: HTML-ul original și rezultatul brut al indexării. Nu le edita.
- `tools/parse_portal.py`, `tools/parse_normativ.py`, `tools/build_*.py`: regenerează corpusul din HTML. Fișierele din `articole/` sunt generate de ele, deci nu le edita de mână.
- `artefacte/`: pagini HTML derivate (de ex. calculatorul de lungimi de evacuare pentru spitale).
