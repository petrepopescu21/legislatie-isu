"""Asambleaza rezultatul workflow-ului P118 in p118/index.json, INDEX.md, INDEX-TEMATIC.md, TABELE-SI-FIGURI.md.
Aplica automat corectiile verificatorilor si valideaza fiecare citare fata de unitati.jsonl.
Utilizare: python -I tools/build_p118.py <rezultat_workflow.json>
"""
import sys, json, os, re, io

ROOT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "p118")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
res = json.load(open(sys.argv[1], encoding="utf-8"))
J = lambda n: json.load(open(os.path.join(ROOT, n), encoding="utf-8"))
cuprins, tabele, figuri = J("cuprins.json"), J("tabele.json"), J("figuri.json")
units = [json.loads(l) for l in open(os.path.join(ROOT, "unitati.jsonl"), encoding="utf-8")]
nz = lambda c: re.sub(r"\s+", "", c or "").rstrip(".")
known = {}
for u in units:
    known.setdefault(nz(u["citare"]), u)
META = {"act": "Normativ privind securitatea la incendiu a construcțiilor, indicativ P 118/1-2025",
        "aprobat_prin": "Ordinul MDLPA nr. 267/2025 (M.Of. nr. 204 și 204 bis din 10 martie 2025)",
        "forma": "forma publicată; Portalul Legislativ nu afișa nicio modificare la data descărcării",
        "sursa": "https://legislatie.just.ro/Public/DetaliiDocument/295705", "descarcat_la": "2026-11-26"}

# ---------- fise
by_file = {}
for f in res["fise"]:
    by_file[f["fisier"].replace("\\", "/").split("p118/")[-1]] = f
arts, lipsa, repere_bad = [], [], 0
for c in cuprins:
    f = by_file.get(c["fisier"])
    if not f:
        lipsa.append(c["fisier"]); f = {}
    rep = []
    for r in f.get("repere") or []:
        ok = nz(r.get("citare")) in known
        repere_bad += (not ok)
        rep.append({"citare": r.get("citare"), "titlu": r.get("titlu"), "cuvinte_cheie": r.get("cuvinte_cheie") or [],
                    "valid": ok})
    arts.append({"tip": c["tip"], "citare": c["citare"], "fisier": c["fisier"], "structura": c["structura"],
                 "tabele": c["tabele"], "figuri": c["figuri"],
                 "titlu_scurt": f.get("titlu_scurt") or c.get("titlu") or "", "rezumat": f.get("rezumat") or "",
                 "cuvinte_cheie": f.get("cuvinte_cheie") or [], "tip_constructii": f.get("tip_constructii") or [],
                 "valori_cheie": f.get("valori_cheie") or [], "trimiteri": f.get("trimiteri") or [], "repere": rep})

# ---------- tematic + corectii
teme, faq, stats = [], [], {"verificate": 0, "probleme": 0, "aplicate": 0, "neaplicate": []}
for g in res["tematic"]:
    tem, ver = g["tematic"], g.get("verificare") or {"probleme": [], "intrari_verificate": 0}
    stats["verificate"] += ver.get("intrari_verificate", 0)
    for p in ver["probleme"]:
        stats["probleme"] += 1
        done = False
        if p["tip"] == "tema":
            for t in tem["teme"]:
                if clean_eq := (t["tema"].strip() == p["titlu"].strip()):
                    for i in list(t["intrari"]):
                        if nz(i["citare"]) == nz(p["citare"]):
                            if p["actiune"] == "elimina":
                                t["intrari"].remove(i)
                            elif p["actiune"] == "inlocuieste_citare":
                                i["citare"] = p["valoare_noua"]
                            else:
                                i["ce_spune"] = p["valoare_noua"]
                            done = True
                            break
        else:
            for q in list(tem["intrebari_frecvente"]):
                if q["intrebare"].strip() == p["titlu"].strip():
                    if p["actiune"] == "elimina" and not p["citare"]:
                        tem["intrebari_frecvente"].remove(q)
                    elif p["actiune"] == "elimina":
                        q["citari"] = [c for c in q["citari"] if nz(c) != nz(p["citare"])]
                    elif p["actiune"] == "inlocuieste_citare":
                        q["citari"] = [p["valoare_noua"] if nz(c) == nz(p["citare"]) else c for c in q["citari"]]
                        if not any(nz(c) == nz(p["valoare_noua"]) for c in q["citari"]):
                            q["citari"].append(p["valoare_noua"])
                    else:
                        q["raspuns"] = p["valoare_noua"]
                    done = True
        if done:
            stats["aplicate"] += 1
        else:
            stats["neaplicate"].append(p)
    for t in tem["teme"]:
        t["grupa"] = g["grupa"]
    teme += tem["teme"]; faq += tem["intrebari_frecvente"]

bad = []
for t in teme:
    for i in list(t["intrari"]):
        if nz(i["citare"]) not in known:
            bad.append((t["tema"], i["citare"])); t["intrari"].remove(i)
for q in faq:
    for c in list(q["citari"]):
        if nz(c) not in known:
            bad.append((q["intrebare"], c)); q["citari"].remove(c)


def link(c):
    u = known.get(nz(c))
    return "[%s](%s)" % (c, u["fisier"]) if u else c


json.dump({"meta": META, "articole": arts, "teme": teme, "intrebari_frecvente": faq, "tabele": tabele, "figuri": figuri},
          open(os.path.join(ROOT, "index.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)

# ---------- INDEX.md
L = ["# Index – " + META["act"], "",
     "- **Aprobat prin:** " + META["aprobat_prin"] + " — " + META["forma"],
     "- **Sursa:** %s (descărcat la %s; original în `sursa/`)" % (META["sursa"], META["descarcat_la"]),
     "- **Text integral:** [p118-1-2025.md](p118-1-2025.md) · **Index tematic:** [INDEX-TEMATIC.md](INDEX-TEMATIC.md) · **Tabele și figuri:** [TABELE-SI-FIGURI.md](TABELE-SI-FIGURI.md)",
     "- **Căutare:** `python tools/cauta.py --act p118 lățime ușă evacuare` · `--art 2.2.1.2` · `--tabel 4` · `--cit \"art. 2.2.1.2 alin. (3)\"`",
     ""]
last = []
for a in arts:
    cr = a["structura"] if a["tip"] == "art" else ["Anexe"]
    for i, h in enumerate(cr):
        if i >= len(last) or last[i] != h:
            L += ["", "#" * min(i + 2, 5) + " " + h, ""]
            last = cr[:i + 1]
    last = cr
    extra = "".join(" · " + x for x in a["tabele"][:6])
    L.append("- **[%s](%s)** — **%s.** %s%s" % (a["citare"], a["fisier"], a["titlu_scurt"].rstrip("."), a["rezumat"], extra))
    if a["cuvinte_cheie"]:
        L.append("  - *cuvinte-cheie:* " + ", ".join(a["cuvinte_cheie"]))
    if a["valori_cheie"]:
        L.append("  - *valori:* " + "; ".join(a["valori_cheie"]))
    for r in a["repere"]:
        L.append("  - %s — %s" % (link(r["citare"]) if r["valid"] else r["citare"], r["titlu"]))
open(os.path.join(ROOT, "INDEX.md"), "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")

# ---------- INDEX-TEMATIC.md
T = ["# Index tematic – " + META["act"], "", "Fiecare citare trimite la fișierul articolului/anexei. Verifică întotdeauna textul integral înainte de a te baza pe o valoare.", ""]
T += ["- [%s](#%s)" % (t["tema"], re.sub(r"[^\w\- ]", "", t["tema"].lower()).replace(" ", "-")) for t in teme] + [""]
for t in teme:
    T += ["## " + t["tema"], "", t["descriere"], ""]
    T += ["- %s — %s" % (link(i["citare"]), i["ce_spune"]) for i in t["intrari"]]
    T.append("")
T += ["## Întrebări frecvente", ""]
for q in faq:
    T += ["**%s**  " % q["intrebare"], q["raspuns"] + "  ", "*Temei:* " + ", ".join(link(c) for c in q["citari"]), ""]
open(os.path.join(ROOT, "INDEX-TEMATIC.md"), "w", encoding="utf-8", newline="\n").write("\n".join(T) + "\n")

# ---------- TABELE-SI-FIGURI.md
R = ["# Tabele și figuri – P 118/1-2025", "", "## Tabele", ""]
R += ["- **%s** — %s — [%s](%s)" % (t["tabel"], t["titlu"], t["citare"], t["fisier"]) for t in tabele]
R += ["", "## Figuri", ""]
R += ["- **%s** — %s — [%s](%s)" % (t["figura"], t["titlu"], t["citare"], t["fisier"]) for t in figuri]
open(os.path.join(ROOT, "TABELE-SI-FIGURI.md"), "w", encoding="utf-8", newline="\n").write("\n".join(R) + "\n")

print("fisiere:", len(arts), "| fara fisa:", len(lipsa), lipsa[:10])
print("repere:", sum(len(a["repere"]) for a in arts), "| repere cu citare negasita:", repere_bad)
print("teme:", len(teme), "| intrari:", sum(len(t["intrari"]) for t in teme), "| FAQ:", len(faq))
print("verificator: verificate", stats["verificate"], "| probleme", stats["probleme"], "| aplicate", stats["aplicate"])
for p in stats["neaplicate"]:
    print("  NEAPLICAT:", json.dumps(p, ensure_ascii=False)[:400])
print("citari invalide eliminate:", len(bad))
for b in bad:
    print("  ", b)
