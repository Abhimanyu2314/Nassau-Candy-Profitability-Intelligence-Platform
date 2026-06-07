import io
import time
import html
import re
from pathlib import Path
from datetime import datetime

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from utils.data_loader import load_data
from utils.factory_mapping import attach_factory
from utils.metrics import (
    add_metrics,
    division_summary,
    factory_summary,
    monthly_margin,
    pareto_table,
    product_summary,
    region_summary,
)
from utils.report_generator import build_executive_pdf
from utils.risk_engine import add_portfolio_actions, classify_products, executive_recommendations

st.set_page_config(
    page_title="Nassau Profitability Intelligence",
    page_icon="🍬",
    layout="wide",
    initial_sidebar_state="expanded",
)

px.defaults.template = "plotly_dark"
px.defaults.color_discrete_sequence = ["#ff4f38", "#ec4899", "#8b5cf6", "#60a5fa", "#22d3ee", "#f59e0b"]

st.markdown(
    """
<style>
:root {
    --bg0: #090514;
    --bg1: #150827;
    --bg2: #22113b;
    --card: rgba(13, 14, 20, 0.82);
    --card2: rgba(28, 19, 38, 0.78);
    --stroke: rgba(236, 72, 153, 0.46);
    --stroke2: rgba(139, 92, 246, 0.38);
    --text: #f8f7ff;
    --muted: #b9aacb;
    --hot: #ff4f38;
    --pink: #ec4899;
    --violet: #7c3aed;
    --blue: #60a5fa;
}
html, body, [data-testid="stAppViewContainer"] {
    background:
        radial-gradient(circle at 68% 6%, rgba(236,72,153,.52), transparent 23%),
        radial-gradient(circle at 28% 30%, rgba(124,58,237,.36), transparent 28%),
        radial-gradient(circle at 85% 72%, rgba(30,64,175,.32), transparent 32%),
        linear-gradient(135deg, #070310 0%, #140822 42%, #0b0616 100%) !important;
    color: var(--text) !important;
}
html::before {
    content:"";
    position:fixed;
    inset:0;
    pointer-events:none;
    background-image: radial-gradient(rgba(255,255,255,.08) 1px, transparent 1px);
    background-size: 3px 3px;
    opacity:.18;
    z-index:0;
}
/* Anti-flash polish: keep Streamlit dark from the first paint and fade page content in after loader disappears */
html, body, #root, .stApp, [data-testid="stAppViewContainer"], [data-testid="stAppViewContainer"] > .main {
    background:#070310 !important;
}
.stApp {
    background:#070310 !important;
    animation:nassauPageFade .34s ease-out both;
}
[data-testid="stAppViewContainer"] > .main {
    background:#070310 !important;
}
@keyframes nassauPageFade {
    from {opacity:.72; filter:brightness(.86);}
    to {opacity:1; filter:brightness(1);}
}

.block-container {
    padding-top: 1.35rem;
    padding-bottom: 2rem;
    max-width: 1700px;
}
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(16,16,20,.98), rgba(9,7,14,.98)) !important;
    border-right: 1px solid rgba(236,72,153,.30);
    box-shadow: 16px 0 55px rgba(0,0,0,.45);
}
[data-testid="stSidebar"]::before {
    content:"";
    display:block;
    height:72px;
    margin: 10px 12px 18px 12px;
    border-radius: 20px;
    background: linear-gradient(135deg, rgba(236,72,153,.25), rgba(124,58,237,.16));
    border: 1px solid rgba(236,72,153,.38);
}
[data-testid="stSidebar"] * {color: #f8f7ff !important;}
[data-testid="stSidebar"] [role="radiogroup"] label {
    padding: 11px 13px;
    border-radius: 15px;
    margin: 6px 0;
    background: rgba(255,255,255,.025);
    border: 1px solid transparent;
    transition: all .18s ease;
}
[data-testid="stSidebar"] [role="radiogroup"] label:hover {
    background: rgba(236,72,153,.14);
    border: 1px solid rgba(236,72,153,.36);
    transform: translateX(4px);
}
[data-testid="stSidebar"] .stExpander {
    border: 1px solid rgba(236,72,153,.25) !important;
    border-radius: 16px !important;
    background: rgba(10,8,16,.36) !important;
}
.topbar {
    height: 78px;
    margin: 6px 0 24px 0;
    padding: 0 22px;
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:18px;
    border-radius: 22px;
    transform: skewX(-7deg);
    background: linear-gradient(100deg, rgba(34,25,54,.88), rgba(70,38,96,.62), rgba(13,14,20,.92));
    border: 1px solid rgba(255,255,255,.12);
    box-shadow: 0 24px 70px rgba(0,0,0,.48), inset 0 1px 0 rgba(255,255,255,.08);
}
.topbar > div {transform: skewX(7deg);} 
.top-date {font-weight:800; letter-spacing:.2px; color:#fff; white-space:nowrap;}
.search-pill {
    min-width: 360px;
    max-width: 560px;
    flex: 1;
    padding: 13px 20px;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,.65);
    color:#ddd0ea;
    background: rgba(20,14,31,.32);
}
/* Functional top search bar: this is the real Streamlit input, not a fake HTML field */
.functional-topbar {
    margin: 6px 0 24px 0;
    padding: 14px 18px;
    border-radius: 22px;
    background: linear-gradient(100deg, rgba(34,25,54,.88), rgba(70,38,96,.62), rgba(13,14,20,.92));
    border: 1px solid rgba(255,255,255,.12);
    box-shadow: 0 24px 70px rgba(0,0,0,.48), inset 0 1px 0 rgba(255,255,255,.08);
}
.functional-topbar [data-testid="stTextInput"] input {
    border-radius: 999px !important;
    border: 1px solid rgba(255,255,255,.60) !important;
    background: rgba(20,14,31,.45) !important;
    color: #fff !important;
    height: 46px;
}
.functional-topbar [data-testid="stTextInput"] input::placeholder {color:#d9c7e9 !important;}

/* Phase 48: Compact integrated enterprise dropdown search */
.functional-topbar div[data-testid="stSelectbox"]{
    width:100%!important;
    margin:0!important;
}
.functional-topbar div[data-testid="stSelectbox"] label{
    display:none!important;
}
.functional-topbar div[data-testid="stSelectbox"] div[data-baseweb="select"]{
    width:100%!important;
}
.functional-topbar div[data-testid="stSelectbox"] div[data-baseweb="select"] > div{
    min-height:52px!important;
    height:52px!important;
    border-radius:28px!important;
    background:linear-gradient(135deg, rgba(14,9,29,.94), rgba(22,12,39,.92))!important;
    border:1px solid rgba(236,72,153,.32)!important;
    box-shadow:0 8px 22px rgba(0,0,0,.30), 0 0 12px rgba(236,72,153,.14), inset 0 1px 0 rgba(255,255,255,.07)!important;
    transition:border-color .18s ease, box-shadow .18s ease, transform .18s ease!important;
    padding:0 12px!important;
}
.functional-topbar div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:hover,
.functional-topbar div[data-testid="stSelectbox"] div[data-baseweb="select"] > div:focus-within{
    transform:translateY(-1px)!important;
    border-color:rgba(236,72,153,.48)!important;
    box-shadow:0 10px 26px rgba(0,0,0,.34), 0 0 16px rgba(236,72,153,.22), inset 0 1px 0 rgba(255,255,255,.10)!important;
}
.functional-topbar div[data-testid="stSelectbox"] div[data-baseweb="select"] input{
    color:#fff!important;
    caret-color:#ff66c4!important;
}
.functional-topbar div[data-testid="stSelectbox"] div[data-baseweb="select"] span{
    color:#f4eaff!important;
    font-weight:750!important;
    letter-spacing:.1px;
}
.functional-topbar div[data-testid="stSelectbox"] svg{
    color:#ffffff!important;
    transition:transform .18s ease!important;
}
.functional-topbar div[data-testid="stSelectbox"]:focus-within svg{
    transform:rotate(180deg);
}
[data-baseweb="popover"]{z-index:999999!important;}
[role="listbox"]{
    max-height:320px!important;
    overflow:auto!important;
    background:rgba(14,8,27,.98)!important;
    border:1px solid rgba(236,72,153,.30)!important;
    border-radius:16px!important;
    padding:7px!important;
    box-shadow:0 22px 55px rgba(0,0,0,.62), 0 0 20px rgba(236,72,153,.14)!important;
}
[role="option"]{
    color:#f8ecff!important;
    background:transparent!important;
    border-radius:11px!important;
    margin:2px 0!important;
    min-height:38px!important;
    transition:background .14s ease, transform .14s ease!important;
}
[role="option"]:hover,
[aria-selected="true"]{
    background:linear-gradient(90deg, rgba(255,79,56,.14), rgba(236,72,153,.18))!important;
    transform:translateX(2px)!important;
}
[role="listbox"]::-webkit-scrollbar{width:8px;}
[role="listbox"]::-webkit-scrollbar-thumb{background:rgba(236,72,153,.32); border-radius:20px;}
.search-active-note{
    display:inline-flex;
    align-items:center;
    gap:8px;
    margin-top:6px;
    padding:6px 11px;
    border-radius:999px;
    background:rgba(34,197,94,.10);
    border:1px solid rgba(34,197,94,.24);
    color:#d8ffe9;
    font-weight:750;
    font-size:.84rem;
}
.nav-button-form button {
    background: transparent !important;
}
.top-icons {display:flex; align-items:center; gap:18px; color:#fff;}
.live-chip {
    display:inline-flex; align-items:center; gap:8px;
    padding:10px 14px; border-radius:999px;
    background:rgba(34,197,94,.10);
    border:1px solid rgba(34,197,94,.35);
    color:#d7ffe8 !important; font-weight:800; font-size:.88rem;
    box-shadow:0 0 22px rgba(34,197,94,.13);
}
.live-chip::first-letter {color:#22c55e;}
.user-chip {display:flex; align-items:center; gap:10px;}
.avatar {
    width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;
    background: linear-gradient(135deg, #ec4899, #fb923c); font-weight:900;
    box-shadow: 0 0 25px rgba(236,72,153,.45);
}
.hero {
    padding: 30px 34px;
    border-radius: 30px;
    background: linear-gradient(145deg, rgba(14,14,20,.88) 0%, rgba(31,21,45,.80) 50%, rgba(78,24,84,.50) 100%);
    color:white;
    box-shadow: 0 24px 70px rgba(0,0,0,.48);
    margin-bottom: 18px;
    border: 1px solid rgba(236,72,153,.42);
    position:relative;
    overflow:hidden;
}
.hero::after {
    content:""; position:absolute; inset:auto -10% -40% 35%; height:170px;
    background: radial-gradient(circle, rgba(236,72,153,.42), transparent 70%);
    filter: blur(18px);
}
.hero h1 {font-size: 2.75rem; margin:0 0 9px 0; letter-spacing:.1px; color:#fff !important;}
.hero p {font-size:1.03rem; color:#d7cceb !important; margin:0;}
.kpi-card {
    padding: 20px 22px;
    border-radius: 24px;
    background: linear-gradient(155deg, rgba(13,14,20,.88), rgba(33,24,42,.70));
    border: 1px solid rgba(236,72,153,.42);
    box-shadow: 0 18px 52px rgba(0,0,0,.40), inset 0 1px 0 rgba(255,255,255,.06);
    min-height: 132px;
    transition: transform .18s ease, border-color .18s ease, box-shadow .18s ease;
}
.kpi-card:hover {transform: translateY(-4px); border-color: rgba(255,79,56,.78); box-shadow: 0 22px 60px rgba(236,72,153,.18), inset 0 1px 0 rgba(255,255,255,.08);}
.kpi-title {font-size:.86rem; color:#bfa8d2; margin-bottom:8px;}
.kpi-value {
    font-size: clamp(1.35rem, 1.55vw, 1.95rem);
    font-weight: 950;
    color: var(--hot);
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    line-height: 1.18;
    display: block;
    max-width: 100%;
    text-shadow:0 0 18px rgba(255,79,56,.28);
}
.kpi-note {font-size:.80rem; color:#a899ba; margin-top:8px;}
.summary-card, .insight-card {
    padding: 19px 21px;
    border-radius: 20px;
    background: linear-gradient(145deg, rgba(13,14,20,.84), rgba(30,22,40,.72));
    border: 1px solid rgba(236,72,153,.36);
    box-shadow: 0 12px 32px rgba(0,0,0,.32);
    margin-bottom: 14px;
}
.reco {padding:16px 18px; border-left:5px solid #ff4f38; border-radius:16px; background:rgba(236,72,153,.13); color:#fff0f8; margin-bottom:12px; font-weight:500; border-top:1px solid rgba(236,72,153,.25); border-right:1px solid rgba(236,72,153,.25); border-bottom:1px solid rgba(236,72,153,.25);}
.warning-card {padding:15px 17px; border-radius:16px; background:rgba(255,79,56,.13); border:1px solid rgba(255,79,56,.38); color:#ffd7cf;}
.small-muted {color:#b9aacb; font-size:.86rem;}
h1, h2, h3, h4, h5, h6, p, span, label {color: var(--text) !important;}
.stTabs [data-baseweb="tab-list"] {display:none;}
[data-testid="stDataFrame"] {border:1px solid rgba(236,72,153,.28); border-radius:16px; overflow:hidden;}
[data-testid="stMetric"] {background: rgba(13,14,20,.7); border:1px solid rgba(236,72,153,.24); border-radius:18px; padding:10px;}
hr {border-color: rgba(236,72,153,.24);}
button[kind="primary"], .stDownloadButton button, .stButton button {
    border-radius: 15px !important;
    background: linear-gradient(135deg, #ff4f38, #ec4899) !important;
    color: white !important;
    border: 1px solid rgba(255,255,255,.14) !important;
    box-shadow: 0 12px 28px rgba(236,72,153,.20);
}
.js-plotly-plot, .plot-container {
    border-radius: 24px;
}
/* Phase 10 polished reference-style floating navigation rail */
.float-rail {
    position: fixed;
    left: 12px;
    top: 88px;
    width: 66px;
    max-height: calc(100vh - 108px);
    z-index: 999;
    border-radius: 26px;
    background: linear-gradient(180deg, rgba(22,18,30,.94), rgba(8,8,12,.96));
    border: 1px solid rgba(255,79,56,.22);
    box-shadow: 0 25px 80px rgba(0,0,0,.60), 0 0 28px rgba(236,72,153,.12), inset 0 1px 0 rgba(255,255,255,.08);
    display:flex;
    flex-direction:column;
    align-items:center;
    padding:14px 0;
    gap:8px;
    backdrop-filter: blur(20px);
}
.rail-logo {font-size:1.5rem; margin-bottom:8px; filter: drop-shadow(0 0 16px rgba(255,79,56,.70));}
.rail-icon {
    position:relative;
    width:39px;height:39px;border-radius:14px;display:flex;align-items:center;justify-content:center;
    color:#f8f7ff;font-size:1.08rem;background:rgba(255,255,255,.025);
    border:1px solid rgba(255,255,255,.045);transition:all .22s ease;
    box-shadow: inset 0 1px 0 rgba(255,255,255,.04);
    text-decoration:none !important;
    cursor:pointer;
}
.rail-icon::before {
    content:""; position:absolute; left:-10px; top:10px; width:3px; height:22px; border-radius:99px;
    background:transparent; box-shadow:none; transition: all .22s ease;
}
.rail-icon:hover, .rail-icon.active {
    transform: translateX(4px) scale(1.05);
    color:#fff;background:linear-gradient(135deg, rgba(255,79,56,.40), rgba(236,72,153,.26));
    border-color:rgba(255,79,56,.58);
    box-shadow:0 0 16px rgba(255,79,56,.34), 0 0 32px rgba(236,72,153,.18), inset 0 1px 0 rgba(255,255,255,.10);
}
.rail-icon.active::before {
    background:#ff4f38; box-shadow:0 0 14px rgba(255,79,56,.88);
}
.rail-icon::after {
    content: attr(data-label);
    position:absolute; left:56px; top:50%; transform:translateY(-50%) translateX(-4px);
    white-space:nowrap; opacity:0; pointer-events:none;
    padding:8px 11px; border-radius:12px;
    background:rgba(15,10,24,.96); color:#fff; font-size:.78rem; font-weight:700;
    border:1px solid rgba(236,72,153,.42);
    box-shadow:0 12px 32px rgba(0,0,0,.45), 0 0 16px rgba(236,72,153,.20);
    transition: all .18s ease;
}
.rail-icon:hover::after {opacity:1; transform:translateY(-50%) translateX(0);}
.rail-spacer {flex:1;border-top:1px solid rgba(255,255,255,.12);width:38px;margin-top:6px;}
.rail-user {
    width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;
    font-weight:900;background:linear-gradient(135deg,#ec4899,#fb923c);
    box-shadow:0 0 22px rgba(236,72,153,.42);font-size:.86rem;
}
.rail-version {font-size:.58rem;color:#9f8fb0;margin-top:-7px;letter-spacing:.5px;}
/* make room for floating rail on large screens */
@media (min-width: 1200px) {
    .block-container { padding-left: 92px; }
}
.chart-shell {
    border-radius: 26px;
    background: linear-gradient(145deg, rgba(13,14,20,.78), rgba(30,22,40,.56));
    border: 1px solid rgba(236,72,153,.26);
    box-shadow: 0 20px 60px rgba(0,0,0,.38), 0 0 25px rgba(236,72,153,.08);
    padding: 10px;
    margin-bottom: 16px;
}
.command-grid-title {font-size:1.05rem;font-weight:800;margin:8px 0 13px 4px;color:#fff;}
.kpi-card, .summary-card, .insight-card {
    box-shadow: 0 18px 52px rgba(0,0,0,.40), 0 0 18px rgba(236,72,153,.18), inset 0 1px 0 rgba(255,255,255,.06);
}
.topbar { position: sticky; top: 0; z-index: 800; }

/* -------------------- Phase 19 Animation & Premium UI Layer -------------------- */
@keyframes bgDrift {0%{background-position:0% 50%;}50%{background-position:100% 50%;}100%{background-position:0% 50%;}}
@keyframes fadeSlideUp {from{opacity:0;transform:translateY(22px) scale(.985);filter:blur(4px);}to{opacity:1;transform:translateY(0) scale(1);filter:blur(0);}}
@keyframes neonPulse {0%,100%{box-shadow:0 0 14px rgba(236,72,153,.18),0 18px 52px rgba(0,0,0,.40);}50%{box-shadow:0 0 24px rgba(255,79,56,.34),0 0 46px rgba(236,72,153,.18),0 22px 64px rgba(0,0,0,.48);}}
@keyframes shimmerSweep {0%{transform:translateX(-120%) rotate(12deg);opacity:0;}18%{opacity:.75;}50%,100%{transform:translateX(145%) rotate(12deg);opacity:0;}}
@keyframes floatSoft {0%,100%{transform:translateY(0);}50%{transform:translateY(-8px);}}
@keyframes statusBlink {0%,100%{opacity:.55;transform:scale(.92);}50%{opacity:1;transform:scale(1.15);}}
@keyframes borderRotate {0%{filter:hue-rotate(0deg);}100%{filter:hue-rotate(360deg);}}
html, body, [data-testid="stAppViewContainer"] {background-size:180% 180% !important;animation:bgDrift 18s ease-in-out infinite;}
.block-container > div:nth-child(n+2){animation:fadeSlideUp .55s ease both;}
.hero,.functional-topbar,.kpi-card,.summary-card,.insight-card,.chart-shell,.float-rail{will-change:transform,box-shadow;}
.hero{animation:fadeSlideUp .65s ease both,neonPulse 5.5s ease-in-out infinite;}
.hero::before{content:"";position:absolute;top:-30%;bottom:-30%;left:-22%;width:34%;background:linear-gradient(90deg,transparent,rgba(255,255,255,.18),transparent);transform:rotate(12deg);animation:shimmerSweep 7.5s ease-in-out infinite;pointer-events:none;}
.functional-topbar{animation:fadeSlideUp .55s ease both;backdrop-filter:blur(22px);}
.kpi-card{animation:fadeSlideUp .55s ease both;position:relative;overflow:hidden;}
.kpi-card::after,.summary-card::after,.insight-card::after{content:"";position:absolute;inset:0;background:radial-gradient(circle at 15% 0%,rgba(255,255,255,.10),transparent 26%);pointer-events:none;opacity:.75;}
.kpi-card:hover,.summary-card:hover,.insight-card:hover,.chart-shell:hover{transform:translateY(-7px) scale(1.01);border-color:rgba(255,79,56,.82)!important;box-shadow:0 0 18px rgba(255,79,56,.36),0 0 46px rgba(236,72,153,.20),0 26px 70px rgba(0,0,0,.52)!important;}
.kpi-value{letter-spacing:.2px;animation:neonPulse 4.8s ease-in-out infinite;white-space:nowrap!important;overflow:hidden!important;text-overflow:ellipsis!important;overflow-wrap:normal!important;word-break:normal!important;}
.chart-shell{position:relative;overflow:hidden;transition:all .28s ease;}
.chart-shell::before{content:"";position:absolute;inset:-1px;border-radius:26px;background:linear-gradient(135deg,rgba(255,79,56,.34),rgba(236,72,153,.08),rgba(96,165,250,.18));opacity:.18;pointer-events:none;animation:borderRotate 9s linear infinite;}
.float-rail{animation:fadeSlideUp .7s ease both;}
.rail-logo{animation:floatSoft 3.6s ease-in-out infinite;}
.rail-icon{transition:transform .22s ease,box-shadow .22s ease,background .22s ease,border-color .22s ease;}
.rail-icon.active{animation:neonPulse 3.2s ease-in-out infinite;}
.stDownloadButton button,.stButton button,button[kind="primary"]{position:relative;overflow:hidden;transition:transform .22s ease,box-shadow .22s ease!important;}
.stDownloadButton button:hover,.stButton button:hover,button[kind="primary"]:hover{transform:translateY(-3px) scale(1.01);box-shadow:0 0 18px rgba(255,79,56,.38),0 0 42px rgba(236,72,153,.18)!important;}
/* Phase 48: select hover handled by smooth search styles above */
.live-strip{display:flex;gap:14px;align-items:center;flex-wrap:wrap;padding:13px 18px;border-radius:18px;background:linear-gradient(135deg,rgba(13,14,20,.70),rgba(33,24,42,.45));border:1px solid rgba(236,72,153,.30);box-shadow:0 16px 40px rgba(0,0,0,.28),inset 0 1px 0 rgba(255,255,255,.05);margin:-4px 0 18px 0;animation:fadeSlideUp .72s ease both;}
.live-dot{width:10px;height:10px;border-radius:50%;background:#22c55e;box-shadow:0 0 18px rgba(34,197,94,.95);animation:statusBlink 1.6s ease-in-out infinite;}
.live-chip{padding:8px 12px;border-radius:999px;background:rgba(255,255,255,.045);border:1px solid rgba(255,255,255,.08);color:#eadcf8;font-weight:750;font-size:.82rem;}
.neon-footer{margin-top:32px;padding:18px 20px;border-radius:20px;background:linear-gradient(135deg,rgba(13,14,20,.74),rgba(45,20,52,.42));border:1px solid rgba(236,72,153,.28);color:#cbb9dc;text-align:center;box-shadow:0 18px 46px rgba(0,0,0,.34);}
[data-testid="stDataFrame"]{animation:fadeSlideUp .5s ease both;box-shadow:0 18px 45px rgba(0,0,0,.26);}
@media (max-width:900px){.float-rail{display:none;}.block-container{padding-left:1rem!important;}.hero h1{font-size:1.9rem;}.live-strip{gap:8px;}}


/* -------------------- Phase 20 KPI Responsiveness + Premium Polish -------------------- */
.kpi-card {
    min-width: 0 !important;
    background: linear-gradient(155deg, rgba(255,255,255,.045), rgba(26,16,38,.72)) !important;
    backdrop-filter: blur(16px);
}
.kpi-card .kpi-value {
    padding: 2px 0 4px 0;
    font-variant-numeric: tabular-nums;
}
.kpi-card .kpi-title,
.kpi-card .kpi-note {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.kpi-card::before {
    content:"";
    position:absolute;
    left:0;
    top:0;
    right:0;
    height:2px;
    background: linear-gradient(90deg, transparent, rgba(255,79,56,.85), rgba(236,72,153,.75), transparent);
    opacity:.75;
}
.kpi-card:hover .kpi-value {filter: drop-shadow(0 0 12px rgba(255,79,56,.55));}
@media (max-width:1500px){.kpi-value{font-size:clamp(1.18rem,1.25vw,1.55rem)!important;}.kpi-card{padding:18px 18px!important;}}
@media (max-width:1200px){.kpi-value{font-size:1.28rem!important;}.kpi-card{min-height:118px!important;}}
.loading-splash {
    display:flex;align-items:center;gap:12px;
    padding:12px 16px;border-radius:18px;
    background:linear-gradient(135deg,rgba(13,14,20,.70),rgba(55,22,64,.42));
    border:1px solid rgba(236,72,153,.28);
    box-shadow:0 12px 34px rgba(0,0,0,.28),0 0 20px rgba(236,72,153,.10);
    margin-bottom:14px;
}
.loading-ring {
    width:16px;height:16px;border-radius:50%;
    border:2px solid rgba(255,255,255,.22);
    border-top-color:#ff4f38;
    animation:spinNeon 1s linear infinite;
}
@keyframes spinNeon {to{transform:rotate(360deg);}}


/* -------------------- Phase 21 Executive Polish: taller KPI cards, softer glow, summary pills -------------------- */
.kpi-card {
    min-height: 158px !important;
    padding: 24px 24px !important;
    display:flex;
    flex-direction:column;
    justify-content:space-between;
    box-shadow: 0 18px 48px rgba(0,0,0,.44), 0 0 10px rgba(255,70,120,.12), inset 0 1px 0 rgba(255,255,255,.06) !important;
}
.kpi-card:hover {
    box-shadow: 0 0 14px rgba(255,79,56,.24), 0 0 30px rgba(236,72,153,.13), 0 24px 62px rgba(0,0,0,.50) !important;
}
.kpi-value {
    background: transparent !important;
    text-shadow: 0 0 10px rgba(255,79,56,.20) !important;
    animation: none !important;
    line-height: 1.05 !important;
}
.kpi-trend {
    margin-top: 6px;
    display:inline-flex;
    align-items:center;
    gap:6px;
    width:fit-content;
    padding:5px 9px;
    border-radius:999px;
    font-size:.72rem;
    font-weight:850;
    color:#f9f7ff;
    border:1px solid rgba(255,255,255,.10);
    background:rgba(255,255,255,.045);
}
.kpi-trend.up { color:#72f2a7; box-shadow:0 0 12px rgba(34,197,94,.18); }
.kpi-trend.down { color:#ff8b8b; box-shadow:0 0 12px rgba(255,79,56,.18); }
.kpi-trend.neutral { color:#e7d8ff; }
.summary-pills {
    display:grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap:14px;
    margin: 10px 0 24px 0;
}
.summary-pill {
    border-radius:18px;
    padding:14px 16px;
    background:linear-gradient(145deg, rgba(255,255,255,.045), rgba(24,15,35,.74));
    border:1px solid rgba(236,72,153,.28);
    box-shadow:0 12px 28px rgba(0,0,0,.26), inset 0 1px 0 rgba(255,255,255,.05);
    overflow:hidden;
}
.summary-pill .pill-label {font-size:.74rem; color:#cbb8da; font-weight:800; margin-bottom:6px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
.summary-pill .pill-value {font-size:.90rem; color:#fff; font-weight:900; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;}
@media (max-width:1500px){.kpi-card{min-height:145px!important;padding:20px!important;}.summary-pills{grid-template-columns:repeat(2,minmax(0,1fr));}}
@media (max-width:900px){.summary-pills{grid-template-columns:1fr;}.kpi-card{min-height:132px!important;}}


/* Full-screen route loading overlay shown after sidebar/top navigation changes */
.route-loader {
    position: fixed !important;
    inset: 0 !important;
    z-index: 2147483647 !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    background:
        radial-gradient(circle at 50% 22%, rgba(236,72,153,.36), transparent 28%),
        radial-gradient(circle at 74% 70%, rgba(124,58,237,.25), transparent 34%),
        rgba(7, 3, 18, .66) !important;
    backdrop-filter: blur(7px) saturate(1.25) !important;
    -webkit-backdrop-filter: blur(7px) saturate(1.25) !important;
    animation: routeLoaderFade 2.35s ease forwards !important;
    pointer-events: all !important;
}
.route-loader-card {
    position: relative !important;
    z-index: 2147483647 !important;
    width: min(590px, 90vw) !important;
    padding: 38px 42px !important;
    border-radius: 34px !important;
    text-align: center !important;
    color: #fff !important;
    background: linear-gradient(145deg, rgba(18,10,30,.98), rgba(64,20,76,.90)) !important;
    border: 1px solid rgba(255,86,180,.72) !important;
    box-shadow:
        0 0 34px rgba(236,72,153,.42),
        0 0 95px rgba(124,58,237,.30),
        0 30px 105px rgba(0,0,0,.70) !important;
    transform: translateZ(0) !important;
    animation: routeCardPop .28s ease-out both !important;
}
.route-loader-orbit {
    width: 104px !important;
    height: 104px !important;
    margin: 0 auto 18px !important;
    position: relative !important;
    border-radius: 50% !important;
    display: grid !important;
    place-items: center !important;
    background: radial-gradient(circle, rgba(255,79,56,.22), rgba(236,72,153,.08) 55%, transparent 70%) !important;
}
.route-loader-orbit:before {
    content: '' !important;
    position: absolute !important;
    inset: 0 !important;
    border-radius: 50% !important;
    border: 3px solid rgba(255,255,255,.10) !important;
    border-top-color: #ff4f38 !important;
    border-right-color: #ec4899 !important;
    box-shadow: 0 0 28px rgba(236,72,153,.55) !important;
    animation: routeSpin 1s linear infinite !important;
}
.route-loader-logo {
    width: 72px !important;
    height: 72px !important;
    display: grid !important;
    place-items: center !important;
    border-radius: 24px !important;
    font-size: 38px !important;
    background: rgba(255,255,255,.07) !important;
    border: 1px solid rgba(255,255,255,.16) !important;
    box-shadow: 0 0 30px rgba(255,79,56,.36) !important;
    animation: loaderPulse .85s ease-in-out infinite alternate !important;
}
.route-loader-title {
    font-size: clamp(24px, 3vw, 34px) !important;
    font-weight: 950 !important;
    letter-spacing: .2px !important;
    margin-bottom: 8px !important;
    color: #ffffff !important;
    text-shadow: 0 0 22px rgba(236,72,153,.42) !important;
}
.route-loader-sub {
    color: #ead9ff !important;
    font-size: 15px !important;
    margin-bottom: 24px !important;
}
.route-loader-bar {
    height: 12px !important;
    overflow: hidden !important;
    border-radius: 999px !important;
    background: rgba(255,255,255,.09) !important;
    border: 1px solid rgba(255,255,255,.13) !important;
}
.route-loader-bar span {
    display: block !important;
    height: 100% !important;
    width: 46% !important;
    border-radius: 999px !important;
    background: linear-gradient(90deg, #ff4f38, #ec4899, #8b5cf6, #ff4f38) !important;
    background-size: 220% 100% !important;
    box-shadow: 0 0 28px rgba(236,72,153,.75) !important;
    animation: loaderMove .85s ease-in-out infinite, loaderGradient 1.4s linear infinite !important;
}
.route-loader-meta {
    margin-top: 16px !important;
    color: #bca9d5 !important;
    font-size: 13px !important;
}
@keyframes loaderMove {0% { transform: translateX(-120%); } 100% { transform: translateX(285%); }}
@keyframes loaderGradient {0%{background-position:0% 50%;}100%{background-position:220% 50%;}}
@keyframes loaderPulse {from { transform: scale(.95); filter: drop-shadow(0 0 9px rgba(236,72,153,.50)); } to { transform: scale(1.06); filter: drop-shadow(0 0 28px rgba(236,72,153,.88)); }}
@keyframes routeSpin {to { transform: rotate(360deg); }}
@keyframes routeCardPop {from { opacity: 0; transform: scale(.94) translateY(12px); } to { opacity: 1; transform: scale(1) translateY(0); }}
@keyframes routeLoaderFade {0% { opacity: 0; } 8% { opacity: 1; } 82% { opacity: 1; } 100% { opacity: 0; visibility: hidden; pointer-events:none; }}


/* PHASE 27: guaranteed visible loading card fallback using pseudo-elements.
   This makes the card visible even if Streamlit/iframe JS removes child HTML during rerun. */
.route-loader::before {
    content: "🍬\\A Nassau Intelligence Platform\\A Loading Dashboard Module...\\A Preparing analytics and controls" !important;
    white-space: pre-line !important;
    position: fixed !important;
    left: 50% !important;
    top: 50% !important;
    transform: translate(-50%, -50%) !important;
    z-index: 2147483647 !important;
    width: min(620px, 88vw) !important;
    min-height: 250px !important;
    padding: 42px 44px 80px !important;
    border-radius: 36px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    line-height: 1.65 !important;
    color: #ffffff !important;
    font-size: clamp(18px, 2.2vw, 30px) !important;
    font-weight: 950 !important;
    letter-spacing: .2px !important;
    background: linear-gradient(145deg, rgba(18,10,30,.98), rgba(65,18,78,.94)) !important;
    border: 1px solid rgba(255,86,180,.80) !important;
    box-shadow: 0 0 42px rgba(236,72,153,.55), 0 0 115px rgba(124,58,237,.36), 0 35px 120px rgba(0,0,0,.78) !important;
    text-shadow: 0 0 24px rgba(236,72,153,.50) !important;
    animation: routeCardPop .25s ease-out both, loaderTextPulse 1.05s ease-in-out infinite alternate !important;
}
.route-loader::after {
    content: "" !important;
    position: fixed !important;
    left: 50% !important;
    top: calc(50% + 106px) !important;
    transform: translateX(-50%) !important;
    z-index: 2147483647 !important;
    width: min(430px, 68vw) !important;
    height: 13px !important;
    border-radius: 999px !important;
    background: linear-gradient(90deg, #ff4f38 0%, #ec4899 35%, #8b5cf6 65%, #ff4f38 100%) !important;
    background-size: 220% 100% !important;
    box-shadow: 0 0 30px rgba(236,72,153,.82) !important;
    animation: loaderGradient 1.1s linear infinite, loaderWidthPulse 1.05s ease-in-out infinite alternate !important;
}
#nassau-visible-nav-loader::before {
    content: "🍬\\A Nassau Intelligence Platform\\A Loading Dashboard Module...\\A Preparing analytics and controls" !important;
    white-space: pre-line !important;
    position: fixed !important;
    left: 50% !important;
    top: 50% !important;
    transform: translate(-50%, -50%) !important;
    z-index: 2147483647 !important;
    width: min(620px, 88vw) !important;
    min-height: 250px !important;
    padding: 42px 44px 80px !important;
    border-radius: 36px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    text-align: center !important;
    line-height: 1.65 !important;
    color: #fff !important;
    font-size: clamp(18px, 2.2vw, 30px) !important;
    font-weight: 950 !important;
    background: linear-gradient(145deg, rgba(18,10,30,.98), rgba(65,18,78,.94)) !important;
    border: 1px solid rgba(255,86,180,.80) !important;
    box-shadow: 0 0 42px rgba(236,72,153,.55), 0 0 115px rgba(124,58,237,.36), 0 35px 120px rgba(0,0,0,.78) !important;
    text-shadow: 0 0 24px rgba(236,72,153,.50) !important;
}
#nassau-visible-nav-loader::after {
    content: "" !important;
    position: fixed !important;
    left: 50% !important;
    top: calc(50% + 106px) !important;
    transform: translateX(-50%) !important;
    z-index: 2147483647 !important;
    width: min(430px, 68vw) !important;
    height: 13px !important;
    border-radius: 999px !important;
    background: linear-gradient(90deg, #ff4f38, #ec4899, #8b5cf6, #ff4f38) !important;
    background-size: 220% 100% !important;
    box-shadow: 0 0 30px rgba(236,72,153,.82) !important;
    animation: nassauVisibleGradient 1.1s linear infinite, loaderWidthPulse 1.05s ease-in-out infinite alternate !important;
}

/* PHASE 31: disable old pseudo-element fallback loader cards.
   The real HTML loader card is now used so the modal is not oversized or clipped. */
.route-loader::before,
.route-loader::after,
#nassau-visible-nav-loader::before,
#nassau-visible-nav-loader::after {
    display: none !important;
    content: none !important;
    visibility: hidden !important;
}

@keyframes loaderTextPulse { from { filter: brightness(.92); } to { filter: brightness(1.16); } }
@keyframes loaderWidthPulse { from { width: min(280px, 50vw); } to { width: min(430px, 68vw); } }



/* PHASE 38: Smooth performance polish + export center cards */
html, body, [data-testid="stAppViewContainer"] { background:#080314 !important; }
.main .block-container { animation: phase38FadeIn .28s ease both; }
@keyframes phase38FadeIn { from { opacity:0; transform:translateY(4px); } to { opacity:1; transform:translateY(0); } }
.kpi-card { min-height: 142px !important; transition: transform .22s ease, box-shadow .22s ease, border-color .22s ease !important; }
.kpi-card:hover, .summary-pill:hover, .export-tile:hover { transform: translateY(-5px); box-shadow:0 0 28px rgba(236,72,153,.28),0 16px 38px rgba(0,0,0,.36) !important; border-color:rgba(255,92,180,.78) !important; }
.kpi-note { background:transparent!important; color:#bfaed3!important; font-family:inherit!important; white-space:normal!important; overflow:visible!important; text-overflow:clip!important; border:0!important; padding:0!important; }
.risk-mini-note { margin-top:12px; padding:11px 13px; border-radius:15px; color:#d9cced; background:rgba(255,255,255,.045); border:1px solid rgba(255,255,255,.08); font-weight:750; font-size:.88rem; }
.export-grid { display:grid; grid-template-columns:repeat(4,minmax(180px,1fr)); gap:18px; margin:18px 0 22px; }
.export-tile { min-height:138px; padding:20px 18px; border-radius:24px; background:linear-gradient(145deg,rgba(16,10,32,.94),rgba(50,18,65,.72)); border:1px solid rgba(236,72,153,.38); box-shadow:0 0 18px rgba(236,72,153,.10); transition:all .22s ease; }
.export-icon { font-size:1.9rem; margin-bottom:12px; filter:drop-shadow(0 0 10px rgba(236,72,153,.55)); }
.export-title { color:#fff; font-weight:950; font-size:1.02rem; margin-bottom:7px; }
.export-copy { color:#bfaed3; font-size:.86rem; line-height:1.35; }
.export-actions { display:grid; grid-template-columns:repeat(3,minmax(180px,1fr)); gap:18px; align-items:stretch; margin-top:18px; }
.export-actions .stDownloadButton button { width:100%!important; min-height:54px!important; border-radius:999px!important; background:linear-gradient(90deg,#ff4f38,#ec4899,#8b5cf6)!important; color:white!important; font-weight:950!important; border:0!important; box-shadow:0 0 20px rgba(236,72,153,.32)!important; transition:transform .20s ease, filter .20s ease!important; }
.export-actions .stDownloadButton button:hover { transform:translateY(-2px)!important; filter:brightness(1.12)!important; }
.neon-footer { animation: phase38FooterGlow 2.8s ease-in-out infinite alternate; }
@keyframes phase38FooterGlow { from { opacity:.74; } to { opacity:1; text-shadow:0 0 15px rgba(236,72,153,.38); } }
@media(max-width:1100px){ .export-grid { grid-template-columns:repeat(2,1fr); } .export-actions { grid-template-columns:1fr; } }
@media(max-width:680px){ .export-grid { grid-template-columns:1fr; } }


/* Phase 39: risk note rendering fix */
.kpi-card .kpi-note, .kpi-note {
    background: transparent !important;
    color: #bfaed3 !important;
    border: 0 !important;
    box-shadow: none !important;
    padding: 0 !important;
    margin-top: 10px !important;
    font-family: inherit !important;
    white-space: normal !important;
}

/* Phase 40: hard KPI note cleanup */

.risk-level-card{
    min-height:210px;
    padding:28px 28px 24px;
    border-radius:24px;
    background:linear-gradient(145deg, rgba(20,12,35,.92), rgba(41,18,64,.80));
    border:1px solid rgba(255,74,143,.48);
    box-shadow:0 0 22px rgba(255,74,143,.16), inset 0 1px 0 rgba(255,255,255,.06);
    display:flex;
    flex-direction:column;
    justify-content:space-between;
    overflow:hidden;
}
.risk-level-title{color:#bfaed3;font-size:1.03rem;font-weight:650;}
.risk-level-value{color:#ff5647;font-size:2.1rem;font-weight:950;line-height:1.1;text-shadow:0 0 18px rgba(255,86,71,.35);}
.risk-level-note{
    margin-top:18px;
    color:#f7efff;
    background:rgba(255,255,255,.06);
    border:1px solid rgba(255,255,255,.10);
    border-radius:16px;
    padding:14px 16px;
    font-weight:700;
    letter-spacing:.01em;
    white-space:normal;
    word-break:break-word;
}
.risk-level-card{
    transition:transform .24s ease, box-shadow .24s ease, border-color .24s ease, background .24s ease;
}
.risk-level-card:hover{
    transform:translateY(-5px);
    box-shadow:0 0 30px rgba(255,80,180,.28), 0 18px 45px rgba(0,0,0,.38), inset 0 1px 0 rgba(255,255,255,.08);
}
.risk-level-card.risk-critical{border-color:rgba(255,77,109,.74);}
.risk-level-card.risk-critical .risk-level-value{color:#ff4d6d;text-shadow:0 0 18px rgba(255,77,109,.42);}
.risk-level-card.risk-high{border-color:rgba(255,140,66,.70);}
.risk-level-card.risk-high .risk-level-value{color:#ff8c42;text-shadow:0 0 18px rgba(255,140,66,.36);}
.risk-level-card.risk-medium{border-color:rgba(255,209,102,.64);}
.risk-level-card.risk-medium .risk-level-value{color:#ffd166;text-shadow:0 0 18px rgba(255,209,102,.30);}
.risk-level-card.risk-low{border-color:rgba(6,214,160,.58);}
.risk-level-card.risk-low .risk-level-value{color:#06d6a0;text-shadow:0 0 18px rgba(6,214,160,.30);}
.risk-level-card.risk-clear{border-color:rgba(6,214,160,.68);}
.risk-level-card.risk-clear .risk-level-value{color:#06d6a0;text-shadow:0 0 18px rgba(6,214,160,.34);}
.risk-level-card.risk-clear .risk-level-note{
    background:rgba(6,214,160,.08);
    border-color:rgba(6,214,160,.26);
    color:#d8fff4;
}

.plain-kpi-note{
    margin-top:10px!important;
    color:#bfaed3!important;
    font-size:.86rem!important;
    font-weight:750!important;
    line-height:1.35!important;
    background:transparent!important;
    border:0!important;
    box-shadow:none!important;
    padding:0!important;
    white-space:normal!important;
    overflow:visible!important;
}



/* PHASE 46: commercial polish, smoother transitions, hidden Plotly toolbars */
.main .block-container {
    animation: phase46PageIn .36s cubic-bezier(.22,.8,.22,1) both;
}
@keyframes phase46PageIn {
    from { opacity:0; transform:translateY(10px); filter:blur(3px); }
    to { opacity:1; transform:translateY(0); filter:blur(0); }
}
.chart-shell {
    animation: phase46ChartIn .42s ease both;
}
@keyframes phase46ChartIn {
    from { opacity:.15; transform:translateY(8px) scale(.992); }
    to { opacity:1; transform:translateY(0) scale(1); }
}
.js-plotly-plot .modebar {
    display:none !important;
    visibility:hidden !important;
}
.rail-icon:hover {
    transform: translateX(6px) scale(1.08) !important;
}
.kpi-card:nth-of-type(1){animation-delay:.02s;}
.kpi-card:nth-of-type(2){animation-delay:.07s;}
.kpi-card:nth-of-type(3){animation-delay:.12s;}
.kpi-card:nth-of-type(4){animation-delay:.17s;}
.kpi-card:nth-of-type(5){animation-delay:.22s;}
.kpi-card:nth-of-type(6){animation-delay:.27s;}
.live-strip {
    backdrop-filter: blur(18px) saturate(1.18);
}

/* PHASE 51: premium dataset import box */
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] {
    background: linear-gradient(145deg, rgba(255,255,255,.055), rgba(236,72,153,.06)) !important;
    border: 1px solid rgba(236,72,153,.32) !important;
    border-radius: 18px !important;
    padding: 12px 12px 10px !important;
    box-shadow: 0 0 18px rgba(236,72,153,.12), inset 0 0 0 1px rgba(255,255,255,.025) !important;
}
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] small { color: #cdbce8 !important; }
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] button {
    border-radius: 999px !important;
    border: 1px solid rgba(255,255,255,.18) !important;
    background: linear-gradient(90deg,#ff4f38,#ec4899,#8b5cf6) !important;
    color: white !important;
    font-weight: 850 !important;
}
.dataset-import-title {
    margin: 14px 0 8px; padding: 12px 13px; border-radius: 16px;
    background: linear-gradient(135deg, rgba(255,79,56,.14), rgba(139,92,246,.11));
    border: 1px solid rgba(236,72,153,.30);
    box-shadow: 0 0 18px rgba(236,72,153,.10);
}
.dataset-import-title b { color:#fff; font-size:.98rem; }
.dataset-import-title span { display:block; color:#bdaed1; font-size:.78rem; margin-top:3px; line-height:1.25; }
.dataset-source-pill {
    display:inline-flex; align-items:center; gap:8px; margin: 8px 0 10px; padding: 7px 12px; border-radius:999px;
    background: rgba(34,197,94,.10); color:#9fffc9; border:1px solid rgba(34,197,94,.25); font-size:.80rem; font-weight:800;
}
.dataset-source-pill.uploaded { background: rgba(236,72,153,.12); color:#ffd2ec; border-color:rgba(236,72,153,.35); }

/* keep loading overlay smooth but lighter */
.route-loader {
    backdrop-filter: blur(5px) saturate(1.12) !important;
    -webkit-backdrop-filter: blur(5px) saturate(1.12) !important;
}
</style>
""",
    unsafe_allow_html=True,
)

DEFAULT_DATA = Path(__file__).parent / "data" / "nassau_orders.csv"


@st.cache_data(show_spinner=False)
def get_data(uploaded=None):
    data = load_data(uploaded if uploaded is not None else DEFAULT_DATA)
    data = attach_factory(data)
    data = add_metrics(data)
    return data


@st.cache_data(show_spinner=False)
def build_dashboard_frames(filtered_df, margin_threshold_value):
    """Cache repeated aggregations so navigation stays smooth and fast."""
    products_base_cached = product_summary(filtered_df)
    products_cached = add_portfolio_actions(classify_products(products_base_cached, margin_threshold_value))
    divisions_cached = division_summary(filtered_df)
    factories_cached = factory_summary(filtered_df)
    regions_cached = region_summary(filtered_df)
    monthly_cached = monthly_margin(filtered_df)
    return products_cached, divisions_cached, factories_cached, regions_cached, monthly_cached


@st.cache_data(show_spinner=False)
def build_export_payloads_cached(products_df, divisions_df, factories_df, monthly_df, regions_df, filtered_df, total_sales_value, total_profit_value, avg_margin_value, risk_count_value, margin_threshold_value):
    """Build export files only when the user requests them.

    Keeping Excel/PDF generation out of the normal page render makes the Reports
    module open almost instantly. Streamlit cache prevents rebuilding the same
    export package when filters have not changed.
    """
    export_products = products_df.copy()
    csv_bytes = export_products.to_csv(index=False).encode("utf-8")

    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        products_df.to_excel(writer, sheet_name="Products", index=False)
        divisions_df.to_excel(writer, sheet_name="Divisions", index=False)
        factories_df.to_excel(writer, sheet_name="Factories", index=False)
        monthly_df.to_excel(writer, sheet_name="Monthly", index=False)
        regions_df.to_excel(writer, sheet_name="Regions", index=False)
        # Keep Excel export responsive on student laptops while still giving a useful raw-data sample.
        filtered_df.head(3000).to_excel(writer, sheet_name="Filtered_Raw_Data", index=False)
    excel_bytes = excel_buffer.getvalue()

    pdf_bytes = build_executive_pdf(
        products=products_df,
        divisions=divisions_df,
        factories=factories_df,
        monthly=monthly_df,
        total_sales=total_sales_value,
        total_profit=total_profit_value,
        avg_margin=avg_margin_value,
        risk_count=risk_count_value,
        margin_threshold=margin_threshold_value,
    )
    return csv_bytes, excel_bytes, pdf_bytes


def money(x):
    return f"${x:,.2f}"


def pct(x):
    return f"{x:,.2f}%"


def clean_label_text(value):
    """Return safe plain text even if older phases pass escaped/raw HTML snippets."""
    text = str(value or "")
    for _ in range(3):
        text = html.unescape(text)
        text = re.sub(r"<\s*/?\s*(div|span|p|br|strong|em|b|i)[^>]*>", " ", text, flags=re.I)
        text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return html.escape(text)


def kpi(title, value, note="", trend="", trend_type="neutral"):
    # Phase 40 hard fix: never allow HTML fragments to reach KPI notes.
    plain_risk_notes = {
        "Critical": "Immediate action required",
        "High": "Management review",
        "Medium": "Monitor closely",
        "Low": "Healthy",
    }
    safe_title = clean_label_text(title)
    safe_value = clean_label_text(value)
    raw_title = re.sub(r"\s+", " ", str(title or "")).strip()
    if raw_title in plain_risk_notes:
        note = plain_risk_notes[raw_title]
    safe_note = clean_label_text(note)
    safe_trend = clean_label_text(trend)
    safe_trend_type = clean_label_text(trend_type)
    trend_html = f"<div class='kpi-trend {safe_trend_type}'>{safe_trend}</div>" if safe_trend else ""
    note_html = f"<div class='plain-kpi-note'>{safe_note}</div>" if safe_note else ""
    st.markdown(
        f"""
        <div class='kpi-card'>
            <div>
                <div class='kpi-title'>{safe_title}</div>
                <div class='kpi-value'>{safe_value}</div>
                {trend_html}
            </div>
            {note_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def risk_level_card(label, count, note):
    """Colored risk card with clean dynamic messages and no raw HTML leakage."""
    label_clean = clean_label_text(label)
    try:
        count_num = int(float(str(count).replace(",", "")))
    except Exception:
        count_num = 0

    default_notes = {
        "Critical": "Immediate action required",
        "High": "Management review",
        "Medium": "Monitor closely",
        "Low": "Healthy",
    }
    zero_notes = {
        "Critical": "🟢 No critical risks detected",
        "High": "🟢 No high risks detected",
        "Medium": "🟢 No medium risks detected",
        "Low": "No low-risk products in current filter",
    }
    note_clean = zero_notes.get(label_clean, "System stable") if count_num == 0 else default_notes.get(label_clean, clean_label_text(note))
    slug = re.sub(r"[^a-z0-9]+", "-", label_clean.lower()).strip("-") or "risk"
    clear_class = " risk-clear" if count_num == 0 else ""

    st.markdown(
        f"""
        <div class="risk-level-card risk-{slug}{clear_class}">
            <div class="risk-level-title">{html.escape(label_clean)}</div>
            <div class="risk-level-value">{count_num:,}</div>
            <div class="risk-level-note">{html.escape(note_clean)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def summary_pill(label, value):
    st.markdown(
        f"<div class='summary-pill'><div class='pill-label'>{label}</div><div class='pill-value'>{value}</div></div>",
        unsafe_allow_html=True,
    )


def insight(title, value, note):
    st.markdown(
        f"<div class='insight-card'><b>{title}</b><br><span style='font-size:1.02rem'>{value}</span><br><span class='small-muted'>{note}</span></div>",
        unsafe_allow_html=True,
    )


def style_fig(fig, height=None):
    """Apply premium dark neon chart styling to every Plotly chart."""
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#f8f7ff", family="Inter, Segoe UI, Arial"),
        title_font=dict(size=18, color="#ffffff"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#d9cced")),
        colorway=["#ff4f38", "#22d3ee", "#a855f7", "#f59e0b", "#10b981", "#ec4899", "#60a5fa"],
        margin=dict(l=35, r=25, t=60, b=40),
    )
    fig.update_xaxes(gridcolor="rgba(255,255,255,.08)", zerolinecolor="rgba(255,255,255,.10)")
    fig.update_yaxes(gridcolor="rgba(255,255,255,.08)", zerolinecolor="rgba(255,255,255,.10)")
    if height:
        fig.update_layout(height=height)
    return fig


def plot_chart(fig, use_container_width=True, height=None):
    """Render Plotly charts with enterprise styling and no development toolbar."""
    st.markdown("<div class='chart-shell'>", unsafe_allow_html=True)
    st.plotly_chart(
        style_fig(fig, height=height),
        use_container_width=use_container_width,
        config={
            "displayModeBar": False,
            "responsive": True,
            "scrollZoom": False,
        },
    )
    st.markdown("</div>", unsafe_allow_html=True)




def show_route_loader(target_page: str, duration: float = 1.05):
    """Render a reliable full-screen loader after navigation changes.

    Earlier versions used sleep + placeholder or component JavaScript. Streamlit can
    finish a rerun so quickly that the loader disappears before the browser paints it.
    This version leaves a fixed overlay in the DOM and lets CSS fade it out, so the
    loading screen is visible on every page change without blocking the app.
    """
    clean_page = target_page.split(" ", 1)[-1] if " " in target_page else target_page
    st.markdown(
        f"""
        <div class="route-loader">
            <div class="route-loader-card">
                <div class="route-loader-orbit"><div class="route-loader-logo">🍬</div></div>
                <div class="route-loader-title">Loading {clean_page}</div>
                <div class="route-loader-sub">Preparing filtered profitability analytics, charts and executive controls...</div>
                <div class="route-loader-bar"><span></span></div>
                <div class="route-loader-meta">Nassau Candy Profitability Intelligence Platform</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )



def inject_instant_navigation_loader():
    """Premium reference-style loader shown instantly on navigation clicks."""
    components.html(
        """
        <script>
        (function () {
            const doc = window.parent.document;
            const overlayId = 'nassau-visible-nav-loader';

            // Anti-flash cleanup: if a loader exists from the previous page, keep it briefly
            // while the new Streamlit page finishes painting, then fade it out smoothly.
            try {
                const stale = doc.getElementById(overlayId);
                if (stale) {
                    stale.style.pointerEvents = 'all';
                    stale.style.opacity = '1';
                    clearTimeout(window.__nassauStaleLoaderCleanup);
                    window.__nassauStaleLoaderCleanup = setTimeout(() => {
                        const current = doc.getElementById(overlayId);
                        if (!current) return;
                        current.style.transition = 'opacity .30s ease';
                        current.style.opacity = '0';
                        setTimeout(() => {
                            try { current.remove(); } catch(e) {}
                            doc.body.style.overflow = doc.body.dataset.nassauPrevOverflow || 'auto';
                            doc.documentElement.style.overflow = doc.documentElement.dataset.nassauPrevOverflow || 'auto';
                            delete doc.body.dataset.nassauPrevOverflow;
                            delete doc.documentElement.dataset.nassauPrevOverflow;
                        }, 180);
                    }, 420);
                }
            } catch(e) {}

            function cleanLabel(text){
                return (text || 'Dashboard Module')
                    .replace(/[🏠📦🏢💸📊🏭⚠️🤖📈📑✅]/g,'')
                    .replace(/&/g,'and')
                    .trim() || 'Dashboard Module';
            }
            function targetMessage(el){
                let label = '';
                if (el){
                    const navLink = el.closest && el.closest('a[href*="?nav="]');
                    const radioLabel = el.closest && el.closest('[data-testid="stSidebar"] [role="radiogroup"] label');
                    const btn = el.closest && el.closest('[data-testid="stSidebar"] button');
                    label = (radioLabel || btn || navLink || el).innerText || (navLink ? navLink.getAttribute('aria-label') : '');
                }
                label = cleanLabel(label);
                const lower = label.toLowerCase();
                if (lower.includes('product')) return 'Loading Product Analytics...';
                if (lower.includes('division')) return 'Loading Division Performance...';
                if (lower.includes('cost')) return 'Loading Cost Diagnostics...';
                if (lower.includes('pareto')) return 'Loading Pareto Intelligence...';
                if (lower.includes('factory')) return 'Loading Factory Analytics...';
                if (lower.includes('risk')) return 'Loading Risk Command Center...';
                if (lower.includes('recommend')) return 'Loading AI Recommendations...';
                if (lower.includes('advanced')) return 'Loading Advanced Analytics...';
                if (lower.includes('report') || lower.includes('export')) return 'Preparing Reports and Export Center...';
                if (lower.includes('coverage')) return 'Checking Requirement Coverage...';
                return 'Loading Executive Dashboard...';
            }
            function createOverlay(message) {
                let old = doc.getElementById(overlayId);
                if (old) old.remove();
                // Freeze page interaction/scroll while the navigation loader is visible.
                if (!doc.body.dataset.nassauPrevOverflow) {
                    doc.body.dataset.nassauPrevOverflow = doc.body.style.overflow || 'auto';
                }
                if (!doc.documentElement.dataset.nassauPrevOverflow) {
                    doc.documentElement.dataset.nassauPrevOverflow = doc.documentElement.style.overflow || 'auto';
                }
                doc.body.style.overflow = 'hidden';
                doc.documentElement.style.overflow = 'hidden';
                const overlay = doc.createElement('div');
                overlay.id = overlayId;
                overlay.setAttribute('aria-live', 'polite');
                overlay.style.cssText = `
                    position:fixed!important;inset:0!important;z-index:2147483647!important;
                    display:flex!important;align-items:center!important;justify-content:center!important;
                    background:radial-gradient(circle at 48% 42%,rgba(236,72,153,.16),transparent 30%),radial-gradient(circle at 70% 66%,rgba(124,58,237,.14),transparent 34%),rgba(3,2,12,.42)!important;
                    backdrop-filter:blur(4px) saturate(1.06)!important;-webkit-backdrop-filter:blur(4px) saturate(1.06)!important;
                    opacity:1!important;transition:opacity .18s ease!important;pointer-events:all!important;cursor:wait!important;touch-action:none!important;`;
                overlay.innerHTML = `
                    <div class="nassau-loader-card">
                        <div class="nassau-loader-stars"></div>
                        <div class="nassau-loader-orbit">
                            <span class="orbit-dot dot-a"></span><span class="orbit-dot dot-b"></span><span class="orbit-dot dot-c"></span>
                            <div class="nassau-loader-logo">🍬</div>
                        </div>
                        <h1 class="nassau-loader-title">Nassau Intelligence Platform</h1>
                        <div class="nassau-title-line"></div>
                        <h2 class="nassau-loader-page">${message}</h2>
                        <p class="nassau-loader-sub">Preparing advanced analytics and intelligence for you</p>
                        <div class="nassau-loader-progress-row"><div class="nassau-loader-track"><div class="nassau-loader-fill"></div></div><span class="nassau-loader-percent">72%</span></div>
                        <div class="nassau-loader-steps">
                            <span class="done"><b>✓</b><strong>Initializing UI</strong><small>Complete</small></span>
                            <span class="done"><b>✓</b><strong>Loading Data</strong><small>Complete</small></span>
                            <span class="active"><b>◔</b><strong>Building Charts</strong><small>In Progress</small></span>
                            <span><b>○</b><strong>AI Insights</strong><small>Pending</small></span>
                        </div>
                        <div class="nassau-loader-meta">🛡️ Secure. Intelligent. Profitable.</div>
                    </div>`;
                let style = doc.getElementById('nassau-visible-nav-loader-style');
                if (!style) {
                    style = doc.createElement('style');
                    style.id = 'nassau-visible-nav-loader-style';
                    style.innerHTML = `
                        #${overlayId} .nassau-loader-card{position:relative;width:min(560px,82vw);max-height:82vh;padding:24px 30px 22px;border-radius:24px;text-align:center;color:#fff;font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:linear-gradient(150deg,rgba(13,10,28,.96),rgba(32,12,45,.92) 48%,rgba(11,8,24,.97));border:1px solid rgba(255,75,180,.72);box-shadow:0 0 0 1px rgba(255,255,255,.06) inset,0 0 34px rgba(236,72,153,.36),0 0 95px rgba(124,58,237,.28),0 28px 110px rgba(0,0,0,.72);overflow:hidden;animation:nassauCardIn .32s cubic-bezier(.2,.8,.2,1) both;}
                        #${overlayId} .nassau-loader-card:before{content:'';position:absolute;inset:-1px;border-radius:inherit;padding:1px;background:linear-gradient(135deg,#ff4f38,#ec4899,#8b5cf6,#22d3ee,#ec4899);-webkit-mask:linear-gradient(#000 0 0) content-box,linear-gradient(#000 0 0);-webkit-mask-composite:xor;mask-composite:exclude;animation:nassauBorderFlow 3s linear infinite;opacity:.92;}
                        #${overlayId} .nassau-loader-card:after{content:'';position:absolute;left:-35%;top:-70%;width:42%;height:240%;background:linear-gradient(90deg,transparent,rgba(255,255,255,.10),transparent);transform:rotate(20deg);animation:nassauSweep 2.15s ease-in-out infinite;}
                        #${overlayId} .nassau-loader-stars{position:absolute;inset:0;opacity:.22;background-image:radial-gradient(circle at 18% 24%,rgba(255,255,255,.75) 1px,transparent 1.5px),radial-gradient(circle at 82% 20%,rgba(236,72,153,.75) 1px,transparent 1.5px),radial-gradient(circle at 75% 72%,rgba(139,92,246,.75) 1px,transparent 1.5px),radial-gradient(circle at 32% 82%,rgba(34,211,238,.55) 1px,transparent 1.5px);}
                        #${overlayId} .nassau-loader-orbit{width:74px;height:74px;margin:0 auto 10px;position:relative;border-radius:50%;display:grid;place-items:center;background:radial-gradient(circle,rgba(236,72,153,.16),rgba(124,58,237,.10) 58%,transparent 72%);}
                        #${overlayId} .nassau-loader-orbit:before{content:'';position:absolute;inset:0;border-radius:50%;border:2px solid rgba(255,255,255,.10);border-top-color:#ff4f38;border-right-color:#ec4899;border-bottom-color:#8b5cf6;box-shadow:0 0 30px rgba(236,72,153,.48);animation:nassauVisibleSpin 1.25s linear infinite;}
                        #${overlayId} .nassau-loader-orbit:after{content:'';position:absolute;inset:12px;border-radius:50%;border:1px dashed rgba(255,255,255,.17);animation:nassauVisibleSpin 3s linear infinite reverse;}
                        #${overlayId} .orbit-dot{position:absolute;width:7px;height:7px;border-radius:50%;background:#ff4f38;box-shadow:0 0 18px #ff4f38;}#${overlayId} .dot-a{top:5px;right:15px;animation:nassauBlink .8s ease-in-out infinite alternate;}#${overlayId} .dot-b{bottom:10px;left:14px;background:#8b5cf6;box-shadow:0 0 18px #8b5cf6;animation:nassauBlink 1.05s ease-in-out infinite alternate;}#${overlayId} .dot-c{bottom:15px;right:10px;background:#d946ef;box-shadow:0 0 18px #d946ef;animation:nassauBlink 1.25s ease-in-out infinite alternate;}
                        #${overlayId} .nassau-loader-logo{width:44px;height:44px;display:grid;place-items:center;border-radius:20px;font-size:26px;background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.16);box-shadow:0 0 20px rgba(255,79,56,.30);animation:nassauVisiblePulse .95s ease-in-out infinite alternate;}
                        #${overlayId} .nassau-loader-title{position:relative;z-index:1;margin:0;font-size:clamp(22px,2.2vw,30px);font-weight:950;line-height:1.12;color:#fff;text-shadow:0 0 24px rgba(236,72,153,.40);}#${overlayId} .nassau-title-line{position:relative;z-index:1;width:38px;height:3px;border-radius:999px;margin:11px auto;background:linear-gradient(90deg,#ff4f38,#ec4899,#8b5cf6);box-shadow:0 0 18px rgba(236,72,153,.68);animation:nassauLinePulse 1s ease-in-out infinite alternate;}
                        #${overlayId} .nassau-loader-page{position:relative;z-index:1;margin:0 0 8px;font-size:clamp(15px,1.7vw,19px);font-weight:950;color:#f779ff;letter-spacing:.01em;}#${overlayId} .nassau-loader-sub{position:relative;z-index:1;color:#d9c7e8;font-size:13.5px;margin:0 auto 16px;max-width:470px;line-height:1.35;}
                        #${overlayId} .nassau-loader-progress-row{position:relative;z-index:1;display:flex;align-items:center;gap:12px;margin:0 auto 16px;}#${overlayId} .nassau-loader-track{flex:1;height:10px;overflow:hidden;border-radius:999px;background:rgba(255,255,255,.075);border:1px solid rgba(255,255,255,.12);box-shadow:inset 0 0 12px rgba(0,0,0,.44);}#${overlayId} .nassau-loader-fill{height:100%;width:72%;border-radius:999px;background:linear-gradient(90deg,#ff4f38,#ec4899,#d946ef,#8b5cf6,#22d3ee);background-size:260% 100%;box-shadow:0 0 24px rgba(236,72,153,.72);animation:nassauVisibleGradient 1.25s linear infinite,nassauFillBreath 1s ease-in-out infinite alternate;}#${overlayId} .nassau-loader-percent{font-size:15px;font-weight:950;color:#fff;min-width:38px;text-align:right;}
                        #${overlayId} .nassau-loader-steps{position:relative;z-index:1;display:grid;grid-template-columns:repeat(4,1fr);gap:9px;margin-bottom:14px;text-align:left;}#${overlayId} .nassau-loader-steps span{display:grid;grid-template-columns:24px 1fr;column-gap:6px;row-gap:1px;align-items:center;padding:8px 7px;border-radius:16px;background:rgba(255,255,255,.035);border:1px solid rgba(255,255,255,.08);}#${overlayId} .nassau-loader-steps b{grid-row:1 / span 2;width:22px;height:22px;border-radius:50%;display:grid;place-items:center;font-size:12px;border:1px solid rgba(255,255,255,.16);color:#bca9d5;}#${overlayId} .nassau-loader-steps strong{font-size:10.5px;font-weight:900;color:#fff;line-height:1.05;}#${overlayId} .nassau-loader-steps small{font-size:9.5px;color:#bca9d5;}#${overlayId} .nassau-loader-steps .done b{border-color:#22c55e;color:#22c55e;box-shadow:0 0 14px rgba(34,197,94,.30);}#${overlayId} .nassau-loader-steps .active b{border-color:#d946ef;color:#d946ef;box-shadow:0 0 16px rgba(217,70,239,.45);animation:nassauVisibleSpin 1.15s linear infinite;}
                        #${overlayId} .nassau-loader-meta{position:relative;z-index:1;margin-top:2px;padding-top:12px;border-top:1px solid rgba(255,255,255,.09);color:#c6b4d9;font-size:11.5px;font-weight:750;}
                        @keyframes nassauVisibleSpin{to{transform:rotate(360deg)}}@keyframes nassauVisiblePulse{from{transform:scale(.96);filter:drop-shadow(0 0 8px rgba(236,72,153,.46))}to{transform:scale(1.05);filter:drop-shadow(0 0 24px rgba(236,72,153,.86))}}@keyframes nassauVisibleGradient{0%{background-position:0% 50%}100%{background-position:260% 50%}}@keyframes nassauFillBreath{from{filter:brightness(.95)}to{filter:brightness(1.18)}}@keyframes nassauCardIn{from{opacity:0;transform:translateY(12px) scale(.96)}to{opacity:1;transform:translateY(0) scale(1)}}@keyframes nassauBorderFlow{0%{filter:hue-rotate(0deg)}100%{filter:hue-rotate(360deg)}}@keyframes nassauSweep{0%{left:-45%;opacity:0}35%{opacity:1}100%{left:115%;opacity:0}}@keyframes nassauBlink{from{opacity:.45;transform:scale(.9)}to{opacity:1;transform:scale(1.08)}}@keyframes nassauLinePulse{from{width:38px;opacity:.78}to{width:64px;opacity:1}}
                        @media(max-width:760px){#${overlayId} .nassau-loader-card{width:88vw;padding:22px 18px;border-radius:22px;}#${overlayId} .nassau-loader-steps{grid-template-columns:repeat(2,1fr);}#${overlayId} .nassau-loader-progress-row{gap:10px;}}
                    `;
                    doc.head.appendChild(style);
                }
                doc.body.appendChild(overlay);
                return overlay;
            }
            function showLoader(triggerEl) {
                const overlay = createOverlay(targetMessage(triggerEl));
                clearTimeout(window.__nassauVisibleLoaderTimer);
                window.__nassauVisibleLoaderTimer = setTimeout(() => {
                    const current = doc.getElementById(overlayId);
                    if (!current) return;
                    current.style.opacity = '0';
                    setTimeout(() => {
                        current.remove();
                        doc.body.style.overflow = doc.body.dataset.nassauPrevOverflow || 'auto';
                        doc.documentElement.style.overflow = doc.documentElement.dataset.nassauPrevOverflow || 'auto';
                        delete doc.body.dataset.nassauPrevOverflow;
                        delete doc.documentElement.dataset.nassauPrevOverflow;
                    }, 180);
                }, 650);
            }
            function isNavigationElement(el) {
                if (!el) return false;
                return !!(el.closest('[data-testid="stSidebar"] [role="radiogroup"] label') || el.closest('[data-testid="stSidebar"] button') || el.closest('.rail-icon') || el.closest('a[href*="?nav="]'));
            }
            if (!window.__nassauVisibleLoaderBoundV33) {
                window.__nassauVisibleLoaderBoundV33 = true;
                window.parent.__nassauShowLoader = function(label){showLoader({innerText: label || 'Dashboard Module'});};
                doc.addEventListener('click', function(e) {
                    const navLink = e.target && e.target.closest ? e.target.closest('a[href*="?nav="]') : null;
                    if (navLink) {
                        // Let the browser update ?nav=... natively. The loader is visual only.
                        showLoader(navLink);
                        return;
                    }
                    // IMPORTANT: do not create the overlay during the capture phase for
                    // Streamlit radio/sidebar controls. If the overlay is inserted before
                    // the browser finishes the click event, it can block the radio option
                    // from being selected. Let Streamlit receive the click first, then
                    // show the loader a few milliseconds later.
                    if (isNavigationElement(e.target)) {
                        const target = e.target;
                        setTimeout(() => showLoader(target), 35);
                    }
                }, true);
                doc.addEventListener('keydown', function(e) {
                    if ((e.key === 'Enter' || e.key === ' ') && isNavigationElement(doc.activeElement)) {
                        const target = doc.activeElement;
                        setTimeout(() => showLoader(target), 35);
                    }
                }, true);
            }
        })();
        </script>
        """,
        height=1,
    )


# PHASE 44: anti-flash navigation loader. The loader stays visible long enough to cover Streamlit rerender.
inject_instant_navigation_loader()

# -------------------- Navigation --------------------
NAV_OPTIONS = [
    "🏠 Executive Overview",
    "📦 Product Profitability",
    "🏢 Division Performance",
    "💸 Cost Diagnostics",
    "📊 Pareto 80/20",
    "🏭 Factory Intelligence",
    "⚠️ Risk Command Center",
    "🤖 Recommendations",
    "📈 Advanced Analytics",
    "📑 Reports & Export",
    "✅ Requirement Coverage",
]

NAV_SLUGS = {
    "executive": "🏠 Executive Overview",
    "products": "📦 Product Profitability",
    "division": "🏢 Division Performance",
    "cost": "💸 Cost Diagnostics",
    "pareto": "📊 Pareto 80/20",
    "factory": "🏭 Factory Intelligence",
    "risk": "⚠️ Risk Command Center",
    "ai": "🤖 Recommendations",
    "analytics": "📈 Advanced Analytics",
    "reports": "📑 Reports & Export",
    "coverage": "✅ Requirement Coverage",
}

PAGE_TO_SLUG = {v: k for k, v in NAV_SLUGS.items()}

# Stable navigation sync for floating HTML rail + Streamlit sidebar radio.
# The previous version used href query links, but the radio widget state stayed fixed,
# so icons looked clickable without changing the page. This block makes the URL query
# parameter the source of truth whenever a rail icon is clicked.
requested_nav = st.query_params.get("nav", "executive")
if isinstance(requested_nav, list):
    requested_nav = requested_nav[0] if requested_nav else "executive"
if requested_nav not in NAV_SLUGS:
    requested_nav = "executive"

default_page = NAV_SLUGS.get(requested_nav, "🏠 Executive Overview")

if "current_nav_slug" not in st.session_state:
    st.session_state.current_nav_slug = requested_nav
    st.session_state.main_navigation = default_page
elif requested_nav != st.session_state.current_nav_slug:
    # User clicked a floating rail icon; force the radio/page state to match the URL.
    st.session_state.current_nav_slug = requested_nav
    st.session_state.main_navigation = default_page

default_index = NAV_OPTIONS.index(st.session_state.get("main_navigation", default_page))

# -------------------- Floating Reference-Style Rail is rendered after sidebar selection --------------------

# -------------------- Sidebar --------------------
with st.sidebar:
    st.markdown("# 🍬 Nassau BI")
    st.caption("Industrial Profitability Control Tower")
    st.markdown(
        """<div class='dataset-import-title'>
        <b>📁 Import Dataset</b>
        <span>Upload a Nassau Candy CSV to replace the default dataset instantly.</span>
        </div>""",
        unsafe_allow_html=True,
    )
    uploaded = st.file_uploader(
        "Upload Nassau Candy CSV",
        type=["csv"],
        key="dataset_import_uploader",
        label_visibility="collapsed",
        help="Upload a CSV containing Order Date, Product Name, Division, Sales, Gross Profit, Cost, Units and related fields.",
    )
    raw = get_data(uploaded)
    source_label = "Uploaded CSV" if uploaded is not None else "Default sample dataset"
    source_class = "uploaded" if uploaded is not None else ""
    st.markdown(f"<div class='dataset-source-pill {source_class}'>● {source_label} · {len(raw):,} valid records</div>", unsafe_allow_html=True)
    st.markdown("<div class='loading-splash'><span class='loading-ring'></span><b>Enterprise analytics engine active</b><span class='small-muted'>Live filters, dropdown search, PDF/Excel export and neon UI loaded</span></div>", unsafe_allow_html=True)

    page = st.radio(
        "Enterprise Navigation",
        NAV_OPTIONS,
        index=default_index,
        key="main_navigation",
        help="Use this menu or the floating icon rail on the left.",
    )

    # If user changes the real Streamlit radio, update URL/state so the floating rail
    # glow follows the selected page on the next rerun.
    selected_slug = PAGE_TO_SLUG.get(page, "executive")
    if selected_slug != st.session_state.get("current_nav_slug", "executive"):
        st.session_state.current_nav_slug = selected_slug
        st.query_params["nav"] = selected_slug

    st.markdown("---")
    with st.expander("Date & Business Filters", expanded=True):
        min_date, max_date = raw["Order Date"].min().date(), raw["Order Date"].max().date()
        date_range = st.date_input(
            "Order date range", value=(min_date, max_date), min_value=min_date, max_value=max_date
        )
        selected_divisions = st.multiselect(
            "Division", sorted(raw["Division"].unique()), default=sorted(raw["Division"].unique())
        )
        selected_regions = st.multiselect(
            "Region", sorted(raw["Region"].unique()), default=sorted(raw["Region"].unique())
        )
        selected_factories = st.multiselect(
            "Factory", sorted(raw["Factory"].unique()), default=sorted(raw["Factory"].unique())
        )

    with st.expander("Risk & Product Controls", expanded=True):
        margin_threshold = st.slider("Margin risk threshold (%)", 0, 100, 25)
        risk_level_filter = st.multiselect(
            "Risk level", ["Low", "Medium", "High", "Critical"], default=["Low", "Medium", "High", "Critical"]
        )
        product_query = st.text_input("Product search")

# Loader is handled by the JavaScript pre-navigation overlay bound above.
# Do not render a post-rerun CSS overlay here; it caused the blur-only screen
# because Streamlit painted the route overlay after the page had already loaded.
if "last_loaded_page" not in st.session_state:
    st.session_state.last_loaded_page = page
elif st.session_state.last_loaded_page != page:
    st.session_state.last_loaded_page = page

# -------------------- Functional Top Search Bar --------------------
@st.cache_data(show_spinner=False)
def build_search_options_cached(dataframe):
    """Build a compact, fast dropdown option list.

    Previous versions pushed too many location values into Streamlit's selectbox,
    which made the top search feel slow. This keeps the command-center dropdown
    lightweight while preserving the most useful choices. Natural shortcut terms
    like factory/product/region still work through apply_global_search().
    """
    def _clean_unique_cached(col_name, limit=None):
        if col_name not in dataframe.columns:
            return []
        vals = dataframe[col_name].dropna().astype(str).str.strip()
        vals = vals[vals != ""]
        values = sorted(vals.unique().tolist())
        return values[:limit] if limit else values

    options = [("All records", "")]

    # High-value shortcuts shown first for instant filtering.
    options += [
        ("🏭 Show all factories", "factory"),
        ("📦 Show all products", "product"),
        ("📊 Show all divisions", "division"),
        ("🌎 Show all regions", "region"),
        ("⚠️ Show risk products", "risk"),
    ]

    # Business categories are small and fast.
    options += [(f"📦 Product: {x}", x) for x in _clean_unique_cached("Product Name")]
    options += [(f"📊 Division: {x}", x) for x in _clean_unique_cached("Division")]
    options += [(f"🏭 Factory: {x}", x) for x in _clean_unique_cached("Factory")]
    options += [(f"🌎 Region: {x}", x) for x in _clean_unique_cached("Region")]

    # Keep geographic choices useful but capped so the dropdown opens quickly.
    options += [(f"📍 State: {x}", x) for x in _clean_unique_cached("State/Province", limit=75)]
    options += [(f"🏙️ City: {x}", x) for x in _clean_unique_cached("City", limit=120)]

    seen = set()
    compact = []
    for label, value in options:
        if label not in seen:
            compact.append((label, value))
            seen.add(label)
    return compact

today_label = datetime.now().strftime("%A, %d %B %Y")
st.markdown("<div class='functional-topbar'>", unsafe_allow_html=True)
tb1, tb2, tb3 = st.columns([1.45, 6.4, 2.15])
with tb1:
    st.markdown(f"<div class='top-date' style='padding-top:12px;'>{today_label}</div>", unsafe_allow_html=True)
with tb2:
    # Cached, type-to-search dropdown. It is faster than rebuilding option lists every rerun.
    compact_options = build_search_options_cached(raw)
    labels = [label for label, _ in compact_options]
    value_map = dict(compact_options)

    selected_search_label = st.selectbox(
        "Global dropdown search",
        options=labels,
        index=0,
        key="global_search_dropdown",
        label_visibility="collapsed",
        placeholder="🔍 Search records, products, factories, regions...",
        help="Type to search or choose All records / factory / product / region shortcuts.",
    )

    global_query = str(value_map.get(selected_search_label, "")).strip()
    st.session_state.global_query = global_query
with tb3:
    st.markdown(
        "<div class='top-icons' style='justify-content:flex-end;padding-top:10px;'>"
        "<span>☾</span><span>🔔</span>"
        "<span class='live-chip'>● Live Analytics</span>"
        "</div>",
        unsafe_allow_html=True,
    )
st.markdown("</div>", unsafe_allow_html=True)

# -------------------- Polished Floating Icon Rail --------------------
def _rail_item(icon, label, slug, active=False):
    cls = "rail-icon active" if active else "rail-icon"
    safe_label = str(label).replace("'", "&#39;")
    return f"<a class='{cls}' data-label='{safe_label}' href='?nav={slug}' target='_self' role='button' aria-label='{safe_label}'>{icon}</a>"

rail_html = "<div class='float-rail'><div class='rail-logo'>🍬</div>"
rail_html += _rail_item("🏠", "Executive Overview", "executive", page == "🏠 Executive Overview")
rail_html += _rail_item("📦", "Product Profitability", "products", page == "📦 Product Profitability")
rail_html += _rail_item("🏢", "Division Performance", "division", page == "🏢 Division Performance")
rail_html += _rail_item("💸", "Cost Diagnostics", "cost", page == "💸 Cost Diagnostics")
rail_html += _rail_item("📊", "Pareto 80/20", "pareto", page == "📊 Pareto 80/20")
rail_html += _rail_item("🏭", "Factory Intelligence", "factory", page == "🏭 Factory Intelligence")
rail_html += _rail_item("⚠️", "Risk Command Center", "risk", page == "⚠️ Risk Command Center")
rail_html += _rail_item("🤖", "AI Insights", "ai", page == "🤖 Recommendations")
rail_html += _rail_item("📈", "Advanced Analytics", "analytics", page == "📈 Advanced Analytics")
rail_html += _rail_item("📑", "Reports & Export", "reports", page == "📑 Reports & Export")
rail_html += _rail_item("✅", "Requirement Coverage", "coverage", page == "✅ Requirement Coverage")
rail_html += "<div class='rail-spacer'></div><div class='rail-version'>v52.0</div></div>"
st.markdown(rail_html, unsafe_allow_html=True)

# -------------------- Search helpers --------------------
def apply_global_search(dataframe, query):
    """Efficient global search across business values and common dashboard terms.

    Improvements:
    - Supports natural terms like "factory", "product", "division", "region", etc.
    - Searches all important text columns using a pre-combined lowercase index.
    - Handles multiple words with AND logic, so "wonka chocolate" returns focused matches.
    - Returns diagnostics so the Settings page can show where matches came from.
    """
    query = str(query or "").strip()
    if not query:
        return dataframe.copy(), pd.DataFrame()

    search_cols = [
        "Product Name", "Product ID", "Division", "Factory", "Region",
        "State/Province", "City", "Customer ID", "Order ID", "Ship Mode",
        "Country/Region", "Postal Code"
    ]
    available_cols = [col for col in search_cols if col in dataframe.columns]
    if not available_cols:
        return dataframe.iloc[0:0].copy(), pd.DataFrame()

    # Column/feature aliases: typing "factory" or "products" should not return zero.
    alias_map = {
        "product": "Product Name", "products": "Product Name", "sku": "Product ID", "skus": "Product ID",
        "division": "Division", "divisions": "Division", "factory": "Factory", "factories": "Factory",
        "region": "Region", "regions": "Region", "state": "State/Province", "states": "State/Province",
        "city": "City", "cities": "City", "customer": "Customer ID", "customers": "Customer ID",
        "order": "Order ID", "orders": "Order ID", "shipping": "Ship Mode", "ship": "Ship Mode",
        "postal": "Postal Code", "zip": "Postal Code", "country": "Country/Region"
    }

    q_lower = query.lower().strip()
    if q_lower in alias_map and alias_map[q_lower] in dataframe.columns:
        col = alias_map[q_lower]
        diagnostics = pd.DataFrame([
            {
                "Matched Column": f"{col} (field search)",
                "Matching Rows": int(len(dataframe)),
                "Unique Matches": int(dataframe[col].nunique())
            }
        ])
        return dataframe.copy(), diagnostics

    # Build one efficient row-wise text index and apply AND search for multi-word queries.
    tokens = [t for t in q_lower.replace(",", " ").split() if t]
    combined = dataframe[available_cols].astype(str).agg(" ".join, axis=1).str.lower()
    mask = pd.Series(True, index=dataframe.index)
    for token in tokens:
        mask &= combined.str.contains(token, regex=False, na=False)

    # If AND search is too strict, fallback to exact query OR search across columns.
    if int(mask.sum()) == 0:
        mask = pd.Series(False, index=dataframe.index)
        for col in available_cols:
            mask |= dataframe[col].astype(str).str.lower().str.contains(q_lower, regex=False, na=False)

    match_counts = []
    filtered_matches = dataframe[mask]
    for col in available_cols:
        col_mask = dataframe[col].astype(str).str.lower().str.contains(q_lower, regex=False, na=False)
        count = int(col_mask.sum())
        if count:
            match_counts.append({
                "Matched Column": col,
                "Matching Rows": count,
                "Unique Matches": int(dataframe.loc[col_mask, col].nunique())
            })

    # Helpful fallback diagnostics when there are row matches through tokenized search.
    if not match_counts and len(filtered_matches):
        match_counts.append({
            "Matched Column": "Multi-column smart search",
            "Matching Rows": int(len(filtered_matches)),
            "Unique Matches": int(filtered_matches["Product Name"].nunique()) if "Product Name" in filtered_matches.columns else int(len(filtered_matches))
        })

    return filtered_matches.copy(), pd.DataFrame(match_counts)

# -------------------- Data filtering --------------------
filtered = raw.copy()
if len(date_range) == 2:
    start, end = date_range
    filtered = filtered[(filtered["Order Date"].dt.date >= start) & (filtered["Order Date"].dt.date <= end)]
filtered = filtered[filtered["Division"].isin(selected_divisions)]
filtered = filtered[filtered["Region"].isin(selected_regions)]
filtered = filtered[filtered["Factory"].isin(selected_factories)]
if product_query:
    filtered = filtered[filtered["Product Name"].str.contains(product_query, case=False, na=False)]

search_diagnostics = pd.DataFrame()
if global_query:
    filtered, search_diagnostics = apply_global_search(filtered, global_query)
    st.markdown(
        f"<div class='warning-card'>🔎 Global search active: <b>{global_query}</b> • Matching rows: <b>{len(filtered):,}</b></div>",
        unsafe_allow_html=True,
    )

if filtered.empty:
    st.error("No records match the selected filters or search term. Clear the top search field or reset filters.")
    st.stop()

products, divisions, factories, regions, monthly = build_dashboard_frames(filtered, margin_threshold)
products_view = products[products["Risk Level"].isin(risk_level_filter)].copy() if risk_level_filter else products.copy()

# KPI calculations
total_sales = filtered["Sales"].sum()
total_profit = filtered["Gross Profit"].sum()
total_cost = filtered["Cost"].sum()
avg_margin = (total_profit / total_sales * 100) if total_sales else 0
risk_count = int((products["Gross Margin %"] < margin_threshold).sum())
# Portfolio-level margin volatility required by the brief.
# Product-level volatility can be 0 when each SKU has stable fixed pricing,
# so the KPI uses monthly portfolio margin standard deviation.
avg_volatility = monthly["Gross Margin %"].std() if len(monthly) > 1 else 0
margin_range = (monthly["Gross Margin %"].max() - monthly["Gross Margin %"].min()) if len(monthly) > 1 else 0
best_product = products.sort_values("Gross Profit", ascending=False).iloc[0]["Product Name"]
highest_margin_product = products.sort_values("Gross Margin %", ascending=False).iloc[0]["Product Name"]
worst_margin_product = products.sort_values("Gross Margin %", ascending=True).iloc[0]["Product Name"]
top_division = divisions.sort_values("Gross Profit", ascending=False).iloc[0]["Division"]
top_factory = factories.sort_values("Gross Profit", ascending=False).iloc[0]["Factory"]

# Lightweight executive trend badges. Uses latest month versus previous month when available.
def _trend_badge(series, suffix=""):
    try:
        if len(series) < 2:
            return "● Stable", "neutral"
        prev = float(series.iloc[-2])
        curr = float(series.iloc[-1])
        if prev == 0:
            return "● Stable", "neutral"
        change = ((curr - prev) / abs(prev)) * 100
        arrow = "▲" if change >= 0 else "▼"
        ttype = "up" if change >= 0 else "down"
        return f"{arrow} {change:+.1f}% {suffix}", ttype
    except Exception:
        return "● Stable", "neutral"

_sales_trend, _sales_type = _trend_badge(monthly["Sales"], "vs prev month")
_profit_trend, _profit_type = _trend_badge(monthly["Gross Profit"], "vs prev month")
_margin_trend, _margin_type = _trend_badge(monthly["Gross Margin %"], "vs prev month")
_cost_trend, _cost_type = _trend_badge(monthly["Cost"], "cost movement")
_risk_trend, _risk_type = ("● Watch", "neutral") if risk_count else ("▲ Healthy", "up")
_vol_trend, _vol_type = ("● Stable", "neutral") if avg_volatility < 1 else ("▼ Volatile", "down")

# -------------------- Header --------------------
st.markdown(
    f"""
<div class='hero'>
  <h1>🍬 Nassau Candy Profitability Intelligence Platform</h1>
  <p>Premium dark BI cockpit inspired by enterprise command centers: product profitability, margin risk, Pareto concentration, factory intelligence, recommendations, and reports.</p>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown(
    f"""
<div class='live-strip'>
  <span class='live-dot'></span>
  <span class='live-chip'>Live Analytics Engine</span>
  <span class='live-chip'>{len(filtered):,} filtered records</span>
  <span class='live-chip'>{products['Product Name'].nunique():,} SKUs monitored</span>
  <span class='live-chip'>Risk threshold: {margin_threshold}%</span>
  <span class='live-chip'>Top factory: {top_factory}</span>
</div>
""",
    unsafe_allow_html=True,
)

c1, c2, c3, c4, c5, c6 = st.columns(6)
with c1:
    kpi("Total Sales", money(total_sales), "Filtered revenue", _sales_trend, _sales_type)
with c2:
    kpi("Gross Profit", money(total_profit), "Sales minus cost", _profit_trend, _profit_type)
with c3:
    kpi("Avg Margin", pct(avg_margin), "Portfolio efficiency", _margin_trend, _margin_type)
with c4:
    kpi("Products", f"{products['Product Name'].nunique():,}", "Unique SKUs", "● Live", "neutral")
with c5:
    kpi("Risk Products", f"{risk_count:,}", f"Below {margin_threshold}% margin", _risk_trend, _risk_type)
with c6:
    kpi("Margin Volatility", pct(avg_volatility), f"Monthly std | range {pct(margin_range)}", _vol_trend, _vol_type)

# Smooth KPI count-up animation. It runs after the KPI DOM is painted and never blocks analytics loading.
components.html(
    """
    <script>
    (function(){
      const doc = window.parent.document;
      const values = Array.from(doc.querySelectorAll('.kpi-value'));
      values.forEach((el, idx) => {
        if (el.dataset.counted === '1') return;
        const original = (el.textContent || '').trim();
        const numeric = parseFloat(original.replace(/[^0-9.-]/g, ''));
        if (!isFinite(numeric)) return;
        el.dataset.counted = '1';
        const isMoney = original.includes('$');
        const isPct = original.includes('%');
        const decimals = isPct || original.includes('.') ? 2 : 0;
        const duration = 720 + idx * 45;
        const start = performance.now();
        function frame(now){
          const p = Math.min(1, (now - start) / duration);
          const ease = 1 - Math.pow(1 - p, 3);
          const val = numeric * ease;
          let text = val.toLocaleString(undefined, {minimumFractionDigits: decimals, maximumFractionDigits: decimals});
          if (isMoney) text = '$' + text;
          if (isPct) text = text + '%';
          el.textContent = text;
          if (p < 1) requestAnimationFrame(frame); else el.textContent = original;
        }
        requestAnimationFrame(frame);
      });
    })();
    </script>
    """,
    height=0,
)

st.markdown("<div class='summary-pills'>", unsafe_allow_html=True)
p1, p2, p3, p4 = st.columns(4)
with p1:
    summary_pill("🏆 Best Profit Product", best_product)
with p2:
    summary_pill("💰 Highest Margin", highest_margin_product)
with p3:
    summary_pill("📊 Top Division", top_division)
with p4:
    summary_pill("🏭 Top Factory", top_factory)
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("---")

# -------------------- Pages --------------------
if page == "🏠 Executive Overview":
    st.subheader("Executive Command Center")
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        insight("Best Product", best_product, "Highest gross profit contributor")
    with s2:
        insight("Margin Watch", worst_margin_product, "Lowest margin product")
    with s3:
        insight("Factory Priority", top_factory, "Highest factory profit node")
    with s4:
        insight("Division Priority", top_division, "Highest division profit node")

    mapped = factories.dropna(subset=["Latitude", "Longitude"])
    if not mapped.empty:
        st.markdown("<div class='command-grid-title'>Factory Command Map</div>", unsafe_allow_html=True)
        fig = px.scatter_geo(
            mapped,
            lat="Latitude",
            lon="Longitude",
            size="Gross Profit",
            color="Gross Margin %",
            hover_name="Factory",
            hover_data=["Sales", "Gross Profit", "Cost", "Products"],
            scope="usa",
            title="Live Factory Profitability Network",
        )
        fig.update_geos(showland=True, landcolor="rgb(12,10,20)", countrycolor="rgba(236,72,153,.35)", lakecolor="rgb(9,5,20)", bgcolor="rgba(0,0,0,0)")
        plot_chart(fig, use_container_width=True, height=430)

    st.markdown("<div class='command-grid-title'>2 x 2 Executive Analytics Grid</div>", unsafe_allow_html=True)
    left, right = st.columns(2)
    with left:
        fig = px.line(
            monthly,
            x="Order Month",
            y=["Sales", "Gross Profit", "Cost"],
            markers=True,
            title="Monthly Sales, Profit and Cost Trend",
        )
        plot_chart(fig, use_container_width=True, height=430)
    with right:
        fig = px.treemap(
            products.head(25), path=["Division", "Product Name"], values="Gross Profit", color="Gross Margin %", title="Profit Contribution Treemap"
        )
        plot_chart(fig, use_container_width=True, height=430)

    c1, c2 = st.columns(2)
    with c1:
        waterfall = go.Figure(
            go.Waterfall(
                name="Profit Bridge",
                orientation="v",
                measure=["absolute", "relative", "total"],
                x=["Revenue", "Cost", "Gross Profit"],
                textposition="outside",
                text=[money(total_sales), "-" + money(total_cost), money(total_profit)],
                y=[total_sales, -total_cost, total_profit],
                connector={"line": {"color": "rgba(236,72,153,.55)"}},
            )
        )
        waterfall.update_layout(title="Revenue-to-Profit Waterfall", yaxis_title="Value")
        plot_chart(waterfall, use_container_width=True, height=430)
    with c2:
        fig = px.histogram(products, x="Gross Margin %", nbins=20, color="Risk Level", title="Margin Distribution by Risk Level")
        fig.add_vline(x=margin_threshold, line_dash="dash", annotation_text="Risk Threshold")
        plot_chart(fig, use_container_width=True, height=430)

    c3, c4 = st.columns(2)
    with c3:
        seg_counts = products["Risk Segment"].value_counts().reset_index()
        seg_counts.columns = ["Risk Segment", "Products"]
        fig = px.pie(seg_counts, names="Risk Segment", values="Products", hole=0.58, title="Product Segmentation Donut")
        plot_chart(fig, use_container_width=True, height=410)
    with c4:
        risk_heat = products.pivot_table(index="Product Name", columns="Risk Level", values="Gross Margin %", aggfunc="mean").fillna(0)
        fig = px.imshow(risk_heat, aspect="auto", title="Margin Risk Heatmap", labels=dict(color="Margin %"))
        plot_chart(fig, use_container_width=True, height=410)

elif page == "📦 Product Profitability":
    st.subheader("Product-Level Profitability Leaderboard")
    st.dataframe(
        products_view[
            [
                "Product Name",
                "Division",
                "Factory",
                "Sales",
                "Gross Profit",
                "Gross Margin %",
                "Profit per Unit",
                "Margin Volatility",
                "Revenue Contribution %",
                "Profit Contribution %",
                "Dependency Index",
                "Risk Score",
                "Risk Level",
                "Risk Segment",
                "Strategic Score",
                "Executive Action",
                "AI Recommendation",
            ]
        ],
        use_container_width=True,
        height=460,
    )
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(
            products.sort_values("Gross Profit", ascending=False).head(12),
            x="Gross Profit",
            y="Product Name",
            color="Division",
            orientation="h",
            title="Top Products by Gross Profit",
        )
        plot_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(
            products.sort_values("Gross Margin %", ascending=False).head(12),
            x="Gross Margin %",
            y="Product Name",
            color="Division",
            orientation="h",
            title="Top Products by Margin %",
        )
        plot_chart(fig, use_container_width=True)

    st.markdown("### Required Product Diagnostics")
    d1, d2 = st.columns(2)
    with d1:
        st.markdown("#### High-Sales / Low-Margin Products")
        high_sales_low_margin = products[(products["Sales"] >= products["Sales"].quantile(0.75)) & (products["Gross Margin %"] < margin_threshold)]
        st.dataframe(high_sales_low_margin[["Product Name", "Sales", "Gross Margin %", "Gross Profit", "Risk Segment", "AI Recommendation"]], use_container_width=True)
    with d2:
        st.markdown("#### Low-Sales / Low-Profit Products")
        low_sales_low_profit = products[(products["Sales"] <= products["Sales"].median()) & (products["Gross Profit"] <= products["Gross Profit"].median())]
        st.dataframe(low_sales_low_profit[["Product Name", "Sales", "Gross Profit", "Gross Margin %", "Risk Segment", "Executive Action"]], use_container_width=True)

elif page == "🏢 Division Performance":
    st.subheader("Division-Level Performance")
    divisions["Revenue-Profit Imbalance"] = (divisions["Revenue Contribution %"] - divisions["Profit Contribution %"]).round(2)
    st.dataframe(divisions, use_container_width=True)
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(divisions, x="Division", y=["Sales", "Gross Profit", "Cost"], barmode="group", title="Revenue vs Profit vs Cost by Division")
        plot_chart(fig, use_container_width=True)
    with c2:
        fig = px.box(filtered, x="Division", y="Gross Margin %", points="all", title="Margin Distribution by Division")
        plot_chart(fig, use_container_width=True)
    fig = px.treemap(products, path=["Division", "Risk Segment", "Product Name"], values="Sales", color="Gross Margin %", title="Division Product Mix and Margin Heat")
    plot_chart(fig, use_container_width=True)

elif page == "💸 Cost Diagnostics":
    st.subheader("Cost vs Margin Diagnostics")
    fig = px.scatter(
        products,
        x="Cost",
        y="Sales",
        size="Gross Profit",
        color="Gross Margin %",
        hover_name="Product Name",
        hover_data=["Risk Segment", "Profit per Unit", "Factory"],
        title="Cost vs Sales with Margin Intensity",
    )
    plot_chart(fig, use_container_width=True)
    fig2 = px.scatter(
        products,
        x="Cost Ratio %",
        y="Gross Margin %",
        size="Sales",
        color="Risk Segment",
        hover_name="Product Name",
        title="Cost Ratio vs Gross Margin Risk Map",
    )
    fig2.add_hline(y=margin_threshold, line_dash="dash", annotation_text="Risk threshold")
    plot_chart(fig2, use_container_width=True)
    heat = products.pivot_table(index="Product Name", columns="Division", values="Gross Margin %", aggfunc="mean").fillna(0)
    fig3 = px.imshow(heat, aspect="auto", title="Product Margin Heatmap", labels=dict(color="Margin %"))
    plot_chart(fig3, use_container_width=True)

    st.markdown("### Pricing, Cost Renegotiation & Discontinuation Review Queue")
    diagnostic = products.copy()
    def diagnostic_issue(row):
        if row["Gross Margin %"] < margin_threshold and row["Sales"] >= products["Sales"].quantile(0.75):
            return "High-volume low-margin product"
        if row["Cost Ratio %"] >= products["Cost Ratio %"].quantile(0.75) and row["Gross Margin %"] < products["Gross Margin %"].median():
            return "Cost-heavy margin-poor product"
        if row["Sales"] <= products["Sales"].quantile(0.25) and row["Gross Profit"] <= products["Gross Profit"].quantile(0.25):
            return "Low-sales low-profit product"
        if row["Profit Contribution %"] >= products["Profit Contribution %"].quantile(0.85):
            return "Strategic profit contributor"
        return "Monitor"
    def diagnostic_action(issue):
        return {
            "High-volume low-margin product": "Reprice and review promotion discounting",
            "Cost-heavy margin-poor product": "Renegotiate sourcing/manufacturing cost",
            "Low-sales low-profit product": "Discontinuation or portfolio rationalization review",
            "Strategic profit contributor": "Protect supply, scale marketing, avoid stockouts",
            "Monitor": "Continue tracking margin and demand"
        }.get(issue, "Monitor")
    diagnostic["Diagnostic Issue"] = diagnostic.apply(diagnostic_issue, axis=1)
    diagnostic["Required Management Action"] = diagnostic["Diagnostic Issue"].apply(diagnostic_action)
    st.dataframe(
        diagnostic.sort_values(["Risk Score", "Cost Ratio %"], ascending=False)[
            ["Product Name", "Division", "Factory", "Sales", "Cost", "Cost Ratio %", "Gross Profit", "Gross Margin %", "Diagnostic Issue", "Required Management Action"]
        ],
        use_container_width=True,
        height=420,
    )

elif page == "📊 Pareto 80/20":
    st.subheader("Pareto 80/20 Profit Concentration")
    p_profit = pareto_table(products, "Gross Profit")
    p_sales = pareto_table(products, "Sales")
    required_profit_products = int((p_profit["Cumulative Gross Profit %"] <= 80).sum() + 1)
    required_sales_products = int((p_sales["Cumulative Sales %"] <= 80).sum() + 1)
    c1, c2, c3 = st.columns(3)
    with c1:
        kpi("Products for 80% Profit", str(required_profit_products), "Dependency indicator")
    with c2:
        kpi("Products for 80% Sales", str(required_sales_products), "Revenue concentration")
    with c3:
        kpi("Top 3 Profit Share", pct(products.sort_values("Profit Contribution %", ascending=False).head(3)["Profit Contribution %"].sum()), "Portfolio dependency")
    fig = go.Figure()
    fig.add_bar(x=p_profit["Product Name"], y=p_profit["Gross Profit"], name="Gross Profit")
    fig.add_scatter(x=p_profit["Product Name"], y=p_profit["Cumulative Gross Profit %"], name="Cumulative Profit %", yaxis="y2")
    fig.update_layout(
        title="Profit Pareto Chart",
        yaxis=dict(title="Gross Profit"),
        yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 110]),
        xaxis_tickangle=-45,
    )
    plot_chart(fig, use_container_width=True)
    st.dataframe(p_profit[["Product Rank", "Product Name", "Division", "Gross Profit", "Profit Contribution %", "Cumulative Gross Profit %"]], use_container_width=True, height=340)

    st.markdown("### Revenue Pareto Chart")
    fig2 = go.Figure()
    fig2.add_bar(x=p_sales["Product Name"], y=p_sales["Sales"], name="Sales")
    fig2.add_scatter(x=p_sales["Product Name"], y=p_sales["Cumulative Sales %"], name="Cumulative Sales %", yaxis="y2")
    fig2.update_layout(
        title="Revenue Pareto Chart",
        yaxis=dict(title="Sales"),
        yaxis2=dict(title="Cumulative %", overlaying="y", side="right", range=[0, 110]),
        xaxis_tickangle=-45,
    )
    plot_chart(fig2, use_container_width=True)

elif page == "🏭 Factory Intelligence":
    st.subheader("Factory-Level Profitability Intelligence")
    st.dataframe(factories, use_container_width=True)
    mapped = factories.dropna(subset=["Latitude", "Longitude"])
    if not mapped.empty:
        fig = px.scatter_geo(
            mapped,
            lat="Latitude",
            lon="Longitude",
            size="Gross Profit",
            color="Gross Margin %",
            hover_name="Factory",
            hover_data=["Sales", "Gross Profit", "Cost", "Products"],
            scope="usa",
            title="Interactive US Factory Profitability Map",
        )
        fig.update_geos(showland=True, landcolor="rgb(12,20,32)", countrycolor="rgb(71,85,105)", lakecolor="rgb(15,23,42)")
        fig.update_layout(height=540)
        plot_chart(fig, use_container_width=True)
    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(factories, x="Factory", y=["Sales", "Gross Profit", "Cost"], barmode="group", title="Factory Sales, Profit and Cost")
        plot_chart(fig, use_container_width=True)
    with c2:
        fig = px.treemap(products, path=["Factory", "Division", "Product Name"], values="Gross Profit", color="Gross Margin %", title="Factory Product Profit Treemap")
        plot_chart(fig, use_container_width=True)

elif page == "⚠️ Risk Command Center":
    st.subheader("Risk Command Center")
    c1, c2, c3, c4 = st.columns(4)
    level_counts = products["Risk Level"].value_counts().to_dict()
    with c1:
        risk_level_card("Critical", level_counts.get("Critical", 0), "Immediate action required")
    with c2:
        risk_level_card("High", level_counts.get("High", 0), "Management review")
    with c3:
        risk_level_card("Medium", level_counts.get("Medium", 0), "Monitor closely")
    with c4:
        risk_level_card("Low", level_counts.get("Low", 0), "Healthy")
    fig = px.scatter(
        products,
        x="Dependency Index",
        y="Risk Score",
        size="Sales",
        color="Risk Level",
        hover_name="Product Name",
        hover_data=["Risk Segment", "Gross Margin %", "Cost Ratio %"],
        title="Dependency vs Risk Matrix",
    )
    plot_chart(fig, use_container_width=True)
    st.markdown("### Management Action Queue")
    st.dataframe(
        products.sort_values("Risk Score", ascending=False).head(12)[
            ["Product Name", "Division", "Factory", "Risk Level", "Risk Segment", "Risk Score", "Dependency Index", "Gross Margin %", "Cost Ratio %", "AI Recommendation"]
        ],
        use_container_width=True,
    )

elif page == "🤖 Recommendations":
    st.subheader("AI-Style Business Recommendations")
    for rec in executive_recommendations(products, divisions, factories):
        st.markdown(f"<div class='reco'>✅ {rec}</div>", unsafe_allow_html=True)
    st.markdown("### Strategic Action Portfolio")
    action_counts = products["Executive Action"].value_counts().reset_index()
    action_counts.columns = ["Executive Action", "Products"]
    fig = px.bar(action_counts, x="Executive Action", y="Products", title="Recommended Management Action Mix")
    plot_chart(fig, use_container_width=True)
    st.markdown("### Product-Level Recommendation Queue")
    action = products.sort_values("Risk Score", ascending=False).head(10)[
        ["Product Name", "Risk Segment", "Risk Level", "Risk Score", "Strategic Score", "Executive Action", "Gross Margin %", "Cost Ratio %", "Dependency Index", "AI Recommendation"]
    ]
    st.dataframe(action, use_container_width=True)
    st.markdown(
        "<div class='warning-card'><b>Management Note:</b> High sales alone should not be treated as success. Products with strong revenue but weak margin are marked as Volume Trap and require pricing or cost intervention.</div>",
        unsafe_allow_html=True,
    )

elif page == "📈 Advanced Analytics":
    st.subheader("Advanced Analytics Lab")
    a1, a2 = st.columns(2)
    with a1:
        heat = products.pivot_table(index="Product Name", columns="Executive Action", values="Gross Margin %", aggfunc="mean").fillna(0)
        fig = px.imshow(heat, aspect="auto", title="Product Margin Heatmap by Executive Action", labels=dict(color="Margin %"))
        plot_chart(fig, use_container_width=True)
    with a2:
        fig = px.scatter(products, x="Strategic Score", y="Risk Score", size="Gross Profit", color="Executive Action", hover_name="Product Name", title="Decision Matrix: Strategic Value vs Risk")
        plot_chart(fig, use_container_width=True)
    fig = go.Figure(
        go.Waterfall(
            name="Profit Bridge",
            orientation="v",
            measure=["absolute", "relative", "total"],
            x=["Total Sales", "Total Cost", "Gross Profit"],
            text=[money(total_sales), "-" + money(total_cost), money(total_profit)],
            y=[total_sales, -total_cost, total_profit],
            textposition="outside",
        )
    )
    fig.update_layout(title="CFO-Style Revenue to Gross Profit Bridge", yaxis_title="USD")
    plot_chart(fig, use_container_width=True)
    st.markdown("### Monthly Margin Volatility Diagnostics")
    fig_vol = px.line(monthly, x="Order Month", y="Gross Margin %", markers=True, title="Portfolio Gross Margin % Over Time")
    fig_vol.add_hline(y=avg_margin, line_dash="dash", annotation_text="Average Margin")
    plot_chart(fig_vol, use_container_width=True, height=360)
    st.caption(f"Portfolio margin volatility is {pct(avg_volatility)} standard deviation across monthly gross margins; observed margin range is {pct(margin_range)}.")

    st.markdown("### Region / State Margin Diagnostics")
    st.dataframe(regions, use_container_width=True, height=320)
    if "State/Province" in regions.columns:
        fig_region = px.bar(regions.head(15), x="Gross Profit", y="State/Province", color="Gross Margin %", orientation="h", title="Top Geographic Profitability by State/Province")
        plot_chart(fig_region, use_container_width=True)

    st.markdown("### Industrial Decision Table")
    st.dataframe(
        products.sort_values(["Executive Action", "Strategic Score"], ascending=[True, False])[
            ["Product Name", "Division", "Factory", "Sales", "Gross Profit", "Gross Margin %", "Risk Level", "Strategic Score", "Executive Action"]
        ],
        use_container_width=True,
    )

elif page == "📑 Reports & Export":
    st.subheader("Reports & Export Center")
    st.markdown(
        """
        <div class='summary-card export-fast-panel'>
          <b>Executive Summary</b><br>
          This export center loads instantly and only prepares heavy CSV, Excel, and PDF files when requested.
          This keeps dashboard navigation smooth while still supporting full filtered reporting.
        </div>
        <div class='export-grid'>
          <div class='export-tile'><div class='export-icon'>📊</div><div class='export-title'>Product CSV</div><div class='export-copy'>Fast product-level profitability table for spreadsheet review.</div></div>
          <div class='export-tile'><div class='export-icon'>📈</div><div class='export-title'>Complete Excel</div><div class='export-copy'>Multi-sheet workbook covering products, divisions, factories, monthly trends, regions, and raw filtered data.</div></div>
          <div class='export-tile'><div class='export-icon'>📑</div><div class='export-title'>Executive PDF</div><div class='export-copy'>Board-ready profitability summary with KPIs and recommendations.</div></div>
          <div class='export-tile'><div class='export-icon'>⚡</div><div class='export-title'>Optimized Build</div><div class='export-copy'>Export files are built on demand and cached for smoother page loading.</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class='export-prep-card'>
          <div><b>Export package status</b><span>Heavy report generation is deferred until you click prepare.</span></div>
          <div class='export-prep-pill'>Smooth Mode Active</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    prepare_exports = st.button("⚡ Prepare Export Package", use_container_width=True, key="prepare_export_package")
    if prepare_exports:
        st.session_state["exports_ready"] = True

    if st.session_state.get("exports_ready", False):
        with st.spinner("Preparing optimized export files..."):
            csv, excel_bytes, pdf_bytes = build_export_payloads_cached(
                products,
                divisions,
                factories,
                monthly,
                regions,
                filtered,
                total_sales,
                total_profit,
                avg_margin,
                risk_count,
                margin_threshold,
            )
        st.success("Export package is ready. Downloads will remain cached until filters or data change.")
        st.markdown("<div class='export-actions'>", unsafe_allow_html=True)
        a1, a2, a3 = st.columns(3)
        with a1:
            st.download_button("⬇️ Export Product CSV", csv, "product_profitability_export.csv", "text/csv", use_container_width=True)
        with a2:
            st.download_button(
                "📈 Export Excel Workbook",
                excel_bytes,
                "nassau_profitability_report.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
        with a3:
            st.download_button("📑 Export Executive PDF", pdf_bytes, "nassau_executive_profitability_report.pdf", "application/pdf", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info("Click **Prepare Export Package** when you are ready to generate downloadable CSV, Excel, and PDF files.")

    st.markdown("### Filtered Raw Data Preview")
    st.dataframe(filtered.head(250), use_container_width=True)

elif page == "✅ Requirement Coverage":
    st.subheader("Project Requirement Coverage Checklist")
    coverage_rows = [
        ["Data Cleaning & Validation", "Complete", "Validates columns, dates, numeric fields, zero sales, missing units, and standardized labels."],
        ["Gross Margin (%)", "Complete", "Calculated for raw, product, division, factory, monthly, and regional views."],
        ["Profit per Unit", "Complete", "Calculated as gross profit divided by units."],
        ["Revenue Contribution", "Complete", "Shows product share of total sales."],
        ["Profit Contribution", "Complete", "Shows product share of total gross profit."],
        ["Margin Volatility", "Complete", "Portfolio monthly margin standard deviation plus product-level volatility diagnostics."],
        ["Product Profitability Leaderboard", "Complete", "Ranked by profit, margin, contribution, volatility, and risk."],
        ["Division Performance", "Complete", "Revenue vs profit, margin distribution, and imbalance analysis."],
        ["Cost vs Margin Diagnostics", "Complete", "Scatter plots, cost ratio maps, heatmaps, and action table for repricing/cost renegotiation/discontinuation."],
        ["Pareto 80/20", "Complete", "Profit and revenue concentration analysis."],
        ["Factory Intelligence", "Complete", "Factory mapping with provided latitude/longitude, profit ranking, factory treemap, and interactive US map."],
        ["User Filters", "Complete", "Date range, division, region, factory, margin threshold, risk level, and product search."],
        ["Exports", "Complete", "CSV, Excel workbook, and executive PDF export."],
        ["Executive Recommendations", "Complete", "AI-style action queue for repricing, scaling, monitoring, and discontinuation review."],
        ["Submission Documentation", "Complete", "README, research paper draft, government executive summary, and documentation included in docs/."],
    ]
    st.dataframe(pd.DataFrame(coverage_rows, columns=["Requirement", "Status", "Implementation Evidence"]), use_container_width=True, height=520)


st.success("Phase 52 active: faster loading, smoother export center, lazy report generation, and optimized transition performance.")


# -------------------- Animated Premium Footer --------------------
st.markdown(
    """
<div class='neon-footer'>
  🍬 Nassau Candy Profitability Intelligence Platform • Enterprise Analytics Suite v52.0 • Powered by Streamlit • Last Refresh: 07 Jun 2026
</div>
""",
    unsafe_allow_html=True,
)


st.markdown("""
<style>
.functional-topbar{margin-top:-25px!important;padding-top:0!important;}
.search-active-note{display:none!important;}
div[data-testid="stSelectbox"]{margin-top:0!important;}
</style>
""", unsafe_allow_html=True)



st.markdown("""
<style>
/* PHASE 52: smoother export center + lighter navigation feel */
.export-fast-panel { animation: fadeIn .26s ease both; }
.export-prep-card{
    display:flex;align-items:center;justify-content:space-between;gap:14px;
    margin:16px 0 18px;padding:16px 18px;border-radius:20px;
    background:linear-gradient(135deg,rgba(255,255,255,.055),rgba(236,72,153,.055));
    border:1px solid rgba(236,72,153,.26);
    box-shadow:0 0 22px rgba(236,72,153,.10), inset 0 0 0 1px rgba(255,255,255,.025);
}
.export-prep-card b{display:block;color:#fff;font-size:1rem;margin-bottom:2px;}
.export-prep-card span{display:block;color:#cdbce8;font-size:.84rem;}
.export-prep-pill{white-space:nowrap;padding:8px 12px;border-radius:999px;font-size:.78rem;font-weight:850;color:#9fffc9;background:rgba(34,197,94,.11);border:1px solid rgba(34,197,94,.28);box-shadow:0 0 16px rgba(34,197,94,.10);}
.export-tile{transition:transform .20s ease, box-shadow .20s ease, border-color .20s ease!important;}
.export-tile:hover{transform:translateY(-3px)!important;box-shadow:0 0 26px rgba(236,72,153,.18),0 12px 38px rgba(0,0,0,.28)!important;border-color:rgba(236,72,153,.42)!important;}
div[data-testid="stSpinner"]{color:#fff!important;}
/* Keep the loader premium but faster and less heavy on route switches */
#nassau-visible-nav-loader{backdrop-filter:blur(3px) saturate(1.03)!important;-webkit-backdrop-filter:blur(3px) saturate(1.03)!important;}
#nassau-visible-nav-loader .nassau-loader-card{animation-duration:.22s!important;}
#nassau-visible-nav-loader .nassau-loader-fill{animation-duration:.78s!important;}
</style>
""", unsafe_allow_html=True)
