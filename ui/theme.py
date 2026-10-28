"""Tema visual: palet navy-slate (terinspirasi referensi GE Aerospace), hero, dan komponen CSS."""
import urllib.parse

import streamlit as st

# Siluet ikan + pita arus air (SVG) dipakai sebagai latar hero.
_HERO_SVG = """<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 1200 520' preserveAspectRatio='xMaxYMid slice'>
<defs>
<linearGradient id='b' x1='0' y1='0' x2='1' y2='0'><stop offset='0' stop-color='#F4F8FF' stop-opacity='0'/><stop offset='.5' stop-color='#DCE7F5' stop-opacity='.9'/><stop offset='1' stop-color='#9FB3CC' stop-opacity='.15'/></linearGradient>
<linearGradient id='f' x1='0' y1='0' x2='1' y2='1'><stop offset='0' stop-color='#1B2D47'/><stop offset='1' stop-color='#070F20'/></linearGradient>
</defs>
<path d='M470 232 C560 118 800 96 960 214 C1010 250 1050 236 1100 178 L1112 330 C1056 282 1010 282 962 308 C800 420 560 402 470 232 Z' fill='url(#f)' stroke='#9FB3CC' stroke-opacity='.45' stroke-width='2'/>
<path d='M720 120 C760 62 830 56 880 124' fill='#10203A' stroke='#9FB3CC' stroke-opacity='.4' stroke-width='2'/>
<path d='M700 372 C730 420 790 432 830 384' fill='#10203A' stroke='#9FB3CC' stroke-opacity='.4' stroke-width='2'/>
<path d='M590 188 C610 230 610 270 592 316' fill='none' stroke='#9FB3CC' stroke-opacity='.5' stroke-width='3'/>
<circle cx='528' cy='226' r='9' fill='#E8EEF6'/><circle cx='526' cy='225' r='4' fill='#070F20'/>
<path d='M0 470 C260 360 520 520 820 390 S1100 300 1200 340' fill='none' stroke='url(#b)' stroke-width='26' stroke-linecap='round'/>
<path d='M120 520 C360 430 600 560 900 440 S1120 380 1200 410' fill='none' stroke='url(#b)' stroke-width='12' stroke-linecap='round'/>
<path d='M260 120 C500 40 700 150 1000 70 S1150 60 1200 90' fill='none' stroke='url(#b)' stroke-width='8' stroke-linecap='round' opacity='.7'/>
<g fill='none' stroke='#DCE7F5' stroke-opacity='.55'><circle cx='420' cy='150' r='7'/><circle cx='390' cy='110' r='4'/><circle cx='448' cy='88' r='5'/><circle cx='1130' cy='120' r='6'/></g>
</svg>"""
_HERO_URI = "data:image/svg+xml;utf8," + urllib.parse.quote(_HERO_SVG)

_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600&family=Outfit:wght@300;400;500&display=swap');
:root{--n950:#070F20;--n900:#0A1730;--n800:#13264A;--s800:#1B2D47;--s700:#2A4060;--steel:#9FB3CC;--ice:#E8EEF6;--acc:#7FB4E8;--ok:#7FD1B9;--warn:#E8C26B;}
html,body,[class*="css"],.stApp{font-family:'Figtree','Segoe UI',system-ui,sans-serif;}
.stApp{background:radial-gradient(1200px 600px at 80% -10%,#16315C 0%,transparent 60%),linear-gradient(180deg,var(--n900),var(--n950));}
[data-testid="stHeader"]{background:transparent;}
.block-container{max-width:1180px;padding-top:1.2rem;padding-bottom:4rem;}
h1,h2,h3{font-family:'Outfit','Figtree',sans-serif;font-weight:400;letter-spacing:-.01em;color:var(--ice);}
h2{font-size:1.9rem;} h3{font-size:1.35rem;}
a{color:var(--acc)!important;text-decoration:none;} a:hover{text-decoration:underline;}

/* hero */
.hero{position:relative;border-radius:18px;overflow:hidden;min-height:370px;padding:56px 52px;margin-bottom:24px;
 background:linear-gradient(100deg,#0A1730 0%,#0A1730 38%,rgba(10,23,48,.2) 100%),url("__HERO__") right center/cover no-repeat,#0A1730;
 border:1px solid rgba(159,179,204,.18);}
.hero .brand{display:flex;align-items:center;gap:12px;color:var(--steel);font-size:.95rem;margin-bottom:34px;}
.hero .logo{width:38px;height:38px;border-radius:50%;border:2px solid var(--ice);display:grid;place-items:center;color:var(--ice);font-family:'Outfit';font-size:1.1rem;}
.hero h1{font-size:clamp(2.1rem,4.6vw,3.7rem);line-height:1.08;font-weight:300;max-width:620px;margin:0 0 18px;}
.hero p{max-width:540px;color:#C9D6E6;font-size:1.05rem;line-height:1.55;margin:0 0 6px;}
.strip{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:12px;margin:0 0 26px;}
.strip div{padding:16px 20px;color:var(--steel);font-size:.9rem;background:var(--s800);border:1px solid rgba(159,179,204,.18);border-radius:14px;}
.strip b{display:block;color:var(--ice);font-family:'Outfit';font-weight:400;font-size:1.5rem;}

/* tab = menu navigasi */
.stTabs [data-baseweb="tab-list"]{width:max-content;max-width:100%;gap:7px;background:rgba(19,38,74,.7);border-radius:18px;padding:7px;border:1px solid rgba(159,179,204,.18);}
.stTabs [data-baseweb="tab"],.stTabs [role="tab"]{height:44px;padding:0 18px;border:1px solid transparent;border-radius:14px!important;overflow:hidden;color:var(--steel);font-weight:500;background:transparent;white-space:nowrap;transition:background .18s,border-color .18s,color .18s,transform .18s;}
.stTabs [data-baseweb="tab"]:hover{background:rgba(127,180,232,.12);border-color:rgba(127,180,232,.2);color:var(--ice);}
.stTabs [aria-selected="true"]{border-radius:14px!important;overflow:hidden;background:linear-gradient(135deg,#315F91,#23466F)!important;border-color:rgba(127,180,232,.5)!important;color:#fff!important;box-shadow:0 4px 14px rgba(0,0,0,.2);}
.stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"]{display:none;}
.stTabs [data-testid="stTabsContent"]{padding-top:1rem;}

/* kartu */
[data-testid="stVerticalBlockBorderWrapper"]{border-radius:14px;}
div[data-testid="stVerticalBlockBorderWrapper"]:has(> div > div[data-testid="stVerticalBlock"] .kartu){background:rgba(27,45,71,.55);border:1px solid rgba(159,179,204,.2);}
[data-testid="stExpander"]{background:rgba(19,38,74,.55);border:1px solid rgba(159,179,204,.16);border-radius:12px;}
[data-testid="stExpander"] summary{font-weight:500;}
[data-testid="stMetric"]{background:rgba(27,45,71,.6);border:1px solid rgba(159,179,204,.16);padding:14px 18px;border-radius:12px;}
[data-testid="stMetricValue"]{font-family:'Outfit';font-weight:300;}

/* tombol: primer = pil putih seperti 'Learn more' */
.stButton>button,.stDownloadButton>button{border-radius:999px;padding:.5rem 1.4rem;font-weight:600;border:1px solid rgba(232,238,246,.5);background:transparent;color:var(--ice);}
.stButton>button[kind="primary"]{background:#fff;color:var(--n900);border-color:#fff;}
.stButton>button:hover,.stDownloadButton>button:hover{border-color:var(--acc);color:var(--acc);}
.stButton>button[kind="primary"]:hover{background:var(--acc);color:var(--n900);}
.stButton>button:focus-visible,.stDownloadButton>button:focus-visible{outline:2px solid var(--acc);outline-offset:2px;}
.stProgress>div>div>div>div{background:linear-gradient(90deg,#4E86C2,var(--acc));}

/* rujukan */
.ref{display:inline-block;margin:2px 6px 2px 0;padding:2px 10px;border-radius:999px;font-size:.78rem;border:1px solid rgba(159,179,204,.3);background:rgba(10,23,48,.6);}
.ref.dibaca{border-color:rgba(127,209,185,.6);} .ref.ditemukan{border-color:rgba(127,180,232,.6);} .ref.perlu_dicek{border-color:rgba(232,194,107,.7);}
.meta{color:var(--steel);font-size:.88rem;} .praktik{color:var(--warn);font-size:.78rem;margin-left:6px;}
.chip{display:inline-block;padding:3px 12px;border-radius:999px;background:var(--s700);color:var(--ice);font-size:.82rem;margin:0 6px 6px 0;}
.kartu{display:none;}
@media (max-width:900px){.strip{grid-template-columns:repeat(3,minmax(0,1fr));}}
@media (max-width:700px){.hero{padding:34px 24px;min-height:320px}.strip{grid-template-columns:repeat(2,minmax(0,1fr));margin-left:0;margin-right:0;}}
@media (max-width:700px){.stTabs [data-baseweb="tab-list"]{width:100%;overflow-x:auto}.stTabs [data-baseweb="tab"]{padding:0 13px;font-size:.9rem}}
@media (prefers-reduced-motion:reduce){.stTabs [data-baseweb="tab"]{transition:none}}
"""


def inject_css() -> None:
    """Pasang CSS global."""
    st.markdown(f"<style>{_CSS.replace('__HERO__', _HERO_URI)}</style>", unsafe_allow_html=True)


def hero(kb) -> None:
    """Banner utama + kartu statistik knowledge base."""
    n_ref = len(kb.references)
    st.markdown(
        f"""<div class="hero"><div class="brand"><span class="logo">SP</span>Sistem Pakar Kesehatan Ikan</div>
<h1>Kenali penyakit ikan sejak gejala pertama.</h1>
<p>Pilih gejala yang Anda lihat pada lele, nila, atau gurame. Sistem menalar dengan forward chaining dan Certainty Factor, lalu menjelaskan penanganannya lengkap dengan tautan sumber.</p></div>
<div class="strip"><div><b>{len(kb.diseases)}</b>penyakit</div><div><b>{len(kb.symptoms)}</b>gejala</div>
<div><b>{len(kb.rules)}</b>rule IF-THEN</div><div><b>{n_ref}</b>rujukan</div><div><b>3</b>jenis ikan</div></div>""",
        unsafe_allow_html=True)
