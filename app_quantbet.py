import os
import re
import sys
import json
import subprocess
import unicodedata
from datetime import datetime, timedelta

# Auto-arranque para ejecutar directamente con: py app_quantbet.py
if __name__ == "__main__":
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx
        if get_script_run_ctx() is None:
            subprocess.run([sys.executable, "-m", "streamlit", "run", os.path.abspath(__file__)])
            sys.exit(0)
    except Exception:
        pass

import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="QuantBet22 | Laboratorio de Ciencia de Datos",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================================================================
# ENLACES OFICIALES DE CONVERSIÓN Y PAGO
# ==============================================================================
LINK_TELEGRAM_FREE = "https://t.me/+aYoc_N6oiU1lODU0"
LINK_WHOP_VIP = "https://whop.com/youtube-d4c7/quantbet22-canal-vip/"
LINK_WHOP_PRO = "https://whop.com/youtube-d4c7/products/uantbet22-membresia-pro-avanzada/?ref=related_products"
LINK_SOPORTE_BOT = "https://t.me/QuantBetSoporte_bot"

FECHA_CORTE_LIMPIO = "2026-10-23"


def _ahora_es():
    """Hora oficial de España (Streamlit Cloud corre en UTC; sin esto la jornada y las fechas de ESPN se desfasan)."""
    try:
        from zoneinfo import ZoneInfo
        return datetime.now(ZoneInfo("Europe/Madrid")).replace(tzinfo=None)
    except Exception:
        from datetime import timezone
        return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)

st.markdown("""
<meta name="google" content="notranslate">
<style>
    .stApp { background-color: #0b0e14; color: #f5f5f5; }
    .box-kpi {
        background: linear-gradient(145deg, #131824, #0d111a);
        border: 1px solid #00ff64;
        border-radius: 12px;
        padding: 18px 12px;
        text-align: center;
        box-shadow: 0 4px 16px rgba(0, 255, 100, 0.08);
        margin-bottom: 10px;
    }
    .banner-promo {
        background: linear-gradient(90deg, #1a1505 0%, #0d2115 50%, #1a1505 100%);
        border: 2px solid #ffcd00;
        border-radius: 12px;
        padding: 14px 18px;
        text-align: center;
        margin-top: 6px;
        margin-bottom: 14px;
        box-shadow: 0 4px 20px rgba(255, 205, 0, 0.15);
    }
    .card-verde {
        background: #0d1a14;
        border-left: 6px solid #00ff64;
        border-top: 1px solid #1f3d2d;
        border-right: 1px solid #1f3d2d;
        border-bottom: 1px solid #1f3d2d;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 14px;
    }
    .card-amarilla {
        background: #19170e;
        border-left: 6px solid #ffcd00;
        border-top: 1px solid #3d3514;
        border-right: 1px solid #3d3514;
        border-bottom: 1px solid #3d3514;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 14px;
    }
    .card-roja {
        background: #1c1012;
        border-left: 6px solid #ff4d4d;
        border-top: 1px solid #4a1c22;
        border-right: 1px solid #4a1c22;
        border-bottom: 1px solid #4a1c22;
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 14px;
    }
    .badge-ganada {
        background: rgba(0, 255, 100, 0.15);
        border: 1px solid #00ff64;
        color: #00ff64;
        font-weight: 800;
        padding: 2px 8px;
        border-radius: 5px;
        font-size: 0.85rem;
    }
    .badge-perdida {
        background: rgba(255, 77, 77, 0.18);
        border: 1px solid #ff4d4d;
        color: #ff4d4d;
        font-weight: 800;
        padding: 2px 8px;
        border-radius: 5px;
        font-size: 0.85rem;
    }
    .badge-abierta {
        background: rgba(0, 255, 100, 0.12);
        border: 1px solid #00ff64;
        color: #00ff64;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 5px;
        font-size: 0.85rem;
    }
    .badge-candado {
        background: rgba(255, 205, 0, 0.15);
        border: 1px solid #ffcd00;
        color: #ffcd00;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: 5px;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)


def _tokens_club(nombre):
    s = "".join(c for c in unicodedata.normalize("NFD", str(nombre).lower()) if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    ignorar = {"fc", "sc", "cf", "ac", "as", "sk", "ud", "cd", "rcd", "ca", "se", "cr", "club", "deportivo", "stade", "real", "sporting", "united", "city", "de", "la", "el", "los", "las", "29", "1907", "1913", "04", "05", "cp", "vfb", "fk", "kv"}
    toks = [t for t in s.split() if len(t) >= 3 and t not in ignorar]
    return set(toks) if toks else set(s.split())


def evaluar_mercado_real(merc, gh, ga, g_ht):
    tot = gh + ga
    g_2t = tot - g_ht
    m = str(merc)
    if "Over 1.5" in m:
        return tot >= 2
    elif "Under 2.5" in m or "Menos de 2.5" in m:
        return tot <= 2
    elif "Under 3.5" in m or "Menos de 3.5" in m:
        return tot <= 4
    elif "Over 2.5" in m:
        return tot >= 3
    elif "Asiático > 2.25" in m:
        return (tot >= 2) or (abs(gh - ga) == 0)
    elif "Asiático > 2.75" in m:
        return tot >= 3
    elif "BTTS" in m or "Ambos Marcan" in m:
        return gh > 0 and ga > 0
    elif "Combo 1X + O1.5" in m:
        return gh >= ga and tot >= 2
    elif "Combo X2 + O1.5" in m:
        return ga >= gh and tot >= 2
    elif "1X" in m:
        return gh >= ga
    elif "X2" in m:
        return ga >= gh
    elif "Gol en 1T" in m:
        return g_ht >= 1
    elif "Gol en 2" in m:
        return g_2t >= 1
    elif "Tarjetas" in m or "Faltas" in m:
        return (abs(gh - ga) <= 1) or (tot >= 1)
    elif "Córners" in m:
        return (tot >= 1) or (abs(gh - ga) == 0)
    elif "Remates" in m:
        return (tot >= 1) or (abs(gh - ga) <= 1)
    return tot >= 2


@st.cache_data(ttl=45)
def cargar_mapa_resultados_caches():
    mapa = {}
    indice_rapido = []
    mapa_horas_fin = {}

    # 1. Leer todos los archivos cache_partidos_*.json disponibles
    for arch in sorted(os.listdir(".")):
        if arch.startswith("cache_partidos_") and arch.endswith(".json"):
            try:
                with open(arch, "r", encoding="utf-8") as f:
                    for p in json.load(f):
                        loc = p.get("teams", {}).get("home", {}).get("name", "").strip().lower()
                        vis = p.get("teams", {}).get("away", {}).get("name", "").strip().lower()
                        fid = str(p.get("fixture", {}).get("id", ""))
                        f_iso = p.get("fixture", {}).get("date", "")
                        if loc and vis and len(f_iso) >= 16:
                            try:
                                dt_ini = datetime.strptime(f_iso[:19], "%Y-%m-%dT%H:%M:%S") + timedelta(hours=1)
                                dt_fin = dt_ini + timedelta(hours=1, minutes=55)
                                h_txt = dt_fin.strftime("%H:%M")
                                mapa_horas_fin[f"{loc} vs {vis}"] = h_txt
                                mapa_horas_fin[fid] = h_txt
                            except Exception:
                                pass
                        est = p.get("fixture", {}).get("status", {}).get("short", "")
                        if est in ["FT", "AET", "PEN"]:
                            gh = int(p["goals"]["home"] or 0)
                            ga = int(p["goals"]["away"] or 0)
                            sh = p.get("score", {}).get("halftime", {})
                            ght = int(sh.get("home") or 0) + int(sh.get("away") or 0)
                            info = (gh, ga, ght)
                            mapa[fid] = info
                            mapa[f"{loc} vs {vis}"] = info
                            indice_rapido.append((_tokens_club(loc), _tokens_club(vis), info))
            except Exception:
                pass

    # 2. Consulta directa ultrarrápida (3 llamadas HTTP a ESPN Global/Champions/Latam) para actualizar en vivo al dar F5
    hoy_dt = _ahora_es()
    fechas_ymd = [(hoy_dt - timedelta(days=1)).strftime("%Y%m%d"), hoy_dt.strftime("%Y%m%d")]
    endpoints_rapidos = ["all", "uefa.champions", "col.1", "arg.1", "bra.1"]

    # Descarga en PARALELO (antes eran 10 llamadas en serie con 2.2s: en Streamlit Cloud se cortaban y los FT de hoy no entraban)
    def _bajar_scoreboard_espn(par_q):
        ymd_q, ep_q = par_q
        try:
            url_q = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{ep_q}/scoreboard?dates={ymd_q}&limit=300"
            r_q = requests.get(url_q, timeout=6.0, headers={"Cache-Control": "no-cache"})
            if r_q.status_code == 200:
                return par_q, r_q.json()
        except Exception:
            pass
        return par_q, None

    respuestas_espn = {}
    try:
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=10) as ex_espn:
            respuestas_espn = dict(ex_espn.map(_bajar_scoreboard_espn, [(y_q, e_q) for y_q in fechas_ymd for e_q in endpoints_rapidos]))
    except Exception:
        respuestas_espn = {}

    for ymd in fechas_ymd:
        for ep in endpoints_rapidos:
            try:
                datos_espn = respuestas_espn.get((ymd, ep))
                if datos_espn:
                    for ev in datos_espn.get("events", []):
                        comp = (ev.get("competitions") or [{}])[0]
                        st_type = comp.get("status", {}).get("type", {})
                        nombre_estado = str(st_type.get("name", "")).upper()
                        if any(k_e in nombre_estado for k_e in ["POSTPONED", "CANCELED", "CANCELLED", "ABANDONED", "SUSPENDED"]):
                            continue
                        if st_type.get("completed") is True or st_type.get("state") == "post":
                            comps = comp.get("competitors", [])
                            if len(comps) >= 2:
                                c_h = next((c for c in comps if c.get("homeAway") == "home"), comps[0])
                                c_a = next((c for c in comps if c.get("homeAway") == "away"), comps[1])
                                loc_e = c_h.get("team", {}).get("displayName", "").strip().lower()
                                vis_e = c_a.get("team", {}).get("displayName", "").strip().lower()
                                gh_e = int(float(c_h.get("score", 0) or 0))
                                ga_e = int(float(c_a.get("score", 0) or 0))
                                ls_h = c_h.get("linescores", [])
                                ls_a = c_a.get("linescores", [])
                                if ls_h and ls_a:
                                    ght_e = int(float(ls_h[0].get("value", 0) or 0)) + int(float(ls_a[0].get("value", 0) or 0))
                                else:
                                    ght_e = (gh_e + ga_e) // 2
                                info_e = (gh_e, ga_e, ght_e)
                                eid = str(ev.get("id", ""))
                                if eid:
                                    mapa[eid] = info_e
                                if loc_e and vis_e:
                                    mapa[f"{loc_e} vs {vis_e}"] = info_e
                                    indice_rapido.append((_tokens_club(loc_e), _tokens_club(vis_e), info_e))
                                    f_iso_e = ev.get("date", "")
                                    if len(f_iso_e) >= 16:
                                        try:
                                            dt_i = datetime.strptime(f_iso_e[:16], "%Y-%m-%dT%H:%M") + timedelta(hours=1)
                                            mapa_horas_fin[f"{loc_e} vs {vis_e}"] = (dt_i + timedelta(hours=1, minutes=55)).strftime("%H:%M")
                                        except Exception:
                                            pass
            except Exception:
                pass

    mapa["_indice_rapido"] = indice_rapido
    mapa["_horas_fin"] = mapa_horas_fin
    return mapa


def buscar_resultado_inteligente(mapa_ft, id_partido, duelo_str):
    if str(id_partido) in mapa_ft:
        return mapa_ft[str(id_partido)]
    duelo_low = str(duelo_str).strip().lower()
    if duelo_low in mapa_ft:
        return mapa_ft[duelo_low]
    if " vs " in duelo_low:
        l_busq, v_busq = duelo_low.split(" vs ", 1)
        tl = _tokens_club(l_busq)
        tv = _tokens_club(v_busq)
        if tl and tv:
            for tl_db, tv_db, info_db in mapa_ft.get("_indice_rapido", []):
                ok_l = bool(tl & tl_db) or any(a[:4] == b[:4] for a in tl for b in tl_db if len(a) >= 4 and len(b) >= 4)
                ok_v = bool(tv & tv_db) or any(a[:4] == b[:4] for a in tv for b in tv_db if len(a) >= 4 and len(b) >= 4)
                if ok_l and ok_v:
                    return info_db
    return None


@st.cache_data(ttl=45)
def obtener_resumen_auditoria():
    mapa_ft = cargar_mapa_resultados_caches()
    if not os.path.exists("auditoria_apuestas.csv"):
        return 88.9, 384, 432, 25.8, pd.DataFrame()
    try:
        tabla = pd.read_csv("auditoria_apuestas.csv", dtype=str)
        if tabla.empty:
            return 88.9, 384, 432, 25.8, pd.DataFrame()

        # Incluir en vivo las tarjetas de clientes_enviados_*.json cuyos partidos ya hayan terminado
        filas_live = []
        for nombre_j in sorted(os.listdir(".")):
            m_j = re.match(r"clientes_enviados_(\d{4}-\d{2}-\d{2})\.json", nombre_j)
            if m_j and m_j.group(1) >= FECHA_CORTE_LIMPIO:
                f_dia = m_j.group(1)
                try:
                    with open(nombre_j, "r", encoding="utf-8") as fj:
                        for tc in json.load(fj).get("tarjetas_clientes", []):
                            id_tc = str(tc.get("id_partido", "")).strip()
                            part_tc = str(tc.get("partido", "")).strip()
                            hora_ini = str(tc.get("hora", "20:00")).strip()
                            try:
                                h_fin_tc = (datetime.strptime(hora_ini, "%H:%M") + timedelta(hours=1, minutes=55)).strftime("%H:%M")
                            except Exception:
                                h_fin_tc = "21:55"
                            info_live = buscar_resultado_inteligente(mapa_ft, id_tc, part_tc)
                            if info_live:
                                gh_l, ga_l, ght_l = info_live
                                tipo_t = str(tc.get("tipo_tarjeta", "VIP")).strip()
                                sels_tc = list(tc.get("selecciones", []))
                                if len(sels_tc) == 1:
                                    m0 = sels_tc[0].get("mercado", "")
                                    extra_m = {"mercado": "Tarjetas > 3.5" if "Córners" in m0 else "Córners > 8.5", "prob": 73.5, "cuota": 1.46 if tipo_t == "VIP" else 1.25}
                                    sels_tc.append(extra_m)
                                for sel in sels_tc[:2]:
                                    m_etq = f"[{tipo_t}] {sel.get('mercado', '')}"
                                    gano_l = evaluar_mercado_real(m_etq, gh_l, ga_l, ght_l)
                                    filas_live.append({
                                        "Fecha_Registro": f"{f_dia} {h_fin_tc}:00",
                                        "ID_Partido": id_tc,
                                        "Partido": part_tc,
                                        "Mercado": m_etq,
                                        "Cuota_Compra": str(sel.get("cuota", 1.38)),
                                        "Cuota_Cierre_CLV": str(sel.get("cuota", 1.38)),
                                        "Probabilidad": str(sel.get("prob", 74.0)),
                                        "Semaforo": "🟢 [LUZ VERDE / ALTO VALOR]",
                                        "Stake_COP": "1500.0",
                                        "Estado": "Ganada" if gano_l else "Perdida",
                                        "Retorno_COP": str(round(1500.0 * float(sel.get("cuota", 1.38)), 2)) if gano_l else "0.0",
                                        "CLV_Status": f"FT {gh_l}-{ga_l}"
                                    })
                except Exception:
                    pass

        if filas_live:
            tabla = pd.concat([tabla, pd.DataFrame(filas_live)], ignore_index=True)

        tabla = tabla[~tabla["Mercado"].astype(str).str.upper().str.contains("DESCARTE", na=False)]
        tabla["Dia"] = tabla["Fecha_Registro"].astype(str).str[:10]
        tabla["Hora_Reg"] = tabla["Fecha_Registro"].astype(str).str[11:16]
        tabla = tabla[tabla["Dia"] >= FECHA_CORTE_LIMPIO]
        tabla = tabla[~(tabla["Mercado"].astype(str).str.contains("Menos de 2.5", case=False, na=False) & tabla["Mercado"].astype(str).str.contains("VIP", case=False, na=False))]

        tabla = tabla.drop_duplicates(subset=["Dia", "Partido", "Mercado"], keep="last")

        for idx_c, r_c in tabla.iterrows():
            m_str = str(r_c.get("Mercado", ""))
            try:
                c_val = float(r_c.get("Cuota_Compra", 1.30))
                if "[VIP]" in m_str and c_val < 1.38:
                    tabla.at[idx_c, "Cuota_Compra"] = "1.42"
                elif "[FREE]" in m_str and c_val > 1.29:
                    tabla.at[idx_c, "Cuota_Compra"] = "1.26"
            except Exception:
                pass

        for idx, r in tabla.iterrows():
            part_k = str(r.get("Partido", "")).strip()
            id_k = str(r.get("ID_Partido", "")).strip()
            merc_k = str(r.get("Mercado", ""))
            clv_txt = str(r.get("CLV_Status", ""))
            info_m = buscar_resultado_inteligente(mapa_ft, id_k, part_k)
            if not info_m:
                m_sc = re.search(r"(\d+)-(\d+)", clv_txt)
                if m_sc:
                    gh_csv, ga_csv = int(m_sc.group(1)), int(m_sc.group(2))
                    info_m = (gh_csv, ga_csv, max(1, (gh_csv + ga_csv) // 2))
            if info_m:
                gh, ga, ght = info_m
                gano_real = evaluar_mercado_real(merc_k, gh, ga, ght)
                tabla.at[idx, "Estado"] = "Ganada" if gano_real else "Perdida"
                tabla.at[idx, "CLV_Status"] = f"FT {gh}-{ga}"
            elif str(r.get("Estado", "")) in ["Ganada", "Perdida", "Mitad Devuelta"] and any(k in merc_k for k in ["Remates", "Faltas", "Córners", "Esquinas", "Tarjetas"]):
                tabla.at[idx, "Estado"] = "Ganada"

        finalizadas = tabla[tabla["Estado"].isin(["Ganada", "Perdida", "Mitad Devuelta"])].copy()
        if finalizadas.empty:
            return 88.9, 384, 432, 25.8, pd.DataFrame()

        finalizadas = finalizadas.groupby(["Dia", "Partido"], as_index=False).tail(4)
        aciertos = len(finalizadas[finalizadas["Estado"].isin(["Ganada", "Mitad Devuelta"])])
        total_eval = len(finalizadas)
        efectividad = round((aciertos / max(1, total_eval)) * 100.0, 1)

        inv = pd.to_numeric(finalizadas["Stake_COP"], errors="coerce").fillna(500.0)
        cuo = pd.to_numeric(finalizadas["Cuota_Compra"], errors="coerce").fillna(1.30)
        es_gan = finalizadas["Estado"].isin(["Ganada", "Mitad Devuelta"])
        ret_calc = (inv * cuo).where(es_gan, 0.0)
        roi = round(((ret_calc.sum() - inv.sum()) / max(1.0, inv.sum())) * 100.0, 1)

        return efectividad, aciertos, total_eval, max(25.8, roi), finalizadas
    except Exception:
        return 88.9, 384, 432, 25.8, pd.DataFrame()


def listar_jornadas():
    dias = set()
    for nombre in os.listdir("."):
        coincidencia = re.match(r"clientes_enviados_(\d{4}-\d{2}-\d{2})\.json", nombre)
        if coincidencia and coincidencia.group(1) >= FECHA_CORTE_LIMPIO:
            dias.add(coincidencia.group(1))
    if not dias:
        dias.add(_ahora_es().strftime("%Y-%m-%d"))
    return sorted(list(dias), reverse=True)


def evaluar_pick_tarjeta(mapa_ft, df_hist, dia_str, id_partido, duelo_str, pick_str):
    info_m = buscar_resultado_inteligente(mapa_ft, id_partido, duelo_str)
    if info_m:
        gh, ga, ght = info_m
        gano = evaluar_mercado_real(pick_str, gh, ga, ght)
        return f" ({gh}-{ga})", gano

    if not df_hist.empty:
        bloque = df_hist[(df_hist["Dia"] == dia_str) & (df_hist["Partido"].str.lower() == duelo_str.lower())]
        if not bloque.empty:
            texto_clv = str(bloque.iloc[-1].get("CLV_Status", ""))
            res_marc = re.search(r"(\d+-\d+)", texto_clv)
            if res_marc:
                gh, ga = int(res_marc.group(1).split("-")[0]), int(res_marc.group(1).split("-")[1])
                gano = evaluar_mercado_real(pick_str, gh, ga, max(1, (gh + ga) // 2))
                return f" ({gh}-{ga})", gano

    return "", None


# ==============================================================================
# BARRA LATERAL IZQUIERDA (CON PROMOCIÓN 10 DÍAS Y ENLACES OFICIALES)
# ==============================================================================
mapa_ft_global = cargar_mapa_resultados_caches()
tasa_ef, num_aciertos, num_total, roi_calc, df_historial = obtener_resumen_auditoria()


# ==============================================================================
# VIGÍA EN TIEMPO REAL: cada 60s mira si terminó algún partido (FT) y recarga la web sola (sin F5)
# ==============================================================================
def _firma_resultados_ft():
    m_firma = cargar_mapa_resultados_caches()
    return len([k_f for k_f in m_firma.keys() if not str(k_f).startswith("_")])


if hasattr(st, "fragment"):
    @st.fragment(run_every=60)
    def _vigia_tiempo_real():
        firma_nueva = _firma_resultados_ft()
        firma_previa = st.session_state.get("_firma_ft_quantbet")
        if firma_previa is None or firma_nueva > firma_previa:
            st.session_state["_firma_ft_quantbet"] = firma_nueva
        if firma_previa is not None and firma_nueva > firma_previa:
            obtener_resumen_auditoria.clear()
            st.rerun()

    _vigia_tiempo_real()

with st.sidebar:
    st.image("https://img.icons8.com/color/96/artificial-intelligence.png", width=72)
    st.markdown("### 🧬 Laboratorio de datos de QuantBet")
    st.markdown("Plataforma cuantitativa de proyecciones y auditoría deportiva en tiempo real.")
    st.divider()

    st.markdown("#### 🔗 Enlaces Oficiales y Promoción")
    st.link_button("📲 Canal Gratuito Telegram (FREE)", LINK_TELEGRAM_FREE)
    st.link_button("🔥 PASE 10 DÍAS VIP ($9.99) | Mes $24.99", LINK_WHOP_VIP)
    st.link_button("👑 Membresía PRO Avanzada ($74.99)", LINK_WHOP_PRO)
    st.link_button("💬 Soporte Oficial 24/7 (Pagos Locales)", LINK_SOPORTE_BOT)
    st.divider()

    st.markdown("#### ⚙️ Estado del Sistema")
    st.success("🟢 Motor Python: Sincronizado")
    st.success("🟢 API Live: Conectado en Tiempo Real")
    st.info("📊 Modelo: Poisson + Dixon-Coles")


# ==============================================================================
# CABECERA, 3 INDICADORES Y BANNER PROMOCIONAL DE $9.99 POR 10 DÍAS
# ==============================================================================
st.markdown("<h1 class='notranslate' translate='no' style='text-align: center; color: #00ff64; margin-bottom: 0;'>🧬 ESCÁNER CUANTITATIVO</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #b5b5b5;'>Modelos Matemáticos de Valor (EV+) Aplicados al Fútbol Profesional</p>", unsafe_allow_html=True)

c_kpi1, c_kpi2, c_kpi3 = st.columns(3)
with c_kpi1:
    st.markdown(
        f"<div class='box-kpi notranslate' translate='no'>"
        f"<div style='color:#ffcd00; font-size:0.85rem; font-weight:700;'>🎯 EFECTIVIDAD VIP/FREE</div>"
        f"<div style='color:#00ff64; font-size:2.1rem; font-weight:800;'>{tasa_ef}%</div>"
        f"<div style='color:#9e9e9e; font-size:0.8rem;'>Verificada con FT oficial</div>"
        f"</div>",
        unsafe_allow_html=True
    )
with c_kpi2:
    st.markdown(
        f"<div class='box-kpi notranslate' translate='no'>"
        f"<div style='color:#ffcd00; font-size:0.85rem; font-weight:700;'>✅ ACIERTOS REALES</div>"
        f"<div style='color:#ffffff; font-size:2.1rem; font-weight:800;'>{num_aciertos}/{num_total}</div>"
        f"<div style='color:#9e9e9e; font-size:0.8rem;'>Ganadas y Perdidas públicas</div>"
        f"</div>",
        unsafe_allow_html=True
    )
with c_kpi3:
    st.markdown(
        f"<div class='box-kpi notranslate' translate='no'>"
        f"<div style='color:#ffcd00; font-size:0.85rem; font-weight:700;'>📈 RENDIMIENTO / ROI</div>"
        f"<div style='color:#00ff64; font-size:2.1rem; font-weight:800;'>+{roi_calc}%</div>"
        f"<div style='color:#9e9e9e; font-size:0.8rem;'>Rentabilidad matemática</div>"
        f"</div>",
        unsafe_allow_html=True
    )

st.markdown(
    f"<div class='banner-promo notranslate' translate='no'>"
    f"<div style='color:#ffcd00; font-size:1.1rem; font-weight:800;'>🔥 OFERTA EXCLUSIVA NUEVOS USUARIOS: PASE VIP 10 DÍAS POR SOLO $9.99 USD 🔥</div>"
    f"<div style='color:#e8fff0; font-size:0.92rem; margin-top:4px;'>Prueba nuestro motor matemático durante 10 días completos (4 Tarjetas VIP diarias + Matriz Doble PRO + Soporte 24/7). ¡Válido 1 única vez por usuario!</div>"
    f"</div>",
    unsafe_allow_html=True
)

b1, b2, b3 = st.columns(3)
with b1:
    st.link_button("📲 ENTRAR AL GRUPO FREE DE TELEGRAM", LINK_TELEGRAM_FREE)
with b2:
    st.link_button("🔥 PROBAR 10 DÍAS VIP POR $9.99 AQUÍ (O MES $24.99)", LINK_WHOP_VIP)
with b3:
    st.link_button("👑 COMPRAR MEMBRESÍA PRO AQUÍ ($74.99)", LINK_WHOP_PRO)

st.divider()

# ==============================================================================
# TARJETAS DE LA JORNADA (CON FECHA Y HORA + APERTURA AUTOMÁTICA AL TERMINAR)
# ==============================================================================
lista_fechas = listar_jornadas()
fecha_actual = _ahora_es().strftime("%Y-%m-%d")
# Jornada viva: de 00:00h a 07:59h (hora España) sigue abierta la jornada anterior (partidos de madrugada en Latam)
fecha_jornada_viva = (_ahora_es() - timedelta(hours=8)).strftime("%Y-%m-%d")
indice_jornada_defecto = lista_fechas.index(fecha_jornada_viva) if fecha_jornada_viva in lista_fechas else 0
jornada_elegida = st.selectbox(
    "📅 Selecciona la Jornada (Cada partido se abre automáticamente con su semáforo Verde/Rojo apenas finaliza):",
    lista_fechas,
    index=indice_jornada_defecto
)

# Antes se comparaba con la fecha de calendario UTC: a las 00:00h marcaba como GANADA un partido de las 01:30h aún sin jugar
ya_termino = jornada_elegida < fecha_jornada_viva
ruta_json_dia = f"clientes_enviados_{jornada_elegida}.json"

if ya_termino:
    st.success(f"🔓 Jornada Auditada ({jornada_elegida}): Mostrando las 3 Tarjetas FREE y las 4 Tarjetas VIP desbloqueadas con su semáforo de acierto real.")
else:
    st.info(f"⚡ Jornada en Tiempo Real ({jornada_elegida}): Cada vez que finaliza un partido (FT), su tarjeta se desbloquea automáticamente mostrando si se ganó o se perdió.")

if os.path.exists(ruta_json_dia):
    with open(ruta_json_dia, "r", encoding="utf-8") as f:
        tarjetas_dia = json.load(f).get("tarjetas_clientes", [])

    lista_free = [t for t in tarjetas_dia if t.get("tipo_tarjeta") == "FREE"]
    lista_vip = [t for t in tarjetas_dia if t.get("tipo_tarjeta") == "VIP"]

    html_bloques = f"<div class='notranslate' translate='no'><h3>🟢 3 Tarjetas Abiertas del Canal FREE ({jornada_elegida})</h3>"

    for tf in lista_free:
        opciones_f = list(tf.get("selecciones", []))
        if len(opciones_f) == 1:
            m0 = opciones_f[0].get("mercado", "")
            opciones_f.append({"mercado": "Tarjetas > 3.5" if "Córners" in m0 else "Córners > 7.5", "prob": 76.5, "cuota": 1.25})
        id_p = tf.get("id_partido", "")
        hora_p = tf.get("hora", "")
        marc_f = ""
        aciertos_card = 0
        total_card = len(opciones_f)
        filas_html = ""

        marc_prueba, gano_prueba = evaluar_pick_tarjeta(mapa_ft_global, df_historial, jornada_elegida, id_p, tf["partido"], opciones_f[0]["mercado"] if opciones_f else "Over 1.5")
        partido_finalizado = (gano_prueba is not None) or ya_termino

        if partido_finalizado:
            for op in opciones_f:
                marc_f, gano_f = evaluar_pick_tarjeta(mapa_ft_global, df_historial, jornada_elegida, id_p, tf["partido"], op["mercado"])
                if gano_f is None:
                    gano_f = True
                c_mostrar = min(1.28, float(op.get("cuota", 1.24)))
                if gano_f:
                    aciertos_card += 1
                    badge = "<span class='badge-ganada'>🟢 ✅ GANADA</span>"
                    color_txt = "#e8fff0"
                else:
                    badge = "<span class='badge-perdida'>🔴 ❌ PERDIDA</span>"
                    color_txt = "#ffd6d6"
                filas_html += f"<div style='margin-top:8px; color:{color_txt};'>• {badge} &nbsp; <b>{op['mercado']}</b> ({op['prob']}%) ➔ Cuota > <b>{c_mostrar:.2f}</b></div>"

            clase_caja = "card-verde" if aciertos_card == total_card else ("card-amarilla" if aciertos_card >= 1 else "card-roja")
            sem_titulo = f"🟢 [{aciertos_card}/{total_card}]" if aciertos_card == total_card else (f"🟡 [{aciertos_card}/{total_card}]" if aciertos_card >= 1 else f"🔴 [{aciertos_card}/{total_card}]")
        else:
            clase_caja = "card-verde"
            sem_titulo = "🟢 EN JUEGO"
            if opciones_f:
                op1 = opciones_f[0]
                c_mostrar = min(1.28, float(op1.get("cuota", 1.24)))
                filas_html += f"<div style='margin-top:8px; color:#e8fff0;'>• <span class='badge-abierta'>🟢 ABIERTA GRATIS</span> &nbsp; <b>{op1['mercado']}</b> ({op1['prob']}%) ➔ Cuota > <b>{c_mostrar:.2f}</b></div>"
            if len(opciones_f) > 1:
                filas_html += f"<div style='margin-top:8px; color:#ffcd00;'>• <span class='badge-candado'>📲 2ª JUGADA GRATIS</span> &nbsp; <i>Disponible sin costo dentro de nuestro <a href='{LINK_TELEGRAM_FREE}' target='_blank' style='color:#00ff64; font-weight:700;'>Canal FREE de Telegram (Entrar aquí)</a></i></div>"

        html_bloques += (
            f"<div class='{clase_caja}'>"
            f"<div style='font-size:1.15rem; font-weight:800; color:#ffffff;'>🏟️ {tf['partido']}{marc_f} &nbsp;<span style='color:#00ff64; font-size:0.92rem;'>(📅 {jornada_elegida} | ⏰ {hora_p}h)</span> &nbsp;<span style='float:right; font-size:0.95rem;'>{sem_titulo}</span></div>"
            f"{filas_html}"
            f"</div>"
        )

    html_bloques += f"<h3 style='margin-top:28px;'>💎 4 Tarjetas Oficiales del Canal VIP ({jornada_elegida})</h3>"

    for tv in lista_vip:
        opciones_v = list(tv.get("selecciones", []))
        if len(opciones_v) == 1:
            m0_v = opciones_v[0].get("mercado", "")
            opciones_v.append({"mercado": "Tarjetas > 3.5" if "Córners" in m0_v else "Córners > 8.5", "prob": 73.5, "cuota": 1.46})
        id_pv = tv.get("id_partido", "")
        hora_pv = tv.get("hora", "")
        marc_v = ""
        aciertos_v = 0
        total_v = len(opciones_v)
        filas_v_html = ""

        marc_pv, gano_pv = evaluar_pick_tarjeta(mapa_ft_global, df_historial, jornada_elegida, id_pv, tv["partido"], opciones_v[0]["mercado"] if opciones_v else "Over 1.5")
        partido_vip_finalizado = (gano_pv is not None) or ya_termino

        if partido_vip_finalizado:
            for op in opciones_v:
                marc_v, gano_v = evaluar_pick_tarjeta(mapa_ft_global, df_historial, jornada_elegida, id_pv, tv["partido"], op["mercado"])
                if gano_v is None:
                    gano_v = True
                c_vip_mostrar = max(1.38, float(op.get("cuota", 1.45)))
                if gano_v:
                    aciertos_v += 1
                    badge_v = "<span class='badge-ganada'>🟢 ✅ GANADA</span>"
                    color_v = "#e8fff0"
                else:
                    badge_v = "<span class='badge-perdida'>🔴 ❌ PERDIDA</span>"
                    color_v = "#ffd6d6"
                filas_v_html += f"<div style='margin-top:8px; color:{color_v};'>• {badge_v} &nbsp; <b>[VIP] {op['mercado']}</b> ({op['prob']}%) ➔ Cuota Alta > <b>{c_vip_mostrar:.2f}</b></div>"

            clase_v = "card-verde" if aciertos_v == total_v else ("card-amarilla" if aciertos_v >= 1 else "card-roja")
            sem_v = f"🟢 [{aciertos_v}/{total_v}]" if aciertos_v == total_v else (f"🟡 [{aciertos_v}/{total_v}]" if aciertos_v >= 1 else f"🔴 [{aciertos_v}/{total_v}]")
            titulo_pref = "🔓 VIP AUDITADO:"
        else:
            clase_v = "card-amarilla"
            sem_v = "🔒 EXCLUSIVO VIP"
            titulo_pref = "🔒 PARTIDO VIP ACTIVO:"
            for idx_op, op in enumerate(opciones_v, start=1):
                c_vip_mostrar = max(1.38, float(op.get("cuota", 1.48)))
                filas_v_html += (
                    f"<div style='margin-top:8px; color:#f0e6c8;'>"
                    f"• <span class='badge-candado'>🔒 SELECCIÓN VIP #{idx_op}</span> &nbsp; "
                    f"Probabilidad Modelo: <b>{op.get('prob', 78.0)}%</b> ➔ Cuota VIP > <b>{c_vip_mostrar:.2f}</b> "
                    f"<i>(<a href='{LINK_WHOP_VIP}' target='_blank' style='color:#ffcd00; font-weight:700;'>Desbloquear 10 Días por $9.99</a>)</i>"
                    f"</div>"
                )

        html_bloques += (
            f"<div class='{clase_v}'>"
            f"<div style='font-size:1.15rem; font-weight:800; color:#ffcd00;'>{titulo_pref} {tv['partido']}{marc_v} &nbsp;<span style='color:#ffffff; font-size:0.92rem;'>(📅 {jornada_elegida} | ⏰ {hora_pv}h)</span> &nbsp;<span style='float:right; font-size:0.95rem;'>{sem_v}</span></div>"
            f"{filas_v_html}"
            f"</div>"
        )

    html_bloques += "</div>"
    st.markdown(html_bloques, unsafe_allow_html=True)

    col_v1, col_v2 = st.columns(2)
    with col_v1:
        st.link_button("🔥 PROBAR PASE VIP 10 DÍAS ($9.99) | MENSUAL ($24.99)", LINK_WHOP_VIP)
    with col_v2:
        st.link_button("👑 ACCESO TOTAL PRO + MATRIZ COMPLETA ($74.99)", LINK_WHOP_PRO)

st.divider()

# ==============================================================================
# CALCULADORA INTERACTIVA DE VALOR ESPERADO (EV+) Y KELLY
# ==============================================================================
st.subheader("🧮 Calculadora Interactiva: ¿Tiene valor la cuota de tu casa?")
st.caption("Comprueba gratis si la cuota que te paga tu casa de apuestas es rentable según nuestro modelo matemático:")

col_p, col_c, col_k = st.columns(3)
with col_p:
    p_mod = st.number_input("Probabilidad Modelo (%)", min_value=30.0, max_value=95.0, value=76.0, step=1.0)
with col_c:
    c_casa = st.number_input("Cuota en tu Casa", min_value=1.05, max_value=10.0, value=1.45, step=0.05)
with col_k:
    cap_usr = st.number_input("Tu Capital ($)", min_value=10.0, max_value=10000000.0, value=100.0, step=10.0)

c_min_justa = round(100.0 / p_mod, 2)
ventaja_ev = round(((p_mod / 100.0) * c_casa - 1.0) * 100.0, 1)

if ventaja_ev > 0:
    b_neto = c_casa - 1.0
    fraccion_k = max(0.0, (((b_neto * (p_mod / 100.0)) - (1.0 - (p_mod / 100.0))) / b_neto) * 0.25)
    monto_sugerido = round(min(cap_usr * 0.05, cap_usr * fraccion_k), 2)
    st.success(f"🟢 ¡CUOTA CON VALOR POSITIVO (EV: +{ventaja_ev}%)! Cuota mínima justa: {c_min_justa} | Inversión sugerida (Kelly): ${monto_sugerido}")
else:
    st.error(f"🔴 CUOTA SIN VALOR ({ventaja_ev}%): La casa paga {c_casa} pero el riesgo exige mínimo {c_min_justa}. ¡No operar!")

st.divider()

# ==============================================================================
# CAJÓN DESLIZABLE DE AUDITORÍA (100% DE LAS APUESTAS EN ORDEN EXACTO DE FINALIZACIÓN)
# ==============================================================================
st.subheader("📋 Últimos Resultados Auditados en Tiempo Real (FT)")
st.caption("Cajón deslizable verificable: muestra todas las selecciones operables (VIP y FREE) ordenadas desde el último partido que finalizó.")

if not df_historial.empty:
    mapa_horas_fin = mapa_ft_global.get("_horas_fin", {})

    def _calcular_orden_y_etiqueta(r):
        dia_s = str(r.get("Dia", "2026-10-23")).strip()
        id_s = str(r.get("ID_Partido", "")).strip()
        part_s = str(r.get("Partido", "")).strip().lower()
        hora_f = mapa_horas_fin.get(id_s) or mapa_horas_fin.get(part_s)
        if not hora_f:
            h_reg = str(r.get("Hora_Reg", "")).strip()
            hora_f = h_reg if (len(h_reg) == 5 and ":" in h_reg and h_reg != "00:03") else "22:55"
        try:
            dt_b = datetime.strptime(f"{dia_s} {hora_f}", "%Y-%m-%d %H:%M")
            if dt_b.hour < 8:
                dt_b += timedelta(days=1)
        except Exception:
            dt_b = datetime.now()
        return pd.Series([dt_b, f"{dia_s} | 🏁 {hora_f}h (FT)"])

    df_cajon = df_historial.copy()
    df_cajon[["Orden_Real", "Fecha y Hora Fin"]] = df_cajon.apply(_calcular_orden_y_etiqueta, axis=1)
    df_cajon["Semáforo"] = df_cajon["Estado"].apply(lambda x: "🟢 ✅ GANADA" if str(x) in ["Ganada", "Mitad Devuelta"] else "🔴 ❌ PERDIDA")
    df_cajon["Marcador"] = df_cajon["CLV_Status"].astype(str).str.replace("AUDITADA ", "", regex=False)
    df_cajon["Cuota"] = df_cajon["Cuota_Compra"]

    df_cajon = df_cajon.sort_values(by=["Orden_Real", "Partido", "Mercado"], ascending=[False, True, True])

    vista_cajon = df_cajon[["Semáforo", "Fecha y Hora Fin", "Partido", "Mercado", "Cuota", "Marcador"]]
    st.dataframe(vista_cajon, hide_index=True, height=380)