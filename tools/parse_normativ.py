"""Parseaza forma printabila a unui normativ de pe legislatie.just.ro (articole numerotate zecimal,
anexe, tabele, figuri) in fisiere markdown + unitati.jsonl + cuprins.json + tabele.json + figuri.json.
Utilizare: python -I parse_normativ.py <html> <out_dir> <slug> <titlu> <url> <data>
"""
import sys, re, json, os
from html.parser import HTMLParser

src, OUT, SLUG, TITLU, URL, DATA = sys.argv[1:7]
VOID = {"br", "img", "hr", "input", "meta", "link"}
LABELLED = {"S_ALN": "alin.", "S_LIT": "lit.", "S_PCT": "pct.", "S_LIN": None}
BLOCK = {"S_PAR", "A_PAR", "S_NTA_PAR", "A_ELEMENT_CENTER", "S_NTA", "li", "p", "div"}


class Node:
    __slots__ = ("tag", "cls", "attrs", "parent", "children")

    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.parent = tag, attrs, parent
        self.cls = attrs.get("class") or ""
        self.children = []


class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("root", {}, None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        n = Node(tag, dict(attrs), self.cur)
        self.cur.children.append(n)
        if tag not in VOID:
            self.cur = n

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, dict(attrs), self.cur))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, d):
        self.cur.children.append(d)


def clean(s):
    return re.sub(r"\s+", " ", s).strip()


def skip(n):
    return n.cls.endswith("_SHORT") or n.cls == "TAG_COLLAPSED" or n.tag in ("script", "style", "head")


def child(n, suffix):
    for c in n.children:
        if isinstance(c, Node) and c.cls == n.cls + suffix:
            return c
    return None


def flat(n):
    """Text plat (pentru etichete si celule de tabel)."""
    out = []
    for c in n.children:
        if isinstance(c, str):
            out.append(c)
        elif skip(c):
            continue
        elif c.tag == "img":
            out.append(" " + img(c) + " ")
        elif c.tag == "br":
            out.append(" ")
        else:
            out.append(" " + flat(c) + " ")
    return "".join(out)


def img(n):
    name = (n.attrs.get("src") or "").rsplit("/", 1)[-1]
    IMAGES.append(name)
    return "![figură](../figuri/%s)" % name


def table_md(t):
    rows = []
    def trs(n):
        for c in n.children:
            if isinstance(c, Node):
                if c.tag == "tr":
                    rows.append(c)
                elif c.tag != "table":
                    trs(c)
    trs(t)
    grid, carry = [], {}
    for r in rows:
        line, col = [], 0
        cells = [c for c in r.children if isinstance(c, Node) and c.tag in ("td", "th")]
        ci = 0
        while ci < len(cells) or col in carry:
            if col in carry:
                txt, left = carry[col]
                line.append(txt)
                if left > 1:
                    carry[col] = (txt, left - 1)
                else:
                    del carry[col]
                col += 1
                continue
            c = cells[ci]; ci += 1
            txt = clean(flat(c)).replace("|", "/")
            cs = int(c.attrs.get("colspan") or 1) if (c.attrs.get("colspan") or "").isdigit() else 1
            rs = int(c.attrs.get("rowspan") or 1) if (c.attrs.get("rowspan") or "").isdigit() else 1
            for _ in range(cs):
                line.append(txt)
                if rs > 1:
                    carry[col] = (txt, rs - 1)
                col += 1
        grid.append(line)
    if not grid:
        return []
    w = max(len(l) for l in grid)
    grid = [l + [""] * (w - len(l)) for l in grid]
    out = ["", "| " + " | ".join(grid[0]) + " |", "|" + "---|" * w]
    out += ["| " + " | ".join(l) + " |" for l in grid[1:]]
    return out + [""]


class Doc:
    def __init__(self, kind, ident, label):
        self.kind, self.id, self.label = kind, ident, label
        self.lines, self.buf, self.units = [], [], []
        self.force = None

    def flush(self, indent=0):
        t = clean("".join(self.buf))
        self.buf = []
        if t and self.force is not None:
            indent = self.force
        if t:
            self.force = None
        if t:
            self.lines.append(("  " * indent) + t)

    def raw(self, lines):
        self.lines.extend(lines)


IMAGES = []
docs = []
inter = Doc("inter", "", "")
stack = [inter]
inter_log = []  # (index of next doc, line)


def cur():
    return stack[-1]


def walk(n, depth, path):
    d = cur()
    for c in n.children:
        if isinstance(c, str):
            d.buf.append(c)
            continue
        if skip(c):
            continue
        if c.tag == "br":
            d.flush(depth); continue
        if c.tag == "img":
            d.flush(depth); d.raw(["", "  " * depth + img(c), ""]); continue
        if c.tag == "table":
            if c.cls == "S_EMT":
                d.buf.append(flat(c)); d.flush(depth)
            else:
                d.flush(depth); d.raw(table_md(c))
            continue
        if c.cls == "S_ART" and len(stack) == 1:
            d.flush(depth)
            lab = clean(flat(child(c, "_TTL")))
            aid = lab.replace("Articolul", "").strip().rstrip(".")
            nd = Doc("art", aid, lab)
            docs.append(nd); stack.append(nd)
            walk(child(c, "_BDY") or c, 0, [])
            nd.flush(0); stack.pop()
            d = cur(); continue
        if c.cls == "S_ANX":
            d.flush(depth)
            lab = clean(flat(child(c, "_TTL")))
            aid = lab.replace("Anexa nr.", "").strip()
            nd = Doc("anx", aid, lab)
            den = child(c, "_DEN")
            if den is not None and clean(flat(den)):
                nd.lines.append(clean(flat(den)))
            docs.append(nd); stack.append(nd)
            walk(child(c, "_BDY") or c, 0, [])
            nd.flush(0); stack.pop()
            d = cur(); continue
        if c.cls in ("S_CAP", "S_SEC", "S_TTL", "S_PRT", "S_ART"):
            d.flush(depth)
            ttl, den = child(c, "_TTL"), child(c, "_DEN")
            h = clean((flat(ttl) if ttl else "") + " " + (flat(den) if den else ""))
            if h:
                d.raw(["", "**" + h + "**", ""])
            walk(child(c, "_BDY") or c, depth, path)
            cur().flush(depth); continue
        if c.cls in LABELLED:
            d.flush(depth)
            ttl, bdy = child(c, "_TTL"), child(c, "_BDY")
            lab = clean(flat(ttl)) if ttl else ""
            start = len(d.lines)
            d.buf.append(("- " if depth else "") + lab + " ")
            d.force = depth
            npath = path + [(LABELLED[c.cls], lab)] if (LABELLED[c.cls] and lab) else path
            walk(bdy if bdy is not None else c, depth + 1, npath)
            # prima linie a unitatii = eticheta + textul propriu
            d.flush(depth)
            if LABELLED[c.cls] and lab and d.kind != "inter" and start < len(d.lines):
                first = d.lines[start].strip()
                d.units.append((npath, first[2:] if first.startswith("- ") else first, start))
            continue
        if c.cls in BLOCK or c.tag in BLOCK:
            d.flush(depth)
            walk(c, depth, path)
            cur().flush(depth); continue
        walk(c, depth, path)


p = P()
p.feed(open(src, encoding="utf-8").read())
body = p.root
orig_flush = Doc.flush
def logged_flush(self, indent=0):
    n = len(self.lines)
    orig_flush(self, indent)
    if self is inter and len(self.lines) > n:
        inter_log.append((len(docs), self.lines[-1].strip()))
Doc.flush = logged_flush
walk(body, 0, [])
inter.flush(0)

# titluri de capitole/sectiuni din liniile dintre articole: "2.3.6. Titlu"
headings = {}
for _, l in inter_log:
    m = re.match(r"^(?:- )?(\d+(?:\.\d+)*)\.\s+(\S.{2,})$", l)
    if m and m.group(1) not in headings:
        headings[m.group(1)] = m.group(2).rstrip(" .…").strip()


def crumbs(aid):
    parts = aid.split(".")
    out = []
    for i in range(1, len(parts)):
        k = ".".join(parts[:i])
        if k in headings:
            out.append(k + ". " + headings[k])
    return out


def cite(d, path):
    base = ("art. " + d.id) if d.kind == "art" else ("Anexa nr. " + d.id)
    out = []
    for kind, lab in path:
        lab = lab.strip()
        if re.match(r"^[(]\d+(\^\d+)?[)]$", lab):
            out.append("alin. " + lab)
        elif re.match(r"^[(]?[a-z]{1,3}(\^\d+)?[)]$", lab):
            out.append("lit. " + lab.lstrip("("))
        elif re.match(r"^(A\.)?\d+(\.\d+)+\.?$", lab):
            out = ["pct. " + lab.rstrip(".")]  # reper global: inlocuieste calea
        else:
            out.append("pct. " + lab.rstrip("."))
    return " ".join([base] + out)


def anx_title(d):
    for l in d.lines[:6]:
        t = l.strip().strip("*")
        if t and not t.startswith("|") and not t.startswith("!["):
            return t[:160]
    return ""


os.makedirs(os.path.join(OUT, "articole"), exist_ok=True)
os.makedirs(os.path.join(OUT, "anexe"), exist_ok=True)
units, cuprins, tabele, figuri = [], [], [], []
seen = {}
import bisect
for d in docs:
    # parti: anexele foarte mari se impart pe capitole
    parts = [("", "", 0)]
    if d.kind == "anx" and sum(len(l) for l in d.lines) > 150000:
        for i, l in enumerate(d.lines):
            m = re.match(r"^\*\*CAPITOLUL (\d+)\s*(.*?)\*\*$", l.strip())
            if m:
                j = i
                while j > 0 and (not d.lines[j - 1].strip() or d.lines[j - 1].startswith("**SECȚIUNEA")):
                    j -= 1
                parts.append(("-cap" + m.group(1), "cap. %s %s" % (m.group(1), m.group(2).strip()), j))
    starts = [x[2] for x in parts]
    pinfo = []
    for k, (suf, ptitle, st) in enumerate(parts):
        en = parts[k + 1][2] if k + 1 < len(parts) else len(d.lines)
        text = re.sub(r"\n{3,}", "\n\n", "\n".join(d.lines[st:en])).strip()
        if d.kind == "art":
            f = "articole/art-%s.md" % d.id
            cr = crumbs(d.id)
            cap = cr[0] if cr else "Capitolul " + d.id.split(".")[0]
            titlu = "Art. " + d.id
        else:
            f = "anexe/anexa-%s%s.md" % (d.id, suf)
            cr = [d.label + " – " + anx_title(d)] + ([ptitle] if ptitle else ([] if len(parts) == 1 else ["partea introductivă"]))
            cap = "Anexe"
            titlu = " – ".join(cr)
        base = cite(d, []) + ((", " + ptitle.split(" ", 2)[0] + " " + ptitle.split(" ", 2)[1]) if ptitle else "")
        tabs = re.findall(r"(?m)^\s*(?:- )?(Tabelul?\s+\d+[a-z]?)\s*[:\-–.]\s*(.{0,200})", text)
        figs = re.findall(r"(?m)^\s*(?:- )?(Figura\s+\d+[a-z]?)\s*[:\-–.]\s*(.{0,200})", text)
        for t, cap_t in tabs:
            tabele.append({"tabel": clean(t), "titlu": clean(cap_t), "citare": base, "fisier": f, "_ok": "|---" in text})
        for t, cap_t in figs:
            figuri.append({"figura": clean(t), "titlu": clean(cap_t), "citare": base, "fisier": f, "_ok": "![figură]" in text})
        fm = ["---", "act: " + TITLU, "citare: \"%s\"" % base, "structura: " + json.dumps(cr, ensure_ascii=False),
              "tabele: " + json.dumps(sorted({clean(t) for t, _ in tabs}), ensure_ascii=False),
              "figuri: " + json.dumps(sorted({clean(t) for t, _ in figs}), ensure_ascii=False),
              "forma: " + DATA, "sursa: " + URL, "---", "", "# " + titlu, ""]
        open(os.path.join(OUT, f), "w", encoding="utf-8", newline="\n").write("\n".join(fm) + text + "\n")
        cuprins.append({"tip": d.kind, "id": d.id + suf, "citare": base, "fisier": f, "structura": cr, "capitol": cap,
                        "titlu": titlu if d.kind == "anx" else "", "octeti": len(text.encode("utf-8")),
                        "tabele": sorted({clean(t) for t, _ in tabs}), "figuri": sorted({clean(t) for t, _ in figs})})
        units.append({"act": SLUG, "citare": base, "tip": "articol" if d.kind == "art" else "anexa", "structura": cr,
                      "text": clean(re.sub(r"!\[figură\]\([^)]*\)", "", text))[:6000], "fisier": f})
        pinfo.append((f, cr))
    for path, first, st in d.units:
        f, cr = pinfo[bisect.bisect_right(starts, st) - 1]
        c = cite(d, path)
        seen[c] = seen.get(c, 0) + 1
        units.append({"act": SLUG, "citare": c, "nr_aparitie": seen[c], "tip": path[-1][0].rstrip("."),
                      "structura": cr, "text": first, "fisier": f})


def dedupe(lst, key):
    best = {}
    for x in lst:
        k = x[key]
        if k not in best or (x["_ok"] and not best[k]["_ok"]):
            best[k] = x
    out = sorted(best.values(), key=lambda x: (int(re.search(r"\d+", x[key]).group()), x[key]))
    for x in out:
        x.pop("_ok")
    return out


tabele, figuri = dedupe(tabele, "tabel"), dedupe(figuri, "figura")

with open(os.path.join(OUT, "unitati.jsonl"), "w", encoding="utf-8", newline="\n") as fh:
    for u in units:
        fh.write(json.dumps(u, ensure_ascii=False) + "\n")
for name, obj in (("cuprins.json", cuprins), ("tabele.json", tabele), ("figuri.json", figuri),
                  ("structura.json", headings)):
    json.dump(obj, open(os.path.join(OUT, name), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
open(os.path.join(OUT, "sursa", "imagini.txt"), "w").write("\n".join(sorted(set(IMAGES))) + "\n")
open(os.path.join(OUT, "sursa", "text-intre-articole.txt"), "w", encoding="utf-8").write(
    "\n".join("%d\t%s" % x for x in inter_log))

full = ["# " + TITLU, "", "Forma: %s — sursa: %s" % (DATA, URL), ""]
last = None
for d in docs:
    if d.kind == "art":
        cr = crumbs(d.id)
        for i, h in enumerate(cr):
            if last is None or i >= len(last) or last[i] != h:
                full += ["#" * min(i + 2, 5) + " " + h, ""]
        last = cr
        full += ["###### Art. " + d.id, ""]
    else:
        full += ["## " + d.label, ""]
    full += [re.sub(r"\n{3,}", "\n\n", "\n".join(d.lines)).strip(), ""]
open(os.path.join(OUT, SLUG + ".md"), "w", encoding="utf-8", newline="\n").write("\n".join(full))
print(len([d for d in docs if d.kind == "art"]), "articole;", len([d for d in docs if d.kind == "anx"]), "anexe;",
      len(units), "unitati;", len(tabele), "tabele;", len(figuri), "figuri;", len(set(IMAGES)), "imagini;",
      len(headings), "titluri; linii intre articole:", len(inter_log))
