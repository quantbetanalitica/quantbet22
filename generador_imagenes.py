from PIL import Image, ImageDraw, ImageFont
import math
import os
import re

# Memoria de rotación para garantizar variedad real de los 20 mercados a lo largo de la jornada
_MEMORIA_VARIEDAD_TARJETAS = {"FREE": [], "VIP": [], "DESCARTES": []}


FAMILIAS_FUTBOL_PURO = {"ganador", "goles", "goles_equipo", "btts", "tiempos", "combo"}
FAMILIAS_SECUNDARIAS = {"remates", "corners", "tarjetas", "faltas"}




def _acortar_nombre_club_limpio(nombre_club, max_len=16):
    """Acorta un nombre de club SIN cortar palabras a la mitad (nunca 'San Jose Earthq' ni 'Deportivo Ca')."""
    s = str(nombre_club or "").strip()
    if not s:
        return ""
    reemplazos_cortos = {
        "san jose earthquakes": "San Jose",
        "houston dynamo fc": "Houston Dynamo",
        "atletico bucaramanga": "Bucaramanga",
        "atlético bucaramanga": "Bucaramanga",
        "independiente santa fe": "Santa Fe",
        "independiente medellin": "Medellín",
        "independiente medellín": "Medellín",
        "atletico nacional": "Atl. Nacional",
        "atlético nacional": "Atl. Nacional",
        "america de cali": "América Cali",
        "américa de cali": "América Cali",
        "deportivo cali": "Dep. Cali",
        "deportes tolima": "Tolima",
        "manchester united": "Man. United",
        "manchester city": "Man. City",
        "paris saint germain": "PSG",
        "paris saint-germain": "PSG",
        "paris sg": "PSG",
        "atletico madrid": "Atl. Madrid",
        "atlético madrid": "Atl. Madrid",
        "atlético de madrid": "Atl. Madrid",
        "borussia dortmund": "Dortmund",
        "bayer leverkusen": "Leverkusen",
        "eintracht frankfurt": "Frankfurt",
        "bayern munich": "Bayern",
        "bayern münchen": "Bayern",
        "real sociedad": "R. Sociedad",
        "rayo vallecano": "Rayo Vallecano",
        "sporting cp": "Sporting",
        "inter miami cf": "Inter Miami",
    }
    low = s.lower()
    if low in reemplazos_cortos:
        return reemplazos_cortos[low]
    s_clean = re.sub(r"\s+(?:FC|CF|SC|CD|AC|AS|BC|KV|SV|SK)$", "", s, flags=re.I).strip()
    if len(s_clean) <= max_len:
        return s_clean
    palabras = s_clean.split()
    out = ""
    for pal in palabras:
        cand = f"{out} {pal}".strip()
        if len(cand) <= max_len:
            out = cand
        else:
            break
    return out if len(out) >= 3 else palabras[0][:max_len]


def _resolver_equipo_en_mercado(fragmento, local="", visitante=""):
    """Recupera el nombre limpio completo si un mercado trae el club truncado (ej. 'San Jose Earthq' o 'Deportivo Ca')."""
    frag = str(fragmento or "").strip()
    fl = frag.lower()
    for eq in (local, visitante):
        el = str(eq or "").strip()
        if not el:
            continue
        if fl and (el.lower().startswith(fl) or fl in el.lower() or (len(fl) >= 5 and fl[:5] in el.lower())):
            return _acortar_nombre_club_limpio(el, max_len=16)
    return _acortar_nombre_club_limpio(frag, max_len=16)


def formatear_mercado_claro_cliente(nombre_mercado, local="", visitante=""):
    """Traduce cualquier mercado interno del motor a español 100% claro para clientes
    (cero abreviaturas confusas como 'U4.5', 'O1.5', '(Under)' sin 'Goles' o clubes cortados).
    Devuelve (titulo_claro, subtitulo_explicativo)."""
    raw = str(nombre_mercado or "").strip()
    pref = ""
    m_pref = re.match(r"^(\[(?:VIP|FREE|PRO|VIP DOBLE|PRO SNIPER)\]\s*)", raw, flags=re.I)
    if m_pref:
        pref = m_pref.group(1)
        raw = raw[len(pref):].strip()

    low = raw.lower()
    loc_c = _acortar_nombre_club_limpio(local, max_len=16) or "Local"
    vis_c = _acortar_nombre_club_limpio(visitante, max_len=16) or "Visitante"

    # 1. Combos (1X / X2 + Over / Under goles)
    m_combo = re.match(r"^combo\s+(1x|x2)\s*\+\s*([ou])\s*(\d+(?:\.\d+)?)$", low)
    if m_combo:
        lado, ou, lin_s = m_combo.group(1).upper(), m_combo.group(2), m_combo.group(3)
        lin_f = float(lin_s)
        eq_lado = loc_c if lado == "1X" else vis_c
        if ou == "u":
            max_g = int(math.floor(lin_f))
            return f"{pref}{lado} + Menos de {lin_s} Goles", f"Gana o empata {eq_lado} y hay máx. {max_g} goles"
        min_g = int(math.floor(lin_f)) + 1
        return f"{pref}{lado} + Más de {lin_s} Goles", f"Gana o empata {eq_lado} y hay {min_g}+ goles"

    # 2. Total Menos de X.5 (Under) -> especificar SIEMPRE GOLES
    m_un = re.search(r"(?:total\s+)?menos\s+de\s+(\d+(?:\.\d+)?)", low)
    if m_un and not any(k in low for k in ("córner", "corner", "tarjeta", "falta", "remate")):
        lin_s = m_un.group(1)
        max_g = int(math.floor(float(lin_s)))
        return f"{pref}Menos de {lin_s} Goles Totales", f"Deben anotarse máximo {max_g} goles en el partido"

    # 3. Over X.5 Goles
    m_ov = re.match(r"^over\s+(\d+(?:\.\d+)?)\s+goles$", low)
    if m_ov:
        lin_s = m_ov.group(1)
        min_g = int(math.floor(float(lin_s))) + 1
        return f"{pref}Más de {lin_s} Goles Totales", f"Deben anotarse {min_g} o más goles en el partido"

    # 4. Total Asiático > 2.25 / 2.75 Goles
    m_asi = re.search(r"asi[áa]tico\s*>\s*(\d+(?:\.\d+)?)", low)
    if m_asi:
        lin_s = m_asi.group(1)
        if lin_s == "2.25":
            return f"{pref}Más de 2.25 Goles (Asiático)", "3+ goles gana • Con 2 goles devuelve mitad"
        if lin_s == "2.75":
            return f"{pref}Más de 2.75 Goles (Asiático)", "4+ goles gana • Con 3 goles gana mitad"
        return f"{pref}Más de {lin_s} Goles (Asiático)", "Línea asiática de goles totales del partido"

    # 5. Ambos Marcan (BTTS)
    if "btts" in low or "ambos marcan" in low:
        return f"{pref}Ambos Equipos Marcan (Sí)", "Tanto local como visitante anotan al menos 1 gol"

    # 6. Tiempos (1T / 2do Tiempo)
    if low == "gol en 1t":
        return f"{pref}Más de 0.5 Goles en 1er Tiempo", "Al menos 1 gol antes del descanso"
    if low.startswith("goles 1t >"):
        lin_s = raw.split(">")[1].strip()
        min_g = int(math.floor(float(lin_s))) + 1
        return f"{pref}Más de {lin_s} Goles en 1er Tiempo", f"{min_g} o más goles antes del descanso"
    if low == "gol en 2do tiempo":
        return f"{pref}Más de 0.5 Goles en 2do Tiempo", "Al menos 1 gol durante la segunda mitad"
    if "2do tiempo >" in low or "2t >" in low:
        lin_s = raw.split(">")[1].strip()
        min_g = int(math.floor(float(lin_s))) + 1
        return f"{pref}Más de {lin_s} Goles en 2do Tiempo", f"{min_g} o más goles en la segunda mitad"

    # 7. Doble Oportunidad 1X / X2
    if "doble oport" in low and "1x" in low:
        return f"{pref}Doble Oportunidad 1X ({loc_c})", f"Gana o empata {loc_c} en los 90 min"
    if "doble oport" in low and "x2" in low:
        return f"{pref}Doble Oportunidad X2 ({vis_c})", f"Gana o empata {vis_c} en los 90 min"

    # 8. Apuesta Sin Empate (DNB)
    if low.startswith("sin empate "):
        eq_c = _resolver_equipo_en_mercado(raw[11:], local, visitante)
        return f"{pref}Sin Empate: {eq_c}", f"Gana {eq_c} acierta • Si empatan se devuelve"

    # 9. Victoria directa
    if low.startswith("victoria "):
        eq_c = _resolver_equipo_en_mercado(raw[9:], local, visitante)
        return f"{pref}Victoria de {eq_c}", f"{eq_c} gana el partido en tiempo reglamentario"

    # 10. Goles por equipo (> 0.5 / > 1.5 / > 2.5)
    m_ge = re.match(r"^goles\s+(.+?)\s*>\s*(\d+(?:\.\d+)?)$", raw, flags=re.I)
    if m_ge:
        eq_c = _resolver_equipo_en_mercado(m_ge.group(1), local, visitante)
        lin_s = m_ge.group(2)
        min_g = int(math.floor(float(lin_s))) + 1
        sub_g = f"{eq_c} anota al menos 1 gol en el partido" if min_g == 1 else f"{eq_c} anota {min_g} o más goles en el partido"
        return f"{pref}Más de {lin_s} Goles: {eq_c}", sub_g

    # 11. Córners por equipo vs Córners totales
    m_ce = re.match(r"^c[óo]rners\s+(.+?)\s*>\s*(\d+(?:\.\d+)?)$", raw, flags=re.I)
    if m_ce:
        eq_c = _resolver_equipo_en_mercado(m_ce.group(1), local, visitante)
        lin_s = m_ce.group(2)
        min_c = int(math.floor(float(lin_s))) + 1
        return f"{pref}Más de {lin_s} Córners: {eq_c}", f"{eq_c} consigue {min_c} o más tiros de esquina"
    m_ct = re.match(r"^c[óo]rners\s*>\s*(\d+(?:\.\d+)?)$", raw, flags=re.I)
    if m_ct:
        lin_s = m_ct.group(1)
        min_c = int(math.floor(float(lin_s))) + 1
        return f"{pref}Más de {lin_s} Córners Totales", f"{min_c} o más tiros de esquina entre ambos equipos"

    # 12. Remates a Puerta
    m_rem = re.match(r"^remates\s+puerta\s*>\s*(\d+(?:\.\d+)?)$", raw, flags=re.I)
    if m_rem:
        lin_s = m_rem.group(1)
        min_r = int(math.floor(float(lin_s))) + 1
        return f"{pref}Más de {lin_s} Remates a Puerta", f"{min_r} o más tiros al arco entre ambos equipos"

    # 13. Faltas Totales
    m_fal = re.match(r"^faltas\s+totales\s*>\s*(\d+(?:\.\d+)?)$", raw, flags=re.I)
    if m_fal:
        lin_s = m_fal.group(1)
        min_f = int(math.floor(float(lin_s))) + 1
        return f"{pref}Más de {lin_s} Faltas Totales", f"{min_f} o más faltas pitadas en el partido"

    # 14. Tarjetas Totales
    m_tar = re.match(r"^tarjetas\s*>\s*(\d+(?:\.\d+)?)$", raw, flags=re.I)
    if m_tar:
        lin_s = m_tar.group(1)
        min_t = int(math.floor(float(lin_s))) + 1
        return f"{pref}Más de {lin_s} Tarjetas Totales", f"{min_t} o más tarjetas mostradas en el partido"

    return f"{pref}{raw}", "Proyección validada por el modelo matemático"


def obtener_familia(nombre_mercado):
    n = str(nombre_mercado).lower()
    if "remates" in n:
        return "remates"
    elif "córners" in n:
        return "corners"
    elif "faltas" in n:
        return "faltas"
    elif "tarjetas" in n:
        return "tarjetas"
    elif "combo" in n:
        return "combo"
    elif "oport" in n or "victoria" in n or "1x" in n or "x2" in n or "sin empate" in n or "dnb" in n:
        return "ganador"
    elif "btts" in n or "ambos marcan" in n:
        return "btts"
    elif "1t" in n or "2do tiempo" in n or "2t" in n:
        return "tiempos"
    elif n.startswith("goles ") and ">" in n:
        return "goles_equipo"
    elif "gol de " in n or "goleador" in n or "9 titular" in n:
        return "goleador"
    else:
        return "goles"


def es_visitante_protegido(nombre_visitante):
    import unicodedata
    v_norm = "".join(
        c for c in unicodedata.normalize("NFD", str(nombre_visitante).lower())
        if unicodedata.category(c) != "Mn"
    ).strip()

    import re as _re_fil
    if _re_fil.search(r"(?:^|\s)(?:ii|iii|b|c|castilla|atletic|jong|reserves|u23|u21)(?:$|\s)", v_norm):
        return False

    falsos_gigantes = [
        "internacional de bogota", "internacional fc", "internacional palmira",
        "boca juniors de cali", "atletico fc", "real santander", "real cundinamarca", "real cartagena"
    ]
    if any(fg in v_norm for fg in falsos_gigantes):
        return False

    gigantes_visitantes = [
        "real madrid", "barcelona", "manchester city", "arsenal", "liverpool",
        "bayern", "inter", "paris sg", "psg", "paris saint germain", "juventus",
        "atletico madrid", "ath madrid", "dortmund", "borussia dortmund", "milan", "ac milan",
        "leverkusen", "napoli", "sevilla", "valencia", "betis", "athletic", "real sociedad",
        "villarreal", "sporting", "benfica", "porto", "braga", "chelsea",
        "manchester united", "tottenham", "aston villa", "newcastle", "roma",
        "atalanta", "lazio", "fiorentina", "bologna", "leipzig", "stuttgart",
        "frankfurt", "hoffenheim", "freiburg", "monaco", "marseille", "lille",
        "lyon", "lyonnes", "nice", "lens", "psv", "ajax", "feyenoord", "az alkmaar",
        "club brugge", "anderlecht", "union sg", "gent", "genk", "galatasaray",
        "fenerbahce", "besiktas", "olympiacos", "paok", "panathinaikos", "aek",
        "rangers", "celtic", "slavia", "sparta praha", "plzen", "salzburg",
        "dinamo zagreb", "shakhtar", "palmeiras", "flamengo", "river plate",
        "boca juniors", "atletico mineiro", "sao paulo", "fluminense", "gremio",
        "botafogo", "corinthians", "racing", "independiente", "san lorenzo",
        "velez", "penarol", "nacional", "colo colo", "millonarios", "america de cali",
        "junior", "santa fe", "medellin", "tolima", "ldu quito", "independiente del valle",
        "cruzeiro", "vasco", "internacional", "olimpia", "cerro porteno", "libertad",
        "al-hilal", "al hilal", "al-nassr", "al nassr", "al-ahli", "al ahli", "al-ittihad", "al ittihad", "al-qadsiah", "al qadsiah",
        "leganes", "valladolid", "las palmas", "almeria", "granada", "espanyol", "elche", "levante",
        "espana", "spain", "argentina", "brasil", "brazil", "francia", "france",
        "inglaterra", "england", "alemania", "germany", "portugal", "italia", "italy",
        "paises bajos", "netherlands", "colombia", "uruguay", "belgica", "belgium", "croacia", "croatia"
    ]
    import re as _re_evp
    if "inter miami" in v_norm:
        return False
    for g in gigantes_visitantes:
        if g == "inter":
            if v_norm in ("inter", "inter milan", "internazionale", "fc internazionale"):
                return True
            continue
        if _re_evp.search(rf"(?<![a-z]){_re_evp.escape(g)}(?![a-z])", v_norm):
            return True
    return False


def _es_pick_dependiente_gol_global(nom_p):
    fm = obtener_familia(nom_p)
    if fm in {"goles", "tiempos", "btts", "goles_equipo"}:
        nl = str(nom_p).lower()
        return ("menos de" not in nl) and ("under" not in nl)
    if fm == "combo" and "o1.5" in str(nom_p).lower():
        return True
    return False


def seleccionar_par_distinto_familia(lista_candidatos, excluidos=None, familias_excluidas=None, tipo_filtro="FREE", registrar_memoria=True, tot_goles=2.5, max_picks_gol=None, **kwargs):
    if "actualizar_memoria" in kwargs:
        registrar_memoria = kwargs["actualizar_memoria"]
    if excluidos is None:
        excluidos = set()
    if familias_excluidas is None:
        familias_excluidas = set()

    historial_reciente = _MEMORIA_VARIEDAD_TARJETAS.get(tipo_filtro, [])[-5:]
    historial_fams = [obtener_familia(x) for x in historial_reciente]

    def _puntaje_rotacion(item):
        nom, prob, _ = item
        fam = obtener_familia(nom)
        # Rotación inteligente basada en efectividad real:
        # 1) Nunca sacrifica un pick muy superior (+10% prob) solo por rotar.
        # 2) Entre mercados de alta efectividad parecida, rota limpiamente para NO repetir los mismos 2-3 mercados siempre.
        penal_hist = 6.0 if nom in historial_reciente else 0.0
        if fam in FAMILIAS_SECUNDARIAS and historial_fams.count(fam) >= 1:
            penal_hist += 5.0 * historial_fams.count(fam)
        elif fam in FAMILIAS_FUTBOL_PURO:
            rep_rec = historial_fams[-4:].count(fam)
            if rep_rec >= 1:
                penal_hist += (4.8 if fam == "goles_equipo" else 3.6) * rep_rec

        if fam == "faltas":
            ajuste_tier = -4.0
        elif fam in {"corners", "tarjetas"}:
            ajuste_tier = -3.0
        elif fam == "remates":
            ajuste_tier = -1.5
        elif fam == "tiempos":
            ajuste_tier = 6.5 if nom == "Gol en 2do Tiempo" else 6.0
        elif fam in {"ganador", "combo", "btts", "goles"}:
            ajuste_tier = 6.0
        else:  # goles_equipo
            ajuste_tier = 4.5
        return float(prob) + ajuste_tier - penal_hist

    candidatos_rotados = sorted(lista_candidatos, key=_puntaje_rotacion, reverse=True)

    def _es_colineal(fam, fams_en_tarjeta, tot_g):
        if fam in fams_en_tarjeta:
            return True
        if (fam == "corners" and "tarjetas" in fams_en_tarjeta) or (fam == "tarjetas" and "corners" in fams_en_tarjeta):
            return True
        if (fam == "combo" and bool(fams_en_tarjeta & {"goles", "tiempos", "ganador", "goles_equipo"})) or (
            fam in {"goles", "tiempos", "ganador", "goles_equipo"} and "combo" in fams_en_tarjeta
        ):
            return True
        if (fam == "goles" and "tiempos" in fams_en_tarjeta) or (fam == "tiempos" and "goles" in fams_en_tarjeta):
            return True
        if float(tot_g or 2.5) < 3.15 and (
            (fam == "goles_equipo" and bool(fams_en_tarjeta & {"goles", "tiempos"}))
            or (fam in {"goles", "tiempos"} and "goles_equipo" in fams_en_tarjeta)
        ):
            return True
        if (fam == "btts" and "goles_equipo" in fams_en_tarjeta) or (fam == "goles_equipo" and "btts" in fams_en_tarjeta):
            return True
        if float(tot_g or 2.5) < 3.25 and (
            (fam == "btts" and bool(fams_en_tarjeta & {"goles", "tiempos"}))
            or (fam in {"goles", "tiempos"} and "btts" in fams_en_tarjeta)
        ):
            return True
        return False

    seleccion = []
    familias_usadas = set(familias_excluidas)

    # Primer pase ESTRICTO:
    #  - Respeta exclusión de mercados y familias de la otra tarjeta (FREE/VIP)
    #  - PROHÍBE 2 mercados secundarios (Córners/Faltas/Tarjetas/Remates) en la misma tarjeta
    for m in candidatos_rotados:
        if m[0] in excluidos:
            continue
        fam = obtener_familia(m[0])
        if fam in familias_usadas:
            continue
        if max_picks_gol is not None and _es_pick_dependiente_gol_global(m[0]):
            if sum(1 for x in seleccion if _es_pick_dependiente_gol_global(x[0])) >= max_picks_gol:
                continue
        fams_ya = {obtener_familia(x[0]) for x in seleccion}
        if _es_colineal(fam, fams_ya, tot_goles):
            continue
        if fam in FAMILIAS_SECUNDARIAS and any(f in FAMILIAS_SECUNDARIAS for f in fams_ya):
            continue
        if float(tot_goles or 2.5) < 2.95 and (
            (fam == "goles" and "tiempos" in familias_usadas) or (fam == "tiempos" and "goles" in familias_usadas)
        ):
            continue
        seleccion.append(m)
        familias_usadas.add(fam)
        if len(seleccion) == 2:
            break

    # Segundo pase: busca completar con 1 mercado de Fútbol Puro o 1 Secundario (nunca 2 de {faltas, corners, tarjetas})
    if len(seleccion) < 2:
        fams_internas = {obtener_familia(x[0]) for x in seleccion}
        for m in candidatos_rotados:
            if m[0] in excluidos or m in seleccion:
                continue
            fam = obtener_familia(m[0])
            if fam in fams_internas or fam in familias_excluidas:
                continue
            if max_picks_gol is not None and _es_pick_dependiente_gol_global(m[0]):
                if sum(1 for x in seleccion if _es_pick_dependiente_gol_global(x[0])) >= max_picks_gol:
                    continue
            if _es_colineal(fam, fams_internas, tot_goles):
                continue
            if fam in {"faltas", "corners", "tarjetas"} and any(f in {"faltas", "corners", "tarjetas"} for f in fams_internas):
                continue
            seleccion.append(m)
            fams_internas.add(fam)
            if len(seleccion) == 2:
                break

    # Tercer pase de emergencia: garantiza siempre 2 selecciones de distinta familia sin repetir entre FREE y VIP
    if len(seleccion) < 2:
        fams_internas = {obtener_familia(x[0]) for x in seleccion}
        for m in candidatos_rotados:
            if m in seleccion or m[0] in excluidos:
                continue
            fam = obtener_familia(m[0])
            if fam in fams_internas:
                continue
            if max_picks_gol is not None and _es_pick_dependiente_gol_global(m[0]):
                if sum(1 for x in seleccion if _es_pick_dependiente_gol_global(x[0])) >= max_picks_gol:
                    continue
            if fam in {"corners", "faltas", "tarjetas", "goles", "tiempos", "btts", "ganador", "goles_equipo"} and fam in familias_excluidas:
                continue
            if _es_colineal(fam, fams_internas, tot_goles):
                continue
            seleccion.append(m)
            fams_internas.add(fam)
            if len(seleccion) == 2:
                break

    if registrar_memoria:
        for s in seleccion:
            _MEMORIA_VARIEDAD_TARJETAS.setdefault(tipo_filtro, []).append(s[0])

    return seleccion


def cargar_lienzo_base():
    ancho, alto = 1080, 1080
    ruta_fondo = "fondo de quant bet.jpg"
    if os.path.exists(ruta_fondo):
        fondo_original = Image.open(ruta_fondo).convert("RGBA")
        w, h = fondo_original.size
        if w > h:
            nuevo_w = int(1080 * (w / h))
            fondo = fondo_original.resize((nuevo_w, 1080), Image.Resampling.LANCZOS)
            left = (nuevo_w - 1080) // 2
            fondo = fondo.crop((left, 0, left + 1080, 1080))
        else:
            nuevo_h = int(1080 * (h / w))
            fondo = fondo_original.resize((1080, nuevo_h), Image.Resampling.LANCZOS)
            top = (nuevo_h - 1080) // 2
            fondo = fondo.crop((0, top, 1080, top + 1080))
    else:
        fondo = Image.new("RGBA", (ancho, alto), (15, 15, 18, 255))
    capa_oscura = Image.new("RGBA", (ancho, alto), (10, 10, 12, 218))
    return Image.alpha_composite(fondo, capa_oscura)


def obtener_fuente_ajustada(draw, texto, archivo_ttf, tam_inicial, ancho_max_px, tam_min=18):
    tam = tam_inicial
    while tam >= tam_min:
        try:
            f = ImageFont.truetype(archivo_ttf, tam)
        except IOError:
            return ImageFont.load_default()
        bbox = draw.textbbox((0, 0), str(texto), font=f)
        if (bbox[2] - bbox[0]) <= ancho_max_px:
            return f
        tam -= 1
    try:
        return ImageFont.truetype(archivo_ttf, tam_min)
    except IOError:
        return ImageFont.load_default()


def cargar_fuentes_fijas():
    try:
        f_alerta = ImageFont.truetype("Montserrat-VariableFont_wght.ttf", 31)
        f_marca = ImageFont.truetype("Montserrat-VariableFont_wght.ttf", 45)
        f_datos = ImageFont.truetype("RobotoMono-VariableFont_wght.ttf", 27)
        f_datos_peq = ImageFont.truetype("RobotoMono-VariableFont_wght.ttf", 23)
        f_datos_bold = ImageFont.truetype("RobotoMono-VariableFont_wght.ttf", 31)
    except IOError:
        f_alerta = f_marca = f_datos = f_datos_peq = f_datos_bold = ImageFont.load_default()
    return f_alerta, f_marca, f_datos, f_datos_peq, f_datos_bold


def dibujar_icono_bandera(draw, x, y, color_bandera=(255, 65, 65, 255)):
    draw.line((x, y + 2, x, y + 30), fill=(235, 235, 235, 255), width=3)
    draw.polygon([(x + 2, y + 2), (x + 22, y + 9), (x + 2, y + 17)], fill=color_bandera)


def limpiar_emojis_fuente(texto):
    reemplazos = {
        "⚖️": "", "⚔️": "", "🔒": "", "🔥": "",
        "⚡": "", "🛡️": "", "⚠️": "", "🎯": "", "🚀": ""
    }
    t = str(texto)
    for k, v in reemplazos.items():
        t = t.replace(k, v)
    return t.strip()


def calcular_cuota_real_casa(prob, cuota_modelo=None, tipo_nivel="FREE", nombre_mercado="", cuotas_reales_casa=None):
    if isinstance(cuotas_reales_casa, dict) and nombre_mercado in cuotas_reales_casa:
        try:
            c_real = round(float(cuotas_reales_casa[nombre_mercado]), 2)
            if c_real >= 1.12:
                return c_real
        except Exception:
            pass
    if prob is None or prob <= 0:
        return 1.25
    cuota_justa = 100.0 / prob
    base = float(cuota_modelo) if (cuota_modelo and cuota_modelo > 1.05) else (cuota_justa * 0.96)
    if tipo_nivel == "FREE":
        return round(max(1.28, min(1.38, max(base, cuota_justa * 0.98))), 2)
    elif tipo_nivel == "VIP":
        n = str(nombre_mercado)
        if "Asiático > 2.25" in n or "BTTS" in n or "Ambos Marcan" in n or "Combo" in n or "Córners > 9.5" in n or "Remates Puerta > 8.5" in n or "Gol de " in n:
            piso_vip = 1.46
        elif "Remates Puerta > 7.5" in n or "Córners > 8.5" in n or "Goles " in n:
            piso_vip = 1.42
        elif "Remates Puerta > 6.5" in n or "Menos de 2.5" in n or "Faltas" in n:
            piso_vip = 1.40
        else:
            piso_vip = 1.38
        # Si el mercado tiene probabilidad >= 79% (cuota justa <= 1.26) y NO vino de Kambi, no inflar artificialmente a 1.38 para VIP
        if prob >= 79.0 and base < 1.30:
            return round(max(1.24, min(1.34, cuota_justa * 0.99)), 2)
        return round(max(piso_vip, min(1.62, max(base, cuota_justa * 1.01))), 2)
    return round(max(1.18, min(1.65, base)), 2)


def obtener_explicacion_apuesta_club(res_m):
    es_loc_fav = res_m.get("p_h", 50.0) >= res_m.get("p_a", 50.0)
    club = res_m["local"] if es_loc_fav else res_m["visitante"]
    tot_tiros = float(res_m.get("tot_tiros") or 6.8)
    return (
        f"DOMINIO TÁCTICO: {club} lidera volumen ({tot_tiros:.1f} remates al arco)",
        "Modelo Matemático: Simulación de 10.000 escenarios (Poisson + Dixon-Coles)"
    )

    if res_m.get("nombre_dom_goles") and res_m.get("p_dom_goles") and res_m["p_dom_goles"] >= 63.0:
        club = res_m["nombre_dom_goles"].replace("Goles ", "").replace(" > 1.5", "").strip()
        prob = res_m["p_dom_goles"]
        cuota = calcular_cuota_real_casa(prob, res_m.get("c_min_dom_goles"), "VIP", "Goles ")
        return (
            f"MÉTRICA POR CLUB: {club} proyecta 2+ Goles ({prob:.1f}%)",
            f"Tendencia Táctica: Goles de {club} -> Más de 1.5 | Índice > {cuota:.2f}"
        )

    if res_m.get("nombre_dom_corn") and res_m.get("p_dom_corn") and res_m["p_dom_corn"] >= 64.0:
        club = res_m["nombre_dom_corn"].replace("Córners ", "").replace(" > 4.5", "").strip()
        prob = res_m["p_dom_corn"]
        cuota = calcular_cuota_real_casa(prob, res_m.get("c_min_dom_corn"), "VIP", "Córners > 8.5")
        return (
            f"MÉTRICA POR CLUB: {club} proyecta 5+ Córners ({prob:.1f}%)",
            f"Tendencia Táctica: Córners de {club} -> Más de 4.5 | Índice > {cuota:.2f}"
        )

    es_loc_fav = res_m.get("p_h", 50.0) >= res_m.get("p_a", 50.0)
    club = res_m["local"] if es_loc_fav else res_m["visitante"]
    tot_tiros = float(res_m.get("tot_tiros") or 6.8)
    prob_rem = min(84.0, max(68.0, float(res_m.get("p_tiros65") or 72.5)))
    cuota_min = calcular_cuota_real_casa(prob_rem, None, "FREE", "Remates Puerta > 6.5")
    return (
        f"VOLUMEN OFENSIVO: {club} lidera proyección ({tot_tiros:.1f} tiros al arco)",
        f"Tendencia Táctica: Presión alta y volumen de finalización | Índice > {cuota_min:.2f}"
    )


def _prob_poisson_over(lmbda, linea):
    if lmbda is None or lmbda <= 0:
        return None, None
    p_under = sum(((math.e ** -lmbda) * (lmbda ** k)) / math.factorial(k) for k in range(int(linea) + 1))
    p_over = min(91.0, max(5.0, (1.0 - p_under) * 100.0))
    c_min = round(max(1.14, (100.0 / p_over) * 0.98), 2)
    return p_over, c_min


def _prob_negbin_over(mu, linea, phi=1.45):
    if mu is None or mu <= 0:
        return None, None
    if phi <= 1.02:
        return _prob_poisson_over(mu, linea)
    r = float(mu) / (float(phi) - 1.0)
    p = 1.0 / float(phi)
    q = 1.0 - p
    p_under = sum(math.exp(math.lgamma(k + r) - math.lgamma(k + 1) - math.lgamma(r) + r * math.log(p) + k * math.log(q)) for k in range(int(linea) + 1))
    p_over = round(min(91.0, max(5.0, (1.0 - p_under) * 100.0)), 1)
    c_min = round(max(1.14, (100.0 / p_over) * 0.98), 2)
    return p_over, c_min


def _fuente_card(preferencia, tam):
    if preferencia == "bold":
        cands = ["Montserrat-VariableFont_wght.ttf", "Montserrat-Bold.ttf", "/usr/share/fonts/truetype/lato/Lato-Black.ttf", "/usr/share/fonts/truetype/lato/Lato-Bold.ttf", "arialbd.ttf"]
    elif preferencia == "mono":
        cands = ["RobotoMono-VariableFont_wght.ttf", "Montserrat-VariableFont_wght.ttf", "/usr/share/fonts/truetype/lato/Lato-Bold.ttf", "consolab.ttf", "arialbd.ttf"]
    else:
        cands = ["Montserrat-VariableFont_wght.ttf", "/usr/share/fonts/truetype/lato/Lato-Regular.ttf", "arial.ttf"]
    for ruta in cands:
        if os.path.exists(ruta):
            try:
                f = ImageFont.truetype(ruta, tam)
                if preferencia in ("bold", "mono") and hasattr(f, "set_variation_by_axes"):
                    try:
                        f.set_variation_by_axes([800 if preferencia == "bold" else 700])
                    except Exception:
                        pass
                return f
            except Exception:
                continue
    return ImageFont.load_default()


def _fuente_card_ajustada(draw, texto, preferencia, tam_ini, ancho_max, tam_min=15):
    tam = tam_ini
    while tam >= tam_min:
        f = _fuente_card(preferencia, tam)
        bb = draw.textbbox((0, 0), str(texto), font=f)
        if (bb[2] - bb[0]) <= ancho_max:
            return f
        tam -= 2
    return _fuente_card(preferencia, tam_min)


def _cx_card(draw, texto, fuente, cx=540):
    bb = draw.textbbox((0, 0), str(texto), font=fuente)
    return int(cx - (bb[2] - bb[0]) / 2)


def _cargar_fondo_card_elegante(acento_izq=(0, 232, 118), acento_der=(255, 204, 0)):
    from PIL import ImageFilter
    base = cargar_lienzo_base()
    glow = Image.new("RGBA", (1080, 1080), (0, 0, 0, 0))
    dg = ImageDraw.Draw(glow, "RGBA")
    for r in range(360, 20, -28):
        a = int(16 * (1.0 - r / 380.0))
        dg.ellipse([(220 - r, 240 - r), (220 + r, 240 + r)], fill=(*acento_izq, a))
        dg.ellipse([(860 - r, 240 - r), (860 + r, 240 + r)], fill=(*acento_der, a))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=38))
    return Image.alpha_composite(base, glow)


def _obtener_escudo_card(nombre_eq, logo_url=None, tam=120):
    try:
        from generador_videos_redes import obtener_escudo_real_equipo
        return obtener_escudo_real_equipo(nombre_eq, logo_url=logo_url, tam=tam)
    except Exception:
        return None


def generar_captura_automatica(res_m, tipo_filtro="DESCARTES", guardar_imagen=True):

    contexto = limpiar_emojis_fuente(res_m.get('etiqueta_contexto', 'ESTÁNDAR'))
    es_derbi = res_m.get('es_derbi', False)
    is_america = res_m.get('is_america', False)
    liga_vis = str(res_m.get('liga_visual', '')).upper()
    tot_goles = float(res_m.get('tot_goles', 2.5) or 2.5)
    tot_corn = float(res_m.get('tot_corn') or 8.6)
    tot_tiros = float(res_m.get('tot_tiros') or 6.5)
    vis_protegido = es_visitante_protegido(res_m.get('visitante', ''))
    loc_protegido = es_visitante_protegido(res_m.get('local', ''))

    es_colombia_o_argentina = is_america and ("COLOMBIA" in liga_vis or "ARGENTINA" in liga_vis)
    es_cerrojo_estricto_latam = es_colombia_o_argentina and tot_goles <= 1.88

    # Solo ofrecer Córners > 9.5 si el partido proyecta >= 11.4 córners (colchón real, evita el fallo de Troyes 3-1)
    if tot_corn >= 11.4:
        p_c95, c_c95 = _prob_poisson_over(tot_corn * 0.96, 9.5)
        lineas_corners_dinamicas = [
            ("Córners > 8.5", res_m.get('p_c85'), res_m.get('c_min_c85')),
            ("Córners > 9.5", p_c95, c_c95),
        ]
    else:
        lineas_corners_dinamicas = [
            ("Córners > 7.5", res_m.get('p_c75'), res_m.get('c_min_c75')),
            ("Córners > 8.5", res_m.get('p_c85'), res_m.get('c_min_c85')),
        ]

    cuotas_bp_all = res_m.get("cuotas_bp") or {}
    over_remates_bp = cuotas_bp_all.get("over_remates") or {}
    over_1t_bp = cuotas_bp_all.get("over_goles_1t") or {}
    over_2t_bp = cuotas_bp_all.get("over_goles_2t") or {}
    linea_t_free = float(res_m.get("linea_tiros_free") or max(6.5, min(12.5, math.floor(tot_tiros - 1.8) + 0.5)))
    linea_t_vip = float(res_m.get("linea_tiros_vip") or max(7.5, min(13.5, math.floor(tot_tiros - 0.8) + 0.5)))
    p_tf_m = res_m.get("p_tiros_free")
    c_tf_m = res_m.get("c_min_tiros_free")
    if p_tf_m is None:
        p_tf_m, c_tf_m = _prob_poisson_over(tot_tiros, linea_t_free)
    p_tv_m = res_m.get("p_tiros_vip")
    c_tv_m = res_m.get("c_min_tiros_vip")
    if p_tv_m is None:
        p_tv_m, c_tv_m = _prob_poisson_over(tot_tiros, linea_t_vip)

    lineas_tiros_dinamicas = [(f"Remates Puerta > {linea_t_free:.1f}", p_tf_m, c_tf_m)]
    if abs(linea_t_vip - linea_t_free) >= 0.5:
        lineas_tiros_dinamicas.append((f"Remates Puerta > {linea_t_vip:.1f}", p_tv_m, c_tv_m))

    cuotas_reales_casa = res_m.get("cuotas_reales_casa") or {}
    over_goles_bp = ((res_m.get("cuotas_bp") or {}).get("over_goles") or {})
    tot_faltas_val = float(res_m.get("tot_faltas") or 22.5)
    linea_f_free = float(res_m.get("linea_faltas_free") or max(16.5, min(25.5, math.floor(tot_faltas_val - 2.3) + 0.5)))
    linea_f_vip = float(res_m.get("linea_faltas_vip") or max(18.5, min(27.5, math.floor(tot_faltas_val - 0.8) + 0.5)))
    p_f_free = res_m.get("p_faltas_free")
    c_f_free = res_m.get("c_min_faltas_free")
    if p_f_free is None:
        p_f_free, c_f_free = _prob_poisson_over(tot_faltas_val, linea_f_free)
    p_f_vip = res_m.get("p_faltas_vip")
    c_f_vip = res_m.get("c_min_faltas_vip")
    if p_f_vip is None:
        p_f_vip, c_f_vip = _prob_poisson_over(tot_faltas_val, linea_f_vip)

    p_25_m = res_m.get("p_25_match")
    c_25_m = res_m.get("c_min_25")
    if p_25_m is None:
        p_25_m, c_25_m = _prob_poisson_over(tot_goles, 2.5)
    p_35_m = res_m.get("p_35_match")
    c_35_m = res_m.get("c_min_35")
    if p_35_m is None:
        p_35_m, c_35_m = _prob_poisson_over(tot_goles, 3.5)
    p_45_m = res_m.get("p_45_match")
    c_45_m = res_m.get("c_min_45")
    if p_45_m is None:
        p_45_m, c_45_m = _prob_poisson_over(tot_goles, 4.5)

    lineas_faltas_dinamicas = [(f"Faltas Totales > {linea_f_free:.1f}", p_f_free, c_f_free)]
    if abs(linea_f_vip - linea_f_free) >= 0.5:
        lineas_faltas_dinamicas.append((f"Faltas Totales > {linea_f_vip:.1f}", p_f_vip, c_f_vip))

    # LOS 20+ MERCADOS MATEMÁTICOS COMPLETOS CALIBRADOS A LAS LÍNEAS REALES DE LA CASA
    mercados_brutos = [
        ("Over 1.5 Goles", res_m.get('p_15_match'), res_m.get('c_min_15')),
        ("Over 2.5 Goles", p_25_m, c_25_m),
        ("Over 3.5 Goles", p_35_m, c_35_m),
        ("Over 4.5 Goles", p_45_m, c_45_m),
        ("Over 5.5 Goles", *_prob_poisson_over(tot_goles, 5.5)),
        ("Gol en 1T", res_m.get('p_05_ht'), res_m.get('c_min_05_ht')),
        ("Goles 1T > 1.5", res_m.get('p_15_ht'), res_m.get('c_min_15_ht')),
        ("Gol en 2do Tiempo", res_m.get('p_05_2t'), res_m.get('c_min_05_2t')),
        ("Goles 2do Tiempo > 1.5", res_m.get('p_15_2t'), res_m.get('c_min_15_2t')),
        ("Ambos Marcan (BTTS)", res_m.get('p_btts'), res_m.get('c_min_btts')),
        ("Total Asiático > 2.25", res_m.get('p_asig225'), res_m.get('c_min_asig225')),
        ("Total Asiático > 2.75", res_m.get('p_asig275'), res_m.get('c_min_asig275')),
        *lineas_faltas_dinamicas,
        ("Doble Oport. 1X", res_m.get('p_1x'), res_m.get('c_min_1x')),
        ("Doble Oport. X2", res_m.get('p_x2'), res_m.get('c_min_x2')),
        ("Combo 1X + O1.5", res_m.get('p_combo_1x_over15'), res_m.get('c_min_combo_1x')),
        ("Combo X2 + O1.5", res_m.get('p_combo_x2_over15'), res_m.get('c_min_combo_x2')),
        ("Combo 1X + U3.5", res_m.get('p_combo_1x_u35'), res_m.get('c_min_combo_1x_u35')),
        ("Combo 1X + U4.5", res_m.get('p_combo_1x_u45'), res_m.get('c_min_combo_1x_u45')),
        ("Combo X2 + U3.5", res_m.get('p_combo_x2_u35'), res_m.get('c_min_combo_x2_u35')),
        (f"Sin Empate {res_m['local'][:12]}", res_m.get('p_dnb_local'), res_m.get('c_min_dnb_local')),
        (f"Sin Empate {res_m['visitante'][:12]}", res_m.get('p_dnb_visita'), res_m.get('c_min_dnb_visita')),
        (f"Goles {res_m['local'][:12]} > 0.5", res_m.get('p_loc_o05'), res_m.get('c_min_loc_o05')),
        (f"Goles {res_m['visitante'][:12]} > 0.5", res_m.get('p_vis_o05'), res_m.get('c_min_vis_o05')),
        (f"Goles {res_m['local'][:12]} > 1.5", res_m.get('p_loc_o15'), res_m.get('c_min_loc_o15')),
        (f"Goles {res_m['visitante'][:12]} > 1.5", res_m.get('p_vis_o15'), res_m.get('c_min_vis_o15')),
        ("Total Menos de 2.5 (Under)", res_m.get('p_under25'), res_m.get('c_min_under25')),
        ("Total Menos de 3.5 (Under)", res_m.get('p_under35'), res_m.get('c_min_under35')),
        *lineas_tiros_dinamicas,
        *lineas_corners_dinamicas,
        (f"Tarjetas > {res_m.get('linea_tarj', 3.5)}", res_m.get('p_t35'), res_m.get('c_min_t35')),
        *( [("Tarjetas > 3.5", *_prob_negbin_over(float(res_m.get('tot_tarj') or 4.5) * 0.92, 3.5, phi=1.35))] if float(res_m.get('linea_tarj', 3.5)) >= 4.5 else [] ),
    ]

    if (res_m.get("p_h") or 0) >= 54.0:
        mercados_brutos.append((f"Victoria {res_m['local'][:12]}", res_m.get("p_h"), res_m.get("cuota_h")))
    if (res_m.get("p_a") or 0) >= 54.0:
        mercados_brutos.append((f"Victoria {res_m['visitante'][:12]}", res_m.get("p_a"), res_m.get("cuota_a")))
    if res_m.get("nombre_dom_goles") and res_m["nombre_dom_goles"] not in {x[0] for x in mercados_brutos} and ((res_m.get("p_dom_goles") or 0) >= 60.0 or (res_m["nombre_dom_goles"] in cuotas_reales_casa and (res_m.get("p_dom_goles") or 0) >= 52.0)):
        mercados_brutos.append((res_m["nombre_dom_goles"], res_m.get("p_dom_goles"), res_m.get("c_min_dom_goles")))
    if res_m.get("nombre_dom_corn") and (res_m.get("p_dom_corn") or 0) >= 64.0:
        mercados_brutos.append((res_m["nombre_dom_corn"], res_m.get("p_dom_corn"), res_m.get("c_min_dom_corn")))
    # Inyectar TODAS las líneas reales abiertas en Kambi/BetPlay (Córners, Córners Equipo, Faltas, Remates, Tarjetas)
    # para que el candado estricto de mercado abierto siempre pueda operar sobre lo que la casa realmente ofrece
    nombres_ya_mb = {x[0] for x in mercados_brutos}
    base_c_l_gi = float(res_m.get("base_corn_l") or (tot_corn * 0.52))
    base_c_v_gi = float(res_m.get("base_corn_v") or (tot_corn * 0.48))
    tot_tarj_gi = float(res_m.get("tot_tarj") or 3.8)
    for nom_k, odd_k in cuotas_reales_casa.items():
        if nom_k in nombres_ya_mb:
            continue
        try:
            odd_kf = float(odd_k)
            if odd_kf < 1.12 or odd_kf > 2.25:
                continue
            if nom_k.startswith("Córners > "):
                lin_k = float(nom_k.split(">")[1].strip())
                pk, _ = _prob_negbin_over(tot_corn, lin_k, phi=1.52)
                if pk:
                    mercados_brutos.append((nom_k, pk, odd_kf))
                    nombres_ya_mb.add(nom_k)
            elif nom_k.startswith("Córners ") and " > " in nom_k:
                lin_k = float(nom_k.split(">")[1].strip())
                es_loc_ck = res_m["local"][:8].lower() in nom_k.lower()
                pk, _ = _prob_negbin_over(base_c_l_gi if es_loc_ck else base_c_v_gi, lin_k, phi=1.42)
                if pk:
                    mercados_brutos.append((nom_k, pk, odd_kf))
                    nombres_ya_mb.add(nom_k)
            elif nom_k.startswith("Faltas Totales > "):
                lin_k = float(nom_k.split(">")[1].strip())
                pk, _ = _prob_negbin_over(tot_faltas_val, lin_k, phi=1.85)
                if pk:
                    mercados_brutos.append((nom_k, pk, odd_kf))
                    nombres_ya_mb.add(nom_k)
            elif nom_k.startswith("Remates Puerta > "):
                lin_k = float(nom_k.split(">")[1].strip())
                pk, _ = _prob_negbin_over(tot_tiros, lin_k, phi=1.38)
                if pk:
                    mercados_brutos.append((nom_k, pk, odd_kf))
                    nombres_ya_mb.add(nom_k)
            elif nom_k.startswith("Tarjetas > "):
                lin_k = float(nom_k.split(">")[1].strip())
                pk, _ = _prob_negbin_over(tot_tarj_gi, lin_k, phi=1.35)
                if pk:
                    mercados_brutos.append((nom_k, pk, odd_kf))
                    nombres_ya_mb.add(nom_k)
        except Exception:
            continue

    # CASCADA REAL DE MERCADOS (v26.6 — NUNCA descartar a ciegas porque Kambi aún no haya abierto una estadística):
    # Si Kambi abrió cuota real del mercado, se calibra con ella (50/50); si no, opera el cálculo histórico 12-20 partidos del modelo.
    fuente_bp_gi = str(cuotas_bp_all.get("fuente") or "").lower()
    candado_mercado_real_kambi = False  # Kambi calibra cuando existe; ya NO bloquea mercados válidos del modelo histórico

    mercados_ritmo = []
    mercados_ganador_respaldo = []

    for nombre, prob, cuota_orig in mercados_brutos:
        if prob is None or cuota_orig is None:
            continue
        en_kambi_exacto = nombre in cuotas_reales_casa
        # Si la casa de apuestas (BetPlay/Kambi) tiene cuota real abierta para este mercado exacto,
        # calibrar la probabilidad combinando nuestro modelo con la probabilidad implícita sin margen de la casa
        if en_kambi_exacto:
            try:
                odd_k_real = float(cuotas_reales_casa[nombre])
                if odd_k_real > 1.05:
                    p_impl_casa = min(92.0, (94.0 / odd_k_real))
                    prob = round((float(prob) * 0.50) + (p_impl_casa * 0.50), 1)
                    cuota_orig = odd_k_real
            except Exception:
                pass
        # Si es estadística (Córners/Faltas/Remates/Tarjetas) sin cuota Kambi aún abierta, exigir convicción sólida >= 60%
        if (not en_kambi_exacto) and obtener_familia(nombre) in FAMILIAS_SECUNDARIAS and float(prob) < 60.0:
            continue
        if prob < 58.0:
            continue



        es_fem_gi = ("WOMEN" in liga_vis) or ("FEMEN" in liga_vis)
        over_corners_bp = cuotas_bp_all.get("over_corners") or {}
        over_faltas_bp = cuotas_bp_all.get("over_faltas") or {}
        over_tarj_bp = cuotas_bp_all.get("over_tarjetas") or {}
        if "AMISTOSO" in liga_vis and ("Tarjetas" in nombre or "Faltas" in nombre):
            continue
        if es_fem_gi:
            # Fútbol femenino (UWCL): muchas menos faltas/tarjetas y menos córners por gol que en masculino.
            # Bloquear Faltas y Tarjetas salvo que la casa (Kambi) abra línea real operable.
            if "Faltas" in nombre and nombre not in cuotas_reales_casa:
                continue
            if "Tarjetas" in nombre and nombre not in cuotas_reales_casa:
                continue
            if "Córners" in nombre:
                if over_corners_bp:
                    if nombre.startswith("Córners > ") and nombre not in cuotas_reales_casa:
                        continue
                elif tot_corn < 8.6 and ("> 8.5" in nombre or "> 9.5" in nombre):
                    continue
                elif "> 7.5" in nombre and tot_corn < 7.8:
                    continue

        if es_cerrojo_estricto_latam:
            if nombre in ["Total Asiático > 2.25", "Total Asiático > 2.75", "Ambos Marcan (BTTS)", "Gol en 1T"]:
                continue

        diferencia_favorito = abs(float(res_m.get("p_h", 50.0)) - float(res_m.get("p_a", 50.0)))
        hay_favorito_claro = (
            (diferencia_favorito >= 16.0)
            or (max(float(res_m.get("p_h", 0)), float(res_m.get("p_a", 0))) >= 55.0)
            or (vis_protegido != loc_protegido)
        )
        es_liga_cerrada = ("SEGUNDA" in liga_vis) or ("ARGENTINA" in liga_vis)

        # 1. Prohibido recomendar Menos de (Under) en Selecciones (incluyendo Nations League), Copas o con favorito claro (evita Suiza vs Escocia 4-0)
        es_torneo_selecciones = any(k in liga_vis for k in ["INTERNACIONAL", "ELIMINATORIAS", "NATIONS", "EURO", "MUNDIAL", "COPA AMÉRICA"])
        if "Menos de" in nombre:
            if res_m.get("es_copa") or es_torneo_selecciones:
                continue
            if "2.5" in nombre:
                tope_u25 = 2.42 if (is_america or es_liga_cerrada) else 2.36
                if tot_goles >= tope_u25 or (hay_favorito_claro and tot_goles >= 2.22) or prob < 56.5:
                    continue
            elif "3.5" in nombre:
                if tot_goles >= 2.52 or (hay_favorito_claro and tot_goles >= 2.35) or prob < 69.0:
                    continue

        # 2. Ambos Marcan (BTTS) calibrado por matemáticas reales (Poisson + Kambi):
        #    Permitido en VIP si ambos equipos tienen gol (prob >= 57.5% y tot_goles >= 2.45), aunque exista favorito (ej. Nice vs PSG 2-3, Newcastle vs Arsenal 2-2)
        if nombre == "Ambos Marcan (BTTS)":
            ataque_min_btts = float(res_m.get("ataque_debil") or 0.95)
            if tot_goles < 2.50 or prob < 58.0 or ataque_min_btts < 0.92:
                continue

        # 3. Regla #3: Filtro Dixon-Coles exacto para Over 1.5 (si P(0-0)+P(1-0)+P(0-1) >= 27%, no priorizar Over 1.5)
        alta_friccion_cerrada = float(res_m.get("tot_faltas") or 22.0) >= 23.0 and abs(float(res_m.get("p_h", 50.0)) - float(res_m.get("p_a", 50.0))) < 18.0
        es_clasico_cerrado = es_derbi or (is_america and loc_protegido and vis_protegido)
        umbral_goles_o15 = 2.72 if es_clasico_cerrado else (2.56 if (es_liga_cerrada or alta_friccion_cerrada or (not loc_protegido and not vis_protegido)) else 2.40)
        riesgo_corto_dc = float(res_m.get("prob_marcador_corto") or 0.0)
        # Calibración con líneas reales abiertas en casa de apuestas (ej. Barcelona: si casa abre desde 3.5, escalar a 3.5)
        if nombre in ("Over 1.5 Goles", "Over 2.5 Goles", "Over 3.5 Goles", "Over 4.5 Goles", "Over 5.5 Goles"):
            lin_g_num = float(nombre.split()[1])
            if over_goles_bp and (candado_mercado_real_kambi or lin_g_num in over_goles_bp or str(lin_g_num) in over_goles_bp):
                odd_real_g = over_goles_bp.get(lin_g_num)
                if odd_real_g is None:
                    odd_real_g = over_goles_bp.get(str(lin_g_num))
                if odd_real_g is None:
                    continue
                odd_real_g = float(odd_real_g)
                if tipo_filtro == "VIP" and (odd_real_g < 1.30 or odd_real_g > 2.15):
                    continue
                if tipo_filtro == "FREE" and (odd_real_g < 1.14 or odd_real_g > 1.50):
                    continue
            else:
                if nombre == "Over 1.5 Goles":
                    if tot_goles < umbral_goles_o15 or prob < 71.0 or riesgo_corto_dc >= 27.0:
                        continue
                    if tot_goles >= 3.20 or (tipo_filtro == "VIP" and tot_goles >= 2.95):
                        continue
                elif nombre == "Over 2.5 Goles":
                    if tot_goles < 2.70 or prob < 56.5:
                        continue
                    if tipo_filtro == "FREE" and tot_goles < 3.25:
                        continue
                elif nombre == "Over 3.5 Goles":
                    if tot_goles < 3.80 or prob < 58.0:
                        continue
                elif nombre == "Over 4.5 Goles":
                    if tot_goles < 4.70 or prob < 57.0:
                        continue
                elif nombre == "Over 5.5 Goles":
                    if tot_goles < 5.65 or prob < 57.0:
                        continue
            if nombre == "Over 1.5 Goles" and (tot_goles < umbral_goles_o15 or prob < 71.0 or riesgo_corto_dc >= 27.0):
                continue

        # Gate de Remates a Puerta contra deslizador real Opta/Kambi (nunca ofrecer 6.5 si la casa empieza en 9.5!)
        if nombre.startswith("Remates Puerta > ") and over_remates_bp:
            try:
                lin_r_num = float(nombre.split(">")[1].strip())
                odd_r_real = over_remates_bp.get(lin_r_num) or over_remates_bp.get(str(lin_r_num))
                if odd_r_real is None:
                    continue
                odd_r_real = float(odd_r_real)
                if tipo_filtro == "VIP" and (odd_r_real < 1.30 or odd_r_real > 2.15):
                    continue
                if tipo_filtro == "FREE" and (odd_r_real < 1.14 or odd_r_real > 1.55):
                    continue
            except Exception:
                pass

        # Gate de Guion de Partido (Match Script) para Córners y Faltas:
        # 1) Sin Kambi abierto, exigir colchón real para Córners (>7.5 requiere >=8.4; >8.5 requiere >=9.6 y partido NO cerrado)
        if nombre == "Córners > 7.5" and not over_corners_bp and tot_corn < 8.40:
            continue
        if nombre == "Córners > 8.5" and not over_corners_bp and (tot_corn < 9.60 or tot_goles < 2.28):
            continue
        # 2) En partidos abiertos (tot_goles >= 2.65) prohibir Faltas altas (>= 23.5 sin Kambi) porque hay menos interrupciones
        if nombre.startswith("Faltas Totales > "):
            try:
                lin_f_chk = float(nombre.split(">")[1].strip())
                if nombre not in cuotas_reales_casa:
                    if lin_f_chk >= 23.5 and (tot_goles >= 2.60 or (tot_faltas_val - lin_f_chk) < 2.8):
                        continue
                    if lin_f_chk >= 22.5 and (tot_faltas_val - lin_f_chk) < 2.2:
                        continue
            except Exception:
                pass
        if nombre.startswith("Remates Puerta > ") and not over_remates_bp:
            try:
                lin_r_chk = float(nombre.split(">")[1].strip())
                if lin_r_chk >= 7.5 and tot_tiros < 9.3:
                    continue
            except Exception:
                pass

        if nombre == "Total Asiático > 2.25":
            if tot_goles < 2.72 or tot_goles >= 3.65 or prob < 58.0:
                continue
            if over_goles_bp and ((2.5 not in over_goles_bp and "2.5" not in over_goles_bp) or float(over_goles_bp.get(2.5) or over_goles_bp.get("2.5") or 9.0) > 1.85):
                continue
        if nombre == "Total Asiático > 2.75":
            if tot_goles < 3.10 or tot_goles >= 4.20 or prob < 60.0:
                continue
            if over_goles_bp and ((2.5 not in over_goles_bp and "2.5" not in over_goles_bp) or float(over_goles_bp.get(2.5) or over_goles_bp.get("2.5") or 9.0) > 1.65):
                continue

        # Gate calibrado de mercados de 45 min (Gol 1T / Gol 2T):
        # Recupera la presencia real de Gol en 1T y Gol en 2T en partidos con ritmo (>= 2.55 goles y riesgo 0-0/1-0 < 27%),
        # separando por cuota real: < 1.35 va a FREE y >= 1.35 va a VIP.
        asim_atq_gi = float(res_m.get("asimetria_ataque") or 0.0)
        if nombre == "Gol en 1T":
            if tot_goles < 2.55 or riesgo_corto_dc >= 26.5 or prob < 69.0:
                continue
            if over_1t_bp:
                odd_1t05 = over_1t_bp.get(0.5) or over_1t_bp.get("0.5")
                if odd_1t05 is None:
                    continue
                odd_1t_f = float(odd_1t05)
                if tipo_filtro == "VIP" and (odd_1t_f < 1.34 or odd_1t_f > 1.85):
                    continue
                if tipo_filtro == "FREE" and (odd_1t_f < 1.16 or odd_1t_f > 1.42):
                    continue
            elif tipo_filtro == "VIP" and tot_goles >= 3.15:
                continue
        if nombre == "Goles 1T > 1.5":
            if over_1t_bp:
                odd_1t15 = over_1t_bp.get(1.5) or over_1t_bp.get("1.5")
                if odd_1t15 is None or float(odd_1t15) < 1.35 or float(odd_1t15) > 2.15:
                    continue
            elif tot_goles < 3.45 or prob < 58.0:
                continue
        if nombre == "Gol en 2do Tiempo":
            if tot_goles < 2.50 or riesgo_corto_dc >= 27.0 or prob < 71.0:
                continue
            if asim_atq_gi >= 0.90:
                # Favorito abrumador puede sentenciar en 1T y dormir el 2T
                continue
            if over_2t_bp:
                odd_2t05 = over_2t_bp.get(0.5) or over_2t_bp.get("0.5")
                if odd_2t05 is None:
                    continue
                odd_2t_f = float(odd_2t05)
                if tipo_filtro == "VIP" and (odd_2t_f < 1.34 or odd_2t_f > 1.80):
                    continue
                if tipo_filtro == "FREE" and (odd_2t_f < 1.14 or odd_2t_f > 1.38):
                    continue
            elif tipo_filtro == "VIP" and tot_goles >= 3.10:
                continue
        if nombre == "Goles 2do Tiempo > 1.5":
            if asim_atq_gi >= 0.85:
                continue
            if over_2t_bp:
                odd_2t15 = over_2t_bp.get(1.5) or over_2t_bp.get("1.5")
                if odd_2t15 is None or float(odd_2t15) < 1.32 or float(odd_2t15) > 2.05:
                    continue
            elif tot_goles < 3.65 or prob < 62.0:
                continue

        # 3B. Gate profesional para Goles por Equipo (> 0.5 y > 1.5): mercado clave de fútbol puro
        if obtener_familia(nombre) == "goles_equipo":
            es_ge_loc = res_m["local"][:8].lower() in nombre.lower()
            lam_ge = float(res_m.get("l_local_mat" if es_ge_loc else "l_vis_mat") or (tot_goles * 0.5))
            if "> 0.5" in nombre:
                if lam_ge < 1.18 or prob < 68.0:
                    continue
                if tipo_filtro == "VIP" and (cuota_orig < 1.34 or cuota_orig > 1.80):
                    continue
                if tipo_filtro == "FREE" and (cuota_orig < 1.16 or cuota_orig > 1.42):
                    continue
            elif "> 1.5" in nombre:
                if lam_ge < 1.65 or prob < 56.0:
                    continue
                if tipo_filtro == "VIP" and (cuota_orig < 1.35 or cuota_orig > 2.05):
                    continue
                if tipo_filtro == "FREE" and (cuota_orig < 1.16 or cuota_orig > 1.44):
                    continue

        # 4. Regla #4 + CANDADO CALIBRADO CONTRA CUOTAS REALES EN 1X2 / SIN EMPATE (DNB) / DOBLE OPORT. / COMBOS
        if "Doble Oport." in nombre or "Combo " in nombre or "Victoria " in nombre or "Sin Empate " in nombre:
            c1_bp = cuotas_bp_all.get("1") if isinstance(cuotas_bp_all.get("1"), (int, float)) else None
            c2_bp = cuotas_bp_all.get("2") if isinstance(cuotas_bp_all.get("2"), (int, float)) else None
            c1x_bp = cuotas_bp_all.get("1X") if isinstance(cuotas_bp_all.get("1X"), (int, float)) else None
            cx2_bp = cuotas_bp_all.get("X2") if isinstance(cuotas_bp_all.get("X2"), (int, float)) else None
            entropia_p = float(res_m.get("entropia_1x2") or 0.0)
            entropia_lim = float(res_m.get("entropia_max_ganador") or 0.94)

            es_copa_domestica = bool(res_m.get("es_copa")) and not any(
                k_int in liga_vis for k_int in ("CHAMPIONS", "EUROPA LEAGUE", "CONFERENCE", "LIBERTADORES", "SUDAMERICANA", "MUNDIAL", "EUROCOPA", "AMÉRICA", "NATIONS")
            )
            if es_copa_domestica and (
                "X2" in nombre
                or ((nombre.startswith("Victoria ") or nombre.startswith("Sin Empate ")) and res_m["visitante"][:8].lower() in nombre.lower())
            ):
                continue

            min_c_casa = min([c for c in (c1_bp, c2_bp) if c is not None], default=2.20)
            if es_derbi and min_c_casa > 1.72:
                continue

            if nombre.startswith("Sin Empate "):
                es_dnb_loc = res_m["local"][:8].lower() in nombre.lower()
                c_fav_dnb = c1_bp if es_dnb_loc else c2_bp
                c_riv_dnb = c2_bp if es_dnb_loc else c1_bp
                if c_fav_dnb is not None:
                    if c_fav_dnb < 1.48 or c_fav_dnb > 2.15 or (c_riv_dnb is not None and c_riv_dnb < 3.20):
                        continue
                else:
                    if (es_dnb_loc and float(res_m.get("p_h", 0)) < 50.0) or ((not es_dnb_loc) and float(res_m.get("p_a", 0)) < 50.0):
                        continue
                if (not es_dnb_loc) and (loc_protegido or res_m.get("es_plaza_hostil_local") or (is_america and (c_fav_dnb is None or c_fav_dnb > 1.85))):
                    continue
                if es_liga_cerrada and (c_fav_dnb is None or c_fav_dnb > 1.85):
                    continue
                if prob < 65.0:
                    continue
                mercados_ganador_respaldo.append((nombre, prob, cuota_orig))
                continue

            if "Doble Oport. 1X" == nombre:
                if tipo_filtro == "VIP" and res_m.get("calidad_datos") != "ALTA" and (c1_bp is None or c1_bp > 1.85):
                    continue
                if (c1x_bp is not None and (c1x_bp < 1.14 or c1x_bp > (1.62 if tipo_filtro == "VIP" else 1.40))):
                    continue
                if (c1_bp is not None and (c1_bp < 1.32 or c1_bp > 2.25)) or (c2_bp is not None and c2_bp <= 3.00):
                    continue
                if float(res_m.get("p_h", 0)) >= 68.0 or float(res_m.get("p_a", 0)) >= 32.0:
                    continue
                if vis_protegido and not loc_protegido and (c1_bp is None or c1_bp > 1.85):
                    continue
                if prob < 69.0:
                    continue
                mercados_ganador_respaldo.append((nombre, prob, cuota_orig))
                continue

            if "Doble Oport. X2" == nombre:
                if (cx2_bp is not None and (cx2_bp < 1.14 or cx2_bp > (1.62 if tipo_filtro == "VIP" else 1.40))):
                    continue
                if (c2_bp is not None and (c2_bp < 1.32 or c2_bp > 2.15)) or (c1_bp is not None and c1_bp <= 3.10):
                    continue
                if (is_america or "ARABIA" in liga_vis) and (c2_bp is None or c2_bp > 1.75):
                    continue
                if float(res_m.get("p_a", 0)) >= 68.0 or float(res_m.get("p_h", 0)) >= 26.0 or res_m.get("es_plaza_hostil_local"):
                    continue
                if loc_protegido and (c2_bp is None or c2_bp > 1.75):
                    continue
                if prob < 71.0:
                    continue
                mercados_ganador_respaldo.append((nombre, prob, cuota_orig))
                continue

            if nombre.startswith("Victoria "):
                es_v_loc = res_m["local"][:8].lower() in nombre.lower()
                c_vic = c1_bp if es_v_loc else c2_bp
                if entropia_p >= entropia_lim:
                    continue
                if es_liga_cerrada and (c_vic is None or c_vic > 1.55):
                    continue
                if c_vic is not None:
                    if tipo_filtro == "FREE" and (c_vic < 1.20 or c_vic > 1.42):
                        continue
                    if tipo_filtro == "VIP" and (c_vic < 1.38 or c_vic > 1.62):
                        continue
                    if prob < 62.0:
                        continue
                else:
                    if es_v_loc and (vis_protegido or float(res_m.get("p_h", 0)) < 68.0):
                        continue
                    if (not es_v_loc) and (loc_protegido or float(res_m.get("p_a", 0)) < 68.0):
                        continue
                mercados_ganador_respaldo.append((nombre, prob, cuota_orig))
                continue

            if nombre in ("Combo 1X + O1.5", "Combo 1X + U3.5", "Combo 1X + U4.5"):
                if es_liga_cerrada and (c1_bp is None or c1_bp > 1.95):
                    continue
                if (c1_bp is not None and (c1_bp < 1.28 or c1_bp > 2.35)) or (c2_bp is not None and c2_bp <= 3.00):
                    continue
                if float(res_m.get("p_a", 0)) >= 32.0:
                    continue
                if nombre == "Combo 1X + O1.5" and (tot_goles < 2.45 or tot_goles >= 3.60):
                    continue
                if nombre == "Combo 1X + U3.5" and (tot_goles >= 2.72):
                    continue
                if nombre == "Combo 1X + U4.5" and (tot_goles >= 2.58):
                    continue
                if prob < 62.0:
                    continue
                mercados_ganador_respaldo.append((nombre, prob, cuota_orig))
                continue

            if nombre in ("Combo X2 + O1.5", "Combo X2 + U3.5"):
                if es_liga_cerrada and (c2_bp is None or c2_bp > 1.85):
                    continue
                if (c2_bp is not None and (c2_bp < 1.28 or c2_bp > 2.10)) or (c1_bp is not None and c1_bp <= 3.15):
                    continue
                if float(res_m.get("p_h", 0)) >= 26.0 or res_m.get("es_plaza_hostil_local") or (is_america and (c2_bp is None or c2_bp > 1.75)):
                    continue
                if nombre == "Combo X2 + O1.5" and (tot_goles < 2.45 or tot_goles >= 3.60):
                    continue
                if nombre == "Combo X2 + U3.5" and (tot_goles >= 2.70):
                    continue
                if prob < 62.0:
                    continue
                mercados_ganador_respaldo.append((nombre, prob, cuota_orig))
                continue
            continue

        mercados_ritmo.append((nombre, prob, cuota_orig))

    # Ordenar priorizando efectividad real en MERCADOS PUROS DE FÚTBOL (equilibrado entre Ganador, Goles, Tiempos, BTTS, Combos y Goles Equipo)
    todos_ordenados = sorted(
        mercados_ritmo + mercados_ganador_respaldo,
        key=lambda x: (
            x[1]
            + (7.5 if obtener_familia(x[0]) in {"ganador", "combo", "btts", "tiempos", "goles"} else (4.5 if obtener_familia(x[0]) == "goles_equipo" else 0.0))
            - (10.5 if obtener_familia(x[0]) == "faltas" else (6.5 if obtener_familia(x[0]) in {"corners", "tarjetas"} else (2.5 if obtener_familia(x[0]) == "remates" else 0.0)))
        ),
        reverse=True
    )

    exclusivos_vip_extremos = {
        "Ambos Marcan (BTTS)", "Over 2.5 Goles", "Over 3.5 Goles",
        "Remates Puerta > 7.5", "Remates Puerta > 8.5", "Córners > 9.5",
        "Total Asiático > 2.25", "Total Asiático > 2.75", "Total Menos de 2.5 (Under)",
        "Combo 1X + O1.5", "Combo X2 + O1.5", "Combo 1X + U3.5", "Combo X2 + U3.5",
        f"Goles {res_m['local'][:12]} > 1.5", f"Goles {res_m['visitante'][:12]} > 1.5",
    }
    if float(over_goles_bp.get(4.5) or over_goles_bp.get("4.5") or 2.0) > 1.38:
        exclusivos_vip_extremos.add("Over 4.5 Goles")
    if abs(linea_f_vip - linea_f_free) >= 0.5 and float(cuotas_reales_casa.get(f"Faltas Totales > {linea_f_vip:.1f}", 1.45)) >= 1.35:
        exclusivos_vip_extremos.add(f"Faltas Totales > {linea_f_vip:.1f}")
    if abs(linea_t_vip - linea_t_free) >= 0.5:
        exclusivos_vip_extremos.add(f"Remates Puerta > {linea_t_vip:.1f}")
    exclusivos_vip_extremos.update({"Over 5.5 Goles", "Goles 1T > 1.5", "Goles 2do Tiempo > 1.5"})
    if res_m.get("nombre_goleador"):
        exclusivos_vip_extremos.add(res_m["nombre_goleador"])
    if res_m.get("nombre_dom_goles") and float(res_m.get("c_min_dom_goles") or 0) >= 1.38:
        exclusivos_vip_extremos.add(res_m["nombre_dom_goles"])

    lineas_bajas_irreales = {"Total Menos de 3.5 (Under)"} if tot_goles >= 2.48 else set()
    if tot_corn >= 9.6:
        lineas_bajas_irreales.add("Córners > 7.5")

    candidatos_free = []
    for m in todos_ordenados:
        if m[0] in exclusivos_vip_extremos or m[0] in lineas_bajas_irreales or m[1] < 66.0:
            continue
        cuo_f = calcular_cuota_real_casa(m[1], m[2], "FREE", m[0], cuotas_reales_casa)
        if cuo_f > 1.42:
            continue
        candidatos_free.append((m[0], min(88.5, round(float(m[1]), 1)), cuo_f))
    if len(candidatos_free) < 2:
        candidatos_free = [
            (m[0], min(88.5, round(float(m[1]), 1)), calcular_cuota_real_casa(m[1], m[2], "FREE", m[0], cuotas_reales_casa))
            for m in todos_ordenados
            if m[0] not in exclusivos_vip_extremos and m[1] >= 60.0
        ]
    # Fase 1 (Máxima Efectividad): priorizar en FREE los mercados con mayor probabilidad real en zona dulce 1.28-1.38
    candidatos_free.sort(
        key=lambda x: (x[1] >= 74.0, 1.28 <= x[2] <= 1.38, x[1]),
        reverse=True
    )

    # Anti-colinealidad cruzada v26.9 (protege auditoría de las 4 apuestas FREE+VIP del mismo partido):
    # 1) Máximo 2 picks dependientes de gol entre las 4 selecciones combinadas (evita que un 0-0/1-0 tumbe 3/4 picks).
    # 2) Prohibir repetir el mismo favorito direccional (ej. Combo 1X en VIP + Sin Empate Local en FREE) en el mismo duelo.
    def _lado_direccional_pick(nom_pk):
        nl = str(nom_pk or "").lower()
        if "1x" in nl:
            return "local"
        if "x2" in nl:
            return "visita"
        if nl.startswith("victoria ") or nl.startswith("sin empate "):
            if str(res_m.get("local", ""))[:7].lower() in nl:
                return "local"
            if str(res_m.get("visitante", ""))[:7].lower() in nl:
                return "visita"
        return None

    sel_vip_prev = res_m.get("seleccion_vip", [])
    nombres_usados_vip = {m[0] for m in sel_vip_prev}
    fams_secundarias_vip = {obtener_familia(m[0]) for m in sel_vip_prev if obtener_familia(m[0]) in FAMILIAS_SECUNDARIAS}
    lados_dir_vip = {_lado_direccional_pick(m[0]) for m in sel_vip_prev} - {None}
    if tipo_filtro == "FREE" and lados_dir_vip:
        for cand_f in candidatos_free:
            if _lado_direccional_pick(cand_f[0]) in lados_dir_vip:
                nombres_usados_vip.add(cand_f[0])
    n_gol_en_vip = sum(1 for m in sel_vip_prev if _es_pick_dependiente_gol_global(m[0]))
    max_gol_free_cruzado = max(0, 2 - n_gol_en_vip) if (tipo_filtro == "FREE" and sel_vip_prev and tot_goles < 3.30) else None

    top_2_free_base = seleccionar_par_distinto_familia(
        candidatos_free,
        excluidos=nombres_usados_vip,
        familias_excluidas=fams_secundarias_vip,
        tipo_filtro="FREE",
        registrar_memoria=(tipo_filtro == "FREE"),
        tot_goles=tot_goles,
        max_picks_gol=max_gol_free_cruzado
    )

    if tipo_filtro == "FREE":
        top_2 = top_2_free_base
    elif tipo_filtro == "VIP":
        nombres_usados_free = {m[0] for m in top_2_free_base}
        fams_secundarias_free = {obtener_familia(m[0]) for m in top_2_free_base if obtener_familia(m[0]) in FAMILIAS_SECUNDARIAS}
        colchones_bajos = {"Córners > 7.5", "Total Menos de 3.5 (Under)"}
        if abs(linea_f_vip - linea_f_free) >= 0.5:
            colchones_bajos.add(f"Faltas Totales > {linea_f_free:.1f}")
        if abs(linea_t_vip - linea_t_free) >= 0.5:
            colchones_bajos.add(f"Remates Puerta > {linea_t_free:.1f}")
        excluidos_vip = nombres_usados_free.union(colchones_bajos)

        candidatos_vip = []
        for m in todos_ordenados:
            if m[1] < 60.0 or m[0] in excluidos_vip:
                continue
            cuo_v = calcular_cuota_real_casa(m[1], m[2], "VIP", m[0], cuotas_reales_casa)
            # Zona dulce VIP v26.6: 1.38 - 1.62 (evita cuotas > 1.65 donde el acierto cae al 58%)
            if cuo_v < 1.38 or cuo_v > 1.68:
                continue
            candidatos_vip.append((m[0], min(89.5, round(float(m[1]), 1)), cuo_v))
        if len(candidatos_vip) < 2:
            for m in todos_ordenados:
                if m[1] < 57.0 or m[0] in excluidos_vip or any(x[0] == m[0] for x in candidatos_vip):
                    continue
                cuo_v = calcular_cuota_real_casa(m[1], m[2], "VIP", m[0], cuotas_reales_casa)
                if cuo_v >= 1.38:
                    candidatos_vip.append((m[0], min(89.5, round(float(m[1]), 1)), cuo_v))
        # Prioridad máxima efectividad en VIP: zona dulce 1.38-1.62 + probabilidad >= 70% + mayor probabilidad real
        candidatos_vip.sort(
            key=lambda x: (
                1.38 <= x[2] <= 1.62,
                x[1] >= 70.0,
                obtener_familia(x[0]) in FAMILIAS_FUTBOL_PURO,
                x[1]
            ),
            reverse=True
        )
        top_2 = seleccionar_par_distinto_familia(
            candidatos_vip,
            excluidos=excluidos_vip,
            familias_excluidas=fams_secundarias_free,
            tipo_filtro="VIP",
            registrar_memoria=True,
            tot_goles=tot_goles
        )
    else:
        candidatos_desc = [
            (m[0], m[1], calcular_cuota_real_casa(m[1], m[2], "FREE", m[0], cuotas_reales_casa))
            for m in todos_ordenados
        ]
        top_2 = seleccionar_par_distinto_familia(candidatos_desc, tipo_filtro="DESCARTES", registrar_memoria=True, tot_goles=tot_goles)

    # Candado final 100% HONESTO MATEMÁTICAMENTE (PROHIBIDO inventar 73.5% en Córners/Tarjetas ni repetir familia entre FREE y VIP)
    if len(top_2) < 2:
        es_copa_dom_fb = bool(res_m.get("es_copa")) and not any(
            k_int in liga_vis for k_int in ("CHAMPIONS", "EUROPA LEAGUE", "CONFERENCE", "LIBERTADORES", "SUDAMERICANA", "MUNDIAL", "EUROCOPA", "AMÉRICA", "NATIONS")
        )
        entropia_fb = float(res_m.get("entropia_1x2") or 0.0)
        entropia_lim_fb = float(res_m.get("entropia_max_ganador") or 0.935)
        puede_1x_resp = (not es_derbi) and (entropia_fb < entropia_lim_fb) and (not (vis_protegido and loc_protegido)) and (not (vis_protegido and not loc_protegido)) and float(res_m.get("p_a") or 50.0) < 34.0
        puede_x2_resp = (not es_copa_dom_fb) and (not es_derbi) and (entropia_fb < entropia_lim_fb) and (not loc_protegido) and (not is_america) and (not res_m.get("es_plaza_hostil_local")) and float(res_m.get("p_h") or 50.0) < 25.0

        # Probabilidades REALES del modelo (cero valores hardcodeados!)
        p_c85_real = round(float(res_m.get("p_c85") or 0.0), 1)
        p_c75_real = round(float(res_m.get("p_c75") or 0.0), 1)
        p_t35_real = round(float(res_m.get("p_t35") or 0.0), 1)
        p_u35_real = round(float(res_m.get("p_under35") or 0.0), 1)
        p_u25_real = round(float(res_m.get("p_under25") or 0.0), 1)
        p_o15_real = round(float(res_m.get("p_15_match") or 0.0), 1)
        p_2t_real = round(float(res_m.get("p_05_2t") or 0.0), 1)
        p_1t_real = round(float(res_m.get("p_05_ht") or 0.0), 1)
        p_btts_real = round(float(res_m.get("p_btts") or 0.0), 1)

        nom_f_vip = f"Faltas Totales > {linea_f_vip:.1f}"
        nom_f_free = f"Faltas Totales > {linea_f_free:.1f}"
        c_fv = calcular_cuota_real_casa(p_f_vip or 50.0, c_f_vip, "VIP", nom_f_vip, cuotas_reales_casa)
        c_ff = calcular_cuota_real_casa(p_f_free or 50.0, c_f_free, "FREE", nom_f_free, cuotas_reales_casa)

        respaldo_vip = []
        respaldo_free = []

        # Respaldo v26.4: TODOS los 20+ mercados activos (incluyendo Under, X2, Córners, Goles Equipo y Combos) con matemática calibrada
        if tot_goles <= 2.35:
            if p_u35_real >= 68.0:
                respaldo_free.append(("Total Menos de 3.5 (Under)", p_u35_real, calcular_cuota_real_casa(p_u35_real, res_m.get("c_min_under35"), "FREE", "Total Menos de 3.5 (Under)", cuotas_reales_casa)))
            if p_u25_real >= 58.0:
                respaldo_vip.append(("Total Menos de 2.5 (Under)", p_u25_real, calcular_cuota_real_casa(p_u25_real, res_m.get("c_min_under25"), "VIP", "Total Menos de 2.5 (Under)", cuotas_reales_casa)))
        else:
            if p_2t_real >= 68.0:
                respaldo_free.append(("Gol en 2do Tiempo", p_2t_real, calcular_cuota_real_casa(p_2t_real, res_m.get("c_min_05_2t"), "FREE", "Gol en 2do Tiempo", cuotas_reales_casa)))
                respaldo_vip.append(("Gol en 2do Tiempo", p_2t_real, calcular_cuota_real_casa(p_2t_real, res_m.get("c_min_05_2t"), "VIP", "Gol en 2do Tiempo", cuotas_reales_casa)))
            if p_o15_real >= 69.0 and tot_goles >= 2.38:
                respaldo_free.append(("Over 1.5 Goles", p_o15_real, calcular_cuota_real_casa(p_o15_real, res_m.get("c_min_15"), "FREE", "Over 1.5 Goles", cuotas_reales_casa)))
            if p_1t_real >= 66.0 and tot_goles >= 2.45:
                respaldo_free.append(("Gol en 1T", p_1t_real, calcular_cuota_real_casa(p_1t_real, res_m.get("c_min_05_ht"), "FREE", "Gol en 1T", cuotas_reales_casa)))
                respaldo_vip.append(("Gol en 1T", p_1t_real, calcular_cuota_real_casa(p_1t_real, res_m.get("c_min_05_ht"), "VIP", "Gol en 1T", cuotas_reales_casa)))
            if p_btts_real >= 58.0 and tot_goles >= 2.50:
                respaldo_vip.append(("Ambos Marcan (BTTS)", p_btts_real, calcular_cuota_real_casa(p_btts_real, res_m.get("c_min_btts"), "VIP", "Ambos Marcan (BTTS)", cuotas_reales_casa)))
        if puede_1x_resp and float(res_m.get("p_1x") or 0) >= 70.0:
            respaldo_free.append(("Doble Oport. 1X", round(float(res_m.get("p_1x")), 1), calcular_cuota_real_casa(float(res_m.get("p_1x")), res_m.get("c_min_1x"), "FREE", "Doble Oport. 1X", cuotas_reales_casa)))
        elif puede_x2_resp and float(res_m.get("p_x2") or 0) >= 72.0:
            respaldo_free.append(("Doble Oport. X2", round(float(res_m.get("p_x2")), 1), calcular_cuota_real_casa(float(res_m.get("p_x2")), res_m.get("c_min_x2"), "FREE", "Doble Oport. X2", cuotas_reales_casa)))

        if p_f_free and float(p_f_free) >= 62.0 and (linea_f_free <= 22.5 or nom_f_free in cuotas_reales_casa):
            respaldo_free.append((nom_f_free, round(float(p_f_free), 1), c_ff))
        if p_f_vip and float(p_f_vip) >= 58.0 and (linea_f_vip <= 22.5 or nom_f_vip in cuotas_reales_casa):
            respaldo_vip.append((nom_f_vip, round(float(p_f_vip), 1), c_fv))
        if p_tf_m and float(p_tf_m) >= 62.0:
            respaldo_free.append((f"Remates Puerta > {linea_t_free:.1f}", round(float(p_tf_m), 1), calcular_cuota_real_casa(float(p_tf_m), c_tf_m, "FREE", f"Remates Puerta > {linea_t_free:.1f}", cuotas_reales_casa)))
        if p_tv_m and float(p_tv_m) >= 57.0:
            respaldo_vip.append((f"Remates Puerta > {linea_t_vip:.1f}", round(float(p_tv_m), 1), calcular_cuota_real_casa(float(p_tv_m), c_tv_m, "VIP", f"Remates Puerta > {linea_t_vip:.1f}", cuotas_reales_casa)))
        if p_t35_real >= 58.0:
            respaldo_vip.append((f"Tarjetas > {res_m.get('linea_tarj', 3.5)}", p_t35_real, calcular_cuota_real_casa(p_t35_real, res_m.get("c_min_t35"), "VIP", f"Tarjetas > {res_m.get('linea_tarj', 3.5)}", cuotas_reales_casa)))
        if p_c75_real >= 66.0 and (tot_corn >= 8.75 or "Córners > 7.5" in cuotas_reales_casa):
            respaldo_free.append(("Córners > 7.5", p_c75_real, calcular_cuota_real_casa(p_c75_real, res_m.get("c_min_c75"), "FREE", "Córners > 7.5", cuotas_reales_casa)))
        if p_c85_real >= 62.0 and (tot_corn >= 9.85 or "Córners > 8.5" in cuotas_reales_casa):
            respaldo_vip.append(("Córners > 8.5", p_c85_real, calcular_cuota_real_casa(p_c85_real, res_m.get("c_min_c85"), "VIP", "Córners > 8.5", cuotas_reales_casa)))

        respaldo_fams = respaldo_vip if tipo_filtro == "VIP" else respaldo_free
        respaldo_fams.sort(key=lambda x: x[1], reverse=True)

        usados_actual = {m[0] for m in top_2}.union(
            {m[0] for m in res_m.get("seleccion_free", [])} if tipo_filtro == "VIP" else {m[0] for m in res_m.get("seleccion_vip", [])}
        )
        fams_actual = {obtener_familia(m[0]) for m in top_2}
        otra_sel = res_m.get("seleccion_free", []) if tipo_filtro == "VIP" else res_m.get("seleccion_vip", [])
        fams_otra = {obtener_familia(m[0]) for m in otra_sel}
        # BLOQUEO DE DOBLE EXPOSICIÓN: nunca repetir Córners ni Faltas/Disciplina entre FREE y VIP en el mismo partido!
        for fam_sens in ("corners", "faltas", "tarjetas", "remates"):
            if fam_sens in fams_otra:
                fams_actual.add(fam_sens)
        if tot_goles < 3.15 and ("goles" in fams_actual or "tiempos" in fams_actual):
            fams_actual.update({"goles", "tiempos"})
        es_fem_resp = ("WOMEN" in liga_vis) or ("FEMEN" in liga_vis)
        for r_m in respaldo_fams:
            if candado_mercado_real_kambi and r_m[0] not in cuotas_reales_casa:
                continue
            if float(r_m[1] or 0) < (56.0 if tipo_filtro == "VIP" else 60.0):
                continue
            if tipo_filtro == "VIP" and float(r_m[2] or 0) < 1.38:
                continue
            if es_fem_resp and ("Faltas" in r_m[0] or "Tarjetas" in r_m[0]) and r_m[0] not in cuotas_reales_casa:
                continue
            if es_fem_resp and "Córners > 8.5" in r_m[0] and tot_corn < 8.6 and r_m[0] not in cuotas_reales_casa:
                continue
            if es_fem_resp and "Córners > 7.5" in r_m[0] and tot_corn < 7.8 and r_m[0] not in cuotas_reales_casa:
                continue
            fam_r = obtener_familia(r_m[0])
            n_gol_comb_r = sum(1 for x in (list(top_2) + list(otra_sel)) if _es_pick_dependiente_gol_global(x[0]))
            if (tot_goles < 3.25 or es_copa_dom_fb) and n_gol_comb_r >= 2 and _es_pick_dependiente_gol_global(r_m[0]):
                continue
            if (fam_r == "combo" and ("goles" in fams_actual or "tiempos" in fams_actual)) or (fam_r in {"goles", "tiempos"} and "combo" in fams_actual):
                continue
            if r_m[0] not in usados_actual and fam_r not in fams_actual and fam_r not in fams_otra:
                top_2.append(r_m)
                fams_actual.add(obtener_familia(r_m[0]))
            if len(top_2) == 2:
                break

        # Pase final coherente con el Guion de Partido (nunca 1 sola selección, nunca contradecir Under, nunca VIP < 1.35, nunca solapar familia FREE/VIP)
        if len(top_2) < 2:
            fams_misma_tarjeta = {obtener_familia(m[0]) for m in top_2}
            hay_under_otra = any("Menos de" in str(m[0]) or "Under" in str(m[0]) for m in otra_sel)
            lvl_em = tipo_filtro if tipo_filtro in ("FREE", "VIP") else "FREE"
            # Escalar líneas de emergencia de forma honesta según la media real en duelos ultra-cerrados (ej. Colombia 1.84 goles)
            if lvl_em == "FREE":
                lin_r_em = linea_t_free if tot_tiros >= 7.8 else (5.5 if tot_tiros >= 6.4 else 4.5)
                p_r_em_v, c_r_em_v = (p_tf_m, c_tf_m) if abs(lin_r_em - linea_t_free) < 0.1 else _prob_negbin_over(tot_tiros, lin_r_em, phi=1.40)
                lin_c_em = 7.5 if tot_corn >= 8.2 else (6.5 if tot_corn >= 7.2 else 5.5)
                p_c_em_v, c_c_em_v = (res_m.get("p_c75"), res_m.get("c_min_c75")) if lin_c_em == 7.5 else _prob_negbin_over(tot_corn, lin_c_em, phi=1.50)
                tot_t_em = float(res_m.get("tot_tarj") or 4.0)
                lin_t_em = 3.5 if float(res_m.get("p_t35") or 0.0) >= 56.0 else 2.5
                p_t_em_v, c_t_em_v = (res_m.get("p_t35"), res_m.get("c_min_t35")) if lin_t_em == 3.5 else _prob_negbin_over(tot_t_em, 2.5, phi=1.35)
                lin_f_em = linea_f_free
                p_f_em_v, c_f_em_v = p_f_free, c_f_free
            else:
                lin_r_em, p_r_em_v, c_r_em_v = linea_t_vip, p_tv_m, c_tv_m
                lin_c_em, p_c_em_v, c_c_em_v = 8.5, res_m.get("p_c85"), res_m.get("c_min_c85")
                lin_t_em, p_t_em_v, c_t_em_v = res_m.get("linea_tarj", 3.5), res_m.get("p_t35"), res_m.get("c_min_t35")
                lin_f_em, p_f_em_v, c_f_em_v = linea_f_vip, p_f_vip, c_f_vip

            emergencia = [
                (f"Remates Puerta > {lin_r_em:.1f}",
                 round(float(p_r_em_v or 0.0), 1),
                 calcular_cuota_real_casa(float(p_r_em_v or 62.0), c_r_em_v, lvl_em, f"Remates Puerta > {lin_r_em:.1f}", cuotas_reales_casa)),
                (f"Tarjetas > {lin_t_em:.1f}",
                 round(float(p_t_em_v or 0.0), 1),
                 calcular_cuota_real_casa(float(p_t_em_v or 62.0), c_t_em_v, lvl_em, f"Tarjetas > {lin_t_em:.1f}", cuotas_reales_casa)),
                (f"Córners > {lin_c_em:.1f}",
                 round(float(p_c_em_v or 0.0), 1),
                 calcular_cuota_real_casa(float(p_c_em_v or 62.0), c_c_em_v, lvl_em, f"Córners > {lin_c_em:.1f}", cuotas_reales_casa)),
                (f"Faltas Totales > {lin_f_em:.1f}",
                 round(float(p_f_em_v or 0.0), 1),
                 calcular_cuota_real_casa(float(p_f_em_v or 62.0), c_f_em_v, lvl_em, f"Faltas Totales > {lin_f_em:.1f}", cuotas_reales_casa)),
            ]
            if tot_goles <= 2.35 or hay_under_otra:
                emergencia.insert(0, ("Total Menos de 2.5 (Under)" if lvl_em == "VIP" else "Total Menos de 3.5 (Under)",
                    round(float((res_m.get("p_under25") if lvl_em == "VIP" else res_m.get("p_under35")) or 0.0), 1),
                    calcular_cuota_real_casa(float((res_m.get("p_under25") if lvl_em == "VIP" else res_m.get("p_under35")) or 68.0), (res_m.get("c_min_under25") if lvl_em == "VIP" else res_m.get("c_min_under35")), lvl_em, "Total Menos de 2.5 (Under)" if lvl_em == "VIP" else "Total Menos de 3.5 (Under)", cuotas_reales_casa)))
            else:
                emergencia = [
                    ("Gol en 2do Tiempo", round(float(res_m.get("p_05_2t") or 0.0), 1), calcular_cuota_real_casa(float(res_m.get("p_05_2t") or 72.0), res_m.get("c_min_05_2t"), lvl_em, "Gol en 2do Tiempo", cuotas_reales_casa)),
                    ("Gol en 1T", round(float(res_m.get("p_05_ht") or 0.0), 1), calcular_cuota_real_casa(float(res_m.get("p_05_ht") or 70.0), res_m.get("c_min_05_ht"), lvl_em, "Gol en 1T", cuotas_reales_casa)),
                    ("Over 1.5 Goles", round(float(res_m.get("p_15_match") or 0.0), 1), calcular_cuota_real_casa(float(res_m.get("p_15_match") or 72.0), res_m.get("c_min_15"), lvl_em, "Over 1.5 Goles", cuotas_reales_casa)),
                    *emergencia
                ]
            if candado_mercado_real_kambi:
                # Si Kambi está activo, el respaldo de emergencia usa exclusivamente los mercados reales restantes de cuotas_reales_casa
                emergencia = [
                    (m[0], round(float(m[1]), 1), calcular_cuota_real_casa(m[1], m[2], lvl_em, m[0], cuotas_reales_casa))
                    for m in todos_ordenados
                    if m[0] in cuotas_reales_casa
                ]
            for e_m in emergencia:
                fam_em = obtener_familia(e_m[0])
                if lvl_em == "VIP" and float(e_m[2] or 0) < 1.38:
                    continue
                n_gol_comb_em = sum(1 for x in (list(top_2) + list(otra_sel)) if _es_pick_dependiente_gol_global(x[0]))
                if (tot_goles < 3.25 or es_copa_dom_fb) and n_gol_comb_em >= 2 and _es_pick_dependiente_gol_global(e_m[0]):
                    continue
                if fam_em in fams_misma_tarjeta or fam_em in fams_otra:
                    continue
                if (fam_em == "goles" and "tiempos" in fams_misma_tarjeta) or (fam_em == "tiempos" and "goles" in fams_misma_tarjeta):
                    continue
                if (fam_em == "goles" and "goles_equipo" in fams_misma_tarjeta) or (fam_em == "goles_equipo" and "goles" in fams_misma_tarjeta):
                    continue
                if (fam_em == "combo" and ("goles" in fams_misma_tarjeta or "tiempos" in fams_misma_tarjeta)) or (fam_em in {"goles", "tiempos"} and "combo" in fams_misma_tarjeta):
                    continue
                if float(e_m[1] or 0) >= 54.0 and e_m[0] not in usados_actual:
                    top_2.append(e_m)
                    fams_misma_tarjeta.add(fam_em)
                if len(top_2) == 2:
                    break

        # GARANTÍA ABSOLUTA DE 2 SELECCIONES REALES EN EL JPG (v26.6):
        # Ninguna tarjeta JPG puede quedar con 1 sola apuesta. Completa con el siguiente mejor mercado real
        # ya calculado del partido (sin inventar probabilidades y de distinta familia).
        if len(top_2) < 2:
            lvl_g = tipo_filtro if tipo_filtro in ("FREE", "VIP") else "FREE"
            usados_g = {m[0] for m in top_2}
            fams_g = {obtener_familia(m[0]) for m in top_2}
            pool_garantia = []
            for m_b in (list(todos_ordenados) + list(mercados_brutos)):
                if not m_b or m_b[1] is None or m_b[2] is None:
                    continue
                nm_g, pr_g, cu_g = m_b[0], round(float(m_b[1]), 1), float(m_b[2])
                if pr_g < 50.0 or nm_g in usados_g:
                    continue
                if any(x[0] == nm_g for x in pool_garantia):
                    continue
                cuo_g = calcular_cuota_real_casa(pr_g, cu_g, lvl_g, nm_g, cuotas_reales_casa)
                pool_garantia.append((nm_g, min(89.0, pr_g), cuo_g))
            pool_garantia.sort(key=lambda x: (obtener_familia(x[0]) not in fams_g, x[1]), reverse=True)
            # Pase 1: distinta familia y sin repetir el pick exacto de la otra tarjeta
            for cand_g in pool_garantia:
                fam_cg = obtener_familia(cand_g[0])
                if fam_cg not in fams_g and cand_g[0] not in usados_actual:
                    top_2.append(cand_g)
                    fams_g.add(fam_cg)
                    usados_g.add(cand_g[0])
                if len(top_2) == 2:
                    break
            # Pase 2 (caso extremo): distinta familia aunque se solape con otra tarjeta (nunca dejar 1 sola apuesta)
            if len(top_2) < 2:
                for cand_g in pool_garantia:
                    fam_cg = obtener_familia(cand_g[0])
                    if fam_cg not in fams_g and cand_g[0] not in usados_g:
                        top_2.append(cand_g)
                        fams_g.add(fam_cg)
                        usados_g.add(cand_g[0])
                    if len(top_2) == 2:
                        break
            # Pase 3 (último recurso absoluto): cualquier mercado distinto con mayor probabilidad real
            if len(top_2) < 2:
                for cand_g in pool_garantia:
                    if cand_g[0] not in usados_g:
                        top_2.append(cand_g)
                        usados_g.add(cand_g[0])
                    if len(top_2) == 2:
                        break

    res_m[f"seleccion_{tipo_filtro.lower()}"] = top_2
    if not guardar_imagen:
        return None

    # ==========================================================================
    # RENDERIZADO ESTÉTICO CENTRADO Y SIMÉTRICO (1080x1080) — ESTILO INSTITUCIONAL
    # ==========================================================================
    es_vip_card = str(tipo_filtro).upper() == "VIP"
    c_blanco = (248, 250, 252, 255)
    c_gris = (168, 182, 200, 255)
    c_verde = (0, 232, 118, 255)
    c_oro = (255, 204, 0, 255)
    c_azul = (64, 174, 255, 255)
    c_panel = (14, 22, 35, 238)
    c_borde = (54, 78, 108, 185)
    c_acento = c_oro if es_vip_card else c_verde

    imagen = _cargar_fondo_card_elegante(
        acento_izq=(255, 204, 0) if es_vip_card else (0, 232, 118),
        acento_der=(0, 232, 118) if es_vip_card else (64, 174, 255),
    )
    draw = ImageDraw.Draw(imagen, "RGBA")

    # 1. Pill superior centrada con nivel y competición
    tag_nivel = "SELECCIÓN VIP PREMIUM  •  EV+" if es_vip_card else ("ANÁLISIS GRATUITO  •  SEGURIDAD" if str(tipo_filtro).upper() == "FREE" else "ESCÁNER QUANT DATA")
    top_pill = f"{tag_nivel}   |   {res_m['liga_visual']}"
    draw.rounded_rectangle([(56, 40), (1024, 92)], radius=26, fill=(22, 20, 12, 238) if es_vip_card else (11, 32, 24, 238), outline=c_acento, width=2)
    f_pill = _fuente_card_ajustada(draw, top_pill.upper(), "bold", 21, 910, 15)
    draw.text((_cx_card(draw, top_pill.upper(), f_pill), 54), top_pill.upper(), font=f_pill, fill=c_acento)

    # 2. Tarjeta central del Partido con ESCUDOS REALES centrados a cada lado
    draw.rounded_rectangle([(56, 114), (1024, 344)], radius=28, fill=c_panel, outline=c_borde, width=2)

    esc_l = _obtener_escudo_card(res_m["local"], logo_url=res_m.get("logo_local"), tam=126)
    esc_v = _obtener_escudo_card(res_m["visitante"], logo_url=res_m.get("logo_vis"), tam=126)
    if esc_l is not None:
        draw.ellipse([(88, 156), (232, 300)], fill=(18, 28, 44, 245), outline=c_verde, width=3)
        imagen.paste(esc_l, (160 - esc_l.width // 2, 228 - esc_l.height // 2), esc_l)
    if esc_v is not None:
        draw.ellipse([(848, 156), (992, 300)], fill=(18, 28, 44, 245), outline=c_oro, width=3)
        imagen.paste(esc_v, (920 - esc_v.width // 2, 228 - esc_v.height // 2), esc_v)

    draw = ImageDraw.Draw(imagen, "RGBA")
    loc_up = res_m["local"].upper()
    vis_up = res_m["visitante"].upper()
    f_loc = _fuente_card_ajustada(draw, loc_up, "bold", 42, 575, 22)
    f_vis = _fuente_card_ajustada(draw, vis_up, "bold", 42, 575, 22)
    f_vs_m = _fuente_card("bold", 24)
    draw.text((_cx_card(draw, loc_up, f_loc), 140), loc_up, font=f_loc, fill=c_blanco)
    draw.text((_cx_card(draw, "VS", f_vs_m), 196), "VS", font=f_vs_m, fill=c_acento)
    draw.text((_cx_card(draw, vis_up, f_vis), 230), vis_up, font=f_vis, fill=c_blanco)

    # Fecha y hora centradas en píldora sutil
    h_esp_c = str(res_m.get("hora", "20:00"))
    try:
        h_c_i = int(h_esp_c.split(":")[0])
        h_col_c = f"{(h_c_i - 6) % 24:02d}:{h_esp_c.split(':')[1]}"
        txt_fh = f"{res_m['fecha']}   •   {h_esp_c}h ESP  /  {h_col_c}h COL"
    except Exception:
        txt_fh = f"{res_m['fecha']}   •   {h_esp_c}h ESP"
    f_fh = _fuente_card_ajustada(draw, txt_fh, "mono", 22, 575, 16)
    draw.text((_cx_card(draw, txt_fh, f_fh), 296), txt_fh, font=f_fh, fill=c_gris)

    # 3. Tres chips métricos simétricos lado a lado (GOLES | CÓRNERS | FALTAS)
    faltas_val = res_m.get('tot_faltas', 22.0)
    faltas_str = f"{faltas_val:.1f}" if isinstance(faltas_val, (int, float)) else "22.0"
    corn_val = res_m.get('tot_corn') or 8.5
    corn_str = f"{corn_val:.1f}" if isinstance(corn_val, (int, float)) else "8.5"
    goles_str = f"{float(res_m.get('tot_goles', 2.5)):.2f}"

    chips_c = [
        ("GOLES ESPERADOS", goles_str, c_verde),
        ("CÓRNERS PROY.", corn_str, c_oro),
        ("FRICCIÓN (FALTAS)", faltas_str, c_azul),
    ]
    w_ch = 306
    gap_ch = 25
    x_ch0 = (1080 - (3 * w_ch + 2 * gap_ch)) // 2
    for idx_m, (lbl_m, val_m, col_m) in enumerate(chips_c):
        xc0 = x_ch0 + idx_m * (w_ch + gap_ch)
        draw.rounded_rectangle([(xc0, 366), (xc0 + w_ch, 478)], radius=20, fill=c_panel, outline=c_borde, width=2)
        f_ml = _fuente_card("bold", 19)
        f_mv = _fuente_card("bold", 44)
        draw.text((_cx_card(draw, lbl_m, f_ml, xc0 + w_ch // 2), 384), lbl_m, font=f_ml, fill=c_gris)
        draw.text((_cx_card(draw, val_m, f_mv, xc0 + w_ch // 2), 416), val_m, font=f_mv, fill=col_m)

    # 4. Banda táctica centrada limpia
    linea_club_1, _ = obtener_explicacion_apuesta_club(res_m)
    ctx_limpio = contexto.replace("[", "").replace("]", "").strip().upper()
    txt_banda = f"PERFIL: {ctx_limpio}   •   {linea_club_1.replace('DOMINIO TÁCTICO: ', '')}"
    draw.rounded_rectangle([(56, 498), (1024, 558)], radius=18, fill=(20, 26, 38, 232), outline=(255, 204, 0, 120), width=2)
    f_bd = _fuente_card_ajustada(draw, txt_banda, "mono", 20, 920, 14)
    draw.text((_cx_card(draw, txt_banda, f_bd), 516), txt_banda, font=f_bd, fill=c_oro)

    # 5. Sección de Proyecciones Matemáticas (2 tarjetas simétricas elegantes)
    f_sec = _fuente_card("bold", 24)
    tit_sec = "PROYECCIONES DEL MODELO MATEMÁTICO (10.000 SIMULACIONES)"
    draw.text((_cx_card(draw, tit_sec, f_sec), 582), tit_sec, font=f_sec, fill=c_acento)

    y_card = 626
    for idx_p, (nombre, prob, cuota) in enumerate(top_2[:2], start=1):
        if prob <= 0:
            continue
        bg_pick = (10, 32, 24, 244) if not es_vip_card else (24, 22, 12, 244)
        draw.rounded_rectangle([(56, y_card), (1024, y_card + 146)], radius=24, fill=bg_pick, outline=c_acento, width=3)

        # Badge izquierdo con número de selección
        draw.rounded_rectangle([(82, y_card + 16), (236, y_card + 46)], radius=13, fill=c_acento)
        f_num = _fuente_card("bold", 18)
        lbl_n = f"SELECCIÓN #{idx_p}"
        draw.text((_cx_card(draw, lbl_n, f_num, 159), y_card + 21), lbl_n, font=f_num, fill=(8, 14, 20, 255))

        # Nombre del mercado 100% claro en español + subtítulo explicativo para clientes
        tit_claro, sub_claro = formatear_mercado_claro_cliente(nombre, res_m.get("local", ""), res_m.get("visitante", ""))
        f_mk = _fuente_card_ajustada(draw, tit_claro.upper(), "bold", 31, 576, 19)
        draw.text((84, y_card + 56), tit_claro.upper(), font=f_mk, fill=c_blanco)
        f_sub_mk = _fuente_card_ajustada(draw, sub_claro, "mono", 18, 576, 14)
        c_sub_mk = (232, 220, 172, 255) if es_vip_card else (188, 232, 210, 255)
        draw.text((84, y_card + 102), sub_claro, font=f_sub_mk, fill=c_sub_mk)

        # Panel derecho con Probabilidad % y Cuota/Índice
        draw.rounded_rectangle([(684, y_card + 20), (998, y_card + 126)], radius=18, fill=(12, 19, 30, 245), outline=c_borde, width=2)
        p_txt = f"PROB. {prob:.1f}%"
        c_txt = f"ÍNDICE > {cuota:.2f}"
        f_pt = _fuente_card_ajustada(draw, p_txt, "bold", 26, 286, 18)
        f_ct = _fuente_card_ajustada(draw, c_txt, "mono", 28, 286, 19)
        draw.text((_cx_card(draw, p_txt, f_pt, 841), y_card + 34), p_txt, font=f_pt, fill=c_blanco)
        draw.text((_cx_card(draw, c_txt, f_ct, 841), y_card + 76), c_txt, font=f_ct, fill=c_verde)

        y_card += 166

    # 6. Pie centrado limpio y profesional
    draw.line((120, 976, 960, 976), fill=(70, 90, 115, 160), width=2)
    f_pie1 = _fuente_card("bold", 28)
    f_pie2 = _fuente_card("mono", 20)
    pie_a = "@QuantBet22   •   COMUNIDAD DE DATOS"
    pie_b = "MODELO POISSON + DIXON-COLES  •  QUANTBET22.STREAMLIT.APP"
    draw.text((_cx_card(draw, pie_a, f_pie1), 992), pie_a, font=f_pie1, fill=c_oro)
    draw.text((_cx_card(draw, pie_b, f_pie2), 1030), pie_b, font=f_pie2, fill=c_gris)

    nombre_carpeta = f"Alertas_Quant_{res_m['fecha']}"
    if not os.path.exists(nombre_carpeta):
        os.makedirs(nombre_carpeta)

    loc_limpio = "".join(c for c in res_m['local'][:5] if c.isalnum())
    vis_limpio = "".join(c for c in res_m['visitante'][:5] if c.isalnum())
    nombre_img = f"QuantBet_{loc_limpio}_{vis_limpio}_{tipo_filtro}.jpg"
    ruta_completa = os.path.join(nombre_carpeta, nombre_img)

    imagen.convert("RGB").save(ruta_completa, quality=98)
    return ruta_completa


def generar_tarjeta_combinada(fecha, titulo_combinada, subtitulo_nivel, lista_selecciones, cuota_total, prob_directa, prob_protegida, stake_sugerido, sufijo_archivo):
    c_blanco = (248, 250, 252, 255)
    c_gris = (168, 182, 200, 255)
    c_verde = (0, 232, 118, 255)
    c_oro = (255, 204, 0, 255)
    c_panel = (14, 22, 35, 238)
    c_borde = (54, 78, 108, 185)

    imagen = _cargar_fondo_card_elegante(acento_izq=(255, 204, 0), acento_der=(0, 232, 118))
    draw = ImageDraw.Draw(imagen, "RGBA")

    titulo_seguro = titulo_combinada.upper().replace("VIP", "PRO").replace("COMBINADA", "MATRIZ")
    sub_limpio = limpiar_emojis_fuente(subtitulo_nivel).upper()

    # 1. Pill superior centrada
    draw.rounded_rectangle([(56, 38), (1024, 90)], radius=26, fill=(24, 20, 11, 240), outline=c_oro, width=2)
    f_sub = _fuente_card_ajustada(draw, sub_limpio, "bold", 22, 910, 15)
    draw.text((_cx_card(draw, sub_limpio, f_sub), 52), sub_limpio, font=f_sub, fill=c_oro)

    # 2. Título principal + Fecha centrados
    f_tit = _fuente_card_ajustada(draw, titulo_seguro, "bold", 50, 940, 28)
    draw.text((_cx_card(draw, titulo_seguro, f_tit), 108), titulo_seguro, font=f_tit, fill=c_blanco)

    txt_f = f"JORNADA {fecha}   •   SELECCIONES EN PARTIDOS DISTINTOS"
    f_ft = _fuente_card_ajustada(draw, txt_f, "mono", 21, 920, 15)
    draw.text((_cx_card(draw, txt_f, f_ft), 174), txt_f, font=f_ft, fill=c_gris)

    # 3. Dos tarjetas KPI centradas lado a lado (ÍNDICE CONJUNTO | PROBABILIDAD CONJUNTA)
    draw.rounded_rectangle([(56, 218), (526, 336)], radius=22, fill=(10, 32, 24, 244), outline=c_verde, width=3)
    draw.text((_cx_card(draw, "ÍNDICE CONJUNTO", _fuente_card("bold", 20), 291), 234), "ÍNDICE CONJUNTO", font=_fuente_card("bold", 20), fill=c_gris)
    draw.text((_cx_card(draw, f"> {cuota_total:.2f}x", _fuente_card("bold", 48), 291), 266), f"> {cuota_total:.2f}x", font=_fuente_card("bold", 48), fill=c_verde)

    draw.rounded_rectangle([(554, 218), (1024, 336)], radius=22, fill=c_panel, outline=c_oro, width=2)
    draw.text((_cx_card(draw, "ESTABILIDAD MODELO", _fuente_card("bold", 20), 789), 234), "ESTABILIDAD MODELO", font=_fuente_card("bold", 20), fill=c_gris)
    draw.text((_cx_card(draw, f"{prob_protegida:.1f}%", _fuente_card("bold", 48), 789), 266), f"{prob_protegida:.1f}%", font=_fuente_card("bold", 48), fill=c_oro)

    # 4. Tarjetas simétricas por cada pierna de la combinada
    n_legs = len(lista_selecciones)
    alto_leg = 128 if n_legs >= 4 else (162 if n_legs == 3 else 210)
    gap_leg = 14 if n_legs >= 4 else (18 if n_legs == 3 else 24)
    y_cur = 364 if n_legs >= 4 else (376 if n_legs == 3 else 404)

    for idx, item in enumerate(lista_selecciones, start=1):
        draw.rounded_rectangle([(56, y_cur), (1024, y_cur + alto_leg)], radius=22, fill=c_panel, outline=c_borde, width=2)
        partido_txt = f"#{idx}  {item['partido'].upper()}  ({item['hora']}h)"
        loc_cb, vis_cb = (str(item['partido']).split(" vs ") + ["", ""])[:2]
        tit_cb, sub_cb = formatear_mercado_claro_cliente(item['mercado'], loc_cb, vis_cb)
        mercado_txt = tit_cb.upper()
        cuota_txt = f"> {item['cuota']:.2f}"
        prob_txt = f"{item['prob']:.1f}%"

        f_p = _fuente_card_ajustada(draw, partido_txt, "bold", 25 if n_legs < 4 else 22, 660, 16)
        f_m = _fuente_card_ajustada(draw, mercado_txt, "bold", 29 if n_legs < 4 else 24, 660, 17)

        pad_top = 22 if n_legs == 2 else (18 if n_legs == 3 else 16)
        draw.text((86, y_cur + pad_top), partido_txt, font=f_p, fill=c_gris)
        draw.text((86, y_cur + pad_top + (42 if n_legs == 2 else 34)), mercado_txt, font=f_m, fill=c_blanco)

        f_scb = _fuente_card_ajustada(draw, sub_cb, "mono", 18 if n_legs < 4 else 16, 660, 14)
        draw.text((86, y_cur + pad_top + (92 if n_legs == 2 else (78 if n_legs == 3 else 68))), sub_cb, font=f_scb, fill=c_oro)

        # Pill derecha con cuota y probabilidad
        draw.rounded_rectangle([(768, y_cur + 18), (998, y_cur + alto_leg - 18)], radius=16, fill=(10, 28, 22, 240), outline=c_verde, width=2)
        cy_box = y_cur + alto_leg // 2
        f_cb = _fuente_card("bold", 34 if n_legs < 4 else 28)
        f_pb = _fuente_card("mono", 22 if n_legs < 4 else 19)
        draw.text((_cx_card(draw, cuota_txt, f_cb, 883), cy_box - (36 if n_legs < 4 else 30)), cuota_txt, font=f_cb, fill=c_verde)
        draw.text((_cx_card(draw, prob_txt, f_pb, 883), cy_box + (8 if n_legs < 4 else 4)), prob_txt, font=f_pb, fill=c_blanco)

        y_cur += alto_leg + gap_leg

    # 5. Pie centrado limpio
    draw.line((120, 976, 960, 976), fill=(70, 90, 115, 160), width=2)
    f_pie1 = _fuente_card("bold", 28)
    f_pie2 = _fuente_card("mono", 20)
    draw.text((_cx_card(draw, "@QuantBet22   •   COMUNIDAD DE DATOS", f_pie1), 992), "@QuantBet22   •   COMUNIDAD DE DATOS", font=f_pie1, fill=c_oro)
    draw.text((_cx_card(draw, "MODELO POISSON + DIXON-COLES  •  QUANTBET22.STREAMLIT.APP", f_pie2), 1030), "MODELO POISSON + DIXON-COLES  •  QUANTBET22.STREAMLIT.APP", font=f_pie2, fill=c_gris)

    directorio_base = f"Alertas_Quant_{fecha}"
    os.makedirs(directorio_base, exist_ok=True)
    ruta_out = os.path.join(directorio_base, f"00_COMBINADA_{sufijo_archivo}.jpg")
    imagen.convert("RGB").save(ruta_out, quality=98)
    return ruta_out

def _diversificar_20_mercados(candidatos, datos, tipo_alerta):
    """
    Regla Profesional QuantBet22:
    1. Da prioridad a los 20 mercados tácticos (Over 1.5, Asiático > 2.25, Combos 1X/X2 + O1.5,
       BTTS, Gol 1T, Gol 2T, Victoria/Doble Oportunidad, Goles Equipo > 1.5, Remates > 6.5/7.5, Goleador).
    2. Prohibido poner Córners + Tarjetas juntos por defecto en todos los partidos.
    3. Si FREE ya eligió Córners (ej. > 7.5) o Tarjetas, VIP tiene PROHIBIDO repetir la familia Córners (ej. > 8.5) o Tarjetas.
    """
    familias_prohibidas_cruzadas = set()
    if str(tipo_alerta).upper() == "FREE" and datos.get("seleccion_vip"):
        for m_v, _, _ in datos.get("seleccion_vip", []):
            if "Córners" in m_v: familias_prohibidas_cruzadas.add("corners")
            if "Tarjetas" in m_v or "Faltas" in m_v: familias_prohibidas_cruzadas.add("disciplina")
    elif str(tipo_alerta).upper() == "VIP" and datos.get("seleccion_free"):
        for m_f, _, _ in datos.get("seleccion_free", []):
            if "Córners" in m_f: familias_prohibidas_cruzadas.add("corners")
            if "Tarjetas" in m_f or "Faltas" in m_f: familias_prohibidas_cruzadas.add("disciplina")

    # Agregar el mercado de Goleador y Dominio de Goles/Córners si superan el umbral de valor
    extras = []
    # Goleador individual excluido de tarjetas automáticas
    if datos.get("nombre_dom_goles") and (datos.get("p_dom_goles") or 0) >= 66.0:
        extras.append((datos["nombre_dom_goles"], float(datos["p_dom_goles"]), max(1.38, float(datos.get("c_min_dom_goles", 1.45)))))

    lista_total = extras + list(candidatos)

    # Ajustar ponderación: Córners y Tarjetas solo ganan si superan por amplio margen a los mercados de Goles/Combos/Remates
    ajustados = []
    for nom_m, prob_m, cuo_m in lista_total:
        fam_m = obtener_familia(nom_m) if "obtener_familia" in globals() else ("corners" if "Córners" in nom_m else ("disciplina" if "Tarjetas" in nom_m else "otro"))
        if fam_m in familias_prohibidas_cruzadas:
            prob_ord = prob_m - 12.0  # Penaliza repetir la misma familia entre FREE y VIP
        elif "Córners" in nom_m or "Tarjetas" in nom_m:
            prob_ord = prob_m - 3.8   # Evita que Córners y Tarjetas desplacen siempre a Goles, BTTS, Combos, 1X2 y Remates
        else:
            prob_ord = prob_m + 1.5
        ajustados.append((prob_ord, nom_m, prob_m, cuo_m))

    ajustados.sort(key=lambda x: x[0], reverse=True)
    return [(nom_m, prob_m, cuo_m) for _, nom_m, prob_m, cuo_m in ajustados]
