"""Parseaza HTML-ul unui act de pe legislatie.just.ro (DetaliiDocumentAfis) in:
  - articole/art-XXX.md   (un fisier pe articol, cu frontmatter)
  - unitati.jsonl         (o inregistrare pe articol/alineat/litera/punct, cu citarea canonica)
  - <slug>.md             (textul integral, structurat)
Utilizare: python -I parse_portal.py <html> <out_dir> <slug> <titlu> <url> <data_consolidare>
"""
import sys, re, json, os
from html.parser import HTMLParser

STRUCT = {"S_CAP", "S_SEC", "S_ART", "S_ALN", "S_LIT", "S_PCT", "S_LIN", "S_PAR", "S_NTA",
          "S_TTL", "S_PRT", "S_ANX", "S_CRT", "S_POR"}
VOID = {"br", "img", "hr", "input", "meta", "link"}


class Node:
    def __init__(self, tag, cls, style, parent):
        self.tag, self.cls, self.style, self.parent = tag, cls, style, parent
        self.children = []  # Node | str


class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("root", "", "", None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        if tag in VOID:
            if tag == "br":
                self.cur.children.append("\n")
            return
        a = dict(attrs)
        n = Node(tag, a.get("class") or "", a.get("style") or "", self.cur)
        self.cur.children.append(n)
        self.cur = n

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
    return (n.cls.endswith("_SHORT") or n.cls == "TAG_COLLAPSED" or n.tag in ("script", "style"))


def text(n, stop_struct=False):
    out = []
    for c in n.children:
        if isinstance(c, str):
            out.append(c)
        elif skip(c):
            continue
        elif stop_struct and c.cls in STRUCT:
            continue
        else:
            out.append(text(c, stop_struct))
    return "".join(out)


def child(n, suffix):
    for c in n.children:
        if isinstance(c, Node) and c.cls == n.cls + suffix:
            return c
    return None


def find_all(n, cls, acc):
    for c in n.children:
        if isinstance(c, Node):
            if c.cls == cls:
                acc.append(c)
            find_all(c, cls, acc)
    return acc


def struct_children(n):
    """Copii structurali directi (trecand prin wrappere nestructurale)."""
    out = []
    for c in n.children:
        if isinstance(c, Node) and not skip(c):
            if c.cls in STRUCT:
                out.append(c)
            elif not c.cls.endswith(("_TTL", "_DEN")):
                out.extend(struct_children(c))
    return out


def art_id(label):
    m = re.match(r"Articolul\s+(\d+)(?:\^(\d+))?", label)
    if not m:
        return clean(label)
    return m.group(1) + ("^" + m.group(2) if m.group(2) else "")


def main():
    src, out, slug, titlu, url, data = sys.argv[1:7]
    p = P()
    p.feed(open(src, encoding="utf-8").read())
    os.makedirs(os.path.join(out, "articole"), exist_ok=True)

    units, articles = [], []
    ctx = {"capitol": "", "sectiune": ""}

    def cite(aid, path):
        s = "art. " + aid
        for kind, lab in path:
            if kind == "S_ALN":
                s += " alin. " + lab
            elif kind == "S_LIT":
                s += " lit. " + lab
            elif kind == "S_PCT":
                s += " pct. " + lab.rstrip(".")
        return s

    def render(n, aid, path, depth, lines, notes):
        ttl, bdy = child(n, "_TTL"), child(n, "_BDY")
        lab = clean(text(ttl)) if ttl else ""
        body = bdy if bdy is not None else n
        own = clean(text(body, stop_struct=True))
        if bdy is None and lab and own.startswith(lab):
            own = own[len(lab):].strip()
        if n.cls == "S_NTA":
            full = clean(text(body))
            notes.append(full)
            lines.append("  " * depth + "> **Notă:** " + full)
            return
        npath = path + [(n.cls, lab)] if n.cls in ("S_ALN", "S_LIT", "S_PCT") and lab else path
        prefix = (lab + " ") if lab else ""
        if own or lab:
            lines.append("  " * depth + ("- " if depth else "") + prefix + own)
        if n.cls in ("S_ALN", "S_LIT", "S_PCT") and lab:
            units.append({"act": slug, "citare": cite(aid, npath), "articol": aid,
                          "capitol": ctx["capitol"], "sectiune": ctx["sectiune"],
                          "tip": {"S_ALN": "alineat", "S_LIT": "litera", "S_PCT": "punct"}[n.cls],
                          "text": own, "fisier": "articole/" + fname(aid),
                          "modificat": "blue" in n.style})
        for c in struct_children(body):
            render(c, aid, npath, depth + (1 if (own or lab) else 0), lines, notes)

    def fname(aid):
        a, _, b = aid.partition("^")
        return "art-%03d%s.md" % (int(a), ("-" + b) if b else "") if a.isdigit() else "art-" + a + ".md"

    def walk(n):
        for c in struct_children(n):
            if c.cls in ("S_CAP", "S_SEC", "S_TTL", "S_PRT"):
                lab = clean(text(child(c, "_TTL"))) if child(c, "_TTL") else ""
                den = clean(text(child(c, "_DEN"))) if child(c, "_DEN") else ""
                full = (lab + " – " + den).strip(" –")
                if c.cls == "S_SEC":
                    ctx["sectiune"] = full
                else:
                    ctx["capitol"], ctx["sectiune"] = full, ""
                walk(child(c, "_BDY") or c)
                if c.cls == "S_SEC":
                    ctx["sectiune"] = ""
            elif c.cls == "S_ART":
                lab = clean(text(child(c, "_TTL")))
                den = clean(text(child(c, "_DEN"))) if child(c, "_DEN") else ""
                aid = art_id(lab)
                lines, notes = [], []
                bdy = child(c, "_BDY") or c
                own = clean(text(bdy, stop_struct=True))
                if own:
                    lines.append(own)
                for s in struct_children(bdy):
                    render(s, aid, [], 0, lines, notes)
                body = "\n".join(lines)
                acte = sorted(set(re.findall(
                    r"(?:ORDONANȚA DE URGENȚĂ|LEGEA|ORDONANȚA|LEGE) nr\. \d+ din \d+ \w+ \d{4}", " ".join(notes))))
                articles.append({"id": aid, "eticheta": lab, "denumire": den, "capitol": ctx["capitol"],
                                 "sectiune": ctx["sectiune"], "fisier": "articole/" + fname(aid),
                                 "modificat_prin": acte, "text": body})
                units.append({"act": slug, "citare": "art. " + aid, "articol": aid, "capitol": ctx["capitol"],
                              "sectiune": ctx["sectiune"], "tip": "articol",
                              "text": re.sub(r"\s+", " ", body), "fisier": "articole/" + fname(aid),
                              "modificat": bool(acte)})
            else:
                walk(c)

    walk(p.root)

    # unitatile de tip articol trebuie sa preceada sub-unitatile lor
    order = {a["id"]: i for i, a in enumerate(articles)}
    units.sort(key=lambda u: (order[u["articol"]], u["tip"] != "articol"))

    for a in articles:
        fm = ["---", "act: " + titlu, "articol: \"" + a["id"] + "\"", "citare: \"art. " + a["id"] + "\"",
              "capitol: \"" + a["capitol"] + "\"", "sectiune: \"" + a["sectiune"] + "\"",
              "forma_consolidata: " + data, "sursa: " + url,
              "modificat_prin: " + json.dumps(a["modificat_prin"], ensure_ascii=False), "---", "",
              "# " + a["eticheta"] + ((" – " + a["denumire"]) if a["denumire"] else ""), "", a["text"], ""]
        open(os.path.join(out, a["fisier"]), "w", encoding="utf-8", newline="\n").write("\n".join(fm))

    with open(os.path.join(out, "unitati.jsonl"), "w", encoding="utf-8", newline="\n") as f:
        for u in units:
            f.write(json.dumps(u, ensure_ascii=False) + "\n")

    full = ["# " + titlu, "", "Forma consolidată la " + data + " — sursa: " + url, ""]
    cap = sec = None
    for a in articles:
        if a["capitol"] != cap:
            cap = a["capitol"]; sec = None
            full += ["## " + cap, ""]
        if a["sectiune"] and a["sectiune"] != sec:
            sec = a["sectiune"]
            full += ["### " + sec, ""]
        full += ["#### " + a["eticheta"], "", a["text"], ""]
    open(os.path.join(out, slug + ".md"), "w", encoding="utf-8", newline="\n").write("\n".join(full))

    json.dump([{k: v for k, v in a.items() if k != "text"} for a in articles],
              open(os.path.join(out, "cuprins.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(articles), "articole;", len(units), "unitati")


main()
