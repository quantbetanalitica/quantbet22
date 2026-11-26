"""
Motor Ambiental Real (Fase 2 - QuantBet22)
Consulta clima real a la hora exacta del partido (Open-Meteo API gratuita, sin API key),
combina altitud exacta en metros, tipo de césped (natural/sintético), temperatura,
humedad relativa, lluvia (mm/h) y viento (km/h), y calcula ajustes físicos acotados
sobre lambdas de goles, remates, faltas, ritmo 1T/2T y sobredispersión (phi).
"""

import json
import os
import re
import time
import unicodedata
from datetime import datetime
import requests

ARCHIVO_CACHE_CLIMA = f"cache_clima_estadios_{datetime.now().strftime('%Y-%m-%d')}.json"
_MEMORIA_CLIMA = None

# Base de datos de estadios / ciudades: clave -> (lat, lon, altitud_m, cesped)
ESTADIOS_DB = {
    # --- COLOMBIA ---
    "millonarios": (4.6459, -74.0775, 2640, "natural"),
    "santa fe": (4.6459, -74.0775, 2640, "natural"),
    "independiente santa fe": (4.6459, -74.0775, 2640, "natural"),
    "la equidad": (4.6231, -74.1353, 2600, "natural"),
    "internacional de bogota": (4.6231, -74.1353, 2600, "natural"),
    "fortaleza ceif": (4.6231, -74.1353, 2600, "natural"),
    "deportivo pasto": (1.1983, -77.2778, 2527, "natural"),
    "boyaca chico": (5.5419, -73.3522, 2820, "natural"),
    "patriotas": (5.5419, -73.3522, 2820, "natural"),
    "once caldas": (5.0561, -75.4897, 2150, "natural"),
    "atletico nacional": (6.2568, -75.5902, 1495, "natural"),
    "independiente medellin": (6.2568, -75.5902, 1495, "natural"),
    "envigado": (6.1645, -75.5988, 1575, "natural"),
    "aguilas doradas": (6.1536, -75.3742, 2125, "natural"),
    "america de cali": (3.4299, -76.5410, 1018, "natural"),
    "deportivo cali": (3.5216, -76.4169, 980, "natural"),
    "junior": (10.9269, -74.8006, 18, "natural"),
    "atletico junior": (10.9269, -74.8006, 18, "natural"),
    "atletico bucaramanga": (7.1365, -73.1166, 959, "natural"),
    "bucaramanga": (7.1365, -73.1166, 959, "natural"),
    "deportes tolima": (4.4296, -75.2185, 1285, "natural"),
    "deportivo pereira": (4.8047, -75.7522, 1411, "natural"),
    "jaguares": (8.7581, -75.8706, 18, "natural"),
    "union magdalena": (11.2241, -74.1856, 6, "natural"),
    "cucuta": (7.8939, -72.5078, 320, "natural"),
    "alianza": (10.4631, -73.2532, 169, "natural"),
    "llaneros": (4.1322, -73.6214, 467, "natural"),

    # --- SUDAMÉRICA (ARGENTINA, BRASIL, ALTURA ANDINA) ---
    "bolivar": (-16.4995, -68.1227, 3640, "natural"),
    "the strongest": (-16.4995, -68.1227, 3640, "natural"),
    "always ready": (-16.4897, -68.1942, 4090, "sintetico"),
    "nacional potosi": (-19.5789, -65.7611, 3900, "natural"),
    "bolivia": (-16.4897, -68.1942, 4090, "natural"),
    "ldu quito": (-0.1077, -78.4891, 2850, "natural"),
    "independiente del valle": (-0.3136, -78.4450, 2500, "natural"),
    "el nacional": (-0.1775, -78.4765, 2850, "natural"),
    "aucas": (-0.2814, -78.5453, 2850, "natural"),
    "ecuador": (-0.1775, -78.4765, 2850, "natural"),
    "cienciano": (-13.5256, -71.9659, 3399, "natural"),
    "melgar": (-16.4070, -71.5205, 2335, "natural"),
    "boca juniors": (-34.6356, -58.3648, 25, "natural"),
    "river plate": (-34.5453, -58.4498, 25, "natural"),
    "racing club": (-34.6675, -58.3686, 20, "natural"),
    "independiente": (-34.6703, -58.3710, 20, "natural"),
    "san lorenzo": (-34.6520, -58.4401, 25, "natural"),
    "velez": (-34.6353, -58.5207, 25, "natural"),
    "huracan": (-34.6433, -58.3964, 25, "natural"),
    "lanus": (-34.7177, -58.3838, 20, "natural"),
    "estudiantes": (-34.9119, -57.9389, 20, "natural"),
    "gimnasia": (-34.9108, -57.9326, 20, "natural"),
    "talleres": (-31.3689, -64.2462, 430, "natural"),
    "rosario central": (-32.9140, -60.6746, 30, "natural"),
    "newells": (-32.9559, -60.6615, 30, "natural"),
    "independiente rivadavia": (-32.8911, -68.8628, 750, "natural"),
    "palmeiras": (-23.5275, -46.6785, 760, "sintetico"),
    "botafogo": (-22.8933, -43.2923, 25, "sintetico"),
    "athletico-pr": (-25.4483, -49.2769, 935, "sintetico"),
    "atletico-mg": (-19.9300, -44.0138, 860, "sintetico"),
    "atletico mineiro": (-19.9300, -44.0138, 860, "sintetico"),
    "flamengo": (-22.9122, -43.2302, 15, "natural"),
    "fluminense": (-22.9122, -43.2302, 15, "natural"),
    "vasco": (-22.8908, -43.2280, 15, "natural"),
    "sao paulo": (-23.6001, -46.7201, 760, "natural"),
    "corinthians": (-23.5453, -46.4743, 760, "natural"),
    "santos": (-23.9511, -46.3389, 10, "natural"),
    "cruzeiro": (-19.8659, -43.9711, 850, "natural"),
    "gremio": (-29.9739, -51.1948, 15, "natural"),
    "internacional": (-30.0656, -51.2361, 15, "natural"),
    "bahia": (-12.9788, -38.5044, 15, "natural"),
    "fortaleza": (-3.8073, -38.5225, 25, "natural"),
    "vitoria": (-12.9192, -38.4272, 20, "natural"),
    "chapecoense": (-27.1041, -52.6070, 674, "sintetico"),
    "cuiaba": (-15.6039, -56.1217, 175, "natural"),

    # --- MÉXICO (LIGA MX) & MLS ---
    "america": (19.3029, -99.1505, 2240, "natural"),
    "club america": (19.3029, -99.1505, 2240, "natural"),
    "cruz azul": (19.3029, -99.1505, 2240, "natural"),
    "pumas": (19.3319, -99.1921, 2270, "natural"),
    "toluca": (19.2874, -99.6669, 2660, "natural"),
    "pachuca": (20.1052, -98.7562, 2426, "natural"),
    "puebla": (19.0782, -98.1644, 2135, "natural"),
    "guadalajara": (20.6817, -103.4628, 1566, "natural"),
    "atlas": (20.7050, -103.3282, 1550, "natural"),
    "monterrey": (25.6691, -100.2444, 540, "natural"),
    "tigres": (25.7226, -100.3120, 540, "natural"),
    "leon": (21.1157, -101.6576, 1815, "natural"),
    "tijuana": (32.5060, -116.9936, 50, "sintetico"),
    "seattle": (47.5952, -122.3316, 15, "sintetico"),
    "portland": (45.5215, -122.6917, 25, "sintetico"),
    "vancouver": (49.2768, -123.1120, 15, "sintetico"),
    "atlanta": (33.7554, -84.4008, 320, "sintetico"),
    "charlotte": (35.2258, -80.8528, 220, "sintetico"),
    "new england": (42.0909, -71.2643, 80, "sintetico"),
    "colorado": (39.8056, -104.8919, 1609, "natural"),
    "real salt lake": (40.5829, -111.8934, 1340, "natural"),
    "inter miami": (26.1931, -80.1611, 5, "natural"),
    "orlando city": (28.5411, -81.3893, 25, "natural"),
    "st. louis": (38.6312, -90.2108, 140, "natural"),
    "lafc": (34.0128, -118.2841, 60, "natural"),
    "nashville": (36.1301, -86.7656, 150, "natural"),
    "cincinnati": (39.1114, -84.5222, 170, "natural"),

    # --- EUROPA (TOP 5, CHAMPIONS & NÓRDICOS / SINTÉTICOS) ---
    "real madrid": (40.4530, -3.6883, 667, "natural"),
    "atletico madrid": (40.4362, -3.5995, 650, "natural"),
    "rayo vallecano": (40.3919, -3.6589, 650, "natural"),
    "getafe": (40.3256, -3.7148, 620, "natural"),
    "barcelona": (41.3809, 2.1228, 40, "natural"),
    "espanyol": (41.3479, 2.0757, 25, "natural"),
    "athletic": (43.2641, -2.9494, 20, "natural"),
    "real sociedad": (43.3014, -1.9736, 15, "natural"),
    "sevilla": (37.3840, -5.9707, 15, "natural"),
    "real betis": (37.3565, -5.9817, 15, "natural"),
    "valencia": (39.4747, -0.3583, 15, "natural"),
    "levante": (39.4947, -0.3642, 15, "natural"),
    "villarreal": (39.9442, -0.1035, 45, "natural"),
    "celta": (42.2118, -8.7397, 25, "natural"),
    "osasuna": (42.7967, -1.6371, 450, "natural"),
    "girona": (41.9613, 2.8286, 75, "natural"),
    "manchester city": (53.4831, -2.2004, 50, "natural"),
    "manchester united": (53.4631, -2.2913, 40, "natural"),
    "liverpool": (53.4308, -2.9608, 35, "natural"),
    "everton": (53.4388, -2.9663, 35, "natural"),
    "arsenal": (51.5549, -0.1084, 30, "natural"),
    "chelsea": (51.4817, -0.1910, 15, "natural"),
    "tottenham": (51.6042, -0.0662, 20, "natural"),
    "brentford": (51.4907, -0.2886, 15, "natural"),
    "west ham": (51.5387, -0.0166, 10, "natural"),
    "newcastle": (54.9756, -1.6217, 65, "natural"),
    "aston villa": (52.5091, -1.8848, 120, "natural"),
    "brighton": (50.8616, -0.0837, 45, "natural"),
    "inter": (45.4781, 9.1240, 120, "natural"),
    "internazionale": (45.4781, 9.1240, 120, "natural"),
    "milan": (45.4781, 9.1240, 120, "natural"),
    "juventus": (45.1096, 7.6413, 250, "natural"),
    "torino": (45.0418, 7.6500, 240, "natural"),
    "napoli": (40.8280, 14.1931, 20, "natural"),
    "roma": (41.9341, 12.4547, 25, "natural"),
    "lazio": (41.9341, 12.4547, 25, "natural"),
    "atalanta": (45.7092, 9.6808, 250, "natural"),
    "fiorentina": (43.7808, 11.2823, 55, "natural"),
    "bologna": (44.4923, 11.3098, 60, "natural"),
    "monza": (45.5829, 9.3080, 160, "natural"),
    "como": (45.8141, 9.0725, 200, "natural"),
    "bayern": (48.2188, 11.6247, 510, "natural"),
    "dortmund": (51.4926, 7.4519, 90, "natural"),
    "leverkusen": (51.0383, 7.0022, 50, "natural"),
    "leipzig": (51.3458, 12.3482, 115, "natural"),
    "frankfurt": (50.0686, 8.6455, 110, "natural"),
    "stuttgart": (48.7923, 9.2320, 230, "natural"),
    "paris saint-germain": (48.8414, 2.2530, 35, "natural"),
    "paris sg": (48.8414, 2.2530, 35, "natural"),
    "psg": (48.8414, 2.2530, 35, "natural"),
    "marseille": (43.2698, 5.3959, 25, "natural"),
    "lyon": (45.7653, 4.9821, 180, "natural"),
    "lille": (50.6119, 3.1305, 35, "natural"),
    "monaco": (43.7276, 7.4156, 20, "natural"),
    "benfica": (38.7527, -9.1847, 75, "natural"),
    "sporting": (38.7612, -9.1608, 80, "natural"),
    "porto": (41.1618, -8.5836, 100, "natural"),
    "ajax": (52.3144, 4.9419, 5, "natural"),
    "psv": (51.4417, 5.4674, 20, "natural"),
    "feyenoord": (51.8939, 4.5233, 5, "natural"),
    "club brugge": (51.1933, 3.1806, 10, "natural"),
    "galatasaray": (41.1034, 28.9912, 100, "natural"),
    "fenerbahce": (40.9877, 29.0369, 15, "natural"),
    "besiktas": (41.0394, 28.9945, 25, "natural"),
    "celtic": (55.8497, -4.2055, 25, "natural"),
    "rangers": (55.8532, -4.3093, 20, "natural"),
    "olympiacos": (37.9464, 23.6644, 15, "natural"),
    "shakhtar": (51.5540, 7.0676, 50, "natural"),
    # Nórdicos y Sintéticos Europeos
    "bodo": (67.2756, 14.4008, 15, "sintetico"),
    "glimt": (67.2756, 14.4008, 15, "sintetico"),
    "molde": (62.7336, 7.1489, 10, "sintetico"),
    "viking": (58.9147, 5.7313, 15, "sintetico"),
    "tromso": (69.6489, 18.9351, 90, "sintetico"),
    "rosenborg": (63.4125, 10.4050, 35, "natural"),
    "young boys": (46.9631, 7.4648, 550, "sintetico"),
    "lugano": (46.0226, 8.9606, 275, "sintetico"),
    "astana": (51.1082, 71.4026, 350, "sintetico"),
    "djurgarden": (59.2909, 18.0846, 25, "sintetico"),
    "hammarby": (59.2909, 18.0846, 25, "sintetico"),
    "hjk": (60.1877, 24.9225, 20, "sintetico"),
    "qarabag": (40.3974, 49.8524, 30, "natural"),
    "sabah": (40.4640, 49.7540, 35, "natural"),

    # --- ARABIA SAUDITA ---
    "al-hilal": (24.7136, 46.6753, 612, "natural"),
    "al hilal": (24.7136, 46.6753, 612, "natural"),
    "al-nassr": (24.6725, 46.6238, 612, "natural"),
    "al nassr": (24.6725, 46.6238, 612, "natural"),
    "al-shabab": (24.7136, 46.6753, 612, "natural"),
    "al-ahli": (21.7634, 39.1642, 15, "natural"),
    "al ahli": (21.7634, 39.1642, 15, "natural"),
    "al-ittihad": (21.7634, 39.1642, 15, "natural"),
    "al ittihad": (21.7634, 39.1642, 15, "natural"),
    "al-qadsiah": (26.3106, 50.1930, 15, "natural"),
}


def _norm_est(txt):
    s = "".join(c for c in unicodedata.normalize("NFD", str(txt or "").lower()) if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s).strip()


def buscar_estadio_equipo(nombre_equipo):
    n = _norm_est(nombre_equipo)
    if not n:
        return None
    if n in ESTADIOS_DB:
        return ESTADIOS_DB[n]
    for clave in sorted(ESTADIOS_DB.keys(), key=len, reverse=True):
        if clave == "inter":
            if n in ("inter", "fc internazionale", "inter milan", "internazionale"):
                return ESTADIOS_DB[clave]
        elif clave == "america":
            if n in ("america", "club america", "cf america"):
                return ESTADIOS_DB[clave]
        elif clave in n:
            return ESTADIOS_DB[clave]
    return None


def _cargar_cache_clima():
    global _MEMORIA_CLIMA
    if _MEMORIA_CLIMA is not None:
        return _MEMORIA_CLIMA
    if os.path.exists(ARCHIVO_CACHE_CLIMA):
        try:
            with open(ARCHIVO_CACHE_CLIMA, "r", encoding="utf-8") as f:
                _MEMORIA_CLIMA = json.load(f) or {}
                return _MEMORIA_CLIMA
        except Exception:
            pass
    _MEMORIA_CLIMA = {}
    return _MEMORIA_CLIMA


def _guardar_cache_clima(cache_d):
    try:
        with open(ARCHIVO_CACHE_CLIMA, "w", encoding="utf-8") as f:
            json.dump(cache_d, f, ensure_ascii=False)
    except Exception:
        pass


def obtener_clima_hora_partido(lat, lon, fecha_str, hora_esp_str, permitir_red=True):
    """Consulta Open-Meteo (100% gratis, sin API key) para la hora exacta del partido (hora España)."""
    cache_c = _cargar_cache_clima()
    hora_hh = str(hora_esp_str or "20:00").strip()[:2]
    if not hora_hh.isdigit():
        hora_hh = "20"
    clave_c = f"{lat:.2f}_{lon:.2f}_{fecha_str}_{hora_hh}"
    if clave_c in cache_c:
        return cache_c[clave_c]
    if not permitir_red:
        return None

    try:
        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat:.4f}&longitude={lon:.4f}"
            "&hourly=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m"
            f"&timezone=Europe%2FMadrid&start_date={fecha_str}&end_date={fecha_str}"
        )
        r = requests.get(url, timeout=3.0)
        if r.status_code == 200:
            hr = r.json().get("hourly") or {}
            tiempos = hr.get("time") or []
            target = f"{fecha_str}T{int(hora_hh):02d}:00"
            idx_t = tiempos.index(target) if target in tiempos else (min(int(hora_hh), len(tiempos) - 1) if tiempos else -1)
            if idx_t >= 0:
                dato = {
                    "temp_c": round(float((hr.get("temperature_2m") or [18.0])[idx_t] or 18.0), 1),
                    "humedad": round(float((hr.get("relative_humidity_2m") or [55.0])[idx_t] or 55.0), 0),
                    "precip_mm": round(float((hr.get("precipitation") or [0.0])[idx_t] or 0.0), 2),
                    "viento_kmh": round(float((hr.get("wind_speed_10m") or [10.0])[idx_t] or 10.0), 1),
                }
                cache_c[clave_c] = dato
                _guardar_cache_clima(cache_c)
                return dato
    except Exception:
        pass
    return None


def calcular_ajustes_ambientales(local, visitante, fecha_str, hora_esp_str, permitir_red=True):
    """Calcula el vector de impacto físico real (altitud, césped, temperatura, humedad, lluvia, viento)
    diferenciado por métrica futbolística, con cotas de seguridad para evitar distorsiones extremas."""
    est_loc = buscar_estadio_equipo(local)
    est_vis = buscar_estadio_equipo(visitante)

    res = {
        "mult_local": 1.0,
        "mult_vis": 1.0,
        "mult_goles": 1.0,
        "mult_remates": 1.0,
        "mult_faltas": 1.0,
        "mult_corners": 1.0,
        "delta_phi_stats": 0.0,
        "delta_ritmo_1t": 0.0,
        "altitud_m": est_loc[2] if est_loc else 0,
        "cesped": est_loc[3] if est_loc else "natural",
        "clima": None,
        "etiqueta_ambiental": "☀️ Condiciones estándar",
    }
    if not est_loc:
        return res

    lat_l, lon_l, alt_l, cesp_l = est_loc
    alt_v = est_vis[2] if est_vis else 200
    cesp_v = est_vis[3] if est_vis else "natural"

    clima = obtener_clima_hora_partido(lat_l, lon_l, fecha_str, hora_esp_str, permitir_red=permitir_red)
    res["clima"] = clima
    tags = []

    # 1. Altitud real (> 2100 m) cuando el visitante NO es de altura (< 1800 m)
    if alt_l >= 2100 and alt_v < 1800:
        hipoxia = min(1.0, (alt_l - 1900.0) / 1700.0)
        res["mult_local"] *= (1.0 + 0.08 * hipoxia)
        res["mult_vis"] *= (1.0 - 0.10 * hipoxia)
        res["mult_corners"] *= (1.0 + 0.04 * hipoxia)
        res["delta_ritmo_1t"] -= (0.025 * hipoxia)  # Visitante se ahoga más en el 2do tiempo
        tags.append(f"🏔️ Altura {alt_l}m")

    # 2. Césped sintético cuando el visitante juega en natural
    if cesp_l == "sintetico" and cesp_v != "sintetico":
        res["mult_local"] *= 1.05
        res["mult_vis"] *= 0.93
        res["delta_phi_stats"] += 0.10
        tags.append("🏟️ Sintético")

    # 3. Factores meteorológicos en vivo a la hora del partido
    if clima:
        temp = float(clima.get("temp_c", 18.0))
        hum = float(clima.get("humedad", 55.0))
        lluvia = float(clima.get("precip_mm", 0.0))
        viento = float(clima.get("viento_kmh", 10.0))

        # Lluvia fuerte (afecta control, remates a puerta y sube faltas/varianza)
        if lluvia >= 4.5:
            res["mult_goles"] *= 0.91
            res["mult_remates"] *= 0.89
            res["mult_faltas"] *= 1.06
            res["delta_phi_stats"] += 0.20
            tags.append(f"🌧️ Lluvia {lluvia:.1f}mm")
        elif lluvia >= 1.8:
            res["mult_goles"] *= 0.95
            res["mult_remates"] *= 0.94
            res["mult_faltas"] *= 1.03
            res["delta_phi_stats"] += 0.10
            tags.append(f"🌦️ Lluvia {lluvia:.1f}mm")

        # Viento fuerte (distorsiona centros, pases largos y tiros)
        if viento >= 38.0:
            res["mult_goles"] *= 0.92
            res["mult_remates"] *= 0.91
            res["delta_phi_stats"] += 0.18
            tags.append(f"💨 Viento {viento:.0f}km/h")
        elif viento >= 26.0:
            res["mult_goles"] *= 0.96
            res["mult_remates"] *= 0.95
            res["delta_phi_stats"] += 0.10
            tags.append(f"💨 Viento {viento:.0f}km/h")

        # Frío extremo (especialmente en estadios nórdicos / invierno europeo)
        if temp <= 0.0:
            res["mult_vis"] *= 0.94
            res["mult_goles"] *= 0.96
            res["delta_phi_stats"] += 0.08
            tags.append(f"❄️ Frío {temp:.0f}°C")
        elif temp <= 3.0:
            res["mult_vis"] *= 0.97
            tags.append(f"🥶 {temp:.0f}°C")

        # Calor húmedo extremo (estrés térmico: Barranquilla, Montería, Yeda, Miami, Manaus)
        elif temp >= 29.0 and hum >= 70.0:
            res["mult_vis"] *= 0.94
            res["mult_goles"] *= 0.95
            res["mult_remates"] *= 0.94
            res["delta_ritmo_1t"] -= 0.03
            tags.append(f"🥵 {temp:.0f}°C ({hum:.0f}% hum)")

        if not tags:
            tags.append(f"☀️ {temp:.0f}°C")

    # Cotas físicas de seguridad (nunca distorsionar en exceso si coinciden múltiples factores)
    res["mult_local"] = round(max(0.94, min(1.12, res["mult_local"])), 4)
    res["mult_vis"] = round(max(0.84, min(1.04, res["mult_vis"])), 4)
    res["mult_goles"] = round(max(0.85, min(1.05, res["mult_goles"])), 4)
    res["mult_remates"] = round(max(0.84, min(1.05, res["mult_remates"])), 4)
    res["mult_faltas"] = round(max(0.94, min(1.10, res["mult_faltas"])), 4)
    res["mult_corners"] = round(max(0.92, min(1.08, res["mult_corners"])), 4)
    res["delta_phi_stats"] = round(min(0.35, res["delta_phi_stats"]), 3)
    res["etiqueta_ambiental"] = " | ".join(tags) if tags else "☀️ Condiciones estándar"
    return res
