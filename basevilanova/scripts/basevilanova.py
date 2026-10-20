#!/usr/bin/env python3
"""Equips, classificacions i calendaris del CNF Base Vilanova (cnfbasevilanova.cat).

Les dades són de la Federació Catalana de Futbol, incrustades a l'HTML del club.
El club NO publica noms ni dorsals: no hi ha "plantilla" enlloc del web.

Ús:
  basevilanova.py equips                      # catàleg d'equips (totes les categories)
  basevilanova.py equips --categoria cadets
  basevilanova.py cerca femeni                # buscar equip pel nom
  basevilanova.py equip cadet-a-femeni        # classificació + propers partits
  basevilanova.py equip cadet-a-femeni --resultats
  basevilanova.py setmana                     # propers partits de tot el club
  basevilanova.py --json equip cadet-a-femeni
"""
import argparse
import datetime as dt
import hashlib
import html
import json
import os
import re
import sys
import time
import unicodedata
import urllib.request

BASE = "https://cnfbasevilanova.cat/ca"
EQUIPS = BASE + "/equips"
CALENDARI = BASE + "/calendari"
CATEGORIES = ["seniors", "juvenils", "cadets", "infantils", "alevi",
              "benjami", "prebenjami", "iniciacio", "futbol-pc"]
UA = "Mozilla/5.0 (compatible; hermes-agent basevilanova skill)"
CACHE_DIR = os.path.expanduser("~/.hermes/cache/basevilanova")
TTL = 30 * 60
TTL_CATALOG = 12 * 3600
DIES = ["dilluns", "dimarts", "dimecres", "dijous", "divendres", "dissabte", "diumenge"]
MESOS = {m: i + 1 for i, m in enumerate(
    ["gener", "febrer", "marc", "abril", "maig", "juny", "juliol",
     "agost", "setembre", "octubre", "novembre", "desembre"])}
MESOS["març"] = 3


# --------------------------------------------------------------- xarxa i caché

def _cache_path(url):
    return os.path.join(CACHE_DIR, hashlib.sha1(url.encode()).hexdigest()[:16] + ".html")


def fetch(url, ttl=TTL, no_cache=False):
    p = _cache_path(url)
    if not no_cache:
        try:
            if time.time() - os.path.getmtime(p) < ttl:
                return open(p, encoding="utf-8").read()
        except OSError:
            pass
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=90) as r:
        data = r.read().decode("utf-8", "replace")
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        open(p, "w", encoding="utf-8").write(data)
    except OSError:
        pass
    return data


# --------------------------------------------------------------- helpers

def clean(s):
    s = re.sub(r"<!--.*?-->", " ", s or "", flags=re.S)
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s).replace("\u200e", "").replace("\u200f", "")
    return re.sub(r"\s+", " ", s).strip()


def norm(s):
    s = (s or "").replace("\u200e", "").replace("\u200f", "")
    s = "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).lower().strip()


def parse_data(txt):
    """'dissabte, 24 d’octubre de 2026 · CAMP' -> (date|None, camp)."""
    txt = clean(txt)
    camp = txt.split("·", 1)[1].strip() if "·" in txt else ""
    m = re.search(r"(\d{1,2})\s+d[e’']?\s*([A-Za-zÀ-ÿ]+)\s+de\s+(\d{4})", txt)
    if not m:
        return None, camp
    mes = MESOS.get(m.group(2).lower().strip("’'"))
    if not mes:
        return None, camp
    try:
        return dt.date(int(m.group(3)), mes, int(m.group(1))), camp
    except ValueError:
        return None, camp


def parse_hora(txt):
    m = re.search(r"(\d{1,2})[.:](\d{2})\s*h", txt or "")
    return f"{int(m.group(1)):02d}:{m.group(2)}" if m else ""


# --------------------------------------------------------------- pàgina de categoria

def parse_roster(h):
    """Llista d'equips de la categoria: nom, slug (o None si no té fitxa) i nota."""
    out = []
    ul = re.search(r'<ul data-roster="true".*?</ul>', h, re.S)
    if not ul:
        return out
    for li in re.finditer(r"<li[^>]*>(.*?)</li>", ul.group(0), re.S):
        c = li.group(1)
        nom = re.search(r'<span class="block truncate[^"]*">(.*?)</span>', c, re.S)
        nota = re.search(r'<span class="text-\[11px\][^"]*">(.*?)</span>', c, re.S)
        href = re.search(r'href="#equip-([a-z0-9\-]+)"', c)
        out.append({"nom": clean(nom.group(1)) if nom else "",
                    "slug": href.group(1) if href else None,
                    "nota": clean(nota.group(1)) if nota else ""})
    return out


def parse_blocs(h):
    """{slug: {nom, lliga, classificacio, partits}} a partir dels <details data-team-block>."""
    teams = {}
    parts = re.split(r'<details data-team-block="true"[^>]*>', h)
    for chunk in parts[1:]:
        m = re.search(r'id="equip-([a-z0-9\-]+)"', chunk)
        if not m:
            continue
        slug = m.group(1)
        suma = re.search(r"<summary[^>]*>(.*?)</summary>", chunk, re.S)
        nom, lliga = slug, ""
        if suma:
            s = suma.group(1)
            nm = re.search(r'<span class="display text-3xl">(.*?)</span>', s, re.S)
            lg = re.search(r'<span class="text-xs[^"]*">(.*?)</span>', s, re.S)
            nom = clean(nm.group(1)) if nm else slug
            lliga = clean(lg.group(1)) if lg else ""

        classif = []
        tbl = re.search(r"<table.*?</table>", chunk, re.S)
        if tbl:
            for row in re.finditer(r"<tr[^>]*>(.*?)</tr>", tbl.group(0), re.S):
                cls = re.search(r'<tr[^>]*class="([^"]*)"', row.group(0))
                cells = [clean(c) for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row.group(1), re.S)]
                if len(cells) >= 10 and cells[0].replace(".", "").isdigit():
                    classif.append({"pos": cells[0], "equip": cells[1],
                                    "pj": cells[2], "g": cells[3], "e": cells[4], "p": cells[5],
                                    "gf": cells[6], "gc": cells[7], "dg": cells[8],
                                    "punts": cells[9],
                                    "propi": bool(cls and "bg-accent" in cls.group(1))})
        propi_nom = next((c["equip"] for c in classif if c["propi"]), "")

        partits = []
        for det in re.finditer(r"<details.*?</details>", chunk, re.S):
            d = det.group(0)
            jor = re.search(r"Jornada[^0-9]*(\d+)", clean(d))
            jornada = jor.group(1) if jor else ""
            bloc = []
            for li in re.finditer(r"<li([^>]*)>(.*?)</li>", d, re.S):
                attr, c = li.group(1), li.group(2)
                eqs = [clean(x) for x in re.findall(r'<span class="truncate">(.*?)</span>', c, re.S)]
                centre = re.search(r'<span class="[^"]*tabular-nums[^"]*">(.*?)</span>', c, re.S)
                marca = clean(centre.group(1)) if centre else ""
                p = re.search(r'<p class="text-xs[^"]*">(.*?)</p>', c, re.S)
                data, camp = parse_data(p.group(1)) if p else (None, "")
                descansa = "descansa" in norm(c)
                if not eqs and not descansa:
                    continue
                propi = ("bg-surface" in attr) or (propi_nom and propi_nom in eqs)
                hora = parse_hora(marca)
                bloc.append({"jornada": jornada,
                             "local": eqs[0] if eqs else "",
                             "visitant": eqs[1] if len(eqs) > 1 else "",
                             "marca": "" if hora else marca.replace(" ", ""),
                             "hora": hora,
                             "data": data.isoformat() if data else "",
                             "camp": camp, "descansa": descansa, "propi": propi})
            # els partits d'una jornada comparteixen cap de setmana: backfill de dates
            ref = next((x["data"] for x in bloc if x["data"]), "")
            for x in bloc:
                if not x["data"]:
                    x["data"] = ref
            partits.extend(bloc)
        teams[slug] = {"slug": slug, "nom": nom, "lliga": lliga, "equip_fcf": propi_nom,
                       "classificacio": classif, "partits": partits}
    return teams


def parse_categoria(h):
    return parse_roster(h), parse_blocs(h)


def cataleg(no_cache=False, nomes=None):
    cats = [nomes] if nomes else CATEGORIES
    eqs = []
    for cat in cats:
        try:
            h = fetch(f"{EQUIPS}/{cat}", ttl=TTL_CATALOG, no_cache=no_cache)
        except Exception as exc:
            print(f"! categoria {cat}: {exc}", file=sys.stderr)
            continue
        roster, blocs = parse_categoria(h)
        for r in roster:
            e = dict(r)
            e["categoria"] = cat
            t = blocs.get(r.get("slug") or "")
            e["lliga"] = t["lliga"] if t else ""
            eqs.append(e)
    vist, out = set(), []
    for e in eqs:
        k = (e["categoria"], e["nom"])
        if k in vist:
            continue
        vist.add(k)
        out.append(e)
    return out


# --------------------------------------------------------------- calendari del club

def parse_calendari(h):
    out = []
    for m in re.finditer(r"<article[^>]*>(.*?)</article>", h, re.S):
        c = m.group(1)
        lliga = re.search(r'<p class="text-\[11px\][^"]*">(.*?)</p>', c, re.S)
        seu = re.search(r'<p class="text-xs[^"]*">(.*?)</p>', c, re.S)
        rival = re.search(r'<h3[^>]*>.*?<span class="min-w-0[^"]*">(.*?)</span>', c, re.S)
        dds = [clean(x) for x in re.findall(r"<dd>(.*?)</dd>", c, re.S)]
        data, camp = (None, "")
        for v in dds:
            if not data:
                data, _ = parse_data(v)
            if not camp and ("CAMP" in v.upper() or "ESTADI" in v.upper() or "PISTA" in v.upper()):
                camp = v
        out.append({"competicio": clean(lliga.group(1)) if lliga else "",
                    "seu_equip": clean(seu.group(1)) if seu else "",
                    "rival": clean(rival.group(1)) if rival else "",
                    "data": data.isoformat() if data else "",
                    "hora": next((parse_hora(v) for v in dds if parse_hora(v)), ""),
                    "camp": camp})
    return out


# --------------------------------------------------------------- presentació

def fmt_partit(p):
    d = dt.date.fromisoformat(p["data"]) if p.get("data") else None
    quan = f"{DIES[d.weekday()][:3]} {d.strftime('%d/%m')}" if d else "?"
    hora = f" {p['hora']}" if p.get("hora") else ""
    if p.get("descansa"):
        return f"{quan} · descansa"
    if p.get("visitant"):
        txt = f"{quan}{hora} · {p['local']} {p['marca'] or 'vs'} {p['visitant']}"
        return txt + (f" · {p['camp']}" if p["camp"] else "")
    return f"{quan}{hora} · {p['marca']}"


def cmd_equips(args):
    eqs = cataleg(args.no_cache, args.categoria)
    if args.json:
        print(json.dumps(eqs, ensure_ascii=False, indent=1))
        return 0
    cat = None
    for e in eqs:
        if e["categoria"] != cat:
            cat = e["categoria"]
            print(f"\n== {cat.upper()} ==")
        slug = e["slug"] or "-"
        print(f"  {slug:<26} {e['nom']}" + (f"  · {e['lliga']}" if e["lliga"] else "")
              + ("" if e["slug"] else "  (sense fitxa)"))
    return 0


def cmd_cerca(args):
    q = norm(args.text)
    eqs = [e for e in cataleg(args.no_cache) if q in norm(e["nom"]) or q in norm(e["slug"] or "")]
    if args.json:
        print(json.dumps(eqs, ensure_ascii=False, indent=1))
        return 0 if eqs else 1
    for e in eqs:
        print(f"{e['categoria']:<12} {(e['slug'] or '-'):<26} {e['nom']}"
              + (f" · {e['lliga']}" if e["lliga"] else ""))
    if not eqs:
        print(f"Cap equip coincideix amb '{args.text}'.", file=sys.stderr)
    return 0 if eqs else 1


def cmd_equip(args):
    slug = args.slug
    cat = args.categoria
    if not cat:
        cand = [e for e in cataleg(args.no_cache) if e["slug"] == slug]
        if not cand:
            q = norm(slug)
            cand = [e for e in cataleg(args.no_cache) if q in norm(e["nom"])]
        if len(cand) == 1:
            slug, cat = cand[0]["slug"], cand[0]["categoria"]
        elif len(cand) > 1:
            print("Diversos equips coincideixen: " + ", ".join(f"{c['slug']} ({c['categoria']})" for c in cand),
                  file=sys.stderr)
            return 1
        else:
            print(f"No trobo l'equip '{args.slug}'. Prova 'cerca'.", file=sys.stderr)
            return 1
    h = fetch(f"{EQUIPS}/{cat}", no_cache=args.no_cache)
    _, blocs = parse_categoria(h)
    d = blocs.get(slug)
    if not d:
        print(f"'{slug}' no té fitxa a la categoria {cat}.", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(d, ensure_ascii=False, indent=1))
        return 0

    print(f"{d['nom']}  ·  {d['lliga']}")
    if d["classificacio"]:
        print("\nClassificació   PJ  G  E  P  GF GC  DG Pts")
        for r in d["classificacio"]:
            marca = "  <<<" if r["propi"] else ""
            print(f"  {r['pos']:>2}. {r['equip'][:38]:<38} {r['pj']:>2} {r['g']:>2} {r['e']:>2} {r['p']:>2} "
                  f"{r['gf']:>3} {r['gc']:>3} {r['dg']:>4} {r['punts']:>3}{marca}")

    avui = dt.date.today()
    meus = [p for p in d["partits"] if p["propi"]]
    jugats = [p for p in meus if p["data"] and dt.date.fromisoformat(p["data"]) < avui and not p["descansa"]]
    propers = [p for p in meus if p["data"] and dt.date.fromisoformat(p["data"]) >= avui]
    if args.resultats and jugats:
        print("\nResultats:")
        for p in jugats:
            print("  " + fmt_partit(p))
    if propers:
        print("\nPropers:")
        for p in propers[:8]:
            print("  " + fmt_partit(p))
    if not jugats and not propers:
        print("\nSense partits publicats per a aquest equip.", file=sys.stderr)
    return 0


def cmd_setmana(args):
    h = fetch(CALENDARI, no_cache=args.no_cache)
    items = parse_calendari(h)
    avui = dt.date.today()
    limit = avui + dt.timedelta(days=args.dies)
    sel = [i for i in items if i["data"] and avui <= dt.date.fromisoformat(i["data"]) <= limit]
    sel.sort(key=lambda x: (x["data"], x["hora"]))
    if args.json:
        print(json.dumps(sel, ensure_ascii=False, indent=1))
        return 0 if sel else 1
    if not sel:
        print(f"Cap partit publicat entre {avui} i {limit}.", file=sys.stderr)
        return 1
    print(f"CNF Base Vilanova · propers partits ({avui} → {limit})")
    for i in sel:
        d = dt.date.fromisoformat(i["data"])
        equip = i["seu_equip"]
        equip = equip.replace("A casa ·", "a casa ·").replace("A fora ·", "fora ·")
        print(f"· {DIES[d.weekday()][:3]} {d.strftime('%d/%m')} {i['hora'] or '--:--'} | {equip} — vs {i['rival']}"
              + (f" · {i['camp']}" if i["camp"] else ""))
    return 0


def main():
    ap = argparse.ArgumentParser(description="CNF Base Vilanova: equips, classificacions i calendaris")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--no-cache", action="store_true")
    sub = ap.add_subparsers(dest="cmd")

    p = sub.add_parser("equips")
    p.add_argument("--categoria")

    p = sub.add_parser("cerca")
    p.add_argument("text")

    p = sub.add_parser("equip")
    p.add_argument("slug")
    p.add_argument("--categoria")
    p.add_argument("--resultats", action="store_true")

    p = sub.add_parser("setmana")
    p.add_argument("--dies", type=int, default=8)

    args = ap.parse_args()
    if not args.cmd:
        ap.print_help()
        return 0
    return {"equips": cmd_equips, "cerca": cmd_cerca, "equip": cmd_equip, "setmana": cmd_setmana}[args.cmd](args)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:
        sys.exit(0)
    except KeyboardInterrupt:
        sys.exit(130)
