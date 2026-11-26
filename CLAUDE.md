# CLAUDE.md

Corpus local de legislație ISU: Legea 307/2006 (rădăcina repo-ului) și Normativul P 118/1-2025 (`p118/`). Vezi [README.md](README.md).

## Cum răspunzi la întrebări

- Caută întâi cu `python tools/cauta.py ...` (exemple în README), apoi citește articolul întreg din `articole/` sau `p118/articole/`, `p118/anexe/`.
- Citează mereu articolul exact (câmpul `citare` din `unitati.jsonl`), cu textul oficial.
- Rezumatele, cuvintele-cheie și indexurile tematice sunt generate de AI: folosește-le doar pentru navigare, nu ca sursă a unei valori sau obligații.
- Tabelele din P118 sunt în `p118/tabele.json` / `TABELE-SI-FIGURI.md`; figurile (`p118/figuri/`) sunt indexate doar după legendă.
