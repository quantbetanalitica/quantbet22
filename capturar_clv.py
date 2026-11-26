"""
CAPTURADOR REAL DE CLV (CLOSING LINE VALUE) — QUANTBET22 (FASE 4 / v25.1)
=========================================================================
100% autónomo (solo usa requests + pandas): funciona igual en tu PC Windows
y en la nube 24/7 con GitHub Actions aunque tengas el ordenador apagado.

Funciones:
1. Consulta Kambi en vivo (espejos Europa + USA + Colombia) justo antes del pitazo inicial
   (ventana por defecto: 45 min antes hasta 2 min después del KO).
2. Guarda la cuota real de cierre en 'auditoria_apuestas.csv' (columna Cuota_Cierre_CLV)
   y en el histórico limpio 'registro_clv_real.csv' (incluyendo CLV% y CLV No-Vig%).
3. Envía una alerta privada resumida a tu Telegram móvil (Bot de Auditorías) con el
   movimiento exacto de cuotas (verde si batiste al mercado, rojo si cerró en contra).

Modos de uso:
  py capturar_clv.py                  -> Pasada única (ventana 45 min antes del KO + alerta Telegram)
  py capturar_clv.py --vigilar        -> Monitor continuo en PC cada 5 min
  py capturar_clv.py --reporte        -> Reporte acumulado (Global, FREE vs VIP, Mercados y Ligas)
  py capturar_clv.py --forzar         -> Captura inmediata de todos los pendientes futuros (test)
  py capturar_clv.py --sin-telegram   -> Ejecuta sin enviar mensaje a Telegram
  py capturar_clv.py --umbral-alerta=3.0 -> Solo avisa por Telegram si |CLV| >= 3.0%
"""

import csv
import difflib
import os
import re
import sys
import time
import unicodedata
from datetime import datetime, timedelta, timezone
import pandas as pd
import requests

if os.name == "nt":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ARCHIVO_AUDITORIA = "auditoria_apuestas.csv"
ARCHIVO_LOG_CLV = "registro_clv_real.csv"

# Bot privado de Auditorías (SOLO tu móvil personal, nunca canales de clientes)
TOKEN_TELEGRAM_CLV = os.getenv("TG_TOKEN_TICKETS", "8805035408:AAGPYUxmFz-Spfum1P2vacMZz5bToXUPMWI")
CHAT_ID_TELEGRAM_CLV = os.getenv("TG_CHAT_ID_AUDITORIAS", "1491740882")

COLUMNAS_LOG_CLV = [
    "Timestamp_Captura",
    "Fecha_Partido",
    "Hora_KO_ESP",
    "ID_Partido",
    "Partido",
    "Liga",
    "Nivel",
    "Mercado",
    "Cuota_Compra",
    "Cuota_Cierre",
    "CLV_Pct",
    "Cuota_Cierre_NoVig",
    "CLV_NoVig_Pct",
    "Minutos_Antes_KO",
    "Fuente",
]

_KAMBI_ACTIVE_CFG = None


def _hora_actual_esp():
    return datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1)


def _asegurar_log_clv():
    if not os.path.exists(ARCHIVO_LOG_CLV):
        with open(ARCHIVO_LOG_CLV, "w", newline="", encoding="utf-8") as f:
            csv.writer(f).writerow(COLUMNAS_LOG_CLV)


def _extraer_liga_de_partido(partido_str):
    m = re.search(r"\((.+)\)$", str(partido_str or "").strip())
    return m.group(1).strip() if m else "Otra"


def _extraer_nivel_y_mercado(mercado_raw):
    s = str(mercado_raw or "").strip()
    m = re.match(r"^\[(VIP|FREE|PRO)\]\s*(.+)$", s, flags=re.I)
    if m:
        return m.group(1).upper(), m.group(2).strip()
    return "OTRO", s


def _familia_mercado_clv(merc_limpio):
    n = str(merc_limpio or "").lower()
    if "remates" in n:
        return "Remates"
    if "córners" in n or "corners" in n:
        return "Córners"
    if "faltas" in n:
        return "Faltas"
    if "tarjetas" in n or "amarill" in n:
        return "Tarjetas"
    if "combo" in n:
        return "Combo"
    if "btts" in n or "ambos marcan" in n:
        return "BTTS"
    if "1t" in n or "2do tiempo" in n or "2t" in n:
        return "Tiempos (1T/2T)"
    if "asiático" in n or "asiatico" in n:
        return "Asiático"
    if "menos de" in n or "under" in n:
        return "Under Goles"
    if "over" in n and "goles" in n:
        return "Over Goles"
    if n.startswith("goles ") and ">" in n:
        return "Goles Equipo"
    if "1x" in n or "x2" in n or "victoria" in n or "sin empate" in n:
        return "Resultado/1X/X2/DNB"
    return "Otro"


# ==============================================================================
# CONECTOR KAMBI AUTÓNOMO MULTI-REGIÓN (EUROPA + USA + COLOMBIA)
# ==============================================================================
def _tokens_club(nombre):
    s = "".join(c for c in unicodedata.normalize("NFD", str(nombre or "").lower()) if unicodedata.category(c) != "Mn")
    s = re.sub(r"\((?:f|w|fem|women)\)", " ", s)
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    ign = {
        "fc", "sc", "cf", "ac", "as", "sk", "ud", "cd", "rcd", "ca", "se", "cr", "ce", "fk", "kv",
        "club", "deportivo", "deportes", "atletico", "stade", "real", "sporting", "united", "city",
        "women", "femenino", "fem", "ladies", "de", "la", "el", "los", "las", "29", "1907", "1913", "04", "05"
    }
    toks = [w for w in s.split() if len(w) >= 3 and w not in ign]
    return set(toks) if toks else set(s.split())


def _tokens_coinciden_seguro(ta, tb, min_pref=4):
    if not ta or not tb:
        return False
    if ("internacional" in ta and ("internazionale" in tb or "inter" in tb or "miami" in tb)) or (
        "internacional" in tb and ("internazionale" in ta or "inter" in ta or "miami" in ta)
    ):
        return False
    if ("miami" in ta and "miami" not in tb) or ("miami" in tb and "miami" not in ta):
        if ("inter" in ta or "internazionale" in ta) and ("inter" in tb or "internazionale" in tb):
            return False
    if ta & tb:
        return True
    bloq = {"inte", "real", "atle", "spor", "depo", "club", "unid", "unit", "sant"}
    for a in ta:
        if len(a) < min_pref or a[:4] in bloq:
            continue
        for b in tb:
            if len(b) < min_pref or b[:4] in bloq:
                continue
            if a[:min_pref] == b[:min_pref]:
                return True
    return False


def _es_evento_femenino(local_str, vis_str, grupo_str=""):
    txt = f" {local_str} {vis_str} {grupo_str} ".lower()
    return any(k in txt for k in ("(f)", "(w)", "women", "femenin", "ladies", "fem.", "wchampions"))


def _crear_info_vacio():
    return {
        "1": "N/A", "X": "N/A", "2": "N/A", "1X": None, "X2": None,
        "dnb_local": None, "dnb_visita": None, "btts_si": None, "over25": None,
        "fuente": "kambi",
        "over_goles": {}, "under_goles": {},
        "over_goles_1t": {}, "under_goles_1t": {},
        "over_goles_2t": {}, "under_goles_2t": {},
        "over_goles_local": {}, "over_goles_visita": {},
        "over_corners": {}, "under_corners": {},
        "over_corners_local": {}, "over_corners_visita": {},
        "over_tarjetas": {}, "under_tarjetas": {},
        "over_faltas": {}, "under_faltas": {},
        "over_remates": {}, "under_remates": {},
    }


def _parsear_ofertas_kambi(bet_offers, info_evento):
    toks_loc = _tokens_club(info_evento.get("local_bp", ""))
    toks_vis = _tokens_club(info_evento.get("visita_bp", ""))

    for oferta in (bet_offers or []):
        tipo_oferta = str((oferta.get("betOfferType") or {}).get("name") or "")
        tipo_low = tipo_oferta.lower()
        crit = oferta.get("criterion") or {}
        crit_lbl = f"{crit.get('label', '')} {crit.get('englishLabel', '')}".lower()
        outcomes = oferta.get("outcomes") or []

        if tipo_oferta == "Match" and len(outcomes) >= 3 and info_evento.get("1") == "N/A":
            try:
                info_evento["1"] = round(outcomes[0]["odds"] / 1000.0, 2)
                info_evento["X"] = round(outcomes[1]["odds"] / 1000.0, 2)
                info_evento["2"] = round(outcomes[2]["odds"] / 1000.0, 2)
            except Exception:
                pass
            continue

        if "double chance" in tipo_low or "doble oportunidad" in tipo_low or "double chance" in crit_lbl or "doble oportunidad" in crit_lbl:
            for out in outcomes:
                lbl = str(out.get("englishLabel") or out.get("label") or "").strip().upper()
                odd_r = out.get("odds")
                if odd_r:
                    o_dec = round(float(odd_r) / 1000.0, 2)
                    if lbl == "1X":
                        info_evento["1X"] = o_dec
                    elif lbl == "X2":
                        info_evento["X2"] = o_dec
            continue

        if any(k in crit_lbl or k in tipo_low for k in ("draw no bet", "sin empate", "empate no acci", "empate no v")):
            if not any(h in crit_lbl for h in ("1st", "2nd", "1.ª", "2.ª", "half", "parte", "tiempo")) and len(outcomes) >= 2:
                try:
                    o0, o1 = outcomes[0].get("odds"), outcomes[1].get("odds")
                    if o0 and o1:
                        info_evento["dnb_local"] = round(float(o0) / 1000.0, 2)
                        info_evento["dnb_visita"] = round(float(o1) / 1000.0, 2)
                except Exception:
                    pass
            continue

        if "both teams to score" in crit_lbl or "ambos equipos marcan" in crit_lbl or "ambos marcan" in crit_lbl:
            if not any(h in crit_lbl for h in ("1st", "2nd", "1.ª", "2.ª", "half", "parte", "tiempo")):
                for out in outcomes:
                    lbl = str(out.get("englishLabel") or out.get("label") or "").strip().lower()
                    odd_r = out.get("odds")
                    if odd_r and lbl in ("yes", "sí", "si"):
                        info_evento["btts_si"] = round(float(odd_r) / 1000.0, 2)
            continue

        if "over/under" not in tipo_low and "total" not in tipo_low:
            continue
        if any(k in crit_lbl for k in ("player", "jugador")):
            continue

        es_1t = any(k in crit_lbl for k in ("1st half", "first half", "1.ª parte", "1ª parte", "primer tiempo", "half time"))
        es_2t = any(k in crit_lbl for k in ("2nd half", "second half", "2.ª parte", "2ª parte", "segundo tiempo"))
        es_por_equipo = any(k in crit_lbl for k in (" by ", " por ", " de ", "home team", "away team", "equipo local", "equipo visitante"))

        toks_crit = _tokens_club(crit_lbl)
        es_equipo_loc = ("home" in crit_lbl or "local" in crit_lbl) or (bool(toks_loc & toks_crit) and not bool(toks_vis & toks_crit))
        es_equipo_vis = ("away" in crit_lbl or "visit" in crit_lbl) or (bool(toks_vis & toks_crit) and not bool(toks_loc & toks_crit))
        if es_equipo_loc or es_equipo_vis:
            es_por_equipo = True

        destino_over = None
        destino_under = None

        es_tiros = any(k in crit_lbl for k in ("shot on target", "shots on target", "tiros a puerta", "remates a puerta", "tiros al arco"))
        es_corners = any(k in crit_lbl for k in ("corner", "córner", "tiros de esquina", "saques de esquina"))
        es_faltas = any(k in crit_lbl for k in ("foul", "falta"))
        es_tarjetas = any(k in crit_lbl for k in ("card", "tarjeta", "amarill")) and "point" not in crit_lbl and "punto" not in crit_lbl
        es_goles = (not es_tiros and not es_corners and not es_faltas and not es_tarjetas) and (
            any(k in crit_lbl for k in ("goal", "gol")) or crit_lbl.strip() in ("", "total")
        )

        if es_goles:
            if es_1t and not es_por_equipo:
                destino_over, destino_under = info_evento["over_goles_1t"], info_evento["under_goles_1t"]
            elif es_2t and not es_por_equipo:
                destino_over, destino_under = info_evento["over_goles_2t"], info_evento["under_goles_2t"]
            elif es_por_equipo and not es_1t and not es_2t:
                destino_over = info_evento["over_goles_local"] if es_equipo_loc else (info_evento["over_goles_visita"] if es_equipo_vis else None)
            elif not es_1t and not es_2t and not es_por_equipo:
                destino_over, destino_under = info_evento["over_goles"], info_evento["under_goles"]
        elif es_tiros and not es_1t and not es_2t and not es_por_equipo:
            destino_over, destino_under = info_evento["over_remates"], info_evento["under_remates"]
        elif es_corners and not es_1t and not es_2t:
            if es_por_equipo:
                destino_over = info_evento["over_corners_local"] if es_equipo_loc else (info_evento["over_corners_visita"] if es_equipo_vis else None)
            else:
                destino_over, destino_under = info_evento["over_corners"], info_evento["under_corners"]
        elif es_faltas and not es_1t and not es_2t and not es_por_equipo:
            destino_over, destino_under = info_evento["over_faltas"], info_evento["under_faltas"]
        elif es_tarjetas and not es_1t and not es_2t and not es_por_equipo:
            destino_over, destino_under = info_evento["over_tarjetas"], info_evento["under_tarjetas"]

        if destino_over is None:
            continue

        for out in outcomes:
            linea_raw, odd_raw = out.get("line"), out.get("odds")
            if linea_raw is None or odd_raw is None:
                continue
            try:
                linea_val = round(float(linea_raw) / 1000.0, 2)
                odd_val = round(float(odd_raw) / 1000.0, 2)
            except Exception:
                continue
            if odd_val <= 1.01:
                continue
            lbl_out = str(out.get("englishLabel") or out.get("label") or "").lower()
            tipo_out = str(out.get("type") or "").upper()
            if "over" in lbl_out or "más" in lbl_out or "mas" in lbl_out or tipo_out == "OT_OVER":
                destino_over[linea_val] = odd_val
                if destino_over is info_evento["over_goles"] and abs(linea_val - 2.5) < 0.01:
                    info_evento["over25"] = odd_val
            elif destino_under is not None and ("under" in lbl_out or "menos" in lbl_out or tipo_out == "OT_UNDER"):
                destino_under[linea_val] = odd_val


def obtener_eventos_kambi_en_vivo():
    """Conecta a Kambi probando espejos de Europa, EE.UU. (para GitHub Actions) y Colombia."""
    global _KAMBI_ACTIVE_CFG
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
    }
    candidatos = [
        ("eu-offering-api.kambicdn.com", "ub", "ES", "es_ES"),
        ("eu-offering-api.kambicdn.com", "pafes", "ES", "es_ES"),
        ("eu-offering-api.kambicdn.com", "ubse", "SE", "es_ES"),
        ("eu-offering-api.kambicdn.com", "ubuk", "GB", "en_GB"),
        ("eu-offering-api.kambicdn.com", "rsi2uspa", "US", "en_US"),
        ("na-offering-api.kambicdn.com", "rsi2uspa", "US", "en_US"),
        ("eu-offering-api.kambicdn.com", "bpco", "CO", "es_ES"),
    ]
    rutas = ["listView/football/all/all/all/matches.json", "listView/football.json"]

    for host, op, mkt, lang in candidatos:
        for ruta_k in rutas:
            url = f"https://{host}/offering/v2018/{op}/{ruta_k}?lang={lang}&market={mkt}&client_id=2&channel_id=1&useCombined=true"
            try:
                res = requests.get(url, headers=headers, timeout=6.5)
                if res.status_code != 200:
                    continue
                eventos = (res.json() or {}).get("events") or []
                if not eventos:
                    continue
                mapa = {}
                for ev in eventos:
                    ev_d = ev.get("event") or {}
                    loc = str(ev_d.get("homeName") or "").strip()
                    vis = str(ev_d.get("awayName") or "").strip()
                    if not loc or not vis:
                        continue
                    info = _crear_info_vacio()
                    info["event_id"] = ev_d.get("id")
                    info["local_bp"] = loc
                    info["visita_bp"] = vis
                    info["grupo_bp"] = str(ev_d.get("group") or "")
                    info["es_femenino_bp"] = _es_evento_femenino(loc, vis, info["grupo_bp"])
                    info["fuente"] = f"kambi:{op}"
                    _parsear_ofertas_kambi(ev.get("betOffers"), info)
                    mapa[f"{loc.lower()} vs {vis.lower()}"] = info
                if mapa:
                    _KAMBI_ACTIVE_CFG = (host, op, mkt, lang)
                    print(f"    ✅ Kambi en vivo conectado vía '{op}' ({mkt}): {len(mapa)} partidos.")
                    return mapa
            except Exception:
                continue
    return {}


def buscar_evento_kambi_fresco(local, visitante, mapa_kambi, es_femenino=False):
    if not mapa_kambi:
        return None
    objetivo = f"{local.lower()} vs {visitante.lower()}"
    elegido = None
    if objetivo in mapa_kambi and bool(mapa_kambi[objetivo].get("es_femenino_bp")) == bool(es_femenino):
        elegido = mapa_kambi[objetivo]
    else:
        tl, tv = _tokens_club(local), _tokens_club(visitante)
        mejor_sc = 0
        for ev_inf in mapa_kambi.values():
            if bool(ev_inf.get("es_femenino_bp")) != bool(es_femenino):
                continue
            tl_k, tv_k = _tokens_club(ev_inf.get("local_bp", "")), _tokens_club(ev_inf.get("visita_bp", ""))
            if _tokens_coinciden_seguro(tl, tl_k, 4) and _tokens_coinciden_seguro(tv, tv_k, 4):
                sc = len(tl & tl_k) + len(tv & tv_k) + 1
                if sc > mejor_sc:
                    mejor_sc, elegido = sc, ev_inf
        if elegido is None:
            claves_g = [k for k, v in mapa_kambi.items() if bool(v.get("es_femenino_bp")) == bool(es_femenino)]
            cands = difflib.get_close_matches(objetivo, claves_g, n=1, cutoff=0.68)
            if cands:
                cand_ev = mapa_kambi[cands[0]]
                if _tokens_coinciden_seguro(tl, _tokens_club(cand_ev.get("local_bp", "")), 4) and _tokens_coinciden_seguro(tv, _tokens_club(cand_ev.get("visita_bp", "")), 4):
                    elegido = cand_ev

    if not elegido or not elegido.get("event_id"):
        return elegido

    # Consultar detalle FRESCO del evento en Kambi (nunca caché antiguo)
    host, op, mkt, lang = _KAMBI_ACTIVE_CFG or ("eu-offering-api.kambicdn.com", "ub", "ES", "es_ES")
    info_fresca = _crear_info_vacio()
    info_fresca["event_id"] = elegido["event_id"]
    info_fresca["local_bp"] = elegido.get("local_bp", local)
    info_fresca["visita_bp"] = elegido.get("visita_bp", visitante)
    info_fresca["fuente"] = elegido.get("fuente", f"kambi:{op}")
    try:
        url_det = f"https://{host}/offering/v2018/{op}/betoffer/event/{elegido['event_id']}.json?lang={lang}&market={mkt}&client_id=2&channel_id=1"
        r_d = requests.get(url_det, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"}, timeout=5.5)
        if r_d.status_code == 200:
            _parsear_ofertas_kambi((r_d.json() or {}).get("betOffers") or [], info_fresca)
            return info_fresca
    except Exception:
        pass
    return elegido


# ==============================================================================
# CÁLCULO NO-VIG Y EXTRACCIÓN EXACTA DE CUOTA DE CIERRE POR MERCADO
# ==============================================================================
def _calcular_cuota_novig_dos_lados(odd_objetivo, odd_opuesta):
    try:
        o1, o2 = float(odd_objetivo), float(odd_opuesta)
        if o1 <= 1.01 or o2 <= 1.01:
            return None
        inv1, inv2 = 1.0 / o1, 1.0 / o2
        p_real = inv1 / (inv1 + inv2)
        if p_real <= 0.01 or p_real >= 0.99:
            return None
        return round(1.0 / p_real, 3)
    except Exception:
        return None


def _calcular_cuota_novig_1x2(c1, cx, c2, lado):
    try:
        c1, cx, c2 = float(c1), float(cx), float(c2)
        if c1 <= 1.01 or cx <= 1.01 or c2 <= 1.01:
            return None
        i1, ix, i2 = 1.0 / c1, 1.0 / cx, 1.0 / c2
        s = i1 + ix + i2
        p1, px, p2 = i1 / s, ix / s, i2 / s
        mapa_p = {"1": p1, "2": p2, "1X": p1 + px, "X2": p2 + px, "DNB_1": p1 / max(p1 + p2, 1e-6), "DNB_2": p2 / max(p1 + p2, 1e-6)}
        p = mapa_p.get(lado)
        return round(1.0 / max(p, 0.01), 3) if p else None
    except Exception:
        return None


def extraer_cuota_cierre_mercado(mercado_limpio, info_kambi, local="", visitante=""):
    if not isinstance(info_kambi, dict):
        return None, None

    m = str(mercado_limpio or "").strip()
    m_low = m.lower()
    loc_low = str(local or "").strip().lower()
    vis_low = str(visitante or "").strip().lower()

    def _get_line(dic, lin_f):
        if not isinstance(dic, dict):
            return None
        for k, v in dic.items():
            try:
                if abs(float(k) - float(lin_f)) < 0.015:
                    return round(float(v), 2)
            except Exception:
                continue
        return None

    def _es_eq(frag, eq_low):
        fl = str(frag or "").strip().lower()
        return bool(fl and eq_low and (eq_low.startswith(fl) or fl in eq_low or (len(fl) >= 5 and fl[:5] in eq_low)))

    m_ov = re.match(r"^over\s+(\d+(?:\.\d+)?)\s+goles$", m_low)
    if m_ov:
        lin = float(m_ov.group(1))
        o_c, u_c = _get_line(info_kambi.get("over_goles"), lin), _get_line(info_kambi.get("under_goles"), lin)
        return o_c, _calcular_cuota_novig_dos_lados(o_c, u_c) if (o_c and u_c) else None

    m_un = re.search(r"menos\s+de\s+(\d+(?:\.\d+)?)", m_low)
    if m_un and not any(k in m_low for k in ("córner", "corner", "tarjeta", "falta", "remate")):
        lin = float(m_un.group(1))
        u_c, o_c = _get_line(info_kambi.get("under_goles"), lin), _get_line(info_kambi.get("over_goles"), lin)
        return u_c, _calcular_cuota_novig_dos_lados(u_c, o_c) if (u_c and o_c) else None

    if "btts" in m_low or "ambos marcan" in m_low:
        b = info_kambi.get("btts_si")
        return (round(float(b), 2), None) if isinstance(b, (int, float)) else (None, None)

    c1, cx, c2 = info_kambi.get("1"), info_kambi.get("X"), info_kambi.get("2")
    if "doble oport" in m_low and "1x" in m_low:
        o_1x = info_kambi.get("1X")
        return (round(float(o_1x), 2), _calcular_cuota_novig_1x2(c1, cx, c2, "1X")) if isinstance(o_1x, (int, float)) else (None, None)
    if "doble oport" in m_low and "x2" in m_low:
        o_x2 = info_kambi.get("X2")
        return (round(float(o_x2), 2), _calcular_cuota_novig_1x2(c1, cx, c2, "X2")) if isinstance(o_x2, (int, float)) else (None, None)

    if m_low.startswith("victoria "):
        frag = m[9:].strip()
        if _es_eq(frag, loc_low) and isinstance(c1, (int, float)):
            return round(float(c1), 2), _calcular_cuota_novig_1x2(c1, cx, c2, "1")
        if _es_eq(frag, vis_low) and isinstance(c2, (int, float)):
            return round(float(c2), 2), _calcular_cuota_novig_1x2(c1, cx, c2, "2")
        return None, None

    if m_low.startswith("sin empate "):
        frag = m[11:].strip()
        if _es_eq(frag, loc_low):
            dnb_l, nv = info_kambi.get("dnb_local"), _calcular_cuota_novig_1x2(c1, cx, c2, "DNB_1")
            if isinstance(dnb_l, (int, float)):
                return round(float(dnb_l), 2), nv
            if isinstance(c1, (int, float)) and isinstance(cx, (int, float)) and float(cx) > 1.05:
                return round(max(1.12, float(c1) * (1.0 - (1.0 / float(cx)))), 2), nv
        if _es_eq(frag, vis_low):
            dnb_v, nv = info_kambi.get("dnb_visita"), _calcular_cuota_novig_1x2(c1, cx, c2, "DNB_2")
            if isinstance(dnb_v, (int, float)):
                return round(float(dnb_v), 2), nv
            if isinstance(c2, (int, float)) and isinstance(cx, (int, float)) and float(cx) > 1.05:
                return round(max(1.12, float(c2) * (1.0 - (1.0 / float(cx)))), 2), nv
        return None, None

    if m_low == "gol en 1t":
        o_c, u_c = _get_line(info_kambi.get("over_goles_1t"), 0.5), _get_line(info_kambi.get("under_goles_1t"), 0.5)
        return o_c, _calcular_cuota_novig_dos_lados(o_c, u_c) if (o_c and u_c) else None
    if m_low.startswith("goles 1t >"):
        lin = float(m.split(">")[1].strip())
        o_c, u_c = _get_line(info_kambi.get("over_goles_1t"), lin), _get_line(info_kambi.get("under_goles_1t"), lin)
        return o_c, _calcular_cuota_novig_dos_lados(o_c, u_c) if (o_c and u_c) else None
    if m_low == "gol en 2do tiempo":
        o_c, u_c = _get_line(info_kambi.get("over_goles_2t"), 0.5), _get_line(info_kambi.get("under_goles_2t"), 0.5)
        return o_c, _calcular_cuota_novig_dos_lados(o_c, u_c) if (o_c and u_c) else None
    if "2do tiempo >" in m_low or "2t >" in m_low:
        lin = float(m.split(">")[1].strip())
        o_c, u_c = _get_line(info_kambi.get("over_goles_2t"), lin), _get_line(info_kambi.get("under_goles_2t"), lin)
        return o_c, _calcular_cuota_novig_dos_lados(o_c, u_c) if (o_c and u_c) else None

    m_ge = re.match(r"^goles\s+(.+?)\s*>\s*(\d+(?:\.\d+)?)$", m, flags=re.I)
    if m_ge:
        frag, lin = m_ge.group(1), float(m_ge.group(2))
        if _es_eq(frag, loc_low):
            return _get_line(info_kambi.get("over_goles_local"), lin), None
        if _es_eq(frag, vis_low):
            return _get_line(info_kambi.get("over_goles_visita"), lin), None
        return None, None

    m_ct = re.match(r"^c[óo]rners\s*>\s*(\d+(?:\.\d+)?)$", m, flags=re.I)
    if m_ct:
        lin = float(m_ct.group(1))
        o_c, u_c = _get_line(info_kambi.get("over_corners"), lin), _get_line(info_kambi.get("under_corners"), lin)
        return o_c, _calcular_cuota_novig_dos_lados(o_c, u_c) if (o_c and u_c) else None
    m_ce = re.match(r"^c[óo]rners\s+(.+?)\s*>\s*(\d+(?:\.\d+)?)$", m, flags=re.I)
    if m_ce:
        frag, lin = m_ce.group(1), float(m_ce.group(2))
        if _es_eq(frag, loc_low):
            return _get_line(info_kambi.get("over_corners_local"), lin), None
        if _es_eq(frag, vis_low):
            return _get_line(info_kambi.get("over_corners_visita"), lin), None
        return None, None

    m_rem = re.match(r"^remates\s+puerta\s*>\s*(\d+(?:\.\d+)?)$", m, flags=re.I)
    if m_rem:
        lin = float(m_rem.group(1))
        o_c, u_c = _get_line(info_kambi.get("over_remates"), lin), _get_line(info_kambi.get("under_remates"), lin)
        return o_c, _calcular_cuota_novig_dos_lados(o_c, u_c) if (o_c and u_c) else None

    m_fal = re.match(r"^faltas\s+totales\s*>\s*(\d+(?:\.\d+)?)$", m, flags=re.I)
    if m_fal:
        lin = float(m_fal.group(1))
        o_c, u_c = _get_line(info_kambi.get("over_faltas"), lin), _get_line(info_kambi.get("under_faltas"), lin)
        return o_c, _calcular_cuota_novig_dos_lados(o_c, u_c) if (o_c and u_c) else None

    m_tar = re.match(r"^tarjetas\s*>\s*(\d+(?:\.\d+)?)$", m, flags=re.I)
    if m_tar:
        lin = float(m_tar.group(1))
        o_c, u_c = _get_line(info_kambi.get("over_tarjetas"), lin), _get_line(info_kambi.get("under_tarjetas"), lin)
        return o_c, _calcular_cuota_novig_dos_lados(o_c, u_c) if (o_c and u_c) else None

    return None, None


def calcular_clv_pct(cuota_compra, cuota_cierre):
    try:
        cc, cl = float(cuota_compra), float(cuota_cierre)
        if cc <= 1.0 or cl <= 1.0:
            return None
        return round(((cc / cl) - 1.0) * 100.0, 2)
    except Exception:
        return None


def enviar_alerta_clv_telegram(items_capturados, umbral_abs_pct=0.0):
    """Envía 1 solo mensaje privado agrupado a tu móvil por Telegram con los movimientos reales de CLV."""
    if not items_capturados or not TOKEN_TELEGRAM_CLV or not CHAT_ID_TELEGRAM_CLV:
        return False

    filtrados = [it for it in items_capturados if abs(float(it["clv_pct"])) >= float(umbral_abs_pct)]
    if not filtrados:
        return False

    clv_med = sum(float(x["clv_pct"]) for x in filtrados) / len(filtrados)
    beat_n = sum(1 for x in filtrados if float(x["clv_pct"]) > 0)
    origen = "☁️ Nube 24/7" if os.getenv("GITHUB_ACTIONS") else "💻 PC Local"
    ahora_s = _hora_actual_esp().strftime("%H:%M")

    lineas = [
        f"📡 <b>ALERTA CLV REAL ({ahora_s}h ESP | {origen})</b>",
        f"📊 <b>CLV Medio del lote:</b> <b>{clv_med:+.2f}%</b> ({beat_n}/{len(filtrados)} baten al cierre)",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━",
    ]
    for it in filtrados[:20]:
        clv_v = float(it["clv_pct"])
        if clv_v >= 3.0:
            ico = "🔥🟢"
        elif clv_v > 0:
            ico = "🟢"
        elif clv_v <= -3.0:
            ico = "⚠️🔴"
        elif clv_v < 0:
            ico = "🔴"
        else:
            ico = "⚪"
        nv_str = f" | NoVig: {float(it['clv_nv']):+.1f}%" if it.get("clv_nv") not in (None, "") else ""
        lineas.append(
            f"{ico} <b>[{it['nivel']}] {it['duelo']}</b> (KO {it['mins_ko']:.0f}m)\n"
            f"   • {it['mercado']}: <code>{it['compra']:.2f}</code> ➔ <code>{it['cierre']:.2f}</code> (<b>CLV {clv_v:+.2f}%</b>{nv_str})"
        )

    texto = "\n".join(lineas)
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TOKEN_TELEGRAM_CLV}/sendMessage",
            json={"chat_id": CHAT_ID_TELEGRAM_CLV, "text": texto[:3950], "parse_mode": "HTML", "disable_web_page_preview": True},
            timeout=10,
        )
        if r.status_code == 200:
            print(f"    📲 [TELEGRAM OK] Alerta CLV enviada a tu móvil ({len(filtrados)} picks).")
            return True
    except Exception as e:
        print(f"    ⚠️ Error enviando alerta CLV por Telegram: {e}")
    return False


def capturar_clv_pendientes(ventana_min=45, forzar=False, enviar_tg=True, umbral_alerta=0.0, ruta_csv=ARCHIVO_AUDITORIA):
    if not os.path.exists(ruta_csv):
        print(f"[!] No se encontró {ruta_csv}.")
        return 0

    df = pd.read_csv(ruta_csv, dtype=str)
    if df.empty or "Estado" not in df.columns or "Cuota_Cierre_CLV" not in df.columns:
        print("[!] El CSV no tiene las columnas esperadas.")
        return 0

    ahora_esp = _hora_actual_esp()
    candidatos_idx = []
    for idx, row in df.iterrows():
        if str(row.get("Estado", "")).strip() != "Pendiente":
            continue
        clv_act = str(row.get("Cuota_Cierre_CLV", "")).strip().upper()
        if clv_act not in ("", "PENDIENTE_CLV", "NAN", "NONE"):
            continue
        f_reg = str(row.get("Fecha_Registro", "")).strip()
        try:
            dt_fin = datetime.strptime(f_reg[:16], "%Y-%m-%d %H:%M")
            dt_ko = dt_fin - timedelta(hours=1, minutes=55)
        except Exception:
            continue

        mins_para_ko = (dt_ko - ahora_esp).total_seconds() / 60.0
        if forzar:
            if mins_para_ko >= -2:
                candidatos_idx.append((idx, dt_ko, mins_para_ko))
        else:
            if -2.0 <= mins_para_ko <= float(ventana_min):
                candidatos_idx.append((idx, dt_ko, mins_para_ko))

    if not candidatos_idx:
        print(f"[{ahora_esp.strftime('%H:%M')}h ESP] Sin partidos pendientes en la ventana de cierre ({ventana_min} min antes del KO).")
        return 0

    print(f"[{ahora_esp.strftime('%H:%M')}h ESP] 🎯 {len(candidatos_idx)} pick(s) pendientes para captura de cierre Kambi...")
    mapa_kambi = obtener_eventos_kambi_en_vivo()
    if not mapa_kambi:
        print("    ⚠️ Ningún espejo de Kambi devolvió eventos en este momento.")
        return 0

    _asegurar_log_clv()
    cache_ev = {}
    capturados = 0
    filas_log = []
    resumen_tg = []

    for idx, dt_ko, mins_ko in candidatos_idx:
        row = df.loc[idx]
        part_full = str(row.get("Partido", "")).strip()
        duelo = part_full.split(" (")[0].strip()
        if " vs " not in duelo:
            continue
        loc, vis = [x.strip() for x in duelo.split(" vs ", 1)]
        liga = _extraer_liga_de_partido(part_full)
        es_fem = ("women" in part_full.lower()) or ("femen" in part_full.lower())

        clave_ev = (loc.lower(), vis.lower(), es_fem)
        if clave_ev not in cache_ev:
            cache_ev[clave_ev] = buscar_evento_kambi_fresco(loc, vis, mapa_kambi, es_femenino=es_fem)
            time.sleep(0.12)

        info_k = cache_ev[clave_ev]
        if not info_k:
            continue
        nivel, merc_limpio = _extraer_nivel_y_mercado(row.get("Mercado", ""))
        cuo_cierre, cuo_novig = extraer_cuota_cierre_mercado(merc_limpio, info_k, local=loc, visitante=vis)
        if cuo_cierre is None:
            continue

        try:
            cuo_compra = float(row.get("Cuota_Compra", 0))
        except Exception:
            continue
        clv_pct = calcular_clv_pct(cuo_compra, cuo_cierre)
        clv_nv_pct = calcular_clv_pct(cuo_compra, cuo_novig) if cuo_novig else ""
        if clv_pct is None:
            continue

        df.at[idx, "Cuota_Cierre_CLV"] = f"{cuo_cierre:.2f}"
        capturados += 1

        ico = "🟢" if clv_pct > 0 else ("⚪" if clv_pct == 0 else "🔴")
        print(f"    {ico} [{nivel}] {duelo} | {merc_limpio}: Compra {cuo_compra:.2f} -> Cierre {cuo_cierre:.2f} | CLV {clv_pct:+.2f}% (KO {mins_ko:.0f}m)")

        resumen_tg.append({
            "nivel": nivel, "duelo": duelo, "mercado": merc_limpio,
            "compra": cuo_compra, "cierre": cuo_cierre, "clv_pct": clv_pct,
            "clv_nv": clv_nv_pct, "mins_ko": mins_ko,
        })
        filas_log.append([
            ahora_esp.strftime("%Y-%m-%d %H:%M:%S"),
            dt_ko.strftime("%Y-%m-%d"),
            dt_ko.strftime("%H:%M"),
            str(row.get("ID_Partido", "")).strip(),
            part_full,
            liga,
            nivel,
            merc_limpio,
            f"{cuo_compra:.2f}",
            f"{cuo_cierre:.2f}",
            f"{clv_pct:.2f}",
            f"{cuo_novig:.3f}" if cuo_novig else "",
            f"{clv_nv_pct:.2f}" if clv_nv_pct != "" else "",
            f"{mins_ko:.1f}",
            str(info_k.get("fuente", "kambi")),
        ])

    if capturados > 0:
        df.to_csv(ruta_csv, index=False)
        with open(ARCHIVO_LOG_CLV, "a", newline="", encoding="utf-8") as f:
            csv.writer(f).writerows(filas_log)
        print(f"[✅] {capturados} cuota(s) de cierre guardadas en {ruta_csv} y {ARCHIVO_LOG_CLV}.")
        if enviar_tg:
            enviar_alerta_clv_telegram(resumen_tg, umbral_abs_pct=umbral_alerta)
    else:
        print("[i] Ningún pick de la ventana tenía línea abierta en Kambi en esta pasada.")

    return capturados


def imprimir_reporte_clv(ruta_log=ARCHIVO_LOG_CLV):
    if not os.path.exists(ruta_log):
        print(f"[i] Todavía no existe {ruta_log}. Ejecuta primero 'py capturar_clv.py' antes de los partidos.")
        return
    df_clv = pd.read_csv(ruta_log)
    if df_clv.empty:
        print(f"[i] {ruta_log} no tiene registros todavía.")
        return
    df_clv["CLV_Pct"] = pd.to_numeric(df_clv["CLV_Pct"], errors="coerce")
    df_clv["CLV_NoVig_Pct"] = pd.to_numeric(df_clv.get("CLV_NoVig_Pct"), errors="coerce")
    df_clv = df_clv.dropna(subset=["CLV_Pct"]).copy()
    if df_clv.empty:
        print("[i] No hay registros numéricos válidos de CLV todavía.")
        return

    df_clv["Familia"] = df_clv["Mercado"].apply(_familia_mercado_clv)
    n_tot = len(df_clv)
    clv_med = df_clv["CLV_Pct"].mean()
    pct_beat = (df_clv["CLV_Pct"] > 0).mean() * 100.0
    nv_valid = df_clv["CLV_NoVig_Pct"].dropna()
    nv_txt = f" | CLV No-Vig Medio: {nv_valid.mean():+.2f}% (N={len(nv_valid)})" if len(nv_valid) > 0 else ""

    print("\n" + "=" * 95)
    print(f" 📈 REPORTE DE CLV REAL (CLOSING LINE VALUE) — QUANTBET22 | N={n_tot} PICKS CAPTURADOS")
    print("=" * 95)
    print(f"  • CLV Medio Global     : {clv_med:+.2f}%{nv_txt}")
    print(f"  • % Picks que baten CLV: {pct_beat:.1f}% ({int((df_clv['CLV_Pct'] > 0).sum())}/{n_tot})")

    print("\n--- POR NIVEL (FREE vs VIP) ---")
    print(df_clv.groupby("Nivel").agg(N=("CLV_Pct", "count"), CLV_Medio=("CLV_Pct", "mean"), Beat_CLV_Pct=("CLV_Pct", lambda s: (s > 0).mean() * 100.0)).round(2).to_string())

    print("\n--- POR FAMILIA DE MERCADO ---")
    print(df_clv.groupby("Familia").agg(N=("CLV_Pct", "count"), CLV_Medio=("CLV_Pct", "mean"), Beat_CLV_Pct=("CLV_Pct", lambda s: (s > 0).mean() * 100.0)).round(2).sort_values("CLV_Medio", ascending=False).to_string())

    print("\n--- POR COMPETICIÓN ---")
    print(df_clv.groupby("Liga").agg(N=("CLV_Pct", "count"), CLV_Medio=("CLV_Pct", "mean"), Beat_CLV_Pct=("CLV_Pct", lambda s: (s > 0).mean() * 100.0)).round(2).sort_values("CLV_Medio", ascending=False).to_string())
    print("=" * 95 + "\n")


def vigilar_clv_continuo(intervalo_seg=300, ventana_min=45, enviar_tg=True, umbral_alerta=0.0):
    print(f"[🛰️ MONITOR CLV ACTIVO] Revisando cada {intervalo_seg // 60} min (ventana {ventana_min} min antes del KO | Telegram={'ON' if enviar_tg else 'OFF'})...")
    while True:
        try:
            capturar_clv_pendientes(ventana_min=ventana_min, forzar=False, enviar_tg=enviar_tg, umbral_alerta=umbral_alerta)
        except KeyboardInterrupt:
            print("\n[⏹️] Monitor CLV detenido.")
            break
        except Exception as e:
            print(f"    ⚠️ Error en ciclo CLV: {e}")
        try:
            time.sleep(intervalo_seg)
        except KeyboardInterrupt:
            print("\n[⏹️] Monitor CLV detenido.")
            break


if __name__ == "__main__":
    if "--reporte" in sys.argv:
        imprimir_reporte_clv()
        sys.exit(0)

    ventana = 45
    umbral_alerta = 0.0
    for arg in sys.argv[1:]:
        if arg.startswith("--ventana="):
            try:
                ventana = max(5, int(arg.split("=")[1]))
            except Exception:
                pass
        elif arg.startswith("--umbral-alerta="):
            try:
                umbral_alerta = max(0.0, float(arg.split("=")[1]))
            except Exception:
                pass

    enviar_tg = "--sin-telegram" not in sys.argv
    if "--vigilar" in sys.argv:
        vigilar_clv_continuo(intervalo_seg=300, ventana_min=ventana, enviar_tg=enviar_tg, umbral_alerta=umbral_alerta)
    else:
        capturar_clv_pendientes(ventana_min=ventana, forzar=("--forzar" in sys.argv), enviar_tg=enviar_tg, umbral_alerta=umbral_alerta)
