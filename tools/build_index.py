"""Asambleaza rezultatul workflow-ului de indexare in index.json, INDEX.md, INDEX-TEMATIC.md.
Utilizare: python -I tools/build_index.py <rezultat_workflow.json>
Valideaza fiecare citare din indexul tematic fata de unitati.jsonl.
"""
import sys, json, os, re, io

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
res = json.load(open(sys.argv[1], encoding="utf-8"))
cuprins = json.load(open(os.path.join(ROOT, "cuprins.json"), encoding="utf-8"))
units = [json.loads(l) for l in open(os.path.join(ROOT, "unitati.jsonl"), encoding="utf-8")]
known = {re.sub(r"\s+", "", u["citare"]): u for u in units}
META = {"act": "Legea nr. 307/2006 privind apărarea împotriva incendiilor, republicată",
        "forma_consolidata": "2026-05-08",
        "ultima_modificare": "OUG nr. 38/2026 (M.Of. nr. 393 din 8 mai 2026); anterior OUG nr. 17/2026 (M.Of. nr. 199 din 13 martie 2026)",
        "sursa": "https://legislatie.just.ro/Public/DetaliiDocument/309352",
        "descarcat_la": "2026-11-26"}

by_file = {f["fisier"].split("/")[-1]: f for f in res["fise"]}
arts, lipsa = [], []
for c in cuprins:
    f = by_file.get(c["fisier"].split("/")[-1])
    if not f:
        lipsa.append(c["fisier"]); f = {}
    arts.append({"articol": c["id"], "citare": "art. " + c["id"], "fisier": c["fisier"], "capitol": c["capitol"],
                 "sectiune": c["sectiune"], "modificat_prin": c["modificat_prin"],
                 **{k: f.get(k) for k in ("titlu_scurt", "rezumat", "cuvinte_cheie", "destinatari",
                                          "relevanta_arhitectura", "de_ce_relevant", "trimiteri_interne",
                                          "acte_externe", "termene_si_valori", "modificat_2026")}})


def check(c):
    return re.sub(r"\s+", "", c) in known


def link(c):
    u = known.get(re.sub(r"\s+", "", c))
    return "[%s](%s)" % (c, u["fisier"]) if u else c + " ⚠"


tem = res.get("tematic") or {"teme": [], "intrebari_frecvente": []}
bad = []
for t in tem["teme"]:
    for i in t["intrari"]:
        if not check(i["citare"]):
            bad.append((t["tema"], i["citare"]))
for q in tem["intrebari_frecvente"]:
    for c in q["citari"]:
        if not check(c):
            bad.append((q["intrebare"], c))

json.dump({"meta": META, "articole": arts, "teme": tem["teme"], "intrebari_frecvente": tem["intrebari_frecvente"]},
          open(os.path.join(ROOT, "index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

L = ["# Index – " + META["act"], "",
     "- **Forma consolidată:** %s — %s" % (META["forma_consolidata"], META["ultima_modificare"]),
     "- **Sursa:** %s (descărcat la %s; original în `sursa/`)" % (META["sursa"], META["descarcat_la"]),
     "- **Text integral:** [legea-307-2006.md](legea-307-2006.md) · **Index tematic:** [INDEX-TEMATIC.md](INDEX-TEMATIC.md)",
     "- **Căutare:** `python tools/cauta.py aviz termen` · `--art 30^1` · `--cit \"art. 30 alin. (6)\"`; sau grep în `unitati.jsonl` (o linie JSON per articol/alineat/literă/punct)",
     "- Relevanță pentru arhitectură: ●●● ridicată · ●● medie · ● scăzută. `★` = modificat/completat în 2026.", ""]
cap = sec = None
REL = {"ridicata": "●●●", "medie": "●●", "scazuta": "●", None: ""}
for a in arts:
    if a["capitol"] != cap:
        cap, sec = a["capitol"], None
        L += ["", "## " + cap, ""]
    if a["sectiune"] and a["sectiune"] != sec:
        sec = a["sectiune"]
        L += ["", "### " + sec, ""]
    L.append("- **[art. %s](%s)** %s%s — **%s.** %s" % (
        a["articol"], a["fisier"], REL[a["relevanta_arhitectura"]], " ★" if a["modificat_2026"] else "",
        (a["titlu_scurt"] or "").rstrip("."), a["rezumat"] or ""))
    if a["cuvinte_cheie"]:
        L.append("  - *cuvinte-cheie:* " + ", ".join(a["cuvinte_cheie"]))
    if a["termene_si_valori"]:
        L.append("  - *termene/valori:* " + "; ".join(a["termene_si_valori"]))
open(os.path.join(ROOT, "INDEX.md"), "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")

T = ["# Index tematic – " + META["act"], "", "Forma consolidată la %s. Fiecare citare trimite la fișierul articolului." % META["forma_consolidata"], ""]
for t in tem["teme"]:
    T += ["## " + t["tema"], "", t["descriere"], ""]
    T += ["- %s — %s" % (link(i["citare"]), i["ce_spune"]) for i in t["intrari"]]
    T.append("")
T += ["## Întrebări frecvente", ""]
for q in tem["intrebari_frecvente"]:
    T += ["**%s**  " % q["intrebare"], q["raspuns"] + "  ", "*Temei:* " + ", ".join(link(c) for c in q["citari"]), ""]
open(os.path.join(ROOT, "INDEX-TEMATIC.md"), "w", encoding="utf-8", newline="\n").write("\n".join(T) + "\n")

print("articole:", len(arts), "| fara fisa:", lipsa)
print("teme:", len(tem["teme"]), "| intrari:", sum(len(t["intrari"]) for t in tem["teme"]), "| FAQ:", len(tem["intrebari_frecvente"]))
print("citari invalide:", len(bad))
for b in bad:
    print("  ", b)
