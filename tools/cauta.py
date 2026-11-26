"""Cautare rapida in actele indexate (fara diacritice, case-insensitive).
  python tools/cauta.py aviz termen                    # toti termenii (AND) in aceeasi unitate, in toate actele
  python tools/cauta.py --act p118 latime usa evacuare # doar in normativul P 118/1-2025
  python tools/cauta.py --act lege --art 30^1          # un articol intreg din Legea 307/2006
  python tools/cauta.py --act p118 --art 2.2.1.2       # un articol din P118
  python tools/cauta.py --cit "art. 30 alin. (6)"      # o citare exacta
  python tools/cauta.py --tabel 4                      # unde se afla Tabelul 4 din P118
Acte: lege = Legea 307/2006 (radacina), p118 = P 118/1-2025 (p118/).
Cauta in unitati.jsonl (articole/alineate/litere/puncte) si in index.json (titluri + cuvinte-cheie).
"""
import sys, json, os, io, re, unicodedata, argparse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ACTE = {"lege": ("", "L307"), "p118": ("p118", "P118")}
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")


def norm(s):
    s = unicodedata.normalize("NFD", (s or "").lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def load(act):
    sub, tag = ACTE[act]
    base = os.path.join(ROOT, sub)
    p = os.path.join(base, "unitati.jsonl")
    if not os.path.exists(p):
        return [], {}, base, tag
    units = [json.loads(l) for l in open(p, encoding="utf-8")]
    fise = {}
    pi = os.path.join(base, "index.json")
    if os.path.exists(pi):
        for x in json.load(open(pi, encoding="utf-8"))["articole"]:
            fise[x["fisier"]] = x
    return units, fise, base, tag


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("termeni", nargs="*")
    ap.add_argument("--act", choices=list(ACTE) + ["toate"], default="toate")
    ap.add_argument("--art")
    ap.add_argument("--cit")
    ap.add_argument("--tabel")
    ap.add_argument("--figura")
    ap.add_argument("-n", type=int, default=20)
    a = ap.parse_args()
    acte = list(ACTE) if a.act == "toate" else [a.act]

    if a.tabel or a.figura:
        idx = json.load(open(os.path.join(ROOT, "p118", "index.json"), encoding="utf-8"))
        key, lst, nr = ("tabel", idx["tabele"], a.tabel) if a.tabel else ("figura", idx["figuri"], a.figura)
        for t in lst:
            if re.search(r"\b%s$" % re.escape(nr), t[key]):
                print("%s — %s\n   %s  (p118/%s)" % (t[key], t["titlu"], t["citare"], t["fisier"]))
        return

    hits = []
    for act in acte:
        units, fise, base, tag = load(act)
        sub = ACTE[act][0]
        rel = lambda f: (sub + "/" + f) if sub else f
        if a.art:
            c = norm("art. " + a.art.rstrip(".")).replace(" ", "")
            for u in units:
                if norm(u["citare"]).replace(" ", "") == c:
                    print(open(os.path.join(base, u["fisier"]), encoding="utf-8").read())
                    return
            continue
        if a.cit:
            c = norm(a.cit).replace(" ", "")
            for u in units:
                if norm(u["citare"]).replace(" ", "") == c:
                    print("[%s] %s — %s\n   %s" % (tag, u["citare"], rel(u["fisier"]), u["text"]))
            continue
        terms = [norm(t) for t in a.termeni]
        if not terms:
            ap.print_help(); return
        for u in units:
            f = fise.get(u["fisier"], {})
            titlu = f.get("titlu_scurt") or ""
            if u["tip"] in ("articol", "anexa"):
                hay = norm(" ".join([titlu] + (f.get("cuvinte_cheie") or [])))
                if hay and all(t in hay for t in terms):
                    hits.append((0, tag, u, "fișă: " + titlu + ((" — " + f["rezumat"]) if f.get("rezumat") else ""), titlu, rel))
                continue
            if all(t in norm(u["text"]) for t in terms):
                hits.append((1, tag, u, u["text"], titlu, rel))
    if a.art:
        sys.exit("Nu există art. " + a.art)
    if a.cit:
        return
    hits.sort(key=lambda h: h[0])
    for _, tag, u, txt, titlu, rel in hits[: a.n]:
        print("● [%s] %s%s  (%s)%s" % (tag, u["citare"], (" [" + titlu + "]") if titlu else "", rel(u["fisier"]),
                                     "  *modificat" if u.get("modificat") else ""))
        print("   " + (txt if len(txt) < 420 else txt[:420] + "…"))
    print("\n%d rezultate%s" % (len(hits), "" if len(hits) <= a.n else " (afișate primele %d; folosește -n)" % a.n))


main()
