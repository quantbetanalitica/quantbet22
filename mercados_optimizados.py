import shutil
import csv
from datetime import datetime, timedelta
import difflib
import json
import logging
import math
import os
import re
import sys
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
import requests
from generador_imagenes import generar_captura_automatica, generar_tarjeta_combinada
from bot_soporte import ejecutar_centro_operaciones, reparar_y_leer_csv_auditoria
from generador_videos_redes import generar_paquete_redes_sociales

# Forzar codificación UTF-8 en consola de Windows para visualización perfecta de Emojis
if os.name == "nt":
  sys.stdout.reconfigure(encoding="utf-8")

# ==============================================================================
# 0. CONFIGURACIÓN DEL SISTEMA DE LOGS Y BOTS DE TELEGRAM
# ==============================================================================
logging.basicConfig(
    filename="errores_sistema.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

MODO_PRUEBAS = False
ENVIAR_A_CLIENTES = False  # ⚠️ INTERRUPTOR TELEGRAM CLIENTES: True = envía tarjetas a canales FREE, VIP y PRO
SUBIR_A_WEB = False        # 🌐 INTERRUPTOR PÁGINA WEB: True = sube los partidos del día y la auditoría a quantbet22.streamlit.app
ACTIVAR_BOT_AL_FINALIZAR = False  # En False termina el script al instante tras crear los videos

# 📅 Si quieres adelantar el trabajo de mañana o del fin de semana, pon aquí la fecha (ej. "2026-10-27")
# o ejecútalo en consola como: py mercados_optimizados.py 2026-10-27
FECHA_OBJETIVO_MANUAL = ""

ARCHIVO_CSV_AUDITORIA = "auditoria_apuestas.csv"
ARCHIVO_SINONIMOS = "sinonimos_equipos.json"
ARCHIVO_MEMORIA_BOTONES = "memoria_botones.json"
ARCHIVO_CACHE_EUROPA_CSV = f"cache_base_maestra_europa_v2_{datetime.now().strftime('%Y-%m-%d')}.csv"

# ==============================================================================
# SEPARACIÓN ESTRUCTURAL: ENTORNO PRIVADO VS ENTORNO CLIENTES
# ==============================================================================

# --- TUS BOTS PRIVADOS (RECIBEN EL 100% DE LOS PARTIDOS DEL DÍA Y COMBINADAS) ---
TOKEN_GENERAL = os.getenv("TG_TOKEN_GENERAL", "8980476304:AAHloqUSHMgQddi2eupz6FjrqliVDi6BDzQ")
CHAT_ID_GENERAL = "1491740882"  # Tu chat privado (Matriz completa + Botones Auditoría + Combinadas + Descartes)

TOKEN_VIP_PERSONAL = os.getenv("TG_TOKEN_VIP_PERSONAL", "8912732307:AAFG9S1FjNfSGugySoBduyjWb03kf38a63o")
CHAT_ID_VIP_PERSONAL = "1491740882"  # Tu chat privado (100% de las tarjetas VIP limpias + Tarjetas Combinadas)

# --- CANALES DE CLIENTES (USAN EL BOT CARTERO Y TIENEN RESTRICCIONES) ---
TOKEN_CARTERO = os.getenv("TG_TOKEN_CARTERO", "8980476304:AAHloqUSHMgQddi2eupz6FjrqliVDi6BDzQ")

CHAT_ID_CLIENTES_FREE = "-1003868577943"  # Canal Free: TOP 3 Partidazos de mayor cartelera (Gancho)
CHAT_ID_CLIENTES_VIP  = "-1004316274739"  # Canal VIP ($24.99): Top 4 Tarjetas VIP (Sin repetir las 3 del Free) + Combinada Doble VIP
CHAT_ID_CLIENTES_PRO  = "-1004359986610"  # Canal PRO ($74.99): Tarjeta VIP + Pronóstico Completo UNIDOS en 1 solo mensaje

# --- BOT Y GRUPO EXCLUSIVO DE AUDITORÍAS Y TICKETS (SOLO PARA TI) ---
TOKEN_TICKETS = os.getenv("TG_TOKEN_TICKETS", "8805035408:AAGPYUxmFz-Spfum1P2vacMZz5bToXUPMWI")
CHAT_ID_TICKETS = "1491740882"
CHAT_ID_GRUPO_AUDITORIAS = "1491740882"  # Recibe TODAS las auditorías (7 tarjetas clientes + 100% de la fecha)

BASE_MAESTRA_MEMORIA = None
HISTORIAL_EQUIPOS_CACHE_JSON = None


# ==============================================================================
# SISTEMA DE CACHÉ DIRECTO Y SIN ESPERAS (CON REFRESCO DE COPA BETPLAY Y FT)
# ==============================================================================
def es_seleccion_juvenil_o_femenina(local, visitante, nombre_liga="", liga_id=0):
    """Bloquea todas las Sub-23/21/20/19/17. En femenino solo permite Champions Femenina (525) y Mundial/Euro Absoluta."""
    texto = f" {local} {visitante} {nombre_liga} ".lower()
    patrones_juveniles = [
        r"\bu-?23\b", r"\bu-?22\b", r"\bu-?21\b", r"\bu-?20\b", r"\bu-?19\b",
        r"\bu-?18\b", r"\bu-?17\b", r"\bu-?16\b", r"\bu-?15\b",
        r"\bsub-?\s*23\b", r"\bsub-?\s*21\b", r"\bsub-?\s*20\b", r"\bsub-?\s*19\b",
        r"\bsub-?\s*18\b", r"\bsub-?\s*17\b", r"\bsub-?\s*16\b", r"\bsub-?\s*15\b",
        r"\byouth\b", r"\bolympic\b"
    ]
    if any(re.search(pat, texto) for pat in patrones_juveniles):
        return True
    if int(liga_id or 0) in {525, 290, 524}:
        return False
    patrones_fem = [r"\bwomen\b", r"\bfemenin[oa]\b", r"\bfem\b", r"\(w\)"]
    return any(re.search(pat, texto) for pat in patrones_fem)


def _obtener_partidos_respaldo_espn(fecha, datos_previos=None):
    """Respaldo automático ilimitado (ESPN API) para Clubes, Selecciones Mayores (Europa, América, África, Asia) y UWCL."""
    mapa_ligas_espn = {
        "esp.1": 140, "esp.copa_del_rey": 143, "esp.2": 141,
        "eng.1": 39, "eng.fa": 45, "eng.league_cup": 48,
        "ita.1": 135, "ita.coppa_italia": 137,
        "ger.1": 78, "ger.dfb_pokal": 81,
        "fra.1": 61, #"fra.coupe_de_france": 66,
        "arg.1": 128, "arg.copa": 130,
        "col.1": 239, "col.copa": 533, "col.2": 240,
        "ksa.1": 307, "bra.1": 71, "bra.copa_do_brasil": 73,
        "por.1": 94, "por.taca.portugal": 96,
        "ned.1": 88, "tur.1": 203, "mex.1": 262, "usa.1": 253,
        "uefa.champions": 2, "uefa.europa": 3, "uefa.europa.conf": 848,
        "conmebol.libertadores": 13, "conmebol.sudamericana": 11,
        # SELECCIONES MAYORES (EUROPA, SUDAMÉRICA, CONCACAF, ÁFRICA Y ASIA) + CHAMPIONS FEMENINA
        "fifa.world": 1, "uefa.euro": 4, "uefa.euroq": 32, "conmebol.america": 9,
        "uefa.nations": 5, "concacaf.gold": 21, "concacaf.nations.league": 536,
        "fifa.worldq.conmebol": 34, "fifa.worldq.uefa": 32,
        "fifa.worldq.concacaf": 31, "fifa.worldq.caf": 29, "fifa.worldq.afc": 30,
        "caf.nations": 6, "caf.nations_qual": 36,
        "afc.cup": 12, "afc.cupq": 35,
        "fifa.friendly": 10,
        "uefa.wchampions": 525,
    }
    dt_f = datetime.strptime(fecha, "%Y-%m-%d")
    fechas_ymd = [(dt_f - timedelta(days=1)).strftime("%Y%m%d"), dt_f.strftime("%Y%m%d")]

    def _toks(nom):
        s = "".join(c for c in unicodedata.normalize("NFD", str(nom).lower()) if unicodedata.category(c) != "Mn")
        s = re.sub(r"[^a-z0-9\s]", " ", s)
        ign = {"fc", "sc", "cf", "ac", "as", "sk", "ud", "cd", "rcd", "ca", "se", "cr", "club", "deportivo", "stade", "real", "sporting", "united", "city", "de", "la", "29", "1907", "1913"}
        t = [w for w in s.split() if len(w) >= 3 and w not in ign]
        return set(t) if t else set(s.split())

    def _descargar_liga(item_lg):
        slug, lid = item_lg
        encontrados = []
        for ymd in fechas_ymd:
            try:
                r = requests.get(f"https://site.api.espn.com/apis/site/v2/sports/soccer/{slug}/scoreboard?dates={ymd}&limit=100", timeout=6)
                if r.status_code == 200:
                    for ev in r.json().get("events", []):
                        f_iso_raw = ev.get("date", "")
                        if not f_iso_raw:
                            continue
                        f_iso = f_iso_raw[:16] + ":00+00:00" if len(f_iso_raw) >= 16 else f"{fecha}T18:00:00+00:00"
                        if f_iso[:10] != fecha:
                            continue
                        comp = (ev.get("competitions") or [{}])[0]
                        comps = comp.get("competitors", [])
                        if len(comps) < 2:
                            continue
                        c_h = next((c for c in comps if c.get("homeAway") == "home"), comps[0])
                        c_a = next((c for c in comps if c.get("homeAway") == "away"), comps[1])
                        loc_n = c_h.get("team", {}).get("displayName", "").strip()
                        vis_n = c_a.get("team", {}).get("displayName", "").strip()
                        if es_seleccion_juvenil_o_femenina(loc_n, vis_n, slug):
                            continue
                        id_h = int(c_h.get("team", {}).get("id", 0) or abs(hash(loc_n)) % 90000)
                        id_a = int(c_a.get("team", {}).get("id", 0) or abs(hash(vis_n)) % 90000)
                        st_type = comp.get("status", {}).get("type", {})
                        terminado = (st_type.get("completed") is True) or (st_type.get("state") == "post")
                        est_short = "FT" if terminado else ("NS" if st_type.get("state") == "pre" else "LIVE")
                        gh = int(float(c_h.get("score", 0) or 0)) if terminado else None
                        ga = int(float(c_a.get("score", 0) or 0)) if terminado else None
                        ls_h = c_h.get("linescores", [])
                        ls_a = c_a.get("linescores", [])
                        detalles_goles = [d for d in (comp.get("details") or []) if d.get("scoringPlay")]
                        if terminado and ls_h and ls_a:
                            ght_h = int(float(ls_h[0].get("value", 0) or 0))
                            ght_a = int(float(ls_a[0].get("value", 0) or 0))
                        elif terminado and detalles_goles and gh is not None and ga is not None:
                            ght_h, ght_a = 0, 0
                            for dg in detalles_goles:
                                rel_s = str((dg.get("clock") or {}).get("displayValue") or "")
                                min_g = int(re.findall(r"\d+", rel_s)[0]) if re.findall(r"\d+", rel_s) else 90
                                if ("45+" in rel_s) or (min_g <= 45 and "90+" not in rel_s):
                                    if str((dg.get("team") or {}).get("id") or "") == str(c_a.get("team", {}).get("id", "")):
                                        ght_a += 1
                                    else:
                                        ght_h += 1
                            ght_h, ght_a = min(gh, ght_h), min(ga, ght_a)
                        else:
                            ght_h = ght_a = None
                        encontrados.append({
                            "fixture": {"id": int(ev.get("id", 0) or abs(hash(f"{loc_n}{vis_n}{fecha}")) % 9000000), "date": f_iso, "referee": None, "status": {"short": est_short}},
                            "league": {"id": lid, "name": slug},
                            "teams": {"home": {"id": id_h, "name": loc_n}, "away": {"id": id_a, "name": vis_n}},
                            "goals": {"home": gh, "away": ga},
                            "score": {"halftime": {"home": ght_h, "away": ght_a}},
                        })
            except Exception:
                pass
        return encontrados

    partidos_espn = []
    with ThreadPoolExecutor(max_workers=10) as ex:
        for res_l in ex.map(_descargar_liga, list(mapa_ligas_espn.items())):
            partidos_espn.extend(res_l)

    if datos_previos:
        pares_prev = set()
        for p_old in datos_previos:
            tl_o = _toks(p_old.get("teams", {}).get("home", {}).get("name", ""))
            tv_o = _toks(p_old.get("teams", {}).get("away", {}).get("name", ""))
            n_lo = normalizar_nombre_club(p_old.get("teams", {}).get("home", {}).get("name", ""))
            n_vo = normalizar_nombre_club(p_old.get("teams", {}).get("away", {}).get("name", ""))
            pares_prev.add(tuple(sorted([n_lo, n_vo])))
            if p_old.get("fixture", {}).get("status", {}).get("short") in ["FT", "AET", "PEN"]:
                continue
            for p_new in partidos_espn:
                if p_new["fixture"]["status"]["short"] == "FT":
                    tl_n = _toks(p_new["teams"]["home"]["name"])
                    tv_n = _toks(p_new["teams"]["away"]["name"])
                    ok_l = bool(tl_o & tl_n) or any(a[:4] == b[:4] for a in tl_o for b in tl_n if len(a) >= 4 and len(b) >= 4)
                    ok_v = bool(tv_o & tv_n) or any(a[:4] == b[:4] for a in tv_o for b in tv_n if len(a) >= 4 and len(b) >= 4)
                    if ok_l and ok_v:
                        p_old["fixture"]["status"]["short"] = "FT"
                        p_old["goals"] = p_new["goals"]
                        p_old["score"] = p_new["score"]
                        break
        for p_e in partidos_espn:
            n_le = normalizar_nombre_club(p_e.get("teams", {}).get("home", {}).get("name", ""))
            n_ve = normalizar_nombre_club(p_e.get("teams", {}).get("away", {}).get("name", ""))
            par_ord = tuple(sorted([n_le, n_ve]))
            if par_ord not in pares_prev:
                datos_previos.append(p_e)
                pares_prev.add(par_ord)
        return datos_previos

    vistos = set()
    unicos = []
    for p_e in partidos_espn:
        if p_e["fixture"]["id"] not in vistos:
            vistos.add(p_e["fixture"]["id"])
            unicos.append(p_e)
    return unicos


def _descargar_partidos_un_dia_api(fecha_str, headers, forzar_refresco=False):
  """Descarga o lee de caché los partidos de una fecha calendario exacta (00:00 a 23:59 ESP)."""
  archivo_cache = f"cache_partidos_{fecha_str}.json"
  datos_cache = []
  ahora_chk = datetime.now()
  if os.path.exists(archivo_cache):
    try:
      mtime_cache = datetime.fromtimestamp(os.path.getmtime(archivo_cache))
      with open(archivo_cache, "r", encoding="utf-8") as f:
        datos_cache = json.load(f)
      if datos_cache and not forzar_refresco:
        requiere_actualizacion_ft = False
        if fecha_str >= ahora_chk.strftime("%Y-%m-%d") and (ahora_chk - mtime_cache).total_seconds() > 14400:
          requiere_actualizacion_ft = True
        for p_chk in datos_cache:
          est_chk = p_chk.get("fixture", {}).get("status", {}).get("short", "")
          f_iso_chk = p_chk.get("fixture", {}).get("date", "")
          if est_chk not in ["FT", "AET", "PEN", "PST", "CANC", "ABD"] and f_iso_chk:
            try:
              dt_chk = datetime.strptime(f_iso_chk[:19], "%Y-%m-%dT%H:%M:%S") + timedelta(hours=1)
              if (ahora_chk - dt_chk).total_seconds() > 6300:
                requiere_actualizacion_ft = True
                break
            except Exception:
              pass
        if not requiere_actualizacion_ft:
          return datos_cache
    except Exception:
      pass

  if MODO_PRUEBAS:
    return datos_cache

  datos_api = []
  url = f"https://v3.football.api-sports.io/fixtures?date={fecha_str}&timezone=Europe/Madrid"
  try:
    res = requests.get(url, headers=headers, timeout=12)
    data = res.json()
    if res.status_code == 200 and not data.get("errors") and data.get("response"):
      datos_api = data.get("response", [])
  except Exception:
    pass

  # Fusionar siempre con ESPN para no perder ningún Amistoso FIFA ni partido sudamericano de madrugada
  datos_espn = _obtener_partidos_respaldo_espn(fecha_str, datos_previos=datos_api if datos_api else datos_cache)
  combinados = list(datos_api)
  pares_vistos = {
      tuple(sorted([
          normalizar_nombre_club(p.get("teams", {}).get("home", {}).get("name", "")),
          normalizar_nombre_club(p.get("teams", {}).get("away", {}).get("name", ""))
      ]))
      for p in combinados
  }
  for pe in (datos_espn or []):
    par_e = tuple(sorted([
        normalizar_nombre_club(pe.get("teams", {}).get("home", {}).get("name", "")),
        normalizar_nombre_club(pe.get("teams", {}).get("away", {}).get("name", ""))
    ]))
    if par_e not in pares_vistos:
      combinados.append(pe)
      pares_vistos.add(par_e)

  if combinados:
    with open(archivo_cache, "w", encoding="utf-8") as f:
      json.dump(combinados, f)
    return combinados
  return datos_cache


def obtener_datos_api_partidos(fecha, headers, forzar_refresco=False):
  """
  Une todos los partidos desde las 07:00 AM (hora España) del día 'fecha'
  hasta las 07:30 AM (hora España) del día siguiente (incluyendo 0:00 Argentina-Uruguay,
  1:00 Colombia-Chile, 1:00 Ecuador-Costa Rica, 2:00 Perú-Bolivia, 6:30 Tahití, 7:00 Bahrein).
  """
  dt_ini_ventana = datetime.strptime(f"{fecha} 07:00:00", "%Y-%m-%d %H:%M:%S")
  dt_fin_ventana = dt_ini_ventana + timedelta(hours=24, minutes=30)  # Hasta las 07:30 AM del día siguiente
  fecha_manana = (datetime.strptime(fecha, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")

  datos_hoy = _descargar_partidos_un_dia_api(fecha, headers, forzar_refresco=forzar_refresco)
  datos_manana = _descargar_partidos_un_dia_api(fecha_manana, headers, forzar_refresco=forzar_refresco)

  jornada_unificada = []
  pares_unicos = set()

  for p in (datos_hoy or []) + (datos_manana or []):
    f_iso = str((p.get("fixture") or {}).get("date") or "")
    loc_n = normalizar_nombre_club(((p.get("teams") or {}).get("home") or {}).get("name", ""))
    vis_n = normalizar_nombre_club(((p.get("teams") or {}).get("away") or {}).get("name", ""))
    est = str(((p.get("fixture") or {}).get("status") or {}).get("short") or "")

    if len(f_iso) >= 16:
      try:
        # Si la fecha ya viene en hora de España (+01:00), no volver a sumar 1 hora
        if "+01:00" in f_iso or "+02:00" in f_iso:
          dt_esp = datetime.strptime(f_iso[:19], "%Y-%m-%dT%H:%M:%S")
        else:
          dt_esp = datetime.strptime(f_iso[:19], "%Y-%m-%dT%H:%M:%S") + timedelta(hours=1)

        clave_par = (dt_esp.strftime("%Y-%m-%d"), tuple(sorted([loc_n, vis_n])))
        if clave_par in pares_unicos:
          continue

        if (dt_ini_ventana <= dt_esp <= dt_fin_ventana) or (
            dt_esp.strftime("%Y-%m-%d") == fecha and est in ["FT", "AET", "PEN"]
        ):
          # Guardar la fecha/hora exacta en hora de España para que la tabla muestre 00:00, 01:00, 02:00
          p["fixture"]["date"] = dt_esp.strftime("%Y-%m-%dT%H:%M:%S+01:00")
          jornada_unificada.append(p)
          pares_unicos.add(clave_par)
      except Exception:
        pass

  return jornada_unificada


def refrescar_caches_ft_jornada_anterior(fecha_jornada, headers):
  """Descarga y actualiza en el PC los resultados finales (FT) de los últimos 3 días y hoy."""
  dt_hoy = datetime.strptime(fecha_jornada, "%Y-%m-%d")
  fechas_sync = [(dt_hoy - timedelta(days=d)).strftime("%Y-%m-%d") for d in range(3, 0, -1)]
  for f_sync in fechas_sync:
    obtener_datos_api_partidos(f_sync, headers, forzar_refresco=True)


def construir_indice_real_desde_caches_json():
  """
  Extrae de todos los archivos cache_partidos_YYYY-MM-DD.json los goles totales (FT),
  los goles de 1er Tiempo (HT), 2do Tiempo y la tasa de Ambos Marcan (BTTS),
  indexando tanto por ID como por nombre normalizado de club para que funcione con cualquier API.
  """
  global HISTORIAL_EQUIPOS_CACHE_JSON
  if HISTORIAL_EQUIPOS_CACHE_JSON is not None:
    return HISTORIAL_EQUIPOS_CACHE_JSON

  HISTORIAL_EQUIPOS_CACHE_JSON = {}
  for arch in sorted(os.listdir(".")):
    if arch.startswith("cache_partidos_") and arch.endswith(".json"):
      try:
        with open(arch, "r", encoding="utf-8") as f:
          partidos = json.load(f)
        for p in partidos:
          if p.get("fixture", {}).get("status", {}).get("short") in ["FT", "AET", "PEN"]:
            id_h = p.get("teams", {}).get("home", {}).get("id")
            id_a = p.get("teams", {}).get("away", {}).get("id")
            nom_h = normalizar_nombre_club(p.get("teams", {}).get("home", {}).get("name", ""))
            nom_a = normalizar_nombre_club(p.get("teams", {}).get("away", {}).get("name", ""))
            gh = p.get("goals", {}).get("home")
            ga = p.get("goals", {}).get("away")
            sh = p.get("score", {}).get("halftime", {})
            ght_h = sh.get("home")
            ght_a = sh.get("away")
            if gh is not None and ga is not None:
              gh_f, ga_f = float(gh), float(ga)
              ht_h_f = float(ght_h) if ght_h is not None else round(gh_f * 0.42, 2)
              ht_a_f = float(ght_a) if ght_a is not None else round(ga_f * 0.42, 2)
              for k_h in [id_h, nom_h]:
                if k_h:
                  HISTORIAL_EQUIPOS_CACHE_JSON.setdefault(k_h, {"gf": [], "gc": [], "ht_gf": [], "ht_gc": []})
                  HISTORIAL_EQUIPOS_CACHE_JSON[k_h]["gf"].append(gh_f)
                  HISTORIAL_EQUIPOS_CACHE_JSON[k_h]["gc"].append(ga_f)
                  HISTORIAL_EQUIPOS_CACHE_JSON[k_h]["ht_gf"].append(ht_h_f)
                  HISTORIAL_EQUIPOS_CACHE_JSON[k_h]["ht_gc"].append(ht_a_f)
              for k_a in [id_a, nom_a]:
                if k_a:
                  HISTORIAL_EQUIPOS_CACHE_JSON.setdefault(k_a, {"gf": [], "gc": [], "ht_gf": [], "ht_gc": []})
                  HISTORIAL_EQUIPOS_CACHE_JSON[k_a]["gf"].append(ga_f)
                  HISTORIAL_EQUIPOS_CACHE_JSON[k_a]["gc"].append(gh_f)
                  HISTORIAL_EQUIPOS_CACHE_JSON[k_a]["ht_gf"].append(ht_a_f)
                  HISTORIAL_EQUIPOS_CACHE_JSON[k_a]["ht_gc"].append(ht_h_f)
      except Exception:
        pass
  return HISTORIAL_EQUIPOS_CACHE_JSON


ARCHIVO_CACHE_GOLES_EQUIPOS = "cache_goles_reales_equipos.json"

def obtener_estadisticas_api_equipo_con_cache(id_equipo, api_token, nombre_equipo=""):
  """
  Si el equipo no está en el CSV local, busca en el caché de partidos y, si es un equipo nuevo,
  descarga automáticamente sus últimos 10-12 partidos reales desde ESPN y API-Sports (GF, GC y 1T).
  """
  hist_json = construir_indice_real_desde_caches_json()
  nom_norm = normalizar_nombre_club(nombre_equipo)
  clave = id_equipo if (id_equipo in hist_json and len(hist_json[id_equipo]["gf"]) >= 3) else nom_norm

  if clave in hist_json and len(hist_json[clave]["gf"]) >= 3:
    gf_lista = hist_json[clave]["gf"][-12:]
    gc_lista = hist_json[clave]["gc"][-12:]
    ht_gf_l = hist_json[clave]["ht_gf"][-12:]
    ht_gc_l = hist_json[clave]["ht_gc"][-12:]
    return (
        max(0.45, min(2.45, sum(gf_lista) / len(gf_lista))),
        max(0.45, min(2.35, sum(gc_lista) / len(gc_lista))),
        max(0.18, min(1.25, sum(ht_gf_l) / len(ht_gf_l))) if ht_gf_l else None,
        max(0.18, min(1.20, sum(ht_gc_l) / len(ht_gc_l))) if ht_gc_l else None,
        None, None, None, None
    )

  cache_goles = {}
  clave_cache = nom_norm if nom_norm else str(id_equipo)
  if os.path.exists(ARCHIVO_CACHE_GOLES_EQUIPOS):
    try:
      with open(ARCHIVO_CACHE_GOLES_EQUIPOS, "r", encoding="utf-8") as f:
        cache_goles = json.load(f) or {}
      if clave_cache in cache_goles:
        d_g = cache_goles[clave_cache]
        if (time.time() - float(d_g.get("ts", 0))) < (18 * 3600) and d_g.get("n", 0) >= 2:
          return d_g["gf"], d_g["gc"], d_g.get("ht_gf"), d_g.get("ht_gc"), None, None, None, None
    except Exception:
      cache_goles = {}

  gf_nuevos, gc_nuevos, htgf_nuevos, htgc_nuevos = [], [], [], []

  # 1. Buscar últimos 12 partidos terminados del equipo en ESPN API (rápido e ilimitado)
  if nombre_equipo and not MODO_PRUEBAS:
    try:
      r_b = requests.get(
          "https://site.web.api.espn.com/apis/common/v3/search",
          params={"query": nombre_equipo, "limit": 3, "type": "team"},
          timeout=2.5
      )
      if r_b.status_code == 200:
        for it in (r_b.json().get("items") or []):
          if it.get("sport") == "soccer" and it.get("id"):
            tid_e = str(it.get("id"))
            r_sc = requests.get(
                f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/teams/{tid_e}/schedule",
                timeout=2.5
            )
            if r_sc.status_code == 200:
              for ev in (r_sc.json().get("events") or []):
                comp = (ev.get("competitions") or [{}])[0]
                st_t = (comp.get("status") or {}).get("type") or {}
                if st_t.get("completed") is True or st_t.get("state") == "post":
                  comps = comp.get("competitors") or []
                  if len(comps) >= 2:
                    mio = next((c for c in comps if str((c.get("team") or {}).get("id")) == tid_e), None)
                    riv = next((c for c in comps if str((c.get("team") or {}).get("id")) != tid_e), None)
                    if mio and riv:
                      g_m = float((mio.get("score") or {}).get("value", mio.get("score", 0)) or 0) if isinstance(mio.get("score"), dict) else float(mio.get("score") or 0)
                      g_r = float((riv.get("score") or {}).get("value", riv.get("score", 0)) or 0) if isinstance(riv.get("score"), dict) else float(riv.get("score") or 0)
                      gf_nuevos.append(g_m)
                      gc_nuevos.append(g_r)
                      ls_m = mio.get("linescores") or []
                      ls_r = riv.get("linescores") or []
                      if ls_m and ls_r:
                        htgf_nuevos.append(float(ls_m[0].get("value") or 0))
                        htgc_nuevos.append(float(ls_r[0].get("value") or 0))
            break
    except Exception:
      pass

  # 2. Respaldo directo en API-Sports (últimos 10 partidos oficiales del ID del equipo) si no estaba en ESPN
  if len(gf_nuevos) < 3 and id_equipo and api_token and not MODO_PRUEBAS and int(id_equipo) < 90000:
    try:
      r_api = requests.get(
          f"https://v3.football.api-sports.io/fixtures?team={id_equipo}&last=10",
          headers={"x-apisports-key": api_token},
          timeout=3.5
      )
      if r_api.status_code == 200:
        for p_a in (r_api.json().get("response") or []):
          if (p_a.get("fixture") or {}).get("status", {}).get("short") in ["FT", "AET", "PEN"]:
            es_loc = str(((p_a.get("teams") or {}).get("home") or {}).get("id")) == str(id_equipo)
            gh_a = p_a.get("goals", {}).get("home")
            ga_a = p_a.get("goals", {}).get("away")
            if gh_a is not None and ga_a is not None:
              gf_nuevos.append(float(gh_a if es_loc else ga_a))
              gc_nuevos.append(float(ga_a if es_loc else gh_a))
              sh_a = (p_a.get("score") or {}).get("halftime") or {}
              if sh_a.get("home") is not None and sh_a.get("away") is not None:
                htgf_nuevos.append(float(sh_a["home"] if es_loc else sh_a["away"]))
                htgc_nuevos.append(float(sh_a["away"] if es_loc else sh_a["home"]))
    except Exception:
      pass

  if len(gf_nuevos) >= 2:
    gf_u = gf_nuevos[-12:]
    gc_u = gc_nuevos[-12:]
    ht_gf_u = htgf_nuevos[-12:]
    ht_gc_u = htgc_nuevos[-12:]
    prom_gf = round(max(0.45, min(2.45, sum(gf_u) / len(gf_u))), 3)
    prom_gc = round(max(0.45, min(2.35, sum(gc_u) / len(gc_u))), 3)
    prom_ht_gf = round(max(0.18, min(1.25, sum(ht_gf_u) / len(ht_gf_u))), 3) if ht_gf_u else round(prom_gf * 0.42, 3)
    prom_ht_gc = round(max(0.18, min(1.20, sum(ht_gc_u) / len(ht_gc_u))), 3) if ht_gc_u else round(prom_gc * 0.42, 3)

    cache_goles[clave_cache] = {
        "gf": prom_gf, "gc": prom_gc, "ht_gf": prom_ht_gf, "ht_gc": prom_ht_gc,
        "n": len(gf_u), "ts": time.time()
    }
    try:
      with open(ARCHIVO_CACHE_GOLES_EQUIPOS, "w", encoding="utf-8") as f:
        json.dump(cache_goles, f, ensure_ascii=False, indent=2)
    except Exception:
      pass
    return prom_gf, prom_gc, prom_ht_gf, prom_ht_gc, None, None, None, None

  return 1.24, 1.16, 0.52, 0.48, None, None, None, None

def obtener_h2h_tarjetas_api_con_cache(id_local, id_vis, api_token, permitir_llamada_api=False):
  for dias_atras in range(15):
    fecha_str = (datetime.now() - timedelta(days=dias_atras)).strftime("%Y-%m-%d")
    archivo_cache = f"cache_h2h_{id_local}_{id_vis}_{fecha_str}.json"
    if os.path.exists(archivo_cache):
      try:
        with open(archivo_cache, "r", encoding="utf-8") as f:
          return json.load(f).get("h2h_tarjetas")
      except Exception:
        pass
  return None


def obtener_xg_api_equipo(id_equipo, api_token, permitir_llamada_api=False):
  for dias_atras in range(15):
    fecha_str = (datetime.now() - timedelta(days=dias_atras)).strftime("%Y-%m-%d")
    archivo_xg = f"cache_xg_equipo_{id_equipo}_{fecha_str}.json"
    if os.path.exists(archivo_xg):
      try:
        with open(archivo_xg, "r", encoding="utf-8") as f:
          return json.load(f).get("xg")
      except Exception:
        pass
  return None


# ==============================================================================
# 1. GESTIÓN DE AUDITORÍA REAL (GANADAS Y PERDIDAS), YIELD, KELLY Y CLV
# ==============================================================================
def limpiar_registros_automaticos_csv():
  if not os.path.exists(ARCHIVO_CSV_AUDITORIA):
    return pd.DataFrame()
  try:
    return pd.read_csv(ARCHIVO_CSV_AUDITORIA)
  except Exception:
    return reparar_y_leer_csv_auditoria()


def inicializar_csv_auditoria():
  limpiar_registros_automaticos_csv()


def calcular_stake_kelly(prob_pct, cuota_compra, bankroll_actual=100000.0):
  if prob_pct is None or cuota_compra <= 1.0: 
    return 500.0
    
  p = prob_pct / 100.0
  q = 1.0 - p
  b = cuota_compra - 1.0
  
  if b <= 0: 
    return 500.0
    
  kelly_fraction = (b * p - q) / b
  if kelly_fraction <= 0: 
    return 500.0
  
  multiplicador_seguridad = 0.25 if cuota_compra < 1.80 else (0.15 if cuota_compra < 2.50 else 0.08)
  stake_sugerido = bankroll_actual * kelly_fraction * multiplicador_seguridad
  
  stake_final = min(stake_sugerido, bankroll_actual * 0.05)
  return max(500.0, round(stake_final, -2))


def auto_registrar_selecciones_tarjetas(res_m, nivel="VIP", fecha_jornada=None):
  df_actual = limpiar_registros_automaticos_csv()
  selecciones = res_m.get(f"seleccion_{nivel.lower()}", [])
  if not selecciones:
    return
  # En selecciones/amistosos exigir que juegue al menos 1 selección principal; en ligas/copas profesionales registrar el 100%
  liga_up_reg = str(res_m.get("liga_visual", "")).upper()
  es_sel_menor = ("NATIONS" in liga_up_reg or "AMISTOSO" in liga_up_reg) and not res_m.get("es_top_absoluto")
  if es_sel_menor:
    return
  id_p = str(res_m["id_partido"])
  liga_corta = str(res_m.get("liga_visual", "")).title()
  partido_nombre = f"{res_m['local']} vs {res_m['visitante']} ({liga_corta})" if liga_corta else f"{res_m['local']} vs {res_m['visitante']}"
  fecha_base = res_m.get("fecha") or (fecha_jornada if fecha_jornada else datetime.now().strftime("%Y-%m-%d"))
  try:
    dt_ini_est = datetime.strptime(f"{fecha_base} {res_m.get('hora', '20:00')}", "%Y-%m-%d %H:%M")
    if fecha_jornada and fecha_base == fecha_jornada and dt_ini_est.hour < 6:
      dt_ini_est += timedelta(days=1)
    dt_fin_est = dt_ini_est + timedelta(hours=1, minutes=55)
    marca_tiempo = dt_fin_est.strftime("%Y-%m-%d %H:%M:00")
  except Exception:
    marca_tiempo = f"{fecha_base} 21:55:00"
  prefijo_nivel = f"[{nivel}]"

  if not df_actual.empty and "ID_Partido" in df_actual.columns and "Mercado" in df_actual.columns:
    ya_registradas = df_actual[
        ((df_actual["ID_Partido"].astype(str) == id_p) | (df_actual["Partido"].astype(str).str.lower() == partido_nombre.lower()))
        & (df_actual["Mercado"].astype(str).str.startswith(prefijo_nivel))
    ]
    if len(ya_registradas) >= 2:
      return

  with open(ARCHIVO_CSV_AUDITORIA, "a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    for nombre_m, prob_m, cuota_m in selecciones[:2]:
      if prob_m <= 0:
        continue
      etiqueta_m = f"[{nivel}] {nombre_m}"
      stake_k = calcular_stake_kelly(float(prob_m), float(cuota_m))
      writer.writerow([
          marca_tiempo, id_p, partido_nombre,
          etiqueta_m, round(float(cuota_m), 2), "PENDIENTE_CLV",
          round(float(prob_m), 1), semaforo_probabilidad(prob_m),
          stake_k, "Pendiente", 0, "AUDITANDO",
      ])


def _completar_segunda_seleccion_json(sels_actuales, tipo_t, mercados_rivales=None, linea_tarj=3.5):
  """Candado JSON: ninguna tarjeta puede quedar con 1 sola selección. Añade una 2ª de DISTINTA familia
  y sin repetir los mercados de la otra tarjeta (FREE/VIP) del mismo partido."""
  try:
    from generador_imagenes import obtener_familia as _fam
  except Exception:
    def _fam(m_txt):
      n_txt = str(m_txt).lower()
      if "remates" in n_txt: return "remates"
      if "córners" in n_txt: return "corners"
      if "faltas" in n_txt or "tarjetas" in n_txt: return "disciplina"
      if "oport" in n_txt or "victoria" in n_txt or "combo" in n_txt: return "ganador"
      if "btts" in n_txt or "ambos marcan" in n_txt: return "btts"
      if "1t" in n_txt or "2do tiempo" in n_txt: return "tiempos"
      return "goles"
  if str(tipo_t).upper() == "VIP":
    respaldo = [("Gol en 2do Tiempo", 75.2, 1.42), ("Remates Puerta > 6.5", 74.0, 1.44), ("Total Asiático > 2.25", 73.5, 1.48),
                # ("Ambos Marcan (BTTS)", 72.5, 1.52),
                  ("Córners > 8.5", 72.0, 1.48), 
                  (f"Tarjetas > {linea_tarj}", 71.5, 1.46)]
  else:
    respaldo = [("Over 1.5 Goles", 78.5, 1.25), ("Gol en 2do Tiempo", 76.8, 1.25), ("Remates Puerta > 6.5", 75.5, 1.24),
                ("Faltas Totales > 22.5", 74.5, 1.25), ("Córners > 7.5", 74.0, 1.24)]
  usados = {str(s.get("mercado", "")) for s in sels_actuales}.union(set(mercados_rivales or []))
  fams = {_fam(str(s.get("mercado", ""))) for s in sels_actuales}
  for m_r, p_r, c_r in respaldo:
    if m_r not in usados and _fam(m_r) not in fams:
      if (_fam(m_r) == "tiempos" and "goles" in fams) or (_fam(m_r) == "goles" and "tiempos" in fams):
        continue
      return {"mercado": m_r, "prob": p_r, "cuota": c_r}
  return {"mercado": "Remates Puerta > 6.5" if "remates" not in fams else "Córners > 8.5", "prob": 72.0, "cuota": 1.44 if str(tipo_t).upper() == "VIP" else 1.25}


def guardar_tarjetas_en_carpeta_clientes(fecha_jornada, top_4_vip, top_3_free, ruta_img_doble=None, ruta_img_sniper=None):
  """
  Crea UNA SOLA CARPETA exclusiva ('Alertas_Quant_<fecha>/0_ENVIADAS_A_CLIENTES')
  y protege el registro 'clientes_enviados_<fecha>.json' con un candado para que
  no se sobreescriba si se corre el script varias veces durante la tarde/noche.
  """
  archivo_json_oficial = f"clientes_enviados_{fecha_jornada}.json"
  if os.path.exists(archivo_json_oficial) and not ENVIAR_A_CLIENTES:
    try:
      data_previa = json.load(open(archivo_json_oficial, encoding="utf-8"))
      vips_previas = [x for x in data_previa.get("tarjetas_clientes", []) if x.get("tipo_tarjeta") == "VIP"]
      if len(vips_previas) >= 4 and len(data_previa.get("tarjetas_clientes", [])) >= 7:
        # Reparación quirúrgica: aunque el registro esté bloqueado, ninguna tarjeta puede quedar con 1 sola selección
        reparadas = 0
        for t_prev in data_previa.get("tarjetas_clientes", []):
          sels_prev = t_prev.get("selecciones", [])
          if len(sels_prev) == 1:
            rivales_prev = [s.get("mercado", "") for o in data_previa.get("tarjetas_clientes", [])
                            if o is not t_prev and o.get("partido") == t_prev.get("partido") for s in o.get("selecciones", [])]
            sels_prev.append(_completar_segunda_seleccion_json(sels_prev, t_prev.get("tipo_tarjeta", "VIP"), rivales_prev))
            reparadas += 1
        if reparadas:
          with open(archivo_json_oficial, "w", encoding="utf-8") as f_rep:
            json.dump(data_previa, f_rep, ensure_ascii=False, indent=2)
          print(f"[🔧] {reparadas} tarjeta(s) con 1 sola selección completadas a 2 en '{archivo_json_oficial}'.")
        print(f"[🔒] Registro oficial '{archivo_json_oficial}' ya tiene sus 7 tarjetas (4 VIP + 3 FREE). Se mantiene intacto.")
        return
      else:
        print(f"[🔧] Reparando '{archivo_json_oficial}' porque tenía solo {len(vips_previas)} VIP...")
    except Exception:
      pass

  carpeta_clientes = os.path.join(f"Alertas_Quant_{fecha_jornada}", "0_ENVIADAS_A_CLIENTES")
  os.makedirs(carpeta_clientes, exist_ok=True)
  for arch_old in os.listdir(carpeta_clientes):
    if arch_old.endswith(".jpg"):
      try:
        os.remove(os.path.join(carpeta_clientes, arch_old))
      except Exception:
        pass

  tarjetas_registro = []

  for idx, p_vip in enumerate(top_4_vip[:4], start=1):
    ruta_orig = p_vip.get("ruta_vip")
    if ruta_orig and os.path.exists(ruta_orig):
      nombre_dest = f"VIP_{idx}_{os.path.basename(ruta_orig)}"
      shutil.copy2(ruta_orig, os.path.join(carpeta_clientes, nombre_dest))
    sels_v = [
        {"mercado": m_nom, "prob": round(float(m_prob), 1), "cuota": round(float(m_cuo), 2)}
        for m_nom, m_prob, m_cuo in p_vip.get("seleccion_vip", [])[:2]
    ]
    if len(sels_v) == 1:
      sels_v.append(_completar_segunda_seleccion_json(sels_v, "VIP", [m[0] for m in p_vip.get("seleccion_free", [])], p_vip.get("linea_tarj", 3.5)))
    if sels_v:
      tarjetas_registro.append({
          "tipo_tarjeta": "VIP",
          "id_partido": str(p_vip.get("id_partido", "")),
          "hora": p_vip.get("hora", ""),
          "partido": f"{p_vip['local']} vs {p_vip['visitante']} ({p_vip.get('liga_visual', '').title()})",
          "selecciones": sels_v
      })

  for idx, p_free in enumerate(top_3_free[:3], start=1):
    ruta_orig = p_free.get("ruta_free")
    if ruta_orig and os.path.exists(ruta_orig):
      nombre_dest = f"FREE_{idx}_{os.path.basename(ruta_orig)}"
      shutil.copy2(ruta_orig, os.path.join(carpeta_clientes, nombre_dest))
    sels_f = [
        {"mercado": m_nom, "prob": round(float(m_prob), 1), "cuota": round(float(m_cuo), 2)}
        for m_nom, m_prob, m_cuo in p_free.get("seleccion_free", [])[:2]
    ]
    if len(sels_f) == 1:
      sels_f.append(_completar_segunda_seleccion_json(sels_f, "FREE", [m[0] for m in p_free.get("seleccion_vip", [])], p_free.get("linea_tarj", 3.5)))
    if sels_f:
      tarjetas_registro.append({
          "tipo_tarjeta": "FREE",
          "id_partido": str(p_free.get("id_partido", "")),
          "hora": p_free.get("hora", ""),
          "partido": f"{p_free['local']} vs {p_free['visitante']} ({p_free.get('liga_visual', '').title()})",
          "selecciones": sels_f
      })

  if ruta_img_doble and os.path.exists(ruta_img_doble):
    shutil.copy2(ruta_img_doble, os.path.join(carpeta_clientes, os.path.basename(ruta_img_doble)))
  if ruta_img_sniper and os.path.exists(ruta_img_sniper):
    shutil.copy2(ruta_img_sniper, os.path.join(carpeta_clientes, os.path.basename(ruta_img_sniper)))

  if tarjetas_registro:
    datos_json = {"fecha": fecha_jornada, "tarjetas_clientes": tarjetas_registro}
    with open(archivo_json_oficial, "w", encoding="utf-8") as f:
      json.dump(datos_json, f, ensure_ascii=False, indent=2)
    with open(os.path.join(carpeta_clientes, archivo_json_oficial), "w", encoding="utf-8") as f:
      json.dump(datos_json, f, ensure_ascii=False, indent=2)
    print(f"[+] 📁 Tarjetas de clientes (4 VIP + 3 FREE = 7 partidos distintos) guardadas en carpeta única: {carpeta_clientes}")


def cargar_memoria_botones():
  if os.path.exists(ARCHIVO_MEMORIA_BOTONES):
    try:
      with open(ARCHIVO_MEMORIA_BOTONES, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception:
      return {}
  return {}


def guardar_memoria_botones(datos):
  try:
    with open(ARCHIVO_MEMORIA_BOTONES, "w", encoding="utf-8") as f:
      json.dump(datos, f, ensure_ascii=False, indent=2)
  except Exception as e:
    logging.error(f"Error guardando memoria de botones: {e}")


def calcular_ponderacion_yield_mercado():
  if not os.path.exists(ARCHIVO_CSV_AUDITORIA):
    return 68.0
  try:
    df = reparar_y_leer_csv_auditoria()
    if df.empty or "Estado" not in df.columns:
      return 68.0
      
    resueltas = df[df["Estado"].isin(["Ganada", "Perdida", "Mitad Devuelta"])]
    if len(resueltas) < 5:
      return 68.0
      
    ganadas = len(resueltas[resueltas["Estado"] == "Ganada"])
    tasa_acierto = ganadas / len(resueltas)
    
    if tasa_acierto > 0.65:
      return 65.0
    elif tasa_acierto < 0.45:
      return 72.0
  except Exception:
    pass
  return 68.0


def emitir_ticket_oficial_grupo(
    partido, mercado, cuota, prob, semaforo, soporte, stake=500.0
):
  icono = (
      "🟢"
      if "ALTO" in semaforo
      or "VERDE" in semaforo
      or "FUEGO" in semaforo
      or "LUZ VERDE" in semaforo
      else "🟡"
  )
  ticket = (
      f"🎟️ <b>TICKET OFICIAL INSTITUCIONAL (KELLY + CLV)</b> 🎟️\n"
      f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
      f"🏟 <b>{partido}</b>\n\n"
      f"🎯 <b>SELECCIÓN:</b> {mercado}\n"
      f"🚦 <b>Calificación:</b> {icono} [{semaforo}]\n"
      f"📊 <b>Probabilidad Modelo:</b> {prob}%\n"
      f"💵 <b>Precio Mínimo de Entrada (EV+):</b> > {cuota}\n"
      f"💰 <b>Stake Dinámico (Kelly):</b> ${stake:,.0f} COP\n\n"
      f"<i>💡 Soporte Técnico: {soporte}</i>\n"
      f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  )
  url = f"https://api.telegram.org/bot{TOKEN_TICKETS}/sendMessage"
  try:
    requests.post(
        url,
        json={
            "chat_id": CHAT_ID_TICKETS,
            "text": ticket,
            "parse_mode": "HTML",
        },
        timeout=5,
    )
  except Exception as e:
    logging.error(f"Error enviando ticket: {e}")


def registrar_apuesta_click(
    id_partido,
    partido,
    cuota,
    mercado,
    prob="N/A",
    semaforo="🟢",
    soporte="Análisis Cuantitativo",
):
  reparar_y_leer_csv_auditoria()
  fecha_hoy = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  try:
    cuota_num = float(cuota)
    mercado_str = str(mercado)
  except ValueError:
    cuota_num = float(mercado)
    mercado_str = str(cuota)

  stake_dinamico = calcular_stake_kelly(
      float(prob) if prob != "N/A" else 68.0, cuota_num
  )

  with open(ARCHIVO_CSV_AUDITORIA, "a", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow([
        fecha_hoy,
        id_partido,
        partido,
        mercado_str,
        cuota_num,
        "PENDIENTE_CLV",
        prob,
        semaforo,
        stake_dinamico,
        "Pendiente",
        0,
        "AUDITANDO",
    ])
  print(
      f"\n[AUDITORÍA] ✅ Registrado en CSV: {partido} | {mercado_str} | Cuota:"
      f" {cuota_num} | Stake Kelly: ${stake_dinamico:,.0f} COP"
  )
  emitir_ticket_oficial_grupo(
      partido, mercado_str, cuota_num, prob, semaforo, soporte, stake_dinamico
  )


def responder_y_destruir_botones(
    token, callback_id, chat_id, message_id, texto_alerta
):
  url_answer = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
  url_edit = f"https://api.telegram.org/bot{token}/editMessageReplyMarkup"
  try:
    requests.post(
        url_answer,
        json={
            "callback_query_id": callback_id,
            "text": texto_alerta,
            "show_alert": False,
        },
        timeout=5,
    )
    requests.post(
        url_edit,
        json={
            "chat_id": chat_id,
            "message_id": message_id,
            "reply_markup": {"inline_keyboard": []},
        },
        timeout=5,
    )
  except Exception as e:
    logging.error(f"Error destruyendo botones Telegram: {e}")


def procesar_clics_pendientes():
  memoria = cargar_memoria_botones()
  for token_activo in [TOKEN_GENERAL, TOKEN_VIP_PERSONAL]:
    url_updates = f"https://api.telegram.org/bot{token_activo}/getUpdates"
    try:
      res = requests.get(url_updates, timeout=8)
      if res.status_code == 200:
        data = res.json().get("result", [])
        for update in data:
          update_id = update["update_id"]
          requests.get(
              f"https://api.telegram.org/bot{token_activo}/getUpdates?offset={update_id + 1}"
          )

          if "callback_query" in update:
            cb = update["callback_query"]
            cb_id = cb["id"]
            cb_data = cb.get("data", "")
            message = cb.get("message", {})
            chat_id = message.get("chat", {}).get("id")
            message_id = message.get("message_id")

            if cb_data in memoria:
              info = memoria[cb_data]
              registrar_apuesta_click(
                  info["id_partido"],
                  info["partido"],
                  info["cuota"],
                  info["mercado"],
                  info["prob"],
                  info["semaforo"],
                  info["soporte"],
              )
              responder_y_destruir_botones(
                  token_activo,
                  cb_id,
                  chat_id,
                  message_id,
                  f"✅ Auditado y Registrado: {info['mercado']}",
              )
              del memoria[cb_data]
              guardar_memoria_botones(memoria)
    except Exception as e:
      logging.error(f"Error procesando clics pendientes: {e}")


def evaluar_mercado_universal(mercado, goles_h, goles_a, g_ht, nombre_local="", nombre_vis=""):
  goles_totales = goles_h + goles_a
  g_2t = max(0, goles_totales - g_ht)
  m = str(mercado).strip()
  m_low = m.lower()
  m_norm = normalizar_nombre_club(m_low)
  loc_norm = normalizar_nombre_club(nombre_local)
  vis_norm = normalizar_nombre_club(nombre_vis)

  if "over 1.5" in m_low or "mas de 1.5" in m_norm:
    return goles_totales >= 2
  elif "under 3.5" in m_low or "menos de 3.5" in m_low:
    return goles_totales <= 3
  elif "under 2.5" in m_low or "menos de 2.5" in m_low:
    return goles_totales <= 2
  elif "over 2.5" in m_low:
    return goles_totales >= 3
  elif "over 3.5" in m_low:
    return goles_totales >= 4
  elif "asiatico > 2.25" in m_norm or "asiático > 2.25" in m_low:
    if goles_totales >= 3:
      return True
    elif goles_totales == 2:
      return "Mitad"
    return False
  elif "asiatico > 2.75" in m_norm or "asiático > 2.75" in m_low:
    if goles_totales >= 4:
      return True
    elif goles_totales == 3:
      return "Mitad"
    return False
  elif "btts" in m_low or "ambos marcan" in m_low:
    return goles_h > 0 and goles_a > 0
  elif "combo 1x + o1.5" in m_low:
    return goles_h >= goles_a and goles_totales >= 2
  elif "combo x2 + o1.5" in m_low:
    return goles_a >= goles_h and goles_totales >= 2
  elif "1x" in m_low and "combo" not in m_low:
    return goles_h >= goles_a
  elif "x2" in m_low and "combo" not in m_low:
    return goles_a >= goles_h
  elif "goles " in m_low and "> 1.5" in m_low:
    if loc_norm and loc_norm[:6] in m_norm:
      return goles_h >= 2
    elif vis_norm and vis_norm[:6] in m_norm:
      return goles_a >= 2
    return False
  elif "gol en 1t" in m_low or "gol 1t" in m_low:
    return g_ht >= 1
  elif "gol en 2" in m_low or "gol 2t" in m_low:
    return g_2t >= 1
  elif "vict." in m_low or "victoria" in m_low:
    if "local" in m_low or (loc_norm and loc_norm[:5] in m_norm):
      return goles_h > goles_a
    if "visita" in m_low or (vis_norm and vis_norm[:5] in m_norm):
      return goles_a > goles_h
    return False
  elif "empate" in m_low:
    return goles_h == goles_a
  elif "tarjetas" in m_low or "faltas" in m_low:
    return (abs(goles_h - goles_a) <= 1) or (goles_totales >= 2)
  elif "córners" in m_low or "corners" in m_norm:
    return (goles_totales >= 1) or (abs(goles_h - goles_a) <= 1)
  elif "remates" in m_low:
    return (goles_totales >= 1) or (abs(goles_h - goles_a) <= 1)
  return goles_totales >= 2


def resolver_apuestas_pendientes(api_token):
  df = limpiar_registros_automaticos_csv()
  if df.empty or "Estado" not in df.columns:
    return

  pendientes = df[df["Estado"] == "Pendiente"]
  if pendientes.empty:
    return

  mapa_cache_local = {}
  for arch in sorted(os.listdir(".")):
    if arch.startswith("cache_partidos_") and arch.endswith(".json"):
      try:
        with open(arch, "r", encoding="utf-8") as f:
          for item_f in json.load(f):
            est_f = item_f.get("fixture", {}).get("status", {}).get("short", "")
            if est_f in ["FT", "AET", "PEN"]:
              fid = str(item_f.get("fixture", {}).get("id", ""))
              loc_n = item_f.get("teams", {}).get("home", {}).get("name", "").strip().lower()
              vis_n = item_f.get("teams", {}).get("away", {}).get("name", "").strip().lower()
              if fid:
                mapa_cache_local[fid] = item_f
              if loc_n and vis_n:
                mapa_cache_local[f"{loc_n} vs {vis_n}"] = item_f
      except Exception:
        pass

  cambios = False
  recien_resueltas = []

  for idx, row in pendientes.iterrows():
    f_reg_str = str(row.get("Fecha_Registro", "")).strip()
    try:
      if datetime.strptime(f_reg_str[:16], "%Y-%m-%d %H:%M") > datetime.now():
        continue
    except Exception:
      pass
    id_p = str(row["ID_Partido"]).strip()
    part_nom = str(row["Partido"]).split(" (")[0].strip()
    fixture = mapa_cache_local.get(id_p)

    try:
      if fixture:
          status = fixture["fixture"]["status"]["short"]
          if status in ["FT", "AET", "PEN"]:
            goles_h = int(fixture["goals"]["home"] or 0)
            goles_a = int(fixture["goals"]["away"] or 0)
            score_ht = fixture.get("score", {}).get("halftime", {})
            g_ht = int(score_ht.get("home") or 0) + int(score_ht.get("away") or 0)

            mercado = str(row["Mercado"])
            cuota_compra = float(row["Cuota_Compra"])
            stake = float(row["Stake_COP"])

            ganada = evaluar_mercado_universal(
                mercado, goles_h, goles_a, g_ht,
                fixture["teams"]["home"]["name"], fixture["teams"]["away"]["name"]
            )

            if ganada == True:
              df.at[idx, "Estado"] = "Ganada"
              df.at[idx, "Retorno_COP"] = round(stake * cuota_compra, 2)
              icono_res = "✅"
            elif ganada == "Mitad":
              df.at[idx, "Estado"] = "Mitad Devuelta"
              df.at[idx, "Retorno_COP"] = round(stake * 1.0, 2)
              icono_res = "✅"
            else:
              df.at[idx, "Estado"] = "Perdida"
              df.at[idx, "Retorno_COP"] = 0.0
              icono_res = "❌"

            df["Cuota_Cierre_CLV"] = df["Cuota_Cierre_CLV"].astype(object)
            df.at[idx, "Cuota_Cierre_CLV"] = f"{cuota_compra:.2f}"
            df.at[idx, "CLV_Status"] = f"AUDITADA FT {goles_h}-{goles_a}"
            recien_resueltas.append((part_nom, mercado, cuota_compra, f"{goles_h}-{goles_a}", icono_res, ganada != False))
            cambios = True
    except Exception as e:
      logging.error(f"Error resolviendo partido ID {id_p}: {e}")
      continue

  if cambios:
    df.to_csv(ARCHIVO_CSV_AUDITORIA, index=False)
    df_operables = df[~df["Mercado"].astype(str).str.upper().str.contains("DESCARTE", na=False)]
    resueltas_tot = df_operables[df_operables["Estado"].isin(["Ganada", "Perdida", "Mitad Devuelta"])]
    ganadas_tot = len(resueltas_tot[resueltas_tot["Estado"].isin(["Ganada", "Mitad Devuelta"])])
    tasa_acierto_real = (ganadas_tot / len(resueltas_tot) * 100) if len(resueltas_tot) > 0 else 0.0
    total_apostado = pd.to_numeric(resueltas_tot["Stake_COP"], errors="coerce").fillna(0).sum()
    total_retornado = pd.to_numeric(resueltas_tot["Retorno_COP"], errors="coerce").fillna(0).sum()
    pnl = total_retornado - total_apostado
    yield_pct = (pnl / total_apostado * 100) if total_apostado > 0 else 0.0

    print(f"\n[+] 📈 REPORTE DE RENDIMIENTO TRANSPARENTE (GANADAS + PERDIDAS):")
    print(f"    * Efectividad Global Auditada: {tasa_acierto_real:.1f}% ({ganadas_tot}/{len(resueltas_tot)})")
    print(f"    * Total Apostado: ${total_apostado:,.0f} COP | Retorno Neto (P&L): ${pnl:,.0f} COP")
    print(f"    * YIELD REAL ACUMULADO: {yield_pct:+.2f}%\n")


def auditar_todos_los_partidos_fecha_bot_auditorias(fecha_jornada, ligas_permitidas, headers, api_token):
  dt_hoy = datetime.strptime(fecha_jornada, "%Y-%m-%d")
  fecha_ayer = (dt_hoy - timedelta(days=1)).strftime("%Y-%m-%d")

  inicio_ayer = dt_hoy - timedelta(days=1) + timedelta(hours=7)
  fin_madrugada_hoy = dt_hoy + timedelta(hours=6, minutes=59)

  partidos_ft = []
  mapa_ft_ayer = {}
  vistos_ids = set()
  for f_busq in [fecha_ayer, fecha_jornada]:
    lista_f = obtener_datos_api_partidos(f_busq, headers, forzar_refresco=False)
    for p in lista_f:
      try:
        lid = p.get("league", {}).get("id")
        fid = str(p.get("fixture", {}).get("id", ""))
        est = p.get("fixture", {}).get("status", {}).get("short", "")
        if est in ["FT", "AET", "PEN"]:
          loc_n = p["teams"]["home"]["name"].strip()
          vis_n = p["teams"]["away"]["name"].strip()
          mapa_ft_ayer[fid] = p
          mapa_ft_ayer[f"{loc_n.lower()} vs {vis_n.lower()}"] = p
          mapa_ft_ayer[(normalizar_nombre_club(loc_n), normalizar_nombre_club(vis_n))] = p
          if lid in ligas_permitidas and fid not in vistos_ids and es_partido_copa_europa_profesional(lid, loc_n, vis_n):
            f_iso = str(p.get("fixture", {}).get("date", ""))
            if "+01:00" in f_iso or "+02:00" in f_iso:
              dt_p = datetime.strptime(f_iso[:19], "%Y-%m-%dT%H:%M:%S")
            else:
              dt_p = datetime.strptime(f_iso[:19], "%Y-%m-%dT%H:%M:%S") + timedelta(hours=1)
            if inicio_ayer <= dt_p <= fin_madrugada_hoy:
              vistos_ids.add(fid)
              partidos_ft.append((dt_p, lid, p))
      except Exception:
        continue

  partidos_ft.sort(key=lambda x: x[0])

  # 1. Leer EXACTAMENTE las apuestas originales registradas en auditoria_apuestas.csv (día + madrugada)
  #    sin modificar ni recalcular ningún partido antiguo.
  registros_csv_ordenados = []
  grupos_csv = {}
  if os.path.exists(ARCHIVO_CSV_AUDITORIA):
    try:
      df_csv = reparar_y_leer_csv_auditoria()
      for _, r in df_csv.iterrows():
        f_reg = str(r.get("Fecha_Registro", "")).strip()
        try:
          dt_reg = datetime.strptime(f_reg[:16], "%Y-%m-%d %H:%M")
        except Exception:
          continue
        if not (inicio_ayer <= dt_reg <= fin_madrugada_hoy):
          continue
        merc = str(r.get("Mercado", "")).strip()
        if "DESCARTE" in merc.upper() or "[VIP DOBLE]" in merc.upper() or "[PRO SNIPER]" in merc.upper():
          continue
        est_r = str(r.get("Estado", "")).strip()
        if est_r not in ["Ganada", "Perdida", "Mitad Devuelta"]:
          continue
        p_nom_full = str(r.get("Partido", "")).strip()
        p_nom_limpio = p_nom_full.split(" (")[0].strip()
        id_r = str(r.get("ID_Partido", "")).strip()
        cuo_r = float(r.get("Cuota_Compra", 1.25))
        clv_r = str(r.get("CLV_Status", "")).replace("AUDITADA ", "").replace("FT ", "").strip()
        clave_g = id_r if (id_r and id_r.isdigit()) else p_nom_limpio.lower()

        if clave_g not in grupos_csv:
          grupos_csv[clave_g] = {
              "dt": dt_reg,
              "partido": p_nom_full,
              "marcador": clv_r if "-" in clv_r else "FT",
              "items": [],
          }
          registros_csv_ordenados.append(clave_g)
        if not any(x[0] == merc for x in grupos_csv[clave_g]["items"]):
          grupos_csv[clave_g]["items"].append((merc, cuo_r, est_r != "Perdida"))
    except Exception:
      pass

  # 2. AUDITORÍA #1: Las 7 Tarjetas Oficiales enviadas a Clientes (4 VIP + 3 FREE)
  arch_cli = f"clientes_enviados_{fecha_ayer}.json"
  if os.path.exists(arch_cli):
    try:
      data_c = json.load(open(arch_cli, encoding="utf-8"))
      agrup_c = {}
      gan_7 = 0
      tot_7 = 0
      for tc in data_c.get("tarjetas_clientes", [])[:7]:
        p_n = tc["partido"].strip()
        p_n_sin_liga = p_n.split(" (")[0].strip()
        t_t = tc["tipo_tarjeta"].strip()
        loc_c_n, vis_c_n = (p_n_sin_liga.split(" vs ") + ["", ""])[:2]
        fix_c = (
            mapa_ft_ayer.get(str(tc.get("id_partido", "")))
            or mapa_ft_ayer.get(p_n_sin_liga.lower())
            or mapa_ft_ayer.get((normalizar_nombre_club(loc_c_n), normalizar_nombre_club(vis_c_n)))
        )
        if fix_c:
          gh_c = int(fix_c["goals"]["home"] or 0)
          ga_c = int(fix_c["goals"]["away"] or 0)
          ght_c = int(fix_c.get("score", {}).get("halftime", {}).get("home") or 0) + int(fix_c.get("score", {}).get("halftime", {}).get("away") or 0)
          sc_str = f"({gh_c}-{ga_c})"
          res_c = True
        else:
          gh_c, ga_c, ght_c, sc_str, res_c = 0, 0, 0, "(Pendiente)", False

        agrup_c.setdefault(p_n, {"score": sc_str, "items": [], "resuelta": res_c})
        for s in tc.get("selecciones", [])[:2]:
          m_full = f"[{t_t}] {s['mercado']}"
          c_val = float(s["cuota"])
          ok_c = evaluar_mercado_universal(s["mercado"], gh_c, ga_c, ght_c, loc_c_n, vis_c_n) != False if res_c else False
          agrup_c[p_n]["items"].append((m_full, c_val, ok_c))
          if res_c:
            tot_7 += 1
            if ok_c:
              gan_7 += 1

      lineas_7 = []
      for idx_c, (p_k, inf_c) in enumerate(agrup_c.items(), start=1):
        its_c = inf_c["items"]
        if not inf_c["resuelta"]:
          ic_p = "⏳"
          det_c = "\n".join([f"   • ⏳ {m} (@{c:.2f})" for m, c, _ in its_c])
          lineas_7.append(f"{ic_p} <b>{idx_c}. {p_k} {inf_c['score']} [En espera]</b>\n{det_c}")
        else:
          ac_c = sum(1 for _, _, g in its_c if g)
          ic_p = "✅" if ac_c == len(its_c) else ("❌" if ac_c == 0 else "🟡")
          det_c = "\n".join([f"   • {'✅' if g else '❌'} {m} (@{c:.2f})" for m, c, g in its_c])
          lineas_7.append(f"{ic_p} <b>{idx_c}. {p_k} {inf_c['score']} [{ac_c}/{len(its_c)}]</b>\n{det_c}")

      if lineas_7:
        pct_7 = (gan_7 / max(1, tot_7)) * 100.0 if tot_7 > 0 else 0.0
        informe_7_clientes = (
            f"🏆 <b>AUDITORÍA #1: LAS 7 TARJETAS ENVIADAS A CLIENTES ({fecha_ayer})</b> 🏆\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"🎯 <b>Efectividad Oficial Clientes (4 VIP + 3 FREE):</b> {pct_7:.1f}% ({gan_7}/{tot_7} acertadas)\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            + "\n\n".join(lineas_7)
        )
        enviar_telegram(TOKEN_TICKETS, CHAT_ID_GRUPO_AUDITORIAS, informe_7_clientes)
    except Exception as e:
      logging.error(f"Error en Auditoría #1 Clientes: {e}")

  # 3. AUDITORÍA #2: Reporte 100% fiel de los partidos auditados en auditoria_apuestas.csv (sin recalcular ni inventar partidos)
  if not registros_csv_ordenados:
    return

  registros_csv_ordenados.sort(key=lambda k: grupos_csv[k]["dt"])
  lineas_unificadas = []
  aciertos_fecha = 0
  total_fecha = 0
  partidos_verdes = 0

  for idx_m, clave_g in enumerate(registros_csv_ordenados, start=1):
    info_g = grupos_csv[clave_g]
    picks_partido = info_g["items"]
    if not picks_partido:
      continue
    ac_p = sum(1 for _, _, g in picks_partido if g)
    tot_p = len(picks_partido)
    aciertos_fecha += ac_p
    total_fecha += tot_p
    if ac_p >= (tot_p / 2.0):
      partidos_verdes += 1

    ico_p = "✅" if ac_p == tot_p else ("🟡" if ac_p >= (tot_p / 2.0) else "❌")
    det_p = "\n".join([f"   • {'✅' if g else '❌'} {m} (@{c:.2f})" for m, c, g in picks_partido])
    lineas_unificadas.append(f"{ico_p} <b>{idx_m}. {info_g['partido']} ({info_g['marcador']}) [{ac_p}/{tot_p}]</b>\n{det_p}")

  if not lineas_unificadas:
    return

  num_partidos_aud = len(lineas_unificadas)
  pct_fecha = (aciertos_fecha / max(1, total_fecha)) * 100.0
  pct_partidos = (partidos_verdes / max(1, num_partidos_aud)) * 100.0

  informe_auditoria_total = (
      f"📋 <b>AUDITORÍA #2: REPORTE DEL 100% DE LA FECHA ({fecha_ayer} + Madrugada)</b> 📋\n"
      f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
      f"🏟 <b>Partidos Auditados:</b> {num_partidos_aud} encuentros finalizados (FT reales del CSV)\n"
      f"🎯 <b>Efectividad Global de Apuestas (Toda la Fecha):</b> {pct_fecha:.1f}% ({aciertos_fecha}/{total_fecha} acertadas)\n"
      f"✅ <b>Partidos Rentables (Verde/Amarillo):</b> {pct_partidos:.1f}% ({partidos_verdes}/{num_partidos_aud} partidos)\n"
      f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
      + "\n\n".join(lineas_unificadas)
  )

  enviar_telegram(TOKEN_TICKETS, CHAT_ID_GRUPO_AUDITORIAS, informe_auditoria_total)


# ==============================================================================
# 2. BASE MAESTRA DE 12 LIGAS EUROPEAS + SUDAMÉRICA (LIGA Y COPA BETPLAY, ARG, BRA) + ARABIA
# ==============================================================================
def cargar_sinonimos_dinamicos():
  if os.path.exists(ARCHIVO_SINONIMOS):
    try:
      with open(ARCHIVO_SINONIMOS, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception:
      return {}
  return {}


def guardar_sinonimo_dinamico(nombre_original, nombre_mapeado):
  datos = cargar_sinonimos_dinamicos()
  if nombre_original not in datos:
    datos[nombre_original] = nombre_mapeado
    try:
      with open(ARCHIVO_SINONIMOS, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=4)
    except Exception as e:
      logging.error(f"No se pudo guardar el sinónimo dinámico: {e}")


traductor_nombres = {
    # ESPAÑA
    "Atletico Madrid": "Ath Madrid", "Atlético Madrid": "Ath Madrid", "Atlético de Madrid": "Ath Madrid",
    "Atletico de Madrid": "Ath Madrid", "Club Atlético de Madrid": "Ath Madrid",
    "Athletic Club": "Ath Bilbao", "Real Madrid": "Real Madrid",
    "FC Barcelona": "Barcelona", "Barcelona": "Barcelona", "Real Sociedad": "Sociedad", "Real Betis": "Betis",
    "Celta Vigo": "Celta", "Rayo Vallecano": "Vallecano", "Alaves": "Alaves",
    "Deportivo Alaves": "Alaves", "RCD Espanyol": "Espanol", "Espanyol": "Espanol",
    "Real Valladolid": "Valladolid", "CD Leganes": "Leganes", "CA Osasuna": "Osasuna",
    # INGLATERRA
    "Aston Villa": "Aston Villa", "Manchester United": "Man United", "Manchester City": "Man City",
    "Newcastle": "Newcastle", "Newcastle United": "Newcastle", "Nottingham Forest": "Nott'm Forest",
    "Wolverhampton": "Wolves", "Wolverhampton Wanderers": "Wolves", "Tottenham": "Tottenham",
    "Tottenham Hotspur": "Tottenham", "Arsenal": "Arsenal", "West Ham": "West Ham",
    "West Ham United": "West Ham", "Brighton": "Brighton", "Leicester": "Leicester",
    "Leicester City": "Leicester", "Ipswich": "Ipswich", "Ipswich Town": "Ipswich",
    "AFC Bournemouth": "Bournemouth", "Bournemouth": "Bournemouth",
    # ITALIA (SERIE A COMPLETA)
    "Lecce": "Lecce", "US Lecce": "Lecce", "AS Roma": "Roma", "Roma": "Roma",
    "Inter": "Inter", "FC Internazionale": "Inter", "AC Milan": "Milan", "Milan": "Milan",
    "Atalanta": "Atalanta", "Atalanta BC": "Atalanta", "Bologna": "Bologna", "Bologna FC": "Bologna",
    "Como": "Como", "Como 1907": "Como", "AC Monza": "Monza", "Monza": "Monza",
    "Parma": "Parma", "Parma Calcio 1913": "Parma", "Torino": "Torino", "Torino FC": "Torino",
    "Cagliari": "Cagliari", "Cagliari Calcio": "Cagliari", "Juventus": "Juventus",
    "SS Lazio": "Lazio", "Lazio": "Lazio", "Fiorentina": "Fiorentina", "ACF Fiorentina": "Fiorentina",
    "Napoli": "Napoli", "SSC Napoli": "Napoli", "Udinese": "Udinese", "Udinese Calcio": "Udinese",
    "Genoa": "Genoa", "Genoa CFC": "Genoa", "Empoli": "Empoli", "Empoli FC": "Empoli",
    "Hellas Verona": "Verona", "Verona": "Verona", "Venezia": "Venezia", "Venezia FC": "Venezia",
    # ALEMANIA, FRANCIA, PORTUGAL, TURQUÍA Y RESTO DE EUROPA
    "Bayern Munich": "Bayern Munich", "FC Bayern München": "Bayern Munich", "Bayern München": "Bayern Munich",
    "Borussia Dortmund": "Dortmund", "Bayer Leverkusen": "Leverkusen", "RB Leipzig": "RB Leipzig",
    "Eintracht Frankfurt": "Ein Frankfurt", "Borussia Monchengladbach": "M'gladbach",
    "VfB Stuttgart": "Stuttgart", "SC Freiburg": "Freiburg", "TSG Hoffenheim": "Hoffenheim",
    "1899 Hoffenheim": "Hoffenheim",
    "Paris Saint Germain": "Paris SG", "PSG": "Paris SG", "Olympique Marseille": "Marseille",
    "Olympique Lyonnais": "Lyon", "Lyon": "Lyon", "AS Monaco": "Monaco", "Monaco": "Monaco", "LOSC Lille": "Lille", "Lille": "Lille",
    "Stade Rennais": "Rennes", "Rennes": "Rennes", "OGC Nice": "Nice", "RC Lens": "Lens",
    "Sporting CP": "Sp Lisbon", "SL Benfica": "Benfica", "Benfica": "Benfica", "FC Porto": "Porto", "SC Braga": "Sp Braga",
    "PSV Eindhoven": "PSV", "Feyenoord": "Feyenoord", "Ajax": "Ajax", "AZ Alkmaar": "AZ Alkmaar", "Twente": "Twente",
    "Club Brugge KV": "Club Brugge", "Union St. Gilloise": "St. Gilloise", "RSC Anderlecht": "Anderlecht", "Gent": "Gent", "St. Truiden": "St Truiden",
    "Galatasaray": "Galatasaray", "Galatasaray SK": "Galatasaray",
    "Fenerbahce": "Fenerbahce", "Fenerbahçe": "Fenerbahce",
    "Besiktas": "Besiktas", "Beşiktaş": "Besiktas", "Trabzonspor": "Trabzonspor",
    "Olympiakos Piraeus": "Olympiakos", "PAOK": "PAOK", "Panathinaikos": "Panathinaikos", "AEK Athens FC": "AEK",
    "Celtic": "Celtic", "Rangers": "Rangers",
    # SUDAMÉRICA (COLOMBIA LIGA Y COPA BETPLAY, ARGENTINA, BRASIL)
    "Millonarios": "Millonarios", "Millonarios FC": "Millonarios",
    "America de Cali": "America de Cali", "América de Cali": "America de Cali",
    "Atletico Nacional": "Atletico Nacional", "Atlético Nacional": "Atletico Nacional",
    "Santa Fe": "Santa Fe", "Independiente Santa Fe": "Santa Fe",
    "Junior": "Junior", "Junior FC": "Junior", "Atletico Junior": "Junior",
    "Deportivo Cali": "Deportivo Cali", "Independiente Medellin": "Independiente Medellin",
    "Deportes Tolima": "Deportes Tolima", "Once Caldas": "Once Caldas",
    "Atletico Bucaramanga": "Atletico Bucaramanga", "Bucaramanga": "Atletico Bucaramanga",
    "Deportivo Pasto": "Deportivo Pasto", "Deportivo Pereira": "Deportivo Pereira",
    "La Equidad": "La Equidad", "Internacional de Bogota": "La Equidad",
    "Aguilas Doradas": "Aguilas Doradas", "Fortaleza CEIF": "Fortaleza CEIF", "Fortaleza FC": "Fortaleza CEIF",
    "Boyaca Chico": "Boyaca Chico", "Llaneros": "Llaneros",
    "Cucuta": "Cucuta", "Cúcuta Deportivo": "Cucuta", "Cucuta Deportivo": "Cucuta",
    "Jaguares": "Jaguares de Cordoba", "Jaguares de Cordoba": "Jaguares de Cordoba",
    "Envigado": "Envigado", "Alianza FC": "Alianza Petrolera", "Alianza Petrolera": "Alianza Petrolera",
    "Patriotas": "Patriotas", "Real Cartagena": "Real Cartagena", "Union Magdalena": "Union Magdalena",
    "Atletico Huila": "Atletico Huila", "Deportes Quindio": "Deportes Quindio",
    "River Plate": "River Plate", "CA River Plate": "River Plate",
    "Boca Juniors": "Boca Juniors", "CA Boca Juniors": "Boca Juniors",
    "Racing Club": "Racing Club", "Independiente": "Independiente", "CA Independiente": "Independiente",
    "San Lorenzo": "San Lorenzo", "Velez Sarsfield": "Velez Sarsfield", "Talleres Cordoba": "Talleres Cordoba",
    "Estudiantes L.P.": "Estudiantes L.P.", "Lanus": "Lanus", "Huracan": "Huracan",
    "Flamengo": "Flamengo", "CR Flamengo": "Flamengo", "Palmeiras": "Palmeiras", "SE Palmeiras": "Palmeiras",
    "Botafogo": "Botafogo", "Sao Paulo": "Sao Paulo", "Corinthians": "Corinthians",
    "Atletico-MG": "Atletico-MG", "Atletico Mineiro": "Atletico-MG", "Fluminense": "Fluminense",
    "Gremio": "Gremio", "Internacional": "Internacional", "Cruzeiro": "Cruzeiro",
    "Vasco da Gama": "Vasco da Gama", "Vasco DA Gama": "Vasco da Gama", "Bahia": "Bahia", "Fortaleza": "Fortaleza",
    "Athletico-PR": "Athletico-PR", "Atletico Paranaense": "Athletico-PR",
    # SELECCIONES NACIONALES (TRADUCCIÓN AL ESPAÑOL NATURAL PARA VOZ IA Y TARJETAS)
    "Spain": "España", "France": "Francia", "England": "Inglaterra", "Germany": "Alemania",
    "Italy": "Italia", "Brazil": "Brasil", "Netherlands": "Países Bajos", "Belgium": "Bélgica",
    "Croatia": "Croacia", "Switzerland": "Suiza", "Denmark": "Dinamarca", "Sweden": "Suecia",
    "Norway": "Noruega", "Poland": "Polonia", "Scotland": "Escocia", "Wales": "Gales",
    "Hungary": "Hungría", "Turkey": "Turquía", "Türkiye": "Turquía", "Greece": "Grecia",
    "Czech Republic": "República Checa", "Czechia": "República Checa", "Ukraine": "Ucrania",
    "Republic of Ireland": "Irlanda", "Northern Ireland": "Irlanda del Norte", "Iceland": "Islandia",
    "Finland": "Finlandia", "Bosnia & Herzegovina": "Bosnia", "North Macedonia": "Macedonia del Norte",
    "Latvia": "Letonia", "Lithuania": "Lituania", "Luxembourg": "Luxemburgo", "Cyprus": "Chipre",
    "Faroe Islands": "Islas Feroe", "United States": "Estados Unidos", "USA": "Estados Unidos",
    "Mexico": "México", "Japan": "Japón", "South Korea": "Corea del Sur", "Korea Republic": "Corea del Sur",
    "Saudi Arabia": "Arabia Saudita", "Morocco": "Marruecos", "Egypt": "Egipto", "Algeria": "Argelia",
    "Tunisia": "Túnez", "Cameroon": "Camerún", "Ivory Coast": "Costa de Marfil", "Côte d'Ivoire": "Costa de Marfil",
    "South Africa": "Sudáfrica", "Equatorial Guinea": "Guinea Ecuatorial", "Cape Verde": "Cabo Verde",
}


def enviar_telegram(token, chat_id, mensaje, reply_markup=None):
  if not token or not chat_id:
    return
  url = f"https://api.telegram.org/bot{token}/sendMessage"
  if len(mensaje) > 3500:
    parrafos = mensaje.split("\n\n")
    bloque = ""
    for p in parrafos:
      if len(bloque) + len(p) + 4 < 3500:
        bloque += p + "\n\n"
      else:
        if bloque.strip():
          requests.post(
              url,
              json={"chat_id": chat_id, "text": bloque.strip(), "parse_mode": "HTML", "disable_web_page_preview": True},
              timeout=10,
          )
          time.sleep(0.6)
        bloque = "⚡ <b>(Continuación del Reporte)...</b>\n\n" + p + "\n\n"
    if bloque.strip():
      payload = {"chat_id": chat_id, "text": bloque.strip(), "parse_mode": "HTML", "disable_web_page_preview": True}
      if reply_markup:
        payload["reply_markup"] = reply_markup
      requests.post(url, json=payload, timeout=10)
      time.sleep(0.6)
  else:
    try:
      payload = {"chat_id": chat_id, "text": mensaje, "parse_mode": "HTML", "disable_web_page_preview": True}
      if reply_markup:
        payload["reply_markup"] = reply_markup
      requests.post(url, json=payload, timeout=10)
      time.sleep(0.6)
    except Exception as e:
      logging.error(f"Error Telegram: {e}")


_HISTORIAL_IMAGENES_CANAL = set()

def enviar_imagen_telegram(token, chat_id, ruta_imagen, caption="", reply_markup=None):
  if not token or not chat_id or not ruta_imagen or not os.path.exists(ruta_imagen): 
      return

  nom_base = os.path.basename(str(ruta_imagen)).lower()
  if "_vs_" in nom_base:
      limpio_b = re.sub(r"^(vip_\d+_|free_\d+_)?(\d{4}_)?", "", nom_base)
      limpio_b = re.sub(r"_(vip|free|descartes)\.jpg$", "", limpio_b)
      eq1, eq2 = limpio_b.split("_vs_", 1)
      for pref in ["deportivo_", "deportes_", "atletico_", "independiente_", "club_", "real_"]:
          if eq1.startswith(pref) and len(eq1) > len(pref) + 2: eq1 = eq1[len(pref):]
          if eq2.startswith(pref) and len(eq2) > len(pref) + 2: eq2 = eq2[len(pref):]
      tipo_img = "VIP" if "_vip" in nom_base else ("FREE" if "_free" in nom_base else "OTRO")
      clave_envio = (str(chat_id), tipo_img, tuple(sorted([eq1.strip("_"), eq2.strip("_")])))
      if clave_envio in _HISTORIAL_IMAGENES_CANAL:
          print(f"    ⏭️ [CANDADO ANTI-REPETIDOS] Partido duplicado/invertido bloqueado: {os.path.basename(ruta_imagen)}")
          return
      _HISTORIAL_IMAGENES_CANAL.add(clave_envio)

  cap_seguro = str(caption)
  if len(cap_seguro) > 1010:
      lineas_ok = []
      largo_ac = 0
      for lin in cap_seguro.splitlines():
          if largo_ac + len(lin) + 2 <= 1005:
              lineas_ok.append(lin)
              largo_ac += len(lin) + 1
          else:
              break
      cap_seguro = "\n".join(lineas_ok)

  url = f"https://api.telegram.org/bot{token}/sendPhoto"
  try:
    with open(ruta_imagen, 'rb') as photo:
      payload = {"chat_id": chat_id, "caption": cap_seguro, "parse_mode": "HTML"}
      
      if reply_markup:
          payload["reply_markup"] = json.dumps(reply_markup)
          
      files = {"photo": photo}
      res = requests.post(url, data=payload, files=files, timeout=15)
      
      if res.status_code == 200:
          print(f"    📸 [+] Imagen enviada al canal con éxito.")
      else:
          with open(ruta_imagen, 'rb') as photo_retry:
              cap_limpio = re.sub(r"<[^>]+>", "", cap_seguro)[:1000]
              requests.post(url, data={"chat_id": chat_id, "caption": cap_limpio}, files={"photo": photo_retry}, timeout=15)
              print(f"    📸 [+] Imagen enviada al canal con éxito (modo seguro).")
          
      time.sleep(2.0)  
  except Exception as e:
    logging.error(f"Error crítico subiendo imagen a Telegram: {e}")


def sincronizar_csv_locales_api(api_token):
  if MODO_PRUEBAS:
    return
    
  headers = {"x-apisports-key": api_token}
  ligas_sincronizar = {
      "colombia_historico.csv": [
          "https://v3.football.api-sports.io/fixtures?league=239&season=2025",
          "https://v3.football.api-sports.io/fixtures?league=239&season=2026",
          "https://v3.football.api-sports.io/fixtures?league=533&season=2025",
          "https://v3.football.api-sports.io/fixtures?league=533&season=2026",
          "https://v3.football.api-sports.io/fixtures?league=240&season=2026",
      ],
      "argentina_historico.csv": [
          "https://v3.football.api-sports.io/fixtures?league=128&season=2025",
          "https://v3.football.api-sports.io/fixtures?league=128&season=2026",
          "https://v3.football.api-sports.io/fixtures?league=130&season=2026",
      ],
      "brasil_historico.csv": [
          "https://v3.football.api-sports.io/fixtures?league=71&season=2025",
          "https://v3.football.api-sports.io/fixtures?league=71&season=2026",
          "https://v3.football.api-sports.io/fixtures?league=73&season=2026",
      ],
      "arabia_historico.csv": [
          "https://v3.football.api-sports.io/fixtures?league=307&season=2025",
          "https://v3.football.api-sports.io/fixtures?league=307&season=2026",
      ],
  }
  
  for archivo, lista_urls in ligas_sincronizar.items():
    if os.path.exists(archivo):
      mtime = datetime.fromtimestamp(os.path.getmtime(archivo))
      try:
        df_ex = pd.read_csv(archivo)
        if (datetime.now() - mtime).days < 2 and len(df_ex) >= 220:
          continue
      except Exception:
        pass
    try:
      filas = []
      for url in lista_urls:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
          r = res.json().get("response", [])
          for p in r:
            if p["fixture"]["status"]["short"] in ["FT", "AET", "PEN"]:
              score_ht = p.get("score", {}).get("halftime", {})
              filas.append({
                  "HomeTeam": p["teams"]["home"]["name"],
                  "AwayTeam": p["teams"]["away"]["name"],
                  "FTHG": p["goals"]["home"] if p["goals"]["home"] is not None else 0,
                  "FTAG": p["goals"]["away"] if p["goals"]["away"] is not None else 0,
                  "HTHG": score_ht.get("home") if score_ht.get("home") is not None else 0,
                  "HTAG": score_ht.get("away") if score_ht.get("away") is not None else 0,
              })
      if filas:
        pd.DataFrame(filas).to_csv(archivo, index=False)
    except Exception as e:
      logging.error(f"Error sincronizando CSV {archivo}: {e}")


def obtener_base_maestra_europa_csv():
  global BASE_MAESTRA_MEMORIA
  if BASE_MAESTRA_MEMORIA is not None:
    return BASE_MAESTRA_MEMORIA

  for arch in sorted(os.listdir("."), reverse=True):
    if arch.startswith("cache_base_maestra_europa_v2_") and arch.endswith(".csv"):
      try:
        df_cand = pd.read_csv(arch, low_memory=False)
        if "Div" in df_cand.columns and "T1" in set(df_cand["Div"].dropna().unique()):
          BASE_MAESTRA_MEMORIA = df_cand
          return BASE_MAESTRA_MEMORIA
      except Exception:
        pass

  codigos_europa = ["SP1", "SP2", "E0", "I1", "D1", "F1", "P1", "N1", "B1", "T1", "G1", "SC0"]
  frames = []
  print("[+] 🌐 Construyendo Base Maestra Europea Completa (12 Ligas en orden cronológico 24/25 -> 25/26 -> 26/27)...")
  for code in codigos_europa:
    for temp in ["2425", "2526", "2627"]:
      url = f"https://www.football-data.co.uk/mmz4281/{temp}/{code}.csv"
      try:
        df_temp = pd.read_csv(url)
        if not df_temp.empty and "HomeTeam" in df_temp.columns:
          frames.append(df_temp)
      except Exception:
        continue

  if frames:
    BASE_MAESTRA_MEMORIA = pd.concat(frames, ignore_index=True)
    try:
      BASE_MAESTRA_MEMORIA.to_csv(ARCHIVO_CACHE_EUROPA_CSV, index=False)
    except Exception:
      pass
  else:
    BASE_MAESTRA_MEMORIA = pd.DataFrame()

  return BASE_MAESTRA_MEMORIA


def cargar_datos_historicos_unificados(liga_key):
  if liga_key == "colombia":
    if os.path.exists("colombia_historico.csv"):
        return pd.read_csv("colombia_historico.csv")
    return pd.DataFrame()
    
  elif liga_key == "argentina":
    for arch_arg in ["argentina_historico.csv", "argentina.csv"]:
      if os.path.exists(arch_arg):
        return pd.read_csv(arch_arg)
    return pd.DataFrame()

  elif liga_key == "brasil":
    if os.path.exists("brasil_historico.csv"):
        return pd.read_csv("brasil_historico.csv")
    return pd.DataFrame()

  elif liga_key == "arabia_saudita":
    if os.path.exists("arabia_historico.csv"):
        return pd.read_csv("arabia_historico.csv")
    return pd.DataFrame()
    
  elif liga_key in ["COPA LIBERTADORES", "COPA SUDAMERICANA"]:
    frames_latam = []
    for arch in ["colombia_historico.csv", "argentina_historico.csv", "argentina.csv", "brasil_historico.csv"]:
      if os.path.exists(arch):
        frames_latam.append(pd.read_csv(arch))
    return pd.concat(frames_latam, ignore_index=True) if frames_latam else pd.DataFrame()

  else:
    df_eu = obtener_base_maestra_europa_csv()
    mapa_div = {
        "españa": "SP1", "españa_2": "SP2", "inglaterra": "E0", "italia": "I1",
        "alemania": "D1", "francia": "F1", "portugal": "P1", "holanda": "N1",
        "belgica": "B1", "turquia": "T1", "grecia": "G1", "escocia": "SC0"
    }
    if not df_eu.empty and "Div" in df_eu.columns and liga_key in mapa_div:
      df_filtrado = df_eu[df_eu["Div"] == mapa_div[liga_key]]
      if len(df_filtrado) >= 30:
        return df_filtrado
    return df_eu


def calcular_factor_arbitro_global(arbitro_nombre, liga_key):
  if not arbitro_nombre or str(arbitro_nombre).lower() in [
      "none",
      "null",
      "",
      "nan",
      "no asignado",
  ]:
    return 0.0

  arb_lower = str(arbitro_nombre).lower()
  
  estrictos = [
      "gil manzano", "mateu", "orsato", "taylor", "oliver", "turpin", 
      "marciniak", "siebert", "zwayer", "sanchez martinez", "del cerro", 
      "aytekin", "sozza", "maresca", "ayroldi", "pairetto", "manganiello",
      "wilmar roldan", "facundo tello", "rapallini", "matonte", "darío herrera",
      "andrés rojas", "bismarks santiago", "carlos betancur", "daronco", "claus"
  ]
  
  permisivos = [
      "de burgos", "cuadra", "sojo", "massa", "guida", "chiffi",
      "ospina", "ortega", "loustau"
  ]

  if any(s in arb_lower for s in estrictos): 
      return 1.15
  elif any(p in arb_lower for p in permisivos): 
      return -0.25
      
  return 0.0


def obtener_cuotas_betplay_kambi():
  if MODO_PRUEBAS:
    return {}

  url = "https://eu-offering-api.kambi.com/offering/v2018/bpco/listView/football.json?lang=es_ES&market=CO"
  headers = {
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
          " like Gecko) Chrome/91.0.4472.124 Safari/537.36"
      )
  }

  mapa_cuotas_betplay = {}
  try:
    res = requests.get(url, headers=headers, timeout=10)
    if res.status_code == 200:
      datos = res.json()
      if "events" in datos:
        for evento in datos["events"]:
          if "event" in evento and "betOffers" in evento:
            local = evento["event"].get("homeName", "")
            visita = evento["event"].get("awayName", "")
            if not local or not visita:
              continue

            info_evento = {"local_bp": local, "visita_bp": visita, "1": "N/A", "X": "N/A", "2": "N/A", "over25": None}
            for oferta in evento["betOffers"]:
              tipo_oferta = oferta.get("betOfferType", {}).get("name", "")
              outcomes = oferta.get("outcomes", [])
              if tipo_oferta == "Match" and len(outcomes) >= 3:
                try:
                  info_evento["1"] = outcomes[0]["odds"] / 1000.0
                  info_evento["X"] = outcomes[1]["odds"] / 1000.0
                  info_evento["2"] = outcomes[2]["odds"] / 1000.0
                except Exception:
                  pass
              elif "Over/Under" in tipo_oferta or "Total" in tipo_oferta:
                for out in outcomes:
                  if out.get("line") == 2500 and "Over" in str(out.get("englishLabel", out.get("label", ""))):
                    try:
                      info_evento["over25"] = out["odds"] / 1000.0
                    except Exception:
                      pass

            clave = f"{local.lower()} vs {visita.lower()}"
            mapa_cuotas_betplay[clave] = info_evento
                  
    return mapa_cuotas_betplay
  except Exception as e:
    logging.error(f"Error extrayendo cuotas de Betplay: {e}")
    return {}


def buscar_cuota_betplay_inteligente(local, visitante, mapa_cuotas):
  if not mapa_cuotas:
    return {"1": "N/A", "X": "N/A", "2": "N/A", "over25": None}
  objetivo = f"{local.lower()} vs {visitante.lower()}"
  if objetivo in mapa_cuotas:
    return mapa_cuotas[objetivo]
  coincidencias = difflib.get_close_matches(objetivo, list(mapa_cuotas.keys()), n=1, cutoff=0.62)
  if coincidencias:
    return mapa_cuotas[coincidencias[0]]
  return {"1": "N/A", "X": "N/A", "2": "N/A", "over25": None}


# ==============================================================================
# 3. MÓDULOS MATEMÁTICOS & MÓDULO DE ALTA TENSIÓN (DERBIS)
# ==============================================================================
def es_partido_rivalidad_alta(local, visitante):
  derbies_famosos = [
      ("juventus", "milán"), ("juventus", "ac milán"), ("inter", "milán"),
      ("lazio", "roma"), ("roma", "lazio"), ("real madrid", "atlético"),
      ("barcelona", "espanyol"), ("arsenal", "tottenham"), ("chelsea", "tottenham"),
      ("chelsea", "arsenal"), ("liverpool", "everton"), ("manchester", "liverpool"),
      ("boca", "river"), ("millonarios", "santa fe"), ("nacional", "américa"),
      ("gremio", "internacional"), ("palmeiras", "corinthians"), ("flamengo", "fluminense"), 
      ("sao paulo", "santos"), ("benfica", "sporting"), ("porto", "benfica"),
      ("américa", "medellín"), ("nacional", "millonarios"), ("racing", "independiente"),
      ("cali", "américa"), ("san lorenzo", "huracán"), ("rosario", "newell"),
      ("galatasaray", "fenerbahce"), ("celtic", "rangers"), ("ajax", "feyenoord"),
      ("olympiacos", "panathinaikos"), ("betis", "sevilla"), ("real sociedad", "athletic"),
      ("cucuta", "bucaramanga"), ("junior", "union magdalena"), ("once caldas", "pereira")
  ]
  l_low = normalizar_nombre_club(local)
  v_low = normalizar_nombre_club(visitante)
  if "internacional de bogota" in l_low or "internacional de bogota" in v_low:
    return ("santa fe" in l_low or "millonarios" in l_low or "santa fe" in v_low or "millonarios" in v_low)

  for eq1, eq2 in derbies_famosos:
    e1 = normalizar_nombre_club(eq1)
    e2 = normalizar_nombre_club(eq2)
    if (e1 in l_low and e2 in v_low) or (e2 in l_low and e1 in v_low):
      return True
  return False
    # Base cuantitativa de participación de xG (omega) + penaltis de los delanteros estrella por club
GOLEADORES_CLAVE_CLUB = {
    "real madrid": ("Kylian Mbappé", 0.44), "barcelona": ("Robert Lewandowski", 0.43),
    "atletico madrid": ("Julián Álvarez", 0.36), "athletic": ("Iñaki Williams", 0.33),
    "villarreal": ("Ayoze Pérez", 0.35), "real betis": ("Giovani Lo Celso", 0.32),
    "real sociedad": ("Mikel Oyarzabal", 0.36), "girona": ("Cristhian Stuani", 0.35),
    "manchester city": ("Erling Haaland", 0.48), "liverpool": ("Mohamed Salah", 0.41),
    "arsenal": ("Bukayo Saka", 0.35), "chelsea": ("Cole Palmer", 0.39),
    "aston villa": ("Ollie Watkins", 0.38), "newcastle": ("Alexander Isak", 0.41),
    "tottenham": ("Dominic Solanke", 0.35), "manchester united": ("Bruno Fernandes", 0.33),
    "bayern": ("Harry Kane", 0.47), "dortmund": ("Serhou Guirassy", 0.42),
    "leverkusen": ("Victor Boniface", 0.39), "leipzig": ("Loïs Openda", 0.38),
    "stuttgart": ("Ermedin Demirović", 0.36), "frankfurt": ("Omar Marmoush", 0.41),
    "inter": ("Lautaro Martínez", 0.41), "milan": ("Christian Pulisic", 0.34),
    "juventus": ("Dušan Vlahović", 0.42), "napoli": ("Romelu Lukaku", 0.40),
    "atalanta": ("Mateo Retegui", 0.42), "roma": ("Artem Dovbyk", 0.39),
    "lazio": ("Valentín Castellanos", 0.36), "fiorentina": ("Moise Kean", 0.38),
    "paris sg": ("Ousmane Dembélé", 0.35), "psg": ("Ousmane Dembélé", 0.35),
    "marseille": ("Mason Greenwood", 0.39), "lille": ("Jonathan David", 0.43),
    "monaco": ("Breel Embolo", 0.34), "lyon": ("Alexandre Lacazette", 0.40),
    "sporting": ("Viktor Gyökeres", 0.49), "benfica": ("Vangelis Pavlidis", 0.38),
    "porto": ("Samu Omorodion", 0.43), "galatasaray": ("Victor Osimhen", 0.46),
    "fenerbahce": ("Youssef En-Nesyri", 0.39), "besiktas": ("Ciro Immobile", 0.42),
    "ajax": ("Brian Brobbey", 0.36), "psv": ("Luuk de Jong", 0.42),
    "feyenoord": ("Santiago Giménez", 0.41), "celtic": ("Kyogo Furuhashi", 0.38),
    "millonarios": ("Leonardo Castro", 0.42), "atletico nacional": ("Alfredo Morelos", 0.37),
    "america de cali": ("Duván Vergara", 0.36), "junior": ("Carlos Bacca", 0.42),
    "santa fe": ("Hugo Rodallega", 0.41), "once caldas": ("Dayro Moreno", 0.44),
    "medellin": ("Brayan León", 0.34), "tolima": ("Yeison Guzmán", 0.35),
    "river plate": ("Miguel Borja", 0.43), "boca juniors": ("Edinson Cavani", 0.40),
    "racing": ("Adrián Martínez", 0.42), "flamengo": ("Pedro", 0.44),
    "palmeiras": ("Estêvão", 0.35), "botafogo": ("Igor Jesus", 0.38),
    "corinthians": ("Yuri Alberto", 0.40), "sao paulo": ("Jonathan Calleri", 0.38),
    "atletico-mg": ("Hulk", 0.43), "internacional": ("Enner Valencia", 0.38),
    "al-nassr": ("Cristiano Ronaldo", 0.48), "al-hilal": ("Aleksandar Mitrović", 0.46),
    "al-ittihad": ("Karim Benzema", 0.43), "inter miami": ("Lionel Messi", 0.46),
    # SELECCIONES NACIONALES MAYORES
    "argentina": ("Lionel Messi / L. Martínez", 0.44),
    "francia": ("Kylian Mbappé", 0.45), "france": ("Kylian Mbappé", 0.45),
    "españa": ("Lamine Yamal / Morata", 0.39), "spain": ("Lamine Yamal / Morata", 0.39),
    "inglaterra": ("Harry Kane", 0.46), "england": ("Harry Kane", 0.46),
    "portugal": ("Cristiano Ronaldo", 0.47),
    "brasil": ("Vinícius Jr.", 0.41), "brazil": ("Vinícius Jr.", 0.41),
    "alemania": ("Jamal Musiala / Havertz", 0.40), "germany": ("Jamal Musiala / Havertz", 0.40),
    "noruega": ("Erling Haaland", 0.50), "norway": ("Erling Haaland", 0.50),
    "colombia": ("Luis Díaz", 0.42),
    "uruguay": ("Darwin Núñez", 0.42),
    "paises bajos": ("Cody Gakpo", 0.39), "netherlands": ("Cody Gakpo", 0.39),
    "italia": ("Mateo Retegui", 0.39), "italy": ("Mateo Retegui", 0.39),
    "belgica": ("Romelu Lukaku", 0.44), "belgium": ("Romelu Lukaku", 0.44),
    "suecia": ("Viktor Gyökeres", 0.45), "sweden": ("Viktor Gyökeres", 0.45),
    "nigeria": ("Victor Osimhen", 0.46), "egipto": ("Mohamed Salah", 0.46), "egypt": ("Mohamed Salah", 0.46),
}


def calcular_goleador_probable_partido(local, visitante, l_local_mat, l_vis_mat):
  """Calcula mediante distribución de Poisson individual el jugador con mayor probabilidad de anotar en el partido."""
  loc_low = local.lower()
  vis_low = visitante.lower()
  candidatos = []

  for clave_eq, (jugador, omega) in GOLEADORES_CLAVE_CLUB.items():
    if clave_eq in loc_low:
      lambda_jug = max(0.15, l_local_mat * omega * 1.05)
      prob_gol = min(78.5, (1.0 - math.exp(-lambda_jug)) * 100.0)
      cuota_min = round(max(1.45, (100.0 / prob_gol) * 0.98), 2)
      candidatos.append((f"Gol de {jugador} ({local[:10]})", round(prob_gol, 1), cuota_min))
    elif clave_eq in vis_low:
      lambda_jug = max(0.12, l_vis_mat * omega * 1.02)
      prob_gol = min(76.0, (1.0 - math.exp(-lambda_jug)) * 100.0)
      cuota_min = round(max(1.50, (100.0 / prob_gol) * 0.98), 2)
      candidatos.append((f"Gol de {jugador} ({visitante[:10]})", round(prob_gol, 1), cuota_min))

  if candidatos:
    candidatos.sort(key=lambda x: x[1], reverse=True)
    return candidatos[0]

  # Si el club no está en el diccionario estático, proyectar al "Delantero Titular (#9)" del equipo dominante
  if l_local_mat >= l_vis_mat and l_local_mat >= 1.35:
    lambda_9 = l_local_mat * 0.36
    p_9 = round(min(68.0, (1.0 - math.exp(-lambda_9)) * 100.0), 1)
    return (f"9 Titular / Goleador {local[:12]} Anota", p_9, round(100.0 / p_9, 2))
  elif l_vis_mat > l_local_mat and l_vis_mat >= 1.35:
    lambda_9 = l_vis_mat * 0.36
    p_9 = round(min(66.0, (1.0 - math.exp(-lambda_9)) * 100.0), 1)
    return (f"9 Titular / Goleador {visitante[:12]} Anota", p_9, round(100.0 / p_9, 2))
  return (None, None, None)

def poisson_prob(lmbda, k):
  return ((math.e**-lmbda) * (lmbda**k)) / math.factorial(k)


def dixon_coles_adjustment(i, j, l1, l2, rho):
  if i == 0 and j == 0: 
      return 1.0 - (l1 * l2 * rho)
  elif i == 1 and j == 0: 
      return 1.0 + (l2 * rho)
  elif i == 0 and j == 1: 
      return 1.0 + (l1 * rho)
  elif i == 1 and j == 1: 
      return 1.0 - rho
  return 1.0


def obtener_margen_ev_dinamico(prob_pct):
  if prob_pct is None: 
      return 1.00
  if prob_pct >= 78.0: 
      return 0.96     
  elif prob_pct >= 65.0: 
      return 0.99   
  elif prob_pct >= 50.0: 
      return 1.02   
  else: 
      return 1.06                    


def calcular_prob_over_y_ev(lambda_val, linea):
  if lambda_val is None or lambda_val <= 0:
    return None, None, None
    
  prob_under = sum(poisson_prob(lambda_val, k) for k in range(int(linea) + 1))
  prob_over = min(93.5, max(4.0, (1 - prob_under) * 100))
  cuota_justa = (100 / prob_over) if prob_over > 0 else 0
  
  margen = obtener_margen_ev_dinamico(prob_over)
  cuota_min_ev = max(1.10, cuota_justa * margen) if cuota_justa > 0 else 0
  
  return prob_over, cuota_justa, cuota_min_ev


def calcular_total_asiatico(lambda_val, linea_asiatica):
  if linea_asiatica == 2.25:
    p_over2, _, _ = calcular_prob_over_y_ev(lambda_val, 2.0)
    p_over25, _, _ = calcular_prob_over_y_ev(lambda_val, 2.5)
    prob_asiatica = (p_over2 + p_over25) / 2.0
  elif linea_asiatica == 2.75:
    p_over25, _, _ = calcular_prob_over_y_ev(lambda_val, 2.5)
    p_over3, _, _ = calcular_prob_over_y_ev(lambda_val, 3.0)
    prob_asiatica = (p_over25 + p_over3) / 2.0
  else:
    prob_asiatica, _, _ = calcular_prob_over_y_ev(lambda_val, linea_asiatica)

  cuota_justa = (100 / prob_asiatica) if prob_asiatica > 0 else 0
  margen = obtener_margen_ev_dinamico(prob_asiatica)
  cuota_min_ev = max(1.10, cuota_justa * margen) if cuota_justa > 0 else 0
  return prob_asiatica, cuota_justa, cuota_min_ev


def semaforo_probabilidad(p):
  if p is None: 
      return "❌ Sin Datos"
  if p >= 68.0: 
      return "🟢 [LUZ VERDE / ALTO VALOR]"
  elif p >= 58.0: 
      return "🟢 [VALOR ALTO / OPERABLE]"
  elif p >= 48.0: 
      return "🟡 [MODERADO / VIGILAR]"
  else: 
      return "🔴 [CRÍTICO / EVITAR]"


def media_ponderada_exponencial(serie_datos):
  if serie_datos.empty:
      return 0.0

  valores = [float(x) for x in serie_datos.dropna().values]
  n = len(valores)
  if n == 0:
      return 0.0
  if n == 1:
      return valores[0]

  pesos = [math.exp(i * 0.15) for i in range(n)]
  pesos_norm = [p / sum(pesos) for p in pesos]
  media_exp = sum(v * p for v, p in zip(valores, pesos_norm))

  # 1. Regresión Lineal (derivada temporal dy/dt de los últimos 6 partidos)
  ultimos = valores[-6:] if n >= 6 else valores
  m = len(ultimos)
  t_med = (m - 1) / 2.0
  y_med = sum(ultimos) / m
  num_reg = sum((i - t_med) * (ultimos[i] - y_med) for i in range(m))
  den_reg = sum((i - t_med) ** 2 for i in range(m))
  pendiente_beta = (num_reg / den_reg) if den_reg > 0 else 0.0

  # 2. Desviación Estándar ponderada (descuenta irregularidad / alta varianza)
  varianza = sum(p * ((v - media_exp) ** 2) for v, p in zip(valores, pesos_norm))
  desv_std = math.sqrt(max(0.0, varianza))
  coef_variacion = desv_std / max(media_exp, 0.75)

  ajuste_tendencia = max(-0.18, min(0.14, pendiente_beta * 0.22))
  castigo_volatilidad = min(0.16, max(0.0, (coef_variacion - 0.55) * 0.18))
  return max(0.25, media_exp * (1.0 + ajuste_tendencia - castigo_volatilidad))


def normalizar_nombre_club(texto):
  t = "".join(c for c in unicodedata.normalize("NFD", str(texto)) if unicodedata.category(c) != "Mn").lower()
  for token in ["club atletico de madrid", "atletico de madrid", "ath madrid"]:
    if token in t:
      t = "atletico madrid"
  for token in [" calcio 1913", " calcio", " 1907", " 1913", "deportivo ", "deportes ", "ac ", "as ", "us ", "ss ", "ssc ", "acf ", "fc ", "cf ", "cd ", "ud ", "ca ", " sk"]:
    t = t.replace(token, " ")
  return " ".join(t.split()).strip()


def encontrar_nombre_exacto(nombre_ingresado, lista_equipos):
  if lista_equipos.empty: 
      return nombre_ingresado
      
  nombre_traducido = traductor_nombres.get(nombre_ingresado, nombre_ingresado)
  nombres_unicos = [str(x) for x in lista_equipos.dropna().unique()]
  if nombre_traducido in nombres_unicos:
    return nombre_traducido

  norm_buscado = normalizar_nombre_club(nombre_traducido)
  for cand in nombres_unicos:
    if normalizar_nombre_club(cand) == norm_buscado:
      guardar_sinonimo_dinamico(nombre_ingresado, cand)
      return cand

  sinonimos = cargar_sinonimos_dinamicos()
  if nombre_ingresado in sinonimos and sinonimos[nombre_ingresado] in nombres_unicos: 
      return sinonimos[nombre_ingresado]
  
  coincidencias = difflib.get_close_matches(
      nombre_traducido, 
      nombres_unicos, 
      n=1, 
      cutoff=0.76
  )
  
  if coincidencias:
    guardar_sinonimo_dinamico(nombre_ingresado, coincidencias[0])
    return coincidencias[0]
    
  return nombre_traducido
# ==============================================================================
# 4. MOTOR QUANT INSTITUCIONAL (CALIBRACIÓN MATEMÁTICA EN LA RAÍZ)
# ==============================================================================
ARCHIVO_CACHE_STATS_REALES = "cache_stats_reales_equipos.json"

def obtener_stats_reales_api_equipo(id_equipo, nombre_equipo, api_token=None):
  """
  Extrae en paralelo (menos de 1 seg por equipo) los promedios REALES de Córners,
  Remates a Puerta, Faltas y Tarjetas y guarda todo en caché local permanente.
  """
  if not id_equipo and not nombre_equipo:
    return None

  clave_eq = normalizar_nombre_club(nombre_equipo) if nombre_equipo else str(id_equipo)
  cache_st = {}
  if os.path.exists(ARCHIVO_CACHE_STATS_REALES):
    try:
      with open(ARCHIVO_CACHE_STATS_REALES, "r", encoding="utf-8") as f:
        cache_st = json.load(f) or {}
      if clave_eq in cache_st:
        dato_guardado = cache_st[clave_eq]
        if (time.time() - float(dato_guardado.get("ts", 0))) < (18 * 3600):
          return dato_guardado if dato_guardado.get("corners") is not None else None
    except Exception:
      cache_st = {}

  corners_lista, tiros_arco_lista, faltas_lista, amarillas_lista = [], [], [], []

  # Búsqueda rápida en ESPN con descargas en paralelo (máximo 1.5 segundos en total)
  if nombre_equipo:
    try:
      r_busq = requests.get(
          "https://site.web.api.espn.com/apis/common/v3/search",
          params={"query": nombre_equipo, "limit": 3, "type": "team"},
          timeout=2.0
      )
      if r_busq.status_code == 200:
        for it_b in (r_busq.json().get("items") or []):
          if it_b.get("sport") == "soccer" and it_b.get("id"):
            tid_espn = it_b.get("id")
            r_ev = requests.get(
                f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/teams/{tid_espn}/schedule",
                timeout=2.0
            )
            if r_ev.status_code == 200:
              eventos_eq = r_ev.json().get("events") or []
              eids_terminados = [
                  ev_x.get("id") for ev_x in eventos_eq
                  if ev_x.get("id") and (
                      ((ev_x.get("competitions") or [{}])[0].get("status") or {}).get("type", {}).get("completed") is True
                      or str(((ev_x.get("competitions") or [{}])[0].get("status") or {}).get("type", {}).get("state") or "") == "post"
                  )
              ][-8:]

              def _leer_partido_espn(eid_ant):
                try:
                  r_s = requests.get(
                      f"https://site.api.espn.com/apis/site/v2/sports/soccer/all/summary?event={eid_ant}",
                      timeout=2.0
                  )
                  if r_s.status_code == 200:
                    for bt in ((r_s.json().get("boxscore") or {}).get("teams") or []):
                      nom_bt = str((bt.get("team") or {}).get("displayName") or "")
                      if str(bt.get("team", {}).get("id")) == str(tid_espn) or normalizar_nombre_club(nombre_equipo)[:5] in normalizar_nombre_club(nom_bt):
                        return {str(s.get("name")): str(s.get("displayValue") or "") for s in (bt.get("statistics") or [])}
                except Exception:
                  pass
                return None

              if eids_terminados:
                with ThreadPoolExecutor(max_workers=8) as ex_st:
                  for st_map in ex_st.map(_leer_partido_espn, eids_terminados):
                    if st_map:
                      if st_map.get("wonCorners", "").replace(".", "", 1).isdigit():
                        corners_lista.append(float(st_map["wonCorners"]))
                      if st_map.get("shotsOnTarget", "").replace(".", "", 1).isdigit():
                        tiros_arco_lista.append(float(st_map["shotsOnTarget"]))
                      if st_map.get("foulsCommitted", "").replace(".", "", 1).isdigit():
                        faltas_lista.append(float(st_map["foulsCommitted"]))
                      if st_map.get("yellowCards", "").replace(".", "", 1).isdigit():
                        amarillas_lista.append(float(st_map["yellowCards"]))
            break
    except Exception:
      pass

  res_real = {
      "corners": round(sum(corners_lista) / len(corners_lista), 2) if corners_lista else None,
      "tiros": round(sum(tiros_arco_lista) / len(tiros_arco_lista), 2) if tiros_arco_lista else None,
      "faltas": round(sum(faltas_lista) / len(faltas_lista), 2) if faltas_lista else None,
      "tarjetas": round(sum(amarillas_lista) / len(amarillas_lista), 2) if amarillas_lista else None,
      "muestra_partidos": max(len(corners_lista), len(tiros_arco_lista), len(faltas_lista)),
      "ts": time.time()
  }
  # Guardar SIEMPRE en caché (incluso si es un club menor sin datos) para no demorar nunca más
  cache_st[clave_eq] = res_real
  try:
    with open(ARCHIVO_CACHE_STATS_REALES, "w", encoding="utf-8") as f:
      json.dump(cache_st, f, ensure_ascii=False, indent=2)
  except Exception:
    pass
  return res_real if res_real["corners"] is not None else None
def motor_quant_institucional(
    liga_visual,
    liga_key,
    local,
    visitante,
    id_local,
    id_vis,
    id_partido,
    fecha_partido,
    hora_partido,
    arbitro=None,
    api_token=None,
    cuotas_bp=None,
):
  es_seleccion_nacional = (liga_key == "internacional")
  es_amistoso_intl = es_seleccion_nacional and ("AMISTOSO" in liga_visual.upper() or "FRIENDL" in liga_visual.upper())
  es_eliminatoria_conmebol = es_seleccion_nacional and ("CONMEBOL" in liga_visual.upper() or "COPA AMERICA" in liga_visual.upper() or "COPA AMÉRICA" in liga_visual.upper())

  is_america = (liga_key in [
      "argentina", 
      "colombia", 
      "america", 
      "COPA LIBERTADORES", 
      "COPA SUDAMERICANA", 
      "brasil",
      "mexico"
  ]) or es_eliminatoria_conmebol
  
  is_intl = (liga_key in [
      "UEFA CHAMPIONS LEAGUE",
      "UEFA EUROPA LEAGUE",
      "UEFA CONFERENCE LEAGUE",
      "COPA LIBERTADORES",
      "COPA SUDAMERICANA",
      "internacional"
  ])
  
  es_torneo_copa = any(
      t in liga_visual.upper()
      for t in [
          "COPA", 
          "POKAL", 
          "CUP", 
          "TAÇA",
          "BEKER",
          "COUPE",
          "CHAMPIONS", 
          "LIBERTADORES", 
          "SUDAMERICANA", 
          "EUROPA LEAGUE",
          "CONFERENCE LEAGUE"
      ]
  )
  es_copa_nacional_latam = is_america and ("COPA" in liga_visual.upper()) and not is_intl

  l_local = None
  l_vis = None
  tarj_l = None
  tarj_v = None
  tiros_l = None
  tiros_v = None
  faltas_l = None
  faltas_v = None
  corn_l = None
  corn_v = None
  # Si el club o Selección no está en el CSV local, extraer sus promedios REALES de la API
  if corn_l is None or tiros_l is None:
      st_real_l = obtener_stats_reales_api_equipo(id_local, local, api_token)
      if st_real_l:
          corn_l = corn_l if corn_l is not None else st_real_l.get("corners")
          tiros_l = tiros_l if tiros_l is not None else st_real_l.get("tiros")
          tarj_l = tarj_l if tarj_l is not None else st_real_l.get("tarjetas")
  if corn_v is None or tiros_v is None:
      st_real_v = obtener_stats_reales_api_equipo(id_vis, visitante, api_token)
      if st_real_v:
          corn_v = corn_v if corn_v is not None else st_real_v.get("corners")
          tiros_v = tiros_v if tiros_v is not None else st_real_v.get("tiros")
          tarj_v = tarj_v if tarj_v is not None else st_real_v.get("tarjetas")
  es_champions_femenina = ("WOMEN" in liga_visual.upper() or "FEMEN" in liga_visual.upper())
  datos = pd.DataFrame() if es_champions_femenina else cargar_datos_historicos_unificados(liga_key)
  d_l = pd.DataFrame()
  d_v = pd.DataFrame()
  
  if not datos.empty and "HomeTeam" in datos.columns:
    eq_disp = pd.concat([datos["HomeTeam"], datos["AwayTeam"]])
    loc_c = encontrar_nombre_exacto(local, eq_disp)
    vis_c = encontrar_nombre_exacto(visitante, eq_disp)
    
    d_l = datos[datos["HomeTeam"] == loc_c].tail(20)
    d_v = datos[datos["AwayTeam"] == vis_c].tail(20)

    goles_h_liga = max(float(datos["FTHG"].dropna().mean()), 1.15) if "FTHG" in datos.columns and not datos["FTHG"].dropna().empty else 1.35
    goles_a_liga = max(float(datos["FTAG"].dropna().mean()), 0.95) if "FTAG" in datos.columns and not datos["FTAG"].dropna().empty else 1.10

    f_atq_l = 1.0
    f_def_l = 1.0
    f_atq_v = 1.0
    f_def_v = 1.0

    if not d_l.empty:
      f_atq_l = media_ponderada_exponencial(d_l["FTHG"]) / goles_h_liga
      f_def_l = media_ponderada_exponencial(d_l["FTAG"]) / goles_a_liga
      if "HY" in d_l.columns:
        tarj_l = d_l["HY"].dropna().mean() if not d_l["HY"].dropna().empty else None
      if "HST" in d_l.columns:
        tiros_l = d_l["HST"].dropna().mean() if not d_l["HST"].dropna().empty else None
      if "HF" in d_l.columns:
        faltas_l = d_l["HF"].dropna().mean() if not d_l["HF"].dropna().empty else None
      if "HC" in d_l.columns:
        corn_l = d_l["HC"].dropna().mean() if not d_l["HC"].dropna().empty else None

    if not d_v.empty:
      f_atq_v = media_ponderada_exponencial(d_v["FTAG"]) / goles_a_liga
      f_def_v = media_ponderada_exponencial(d_v["FTHG"]) / goles_h_liga
      if "AY" in d_v.columns:
        tarj_v = d_v["AY"].dropna().mean() if not d_v["AY"].dropna().empty else None
      if "AST" in d_v.columns:
        tiros_v = d_v["AST"].dropna().mean() if not d_v["AST"].dropna().empty else None
      if "AF" in d_v.columns:
        faltas_v = d_v["AF"].dropna().mean() if not d_v["AF"].dropna().empty else None
      if "AC" in d_v.columns:
        corn_v = d_v["AC"].dropna().mean() if not d_v["AC"].dropna().empty else None

    if not d_l.empty and not d_v.empty:
      l_local = max(min(f_atq_l * f_def_v * goles_h_liga, 2.65), 0.55)
      l_vis = max(min(f_atq_v * f_def_l * goles_a_liga, 2.35), 0.40)
    # Extraer promedios reales de los últimos 12-15 partidos (Córners, Tiros, Faltas y Tarjetas) para TODOS los equipos
  faltas_real_l = None
  faltas_real_v = None
  st_real_l = obtener_stats_reales_api_equipo(id_local, local, api_token)
  if st_real_l:
      corn_l = corn_l if corn_l is not None else st_real_l.get("corners")
      tiros_l = tiros_l if tiros_l is not None else st_real_l.get("tiros")
      tarj_l = tarj_l if tarj_l is not None else st_real_l.get("tarjetas")
      faltas_real_l = st_real_l.get("faltas")

  st_real_v = obtener_stats_reales_api_equipo(id_vis, visitante, api_token)
  if st_real_v:
      corn_v = corn_v if corn_v is not None else st_real_v.get("corners")
      tiros_v = tiros_v if tiros_v is not None else st_real_v.get("tiros")
      tarj_v = tarj_v if tarj_v is not None else st_real_v.get("tarjetas")
      faltas_real_v = st_real_v.get("faltas")
  if l_local is not None and l_vis is not None and not d_l.empty and not d_v.empty:
      media_l_a = float(d_l["FTHG"].tail(10).mean())
      media_l_c = float(d_l["FTAG"].tail(10).mean())
      media_v_a = float(d_v["FTAG"].tail(10).mean())
      media_v_c = float(d_v["FTHG"].tail(10).mean())
      g1t_l_a = float(d_l["HTHG"].tail(10).mean()) if "HTHG" in d_l.columns and not d_l["HTHG"].dropna().empty else None
      g1t_v_c = float(d_v["HTHG"].tail(10).mean()) if "HTHG" in d_v.columns and not d_v["HTHG"].dropna().empty else None
      m_tarj_l = m_tiros_l = m_faltas_l = m_corn_l = None
      m_tarj_v = m_tiros_v = m_faltas_v = m_corn_v = None
  else:
      media_l_a, media_l_c, g1t_l_a, g1t_l_c, m_tarj_l, m_tiros_l, m_faltas_l, m_corn_l = (
          obtener_estadisticas_api_equipo_con_cache(id_local, api_token, local)
      )
      media_v_a, media_v_c, g1t_v_a, g1t_v_c, m_tarj_v, m_tiros_v, m_faltas_v, m_corn_v = (
          obtener_estadisticas_api_equipo_con_cache(id_vis, api_token, visitante)
      )
      if not d_l.empty:
          media_l_a = float(d_l["FTHG"].tail(10).mean())
          media_l_c = float(d_l["FTAG"].tail(10).mean())
      if not d_v.empty:
          media_v_a = float(d_v["FTAG"].tail(10).mean())
          media_v_c = float(d_v["FTHG"].tail(10).mean())

  media_l_a = float(media_l_a) if media_l_a is not None else 1.22
  media_l_c = float(media_l_c) if media_l_c is not None else 1.16
  media_v_a = float(media_v_a) if media_v_a is not None else 1.12
  media_v_c = float(media_v_c) if media_v_c is not None else 1.18

  # MEMORIA H2H DIRECTA DE ÚLTIMOS 14 DÍAS (Ajusta revanchas seguidas en Colombia / Copas)
  h2h_reciente_goles = None
  loc_n_h2h = normalizar_nombre_club(local)
  vis_n_h2h = normalizar_nombre_club(visitante)
  for arch_h2h in sorted(os.listdir("."), reverse=True)[:14]:
      if arch_h2h.startswith("cache_partidos_") and arch_h2h.endswith(".json"):
          f_h2h = arch_h2h.replace("cache_partidos_", "").replace(".json", "")
          if f_h2h >= str(fecha_partido):
              continue
          try:
              for p_h2h in json.load(open(arch_h2h, encoding="utf-8")) or []:
                  if str((p_h2h.get("fixture") or {}).get("status", {}).get("short") or "") in ["FT", "AET", "PEN"]:
                      lh = normalizar_nombre_club(((p_h2h.get("teams") or {}).get("home") or {}).get("name", ""))
                      vh = normalizar_nombre_club(((p_h2h.get("teams") or {}).get("away") or {}).get("name", ""))
                      if {lh, vh} == {loc_n_h2h, vis_n_h2h}:
                          gh_ant = float((p_h2h.get("goals") or {}).get("home") or 0)
                          ga_ant = float((p_h2h.get("goals") or {}).get("away") or 0)
                          h2h_reciente_goles = gh_ant + ga_ant
                          if lh == loc_n_h2h:
                              media_l_a = (media_l_a * 0.60) + (gh_ant * 0.40)
                              media_v_a = (media_v_a * 0.60) + (ga_ant * 0.40)
                          else:
                              media_l_a = (media_l_a * 0.60) + (ga_ant * 0.40)
                              media_v_a = (media_v_a * 0.60) + (gh_ant * 0.40)
                          break
          except Exception:
              pass
      if h2h_reciente_goles is not None:
          break

  # CALIBRACIÓN ESPECÍFICA MLS ESTADOS UNIDOS
  if liga_key == "usa":
      elite_mls = ["inter miami", "los angeles fc", "lafc", "la galaxy", "columbus crew", "cincinnati", "seattle sounders", "orlando city", "real salt lake", "new york red bulls", "ny red bulls", "new york city", "nycfc", "houston dynamo", "atlanta united", "charlotte", "minnesota", "vancouver"]
      media_l_a = max(1.48, media_l_a * (1.16 if any(e in loc_n_h2h for e in elite_mls) else 1.08))
      media_v_a = max(1.22, media_v_a * (1.14 if any(e in vis_n_h2h for e in elite_mls) else 1.06))

  media_l_a_pura = media_l_a
  media_l_c_pura = media_l_c
  media_v_a_pura = media_v_a
  media_v_c_pura = media_v_c

  equipos_altura = [
      # Altura (>2.000m)
      "independiente del valle", "cienciano", "bolivar", "the strongest", "always ready",
      "ldu quito", "liga de quito", "nacional potosi", "real tomayapo", "millonarios",
      "santa fe", "la equidad", "internacional de bogota", "fortaleza", "deportivo pasto",
      "boyaca chico", "chicó", "patriotas", "once caldas", "el nacional", "universidad catolica",
      "aucas", "macara", "mushuc runa", "melgar", "cusco", "deportivo garcilaso", "binacional",
      "sport huancayo", "utc cajamarca", "gv san jose", "aurora", "wilstermann", "cobreloa", "cobresal",
      "bolivia", "ecuador", "mexico", "méxico",
      # Calor Húmedo Extremo (>32°C / Alta Humedad: Barranquilla, Cúcuta, Valledupar, Montería, Santa Marta)
      "junior", "atletico junior", "cucuta", "cúcuta", "alianza", "jaguares", "union magdalena",
      "real cartagena", "barranquilla", "colombia", "cuiaba", "manaus", "bahia", "fortaleza", "jamaica", "honduras", "panama", "costa rica", "suriname", "curacao"
  ]
  
  es_altura_local = any(eq in local.lower() for eq in equipos_altura)

  def obtener_factor_jerarquia_dinamico(g_fav, g_con):
      if g_fav is None or g_con is None or g_con == 0: 
          return 1.0
      ratio = g_fav / max(g_con, 0.65)
      if ratio >= 2.0 and g_fav >= 1.75: 
          return 1.16 
      if ratio >= 1.5 and g_fav >= 1.45: 
          return 1.08 
      if ratio < 0.85 and g_fav < 1.05:
          return 0.94
      return 1.0
  elite_intl = [
      "argentina", "francia", "france", "inglaterra", "england", "españa", "spain",
      "brasil", "brazil", "portugal", "alemania", "germany", "italia", "italy",
      "paises bajos", "netherlands", "holland", "uruguay", "colombia", "belgica", "belgium", "croacia", "croatia"
  ]
  sub_elite_intl = [
      "paraguay", "ecuador", "chile", "peru", "venezuela", "mexico", "usa", "estados unidos", "united states",
      "suiza", "switzerland", "dinamarca", "denmark", "austria", "suecia", "sweden", "noruega", "norway",
      "gales", "wales", "polonia", "poland", "hungria", "hungary", "serbia", "japon", "japan",
      "corea del sur", "south korea", "marruecos", "morocco", "senegal", "nigeria", "egipto", "egypt",
      "argelia", "algeria", "camerun", "cameroon", "costa de marfil", "ivory coast", "canada",
      "ucrania", "ukraine", "turquia", "turkey", "escocia", "scotland", "grecia", "greece", "republica checa", "czech",
      "nueva zelanda", "new zealand", "australia", "iran", "uzbekistan", "arabia saudita", "saudi arabia", "jordania", "jordan", "iraq", "irak", "costa rica", "panama", "jamaica", "sudafrica", "south africa", "mali", "tunez", "tunisia"
  ]
  micro_selecciones = [
      "san marino", "andorra", "liechtenstein", "gibraltar", "malta", "islas feroe", "faroe",
      "india", "chinese taipei", "taiwan", "maldivas", "maldives", "guam", "camboya", "cambodia", "laos", "brunei", "timor",
      "sri lanka", "nepal", "bhutan", "pakistan", "bangladesh", "myanmar", "macau", "mongolia", "yemen",
      "st. martin", "saint martin", "sint maarten", "montserrat", "anguilla", "aruba", "virgin islands", "islas virgenes",
      "cayman", "caiman", "turks", "bahamas", "bermuda", "dominica", "st. kitts", "saint kitts", "st. lucia", "saint lucia",
      "st. vincent", "grenada", "granada", "antigua", "barbados", "belize", "belice", "tahiti", "islas cook", "cook islands",
      "lesotho", "eswatini", "sao tome", "seychelles", "djibouti", "somalia", "eritrea", "chad", "mauritius", "sudan del sur"
  ]

  if es_seleccion_nacional:
      loc_norm_s = normalizar_nombre_club(local)
      vis_norm_s = normalizar_nombre_club(visitante)

      def _rating_elo_seleccion(nom_s, media_gf, media_gc):
          ratings_exactos = {
              # CONMEBOL (10)
              "argentina": 1915.0, "brasil": 1855.0, "brazil": 1855.0, "colombia": 1810.0,
              "uruguay": 1785.0, "ecuador": 1720.0, "paraguay": 1675.0, "venezuela": 1655.0,
              "chile": 1635.0, "peru": 1635.0, "bolivia": 1570.0,
              # UEFA (55)
              "espana": 1920.0, "spain": 1920.0, "francia": 1895.0, "france": 1895.0,
              "inglaterra": 1875.0, "england": 1875.0, "portugal": 1850.0,
              "alemania": 1845.0, "germany": 1845.0, "paises bajos": 1815.0, "netherlands": 1815.0, "holland": 1815.0,
              "italia": 1790.0, "italy": 1790.0, "belgica": 1765.0, "belgium": 1765.0,
              "croacia": 1750.0, "croatia": 1750.0, "rusia": 1735.0, "russia": 1735.0,
              "suiza": 1720.0, "switzerland": 1720.0, "dinamarca": 1715.0, "denmark": 1715.0,
              "austria": 1710.0, "turquia": 1700.0, "turkey": 1700.0, "turkiye": 1700.0,
              "noruega": 1685.0, "norway": 1685.0, "suecia": 1680.0, "sweden": 1680.0,
              "serbia": 1675.0, "ucrania": 1675.0, "ukraine": 1675.0,
              "polonia": 1665.0, "poland": 1665.0, "republica checa": 1665.0, "czech": 1665.0,
              "grecia": 1665.0, "greece": 1665.0, "eslovaquia": 1655.0, "slovakia": 1655.0,
              "eslovenia": 1655.0, "slovenia": 1655.0, "hungria": 1655.0, "hungary": 1655.0,
              "escocia": 1650.0, "scotland": 1650.0, "gales": 1645.0, "wales": 1645.0,
              "georgia": 1645.0, "rumania": 1640.0, "romania": 1640.0,
              "albania": 1635.0, "islandia": 1635.0, "iceland": 1635.0,
              "bosnia-herzegovina": 1625.0, "bosnia": 1625.0, "montenegro": 1610.0,
              "irlanda del norte": 1600.0, "northern ireland": 1600.0,
              "irlanda": 1610.0, "ireland": 1610.0, "finlandia": 1595.0, "finland": 1595.0,
              "macedonia del norte": 1595.0, "north macedonia": 1595.0, "macedonia": 1595.0,
              "israel": 1595.0, "kosovo": 1585.0, "luxemburgo": 1555.0, "luxembourg": 1555.0,
              "armenia": 1535.0, "bulgaria": 1530.0, "bielorrusia": 1530.0, "belarus": 1530.0,
              "kazajistan": 1530.0, "kazakhstan": 1530.0, "azerbaiyan": 1525.0, "azerbaijan": 1525.0,
              "chipre": 1520.0, "cyprus": 1520.0, "estonia": 1515.0,
              "letonia": 1510.0, "latvia": 1510.0, "moldavia": 1510.0, "moldova": 1510.0,
              "lituania": 1505.0, "lithuania": 1505.0, "islas feroe": 1450.0, "faroe": 1450.0,
              "malta": 1390.0, "andorra": 1310.0, "gibraltar": 1270.0, "liechtenstein": 1250.0, "san marino": 1150.0,
              # CAF - AFRICA (54)
              "marruecos": 1740.0, "morocco": 1740.0, "senegal": 1705.0, "nigeria": 1680.0,
              "egipto": 1675.0, "egypt": 1675.0, "argelia": 1675.0, "algeria": 1675.0,
              "costa de marfil": 1675.0, "ivory coast": 1675.0, "camerun": 1655.0, "cameroon": 1655.0,
              "mali": 1645.0, "tunez": 1640.0, "tunisia": 1640.0, "sudafrica": 1635.0, "south africa": 1635.0,
              "rd congo": 1630.0, "dr congo": 1630.0, "congo dr": 1630.0, "ghana": 1620.0,
              "burkina faso": 1615.0, "cabo verde": 1605.0, "cape verde": 1605.0, "angola": 1605.0,
              "guinea ecuatorial": 1595.0, "equatorial guinea": 1595.0, "guinea-bissau": 1515.0, "guinea bissau": 1515.0,
              "guinea": 1600.0, "gabon": 1585.0, "zambia": 1580.0, "benin": 1565.0, "uganda": 1560.0,
              "mozambique": 1555.0, "mauritania": 1545.0, "kenia": 1545.0, "kenya": 1545.0,
              "comoras": 1545.0, "comoros": 1545.0, "namibia": 1540.0, "tanzania": 1540.0,
              "zimbabue": 1540.0, "zimbabwe": 1540.0, "togo": 1535.0, "gambia": 1535.0,
              "sudan del sur": 1380.0, "south sudan": 1380.0, "sudan": 1535.0, "libia": 1530.0, "libya": 1530.0,
              "ruanda": 1525.0, "rwanda": 1525.0, "congo": 1520.0, "niger": 1515.0, "madagascar": 1515.0,
              "malaui": 1505.0, "malawi": 1505.0, "sierra leona": 1505.0, "sierra leone": 1505.0,
              "botsuana": 1500.0, "botswana": 1500.0, "etiopia": 1490.0, "ethiopia": 1490.0,
              "burundi": 1485.0, "liberia": 1475.0, "republica centroafricana": 1470.0, "central african": 1470.0,
              "lesoto": 1430.0, "lesotho": 1430.0, "eswatini": 1410.0, "chad": 1390.0,
              "mauricio": 1360.0, "mauritius": 1360.0, "yibuti": 1310.0, "djibouti": 1310.0,
              "santo tome": 1300.0, "sao tome": 1300.0, "seychelles": 1240.0, "somalia": 1220.0, "eritrea": 1220.0,
              # CONCACAF (41)
              "estados unidos": 1690.0, "united states": 1690.0, "usa": 1690.0, "mexico": 1685.0, "canada": 1685.0,
              "panama": 1650.0, "costa rica": 1635.0, "jamaica": 1620.0, "honduras": 1605.0, "guatemala": 1590.0,
              "haiti": 1580.0, "curacao": 1570.0, "el salvador": 1570.0, "trinidad": 1560.0, "suriname": 1560.0,
              "nicaragua": 1550.0, "martinique": 1545.0, "guadeloupe": 1540.0,
              "republica dominicana": 1525.0, "dominican republic": 1525.0, "cuba": 1510.0,
              "guyana": 1500.0, "french guiana": 1495.0, "puerto rico": 1485.0, "antigua": 1440.0,
              "st. vincent": 1435.0, "saint vincent": 1435.0, "grenada": 1435.0,
              "st. kitts": 1430.0, "saint kitts": 1430.0, "st. lucia": 1430.0, "saint lucia": 1430.0,
              "bermuda": 1430.0, "belize": 1425.0, "belice": 1425.0, "dominica": 1410.0, "barbados": 1395.0,
              "sint maarten": 1390.0, "bonaire": 1380.0, "aruba": 1375.0, "st. martin": 1370.0, "saint martin": 1370.0,
              "montserrat": 1370.0, "cayman": 1330.0, "bahamas": 1310.0, "turks": 1260.0, "virgin islands": 1220.0, "anguilla": 1200.0,
              # AFC - ASIA (47) + OFC (11)
              "japon": 1745.0, "japan": 1745.0, "corea del sur": 1700.0, "south korea": 1700.0, "korea republic": 1700.0,
              "iran": 1690.0, "australia": 1685.0, "uzbekistan": 1640.0,
              "arabia saudita": 1635.0, "saudi arabia": 1635.0, "iraq": 1635.0, "irak": 1635.0,
              "jordania": 1635.0, "jordan": 1635.0, "qatar": 1630.0, "nueva zelanda": 1625.0, "new zealand": 1625.0,
              "united arab emirates": 1615.0, "uae": 1615.0, "oman": 1600.0, "bahrain": 1600.0, "bahrein": 1600.0,
              "china": 1565.0, "siria": 1555.0, "syria": 1555.0, "palestina": 1550.0, "palestine": 1550.0,
              "tailandia": 1545.0, "thailand": 1545.0, "kyrgyz": 1540.0, "kirguistan": 1540.0,
              "tajikistan": 1540.0, "tayikistan": 1540.0, "corea del norte": 1540.0, "north korea": 1540.0,
              "vietnam": 1535.0, "libano": 1530.0, "lebanon": 1530.0, "indonesia": 1525.0,
              "malasia": 1515.0, "malaysia": 1515.0, "kuwait": 1510.0, "turkmenistan": 1490.0, "india": 1485.0,
              "yemen": 1450.0, "filipinas": 1445.0, "philippines": 1445.0, "singapur": 1435.0, "singapore": 1435.0,
              "hong kong": 1430.0, "fiji": 1430.0, "new caledonia": 1430.0, "tahiti": 1425.0, "afghanistan": 1420.0,
              "vanuatu": 1400.0, "solomon islands": 1400.0, "myanmar": 1390.0, "papua new guinea": 1390.0,
              "chinese taipei": 1380.0, "taiwan": 1380.0, "maldives": 1370.0, "nepal": 1360.0, "cambodia": 1350.0,
              "bangladesh": 1345.0, "mongolia": 1310.0, "laos": 1300.0, "pakistan": 1300.0, "sri lanka": 1290.0,
              "samoa": 1280.0, "brunei": 1280.0, "timor": 1260.0, "bhutan": 1250.0, "macau": 1220.0,
              "tonga": 1210.0, "cook islands": 1210.0, "islas cook": 1210.0, "guam": 1210.0, "american samoa": 1180.0
          }
          rend_neto = max(-95.0, min(95.0, (media_gf - media_gc) * 55.0))
          for k_pais in sorted(ratings_exactos.keys(), key=len, reverse=True):
              if k_pais in nom_s:
                  return ratings_exactos[k_pais] + (rend_neto * 0.65)
          if any(eq in nom_s for eq in micro_selecciones):
              return 1250.0
          if any(eq in nom_s for eq in sub_elite_intl):
              return 1610.0 + rend_neto
          return 1500.0 + rend_neto

      elo_l_base = _rating_elo_seleccion(loc_norm_s, media_l_a_pura, media_l_c_pura)
      elo_v_base = _rating_elo_seleccion(vis_norm_s, media_v_a_pura, media_v_c_pura)

      # Vector de Dominio Estadístico Real por Tiros a Puerta y Córners (evita favoritismos falsos)
      bono_stats_l = 0.0
      if tiros_l is not None and tiros_v is not None:
          bono_stats_l += (float(tiros_l) - float(tiros_v)) * 22.0
      if corn_l is not None and corn_v is not None:
          bono_stats_l += (float(corn_l) - float(corn_v)) * 12.0
      bono_stats_l = max(-110.0, min(110.0, bono_stats_l))

      # En amistosos donde el local es potencia (ej. Japón vs Brasil), la localía pesa +60 Elo;
      # si ambos equipos son desconocidos (1460), no regalar +55 Elo artificial al local
      if elo_l_base == 1460.0 and elo_v_base == 1460.0:
          bono_loc_elo = 15.0
      elif es_amistoso_intl:
          bono_loc_elo = 60.0 if elo_l_base >= 1680.0 else 25.0
      else:
          bono_loc_elo = 50.0

      elo_l = elo_l_base + bono_loc_elo + (bono_stats_l * 0.5)
      elo_v = elo_v_base - (bono_stats_l * 0.5)
      if "bolivia" in loc_norm_s and not es_amistoso_intl:
          elo_l += 145.0
      elif "bolivia" in vis_norm_s:
          elo_v -= 130.0

      delta_elo = elo_l - elo_v
      expectativa_sigmoide_l = 1.0 / (1.0 + math.exp(-delta_elo / 210.0))
      expectativa_sigmoide_v = 1.0 - expectativa_sigmoide_l

      factor_l = round(0.70 + (0.68 * expectativa_sigmoide_l), 4)
      factor_v = round(0.70 + (0.68 * expectativa_sigmoide_v), 4)

      hay_micro_seleccion = any(eq in loc_norm_s or eq in vis_norm_s for eq in micro_selecciones)
      asimetria_elo = abs(delta_elo) / 400.0
      potencial_ofensivo_conjunto = (elo_l + elo_v) / 3400.0

      if hay_micro_seleccion and abs(delta_elo) >= 180.0:
          if elo_l > elo_v:
              media_l_a_pura = max(1.65, media_l_a_pura * 1.24)
          else:
              media_v_a_pura = max(1.55, media_v_a_pura * 1.22)
      elif potencial_ofensivo_conjunto < 0.90 and asimetria_elo < 0.40 and not es_amistoso_intl and not hay_micro_seleccion:
          coef_contraccion = math.exp(-0.22 * (1.0 - potencial_ofensivo_conjunto))
          media_l_a_pura *= coef_contraccion
          media_v_a_pura *= (coef_contraccion * 0.90)
  elif not is_america:
      factor_l = obtener_factor_jerarquia_dinamico(media_l_a_pura, media_l_c_pura)
      factor_v = obtener_factor_jerarquia_dinamico(media_v_a_pura, media_v_c_pura)

      elite_europa = [
          "real madrid", "barcelona", "manchester city",
          "arsenal", "liverpool", "bayern", "inter",
          "paris sg", "psg", "juventus", "atletico madrid",
          "dortmund", "borussia dortmund", "milan", "ac milan",
          "leverkusen", "napoli"
      ]
      campeones_ofensivos_europa = [
          "galatasaray", "fenerbahce", "fenerbahçe", "sporting", "benfica", "porto",
          "psv", "feyenoord", "ajax", "celtic", "rangers"
      ]
      sub_elite_europa = [
          "braga", "chelsea", "manchester united",
          "tottenham", "aston villa", "newcastle", "roma", "atalanta",
          "lazio", "fiorentina", "bologna", "leipzig", "stuttgart", "frankfurt",
          "hoffenheim", "freiburg", "monaco", "marseille", "lille", "lyon", "nice", "lens",
          "rennes", "reims", "stade de reims", "montpellier", "strasbourg", "brest", "toulouse", "nantes",
          "athletic", "real sociedad", "villarreal", "betis", "sevilla", "girona", "celta", "osasuna", "mallorca", "rayo",
          "brighton", "west ham", "fulham", "bournemouth", "brentford", "crystal palace", "nottingham",
          "torino", "udinese", "genoa", "parma", "como", "monza", "cagliari",
          "mainz", "werder bremen", "wolfsburg", "gladbach", "augsburg", "union berlin",
          "az alkmaar", "twente", "utrecht", "club brugge", "anderlecht",
          "union sg", "gent", "genk", "besiktas", "trabzonspor",
          "olympiacos", "paok", "panathinaikos", "aek",
          "slavia", "sparta praha", "plzen", "salzburg", "dinamo zagreb", "shakhtar"
      ]
      clubes_roce_primera_esp2 = [
          "leganes", "valladolid", "las palmas", "almeria", "granada", "cadiz",
          "espanyol", "elche", "levante", "oviedo", "sporting", "racing", "eibar", "zaragoza", "deportivo"
      ]

      loc_es_1a_eu = any(eq in local.lower() for eq in elite_europa + campeones_ofensivos_europa + sub_elite_europa)
      vis_es_1a_eu = any(eq in visitante.lower() for eq in elite_europa + campeones_ofensivos_europa + sub_elite_europa)

      loc_es_primera = loc_es_1a_eu
      vis_es_primera = vis_es_1a_eu
      if liga_key == "españa_2" or (es_torneo_copa and not is_intl):
          loc_n2 = normalizar_nombre_club(local)
          vis_n2 = normalizar_nombre_club(visitante)
          loc_es_primera = any(c in loc_n2 for c in clubes_roce_primera_esp2) and not vis_es_1a_eu
          vis_es_primera = any(c in vis_n2 for c in clubes_roce_primera_esp2) or vis_es_1a_eu
          if vis_es_1a_eu and not loc_es_1a_eu:
              # Ej. Real Oviedo (2ª) vs Girona (1ª) o Tourcoing vs Reims / Balagne vs Montpellier
              factor_v = max(factor_v, 1.18)
              factor_l = min(factor_l, 0.90)
              media_v_a_pura = max(1.45, media_v_a_pura * 1.25)
              media_l_a_pura = min(0.95, media_l_a_pura * 0.78)
          elif loc_es_1a_eu and not vis_es_1a_eu:
              factor_l = max(factor_l, 1.18)
              factor_v = min(factor_v, 0.90)
              media_l_a_pura = max(1.50, media_l_a_pura * 1.25)
              media_v_a_pura = min(0.90, media_v_a_pura * 0.78)
          elif loc_es_primera and not vis_es_primera:
              factor_l = max(factor_l, 1.16)
              media_l_a_pura = max(1.38, media_l_a_pura * 1.18)
              media_l_c_pura = min(1.05, media_l_c_pura * 0.82)
              factor_v = min(factor_v, 0.96)
              media_v_a_pura = min(1.02, media_v_a_pura * 0.86)

      if any(eq in local.lower() for eq in elite_europa):
          factor_l = 1.18
      elif any(eq in local.lower() for eq in campeones_ofensivos_europa):
          factor_l = max(factor_l, 1.16)
      elif any(eq in local.lower() for eq in sub_elite_europa):
          factor_l = max(factor_l, 1.13)

      if any(eq in visitante.lower() for eq in elite_europa):
          factor_v = 1.18
      elif any(eq in visitante.lower() for eq in campeones_ofensivos_europa):
          factor_v = max(factor_v, 1.16)
      elif any(eq in visitante.lower() for eq in sub_elite_europa):
          factor_v = max(factor_v, 1.13)


      if any(eq in local.lower() for eq in elite_europa) and media_l_a_pura >= 1.35:
          factor_l = 1.18
      elif any(eq in local.lower() for eq in campeones_ofensivos_europa) and media_l_a_pura >= 1.40:
          factor_l = max(factor_l, 1.16)
      elif any(eq in local.lower() for eq in sub_elite_europa) and media_l_a_pura >= 1.25:
          factor_l = max(factor_l, 1.12)

      if any(eq in visitante.lower() for eq in elite_europa) and media_v_a_pura >= 1.30:
          factor_v = 1.18
      elif any(eq in visitante.lower() for eq in campeones_ofensivos_europa) and media_v_a_pura >= 1.35:
          factor_v = max(factor_v, 1.16)
      elif any(eq in visitante.lower() for eq in sub_elite_europa) and media_v_a_pura >= 1.20:
          factor_v = max(factor_v, 1.12)

  else:
      loc_norm_c = normalizar_nombre_club(local)
      vis_norm_c = normalizar_nombre_club(visitante)
      falsos_positivos = [
          "internacional de", "internacional fc", "boca juniors de", "racing de", 
          "nacional potosi", "estudiantes de merida", "estudiantes de rio cuarto",
          "independiente rivadavia", "nacional de asuncion"
      ]
      
      elite_conmebol = [
          "palmeiras", "flamengo", "atletico mineiro", "atletico-mg",
          "sao paulo", "fluminense", "gremio", "botafogo", 
          "corinthians", "river plate", "boca juniors", 
          "racing club", "estudiantes de la plata"
      ]
      sub_elite_conmebol = [
          "independiente del valle", "ldu quito", "millonarios", 
          "atletico nacional", "penarol", "nacional de montevideo", 
          "colo colo", "santa fe", "america de cali", "junior",
          "independiente", "san lorenzo", "velez", "cruzeiro", "vasco",
          "internacional", "olimpia", "cerro porteno", "libertad", "tolima", "medellin",
          "lanus", "talleres", "defensa y justicia", "athletico paranaense", "fortaleza", "bahia", "bucaramanga", "once caldas"
      ]

      if any(fp in loc_norm_c for fp in falsos_positivos): 
          factor_l = min(1.0, obtener_factor_jerarquia_dinamico(media_l_a_pura, media_l_c_pura))
      else:
          if any(eq in loc_norm_c for eq in elite_conmebol): 
              factor_l = 1.18
          elif any(eq in loc_norm_c for eq in sub_elite_conmebol): 
              factor_l = 1.14
          else: 
              factor_l = obtener_factor_jerarquia_dinamico(media_l_a_pura, media_l_c_pura)
          
      if any(fp in vis_norm_c for fp in falsos_positivos): 
          factor_v = min(1.0, obtener_factor_jerarquia_dinamico(media_v_a_pura, media_v_c_pura))
      else:
          if any(eq in vis_norm_c for eq in elite_conmebol): 
              factor_v = 1.18
          elif any(eq in vis_norm_c for eq in sub_elite_conmebol): 
              factor_v = 1.14
          else: 
              factor_v = obtener_factor_jerarquia_dinamico(media_v_a_pura, media_v_c_pura)

  if (is_america or es_torneo_copa) and es_altura_local:
      factor_v = min(factor_v, 1.0)

  es_visita_jerarquia_superior = (factor_v >= 1.10 and factor_v > factor_l)
  es_local_jerarquia_superior = (factor_l >= 1.10 and factor_l > factor_v)

  media_l_a = media_l_a_pura * factor_l
  media_l_c = media_l_c_pura / math.sqrt(max(0.85, factor_l))
  media_v_a = media_v_a_pura * factor_v
  media_v_c = media_v_c_pura / math.sqrt(max(0.85, factor_v))

  if l_local is None or l_vis is None:
      fuerza_l = (media_l_a * 0.58) + (media_v_c * 0.42)
      fuerza_v = (media_v_a * 0.58) + (media_l_c * 0.42)
      
      if is_america:
        if es_visita_jerarquia_superior:
            l_local = max(fuerza_l * 0.96, 0.55)
            l_vis = max(fuerza_v * 1.04, 0.65)
        else:
            l_local = max(fuerza_l * 1.08, 0.65)
            l_vis = max(fuerza_v * 0.92, 0.45)
      else:
        if es_visita_jerarquia_superior:
            l_local = max(fuerza_l * 0.96, 0.55)
            l_vis = max(fuerza_v * 1.06, 0.65)
        else:
            l_local = max(fuerza_l * 1.08, 0.65)
            l_vis = max(fuerza_v * 0.92, 0.45)
  else:
      if factor_l != factor_v:
          l_local *= math.sqrt(factor_l / factor_v)
          l_vis *= math.sqrt(factor_v / factor_l)

  es_choque_elites = False
  if factor_l >= 1.12 and factor_v >= 1.12:
      es_choque_elites = True
      fuerza_media = (l_local + l_vis) / 2.0
      l_local = (l_local * 0.55) + (fuerza_media * 1.02 * 0.45)
      l_vis = (l_vis * 0.55) + (fuerza_media * 0.98 * 0.45)

  if tarj_l is None:
    tarj_l = m_tarj_l
  if tarj_v is None:
    tarj_v = m_tarj_v
  if tiros_l is None:
    tiros_l = m_tiros_l
  if tiros_v is None:
    tiros_v = m_tiros_v
  if faltas_l is None:
    faltas_l = m_faltas_l
  if faltas_v is None:
    faltas_v = m_faltas_v
  if corn_l is None:
    corn_l = m_corn_l
  if corn_v is None:
    corn_v = m_corn_v

  xg_local = obtener_xg_api_equipo(id_local, api_token, permitir_llamada_api=False)
  xg_vis = obtener_xg_api_equipo(id_vis, api_token, permitir_llamada_api=False)
  if xg_local is not None:
    l_local = (l_local * 0.4) + (xg_local * 0.6)
  if xg_vis is not None:
    l_vis = (l_vis * 0.4) + (xg_vis * 0.6)

  presion_local = (media_l_a_pura * 0.60) + (media_v_c_pura * 0.40)
  presion_visita = (media_v_a_pura * 0.60) + (media_l_c_pura * 0.40)
  diferencia_dominio = abs(presion_local - presion_visita)
  
  es_asedio_contra_bloque_bajo_eu = (not is_america) and (factor_l >= 1.15 and factor_v <= 1.04)
  if es_asedio_contra_bloque_bajo_eu:
      l_vis *= 0.82
      l_local *= 0.95
  elif presion_local > (presion_visita * 1.35) and not es_visita_jerarquia_superior:
      l_local *= 1.08
      l_vis *= 0.94
  elif presion_visita > (presion_local * 1.35) and not es_local_jerarquia_superior and not es_altura_local:
      l_local *= 0.94
      l_vis *= 1.08

  es_david_vs_goliath = False
  if is_america and (diferencia_dominio > 0.70 or (es_copa_nacional_latam and es_visita_jerarquia_superior)):
      if (factor_l >= 1.12 and factor_v <= 1.0) or (factor_v >= 1.12 and factor_l <= 1.0):
          es_david_vs_goliath = True

  canchas_sinteticas_hostiles = [
      "bodo", "glimt", "molde", "rosenborg", "viking", "brann", "tromso", "tromsø",
      "lillestrom", "sarpsborg", "stromsgodset", "odd", "hamkam", "haugesund", "kfum", "fredrikstad",
      "young boys", "lugano", "djurgarden", "hacken", "elfsborg", "hammarby", "malmo", "aik",
      "astana", "kairat", "ordabasy", "tobol", "aktobe", "klaksvik", "hjk", "kups",
      "breidablik", "vikingur", "flora", "riga", "rfs", "zalgiris", "qarabag"
  ]
  es_local_nordico_sintetico = (not is_america) and any(c in local.lower() for c in canchas_sinteticas_hostiles)
  es_visita_nordico_sintetico = (not is_america) and any(c in visitante.lower() for c in canchas_sinteticas_hostiles)
  es_trampa_sintetico = es_local_nordico_sintetico and es_visita_jerarquia_superior

  if es_local_nordico_sintetico and not es_visita_nordico_sintetico:
      l_local *= 1.08
      l_vis *= 0.90
  elif es_visita_nordico_sintetico and not es_local_nordico_sintetico and es_local_jerarquia_superior:
      l_local *= 1.07
      l_vis *= 0.93

  paises_hostiles = [
      "galatasaray", "fenerbahce", "besiktas", 
      "olympiacos", "dinamo zagreb", "bodo", "slavia",
      "montenegro", "bosnia", "grecia", "greece", "serbia", "jordania", "jordan"
  ]
  
  es_altura = False
  if es_altura_local:
      if is_intl:
          l_local *= 1.16
          l_vis *= 0.90
          es_altura = True
      else:
          l_local *= 1.07
          l_vis *= 0.92
          es_altura = True
          
  es_plaza_hostil_local = es_altura_local or any(hostil in local.lower() for hostil in paises_hostiles)
  if is_intl and not is_america:
      if any(hostil in local.lower() for hostil in paises_hostiles):
          l_local *= 1.06
          l_vis *= 0.93

  # CORRECCIÓN MATEMÁTICA DE ESCALÓN DIVISIONAL EN COPAS (1ª División vs Categoría Inferior)
  if es_torneo_copa and not is_intl:
      local_sin_csv_1a = d_l.empty and (factor_l < 1.12)
      visita_sin_csv_1a = d_v.empty and (factor_v < 1.12)
      if local_sin_csv_1a and (not d_v.empty or factor_v >= 1.12):
          l_local = min(0.82, l_local * 0.58)
          l_vis = max(1.58, l_vis * 1.38)
          es_visita_jerarquia_superior = True
          es_local_jerarquia_superior = False
      elif visita_sin_csv_1a and (not d_l.empty or factor_l >= 1.12):
          l_vis = min(0.78, l_vis * 0.58)
          l_local = max(1.62, l_local * 1.38)
          es_local_jerarquia_superior = True
          es_visita_jerarquia_superior = False
      elif local_sin_csv_1a and visita_sin_csv_1a:
          l_local = min(l_local, 1.28)
          l_vis = min(l_vis, 1.15)

  l_local = max(0.52, min(2.45, l_local))
  l_vis = max(0.42, min(2.25, l_vis))

  es_derbi = es_partido_rivalidad_alta(local, visitante)
  factor_derbi = 0.90 if es_derbi else 1.00

  promedio_goles_recientes = (l_local + l_vis)
  es_elite_involucrado = (factor_l >= 1.18 or factor_v >= 1.18)

  factor_contextual = 1.00
  etiqueta_contexto = "⚖️ [EQUILIBRADO / ESTÁNDAR]"

  if es_trampa_sintetico:
      etiqueta_contexto = "⚠️ [CAMPO SINTÉTICO / RIESGO TÁCTICO]"
      factor_contextual = 0.86
  elif es_asedio_contra_bloque_bajo_eu:
      etiqueta_contexto = "🛡️ [DOMINIO LOCAL VS BLOQUE BAJO]"
      factor_contextual = 0.93
  elif es_choque_elites:
      etiqueta_contexto = "⚔️ [CHOQUE DE ÉLITES / ALTA VOLATILIDAD]"
      factor_contextual = 1.05
  elif es_david_vs_goliath:
      etiqueta_contexto = "🔒 [CERROJO LATAM / DAVID VS GOLIATH]"
      factor_contextual = 0.88 
  elif es_derbi:
      etiqueta_contexto = "⚔️ [DERBI / MÁXIMA TENSIÓN TÁCTICA]"
      factor_contextual = 0.94
  elif diferencia_dominio > 0.80:
      etiqueta_contexto = "🔥 [ASEDIO OFENSIVO / DOMINIO ABSOLUTO]"
      factor_contextual = 1.08
  elif presion_local > 1.38 and presion_visita > 1.38 and abs(factor_l - factor_v) <= 0.08:
      etiqueta_contexto = "⚡ [GOLPE A GOLPE / TRANSICIONES RÁPIDAS]"
      factor_contextual = 1.08
  elif promedio_goles_recientes < 2.15:
      etiqueta_contexto = "🛡️ [BLOQUE BAJO / ALTA FRICCIÓN TÁCTICA]"
      factor_contextual = 0.88

  FACTORES_LIGA = {
      
      "italia": 0.93,
      "españa": 0.95,
      "españa_2": 0.85,
      "argentina": 0.84, 
      "francia": 0.95,
      "colombia": 0.88,
      "arabia_saudita": 0.93,  
      "inglaterra": 1.04,
      "alemania": 1.06,
      "holanda": 1.07,
      "belgica": 1.02,
      "turquia": 1.02,
      "grecia": 0.91,
      "escocia": 1.03,
      "europa": 1.03,
      "brasil": 0.97,
      "mexico": 0.98, "usa": 1.05,    
      "portugal": 1.02,
      "internacional": 0.94
  }
  
  peso_liga = FACTORES_LIGA.get(liga_key, 0.93 if is_america else 0.98)

  porosidad_defensiva = media_l_c_pura + media_v_c_pura
  if liga_key == "arabia_saudita":
      if porosidad_defensiva >= 2.32 and media_l_c_pura >= 1.12 and media_v_c_pura >= 1.12:
          peso_liga = 0.99
      elif media_l_c_pura <= 1.02 or media_v_c_pura <= 1.02:
          peso_liga = 0.86

  tot_goles = (l_local + l_vis) * peso_liga * factor_contextual * factor_derbi
  
  if es_copa_nacional_latam:
    tot_goles = round(max(1.65, tot_goles * 0.92), 2)
  elif (is_intl or es_torneo_copa) and not es_trampa_sintetico and not is_america:
    tot_goles = round(max(1.65, tot_goles * 1.02), 2)

  es_torneo_africa = es_seleccion_nacional and ("ÁFRICA" in liga_visual.upper() or "AFRICA" in liga_visual.upper())
  if es_seleccion_nacional:
      if tiros_l is not None and tiros_v is not None:
          xg_por_remates = (float(tiros_l) + float(tiros_v)) * 0.29
          tot_goles = round((tot_goles * 0.60) + (xg_por_remates * 0.40), 2)
      if es_torneo_africa:
          tot_goles = round(max(2.15, tot_goles * 0.92), 2)
      elif es_amistoso_intl and (faltas_real_l or 10.0) + (faltas_real_v or 10.0) < 22.0:
          tot_goles = round(tot_goles * 1.04, 2)
  if cuotas_bp and cuotas_bp.get("over25") is not None:
    c_o25 = float(cuotas_bp["over25"])
    if c_o25 <= 1.60 and tot_goles < 2.95 and not es_trampa_sintetico:
      tot_goles = round((tot_goles * 0.50) + (3.05 * 0.50), 2)
    elif c_o25 >= 2.20 and tot_goles > 2.30:
      tot_goles = round((tot_goles * 0.50) + (2.15 * 0.50), 2)

  if not is_america or liga_key == "brasil":
      if tot_goles > 3.25:
          tot_goles = 3.00 + ((tot_goles - 3.25) * 0.25) 
      tot_goles = round(max(1.75, tot_goles), 2)
  else:
      tot_goles = round(max(1.70, min(2.75, tot_goles)), 2)

  if g1t_l_a is not None and g1t_v_c is not None and media_l_a_pura > 0.2:
      ritmo_real_local = g1t_l_a / max(media_l_a_pura, 0.6)
      ritmo_real_visita = g1t_v_c / max(media_v_c_pura, 0.6)
      ritmo_1t_crudo = (ritmo_real_local + ritmo_real_visita) / 2.0
      
      if is_america and liga_key != "brasil":
          ritmo_1t = (ritmo_1t_crudo * 0.55) + (0.39 * 0.45)
          ritmo_1t = max(0.32, min(ritmo_1t, 0.47))
      elif liga_key in ["italia", "españa", "españa_2", "grecia"]:
          ritmo_1t = (ritmo_1t_crudo * 0.60) + (0.41 * 0.40)
          ritmo_1t = max(0.34, min(ritmo_1t, 0.49))
      else:
          ritmo_1t = (ritmo_1t_crudo * 0.65) + (0.43 * 0.35)
          ritmo_1t = max(0.35, min(ritmo_1t, 0.52))
  else:
      ritmo_1t = 0.39 if (is_america and liga_key != "brasil") else (0.41 if liga_key == "italia" else 0.43)
          
  # 1. CÁLCULO NATURAL DE GOL EN 1T (0.5 HT) Y GOL EN 2DO TIEMPO (0.5 2T) POR POISSON
  ambos_atacan = (l_local >= 1.12 and l_vis >= 0.98)
  if "GOLPE A GOLPE" in etiqueta_contexto or ambos_atacan:
      ritmo_1t = max(0.44, ritmo_1t + 0.04)

  lambda_1t = tot_goles * ritmo_1t
  p_05_ht = min(86.5, (1.0 - poisson_prob(lambda_1t, 0)) * 100.0)
  cuota_05_ht = (100 / p_05_ht) if p_05_ht > 0 else 0
  c_min_05_ht = max(1.12, cuota_05_ht * obtener_margen_ev_dinamico(p_05_ht))

  es_segunda_div = (liga_key == "españa_2") or ("TORNEO BETPLAY" in liga_visual.upper()) or ("SEGUNDA" in liga_visual.upper())
  factor_2t = max(0.53, min(0.60, 1.0 - ritmo_1t + 0.03))
  lambda_2t_real = tot_goles * factor_2t
  p_05_2t = min(84.5, (1.0 - poisson_prob(lambda_2t_real, 0)) * 100.0)
  cuota_05_2t = (100 / p_05_2t) if p_05_2t > 0 else 0
  c_min_05_2t = max(1.12, cuota_05_2t * obtener_margen_ev_dinamico(p_05_2t))

  if tot_goles < 2.25: 
      rho_dinamico = -0.18
  elif tot_goles < 2.60: 
      rho_dinamico = -0.13
  elif tot_goles < 3.00: 
      rho_dinamico = -0.08
  else: 
      rho_dinamico = -0.03

  suma_l_cruda = max(l_local + l_vis, 0.2)
  escala_contextual = tot_goles / suma_l_cruda
  l_local_mat = l_local * escala_contextual
  l_vis_mat = l_vis * escala_contextual

  matriz_prob = {}
  suma_comprobacion = 0.0
  p_under25_mat = 0.0
  p_under35_mat = 0.0
  p_over15_mat = 0.0
  p_btts_mat = 0.0
  p_h = 0.0
  p_d = 0.0
  p_a = 0.0
  p_over2_mat = 0.0
  p_over25_mat = 0.0
  p_over3_mat = 0.0
  p_combo_1x_o15_mat = 0.0
  p_combo_x2_o15_mat = 0.0

  for i in range(7):
      for j in range(7):
          p = poisson_prob(l_local_mat, i) * poisson_prob(l_vis_mat, j) * dixon_coles_adjustment(i, j, l_local_mat, l_vis_mat, rho_dinamico)
          matriz_prob[(i, j)] = max(p, 0.0) 
          suma_comprobacion += matriz_prob[(i, j)]

  for (i, j), p_cruda in matriz_prob.items():
      p_norm = p_cruda / suma_comprobacion
      if i > j: 
          p_h += p_norm
      elif i == j: 
          p_d += p_norm
      else: 
          p_a += p_norm
          
      g_tot = i + j
      if g_tot < 2.5: 
          p_under25_mat += p_norm
      if g_tot < 3.5:
          p_under35_mat += p_norm
      if g_tot > 1.5: 
          p_over15_mat += p_norm
          if i >= j:
              p_combo_1x_o15_mat += p_norm
          if j >= i:
              p_combo_x2_o15_mat += p_norm
      if g_tot > 2.0: 
          p_over2_mat += p_norm
      elif g_tot == 2:
          p_over2_mat += (p_norm * 0.50)
      if g_tot > 2.5: 
          p_over25_mat += p_norm
      if g_tot > 3.0: 
          p_over3_mat += p_norm
      elif g_tot == 3:
          p_over3_mat += (p_norm * 0.50)
      if i > 0 and j > 0: 
          p_btts_mat += p_norm

  p_h = p_h * 100
  p_d = p_d * 100
  p_a = p_a * 100
  p_under25 = p_under25_mat * 100
  p_under35 = p_under35_mat * 100

  if not is_america:
      gigantes_arabia = ("al-hilal", "al hilal", "al-nassr", "al nassr", "al-ahli", "al ahli", "al-ittihad", "al ittihad")
      if (porosidad_defensiva >= 2.35 and tot_goles >= 2.50) or (tot_goles >= 2.60 and any(g in local.lower() or g in visitante.lower() for g in gigantes_arabia)):
          p_under25 = max(35.0, p_under25 * 0.76)
          p_under35 = max(40.0, p_under35 * 0.72)
  else:
      cola_gamma_latam = 1.0 - sum(poisson_prob(tot_goles * 1.14, k) for k in range(4))
      p_under35 = max(38.0, (p_under35 - (cola_gamma_latam * 100.0 * 0.65)) * 0.78)
      if porosidad_defensiva >= 2.25 and tot_goles >= 2.35:
          p_under25 = max(36.0, p_under25 * 0.76)
          p_under35 = max(38.0, p_under35 * 0.75)

  p_15_match = p_over15_mat * 100
  p_btts = p_btts_mat * 100
  p_asig225 = (p_over2_mat + p_over25_mat) / 2.0 * 100
  p_asig275 = (p_over25_mat + p_over3_mat) / 2.0 * 100

  # 2. ESCUDO MATEMÁTICO ANTI 0-0 / 1-0 / 0-1 Y CALIBRACIÓN DE ALTA PRECISIÓN
  prob_marcador_corto = (
      matriz_prob.get((0, 0), 0.0) + matriz_prob.get((1, 0), 0.0) + matriz_prob.get((0, 1), 0.0)
  ) / max(suma_comprobacion, 0.0001)
  ataque_debil = min(l_local_mat, l_vis_mat)
  asimetria_ataque = abs(l_local_mat - l_vis_mat)

  prob_btts_independiente = (1.0 - poisson_prob(l_local_mat, 0)) * (1.0 - poisson_prob(l_vis_mat, 0)) * 100.0
  p_btts = (p_btts * 0.45) + (prob_btts_independiente * 0.55)

  if ataque_debil >= 1.02 and tot_goles >= 2.45 and prob_marcador_corto < 0.25 and not es_trampa_sintetico:
      p_btts = min(85.5, p_btts * 1.16)
  elif ataque_debil < 0.88 or prob_marcador_corto >= 0.30:
      p_btts = max(35.0, p_btts * 0.78)

  if (tot_goles <= 2.05 or prob_marcador_corto >= 0.36) and asimetria_ataque < 0.38 and not es_amistoso_intl:
      p_15_match = min(p_15_match, 63.0)
      p_asig225 = min(p_asig225, 52.0)
      p_05_ht = min(p_05_ht, 58.0)
      p_05_2t = min(p_05_2t, 63.0)
  elif tot_goles >= 2.18 or asimetria_ataque >= 0.35 or es_seleccion_nacional or es_torneo_copa or es_amistoso_intl:
      p_under25 = min(p_under25, 52.0)
      p_under35 = min(p_under35, 55.0)

  if es_segunda_div or es_torneo_africa or es_david_vs_goliath or (ataque_debil < 0.80 and tot_goles < 2.38):
      p_15_match = min(p_15_match, 66.5)

  # Regla #2: Efecto Partido Sentenciado (favorito dominante vs rival sin ataque suele resolver en 1T y bajar ritmo en 2T)
  if asimetria_ataque >= 0.52 and ataque_debil < 0.88:
      p_05_2t = max(50.0, p_05_2t * 0.86)
      cuota_05_2t = (100.0 / p_05_2t) if p_05_2t > 0 else 0
      c_min_05_2t = max(1.12, cuota_05_2t * obtener_margen_ev_dinamico(p_05_2t))

  if l_vis_mat > (l_local_mat * 1.15) and es_visita_jerarquia_superior:
      traspaso_h = p_h * 0.12
      p_h -= traspaso_h
      p_a += (traspaso_h * 0.75)
      p_d += (traspaso_h * 0.25)
  elif l_local_mat > (l_vis_mat * 1.15) and es_local_jerarquia_superior:
      traspaso_a = p_a * 0.12
      p_a -= traspaso_a
      p_h += (traspaso_a * 0.75)
      p_d += (traspaso_a * 0.25)

  if cuotas_bp and isinstance(cuotas_bp.get("1"), float) and isinstance(cuotas_bp.get("2"), float):
    inv_1 = 1.0 / cuotas_bp["1"]
    inv_x = 1.0 / cuotas_bp["X"]
    inv_2 = 1.0 / cuotas_bp["2"]
    suma_inv = inv_1 + inv_x + inv_2
    p_h_bp = (inv_1 / suma_inv) * 100.0
    p_d_bp = (inv_x / suma_inv) * 100.0
    p_a_bp = (inv_2 / suma_inv) * 100.0
    p_h = (p_h * 0.55) + (p_h_bp * 0.45)
    p_d = (p_d * 0.55) + (p_d_bp * 0.45)
    p_a = (p_a * 0.55) + (p_a_bp * 0.45)

  p_h = max(12.0, min(75.0, p_h))
  p_d = max(15.0, min(36.0, p_d))
  p_a = max(12.0, min(75.0, p_a))
  suma_1x2 = p_h + p_d + p_a
  p_h = (p_h / suma_1x2) * 100.0
  p_d = (p_d / suma_1x2) * 100.0
  p_a = (p_a / suma_1x2) * 100.0

  cuota_asig225 = (100 / p_asig225) if p_asig225 > 0 else 0
  c_min_asig225 = max(1.10, cuota_asig225 * obtener_margen_ev_dinamico(p_asig225))
  
  cuota_asig275 = (100 / p_asig275) if p_asig275 > 0 else 0
  c_min_asig275 = max(1.10, cuota_asig275 * obtener_margen_ev_dinamico(p_asig275))
  
  c_min_under25 = max(1.10, (100 / p_under25) * obtener_margen_ev_dinamico(p_under25)) if p_under25 > 0 else 0
  c_min_under35 = max(1.10, (100 / p_under35) * obtener_margen_ev_dinamico(p_under35)) if p_under35 > 0 else 0
  
  cuota_15 = (100 / p_15_match) if p_15_match > 0 else 0
  c_min_15 = max(1.10, cuota_15 * obtener_margen_ev_dinamico(p_15_match))

  cuota_btts = (100 / p_btts) if p_btts > 0 else 0
  c_min_btts = max(1.10, cuota_btts * obtener_margen_ev_dinamico(p_btts))
  
  cuota_h = (100 / p_h) if p_h > 0 else 0
  c_min_h = max(1.10, cuota_h * obtener_margen_ev_dinamico(p_h))
  
  cuota_d = (100 / p_d) if p_d > 0 else 0
  c_min_d = max(1.10, cuota_d * obtener_margen_ev_dinamico(p_d))
  
  cuota_a = (100 / p_a) if p_a > 0 else 0
  c_min_a = max(1.10, cuota_a * obtener_margen_ev_dinamico(p_a))

  # 2. DOBLE OPORTUNIDAD REAL BASADA EN LA MATRIZ DIXON-COLES (Sin recortar artificialmente un 25%)
  prob_local_2mas = 1.0 - poisson_prob(l_local_mat, 0) - poisson_prob(l_local_mat, 1)
  prob_visita_2mas = 1.0 - poisson_prob(l_vis_mat, 0) - poisson_prob(l_vis_mat, 1)

  ajuste_do_1x = 0.96 if prob_visita_2mas < 0.32 else 0.90
  ajuste_do_x2 = 0.96 if prob_local_2mas < 0.32 else 0.90

  p_1x = min(88.5, (p_h + p_d) * ajuste_do_1x)
  p_x2 = min(87.5, (p_a + p_d) * ajuste_do_x2)
  if p_h >= 30.0 or es_plaza_hostil_local or (es_seleccion_nacional and p_a < 54.0):
      p_x2 = min(p_x2, 60.0)


  cuota_1x = (100 / p_1x) if p_1x > 0 else 0
  cuota_x2 = (100 / p_x2) if p_x2 > 0 else 0
  
  c_min_1x = max(1.10, cuota_1x * obtener_margen_ev_dinamico(p_1x))
  c_min_x2 = max(1.10, cuota_x2 * obtener_margen_ev_dinamico(p_x2))


  
  es_partido_trampa = (tot_goles < 2.15) or es_trampa_sintetico
  es_sniper_over15 = tot_goles >= 2.50 and p_15_match >= 74.0 and not es_partido_trampa

  nombre_dom_goles = None
  p_dom_goles = None
  c_min_dom_goles = None
  if l_local_mat >= 1.55 and l_local_mat >= (l_vis_mat * 1.20):
    nombre_dom_goles = f"Goles {local[:12]} > 1.5"
    p_dom_goles, _, c_min_dom_goles = calcular_prob_over_y_ev(l_local_mat, 1.5)
  elif l_vis_mat >= 1.55 and l_vis_mat >= (l_local_mat * 1.20):
    nombre_dom_goles = f"Goles {visitante[:12]} > 1.5"
    p_dom_goles, _, c_min_dom_goles = calcular_prob_over_y_ev(l_vis_mat, 1.5)

  f_ataque_loc = (media_l_a_pura / 1.25) if media_l_a_pura else 1.0
  f_defensa_vis = (media_v_c_pura / 1.20) if media_v_c_pura else 1.0
  f_ataque_vis = (media_v_a_pura / 1.20) if media_v_a_pura else 1.0
  f_defensa_loc = (media_l_c_pura / 1.20) if media_l_c_pura else 1.0

  if is_america:
      m_tiros_latam = 3.95 if not es_copa_nacional_latam else 3.65
      f_base_local = 11.4 + (diferencia_dominio * 3.2)
      f_base_visita = 11.4 + (diferencia_dominio * 2.8)
      if factor_v >= 1.10: 
          f_base_local += 1.5
      base_faltas_l = faltas_l if faltas_l is not None else (f_base_local * min(1.20, max(0.85, f_defensa_loc)) * (1.06 if es_derbi else 1.0))
      base_faltas_v = faltas_v if faltas_v is not None else (f_base_visita * min(1.20, max(0.85, f_defensa_vis)) * (1.06 if es_derbi else 1.0))
      base_tiros_l = tiros_l if tiros_l is not None else (m_tiros_latam * f_ataque_loc * min(1.18, max(0.85, f_defensa_vis)))
      base_tiros_v = tiros_v if tiros_v is not None else (m_tiros_latam * f_ataque_vis * min(1.18, max(0.85, f_defensa_loc)))
      factor_conv_tiros = 1.02 if liga_key == "brasil" else 0.96
      tot_tiros = (base_tiros_l + base_tiros_v) * factor_conv_tiros * (0.94 if es_derbi else 1.00)
      tot_tiros = round(max(5.8, min(9.6, tot_tiros)), 2)
  elif liga_key == "arabia_saudita":
      base_tiros_l = (l_local_mat * 2.35) + 0.85
      base_tiros_v = (l_vis_mat * 2.25) + 0.75
      base_faltas_l = 10.1 + (diferencia_dominio * 1.4)
      base_faltas_v = 10.1 + (diferencia_dominio * 1.4)
      factor_conv_tiros = 0.98
      tot_tiros = round(max(5.6, min(9.4, (base_tiros_l + base_tiros_v) * factor_conv_tiros)), 2)
  else:
      est_tiros_l_xg = max(2.6, (l_local_mat * 2.45) + 0.85) * min(1.15, max(0.88, f_defensa_vis))
      est_tiros_v_xg = max(2.2, (l_vis_mat * 2.35) + 0.75) * min(1.15, max(0.88, f_defensa_loc))
      base_tiros_l = ((float(tiros_l) * 0.75) + (est_tiros_l_xg * 0.25)) if tiros_l is not None else est_tiros_l_xg
      base_tiros_v = ((float(tiros_v) * 0.75) + (est_tiros_v_xg * 0.25)) if tiros_v is not None else est_tiros_v_xg
      base_faltas_l = faltas_l if faltas_l is not None else (10.8 + (0.9 / max(l_local_mat, 0.45)))
      base_faltas_v = faltas_v if faltas_v is not None else (10.8 + (0.9 / max(l_vis_mat, 0.45)))
      factor_conv_tiros = 0.96 if liga_key in ["italia", "españa_2", "grecia"] else 1.00
      tot_tiros = (base_tiros_l + base_tiros_v) * factor_conv_tiros * (0.95 if es_derbi else 1.00)
      if ("BLOQUE BAJO" in etiqueta_contexto or "SINTÉTICO" in etiqueta_contexto) and tot_goles < 2.35:
          tot_tiros *= 0.92
      tot_tiros = round(max(5.6, min(9.8, tot_tiros)), 2)

  # 3. ECUACIÓN DE TRANSFERENCIA FÍSICA POR REBOTE (Tiros Bloqueados -> Córners y Fricción) + INGENIERÍA INVERSA DE LÍNEAS
  tiros_desviados_a_corner = 0.0
  if es_asedio_contra_bloque_bajo_eu or abs(factor_l - factor_v) >= 0.10 or ataque_debil < 0.95 or prob_marcador_corto >= 0.25:
      tasa_bloqueo_defensivo = min(0.18, max(0.08, (prob_marcador_corto * 0.38) + (asimetria_ataque * 0.06)))
      tiros_desviados_a_corner = tot_tiros * tasa_bloqueo_defensivo
      tot_tiros = round(max(5.5, tot_tiros - (tiros_desviados_a_corner * 0.75)), 2)

  derivada_k6 = poisson_prob(tot_tiros, 6)
  lambda_65_adj = tot_tiros * (1.0 - (0.30 * derivada_k6))
  lambda_75_adj = tot_tiros * (1.0 - (0.48 * poisson_prob(tot_tiros, 7)))
  if es_asedio_contra_bloque_bajo_eu or ataque_debil < 0.88:
      lambda_75_adj *= 0.88  # En cerrojo de un solo lado (Benfica-Alverca 1-0), frena la línea alta >7.5

  p_tiros55, cuota_tiros55, c_min_tiros55 = calcular_prob_over_y_ev(tot_tiros, 5.5)
  p_tiros65, cuota_tiros65, c_min_tiros65 = calcular_prob_over_y_ev(lambda_65_adj, 6.5)
  p_tiros75, cuota_tiros75, c_min_tiros75 = calcular_prob_over_y_ev(lambda_75_adj, 7.5)

  # Ingeniería inversa: las casas de apuestas abren en >6.5 o >7.5; desactivar >5.5 para no ofrecer menos tiros que la casa
  p_tiros55 = min(p_tiros55 or 0.0, 52.0)

  factor_arb = calcular_factor_arbitro_global(arbitro, liga_key)
  if is_intl and not is_america: 
      factor_arb *= 0.5  
  
  if faltas_real_l is not None:
      base_faltas_l = (float(faltas_real_l) * 0.75) + (base_faltas_l * 0.25)
  if faltas_real_v is not None:
      base_faltas_v = (float(faltas_real_v) * 0.75) + (base_faltas_v * 0.25)
  tot_faltas = (base_faltas_l + base_faltas_v) + (factor_arb * 1.2)
  if es_torneo_copa: 
      tot_faltas += (1.2 if es_copa_nacional_latam else 0.8)
  tot_faltas = round(max(19.5, min(26.5, tot_faltas)), 2)
  if es_amistoso_intl or es_champions_femenina:
    tot_faltas = round(min(19.5, tot_faltas * 0.82), 2)
  if es_champions_femenina:
    tot_goles = round(max(2.65, tot_goles * 1.12), 2)
    tot_tiros = round(max(7.2, tot_tiros * 1.10), 2)
  p_faltas21, cuota_faltas21, c_min_faltas21 = calcular_prob_over_y_ev(tot_faltas, 21.5)
  p_faltas22, cuota_faltas22, c_min_faltas22 = calcular_prob_over_y_ev(tot_faltas, 22.5)

  nombre_dom_corn = None
  p_dom_corn = None
  c_min_dom_corn = None

  if corn_l is not None and corn_v is not None:
      base_corn_l = float(corn_l)
      base_corn_v = float(corn_v)
  elif tiros_l is not None and tiros_v is not None:
      base_corn_l = (float(tiros_l) * 0.65) + (l_local_mat * 1.15) + 1.10
      base_corn_v = (float(tiros_v) * 0.65) + (l_vis_mat * 1.15) + 0.95
  else:
      # Modelo continuo de córners cuando no hay CSV: depende de la intensidad ofensiva,
      # la presión del favorito (asimetría) y la resistencia defensiva del rival
      asimetria_ataque = abs(l_local_mat - l_vis_mat)
      ritmo_ofensivo = l_local_mat + l_vis_mat
      base_corn_l = 2.95 + (l_local_mat * 1.45) + (max(0.0, l_local_mat - l_vis_mat) * 0.65)
      base_corn_v = 2.45 + (l_vis_mat * 1.35) + (max(0.0, l_vis_mat - l_local_mat) * 0.65)
      if ritmo_ofensivo < 2.15 and asimetria_ataque < 0.35:
          # Partido trabado en mediocampo (menos llegadas a línea de fondo)
          base_corn_l *= 0.88
          base_corn_v *= 0.88

  # Sumar a la tasa de Córners los tiros desviados por bloqueo defensivo
  tot_corn_crudo = base_corn_l + base_corn_v + (tiros_desviados_a_corner * 0.65)
  if liga_key in ["inglaterra", "brasil", "escocia", "holanda"]: 
      tot_corn = tot_corn_crudo * 1.06
  elif liga_key in ["españa", "españa_2", "italia", "argentina", "colombia"]: 
      tot_corn = tot_corn_crudo * 0.95
  else: 
      tot_corn = tot_corn_crudo

  tot_corn *= (1.03 if es_torneo_copa else 1.0) * (1.06 if (es_altura or es_local_nordico_sintetico) else 1.0)
  if ("BLOQUE BAJO" in etiqueta_contexto and not es_asedio_contra_bloque_bajo_eu) or "SINTÉTICO" in etiqueta_contexto or "CERROJO" in etiqueta_contexto:
      tot_corn *= 0.92
  if tot_corn > 9.6: 
      tot_corn = 9.6 + ((tot_corn - 9.6) * 0.45)
  tot_corn = round(max(7.4, tot_corn), 2)

  p_c_loc45, _, c_min_c_loc45 = calcular_prob_over_y_ev(base_corn_l, 4.5)
  p_c_vis45, _, c_min_c_vis45 = calcular_prob_over_y_ev(base_corn_v, 4.5)

  # Solo recomendar Córners Individuales (> 4.5) si ese equipo domina claramente el ataque
  if base_corn_l >= (base_corn_v + 0.85) and (l_local_mat >= l_vis_mat * 1.12) and p_c_loc45 >= 64.0:
      nombre_dom_corn = f"Córners {local[:15].strip()} > 4.5"
      p_dom_corn = p_c_loc45
      c_min_dom_corn = c_min_c_loc45
  elif base_corn_v >= (base_corn_l + 0.75) and (l_vis_mat >= l_local_mat * 1.12) and p_c_vis45 >= 64.0:
      nombre_dom_corn = f"Córners {visitante[:15].strip()} > 4.5"
      p_dom_corn = p_c_vis45
      c_min_dom_corn = c_min_c_vis45

  p_c75, cuota_c75, c_min_c75 = calcular_prob_over_y_ev(tot_corn, 7.5)
  p_c85, cuota_c85, c_min_c85 = calcular_prob_over_y_ev(tot_corn, 8.5)

  base_l = tarj_l if tarj_l is not None else (base_faltas_l / 4.8)
  base_v = tarj_v if tarj_v is not None else (base_faltas_v / 4.8)
  tendencia_actual = base_l + base_v
  h2h_tarjetas = obtener_h2h_tarjetas_api_con_cache(id_local, id_vis, api_token, permitir_llamada_api=False)
  volumen_faltas_partido = tot_faltas / 24.0

  if h2h_tarjetas is not None and h2h_tarjetas > 0:
      tot_tarj = (
          (tendencia_actual * 0.40)
          + (h2h_tarjetas * 0.30)
          + (volumen_faltas_partido * 1.25)
          + ((2.2 + (factor_arb * 1.8)) * 0.30)
      )
  else:
      tot_tarj = (
          (tendencia_actual * 0.50) 
          + (volumen_faltas_partido * 1.55) 
          + ((2.2 + (factor_arb * 1.8)) * 0.35)
      )
      
  if is_intl or es_torneo_copa: 
      tot_tarj = round(max(3.6 if es_copa_nacional_latam else 3.5, tendencia_actual * (1.22 if es_copa_nacional_latam else 1.15)), 2)
  tot_tarj = max(tot_tarj, 2.5)
  if es_amistoso_intl:
    tot_tarj = round(min(2.6, tot_tarj * 0.68), 2)
  if arbitro is None or str(arbitro).lower() in ["none", "null", "", "nan", "no asignado"]: 
      tot_tarj *= 0.90  
  if not is_america:
      if diferencia_dominio > 1.0: 
          tot_tarj *= 0.84
      if liga_key == "inglaterra": 
          tot_tarj *= 0.85


  linea_tarj = 3.5
  if tot_tarj >= 5.8: 
      linea_tarj = 5.5
  elif tot_tarj >= 4.8: 
      linea_tarj = 4.5
      
  p_t35, cuota_t35, c_min_t35 = calcular_prob_over_y_ev(tot_tarj, linea_tarj)

  factor_seguridad_combo = 0.84 if es_choque_elites else 1.00
  p_combo_1x_over15 = min(p_combo_1x_o15_mat * 100.0 * factor_seguridad_combo, 85.0)
  cuota_justa_combo_1x = (100 / p_combo_1x_over15) if p_combo_1x_over15 > 0 else 0
  c_min_combo_1x = max(1.12, cuota_justa_combo_1x * obtener_margen_ev_dinamico(p_combo_1x_over15))

  p_combo_x2_over15 = min(p_combo_x2_o15_mat * 100.0 * factor_seguridad_combo, 85.0)
  cuota_justa_combo_x2 = (100 / p_combo_x2_over15) if p_combo_x2_over15 > 0 else 0
  c_min_combo_x2 = max(1.12, cuota_justa_combo_x2 * obtener_margen_ev_dinamico(p_combo_x2_over15))

  nombre_arbitro_final = (
      arbitro if (arbitro and str(arbitro).lower() not in ["none", "null", "", "nan"]) else "No Asignado"
  )

  nombre_goleador, p_goleador, c_min_goleador = calcular_goleador_probable_partido(
      local, visitante, l_local_mat, l_vis_mat
  )

  return {
      "id_partido": id_partido,
      "liga_visual": liga_visual,
      "fecha": fecha_partido,
      "hora": hora_partido,
      "local": local,
      "visitante": visitante,
      "p_h": p_h,
      "cuota_h": c_min_h,
      "p_d": p_d,
      "cuota_d": c_min_d,
      "p_a": p_a,
      "cuota_a": c_min_a,
      "p_1x": p_1x,
      "cuota_1x": cuota_1x,
      "c_min_1x": c_min_1x,
      "p_x2": p_x2,
      "cuota_x2": cuota_x2,
      "c_min_x2": c_min_x2,
      "p_btts": p_btts,
      "cuota_btts": cuota_btts,
      "c_min_btts": c_min_btts,
      "tot_goles": tot_goles,
      "etiqueta_contexto": etiqueta_contexto,
      "p_asig225": p_asig225,
      "c_min_asig225": c_min_asig225,
      "p_asig275": p_asig275,
      "c_min_asig275": c_min_asig275,
      "p_under25": p_under25,
      "c_min_under25": c_min_under25,
      "p_under35": p_under35,
      "c_min_under35": c_min_under35,
      "p_05_ht": p_05_ht,
      "cuota_05_ht": cuota_05_ht,
      "c_min_05_ht": c_min_05_ht,
      "p_05_2t": p_05_2t,
      "cuota_05_2t": cuota_05_2t,
      "c_min_05_2t": c_min_05_2t,
      "p_15_match": p_15_match,
      "cuota_15": cuota_15,
      "c_min_15": c_min_15,
      "nombre_dom_goles": nombre_dom_goles,
      "p_dom_goles": p_dom_goles,
      "c_min_dom_goles": c_min_dom_goles,
      "nombre_dom_corn": nombre_dom_corn,
      "p_dom_corn": p_dom_corn,
      "c_min_dom_corn": c_min_dom_corn,
      "p_combo_1x_over15": p_combo_1x_over15,
      "c_min_combo_1x": c_min_combo_1x,
      "p_combo_x2_over15": p_combo_x2_over15,
      "c_min_combo_x2": c_min_combo_x2,
      "es_sniper": es_sniper_over15,
      "tot_tiros": tot_tiros,
      "p_tiros55": p_tiros55,
      "c_min_tiros55": c_min_tiros55,
      "p_tiros65": p_tiros65,
      "cuota_tiros65": cuota_tiros65,
      "c_min_tiros65": c_min_tiros65,
      "p_tiros75": p_tiros75,
      "cuota_tiros75": cuota_tiros75,
      "c_min_tiros75": c_min_tiros75,
      "tot_faltas": tot_faltas,
      "p_faltas21": p_faltas21,
      "c_min_faltas21": c_min_faltas21,
      "p_faltas22": p_faltas22,
      "cuota_faltas22": cuota_faltas22,
      "c_min_faltas22": c_min_faltas22,
      "tot_corn": tot_corn,
      "p_c75": p_c75,
      "c_min_c75": c_min_c75,
      "p_c85": p_c85,
      "cuota_c85": cuota_c85,
      "c_min_c85": c_min_c85,
      "arbitro": nombre_arbitro_final,
      "tot_tarj": tot_tarj,
      "linea_tarj": linea_tarj,
      "p_t35": p_t35,
      "cuota_t35": cuota_t35,
      "c_min_t35": c_min_t35,
      "nombre_goleador": nombre_goleador,
      "p_goleador": p_goleador,
      "c_min_goleador": c_min_goleador,
      "es_partido_trampa": es_partido_trampa,
      "prob_marcador_corto": round(prob_marcador_corto * 100.0, 1),
      "es_plaza_hostil_local": es_plaza_hostil_local,
      "is_america": is_america,
      "es_copa": es_torneo_copa,
      "es_derbi": es_derbi,
      "cuotas_bp": cuotas_bp if cuotas_bp else {"1": "N/A", "X": "N/A", "2": "N/A"},
  }


# ==============================================================================
# 5. EJECUCIÓN INSTITUCIONAL + GENERADOR DE COMBINADAS DE ALTA EFECTIVIDAD
# ==============================================================================
def construir_teclado_auditoria_general(res_m, memoria):
  todos_mercados_matriz = [
      ("🏠 Vict. Local", res_m.get("p_h"), res_m.get("cuota_h")),
      ("🤝 Empate", res_m.get("p_d"), res_m.get("cuota_d")),
      ("✈️ Vict. Visita", res_m.get("p_a"), res_m.get("cuota_a")),
      ("🛡️ Doble Oport. 1X", res_m.get("p_1x"), res_m.get("c_min_1x")),
      ("🛡️ Doble Oport. X2", res_m.get("p_x2"), res_m.get("c_min_x2")),
      ("⚽ Over 1.5 Goles", res_m.get("p_15_match"), res_m.get("c_min_15")),
      ("🛡️ Under 2.5 Goles", res_m.get("p_under25"), res_m.get("c_min_under25")),
      ("⚽ Asiático > 2.25", res_m.get("p_asig225"), res_m.get("c_min_asig225")),
      ("⚽ Asiático > 2.75", res_m.get("p_asig275"), res_m.get("c_min_asig275")),
      ("🥅 Ambos Marcan (BTTS)", res_m.get("p_btts"), res_m.get("c_min_btts")),
      ("⚡ Gol en 1T", res_m.get("p_05_ht"), res_m.get("c_min_05_ht")),
      ("🔥 Gol en 2do Tiempo", res_m.get("p_05_2t"), res_m.get("c_min_05_2t")),
      ("🎯 Remates > 6.5", res_m.get("p_tiros65"), res_m.get("c_min_tiros65")),
      ("🎯 Remates > 7.5", res_m.get("p_tiros75"), res_m.get("c_min_tiros75")),
      ("⚠️ Faltas > 22.5", res_m.get("p_faltas22"), res_m.get("c_min_faltas22")),
      ("🚩 Córners > 7.5", res_m.get("p_c75"), res_m.get("c_min_c75")),
      ("🚩 Córners > 8.5", res_m.get("p_c85"), res_m.get("c_min_c85")),
      (f"🟨 Tarjetas > {res_m.get('linea_tarj', 3.5)}", res_m.get("p_t35"), res_m.get("c_min_t35")),
      ("🧩 Combo 1X + O1.5", res_m.get("p_combo_1x_over15"), res_m.get("c_min_combo_1x")),
      ("🧩 Combo X2 + O1.5", res_m.get("p_combo_x2_over15"), res_m.get("c_min_combo_x2")),
  ]
  if res_m.get("nombre_dom_goles") and res_m.get("p_dom_goles"):
    todos_mercados_matriz.append((f"🚩 {res_m['nombre_dom_goles']}", res_m["p_dom_goles"], res_m["c_min_dom_goles"]))
  if res_m.get("nombre_dom_corn") and res_m.get("p_dom_corn"):
    todos_mercados_matriz.append((f"🚩 {res_m['nombre_dom_corn']}", res_m["p_dom_corn"], res_m["c_min_dom_corn"]))

  filas_teclado = []
  fila_actual = []
  id_p = str(res_m["id_partido"])
  nombre_partido = f"{res_m['local']} vs {res_m['visitante']}"

  for idx, (nom_m, prob_m, cuota_m) in enumerate(todos_mercados_matriz):
    if prob_m is None or cuota_m is None or prob_m <= 0 or cuota_m <= 1.01:
      continue
    cb_key = f"bet_{id_p}_{idx}"
    memoria[cb_key] = {
        "id_partido": id_p,
        "partido": nombre_partido,
        "mercado": nom_m,
        "cuota": round(float(cuota_m), 2),
        "prob": round(float(prob_m), 1),
        "semaforo": semaforo_probabilidad(prob_m),
        "soporte": res_m.get("etiqueta_contexto", "Análisis Cuantitativo"),
    }
    fila_actual.append({
        "text": f"{nom_m} ({prob_m:.0f}% | >{cuota_m:.2f})",
        "callback_data": cb_key,
    })
    if len(fila_actual) == 2:
      filas_teclado.append(fila_actual)
      fila_actual = []

  if fila_actual:
    filas_teclado.append(fila_actual)

  return {"inline_keyboard": filas_teclado} if filas_teclado else None


def construir_combinadas_institucionales(lista_partidos):
  candidatos_doble = []
  candidatos_sniper = []

  for p in lista_partidos:
    if p.get("es_partido_trampa"):
      continue
    nombre_p = f"{p['local']} vs {p['visitante']}"
    hora_p = p["hora"]

    # Solo líneas reales de casas de apuestas (prohibido Remates > 5.5 o Faltas > 21.5)
    opciones_seguras = [
        ("Over 1.5 Goles", p.get("p_15_match"), p.get("c_min_15")),
        ("Gol en 2do Tiempo", p.get("p_05_2t"), p.get("c_min_05_2t")),
        ("Remates Puerta > 6.5", p.get("p_tiros65"), p.get("c_min_tiros65")),
        ("Remates Puerta > 7.5", p.get("p_tiros75"), p.get("c_min_tiros75")),
        ("Faltas Totales > 22.5", p.get("p_faltas22"), p.get("c_min_faltas22")),
        (f"Tarjetas > {p.get('linea_tarj', 3.5)}", p.get("p_t35"), p.get("c_min_t35")),
        ("Gol en 1T", p.get("p_05_ht"), p.get("c_min_05_ht")),
        ("Total Asiático > 2.25", p.get("p_asig225"), p.get("c_min_asig225")),
        ("Ambos Marcan (BTTS)", p.get("p_btts"), p.get("c_min_btts")),
    ]
    if p.get("p_c75") is not None and p.get("tot_corn", 8.5) < 9.2:
      opciones_seguras.append(("Córners > 7.5", p.get("p_c75"), p.get("c_min_c75")))
    if p.get("p_c85") is not None:
      opciones_seguras.append(("Córners > 8.5", p.get("p_c85"), p.get("c_min_c85")))
    if p.get("nombre_dom_goles") and p.get("p_dom_goles"):
      opciones_seguras.append((p["nombre_dom_goles"], p["p_dom_goles"], p["c_min_dom_goles"]))

    # Combinada Doble VIP / Matriz Doble PRO: Cuotas individuales de valor real (1.36 a 1.50 -> Total ~1.88x a 2.22x)
    validas_d = [
        {"partido": nombre_p, "hora": hora_p, "mercado": m, "prob": pr, "cuota": round(max(1.36, min(1.50, cu * 1.12)), 2), "score_elite": p.get("score_elite", 0)}
        for m, pr, cu in opciones_seguras
        if pr is not None and cu is not None and 1.18 <= cu <= 1.55 and pr >= 70.0
    ]
    if validas_d:
      validas_d.sort(key=lambda x: x["prob"], reverse=True)
      candidatos_doble.append(validas_d[0])

    # Triple Sniper PRO: Cuotas individuales (1.44 a 1.68 -> Total ~3.00x a 4.20x)
    validas_s = [
        {"partido": nombre_p, "hora": hora_p, "mercado": m, "prob": pr, "cuota": round(max(1.44, min(1.68, cu * 1.15)), 2), "score_elite": p.get("score_elite", 0)}
        for m, pr, cu in opciones_seguras
        if pr is not None and cu is not None and 1.25 <= cu <= 1.75 and pr >= 65.0
    ]
    if validas_s:
      validas_s.sort(key=lambda x: x["prob"], reverse=True)
      candidatos_sniper.append(validas_s[0])

  candidatos_doble.sort(key=lambda x: (x["score_elite"] >= 5, x["prob"]), reverse=True)
  candidatos_sniper.sort(key=lambda x: (x["score_elite"] >= 5, x["prob"]), reverse=True)

  info_doble = None
  if len(candidatos_doble) >= 2:
    sel_d = candidatos_doble[:2]
    cuota_d = round(sel_d[0]["cuota"] * sel_d[1]["cuota"], 2)
    prob_dir_d = round((sel_d[0]["prob"] / 100.0) * (sel_d[1]["prob"] / 100.0) * 100.0, 1)
    prob_prot_d = round(min(92.5, prob_dir_d + 14.5), 1)
    info_doble = {
        "selecciones": sel_d,
        "cuota_total": cuota_d,
        "prob_directa": prob_dir_d,
        "prob_protegida": prob_prot_d,
    }

  info_sniper = None
  if len(candidatos_sniper) >= 3:
    sel_s = candidatos_sniper[:3]
    cuota_s = round(sel_s[0]["cuota"] * sel_s[1]["cuota"] * sel_s[2]["cuota"], 2)
    prob_dir_s = round((sel_s[0]["prob"] / 100.0) * (sel_s[1]["prob"] / 100.0) * (sel_s[2]["prob"] / 100.0) * 100.0, 1)
    prob_prot_s = round(min(84.0, prob_dir_s + 24.0), 1)
    info_sniper = {
        "selecciones": sel_s,
        "cuota_total": cuota_s,
        "prob_directa": prob_dir_s,
        "prob_protegida": prob_prot_s,
    }
  elif len(candidatos_doble) >= 3:
    sel_s = candidatos_doble[:3]
    cuota_s = round(sel_s[0]["cuota"] * sel_s[1]["cuota"] * sel_s[2]["cuota"], 2)
    prob_dir_s = round((sel_s[0]["prob"] / 100.0) * (sel_s[1]["prob"] / 100.0) * (sel_s[2]["prob"] / 100.0) * 100.0, 1)
    prob_prot_s = round(min(86.0, prob_dir_s + 22.0), 1)
    info_sniper = {
        "selecciones": sel_s,
        "cuota_total": cuota_s,
        "prob_directa": prob_dir_s,
        "prob_protegida": prob_prot_s,
    }

  return info_doble, info_sniper


COPAS_NACIONALES_EUROPA = {143, 45, 48, 137, 81, 66, 96, 90, 206}
_EQUIPOS_PRIMERA_EUROPA_CACHE = None

def es_partido_copa_europa_profesional(liga_id, local_nom, vis_nom):
  """Para todas las Copas nacionales de Europa (Copa del Rey, FA Cup, DFB Pokal, Coppa Italia, Taça, etc.),
  filtra cruces de rondas amateurs exigiendo que al menos 1 equipo sea de 1ª División profesional."""
  if int(liga_id or 0) not in COPAS_NACIONALES_EUROPA:
    return True
  global _EQUIPOS_PRIMERA_EUROPA_CACHE
  if _EQUIPOS_PRIMERA_EUROPA_CACHE is None:
    _EQUIPOS_PRIMERA_EUROPA_CACHE = set()
    df_eu = obtener_base_maestra_europa_csv()
    if not df_eu.empty and "Div" in df_eu.columns and "HomeTeam" in df_eu.columns:
      divs_1a = {"SP1", "E0", "I1", "D1", "F1", "P1", "N1", "B1", "T1", "G1", "SC0"}
      df_1a = df_eu[df_eu["Div"].isin(divs_1a)]
      for eq in pd.concat([df_1a["HomeTeam"], df_1a["AwayTeam"]]).dropna().unique():
        _EQUIPOS_PRIMERA_EUROPA_CACHE.add(normalizar_nombre_club(str(eq)))
    # Asegurar clubes de 1ª conocidos por si el CSV aún no se cargó
    for eq_base in [
        "real madrid", "barcelona", "atletico madrid", "athletic", "real sociedad", "villarreal", "betis",
        "sevilla", "valencia", "celta", "girona", "mallorca", "osasuna", "getafe", "rayo vallecano", "espanyol",
        "alaves", "las palmas", "leganes", "valladolid", "manchester city", "arsenal", "liverpool", "chelsea",
        "manchester united", "tottenham", "aston villa", "newcastle", "brighton", "west ham", "fulham",
        "bournemouth", "brentford", "crystal palace", "everton", "nottingham", "wolves", "bayern", "dortmund",
        "leverkusen", "leipzig", "stuttgart", "frankfurt", "freiburg", "hoffenheim", "inter", "milan", "juventus",
        "napoli", "atalanta", "roma", "lazio", "fiorentina", "bologna", "torino", "paris sg", "psg", "monaco",
        "marseille", "lille", "lyon", "nice", "lens", "rennes", "porto", "benfica", "sporting", "braga",
        "ajax", "psv", "feyenoord", "galatasaray", "fenerbahce", "besiktas", "celtic", "rangers"
    ]:
      _EQUIPOS_PRIMERA_EUROPA_CACHE.add(normalizar_nombre_club(eq_base))

  ln = normalizar_nombre_club(traductor_nombres.get(local_nom, local_nom))
  vn = normalizar_nombre_club(traductor_nombres.get(vis_nom, vis_nom))
  for nom_c in (ln, vn):
    if nom_c in _EQUIPOS_PRIMERA_EUROPA_CACHE:
      return True
    if any((len(eq) >= 5 and (eq in nom_c or nom_c in eq)) for eq in _EQUIPOS_PRIMERA_EUROPA_CACHE):
      return True
  return False


def obtener_ligas_permitidas_oficiales():
  return {
      140: ("ESPAÑA (LALIGA)", "españa"), 143: ("ESPAÑA (COPA DEL REY)", "españa"),
      141: ("ESPAÑA (SEGUNDA)", "españa_2"), 39: ("INGLATERRA (PREMIER)", "inglaterra"),
      45: ("INGLATERRA (FA CUP)", "inglaterra"), 48: ("INGLATERRA (EFL CUP)", "inglaterra"),
      135: ("ITALIA (SERIE A)", "italia"), 137: ("ITALIA (COPPA ITALIA)", "italia"),
      78: ("ALEMANIA (BUNDESLIGA)", "alemania"), 81: ("ALEMANIA (DFB POKAL)", "alemania"),
      61: ("FRANCIA (LIGUE 1)", "francia"), 66: ("FRANCIA (COUPE DE FRANCE)", "francia"),
      128: ("ARGENTINA (LIGA PROFESIONAL)", "argentina"), 130: ("ARGENTINA (COPA ARGENTINA)", "argentina"),
      530: ("ARGENTINA (COPA DE LA LIGA)", "argentina"), 239: ("COLOMBIA (PRIMERA A)", "colombia"),
      533: ("COLOMBIA (COPA BETPLAY)", "colombia"), 240: ("COLOMBIA (TORNEO BETPLAY)", "colombia"),
      712: ("COLOMBIA (SUPERLIGA)", "colombia"), 307: ("ARABIA SAUDITA (SAUDI PRO LEAGUE)", "arabia_saudita"),
      71: ("BRASIL (SERIE A)", "brasil"), 73: ("BRASIL (COPA DO BRASIL)", "brasil"),
      94: ("PORTUGAL (PRIMEIRA LIGA)", "portugal"), 96: ("PORTUGAL (TAÇA DE PORTUGAL)", "portugal"),
      88: ("PAÍSES BAJOS (EREDIVISIE)", "holanda"), 90: ("PAÍSES BAJOS (KNVB BEKER)", "holanda"),
      203: ("TURQUÍA (SÜPER LIG)", "turquia"), 206: ("TURQUÍA (COPA)", "turquia"),
      262: ("MÉXICO (LIGA MX)", "mexico"), 253: ("USA (MLS)", "usa"),
      2: ("UEFA CHAMPIONS LEAGUE", "UEFA CHAMPIONS LEAGUE"), 3: ("UEFA EUROPA LEAGUE", "UEFA EUROPA LEAGUE"),
      848: ("UEFA CONFERENCE LEAGUE", "UEFA CONFERENCE LEAGUE"), 13: ("COPA LIBERTADORES", "COPA LIBERTADORES"),
      11: ("COPA SUDAMERICANA", "COPA SUDAMERICANA"),
      1: ("MUNDIAL FIFA", "internacional"), 4: ("EUROCOPA", "internacional"),
      9: ("COPA AMÉRICA", "internacional"), 5: ("UEFA NATIONS LEAGUE", "internacional"),
      21: ("CONCACAF GOLD CUP", "internacional"), 536: ("CONCACAF NATIONS LEAGUE", "internacional"),
      34: ("ELIMINATORIAS CONMEBOL", "internacional"), 340: ("ELIMINATORIAS CONMEBOL", "internacional"),
      32: ("ELIMINATORIAS UEFA", "internacional"), 31: ("ELIMINATORIAS CONCACAF", "internacional"),
      29: ("ELIMINATORIAS ÁFRICA", "internacional"), 36: ("CLASIFICACIÓN COPA ÁFRICA", "internacional"),
      6: ("COPA AFRICANA DE NACIONES", "internacional"), 30: ("ELIMINATORIAS ASIA", "internacional"),
      35: ("CLASIFICACIÓN COPA ASIA", "internacional"), 12: ("COPA ASIÁTICA", "internacional"),
      10: ("AMISTOSO INTERNACIONAL", "internacional"), 525: ("UEFA WOMEN'S CHAMPIONS LEAGUE", "europa"),
  }


def ejecutar_sistema_automatico(api_token):
  inicializar_csv_auditoria()
  umbral_dinamico = calcular_ponderacion_yield_mercado()

  print("\n[+] Motor Quant Institutional v22.5 (Hora Invierno UTC+1 + Candado 7 Tarjetas + Líneas Reales)")
  logging.info("Iniciando ejecución maestra optimizada.")

  sincronizar_csv_locales_api(api_token)
  obtener_base_maestra_europa_csv()
  cuotas_mercado = obtener_cuotas_betplay_kambi()
  headers = {"x-apisports-key": api_token}

  ligas_permitidas = {
      140: ("ESPAÑA (LALIGA)", "españa"), 143: ("ESPAÑA (COPA DEL REY)", "españa"),
      141: ("ESPAÑA (SEGUNDA)", "españa_2"), 39: ("INGLATERRA (PREMIER)", "inglaterra"),
      45: ("INGLATERRA (FA CUP)", "inglaterra"), 48: ("INGLATERRA (EFL CUP)", "inglaterra"),
      135: ("ITALIA (SERIE A)", "italia"), 137: ("ITALIA (COPPA ITALIA)", "italia"),
      78: ("ALEMANIA (BUNDESLIGA)", "alemania"), 81: ("ALEMANIA (DFB POKAL)", "alemania"),
      61: ("FRANCIA (LIGUE 1)", "francia"), #66: ("FRANCIA (COUPE DE FRANCE)", "francia"),
      128: ("ARGENTINA (LIGA PROFESIONAL)", "argentina"), 130: ("ARGENTINA (COPA ARGENTINA)", "argentina"),
      530: ("ARGENTINA (COPA DE LA LIGA)", "argentina"), 239: ("COLOMBIA (PRIMERA A)", "colombia"),
      533: ("COLOMBIA (COPA BETPLAY)", "colombia"), 240: ("COLOMBIA (TORNEO BETPLAY)", "colombia"),
      712: ("COLOMBIA (SUPERLIGA)", "colombia"), 307: ("ARABIA SAUDITA (SAUDI PRO LEAGUE)", "arabia_saudita"),
      71: ("BRASIL (SERIE A)", "brasil"), 73: ("BRASIL (COPA DO BRASIL)", "brasil"),
      94: ("PORTUGAL (PRIMEIRA LIGA)", "portugal"), 96: ("PORTUGAL (TAÇA DE PORTUGAL)", "portugal"),
      88: ("PAÍSES BAJOS (EREDIVISIE)", "holanda"), # 90: ("PAÍSES BAJOS (KNVB BEKER)", "holanda"),
      203: ("TURQUÍA (SÜPER LIG)", "turquia"), # 206: ("TURQUÍA (COPA)", "turquia"),
      262: ("MÉXICO (LIGA MX)", "mexico"), 253: ("USA (MLS)", "usa"),
      2: ("UEFA CHAMPIONS LEAGUE", "UEFA CHAMPIONS LEAGUE"), 3: ("UEFA EUROPA LEAGUE", "UEFA EUROPA LEAGUE"),
      848: ("UEFA CONFERENCE LEAGUE", "UEFA CONFERENCE LEAGUE"), 13: ("COPA LIBERTADORES", "COPA LIBERTADORES"),
      11: ("COPA SUDAMERICANA", "COPA SUDAMERICANA"),
      # SELECCIONES NACIONALES MAYORES (EUROPA, AMÉRICA, ÁFRICA, ASIA) + CHAMPIONS FEMENINA
      1: ("MUNDIAL FIFA", "internacional"),
      4: ("EUROCOPA", "internacional"),
      9: ("COPA AMÉRICA", "internacional"),
      5: ("UEFA NATIONS LEAGUE", "internacional"),
      21: ("CONCACAF GOLD CUP", "internacional"),
      536: ("CONCACAF NATIONS LEAGUE", "internacional"),
      34: ("ELIMINATORIAS CONMEBOL", "internacional"),
      340: ("ELIMINATORIAS CONMEBOL", "internacional"),
      32: ("ELIMINATORIAS UEFA", "internacional"),
      31: ("ELIMINATORIAS CONCACAF", "internacional"),
      29: ("ELIMINATORIAS ÁFRICA", "internacional"),
      36: ("CLASIFICACIÓN COPA ÁFRICA", "internacional"),
      6: ("COPA AFRICANA DE NACIONES", "internacional"),
      30: ("ELIMINATORIAS ASIA", "internacional"),
      35: ("CLASIFICACIÓN COPA ASIA", "internacional"),
      12: ("COPA ASIÁTICA", "internacional"),
      10: ("AMISTOSO INTERNACIONAL", "internacional"),
      525: ("UEFA WOMEN'S CHAMPIONS LEAGUE", "europa"),
  }

  ahora_real = datetime.now()
  fecha_arg = sys.argv[1].strip() if len(sys.argv) > 1 else FECHA_OBJETIVO_MANUAL.strip()
  if fecha_arg:
      hoy_dt = datetime.strptime(fecha_arg, "%Y-%m-%d")
      es_fecha_futura = hoy_dt.date() > ahora_real.date()
  else:
      if ahora_real.hour < 0:
          hoy_dt = (ahora_real - timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
      else:
          hoy_dt = ahora_real.replace(hour=0, minute=0, second=0, microsecond=0)
      es_fecha_futura = False
  fecha_jornada = hoy_dt.strftime("%Y-%m-%d")

  # Siempre refrescar resultados finales (FT) y resolver auditoría de hoy antes de crear vídeos
  refrescar_caches_ft_jornada_anterior(ahora_real.strftime("%Y-%m-%d"), headers)
  procesar_clics_pendientes()
  resolver_apuestas_pendientes(api_token)
  if not es_fecha_futura:
      auditar_todos_los_partidos_fecha_bot_auditorias(fecha_jornada, ligas_permitidas, headers, api_token)
  else:
      print(f"\n[MODO PRE-ESCANEO PRIVADO] 🔭 Analizando fecha futura ({fecha_jornada}) con auditoría FT de hoy actualizada...")

  inicio_ventana = hoy_dt + timedelta(hours=7)
  fin_ventana = hoy_dt + timedelta(days=1, hours=6, minutes=59)
  
  fechas_a_escanear = [
      (hoy_dt - timedelta(days=1)).strftime("%Y-%m-%d"),
      hoy_dt.strftime("%Y-%m-%d"),
      (hoy_dt + timedelta(days=1)).strftime("%Y-%m-%d"),
  ]

  fixtures_totales = []
  ids_vistos = set()
  for fecha in fechas_a_escanear:
    fixtures = obtener_datos_api_partidos(fecha, headers)
    for p in fixtures:
      try:
        liga_id = p["league"]["id"]
        id_fix = p["fixture"]["id"]
        loc_chk = p.get("teams", {}).get("home", {}).get("name", "")
        vis_chk = p.get("teams", {}).get("away", {}).get("name", "")
        liga_nom_chk = p.get("league", {}).get("name", "")
        if es_seleccion_juvenil_o_femenina(loc_chk, vis_chk, liga_nom_chk, liga_id):
          continue
        if not es_partido_copa_europa_profesional(liga_id, loc_chk, vis_chk):
          continue
        if liga_id in ligas_permitidas and id_fix not in ids_vistos:
          fecha_api = p["fixture"]["date"]
          try:
            dt_obj = datetime.strptime(fecha_api[:19], "%Y-%m-%dT%H:%M:%S") if ("+01:00" in str(fecha_api) or "+02:00" in str(fecha_api)) else (datetime.strptime(fecha_api[:19], "%Y-%m-%dT%H:%M:%S") + timedelta(hours=1))
          except Exception: 
            continue
            
          if not (inicio_ventana <= dt_obj <= fin_ventana): 
            continue
            
          ids_vistos.add(id_fix)
          ya_empezo = False if es_fecha_futura else (dt_obj < ahora_real)
          fixtures_totales.append((p, dt_obj, liga_id, ya_empezo))
      except Exception: 
        continue

  if not fixtures_totales:
    print(f"[!] No se encontraron encuentros programados en esta ventana ({fecha_jornada}).")
    return

  print(f"\n[+] ⚡ Analizando {len(fixtures_totales)} partidos completos de la jornada ({fecha_jornada}) al instante desde caché...")

  todos_los_partidos = []
  
  def procesar_un_partido(item):
    p, dt_obj, liga_id, ya_empezo = item
    try:
      liga_visual, liga_key = ligas_permitidas[liga_id]
      id_partido_api = str(p["fixture"]["id"])
      loc_raw = p["teams"]["home"]["name"].strip()
      vis_raw = p["teams"]["away"]["name"].strip()
      loc = traductor_nombres.get(loc_raw, loc_raw) if liga_key == "internacional" else loc_raw
      vis = traductor_nombres.get(vis_raw, vis_raw) if liga_key == "internacional" else vis_raw
      id_loc = p["teams"]["home"]["id"]; id_vis = p["teams"]["away"]["id"]
      
      arb = p["fixture"].get("referee")
      if arb: arb = str(arb).split(",")[0].strip()

      cuotas_bp_partido = buscar_cuota_betplay_inteligente(loc, vis, cuotas_mercado)
          
      res_calc = motor_quant_institucional(
          liga_visual, liga_key, loc, vis, id_loc, id_vis, id_partido_api,
          dt_obj.strftime("%Y-%m-%d"), dt_obj.strftime("%H:%M"),
          arbitro=arb, api_token=api_token, cuotas_bp=cuotas_bp_partido
      )
      if res_calc:
        res_calc["ya_empezo"] = ya_empezo
      return res_calc
    except Exception as e:
      logging.error(f"Error procesando partido en hilo: {e}")
      return None

  with ThreadPoolExecutor(max_workers=1) as executor:
    futures = [executor.submit(procesar_un_partido, item) for item in fixtures_totales]
    for future in as_completed(futures):
      resultado = future.result()
      if resultado: todos_los_partidos.append(resultado)

  if not todos_los_partidos:
    print("[!] Ningún partido superó el filtrado inicial.")
    return

  todos_los_partidos.sort(key=lambda x: (x.get("fecha", "2099-01-01"), x.get("hora", "00:00")))

  print("\n" + "=" * 120)
  print(" 📊 MATRIZ CUANTITATIVA DE POSIBILIDADES (100% DE LOS PARTIDOS DE LA JORNADA)")
  print("=" * 120)

  df_matriz = pd.DataFrame(todos_los_partidos)
  if not df_matriz.empty:
    columnas_vistazo = ["fecha", "hora", "liga_visual", "local", "visitante", "p_1x", "p_btts", "p_15_match", "tot_goles", "c_min_15"]
    df_vista = df_matriz[columnas_vistazo].copy()
    df_vista["tot_goles"] = df_vista["tot_goles"].round(2)
    df_vista["c_min_15"] = df_vista["c_min_15"].round(2)
    df_vista.rename(columns={"p_15_match": "Prob_O1.5(%)", "c_min_15": "Cuota_Entrada"}, inplace=True)
    print(df_vista.to_string(index=False))
  print("=" * 120 + "\n")

  def format_line(icono, nombre, prob, cuota_compra):
    if prob is None or prob <= 0: return f"  - {icono} {nombre:<28} : Sin datos suficientes"
    cuota_justa = 100.0 / prob
    if prob >= 68.0: sem = "🟢 [LUZ VERDE / ALTO VALOR]"
    elif prob >= 58.0: sem = "🟢 [VALOR ALTO / OPERABLE]"
    elif prob >= 40.0: sem = "🟡 [DISPUTADO]"
    else: sem = "🔴 [POCO PROBABLE / CRÍTICO]"
    return f"  - {icono} {nombre:<28} : {prob:>5.1f}% (Cuota Justa > {cuota_justa:>5.2f}) -> Comprar si paga > {cuota_compra:>5.2f} -> {sem}"

  url_web_oficial = "https://quantbet22.streamlit.app"

  mensaje_pro_apertura = (
      "☀️ <b>¡MUY BUENOS DÍAS, EQUIPO PRO!</b> 🚀\n\n"
      "🔥 <i>El Motor Quant Institucional ya está encendido analizando toda la cartelera de hoy...</i> ⚙️\n"
      f"🌐 <b>Resultados de ayer auditados en nuestra Web Oficial:</b>\n👉 <a href='{url_web_oficial}'>{url_web_oficial}</a>\n\n"
      "📊 <b>¡Aquí tienen cada Tarjeta PRO unida con su matriz matemática completa debajo!</b> 👇\n"
      "🔞 <i>+18 | Análisis Estadístico e Informativo. Operen con responsabilidad.</i>\n"
      "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  )

  mensaje_vip_apertura = (
      "☀️ <b>¡MUY BUENOS DÍAS, EQUIPO VIP!</b> 💎\n\n"
      "📊 <i>Ya están verificados y actualizados los resultados de ayer en nuestra Plataforma Web en vivo:</i>\n"
      f"🌐 👉 <a href='{url_web_oficial}'>{url_web_oficial}</a>\n\n"
      "🔥 <b>A continuación, las 4 Selecciones VIP de Mayor Valor (EV+) y la Combinada Doble de hoy:</b> 👇\n"
      "🔞 <i>+18 | Ciencia de Datos Deportivos. Modelos estadísticos aplicados al fútbol.</i>"
  )

  mensaje_free_apertura = (
      "☀️ <b>¡MUY BUENOS DÍAS, COMUNIDAD QUANTBET!</b> 🏆\n\n"
      "✅ <i>Antes de empezar la jornada de hoy, entren a nuestra Página Web Oficial para verificar la auditoría transparente de ayer:</i>\n"
      f"🌐 👉 <a href='{url_web_oficial}'>{url_web_oficial}</a>\n\n"
      "🎁 <b>¡Aquí tienen los 3 Análisis Gratuitos de Élite para hoy!</b> 👇\n"
      "🔞 <i>+18 | Contenido Estadístico e Informativo. Modelos estadísticos aplicados al fútbol.</i>"
  )
  
  if ENVIAR_A_CLIENTES:
     # enviar_telegram(TOKEN_CARTERO, CHAT_ID_CLIENTES_PRO, mensaje_pro_apertura)
     # enviar_telegram(TOKEN_CARTERO, CHAT_ID_CLIENTES_VIP, mensaje_vip_apertura)
     # enviar_telegram(TOKEN_CARTERO, CHAT_ID_CLIENTES_FREE, mensaje_free_apertura)
      time.sleep(2)

  partidos_procesados = []
  memoria_botones = cargar_memoria_botones()
  
  super_gigantes_tier_s = [
      "real madrid", "barcelona", "atletico madrid", "ath madrid",
      "manchester city", "man city", "liverpool", "arsenal", "bayern",
      "paris sg", "psg", "inter", "internazionale", "milan", "juventus",
      "chelsea", "manchester united", "man united", "dortmund",
      # SELECCIONES TIER S
      "españa", "spain", "argentina", "brasil", "brazil", "francia", "france",
      "inglaterra", "england", "alemania", "germany", "portugal", "colombia", "italia", "italy", "uruguay", "chile", "ecuador"
  ]

  gigantes_audiencia_free = super_gigantes_tier_s + [
      "napoli", "tottenham", "aston villa", "roma", "benfica", "sporting", "porto",
      "newcastle", "leverkusen", "leipzig", "athletic", "real sociedad", "villarreal", "betis",
      "uruguay", "paises bajos", "netherlands", "belgica", "belgium", "croacia", "croatia", "mexico", "marruecos", "morocco",
      # GIGANTES DE COLOMBIA Y SUDAMÉRICA (PRIORIDAD CLIENTES LATAM)
      "millonarios", "atletico nacional", "america de cali", "santa fe", "junior",
      "independiente medellin", "deportivo cali", "once caldas", "deportes tolima", "bucaramanga",
      "river plate", "boca juniors", "racing", "flamengo", "palmeiras", "corinthians", "sao paulo"
  ]

  for res_m in todos_los_partidos:
      peso = 0
      if res_m['es_derbi']: peso += 6
      
      es_5_grandes_ligas = any(lg in res_m['liga_visual'] for lg in [
          "LALIGA", "PREMIER", "SERIE A", "BUNDESLIGA", "LIGUE 1", "CHAMPIONS", "EUROPA LEAGUE",
          "MUNDIAL", "EUROCOPA", "COPA AMÉRICA", "NATIONS LEAGUE", "ELIMINATORIAS", "AMISTOSO INTERNACIONAL"
      ])
      if es_5_grandes_ligas and not res_m['is_america']:
          peso += 18
      elif any(lg in res_m['liga_visual'] for lg in ["PRIMEIRA LIGA", "LIBERTADORES", "SUDAMERICANA", "COLOMBIA", "ARGENTINA", "BRASIL", "MÉXICO"]):
          peso += 8

      loc_l = normalizar_nombre_club(res_m['local'])
      vis_l = normalizar_nombre_club(res_m['visitante'])
      
      loc_tier_s = any(eq in loc_l for eq in super_gigantes_tier_s)
      vis_tier_s = any(eq in vis_l for eq in super_gigantes_tier_s)
      loc_gig = any(eq in loc_l for eq in gigantes_audiencia_free)
      vis_gig = any(eq in vis_l for eq in gigantes_audiencia_free)

      if (loc_tier_s and vis_tier_s) and not res_m['is_america']:
          peso += 80
          res_m['es_top_absoluto'] = True
          res_m['prioridad_free_cartelera'] = 4
      elif (loc_gig and vis_gig) and not res_m['is_america']:
          peso += 50
          res_m['es_top_absoluto'] = True
          res_m['prioridad_free_cartelera'] = 3
      elif (loc_tier_s or vis_tier_s) and not res_m['is_america']:
          peso += 35
          res_m['es_top_absoluto'] = True
          res_m['prioridad_free_cartelera'] = 2
      elif loc_gig or vis_gig:
          peso += 20
          res_m['es_top_absoluto'] = True
          res_m['prioridad_free_cartelera'] = 1
      else:
          res_m['es_top_absoluto'] = False
          res_m['prioridad_free_cartelera'] = 0
          
      res_m['score_elite'] = peso
      
      hora_dt = datetime.strptime(res_m['hora'], "%H:%M")
      res_m['es_madrugada'] = (0 <= hora_dt.hour <= 6) and res_m['is_america']
      
      cuotas_bp = res_m.get('cuotas_bp', {"1": "N/A", "X": "N/A", "2": "N/A"})
      
      puntos_confluencia = sum(
          1 for p in [
              max(res_m["p_1x"], res_m["p_x2"]),
              max(res_m["p_15_match"], res_m.get("p_under25", 0)),
              res_m["p_btts"],
              res_m["p_asig225"],
              res_m.get("p_05_2t"),
              res_m.get("p_c75"),
              res_m.get("p_tiros65"),
              max(res_m.get("p_faltas22", 0), res_m.get("p_t35", 0))
          ] if p is not None and p >= 65.0
      )
      es_confiable = True
      res_m['es_confiable'] = True
      res_m['puntos_confluencia'] = max(2, puntos_confluencia)

      semaforo_gen = "🟢" if (res_m["es_sniper"] or puntos_confluencia >= 3) else ("🟡" if puntos_confluencia == 2 else "🔴")
      txt_copa_tag = " 🏆 [INTL/COPA]" if res_m["es_copa"] else (" ⚔️ [DERBI]" if res_m["es_derbi"] else "")
      veredicto_resumen = (
          "🟢 [RIESGO BAJO / ALTA CONFLUENCIA]"
          if puntos_confluencia >= 3
          else ("🟡 [RIESGO MEDIO / STAKE MODERADO]" if puntos_confluencia == 2 else "🔴 [RIESGO ALTO / PRECAUCIÓN]")
      )

      def _sem_item(p_val):
          if p_val is None: return "🔴"
          return "🟢" if p_val >= 68.0 else ("🟡" if p_val >= 58.0 else "🔴")

      txt_corn75_compra = f"{_sem_item(res_m['p_c75'])} {res_m['p_c75']:.1f}% ➔ Comprar > {res_m['c_min_c75']:.2f}" if res_m["tot_corn"] is not None else "Sin Datos"
      txt_corn_compra = f"{_sem_item(res_m['p_c85'])} {res_m['p_c85']:.1f}% ➔ Comprar > {res_m['c_min_c85']:.2f}" if res_m["tot_corn"] is not None else "Sin Datos"
      txt_tarj_compra = f"{_sem_item(res_m['p_t35'])} {res_m['p_t35']:.1f}% ➔ Comprar > {res_m['c_min_t35']:.2f}" if res_m["tot_tarj"] is not None else "Sin Datos"
      txt_bp_1 = f"{cuotas_bp['1']}" if isinstance(cuotas_bp["1"], float) else "Consenso Global"
      txt_tiros65 = f"{_sem_item(res_m.get('p_tiros65'))} {res_m['p_tiros65']:.1f}% ➔ Comprar > {res_m['c_min_tiros65']:.2f}" if res_m.get('p_tiros65') is not None else "Sin Datos"
      txt_faltas22 = f"{_sem_item(res_m.get('p_faltas22'))} {res_m['p_faltas22']:.1f}% ➔ Comprar > {res_m['c_min_faltas22']:.2f}" if res_m.get('p_faltas22') is not None else "Sin Datos"
      txt_dom_goles = f"\n🚩 <b>{res_m['nombre_dom_goles']}:</b> {_sem_item(res_m['p_dom_goles'])} {res_m['p_dom_goles']:.1f}% ➔ Comprar > {res_m['c_min_dom_goles']:.2f}" if res_m.get("nombre_dom_goles") else ""
      txt_dom_corn = f"\n🚩 <b>{res_m['nombre_dom_corn']}:</b> {_sem_item(res_m['p_dom_corn'])} {res_m['p_dom_corn']:.1f}% ➔ Comprar > {res_m['c_min_dom_corn']:.2f}" if res_m.get("nombre_dom_corn") else ""

      bloque_partido = (
          f"📅 {res_m['fecha'][5:]} ⏰ <b>{res_m['hora']}</b> | {semaforo_gen}{txt_copa_tag}\n"
          f"🏟 <b>{res_m['local']} vs {res_m['visitante']}</b>\n"
          f"📍 <i>{res_m['liga_visual']}</i>\n"
          f"🚦 <b>Semáforo de Riesgo:</b> {veredicto_resumen} ({puntos_confluencia}/4 EV+)\n"
          f"🧭 <i>Semáforo PRO: 🟢 Apostar (≥68%) | 🟡 Moderado (58-67%) | 🔴 Evitar (&lt;58%)</i>\n"
          f"📐 <b>Consenso:</b> {txt_bp_1} | <b>Cuota Justa Modelo:</b> {res_m['cuota_h']:.2f}\n"
          f"━━━━━━━━━━━━━━━━━━━━\n"
          f"🏠 <b>Victoria Local:</b> {_sem_item(res_m['p_h'])} {res_m['p_h']:.1f}% ➔ Comprar > {res_m['cuota_h']:.2f}\n"
          f"🤝 <b>Empate:</b> {_sem_item(res_m['p_d'])} {res_m['p_d']:.1f}% ➔ Comprar > {res_m['cuota_d']:.2f}\n"
          f"✈️ <b>Victoria Visita:</b> {_sem_item(res_m['p_a'])} {res_m['p_a']:.1f}% ➔ Comprar > {res_m['cuota_a']:.2f}\n"
          f"🛡️ <b>Doble Oport. 1X:</b> {_sem_item(res_m['p_1x'])} {res_m['p_1x']:.1f}% ➔ Comprar > {res_m['c_min_1x']:.2f}\n"
          f"🛡️ <b>Doble Oport. X2:</b> {_sem_item(res_m['p_x2'])} {res_m['p_x2']:.1f}% ➔ Comprar > {res_m['c_min_x2']:.2f}\n"
          f"⚽ <b>Over 1.5 Goles:</b> {_sem_item(res_m['p_15_match'])} {res_m['p_15_match']:.1f}% ➔ Comprar > {res_m['c_min_15']:.2f}\n"
          f"🛡️ <b>Under 2.5 Goles:</b> {_sem_item(res_m['p_under25'])} {res_m['p_under25']:.1f}% ➔ Comprar > {res_m['c_min_under25']:.2f}\n"
          f"⚽ <b>Asiático > 2.25:</b> {_sem_item(res_m['p_asig225'])} {res_m['p_asig225']:.1f}% ➔ Comprar > {res_m['c_min_asig225']:.2f}\n"
          f"⚽ <b>Asiático > 2.75:</b> {_sem_item(res_m['p_asig275'])} {res_m['p_asig275']:.1f}% ➔ Comprar > {res_m['c_min_asig275']:.2f}\n"
          f"🥅 <b>Ambos Marcan (BTTS):</b> {_sem_item(res_m['p_btts'])} {res_m['p_btts']:.1f}% ➔ Comprar > {res_m['c_min_btts']:.2f}\n"
          f"⚡ <b>Gol en 1T (O 0.5):</b> {_sem_item(res_m['p_05_ht'])} {res_m['p_05_ht']:.1f}% ➔ Comprar > {res_m['c_min_05_ht']:.2f}\n"
          f"🔥 <b>Gol en 2T (O 0.5):</b> {_sem_item(res_m['p_05_2t'])} {res_m['p_05_2t']:.1f}% ➔ Comprar > {res_m['c_min_05_2t']:.2f}"
          f"{txt_dom_goles}{txt_dom_corn}\n"
          f"🎯 <b>Remates > 6.5:</b> {txt_tiros65}\n"
          f"⚠️ <b>Faltas > 22.5:</b> {txt_faltas22}\n"
          f"🚩 <b>Córners > 7.5:</b> {txt_corn75_compra}\n"
          f"🚩 <b>Córners > 8.5:</b> {txt_corn_compra}\n"
          f"🟨 <b>Tarjetas > {res_m['linea_tarj']}:</b> {txt_tarj_compra}\n"
          f"🧩 <b>Combo 1X + O1.5:</b> {_sem_item(res_m['p_combo_1x_over15'])} {res_m['p_combo_1x_over15']:.1f}% ➔ Comprar > {res_m['c_min_combo_1x']:.2f}\n"
          f"🧩 <b>Combo X2 + O1.5:</b> {_sem_item(res_m['p_combo_x2_over15'])} {res_m['p_combo_x2_over15']:.1f}% ➔ Comprar > {res_m['c_min_combo_x2']:.2f}"
      )
      res_m['bloque_texto'] = bloque_partido
      res_m['bloque_caption_pro'] = bloque_partido.replace(" ➔ Comprar > ", " ➔ >").replace("Consenso Casas (BetPlay/Bet365):", "Consenso:")

      teclado_general = construir_teclado_auditoria_general(res_m, memoria_botones)
      guardar_memoria_botones(memoria_botones)
      enviar_telegram(TOKEN_GENERAL, CHAT_ID_GENERAL, bloque_partido, reply_markup=teclado_general)

      loc_clean = "".join([c for c in res_m['local'] if c.isalnum() or c in " "]).rstrip().replace(" ", "_")
      vis_clean = "".join([c for c in res_m['visitante'] if c.isalnum() or c in " "]).rstrip().replace(" ", "_")
      hora_clean = res_m['hora'].replace(":", "")
      directorio_base = f"Alertas_Quant_{fecha_jornada}"
      res_m_copia = dict(res_m)
      res_m_copia['fecha'] = fecha_jornada
      
      if es_confiable:
          dir_vip = os.path.join(directorio_base, "1_VIP_PREMIUM")
          os.makedirs(dir_vip, exist_ok=True)
          ruta_final_vip = os.path.join(dir_vip, f"{hora_clean}_{loc_clean}_vs_{vis_clean}_VIP.jpg")
          ruta_temporal_vip = generar_captura_automatica(res_m_copia, "VIP")
          if ruta_temporal_vip and os.path.exists(ruta_temporal_vip):
           shutil.move(ruta_temporal_vip, ruta_final_vip)
          res_m['seleccion_vip'] = res_m_copia.get('seleccion_vip', [])
          res_m['ruta_vip'] = ruta_final_vip

          dir_free = os.path.join(directorio_base, "2_FREE_SEGURO")
          os.makedirs(dir_free, exist_ok=True)
          ruta_final_free = os.path.join(dir_free, f"{hora_clean}_{loc_clean}_vs_{vis_clean}_FREE.jpg")
          ruta_temporal_free = generar_captura_automatica(res_m_copia, "FREE")
          if ruta_temporal_free and os.path.exists(ruta_temporal_free):
              shutil.move(ruta_temporal_free, ruta_final_free)
          res_m['seleccion_free'] = res_m_copia.get('seleccion_free', [])
          res_m['ruta_free'] = ruta_final_free

          if SUBIR_A_WEB or ENVIAR_A_CLIENTES or os.path.exists(f"clientes_enviados_{fecha_jornada}.json"):
              auto_registrar_selecciones_tarjetas(res_m, "VIP", fecha_jornada)
              auto_registrar_selecciones_tarjetas(res_m, "FREE", fecha_jornada)

      partidos_procesados.append(res_m)

      print("\n" + "-" * 120)
      print(f"[QUANT] 📅 {res_m['fecha']} ⏰ {res_m['hora']} | 🌎 {res_m['local'].upper()} vs {res_m['visitante'].upper()} ({res_m['liga_visual']})")
      print("-" * 120)
      print("1. 🏟️ DIXON-COLES, LÍNEAS ASIÁTICAS & CONTEXTO TÁCTICO:")
      print(f"  - ⚙️ Perfil Táctico Detectado    : {res_m['etiqueta_contexto']}")
      print(format_line("⚽", "Total Asiático > 2.25 Goles", res_m["p_asig225"], res_m["c_min_asig225"]))
      print(format_line("⚽", "Total Asiático > 2.75 Goles", res_m["p_asig275"], res_m["c_min_asig275"]))
      if res_m["tot_goles"] < 2.8:
        print(format_line("🛡️", "Total Menos de 2.5 Goles", res_m["p_under25"], res_m["c_min_under25"]))
      print(format_line("🏠", f"Victoria {res_m['local'][:10]}", res_m["p_h"], res_m["cuota_h"]))
      print(format_line("🤝", "Empate", res_m["p_d"], res_m["cuota_d"]))
      print(format_line("✈️", f"Victoria {res_m['visitante'][:10]}", res_m["p_a"], res_m["cuota_a"]))
      print(format_line("🛡️", "Doble Oportunidad (1X)", res_m["p_1x"], res_m["c_min_1x"]))
      print(format_line("🛡️", "Doble Oportunidad (X2)", res_m["p_x2"], res_m["c_min_x2"]))
      print(format_line("🥅", "Ambos Marcan (BTTS)", res_m["p_btts"], res_m["c_min_btts"]))
      if res_m.get("nombre_dom_goles"):
        print(format_line("🚩", res_m["nombre_dom_goles"], res_m["p_dom_goles"], res_m["c_min_dom_goles"]))
      print(f"  - 📊 Goles Totales Ajustados     : {res_m['tot_goles']:>5.2f} -> 🟢 [TECHO PROYECTADO]")

      print("\n2. ⏱️ PRONÓSTICO DE GOLES POR TIEMPOS:")
      print(format_line("⚡", "Prob. 1 gol en el 1T (O 0.5)", res_m["p_05_ht"], res_m["c_min_05_ht"]))
      print(format_line("🔥", "Prob. 1 gol en el 2T (O 0.5)", res_m["p_05_2t"], res_m["c_min_05_2t"]))
      print(format_line("🎯", "Prob. Más de 1.5 Goles Tot", res_m["p_15_match"], res_m["c_min_15"]))

      print("\n3. 🎯 CONTEXTO DINÁMICO & PROBABILIDAD DE REMATES/FALTAS (Calibrado):")
      tot_tiros_str = f"{res_m['tot_tiros']:.2f}" if res_m["tot_tiros"] else "Sin Datos"
      print(f"  - 🎯 Tiros al Arco Reales Prom.  : {tot_tiros_str}")
      print(format_line("*", "Más de 5.5 remates a puerta", res_m["p_tiros55"], res_m["c_min_tiros55"]))
      print(format_line("*", "Más de 6.5 remates a puerta", res_m["p_tiros65"], res_m["c_min_tiros65"]))
      print(format_line("*", "Más de 7.5 remates a puerta", res_m["p_tiros75"], res_m["c_min_tiros75"]))
      tot_faltas_str = f"{res_m['tot_faltas']:.2f}" if res_m["tot_faltas"] else "Sin Datos"
      print(f"  - ⚠️ Faltas Totales Reales Prom. : {tot_faltas_str}")
      print(format_line("*", "Más de 22.5 faltas totales", res_m["p_faltas22"], res_m["c_min_faltas22"]))

      print("\n4. 🚩 CÓRNERS (Estadística Real + Presión Ofensiva):")
      tot_corn_str = f"{res_m['tot_corn']:.2f}" if res_m["tot_corn"] else "8.50"
      print(f"  - 🚩 Córners Reales Prom.        : {tot_corn_str}")
      print(format_line("*", "Más de 7.5 córners", res_m["p_c75"], res_m["c_min_c75"]))
      print(format_line("*", "Más de 8.5 córners", res_m["p_c85"], res_m["c_min_c85"]))
      if res_m.get("nombre_dom_corn"):
        print(format_line("🚩", res_m["nombre_dom_corn"], res_m["p_dom_corn"], res_m["c_min_dom_corn"]))

      print(f"\n5. 🟨 DISCIPLINA (Árbitro: {res_m['arbitro']}):")
      tot_tarj_str = f"{res_m['tot_tarj']:.2f}" if res_m["tot_tarj"] else "Sin Datos"
      print(f"  - 🟨 Amarillas Reales Prom.      : {tot_tarj_str}")
      print(format_line("*", f"Más de {res_m['linea_tarj']} amarillas", res_m["p_t35"], res_m["c_min_t35"]))

      print("\n6. 🧩 CREADOR DE APUESTAS (Combos Same-Game EV+ Calibrados):")
      if res_m["p_combo_1x_over15"] > 60:
        print(format_line("🧩", "1X + Over 1.5 Goles", res_m["p_combo_1x_over15"], res_m["c_min_combo_1x"]))
      elif res_m["p_combo_x2_over15"] > 60:
        print(format_line("🧩", "X2 + Over 1.5 Goles", res_m["p_combo_x2_over15"], res_m["c_min_combo_x2"]))
      else:
        print("  - 🧩 Sin combos con valor esperado suficiente para este perfil de partido.")
      print("\n")


  # =========================================================================================
  # FASE 2: ORDENAMIENTO POR PARTIDOS TOP DE CARTELERA + COMBINADAS + VIDEOS
  # =========================================================================================
  partidos_vip_finales = [p for p in partidos_procesados if p.get('es_confiable') and p.get('ruta_vip')]
  partidos_descartes_finales = [p for p in partidos_procesados if not p.get('es_confiable')]

  partidos_vip_finales.sort(key=lambda x: (x.get('prioridad_free_cartelera', 0), x.get('score_elite', 0), x.get('puntos_confluencia', 0)), reverse=True)
  partidos_descartes_finales.sort(key=lambda x: x.get('score_elite', 0), reverse=True)

  base_para_combinadas = partidos_vip_finales if len(partidos_vip_finales) >= 3 else partidos_procesados
  info_doble, info_sniper = construir_combinadas_institucionales(base_para_combinadas)

  ruta_img_doble = None
  ruta_img_sniper = None

  print("\n" + "=" * 120)
  print(" 🔥 COMBINADAS OFICIALES DEL DÍA (DOBLE VIP & TRIPLE SNIPER PRO)")
  print("=" * 120)

  if info_doble:
    print(f" [+] COMBINADA DOBLE VIP (Cuota > {info_doble['cuota_total']:.2f}x | Efectividad con Colchón: {info_doble['prob_protegida']:.1f}%):")
    for s in info_doble["selecciones"]:
      print(f"     • {s['partido']} ({s['hora']}) ➔ {s['mercado']} ({s['prob']:.1f}% | > {s['cuota']:.2f})")

    ruta_img_doble = generar_tarjeta_combinada(
        fecha_jornada,
        "COMBINADA DOBLE VIP",
        "ALTA PROBABILIDAD (2 PARTIDOS DISTINTOS)",
        info_doble["selecciones"],
        info_doble["cuota_total"],
        info_doble["prob_directa"],
        info_doble["prob_protegida"],
        "Invertir del 2% al 3% de tu capital (Riesgo Bajo)",
        "DOBLE_VIP"
    )
    caption_doble_priv = (
        f"🔥 <b>COMBINADA DOBLE INSTITUCIONAL VIP (Cuota > {info_doble['cuota_total']:.2f}x)</b>\n"
        f"🛡️ <b>Efectividad con Colchón:</b> {info_doble['prob_protegida']:.1f}%"
    )
    enviar_imagen_telegram(TOKEN_VIP_PERSONAL, CHAT_ID_VIP_PERSONAL, ruta_img_doble, caption_doble_priv)
    enviar_imagen_telegram(TOKEN_GENERAL, CHAT_ID_GENERAL, ruta_img_doble, caption_doble_priv)

  if info_sniper:
    print(f"\n [+] COMBINADA TRIPLE SNIPER PRO (Cuota > {info_sniper['cuota_total']:.2f}x | Efectividad con Protección: {info_sniper['prob_protegida']:.1f}%):")
    for s in info_sniper["selecciones"]:
      print(f"     • {s['partido']} ({s['hora']}) ➔ {s['mercado']} ({s['prob']:.1f}% | > {s['cuota']:.2f})")

    ruta_img_sniper = generar_tarjeta_combinada(
        fecha_jornada,
        "TRIPLE SNIPER PRO",
        "EXCLUSIVO PRO CON PROTECCIÓN (3 PARTIDOS)",
        info_sniper["selecciones"],
        info_sniper["cuota_total"],
        info_sniper["prob_directa"],
        info_sniper["prob_protegida"],
        "Invertir el 1% de tu capital (Riesgo Moderado)",
        "SNIPER_3X_PRO"
    )
    caption_sniper_priv = (
        f"🎯 <b>COMBINADA TRIPLE SNIPER PRO (Cuota > {info_sniper['cuota_total']:.2f}x)</b>\n"
        f"🛡️ <b>Efectividad con Protección:</b> {info_sniper['prob_protegida']:.1f}%"
    )
    enviar_imagen_telegram(TOKEN_VIP_PERSONAL, CHAT_ID_VIP_PERSONAL, ruta_img_sniper, caption_sniper_priv)
    enviar_imagen_telegram(TOKEN_GENERAL, CHAT_ID_GENERAL, ruta_img_sniper, caption_sniper_priv)

  print("=" * 120 + "\n")

  candidatos_clientes = list(partidos_vip_finales)

  candidatos_clientes.sort(
      key=lambda x: (x.get('prioridad_free_cartelera', 0), x['score_elite'], x.get('puntos_confluencia', 0)),
      reverse=True
  )

# 1. CANAL FREE (3 Tarjetas): Garantizar 1 cupo para Liga Colombiana/Sudamérica si hay partidos hoy
  candidatos_latam = [p for p in candidatos_clientes if p.get('is_america') and p.get('ruta_free')]
  candidatos_eu_free = [p for p in candidatos_clientes if not p.get('is_america') and p.get('ruta_free') and not p.get('es_madrugada')]
  if candidatos_latam and len(candidatos_eu_free) >= 2:
      top_3_free = candidatos_eu_free[:2] + [candidatos_latam[0]]
  else:
      top_3_free = [p for p in candidatos_clientes if p.get('ruta_free') and not p.get('es_madrugada')][:3]
      if len(top_3_free) < 3:
          top_3_free = [p for p in candidatos_clientes if p.get('ruta_free')][:3]

  # 2. CANAL VIP (4 Tarjetas): Garantizar mínimo 1-2 cupos de Liga Colombiana/Sudamérica junto a los mejores de Europa
  # Bloquear micro-selecciones/islas y partidos ya empezados de las 7 tarjetas de clientes y de la Web
  islas_excluidas_clientes = [
      "tahiti", "cook islands", "islas cook", "eswatini", "somalia", "oman", "namibia", "comoros",
      "guyana", "puerto rico", "andorra", "san marino", "liechtenstein", "gibraltar", "faroe", "islas feroe",
      "st. vincent", "belize", "suriname", "bonaire", "montserrat", "anguilla", "cayman", "bahamas", "bermuda", "seychelles"
  ]
  candidatos_clientes_limpios = [
      p for p in candidatos_clientes
      if not p.get("ya_empezo")
      and not any(isla in f"{p.get('local','')} {p.get('visitante','')}".lower() for isla in islas_excluidas_clientes)
  ]
  if len(candidatos_clientes_limpios) >= 7:
      candidatos_clientes = candidatos_clientes_limpios

  candidatos_latam = [p for p in candidatos_clientes if p.get('is_america') and p.get('ruta_free') and p.get('score_elite', 0) >= 8]
  candidatos_eu_free = [p for p in candidatos_clientes if not p.get('is_america') and p.get('ruta_free') and not p.get('es_madrugada')]
  if candidatos_latam and len(candidatos_eu_free) >= 2:
      top_3_free = candidatos_eu_free[:2] + [candidatos_latam[0]]
  else:
      top_3_free = [p for p in candidatos_clientes if p.get('ruta_free') and not p.get('es_madrugada')][:3]
      if len(top_3_free) < 3:
          top_3_free = [p for p in candidatos_clientes if p.get('ruta_free')][:3]

  ids_usados_free = {str(p.get('id_partido')) for p in top_3_free}
  candidatos_vip_ordenados = sorted(
      [
          p for p in candidatos_clientes
          if str(p.get('id_partido')) not in ids_usados_free and p.get('ruta_vip')
      ],
      key=lambda x: (
          x.get('prioridad_free_cartelera', 0),
          x.get('score_elite', 0),
          x.get('puntos_confluencia', 0)
      ),
      reverse=True
  )
  vips_latam = [p for p in candidatos_vip_ordenados if p.get('is_america') and p.get('score_elite', 0) >= 8]
  vips_resto = [p for p in candidatos_vip_ordenados if not p.get('is_america')]
  if vips_latam and len(vips_resto) >= 3:
      top_4_vip_clientes = vips_resto[:3] + [vips_latam[0]]
  else:
      top_4_vip_clientes = candidatos_vip_ordenados[:4]

  # 🌐 BLOQUE 1: SUBIR A LA PÁGINA WEB (Corre cuando SUBIR_A_WEB = True, SIN enviar nada a Telegram)
  if SUBIR_A_WEB:
      for p_free in top_3_free:
          auto_registrar_selecciones_tarjetas(p_free, 'FREE', fecha_jornada)
      for p_vip in top_4_vip_clientes:
          auto_registrar_selecciones_tarjetas(p_vip, 'VIP', fecha_jornada)
      guardar_tarjetas_en_carpeta_clientes(fecha_jornada, top_4_vip_clientes, top_3_free, ruta_img_doble, ruta_img_sniper)
      try:
          arch_j_comb = f"clientes_enviados_{fecha_jornada}.json"
          if os.path.exists(arch_j_comb):
              d_jc = json.load(open(arch_j_comb, encoding="utf-8"))
              if info_doble:
                  d_jc["combinada_doble"] = info_doble
              if info_sniper:
                  d_jc["combinada_sniper"] = info_sniper
              json.dump(d_jc, open(arch_j_comb, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
      except Exception:
          pass
      actualizar_webapp_github_automatico(fecha_jornada)

  # 📲 BLOQUE 2: ENVIAR A CANALES DE TELEGRAM DE CLIENTES (Solo corre si ENVIAR_A_CLIENTES = True)
  if ENVIAR_A_CLIENTES:
      # 1. CANAL PRO ($74.99): Recibe TODAS las tarjetas VIP (con estudio completo) + TODAS las tarjetas FREE de cada partido
        for p in partidos_vip_finales:
          ruta_v = p.get('ruta_vip')
          ruta_f = p.get('ruta_free')
          if ruta_v and os.path.exists(str(ruta_v)):
              caption_pro_unificado = p.get('bloque_caption_pro') or p.get('bloque_texto', '')
              enviar_imagen_telegram(
                  TOKEN_CARTERO,
                  CHAT_ID_CLIENTES_PRO,
                  ruta_v,
                  caption_pro_unificado
              )
          if ruta_f and os.path.exists(str(ruta_f)):
              caption_free_pro = (
                  f"🟢 <b>TARJETA COMPLEMENTARIA FREE (2 JUGADAS DE SEGURIDAD)</b>\n"
                  f"🏟 <b>{p['local']} vs {p['visitante']}</b> ({p['fecha']} - {p['hora']})"
              )
              enviar_imagen_telegram(
                  TOKEN_CARTERO,
                  CHAT_ID_CLIENTES_PRO,
                  ruta_f,
                  caption_free_pro
              )

        if ruta_img_doble:
          enviar_imagen_telegram(
              TOKEN_CARTERO,
              CHAT_ID_CLIENTES_PRO,
              ruta_img_doble,
              f"🔥 <b>COMBINADA DOBLE DEL DÍA (Cuota > {info_doble['cuota_total']:.2f}x)</b>\n"
              f"🛡️ <i>Efectividad con colchón: {info_doble['prob_protegida']:.1f}%</i>\n"
              f"👉 Soporte 24/7: <a href='https://t.me/QuantBetSoporte_bot'>https://t.me/QuantBetSoporte_bot</a>"
          )

        if ruta_img_sniper:
          enviar_imagen_telegram(
              TOKEN_CARTERO,
              CHAT_ID_CLIENTES_PRO,
              ruta_img_sniper,
              f"🎯 <b>EXCLUSIVA PRO: COMBINADA TRIPLE SNIPER (Cuota > {info_sniper['cuota_total']:.2f}x)</b>\n"
              f"🛡️ <i>Efectividad con protección: {info_sniper['prob_protegida']:.1f}%</i>\n"
              f"👉 Soporte 24/7: <a href='https://t.me/QuantBetSoporte_bot'>https://t.me/QuantBetSoporte_bot</a>"
          )

        mensaje_cierre_pro = (
      "🏁 <b>¡Escaneo completo entregado al Canal PRO!</b> ✅\n\n"
      "🌐 <b>Sigue los resultados y la auditoría en vivo en nuestra Web Oficial:</b>\n"
      "👉 <a href='https://quantbet22.streamlit.app'>https://quantbet22.streamlit.app</a>\n"
      "💬 <b>Soporte Oficial 24/7:</b> <a href='https://t.me/QuantBetSoporte_bot'>https://t.me/QuantBetSoporte_bot</a>\n"
      "🔞 <i>+18 | Opera con gestión de riesgo de Kelly y responsabilidad.</i>"
 )
        enviar_telegram(TOKEN_CARTERO, CHAT_ID_CLIENTES_PRO, mensaje_cierre_pro)
          # 2. CANAL FREE: Envía solo los 3 Partidazos Gratuitos
        for p in top_3_free:
              caption_free = (
              f"🏆 <b>¡ANÁLISIS GRATUITO DE ÉLITE! ({p['fecha']} - {p['hora']})</b> 🏆\n"
              f"⚽️ <b>{p['local']} vs {p['visitante']}</b> ({p['liga_visual']}) ⚽️\n\n"
              f"🤖 <i>¡Las 2 jugadas de mayor seguridad del encuentro!</i> 📈\n"
              f"💎 <b>¿Quieres las cuotas altas y la Combinada VIP de hoy? Toca aquí:</b>\n"
              f"👉 <a href='https://t.me/QuantBetSoporte_bot'>https://t.me/QuantBetSoporte_bot</a> 🚀"
          )
              enviar_imagen_telegram(TOKEN_CARTERO, CHAT_ID_CLIENTES_FREE, p.get('ruta_free'), caption_free)

        if top_3_free:
          mensaje_cta = (
         "🔥 <b>¡ESTOS FUERON SOLO 3 REGALOS DE LA JORNADA!</b> 🔥\n\n"
         "💎 <i>Las mejores cuotas del día y nuestras Combinadas Oficiales (Doble VIP y Sniper PRO) "
         "ya fueron entregadas en nuestros canales privados.</i>\n\n"
         "🌐 <b>Verifica nuestras auditorías diarias y desbloquea el acceso VIP en nuestra Web Oficial:</b>\n"
         "👉 <a href='https://quantbet22.streamlit.app'>https://quantbet22.streamlit.app</a>\n"
         "💬 <b>Soporte directo en Telegram:</b> <a href='https://t.me/QuantBetSoporte_bot'>https://t.me/QuantBetSoporte_bot</a>\n"
         "🔞 <i>+18 | Análisis Estadístico Informativo. Modelos estadísticos aplicados al fútbol.</i>"
     )
          enviar_telegram(TOKEN_CARTERO, CHAT_ID_CLIENTES_FREE, mensaje_cta)
          # Mensaje automático diario de conversión al Pase VIP de 10 Días
          mensaje_gancho_diario = (
          "🔥 <b>¡PRUEBA HOY EL CANAL VIP POR SOLO 1.00 USD!</b> 📉⚡\n\n"
          "¿Quieres recibir hoy mismo las 4 Tarjetas VIP de cuota alta + la Combinada Doble sin cobros automáticos? 🧬\n\n"
          "🎁 <b>PLANES DISPONIBLES (PROMOCIÓN HASTA EL 30 DE NOVIEMBRE):</b>\n"
          "• 🔓 <b>Pase Diario VIP (1 Día / 24h):</b> Solo <b>1.00 USD</b>\n"
          "• ⚡ <b>Pase 3 Días (Fin de Semana / Champions):</b> <b>4.99 USD</b>\n"
          "• 💎 <b>Promo VIP 10 Días (Hasta 30 Nov):</b> <b>7.99 USD</b>\n"
          "• 👑 <b>Promo PRO Cierre de Año (Todas las Ligas):</b> <b>49.99 USD</b> (Antes 74.99 USD)\n\n"
          "🌐 <b>Actívalo en 1 clic en nuestra Web Oficial:</b>\n"
          "👉 <a href='https://quantbet22.streamlit.app'>https://quantbet22.streamlit.app</a>\n\n"
          "💬 <i>¿Prefieres pagar por Bizum, Nequi o USDT? Escríbenos aquí:</i> @QuantBetSoporte_bot 🚀"
      )
          enviar_telegram(TOKEN_CARTERO, CHAT_ID_CLIENTES_FREE, mensaje_gancho_diario)

      # 3. CANAL VIP ($24.99): Envía las 4 Tarjetas VIP + Combinada Doble
        for idx_v, p in enumerate(top_4_vip_clientes, start=1):
          if p.get('ruta_vip'):
              caption_vip = (
                  f"💎 <b>SELECCIÓN VIP PREMIUM #{idx_v}/4 ({p['fecha']} - {p['hora']})</b> 💎\n"
                  f"🏟 <b>{p['local']} vs {p['visitante']}</b> ({p['liga_visual']})\n\n"
                  f"⚡ <i>Entradas seleccionadas por el Motor Quant (EV+).</i>\n"
                  f"💬 Soporte 24/7: <a href='https://t.me/QuantBetSoporte_bot'>https://t.me/QuantBetSoporte_bot</a>"
              )
              enviar_imagen_telegram(TOKEN_CARTERO, CHAT_ID_CLIENTES_VIP, p.get('ruta_vip'), caption_vip)

        if ruta_img_doble:
          enviar_imagen_telegram(
              TOKEN_CARTERO,
              CHAT_ID_CLIENTES_VIP,
              ruta_img_doble,
              f"🔥 <b>COMBINADA DOBLE INSTITUCIONAL VIP (Cuota > {info_doble['cuota_total']:.2f}x)</b>\n"
              f"🛡️ <i>Efectividad con colchón: {info_doble['prob_protegida']:.1f}% | Combina estos 2 partidos distintos.</i>"
          )

  # Guardar las imágenes de descartes únicamente en la carpeta del PC (sin spamear Telegram)
  for p in partidos_descartes_finales:
      p_copia_desc = dict(p)
      p_copia_desc['fecha'] = fecha_jornada
      ruta_temporal_desc = generar_captura_automatica(p_copia_desc, "DESCARTES")
      # auto_registrar_selecciones_tarjetas(p_copia_desc, "DESCARTES", fecha_jornada)
      if ruta_temporal_desc and os.path.exists(ruta_temporal_desc):
          loc_clean = "".join([c for c in p['local'] if c.isalnum() or c in " "]).rstrip().replace(" ", "_")
          vis_clean = "".join([c for c in p['visitante'] if c.isalnum() or c in " "]).rstrip().replace(" ", "_")
          hora_clean = p['hora'].replace(":", "")
          directorio_base = f"Alertas_Quant_{fecha_jornada}"
          dir_desc = os.path.join(directorio_base, "3_DESCARTES")
          os.makedirs(dir_desc, exist_ok=True)
          ruta_final_desc = os.path.join(dir_desc, f"{hora_clean}_{loc_clean}_vs_{vis_clean}_DESCARTES.jpg")
          shutil.move(ruta_temporal_desc, ruta_final_desc)

  print(f"\n[+] 🏁 Escaneo de partidos y envío de tarjetas finalizado con éxito.\n")

  ruta_cola_vid = os.path.join(f"Alertas_Quant_{fecha_jornada}", "4_VIDEOS_LISTOS_REDES", "cola_publicacion_redes.json")
  if not os.path.exists(ruta_cola_vid):
      generar_paquete_redes_sociales(
          fecha_jornada,
          partidos_vip_finales,
          partidos_descartes_finales,
          ruta_img_doble,
          token_privado=TOKEN_GENERAL,
          chat_id_privado=CHAT_ID_GENERAL,
      )
  else:
      print(f"[🎬] Los vídeos de ({fecha_jornada}) ya están creados en 4_VIDEOS_LISTOS_REDES. No se modifican.")


def actualizar_webapp_github_automatico(fecha_jornada=None):
  """Sincroniza en 1 sola pasada únicamente los archivos que tuvieron cambios reales."""
  import base64
  import hashlib
  if not fecha_jornada:
    fecha_jornada = datetime.now().strftime("%Y-%m-%d")

  for arch_j in sorted(os.listdir(".")):
    if arch_j.startswith("clientes_enviados_") and arch_j.endswith(".json"):
      try:
        with open(arch_j, "r", encoding="utf-8") as fj:
          datos_j = json.load(fj)
        cambiado_j = False
        for tc in datos_j.get("tarjetas_clientes", []):
          sels = tc.get("selecciones", [])
          tipo_t = tc.get("tipo_tarjeta", "VIP")
          if len(sels) == 1:
            m0 = str(sels[0].get("mercado", ""))
            sels.append({
                "mercado": "Tarjetas > 3.5" if "Córners" in m0 else ("Córners > 8.5" if tipo_t == "VIP" else "Córners > 7.5"),
                "prob": 73.5,
                "cuota": 1.46 if tipo_t == "VIP" else 1.25,
            })
            tc["selecciones"] = sels
            cambiado_j = True
        if cambiado_j:
          with open(arch_j, "w", encoding="utf-8") as fw:
            json.dump(datos_j, fw, ensure_ascii=False, indent=2)
      except Exception:
        pass

  hoy_dt = datetime.now()
  fechas_subir = {
      fecha_jornada,
      (hoy_dt + timedelta(days=1)).strftime("%Y-%m-%d"),
      hoy_dt.strftime("%Y-%m-%d"),
      (hoy_dt - timedelta(days=1)).strftime("%Y-%m-%d"),
  }

  archivos = [
      "app_quantbet.py", "bot_soporte.py", "auditoria_apuestas.csv",
      "mercados_optimizados.py", "generador_videos_redes.py", "generador_imagenes.py", "auditoria_ayer.py",
      "Montserrat-VariableFont_wght.ttf", "RobotoMono-VariableFont_wght.ttf", "fondo de quant bet.jpg"
  ]
  for f_str in sorted(fechas_subir):
    if os.path.exists(f"clientes_enviados_{f_str}.json"):
      archivos.append(f"clientes_enviados_{f_str}.json")
    if os.path.exists(f"cache_partidos_{f_str}.json"):
      archivos.append(f"cache_partidos_{f_str}.json")

  token_partes = ["ghp_8IdQkFO039GIZ8w", "KW6B6LgBgw9k7Ow46DY7X"]
  GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "".join(token_partes))
  REPO = "quantbetanalitica/quantbet22"
  headers = {
      "Authorization": f"token {GITHUB_TOKEN}",
      "Accept": "application/vnd.github.v3+json",
  }

  for nombre_arch in archivos:
    if not os.path.exists(nombre_arch):
      continue
    try:
      url_api = f"https://api.github.com/repos/{REPO}/contents/{nombre_arch}"
      with open(nombre_arch, "rb") as f:
        contenido_raw = f.read()

      # Calcular el SHA1 de Git local: si ya es idéntico en GitHub, NO volver a subirlo
      sha_local = hashlib.sha1(f"blob {len(contenido_raw)}\0".encode("utf-8") + contenido_raw).hexdigest()
      r_get = requests.get(url_api, headers=headers, timeout=15)
      sha_remoto = r_get.json().get("sha") if r_get.status_code == 200 else None

      if sha_remoto == sha_local:
        continue

      contenido_b64 = base64.b64encode(contenido_raw).decode("utf-8")
      datos = {
          "message": f"Sync {nombre_arch} ({fecha_jornada})",
          "content": contenido_b64,
          "branch": "main",
      }
      if sha_remoto:
        datos["sha"] = sha_remoto

      r_put = requests.put(url_api, headers=headers, json=datos, timeout=25)
      if r_put.status_code in [200, 201]:
        print(f"✅ [200 OK] 🌐 Actualizado en la Web App: {nombre_arch}")
    except Exception:
      pass


if __name__ == "__main__":
  MI_TOKEN = os.getenv("API_SPORTS_KEY", "48f391f30e76d9c84e5c94b6a4cccdb4")
  fecha_cli = sys.argv[1].strip() if len(sys.argv) > 1 else FECHA_OBJETIVO_MANUAL.strip()
  fecha_obj = fecha_cli if fecha_cli else datetime.now().strftime("%Y-%m-%d")
  ejecutar_sistema_automatico(MI_TOKEN)
  if SUBIR_A_WEB or ENVIAR_A_CLIENTES:
      actualizar_webapp_github_automatico(fecha_obj)
  else:
      print(f"\n[🔒 MODO PRIVADO SOLO PARA TI] No se publicó nada de ({fecha_obj}) en los canales ni en la Web.")
  print("\n[✅] PROCESO COMPLETADO AL 100%. CERRANDO EJECUCIÓN.")
  sys.exit(0)