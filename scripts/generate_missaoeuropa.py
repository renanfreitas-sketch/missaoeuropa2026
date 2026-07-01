!/usr/bin/env python3
"""
generate_missaoeuropa.py
Busca dados do board monday.com 18420142846 (Missão Comercial Europa 2026)
e gera missaoeuropa2026/index.html no repositório.
Requer: MONDAY_API_TOKEN como variável de ambiente.
"""

import os, json, urllib.request, urllib.error, base64, sys
from datetime import datetime, timezone, timedelta
from collections import Counter

# ── CONFIG ────────────────────────────────────────────────────────────────────
BOARD_ID       = 18420142846
MONDAY_API_URL = "https://api.monday.com/v2"
MONDAY_TOKEN   = os.environ.get("MONDAY_API_TOKEN", "")

# Column IDs (idênticos ao board de Bruxelas)
COL_EMPRESA   = "short_text2ykzxnei"
COL_RESP      = "short_texthyvt3a2x"
COL_FUNCAO    = "short_textcahqz9j1"
COL_CONTATOS  = "numbersnh3p64o"
COL_NOVOS     = "number648tl9lq"
COL_EV        = "number2a68bhzp"
COL_12M       = "numberjw7h2n4q"
COL_PAPEL     = "single_selectkpjetf5"
COL_RESULT    = "single_selectl726nsw"
COL_INFRA     = "single_selecttig2xxg"
COL_ATD       = "single_selectz3q3lpx"
COL_ORG       = "single_selectt67l8vw"
COL_NEGOCIO   = "single_selectpkpo16k"
COL_ESTRATEGIA= "single_selectbft1eym"
COL_CASE      = "single_selectivw9m55"
COL_CONTTYPE  = "multi_selectccnwx71v"
COL_DATE      = "date4pfzxy2k"
COL_SAT       = "long_textsn2j4f5n"
COL_APEX      = "long_textq0q9r47l"
COL_CITEQUAIS = "short_textkmog7yzv"

# ── FETCH FROM MONDAY ─────────────────────────────────────────────────────────
def fetch_items():
    all_items = []
    cursor    = None
    while True:
        cursor_arg = f', cursor: "{cursor}"' if cursor else ""
        query = f"""
        query {{
          boards(ids: [{BOARD_ID}]) {{
            items_page(limit: 100{cursor_arg}) {{
              cursor
              items {{
                id name
                column_values(ids: [
                  "{COL_EMPRESA}", "{COL_RESP}", "{COL_FUNCAO}",
                  "{COL_CONTATOS}", "{COL_NOVOS}", "{COL_EV}", "{COL_12M}",
                  "{COL_PAPEL}", "{COL_RESULT}", "{COL_INFRA}", "{COL_ATD}",
                  "{COL_ORG}", "{COL_NEGOCIO}", "{COL_ESTRATEGIA}", "{COL_CASE}",
                  "{COL_CONTTYPE}", "{COL_DATE}",
                  "{COL_SAT}", "{COL_APEX}", "{COL_CITEQUAIS}"
                ]) {{ id text value }}
              }}
            }}
          }}
        }}
        """
        payload = json.dumps({"query": query}).encode()
        req = urllib.request.Request(
            MONDAY_API_URL,
            data=payload,
            method="POST",
            headers={
                "Authorization": MONDAY_TOKEN,
                "Content-Type":  "application/json",
                "API-Version":   "2024-10",
            }
        )
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read())

        page    = data["data"]["boards"][0]["items_page"]
        items   = page["items"]
        cursor  = page.get("cursor")
        all_items.extend(items)
        if not cursor or not items:
            break
    return all_items


def col(item, col_id):
    for cv in item["column_values"]:
        if cv["id"] == col_id:
            return cv.get("text") or ""
    return ""


def num(item, col_id):
    txt = col(item, col_id)
    if not txt:
        return 0.0
    try:
        return float(str(txt).replace(",", "."))
    except ValueError:
        return 0.0


def papel_short(v):
    if "Muito relevante" in v or v.startswith("Muito"):
        return "Muito relevante"
    if v == "Relevante":
        return "Relevante"
    if "Pouco" in v:
        return "Pouco relevante"
    return "Irrelevante"


def result_short(v):
    v = v.strip()
    if v.startswith("Muito maior"):
        return "Muito maior que o esperado"
    if v.startswith("Maior"):
        return "Maior que o esperado"
    if v.startswith("Igual"):
        return "Igual ao esperado"
    if v.startswith("Abaixo"):
        return "Abaixo do esperado"
    if v.startswith("Muito abaixo"):
        return "Muito abaixo do esperado"
    return v


def date_short(v):
    """'2026-06-28' → '28/06'"""
    if not v:
        return "—"
    try:
        d = datetime.strptime(v[:10], "%Y-%m-%d")
        return d.strftime("%d/%m")
    except Exception:
        return v


# ── HTML BUILDER ──────────────────────────────────────────────────────────────
def fmt_m(n):
    """Format number as compact USD string."""
    if n >= 1_000_000:
        return f"USD {n/1_000_000:,.1f}M"
    if n >= 1_000:
        return f"USD {int(n/1_000):,}K"
    return f"USD {int(n):,}"


def build_html(items_raw):
    # ── Parse items ──────────────────────────────────────────────────────────
    items = []
    for it in items_raw:
        emp = col(it, COL_EMPRESA) or it["name"]
        if not emp:
            continue
        items.append({
            "e":     emp,
            "r":     col(it, COL_RESP),
            "f":     col(it, COL_FUNCAO),
            "c":     int(num(it, COL_CONTATOS)),
            "n":     int(num(it, COL_NOVOS)),
            "ev":    num(it, COL_EV),
            "m12":   num(it, COL_12M),
            "papel": papel_short(col(it, COL_PAPEL)),
            "res":   result_short(col(it, COL_RESULT)),
            "inf":   col(it, COL_INFRA),
            "atd":   col(it, COL_ATD),
            "org":   col(it, COL_ORG),
            "neg":   col(it, COL_NEGOCIO),
            "estr":  col(it, COL_ESTRATEGIA),
            "case":  col(it, COL_CASE),
            "types": col(it, COL_CONTTYPE),
            "dt":    date_short(col(it, COL_DATE)),
            "sat":   col(it, COL_SAT) or "",
            "apex":  col(it, COL_APEX) or "",
            "cq":    col(it, COL_CITEQUAIS) or "",
        })

    N         = len(items)
    total_c   = sum(d["c"] for d in items)
    total_n   = sum(d["n"] for d in items)
    total_ev  = sum(d["ev"] for d in items)
    total_12m = sum(d["m12"] for d in items)
    pct_new   = round(total_n / total_c * 100) if total_c else 0

    # ── Chart: Papel BSCA ────────────────────────────────────────────────────
    papel_cnt = Counter(d["papel"] for d in items)
    papel_data   = [papel_cnt.get("Muito relevante",0), papel_cnt.get("Relevante",0), papel_cnt.get("Pouco relevante",0), papel_cnt.get("Irrelevante",0)]

    # ── Chart: Resultados ────────────────────────────────────────────────────
    res_map = {
        "Muito maior que o esperado": 0,
        "Maior que o esperado":       1,
        "Igual ao esperado":          2,
        "Abaixo do esperado":         3,
        "Muito abaixo do esperado":   4,
    }
    res_cnt  = Counter(d["res"] for d in items)
    res_data = [res_cnt.get(k,0) for k in res_map.keys()]

    # ── Satisfaction bars ────────────────────────────────────────────────────
    sat_levels = ["Muito Satisfeito", "Satisfeito", "Indiferente", "Insatisfeito", "Muito Insatisfeito"]
    def sat_counts(field):
        cnt = Counter(d[field] for d in items)
        return {lvl: cnt.get(lvl, 0) for lvl in sat_levels}

    sat_infra = sat_counts("inf")
    sat_atd   = sat_counts("atd")
    sat_org   = sat_counts("org")
    sat_neg   = sat_counts("neg")

    # ── Chart: Tipos de contato ──────────────────────────────────────────────
    type_labels = ["Compradores Diretos","Distribuidores","Comerciais Exportadoras","Atacadistas","Outros"]
    type_cnt    = Counter()
    for d in items:
        for t in d["types"].split(", "):
            t = t.strip()
            if t in type_labels:
                type_cnt[t] += 1
    type_data = [type_cnt.get(l, 0) for l in type_labels]

    # ── Word cloud: "Cite quais:" ────────────────────────────────────────────
    import re as _re
    _stopwords = {"de","a","o","e","que","em","do","da","os","as","um","uma",
                  "para","com","por","no","na","se","é","ao","das","dos","mais",
                  "mas","não","foi","são","pelo","pela","isso","esta","esse",
                  "este","sua","seu","suas","seus","tem","nos","nas","ter","ou",
                  "até","já","como","quando","após","entre","sobre","the","and"}
    _wfreq = Counter()
    for d in items:
        cq = d["cq"].strip()
        if cq:
            for w in _re.split(r'[\s,;./\-\n]+', cq.lower()):
                w = w.strip('.,;:!?"\'()')
                if len(w) > 2 and w not in _stopwords:
                    _wfreq[w] += 1
    wc_data = [[w, max(cnt * 12, 14)] for w, cnt in _wfreq.most_common(50)]

    # ── Qualitative text cards ───────────────────────────────────────────────
    def esc(s):
        return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;").replace('"',"&quot;")

    sat_cards_html = ""
    for d in items:
        txt = d["sat"].strip()
        if txt and txt not in (".", "-", ""):
            sat_cards_html += f"""
        <div class="qual-card">
          <div class="qual-company">{esc(d['e'])}</div>
          <div class="qual-text">{esc(txt)}</div>
        </div>"""

    apex_cards_html = ""
    for d in items:
        txt = d["apex"].strip()
        if txt and txt not in (".", "-", ""):
            apex_cards_html += f"""
        <div class="qual-card apex-card">
          <div class="qual-company">{esc(d['e'])}</div>
          <div class="qual-text">{esc(txt)}</div>
        </div>"""

    # ── Mini donuts ──────────────────────────────────────────────────────────
    estr_sim = sum(1 for d in items if "Sim" in d["estr"])
    estr_nao = N - estr_sim
    case_sim  = sum(1 for d in items if "Sim" in d["case"])
    case_nao  = N - case_sim

    # ── Timestamp ────────────────────────────────────────────────────────────
    brt = timezone(timedelta(hours=-3))
    now = datetime.now(brt)
    timestamp = now.strftime("%d/%m/%Y, %H:%M")

    # ── Table rows ───────────────────────────────────────────────────────────
    def b_papel(v):
        cls = {"Muito relevante":"b-green","Relevante":"b-blue","Pouco relevante":"b-gold"}.get(v,"b-gray")
        return f'<span class="badge {cls}">{v}</span>'

    def b_res(v):
        if "Muito maior" in v: cls="b-green"
        elif "Maior" in v:"    cls="b-blue"
        elif "Igual" in v:     cls="b-gold"
        elif "Abaixo" in v:    cls="b-red"
        else:                  cls="b-gray"
        return f'<span class="badge {cls}">{v}</span>'

    def b_sat(v):
        cls = {"Muito Satisfeito":"b-green","Satisfeito":"b-blue","Indiferente":"b-gold"}.get(v,"b-red")
        return f'<span class="badge {cls}">{v}</span>'

    rows = ""
    for d in items:
        rows += f"""
        <tr>
          <td><strong>{d['e']}</strong><div class="company-sub">{d['r']} · {d['f']}</div></td>
          <td class="num">{d['c']}</td>
          <td class="num">{d['n']}</td>
          <td>{b_papel(d['papel'])}</td>
          <td>{b_res(d['res'])}</td>
          <td>{b_sat(d['inf'])}</td>
          <td>{b_sat(d['atd'])}</td>
          <td>{b_sat(d['org'])}</td>
          <td style="color:var(--text-muted);white-space:nowrap">{d['dt']}/26</td>
        </tr>"""

    # ── Sat bar HTML ─────────────────────────────────────────────────────────
    def sat_bar(label, sc):
        ms, s, i, ins = sc["Muito Satisfeito"], sc["Satisfeito"], sc["Indiferente"], sc.get("Insatisfeito",0)+sc.get("Muito Insatisfeito",0)
        p = lambda v: f"{v/N*100:.0f}"
        pct = f"{(ms+s)/N*100:.0f}"
        segs = ""
        if ms:  segs += f'<div class="sat-seg" style="width:{p(ms)}%;background:#2D5E42">{ms}</div>'
        if s:   segs += f'<div class="sat-seg" style="width:{p(s)}%;background:#4A8C64">{s}</div>'
        if i:   segs += f'<div class="sat-seg" style="width:{p(i)}%;background:#C9A84C">{i}</div>'
        if ins: segs += f'<div class="sat-seg" style="width:{p(ins)}%;background:#C0614A">{ins}</div>'
        return f"""
        <div class="sat-row">
          <div class="sat-label">{label}</div>
          <div class="sat-track">{segs}</div>
          <div class="sat-pct">{pct}%</div>
        </div>"""

    sat_html = (
        sat_bar("Infraestrutura do evento", sat_infra) +
        sat_bar("Atendimento BSCA",         sat_atd)   +
        sat_bar("Organização do evento",     sat_org)   +
        sat_bar("Ambiente de negócios",      sat_neg)
    )

    # ── Assemble HTML ─────────────────────────────────────────────────────────
    ev_fmt  = fmt_m(total_ev)
    m12_fmt = fmt_m(total_12m)

    return f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8" />
<meta name="viewport" content="width=device-width, initial-scale=1.0" />
<title>Relatório de Avaliação – Missão Comercial Europa 2026 | BSCA</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/wordcloud2.js/1.2.2/wordcloud2.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet" />
<style>
:root {{
  --green:       #1E3D2F;
  --green-mid:   #2D5E42;
  --green-light: #4A8C64;
  --brown:       #7D5A35;
  --brown-light: #B8895A;
  --gold:        #C9A84C;
  --cream:       #F6F1E9;
  --cream-2:     #EDE6D8;
  --white:       #FFFFFF;
  --text:        #1A1A1A;
  --text-2:      #4A4A4A;
  --text-muted:  #7A7A7A;
  --border:      #DDD5C5;
  --shadow:      0 1px 4px rgba(0,0,0,.06), 0 4px 16px rgba(0,0,0,.07);
  --shadow-sm:   0 1px 3px rgba(0,0,0,.07);
  --radius:      12px;
}}
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ scroll-behavior: smooth; }}
body {{
  font-family: 'Inter', system-ui, sans-serif;
  background: var(--cream);
  color: var(--text);
  min-height: 100vh;
  font-size: 14px;
  line-height: 1.5;
}}
img {{ max-width: 100%; display: block; }}
.site-header {{
  background: var(--green);
  padding: 0 32px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 64px;
  position: sticky;
  top: 0;
  z-index: 100;
  box-shadow: 0 2px 12px rgba(0,0,0,.18);
}}
.site-header img.logo {{ height: 36px; width: auto; }}
.header-right {{ display: flex; align-items: center; gap: 12px; }}
.header-date {{ font-size: 12px; color: rgba(255,255,255,.6); }}
.header-badge {{
  background: var(--gold); color: var(--green);
  font-size: 11px; font-weight: 700; letter-spacing: .4px;
  padding: 4px 12px; border-radius: 20px; text-transform: uppercase;
}}
.hero {{
  background: linear-gradient(135deg, var(--green) 0%, var(--green-mid) 55%, #3A7557 100%);
  padding: 48px 32px 52px; color: white; position: relative; overflow: hidden;
}}
.hero::before {{
  content: '';
  position: absolute; inset: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.03'%3E%3Ccircle cx='30' cy='30' r='28'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E") repeat;
  pointer-events: none;
}}
.hero-inner {{ max-width: 1200px; margin: 0 auto; position: relative; }}
.hero-eyebrow {{
  font-size: 11px; font-weight: 600; letter-spacing: 2px; text-transform: uppercase;
  color: var(--gold); margin-bottom: 12px; display: flex; align-items: center; gap: 8px;
}}
.hero-eyebrow::before {{ content: ''; display: block; width: 24px; height: 2px; background: var(--gold); }}
.hero h1 {{
  font-size: clamp(22px, 4vw, 34px); font-weight: 800;
  line-height: 1.15; margin-bottom: 10px; letter-spacing: -.3px;
}}
.hero h1 span {{ color: var(--gold); }}
.hero p {{ font-size: 14px; color: rgba(255,255,255,.7); max-width: 520px; line-height: 1.6; }}
main {{ max-width: 1200px; margin: 0 auto; padding: 36px 24px 48px; }}
.section-label {{
  font-size: 10px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase;
  color: var(--brown); display: flex; align-items: center; gap: 8px; margin-bottom: 16px;
}}
.section-label::after {{ content: ''; flex: 1; height: 1px; background: var(--border); }}
.kpi-grid {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 14px; margin-bottom: 36px; }}
.kpi-card {{
  background: var(--white); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 22px 18px 18px;
  position: relative; overflow: hidden; box-shadow: var(--shadow-sm);
  transition: transform .2s, box-shadow .2s;
}}
.kpi-card:hover {{ transform: translateY(-2px); box-shadow: var(--shadow); }}
.kpi-card::after {{
  content: ''; position: absolute; bottom: 0; left: 0; right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--green), var(--green-light));
  border-radius: 0 0 var(--radius) var(--radius);
}}
.kpi-card:nth-child(4)::after, .kpi-card:nth-child(5)::after {{
  background: linear-gradient(90deg, var(--brown), var(--gold));
}}
.kpi-icon {{ font-size: 20px; margin-bottom: 12px; display: block; }}
.kpi-label {{ font-size: 11px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; letter-spacing: .6px; margin-bottom: 8px; }}
.kpi-value {{ font-size: 30px; font-weight: 800; color: var(--green); line-height: 1; letter-spacing: -.5px; }}
.kpi-value.brown {{ color: var(--brown); font-size: 24px; }}
.kpi-sub {{ font-size: 11px; color: var(--text-muted); margin-top: 6px; }}
.card {{
  background: var(--white); border: 1px solid var(--border);
  border-radius: var(--radius); padding: 24px 22px; box-shadow: var(--shadow-sm);
}}
.card-title {{
  font-size: 12px; font-weight: 700; text-transform: uppercase;
  letter-spacing: .8px; color: var(--text-2); margin-bottom: 20px;
  padding-bottom: 12px; border-bottom: 1px solid var(--cream-2);
}}
.chart-row {{ display: grid; gap: 14px; margin-bottom: 14px; }}
.cols-2  {{ grid-template-columns: 1fr 1fr; }}
.cols-3  {{ grid-template-columns: 1fr 1fr 1fr; }}
.cols-21 {{ grid-template-columns: 2fr 1fr; }}
.cols-1  {{ grid-template-columns: 1fr; }}
.sat-row {{ display: flex; align-items: center; gap: 14px; margin-bottom: 16px; }}
.sat-row:last-child {{ margin-bottom: 0; }}
.sat-label {{ font-size: 12px; color: var(--text-2); width: 200px; flex-shrink: 0; font-weight: 500; }}
.sat-track {{
  flex: 1; height: 24px; background: var(--cream); border-radius: 6px;
  overflow: hidden; display: flex; border: 1px solid var(--border);
}}
.sat-seg {{
  height: 100%; display: flex; align-items: center; justify-content: center;
  font-size: 10px; font-weight: 700; color: white;
  transition: width .5s cubic-bezier(.4,0,.2,1);
}}
.sat-pct {{ width: 42px; text-align: right; font-size: 12px; font-weight: 700; color: var(--green); flex-shrink: 0; }}
.sat-legend {{
  display: flex; gap: 16px; flex-wrap: wrap;
  margin-top: 18px; padding-top: 14px; border-top: 1px solid var(--cream-2);
}}
.sat-legend-item {{ display: flex; align-items: center; gap: 6px; font-size: 11px; color: var(--text-muted); }}
.sat-legend-dot {{ width: 10px; height: 10px; border-radius: 3px; flex-shrink: 0; }}
.mini-pair {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; height: 100%; }}
.mini-item {{
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 12px; padding: 12px;
  background: var(--cream); border-radius: 10px;
}}
.mini-item canvas {{ width: 90px !important; height: 90px !important; }}
.mini-item p {{ font-size: 11px; color: var(--text-muted); text-align: center; line-height: 1.4; font-weight: 500; }}
.badge {{ display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 600; white-space: nowrap; line-height: 1.4; }}
.b-green  {{ background: #D4EDDA; color: #1E6B35; }}
.b-blue   {{ background: #D1E8F5; color: #1A5E8A; }}
.b-gold   {{ background: #FEF3CD; color: #7D5A00; }}
.b-red    {{ background: #FDDEDE; color: #8A1A1A; }}
.b-gray   {{ background: #F0EDE8; color: #5A5048; }}
.table-scroll {{ overflow-x: auto; border-radius: 8px; }}
table {{ width: 100%; border-collapse: collapse; font-size: 12.5px; min-width: 780px; }}
thead th {{
  background: var(--green); color: rgba(255,255,255,.85);
  font-weight: 600; font-size: 10px; text-transform: uppercase;
  letter-spacing: .7px; padding: 11px 14px; text-align: left; white-space: nowrap;
}}
thead th:first-child {{ border-radius: 8px 0 0 0; }}
thead th:last-child  {{ border-radius: 0 8px 0 0; }}
tbody tr {{ border-bottom: 1px solid var(--cream-2); transition: background .15s; }}
tbody tr:hover {{ background: var(--cream); }}
tbody td {{ padding: 11px 14px; color: var(--text-2); vertical-align: middle; }}
tbody td strong {{ color: var(--text); font-weight: 600; }}
td.num {{ text-align: right; font-variant-numeric: tabular-nums; font-weight: 600; color: var(--green); }}
.company-sub {{ font-size: 11px; color: var(--text-muted); margin-top: 1px; }}
.site-footer {{
  background: var(--white); border-top: 1px solid var(--border);
  text-align: center; padding: 28px 32px; margin-top: 24px;
}}
.site-footer img.logos-bar {{ max-width: 960px; width: 100%; height: auto; margin: 0 auto; }}
.site-footer p {{ font-size: 11px; color: var(--text-muted); margin-top: 14px; }}
@media (max-width: 1100px) {{
  .kpi-grid {{ grid-template-columns: repeat(3, 1fr); }}
  .cols-3   {{ grid-template-columns: 1fr 1fr; }}
}}
@media (max-width: 820px) {{
  .site-header {{ padding: 0 20px; }}
  .hero {{ padding: 36px 20px 40px; }}
  main {{ padding: 24px 16px 40px; }}
  .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
  .cols-2, .cols-21 {{ grid-template-columns: 1fr; }}
  .cols-3 {{ grid-template-columns: 1fr; }}
  .sat-label {{ width: 130px; font-size: 11px; }}
  .header-date {{ display: none; }}
}}
@media (max-width: 540px) {{
  .kpi-grid {{ grid-template-columns: 1fr 1fr; }}
  .kpi-value {{ font-size: 24px; }}
  .hero h1 {{ font-size: 20px; }}
}}
/* ── Word cloud ─────────────────────────────────────────── */
#wordCloudCanvas {{ width:100%!important; height:220px!important; }}
/* ── Qualitative cards ──────────────────────────────────── */
.qual-grid {{
  display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 14px; margin-top: 4px;
}}
.qual-card {{
  background: var(--cream); border-radius: 10px; padding: 14px 16px;
  border-left: 4px solid var(--green);
}}
.apex-card {{ border-left-color: var(--gold); }}
.qual-company {{
  font-size: 11px; font-weight: 700; color: var(--green); text-transform: uppercase;
  letter-spacing: .5px; margin-bottom: 6px;
}}
.apex-card .qual-company {{ color: var(--brown); }}
.qual-text {{
  font-size: 12.5px; color: var(--text-2); line-height: 1.55; white-space: pre-wrap;
}}
</style>
</head>
<body>

<header class="site-header">
  <img class="logo"
       src="https://www.bsca.com.br/wp-content/uploads/2025/09/Logo_BSCA-white.png"
       alt="BSCA"
       onerror="this.style.display='none';this.nextElementSibling.style.display='block'">
  <span style="display:none;color:white;font-weight:800;font-size:16px;letter-spacing:1px">BSCA</span>
  <div class="header-right">
    <span class="header-date">Atualizado em {timestamp}</span>
    <span class="header-badge">{N} Respostas</span>
  </div>
</header>

<section class="hero">
  <div class="hero-inner">
    <div class="hero-eyebrow">Brazil. The Coffee Nation</div>
    <h1>Relatório de Avaliação<br><span>Missão Comercial Europa 2026</span></h1>
    <p>Resultados consolidados das avaliações recebidas das empresas participantes da Missão Comercial Europa 2026.</p>
  </div>
</section>

<main>

  <div class="section-label">Indicadores principais</div>
  <div class="kpi-grid">
    <div class="kpi-card">
      <span class="kpi-icon">🏢</span>
      <div class="kpi-label">Empresas respondentes</div>
      <div class="kpi-value">{N}</div>
      <div class="kpi-sub">formulários recebidos</div>
    </div>
    <div class="kpi-card">
      <span class="kpi-icon">🤝</span>
      <div class="kpi-label">Contatos realizados</div>
      <div class="kpi-value">{total_c:,}</div>
      <div class="kpi-sub">total no evento</div>
    </div>
    <div class="kpi-card">
      <span class="kpi-icon">✨</span>
      <div class="kpi-label">Novos contatos</div>
      <div class="kpi-value">{total_n:,}</div>
      <div class="kpi-sub">{pct_new}% do total</div>
    </div>
    <div class="kpi-card">
      <span class="kpi-icon">💰</span>
      <div class="kpi-label">Negócios no evento</div>
      <div class="kpi-value brown">{ev_fmt}</div>
      <div class="kpi-sub">em USD · estimativa declarada</div>
    </div>
    <div class="kpi-card">
      <span class="kpi-icon">📈</span>
      <div class="kpi-label">Projeção 12 meses</div>
      <div class="kpi-value brown">{m12_fmt}</div>
      <div class="kpi-sub">em USD · estimativa declarada</div>
    </div>
  </div>

  <div class="section-label">Percepção de resultados</div>
  <div class="chart-row cols-2" style="margin-bottom:14px">
    <div class="card">
      <div class="card-title">Papel do Brazil The Coffee Nation</div>
      <div style="height:220px;position:relative"><canvas id="chartRole"></canvas></div>
    </div>
    <div class="card">
      <div class="card-title">Resultado vs. expectativa pré-evento</div>
      <div style="height:220px;position:relative"><canvas id="chartExpect"></canvas></div>
    </div>
  </div>

  <div class="section-label">Satisfação por categoria</div>
  <div class="chart-row cols-1" style="margin-bottom:14px">
    <div class="card">
      <div class="card-title">Avaliação de satisfação — todas as categorias</div>
      {sat_html}
      <div class="sat-legend">
        <div class="sat-legend-item"><div class="sat-legend-dot" style="background:#2D5E42"></div>Muito Satisfeito</div>
        <div class="sat-legend-item"><div class="sat-legend-dot" style="background:#4A8C64"></div>Satisfeito</div>
        <div class="sat-legend-item"><div class="sat-legend-dot" style="background:#C9A84C"></div>Indiferente</div>
        <div class="sat-legend-item"><div class="sat-legend-dot" style="background:#C0614A"></div>Insatisfeito</div>
      </div>
    </div>
  </div>

  <div class="section-label">Contatos e indicadores adicionais</div>
  <div class="chart-row cols-21" style="margin-bottom:14px">
    <div class="card">
      <div class="card-title">Tipos de contatos realizados</div>
      <div style="height:200px;position:relative"><canvas id="chartContacts"></canvas></div>
      <div style="margin-top:16px">
        <div class="card-title" style="margin-bottom:8px">Outros tipos citados — nuvem de palavras</div>
        <canvas id="wordCloudCanvas" height="220"></canvas>
      </div>
    </div>
    <div class="card">
      <div class="card-title">Indicadores qualitativos</div>
      <div class="mini-pair">
        <div class="mini-item">
          <canvas id="chartStrategy" width="90" height="90"></canvas>
          <p>Necessidade de<br>mudar estratégia</p>
        </div>
        <div class="mini-item">
          <canvas id="chartCase" width="90" height="90"></canvas>
          <p>Disponíveis para<br>estudo de caso</p>
        </div>
      </div>
    </div>
  </div>

  <div class="section-label">Vozes das empresas</div>
  <div class="card" style="margin-bottom:14px">
    <div class="card-title">Principais motivos de satisfação e insatisfação</div>
    <div class="qual-grid">{sat_cards_html}</div>
  </div>
  <div class="card" style="margin-bottom:36px">
    <div class="card-title">Ações Apex-Brasil sugeridas pelas empresas</div>
    <div class="qual-grid">{apex_cards_html}</div>
  </div>

  <div class="section-label">Empresas participantes</div>
  <div class="card">
    <div class="card-title">Detalhamento por empresa</div>
    <div class="table-scroll">
      <table>
        <thead>
          <tr>
            <th>Empresa / Responsável</th>
            <th class="num">Contatos</th>
            <th class="num">Novos</th>
            <th>Papel BSCA</th>
            <th>Resultado</th>
            <th>Infraestrutura</th>
            <th>Atendimento</th>
            <th>Organização</th>
            <th>Data</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </div>
  </div>

</main>

<footer class="site-footer">
  <img class="logos-bar"
       src="https://www.bsca.com.br/wp-content/uploads/2026/03/logos-realizacao-promovidos-desktop-2048x193.png"
       alt="Realização: BSCA e ApexBrasil">
  <p>BSCA – Associação Brasileira de Cafés Especiais &nbsp;·&nbsp; Projeto Brazil. The Coffee Nation &nbsp;·&nbsp; Missão Comercial Europa 2026</p>
</footer>

<script>
Chart.defaults.font.family = "'Inter', system-ui, sans-serif";
Chart.defaults.font.size   = 12;
Chart.defaults.color:       = '#7A7A7A';
Chart.defaults.plugins.legend.labels.boxWidth = 12;
Chart.defaults.plugins.legend.labels.padding  = 14;

const C = {{ green:'#2D5E42', greenL:'#4A8C64', gold:'#C9A84C', brown:'#7D5A35', red:'#C0614A', blue:'#4A7FA5' }};
const N = {N};

new Chart(document.getElementById('chartRole'), {{
  type: 'doughnut',
  data: {{
    labels:   ['Muito relevante','Relevante','Pouco relevante','Irrelevante'],
    datasets: [{{ data:{papel_data}, backgroundColor:[C.green,C.blue,C.gold,C.red], borderWidth:3, borderColor:'#fff', hoverOffset:6 }}]
  }},
  options: {{
    responsive:true, maintainAspectRatio:false, cutout:'62%',
    plugins: {{
      legend:  {{ position:'right' }},
      tooltip: {{ callbacks:{{ label: ctx=>`  ${{ctx.label}}: ${{ctx.raw}} (${{Math.round(ctx.raw/N*100)}}%)` }} }}
    }}
  }}
}});
new Chart(document.getElementById('chartExpect'), {{
  type: 'doughnut',
  data: {{
    labels:   ['Muito maior','Maior','Igual','Abaixo','Muito abaixo'],
    datasets: [{{ data:{res_data}, backgroundColor:[C.green,C.blue,C.gold,C.red,'#888'], borderWidth:3, borderColor:'#fff', hoverOffset:6 }}]
  }},
  options: {{
  2 responsive:true, maintainAspectRatio:false, cutout:'62%',
    plugins: {{
      legend:  {{ position:'right' }},
      tooltip: {{ callbacks:{{ label: ctx=>`  ${{ctx.label}}: ${{ctx.raw}} (${{Math.round(ctx.raw/N*100)}}%)` }} }}
    }}
  }}
}});

new Chart(document.getElementById('chartContacts'), {{
  type: 'bar',
  data: {{
    labels: {json.dumps(type_labels)},
    datasets: [{{
      data: {type_data},
      backgroundColor: [C.green,C.greenL,C.brown,C.gold,'#ddd'],
      borderRadius: 6, borderSkipped: false,
    }}]
  }},
  options: {{
    responsive:true, maintainAspectRatio:false, indexAxis:'y',
    plugins:{{ legend:{{ display:false }} }},
    scales:{{
      x:{{ grid:{{ color:'#EDE6D8' }}, ticks:{{ stepSize:2 }} }},
      y:{{ grid:{{ display:false }} }}
    }}
  }}
}});

const mini = (id, data, colors, labels) => new Chart(document.getElementById(id),{{
  type:'doughnut',
  data:{{ labels, datasets:[{{ data, backgroundColor:colors, borderWidth:2, borderColor:'#EDE6D8', hoverOffset:4 }}]}},
  options:{{
    responsive:false, maintainAspectRatio:false, cutout:'58%',
    plugins:{{
      legend:{{ display:false }},
      tooltip:{{ callbacks:{{ label: ctx=>`  ${{ctx.label}}: ${{ctx.raw}}` }} }}
    }}
  }}
}});
mini('chartStrategy', [{estr_sim},{estr_nao}], [C.red, C.green],  ['Sim','Não']);
mini('chartCase',     [{case_sim},{case_nao}], [C.green, C.gold],  ['Sim','Não']);

// ── Word cloud ─────────────────────────────────────────────────────────────
const wcData = {json.dumps(wc_data, ensure_ascii=False)};
if (wcData.length > 0 && typeof WordCloud !== 'undefined') {{
  const wcCanvas = document.getElementById('wordCloudCanvas');
  wcCanvas.width  = wcCanvas.parentElement.offsetWidth || 500;
  wcCanvas.height = 220;
  WordCloud(wcCanvas, {{
    list: wcData,
    gridSize: 6,
    weightFactor: 1.4,
    fontFamily: "'Inter', sans-serif",
    color: (word, weight) => {{
      const palette = ['#1E3D2F','#2D5E42','#4A8C64','#C9A84C','#7D5A35','#4A7FA5'];
      return palette[Math.floor(Math.random() * palette.length)];
    }},
    rotateRatio: 0.3,
    rotationSteps: 2,
    backgroundColor: '#F8F4EE',
    drawOutOfBound: false,
    shrinkToFit: true,
  }});
}} else if (wcData.length === 0) {{
  const el = document.getElementById('wordCloudCanvas');
  el.style.display = 'none';
  el.insertAdjacentHTML('afterend','<p style="font-size:12px;color:#aaa;padding:8px 0">Nenhuma resposta registrada.</p>');
}}
</script>
</body>
</html>"""


# ── PUSH TO GITHUB ────────────────────────────────────────────────────────────
def push_to_github(html_content):
    GH_TOKEN = os.environ.get("GITHUB_TOKEN", "")
    GH_REPO  = os.environ.get("GITHUB_REPOSITORY", "renanfreitas-sketch/missaoeuropa2026")
    BRANCH   = os.environ.get("GITHUB_REF_NAME", "main")
    FILE_PATH = "index.html"

    # Get current SHA
    req_get = urllib.request.Request(
        f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_PATH}",
        headers={
            "Authorization": f"Bearer {GH_TOKEN}",
            "Accept":        "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    )
    sha = None
    try:
        with urllib.request.urlopen(req_get) as resp:
            sha = json.loads(resp.read()).get("sha")
    except Exception:
        pass  # file doesn't exist yet

    brt = timezone(timedelta(hours=-3))
    now = datetime.now(brt).strftime("%d/%m/%Y %H:%M BRT")

    payload = {
        "message": f"missaoeuropa: auto-update {now}",
        "content": base64.b64encode(html_content.encode()).decode(),
        "branch":  BRANCH,
    }
    if sha:
        payload["sha"] = sha

    req_put = urllib.request.Request(
        f"https://api.github.com/repos/{GH_REPO}/contents/{FILE_PATH}",
        data=json.dumps(payload).encode(),
        method="PUT",
        headers={
            "Authorization":        f"Bearer {GH_TOKEN}",
            "Accept":               "application/vnd.github+json",
            "Content-Type":         "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
    )
    with urllib.request.urlopen(req_put) as resp:
        result = json.loads(resp.read())
        print(f"Pushed: {result.get('content', {}).get('html_url', 'OK')}")  # type: ignore


# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if not MONDAY_TOKEN:
        print("ERROR: MONDAY_API_TOKEN not set", file=sys.stderr)
        sys.exit(1)

    print("Fetching monday.com data (Missão Comercial Europa 2026)…")
    raw = fetch_items()
    print(f"  {len(raw)} items fetched")

    print("Building HTML…")
    html = build_html(raw)

    if "--dry-run" in sys.argv:
        with open("missaoeuropa2026.html", "w", encoding="utf-8") as f:
            f.write(html)
        print("Saved to missaoeuropa2026.html (dry run)")
    else:
        push_to_github(html)
        print("Done.")
