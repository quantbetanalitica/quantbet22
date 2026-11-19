from PIL import Image, ImageDraw, ImageFont
import math
import os

# Memoria de rotación para garantizar variedad real de los 20 mercados a lo largo de la jornada
_MEMORIA_VARIEDAD_TARJETAS = {"FREE": [], "VIP": [], "DESCARTES": []}


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
    elif "oport" in n or "victoria" in n or "1x" in n or "x2" in n:
        return "ganador"
    elif "btts" in n or "ambos marcan" in n:
        return "btts"
    elif "1t" in n or "2do tiempo" in n:
        return "tiempos"
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
        "leverkusen", "napoli", "sevilla", "betis", "athletic", "real sociedad",
        "villarreal", "sporting", "benfica", "porto", "braga", "chelsea",
        "manchester united", "tottenham", "aston villa", "newcastle", "roma",
        "atalanta", "lazio", "fiorentina", "bologna", "leipzig", "stuttgart",
        "frankfurt", "hoffenheim", "freiburg", "monaco", "marseille", "lille",
        "lyon", "nice", "lens", "psv", "ajax", "feyenoord", "az alkmaar",
        "club brugge", "anderlecht", "union sg", "gent", "genk", "galatasaray",
        "fenerbahce", "besiktas", "olympiacos", "paok", "panathinaikos", "aek",
        "rangers", "celtic", "slavia", "sparta praha", "plzen", "salzburg",
        "dinamo zagreb", "shakhtar", "palmeiras", "flamengo", "river plate",
        "boca juniors", "atletico mineiro", "sao paulo", "fluminense", "gremio",
        "botafogo", "corinthians", "racing", "independiente", "san lorenzo",
        "velez", "penarol", "nacional", "colo colo", "millonarios", "america de cali",
        "junior", "santa fe", "medellin", "tolima", "ldu quito", "independiente del valle",
        "cruzeiro", "vasco", "internacional", "olimpia", "cerro porteno", "libertad",
        "espana", "spain", "argentina", "brasil", "brazil", "francia", "france",
        "inglaterra", "england", "alemania", "germany", "portugal", "italia", "italy",
        "paises bajos", "netherlands", "colombia", "uruguay", "belgica", "belgium", "croacia", "croatia"
    ]
    return any(g in v_norm for g in gigantes_visitantes)


def seleccionar_par_distinto_familia(lista_candidatos, excluidos=None, familias_excluidas=None, tipo_filtro="FREE", registrar_memoria=True, tot_goles=2.5, **kwargs):
    if "actualizar_memoria" in kwargs:
        registrar_memoria = kwargs["actualizar_memoria"]
    if excluidos is None:
        excluidos = set()
    if familias_excluidas is None:
        familias_excluidas = set()

    historial_reciente = _MEMORIA_VARIEDAD_TARJETAS.get(tipo_filtro, [])[-4:]

    def _puntaje_rotacion(item):
        nom, prob, _ = item
        fam = obtener_familia(nom)
        penal_hist = 4.5 if nom in historial_reciente else 0.0
        # Evitar que Córners y Tarjetas monopolicen las tarjetas cuando hay mercados tácticos fuertes
        penal_familia = 3.2 if fam in {"corners", "tarjetas"} else 0.0
        return prob - penal_hist - penal_familia

    candidatos_rotados = sorted(lista_candidatos, key=_puntaje_rotacion, reverse=True)

    seleccion = []
    familias_usadas = set(familias_excluidas)

    # Primer pase: respeta exclusión de mercados y prohibición de repetir familia entre FREE y VIP
    for m in candidatos_rotados:
        if m[0] in excluidos:
            continue
        fam = obtener_familia(m[0])
        if fam in familias_usadas:
            continue
        # Prohibir colinealidad en la misma tarjeta (Córners+Tarjetas juntos, o Combo+Goles/Tiempos juntos)
        if (fam == "corners" and "tarjetas" in familias_usadas) or (fam == "tarjetas" and "corners" in familias_usadas):
            if len(candidatos_rotados) > 3:
                continue
        if (fam == "combo" and ("goles" in familias_usadas or "tiempos" in familias_usadas or "ganador" in familias_usadas)) or (
            fam in {"goles", "tiempos", "ganador"} and "combo" in familias_usadas
        ):
            continue
        # Regla #1 Anti-Doble Castigo: no juntar Over 1.5 (goles) + Gol 1T/2T (tiempos) en el mismo partido si tot_goles < 2.95
        if float(tot_goles or 2.5) < 2.95 and (
            (fam == "goles" and "tiempos" in familias_usadas) or (fam == "tiempos" and "goles" in familias_usadas)
        ):
            continue
        seleccion.append(m)
        familias_usadas.add(fam)
        if len(seleccion) == 2:
            break

    # Segundo pase: relaja exclusión de familias cruzadas salvo Córners y Tarjetas
    if len(seleccion) < 2:
        fams_internas = {obtener_familia(x[0]) for x in seleccion}
        for m in candidatos_rotados:
            if m[0] in excluidos or m in seleccion:
                continue
            fam = obtener_familia(m[0])
            if float(tot_goles or 2.5) < 2.95 and (
                (fam == "goles" and ("tiempos" in fams_internas or "tiempos" in familias_excluidas))
                or (fam == "tiempos" and ("goles" in fams_internas or "goles" in familias_excluidas))
            ):
                continue
            if fam not in fams_internas and not (fam in {"corners", "tarjetas", "tiempos", "goles"} and fam in familias_excluidas):
                seleccion.append(m)
                fams_internas.add(fam)
                if len(seleccion) == 2:
                    break

    # Tercer pase de emergencia: garantiza siempre 2 selecciones de distinta familia sin repetir picks de la otra tarjeta
    if len(seleccion) < 2:
        fams_internas = {obtener_familia(x[0]) for x in seleccion}
        for m in lista_candidatos:
            if m in seleccion or m[0] in excluidos:
                continue
            fam = obtener_familia(m[0])
            if float(tot_goles or 2.5) < 2.95 and fam in {"goles", "tiempos"} and (
                "goles" in fams_internas or "tiempos" in fams_internas or "goles" in familias_excluidas or "tiempos" in familias_excluidas
            ):
                continue
            if fam not in fams_internas:
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


def calcular_cuota_real_casa(prob, cuota_modelo=None, tipo_nivel="FREE", nombre_mercado=""):
    if prob is None or prob <= 0:
        return 1.25
    cuota_justa = 100.0 / prob
    base = float(cuota_modelo) if (cuota_modelo and cuota_modelo > 1.05) else (cuota_justa * 0.96)
    if tipo_nivel == "FREE":
        return round(max(1.18, min(1.28, base * 0.96)), 2)
    elif tipo_nivel == "VIP":
        n = str(nombre_mercado)
        if "Asiático > 2.25" in n or "BTTS" in n or "Ambos Marcan" in n or "Combo" in n or "Córners > 9.5" in n or "Remates Puerta > 8.5" in n or "Gol de " in n:
            piso_vip = 1.50
        elif "Remates Puerta > 7.5" in n or "Córners > 8.5" in n or "Goles " in n:
            piso_vip = 1.45
        elif "Remates Puerta > 6.5" in n or "Menos de 2.5" in n or "Faltas" in n:
            piso_vip = 1.42
        else:
            piso_vip = 1.38
        return round(max(piso_vip, min(1.88, max(base, cuota_justa * 1.02))), 2)
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


def generar_captura_automatica(res_m, tipo_filtro="DESCARTES"):
    imagen = cargar_lienzo_base()
    draw = ImageDraw.Draw(imagen, "RGBA")

    loc_str = res_m['local'].upper()
    vis_str = "VS " + res_m['visitante'].upper()

    fuente_alerta, fuente_marca, fuente_datos, fuente_datos_peq, fuente_datos_bold = cargar_fuentes_fijas()
    fuente_titulo = obtener_fuente_ajustada(draw, loc_str, "Montserrat-VariableFont_wght.ttf", 54, 950, tam_min=30)
    fuente_vs = obtener_fuente_ajustada(draw, vis_str, "Montserrat-VariableFont_wght.ttf", 41, 950, tam_min=26)

    c_blanco = (245, 245, 245, 255)
    c_gris = (185, 185, 185, 255)
    c_verde = (0, 255, 100, 255)
    c_oro = (255, 205, 0, 255)

    draw.text((60, 42), "ESCÁNER QUANT DATA", font=fuente_alerta, fill=c_verde)
    draw.text((60, 84), loc_str, font=fuente_titulo, fill=c_blanco)
    draw.text((60, 148), vis_str, font=fuente_vs, fill=c_gris)

    texto_fecha_hora = f"Fecha: {res_m['fecha']}  |  Hora: {res_m['hora']}"
    texto_liga = f"Liga: {res_m['liga_visual']}"
    f_liga = obtener_fuente_ajustada(draw, texto_liga, "RobotoMono-VariableFont_wght.ttf", 27, 950, tam_min=19)
    draw.text((60, 204), texto_fecha_hora, font=fuente_datos, fill=c_gris)
    draw.text((60, 240), texto_liga, font=f_liga, fill=c_gris)
    draw.line((60, 282, 1020, 282), fill=(85, 85, 85, 255), width=2)

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

    if tot_corn >= 10.1:
        p_c95, c_c95 = _prob_poisson_over(tot_corn, 9.5)
        lineas_corners_dinamicas = [
            ("Córners > 8.5", res_m.get('p_c85'), res_m.get('c_min_c85')),
            ("Córners > 9.5", p_c95, c_c95),
        ]
    else:
        lineas_corners_dinamicas = [
            ("Córners > 7.5", res_m.get('p_c75'), res_m.get('c_min_c75')),
            ("Córners > 8.5", res_m.get('p_c85'), res_m.get('c_min_c85')),
        ]

    if tot_tiros >= 8.2:
        p_t85, c_t85 = _prob_poisson_over(tot_tiros, 8.5)
        lineas_tiros_dinamicas = [
            ("Remates Puerta > 6.5", res_m.get('p_tiros65'), res_m.get('c_min_tiros65')),
            ("Remates Puerta > 7.5", res_m.get('p_tiros75'), res_m.get('c_min_tiros75')),
            ("Remates Puerta > 8.5", p_t85, c_t85),
        ]
    else:
        lineas_tiros_dinamicas = [
            ("Remates Puerta > 6.5", res_m.get('p_tiros65'), res_m.get('c_min_tiros65')),
            ("Remates Puerta > 7.5", res_m.get('p_tiros75'), res_m.get('c_min_tiros75')),
        ]

    # LOS 20 MERCADOS MATEMÁTICOS COMPLETOS CONECTADOS AL MOTOR
    mercados_brutos = [
        ("Over 1.5 Goles", res_m.get('p_15_match'), res_m.get('c_min_15')),
        ("Gol en 1T", res_m.get('p_05_ht'), res_m.get('c_min_05_ht')),
        ("Gol en 2do Tiempo", res_m.get('p_05_2t'), res_m.get('c_min_05_2t')),
        ("Ambos Marcan (BTTS)", res_m.get('p_btts'), res_m.get('c_min_btts')),
        ("Total Asiático > 2.25", res_m.get('p_asig225'), res_m.get('c_min_asig225')),
        ("Total Asiático > 2.75", res_m.get('p_asig275'), res_m.get('c_min_asig275')),
        ("Faltas Totales > 22.5", res_m.get('p_faltas22'), res_m.get('c_min_faltas22')),
        ("Doble Oport. 1X", res_m.get('p_1x'), res_m.get('c_min_1x')),
        ("Doble Oport. X2", res_m.get('p_x2'), res_m.get('c_min_x2')),
        ("Combo 1X + O1.5", res_m.get('p_combo_1x_over15'), res_m.get('c_min_combo_1x')),
        ("Combo X2 + O1.5", res_m.get('p_combo_x2_over15'), res_m.get('c_min_combo_x2')),
        ("Total Menos de 2.5 (Under)", res_m.get('p_under25'), res_m.get('c_min_under25')),
        ("Total Menos de 3.5 (Under)", res_m.get('p_under35'), res_m.get('c_min_under35')),
        *lineas_tiros_dinamicas,
        *lineas_corners_dinamicas,
        (f"Tarjetas > {res_m.get('linea_tarj', 3.5)}", res_m.get('p_t35'), res_m.get('c_min_t35')),
    ]

    if (res_m.get("p_h") or 0) >= 63.0:
        mercados_brutos.append((f"Victoria {res_m['local'][:12]}", res_m.get("p_h"), res_m.get("cuota_h")))
    if (res_m.get("p_a") or 0) >= 63.0:
        mercados_brutos.append((f"Victoria {res_m['visitante'][:12]}", res_m.get("p_a"), res_m.get("cuota_a")))
    if res_m.get("nombre_dom_goles") and (res_m.get("p_dom_goles") or 0) >= 62.0:
        mercados_brutos.append((res_m["nombre_dom_goles"], res_m.get("p_dom_goles"), res_m.get("c_min_dom_goles")))
    if res_m.get("nombre_dom_corn") and (res_m.get("p_dom_corn") or 0) >= 64.0:
        mercados_brutos.append((res_m["nombre_dom_corn"], res_m.get("p_dom_corn"), res_m.get("c_min_dom_corn")))
    if res_m.get("nombre_goleador") and (res_m.get("p_goleador") or 0) >= 62.0:
        mercados_brutos.append((res_m["nombre_goleador"], res_m.get("p_goleador"), res_m.get("c_min_goleador")))

    mercados_ritmo = []
    mercados_ganador_respaldo = []

    for nombre, prob, cuota_orig in mercados_brutos:
        if prob is None or cuota_orig is None or prob < 56.0:
            continue
        if "AMISTOSO" in liga_vis and ("Tarjetas" in nombre or "Faltas" in nombre):
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
            if tot_goles >= 2.20 or hay_favorito_claro or res_m.get("es_copa") or es_torneo_selecciones:
                continue
            if tipo_filtro == "VIP" and tot_goles >= 2.12:
                continue

        # 2. Prohibido recomendar Ambos Marcan (BTTS) cuando hay diferencia de nivel
        if nombre == "Ambos Marcan (BTTS)":
            if tot_goles < 2.55 or prob < 66.5 or hay_favorito_claro:
                continue

        # 3. Regla #3: Filtro Dixon-Coles exacto para Over 1.5 (si P(0-0)+P(1-0)+P(0-1) >= 27%, no priorizar Over 1.5)
        alta_friccion_cerrada = float(res_m.get("tot_faltas") or 22.0) >= 23.0 and abs(float(res_m.get("p_h", 50.0)) - float(res_m.get("p_a", 50.0))) < 18.0
        umbral_goles_o15 = 2.56 if (es_liga_cerrada or alta_friccion_cerrada or (not loc_protegido and not vis_protegido)) else 2.40
        riesgo_corto_dc = float(res_m.get("prob_marcador_corto") or 0.0)
        if nombre == "Over 1.5 Goles" and (tot_goles < umbral_goles_o15 or prob < 71.0 or riesgo_corto_dc >= 27.0):
            continue
        if nombre == "Total Asiático > 2.25" and tot_goles < 2.52:
            continue
        if nombre == "Total Asiático > 2.75" and tot_goles < 2.78:
            continue
        if nombre == "Gol en 1T" and (tot_goles < umbral_goles_o15 or prob < 67.0):
            continue
        if nombre == "Gol en 2do Tiempo" and (tot_goles < 2.38 or prob < 67.0):
            continue

        # 4. Regla #4: Prohibir X2 (visitante) cuando el local tiene >= 30% de ganar o juega en plaza hostil/altura (ej. Bosnia)
        if "Doble Oport." in nombre or "Combo " in nombre or "Victoria " in nombre:
            if "1X" in nombre and (vis_protegido and not loc_protegido or float(res_m.get("p_a", 0)) >= 40.0):
                continue
            if "X2" in nombre and (loc_protegido and not vis_protegido or float(res_m.get("p_h", 0)) >= 30.0 or res_m.get("es_plaza_hostil_local")):
                continue
            umbral_do = 71.0 if "X2" in nombre else (68.0 if "Doble Oport." in nombre else (65.0 if "Combo " in nombre else 70.0))
            if prob < umbral_do:
                continue
            mercados_ganador_respaldo.append((nombre, prob, cuota_orig))
            continue

        mercados_ritmo.append((nombre, prob, cuota_orig))

    # Ordenar por probabilidad + prioridad a mercados tácticos variados sobre Córners/Tarjetas
    todos_ordenados = sorted(
        mercados_ritmo + mercados_ganador_respaldo,
        key=lambda x: (x[1] - (3.0 if obtener_familia(x[0]) in {"corners", "tarjetas"} else 0.0)),
        reverse=True
    )

    exclusivos_vip_extremos = {
        "Remates Puerta > 7.5", "Remates Puerta > 8.5", "Córners > 9.5",
        "Total Asiático > 2.25", "Total Asiático > 2.75", "Total Menos de 2.5 (Under)",
        "Combo 1X + O1.5", "Combo X2 + O1.5"
    }
    if res_m.get("nombre_goleador"):
        exclusivos_vip_extremos.add(res_m["nombre_goleador"])

    lineas_bajas_irreales = {"Total Menos de 3.5 (Under)"} if tot_goles >= 2.25 else set()
    if tot_corn >= 9.6:
        lineas_bajas_irreales.add("Córners > 7.5")

    candidatos_free = [
        (m[0], min(86.5, m[1]), calcular_cuota_real_casa(m[1], m[2], "FREE", m[0]))
        for m in todos_ordenados
        if m[0] not in exclusivos_vip_extremos and m[0] not in lineas_bajas_irreales and m[1] >= 62.0
    ]
    if len(candidatos_free) < 2:
        candidatos_free = [
            (m[0], min(86.5, m[1]), calcular_cuota_real_casa(m[1], m[2], "FREE", m[0]))
            for m in todos_ordenados
            if m[0] not in exclusivos_vip_extremos
        ]

    # Familias ya usadas en la otra tarjeta del mismo partido (prohibido repetir Córners/Tarjetas y, si tot_goles < 2.95, goles <-> tiempos)
    fams_usadas_vip = {obtener_familia(m[0]) for m in res_m.get("seleccion_vip", [])}
    if tot_goles < 2.95 and ("goles" in fams_usadas_vip or "tiempos" in fams_usadas_vip):
        fams_usadas_vip.update({"goles", "tiempos"})

    top_2_free_base = seleccionar_par_distinto_familia(
        candidatos_free,
        excluidos={m[0] for m in res_m.get("seleccion_vip", [])},
        familias_excluidas=fams_usadas_vip,
        tipo_filtro="FREE",
        registrar_memoria=(tipo_filtro == "FREE"),
        tot_goles=tot_goles
    )

    if tipo_filtro == "FREE":
        top_2 = top_2_free_base
    elif tipo_filtro == "VIP":
        nombres_usados_free = {m[0] for m in top_2_free_base}
        fams_usadas_free = {obtener_familia(m[0]) for m in top_2_free_base}
        if tot_goles < 2.95 and ("goles" in fams_usadas_free or "tiempos" in fams_usadas_free):
            fams_usadas_free.update({"goles", "tiempos"})
        colchones_bajos = {"Córners > 7.5", "Total Menos de 3.5 (Under)"}
        excluidos_vip = nombres_usados_free.union(colchones_bajos)

        candidatos_vip = [
            (m[0], min(89.5, max(66.5, m[1])), calcular_cuota_real_casa(m[1], m[2], "VIP", m[0]))
            for m in todos_ordenados
            if m[1] >= 57.0 and m[0] not in excluidos_vip
        ]
        candidatos_vip.sort(
            key=lambda x: (
                obtener_familia(x[0]) not in fams_usadas_free,
                obtener_familia(x[0]) not in {"corners", "tarjetas"},
                x[2] >= 1.40,
                x[1]
            ),
            reverse=True
        )
        top_2 = seleccionar_par_distinto_familia(
            candidatos_vip,
            excluidos=excluidos_vip,
            familias_excluidas=fams_usadas_free,
            tipo_filtro="VIP",
            registrar_memoria=True,
            tot_goles=tot_goles
        )
    else:
        candidatos_desc = [
            (m[0], m[1], calcular_cuota_real_casa(m[1], m[2], "FREE", m[0]))
            for m in todos_ordenados
        ]
        top_2 = seleccionar_par_distinto_familia(candidatos_desc, tipo_filtro="DESCARTES", registrar_memoria=True, tot_goles=tot_goles)

    # Candado final variado (con Gol 2T, Remates, Faltas, Over 1.5 antes de Córners/Tarjetas)
    if len(top_2) < 2:
        do_segura_respaldo = (
            ("Doble Oport. 1X", float(res_m.get("p_1x") or 72.0), 1.22)
            if float(res_m.get("p_1x") or 0) >= float(res_m.get("p_x2") or 0)
            else ("Doble Oport. X2", float(res_m.get("p_x2") or 72.0), 1.22)
        )
        if tot_goles >= 2.35 or hay_favorito_claro:
            respaldo_fams = (
                [("Gol en 2do Tiempo", 76.5, 1.42), ("Remates Puerta > 6.5", 74.5, 1.44), ("Gol en 1T", 74.0, 1.42), ("Córners > 8.5", 73.5, 1.48), ("Faltas Totales > 22.5", 73.0, 1.42), (f"Tarjetas > {res_m.get('linea_tarj', 3.5)}", 72.0, 1.46)]
                if tipo_filtro == "VIP"
                else [("Over 1.5 Goles", 78.5, 1.24), ("Gol en 2do Tiempo", 77.0, 1.24), ("Remates Puerta > 6.5", 75.5, 1.24), ("Córners > 7.5", 74.5, 1.24), ("Faltas Totales > 22.5", 74.0, 1.24), do_segura_respaldo]
            )
        else:
            respaldo_fams = (
                [("Faltas Totales > 22.5", 74.5, 1.42), ("Córners > 8.5", 73.0, 1.48), (f"Tarjetas > {res_m.get('linea_tarj', 3.5)}", 72.5, 1.46)]
                if tipo_filtro == "VIP"
                else [("Faltas Totales > 22.5", 75.5, 1.24), ("Córners > 7.5", 74.5, 1.24), ("Total Menos de 3.5 (Under)", 78.0, 1.22)]
            )

        usados_actual = {m[0] for m in top_2}.union(
            {m[0] for m in res_m.get("seleccion_free", [])} if tipo_filtro == "VIP" else {m[0] for m in res_m.get("seleccion_vip", [])}
        )
        fams_actual = {obtener_familia(m[0]) for m in top_2}
        otra_sel = res_m.get("seleccion_free", []) if tipo_filtro == "VIP" else res_m.get("seleccion_vip", [])
        fams_otra = {obtener_familia(m[0]) for m in otra_sel}
        if tot_goles < 2.95 and ("goles" in fams_actual or "tiempos" in fams_actual or "goles" in fams_otra or "tiempos" in fams_otra):
            fams_actual.update({"goles", "tiempos"})
        for r_m in respaldo_fams:
            if r_m[0] not in usados_actual and obtener_familia(r_m[0]) not in fams_actual:
                top_2.append(r_m)
                fams_actual.add(obtener_familia(r_m[0]))
            if len(top_2) == 2:
                break

    res_m[f"seleccion_{tipo_filtro.lower()}"] = top_2

    linea_club_1, linea_club_2 = obtener_explicacion_apuesta_club(res_m)
    faltas_val = res_m.get('tot_faltas', 23.0)
    faltas_str = f"{faltas_val:.1f}" if isinstance(faltas_val, (int, float)) else "23.0"
    corn_val = res_m.get('tot_corn') or 8.6
    corn_str = f"{corn_val:.1f}" if isinstance(corn_val, (int, float)) else "8.6"

    draw.text((60, 296), "CONTEXTO TÁCTICO", font=fuente_datos_bold, fill=c_blanco)
    txt_perfil = f"  └─ Perfil: {contexto}"
    f_perf = obtener_fuente_ajustada(draw, txt_perfil, "RobotoMono-VariableFont_wght.ttf", 27, 950, tam_min=19)
    draw.text((60, 340), txt_perfil, font=f_perf, fill=c_gris)

    txt_metricas = f"  └─ Goles: {res_m.get('tot_goles', 0):.2f}  |  Córners: {corn_str}  |  Fricción: {faltas_str} faltas"
    f_met = obtener_fuente_ajustada(draw, txt_metricas, "RobotoMono-VariableFont_wght.ttf", 27, 950, tam_min=19)
    draw.text((60, 380), txt_metricas, font=f_met, fill=c_gris)

    draw.rectangle([(60, 424), (1020, 516)], fill=(25, 24, 18, 220), outline=(255, 205, 0, 145), width=2)
    dibujar_icono_bandera(draw, 78, 436, color_bandera=(255, 70, 70, 255))
    f_club_1 = obtener_fuente_ajustada(draw, linea_club_1, "RobotoMono-VariableFont_wght.ttf", 26, 895, tam_min=18)
    f_club_2 = obtener_fuente_ajustada(draw, linea_club_2, "RobotoMono-VariableFont_wght.ttf", 23, 895, tam_min=16)
    draw.text((108, 432), linea_club_1, font=f_club_1, fill=c_oro)
    draw.text((108, 474), linea_club_2, fill=c_blanco, font=f_club_2)

    y_pos = 540
    draw.text((60, y_pos), "PROYECCIONES DEL MODELO MATEMÁTICO", font=fuente_datos_bold, fill=c_verde)
    y_pos += 52

    for nombre, prob, cuota in top_2:
        if prob > 0:
            txt_op = f"  [+] {nombre}: {prob:.1f}%"
            f_op = obtener_fuente_ajustada(draw, txt_op, "Montserrat-VariableFont_wght.ttf", 34, 950, tam_min=22)
            txt_ind = f"      ➔ ÍNDICE DE VALOR > {cuota:.2f}"
            f_ind = obtener_fuente_ajustada(draw, txt_ind, "RobotoMono-VariableFont_wght.ttf", 29, 950, tam_min=20)
            draw.text((60, y_pos), txt_op, font=f_op, fill=c_blanco)
            y_pos += 44
            draw.text((60, y_pos), txt_ind, font=f_ind, fill=c_verde)
            y_pos += 56

    draw.line((60, 885, 1020, 885), fill=(65, 65, 65, 255), width=1)
    draw.text((60, 902), "@QuantBet22", font=fuente_marca, fill=(255, 255, 255, 110))
    draw.text((60, 966), "COMUNIDAD DE DATOS: @QuantBet22", font=fuente_datos_bold, fill=c_oro)

    nombre_carpeta = f"Alertas_Quant_{res_m['fecha']}"
    if not os.path.exists(nombre_carpeta):
        os.makedirs(nombre_carpeta)

    loc_limpio = "".join(c for c in res_m['local'][:5] if c.isalnum())
    vis_limpio = "".join(c for c in res_m['visitante'][:5] if c.isalnum())
    nombre_img = f"QuantBet_{loc_limpio}_{vis_limpio}_{tipo_filtro}.jpg"
    ruta_completa = os.path.join(nombre_carpeta, nombre_img)

    imagen_final = imagen.convert("RGB")
    imagen_final.save(ruta_completa, quality=98)
    return ruta_completa


def generar_tarjeta_combinada(fecha, titulo_combinada, subtitulo_nivel, lista_selecciones, cuota_total, prob_directa, prob_protegida, stake_sugerido, sufijo_archivo):
    imagen = cargar_lienzo_base()
    draw = ImageDraw.Draw(imagen, "RGBA")
    fuente_alerta, fuente_marca, fuente_datos, fuente_datos_peq, fuente_datos_bold = cargar_fuentes_fijas()
    titulo_seguro = titulo_combinada.upper().replace("VIP", "PRO").replace("COMBINADA", "MATRIZ")
    fuente_titulo = obtener_fuente_ajustada(draw, titulo_seguro, "Montserrat-VariableFont_wght.ttf", 50, 950, tam_min=30)
    fuente_vs = obtener_fuente_ajustada(draw, f"ÍNDICE CONJUNTO: > {cuota_total:.2f}x", "Montserrat-VariableFont_wght.ttf", 38, 950, tam_min=26)

    c_blanco = (245, 245, 245, 255)
    c_gris = (185, 185, 185, 255)
    c_verde = (0, 255, 100, 255)
    c_oro = (255, 205, 0, 255)

    sub_limpio = limpiar_emojis_fuente(subtitulo_nivel)
    draw.text((60, 44), sub_limpio, font=fuente_alerta, fill=c_oro)
    draw.text((60, 88), titulo_seguro, font=fuente_titulo, fill=c_blanco)
    draw.text((60, 152), f"ÍNDICE CONJUNTO: > {cuota_total:.2f}x", font=fuente_vs, fill=c_verde)
    draw.text((60, 206), f"Fecha: {fecha}   |   Metodología: Partidos distintos", font=fuente_datos, fill=c_gris)
    draw.line((60, 250, 1020, 250), fill=(90, 90, 90, 255), width=2)

    draw.text((60, 268), "PARÁMETROS DE CONFIANZA", font=fuente_datos_bold, fill=c_blanco)
    txt_ef = f"  └─ Probabilidad Conjunta: {prob_protegida:.1f}% (Base: {prob_directa:.1f}%)"
    txt_gb = "  └─ Nivel de Confluencia: Alta Estabilidad Estadística"
    f_ef = obtener_fuente_ajustada(draw, txt_ef, "RobotoMono-VariableFont_wght.ttf", 26, 950, tam_min=18)
    f_gb = obtener_fuente_ajustada(draw, txt_gb, "RobotoMono-VariableFont_wght.ttf", 26, 950, tam_min=18)
    draw.text((60, 308), txt_ef, font=f_ef, fill=c_verde)
    draw.text((60, 344), txt_gb, font=f_gb, fill=c_oro)

    y_pos = 394
    draw.text((60, y_pos), "ESCENARIOS SELECCIONADOS:", font=fuente_datos_bold, fill=c_blanco)
    y_pos += 44

    for idx, item in enumerate(lista_selecciones, start=1):
        partido_txt = f"{idx}. {item['partido']} ({item['hora']})"
        mercado_txt = f"   [+] {item['mercado']} ({item['prob']:.1f}%)"
        cuota_txt = f"       ➔ Índice Individual: > {item['cuota']:.2f}"

        f_part = obtener_fuente_ajustada(draw, partido_txt, "Montserrat-VariableFont_wght.ttf", 29, 950, tam_min=19)
        f_merc = obtener_fuente_ajustada(draw, mercado_txt, "RobotoMono-VariableFont_wght.ttf", 26, 950, tam_min=18)
        draw.text((60, y_pos), partido_txt, font=f_part, fill=c_blanco)
        y_pos += 36
        draw.text((60, y_pos), mercado_txt, font=f_merc, fill=c_verde)
        y_pos += 32
        draw.text((60, y_pos), cuota_txt, font=fuente_datos_peq, fill=c_gris)
        y_pos += 40

    draw.line((60, 885, 1020, 885), fill=(65, 65, 65, 255), width=1)
    draw.text((60, 902), "@QuantBet22", font=fuente_marca, fill=(255, 255, 255, 110))
    draw.text((60, 966), "COMUNIDAD DE DATOS: @QuantBet22", font=fuente_datos_bold, fill=c_oro)

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
    if datos.get("nombre_goleador") and (datos.get("p_goleador") or 0) >= 64.0:
        if str(tipo_alerta).upper() == "VIP":
            extras.append((datos["nombre_goleador"], float(datos["p_goleador"]), max(1.45, float(datos.get("c_min_goleador", 1.55)))))
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
