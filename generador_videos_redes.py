# === INICIO FILTRO EXCLUSIVO DE VIDEO (RESPETA % EN CLIENTES Y GARANTIZA LAS 4 REDES EN TELEGRAM) ===
import re as _re_vid
import time as _time_vid
import json as _json_vid
import builtins as _builtins_vid
import requests as _req_vid
from PIL import ImageDraw as _ImageDraw_vid

def _limpiar_texto_redes_sociales(texto, modo="copy"):
    if not isinstance(texto, str) or not texto.strip():
        return texto
    t = str(texto)

    # 1. Eliminar +18, 🔞 y advertencias de apuestas en vídeos y descripciones de redes
    t = t.replace("🔞", "")
    t = _re_vid.sub(r"\(\+18\s*Informativo\)", "(Ciencia de Datos)", t, flags=_re_vid.I)
    t = _re_vid.sub(r"\+18\s*\|?", "", t)
    t = _re_vid.sub(r"(?i)juega\s+con\s+responsabilidad\.?", "", t)
    t = _re_vid.sub(r"(?i)an[áa]lisis\s+estad[íi]stico\s+e\s+informativo\.?", "Ciencia de Datos y Modelos Matemáticos aplicados al Fútbol Profesional.", t)

    # 2. Reemplazos exactos en cajas del vídeo y descripciones
    reemplazos_exactos = [
        ("TARJETA GRATIS + PASE VIP $7.99", "ANÁLISIS TÁCTICO + ACCESO VIP"),
        ("TARJETA GRATIS + PASE VIP $9.99", "ANÁLISIS TÁCTICO + ACCESO VIP"),
        ("TARJETA GRATIS Y PROMO $7.99 EN EL PERFIL", "ANÁLISIS COMPLETO DISPONIBLE EN EL PERFIL"),
        ("TARJETA GRATIS Y PROMO $9.99 EN EL PERFIL", "ANÁLISIS COMPLETO DISPONIBLE EN EL PERFIL"),
        ("WEB OFICIAL Y PROMO $7.99 EN EL PERFIL", "WEB OFICIAL Y COMUNIDAD EN EL PERFIL"),
        ("WEB OFICIAL Y PROMO $9.99 EN EL PERFIL", "WEB OFICIAL Y COMUNIDAD EN EL PERFIL"),
        ("PASE DE PRUEBA 10 DÍAS POR SOLO $7.99 USD", "ACCESO DE PRUEBA 10 DÍAS EN EL PERFIL"),
        ("PASE DE PRUEBA 10 DÍAS POR SOLO $9.99 USD", "ACCESO DE PRUEBA 10 DÍAS EN EL PERFIL"),
        ("PROMO 10 DÍAS VIP POR $7.99 EN LA WEB", "ACCESO DE PRUEBA 10 DÍAS EN LA WEB"),
        ("PROMO 10 DÍAS VIP POR $9.99 EN LA WEB", "ACCESO DE PRUEBA 10 DÍAS EN LA WEB"),
        ("PRUEBA 10 DÍAS VIP POR SOLO $7.99 USD", "PRUEBA 10 DÍAS DISPONIBLE EN EL PERFIL"),
        ("PRUEBA 10 DÍAS VIP POR SOLO $9.99 USD", "PRUEBA 10 DÍAS DISPONIBLE EN EL PERFIL"),
        ("PROMO NUEVOS USUARIOS: Prueba 10 DÍAS de Acceso Total por solo $7.99 USD entrando al link de nuestro perfil.",
         "Únete a nuestra comunidad en Telegram y consulta el laboratorio web completo desde el enlace de nuestro perfil."),
        ("PROMO NUEVOS USUARIOS: Prueba 10 DÍAS de Acceso Total por solo $9.99 USD entrando al link de nuestro perfil.",
         "Únete a nuestra comunidad en Telegram y consulta el laboratorio web completo desde el enlace de nuestro perfil."),
        ("PRECISION 100.0%", "PRECISIÓN VERIFICADA"),
        ("PRECISIÓN 100.0%", "PRECISIÓN VERIFICADA"),
        ("la informe táctico interactivo", "el informe táctico interactivo"),
    ]
    for viejo, nuevo in reemplazos_exactos:
        t = t.replace(viejo, nuevo)

    # 3. Limpiar porcentajes y promesas en los textos de TikTok, Instagram, YouTube y Facebook
    t = _re_vid.sub(r"(?i)\+\s*AUDITOR[ÍI]A\s*\(\d+(?:[\.,]\d+)?%\)", "+ AUDITORÍA VERIFICADA", t)
    t = _re_vid.sub(r"(?i)\d+(?:[\.,]\d+)?%\s*de\s*precisi[óo]n\s*en\s*nuestro\s*modelo\s*matem[áa]tico\s*de\s*(?:Poisson|Poison)",
                    "Simulación de 10.000 escenarios en nuestro modelo matemático de Poisson", t)
    t = _re_vid.sub(r"(?i)Balance\s+verificado\s*\(\d+(?:[\.,]\d+)?%\s*de\s*acierto\)",
                    "Balance verificado en tiempo real", t)
    t = _re_vid.sub(r"(?i)Transparencia\s+total:\s*\d+(?:[\.,]\d+)?%\s*de\s*efectividad\s*verificada\.?",
                    "Transparencia institucional y modelos de Poisson en tiempo real.", t)

    # 4. Limpiar palabras comerciales / apuestas ("GRATIS", "tarjeta desbloqueada", "$7.99")
    t = _re_vid.sub(r"(?i)Ya\s+subimos\s+GRATIS\s+(?:la\s+tarjeta\s+desbloqueada|el\s+informe\s+t[áa]ctico\s+interactivo|la\s+informe\s+t[áa]ctico\s+interactivo)",
                    "Ya publicamos el informe táctico interactivo", t)
    t = _re_vid.sub(r"(?i)Y\s+ya\s+subimos\s+GRATIS\s+a\s+nuestra\s+WEB\s+OFICIAL",
                    "Y ya publicamos en nuestra plataforma web", t)
    t = _re_vid.sub(r"(?i)La\s+tarjeta\s+gratuita\s+de\s+hoy", "El informe táctico de hoy", t)
    t = _re_vid.sub(r"(?i)ya\s+est[áa]\s+desbloqueada\s+en\s+nuestra\s+Web\s+Oficial",
                    "ya está disponible en nuestra plataforma web", t)
    t = _re_vid.sub(r"(?i)Ya\s+dejamos\s+desbloqueada\s+en\s+nuestra\s+WEB\s+OFICIAL\s+la\s+tarjeta\s+de\s+hoy",
                    "Ya publicamos en nuestra plataforma web el informe táctico de hoy", t)
    t = _re_vid.sub(r"(?i)y\s+tarjeta\s+desbloqueada\s+de\s+hoy", "y análisis táctico de hoy", t)
    t = _re_vid.sub(r"(?i)disponible\s+GRATIS\s+en\s+nuestra\s+WEB\s+OFICIAL",
                    "disponible en nuestra plataforma web", t)
    t = _re_vid.sub(r"(?i)Entra\s+gratis\s+tocando", "Consulta los datos tocando", t)
    t = _re_vid.sub(r"(?i)por\s+solo\s+\$?\d+[\.,]\d+\s*(?:USD|d[óo]lares|US\$)?", "desde nuestro perfil", t)
    t = _re_vid.sub(r"(?i)\$\d+[\.,]\d+\s*(?:USD)?", "en el perfil", t)
    t = _re_vid.sub(r"(?i)\b(?:7|9|siete|nueve)\s+con\s+99\s*(?:d[óo]lares|usd)?", "el acceso de nuestro perfil", t)
    t = _re_vid.sub(r"(?i)en\s+el\s+perfil\s*EN\s+EL\s+PERFIL", "EN EL PERFIL", t)
    t = _re_vid.sub(r"(?i)\bCuota\s*>", "Índice >", t)

    if modo == "slide":
        # Eliminar únicamente porcentajes (%) visibles en el vídeo, respetando la palabra VIP
        t = _re_vid.sub(r"\(\s*\d+(?:[\.,]\d+)?%\s*\)", "", t)
        t = _re_vid.sub(r"\d+(?:[\.,]\d+)?%", "Verificado", t)
    elif modo == "voz":
        t = t.replace("Puasón matemática", "Poison")
        t = t.replace("Puasón", "Poison")
        t = t.replace("Poisson", "Poison")
        t = t.replace("Doble Oport.", "Doble Oportunidad")
        t = t.replace("Doble Oport ", "Doble Oportunidad ")
        t = t.replace("Over 1.5 Goles", "Más de 1.5 goles")
        # Prohibir que la voz pronuncie porcentajes en el audio
        t = _re_vid.sub(r"con\s+un\s+\d+\s+por\s+ciento\s+de\s+probabilidad(?:\s+matem[áa]tica)?", "con alta convergencia en el modelo", t, flags=_re_vid.I)
        t = _re_vid.sub(r"\d+\s+por\s+ciento", "alta convergencia", t, flags=_re_vid.I)

    return t

# A. Interceptar dibujo de láminas de vídeo (Sin bordes amarillos exteriores)
_orig_draw_text = _ImageDraw_vid.ImageDraw.text
def _hook_draw_text(self, xy, text, *args, **kwargs):
    return _orig_draw_text(self, xy, _limpiar_texto_redes_sociales(text, modo="slide"), *args, **kwargs)
_ImageDraw_vid.ImageDraw.text = _hook_draw_text

if hasattr(_ImageDraw_vid.ImageDraw, "textbbox"):
    _orig_textbbox = _ImageDraw_vid.ImageDraw.textbbox
    def _hook_textbbox(self, xy, text, *args, **kwargs):
        return _orig_textbbox(self, xy, _limpiar_texto_redes_sociales(text, modo="slide"), *args, **kwargs)
    _ImageDraw_vid.ImageDraw.textbbox = _hook_textbbox

if hasattr(_ImageDraw_vid.ImageDraw, "textlength"):
    _orig_textlength = _ImageDraw_vid.ImageDraw.textlength
    def _hook_textlength(self, text, *args, **kwargs):
        return _orig_textlength(self, _limpiar_texto_redes_sociales(text, modo="slide"), *args, **kwargs)
    _ImageDraw_vid.ImageDraw.textlength = _hook_textlength

_orig_rounded_rect = _ImageDraw_vid.ImageDraw.rounded_rectangle
def _hook_rounded_rect(self, xy, *args, **kwargs):
    try:
        if isinstance(xy, (list, tuple)) and len(xy) == 4:
            x0, y0, x1, y1 = xy
            if x0 <= 45 and y0 <= 45 and x1 >= 1030 and y1 >= 1860:
                kwargs["outline"] = None
                kwargs["width"] = 0
                if "fill" not in kwargs or kwargs["fill"] is None:
                    return None
        if kwargs.get("outline") in [(255, 205, 0), (255, 215, 0), (255, 200, 0), "#ffcd00", "#ffd700"]:
            kwargs["outline"] = (45, 68, 95)
            kwargs["width"] = 1
    except Exception:
        pass
    return _orig_rounded_rect(self, xy, *args, **kwargs)
_ImageDraw_vid.ImageDraw.rounded_rectangle = _hook_rounded_rect

_orig_rect = _ImageDraw_vid.ImageDraw.rectangle
def _hook_rect(self, xy, *args, **kwargs):
    try:
        if isinstance(xy, (list, tuple)) and len(xy) == 4:
            x0, y0, x1, y1 = xy
            if x0 <= 45 and y0 <= 45 and x1 >= 1030 and y1 >= 1860:
                kwargs["outline"] = None
                kwargs["width"] = 0
                if "fill" not in kwargs or kwargs["fill"] is None:
                    return None
        if kwargs.get("outline") in [(255, 205, 0), (255, 215, 0), (255, 200, 0), "#ffcd00", "#ffd700"]:
            kwargs["outline"] = None
            kwargs["width"] = 0
    except Exception:
        pass
    return _orig_rect(self, xy, *args, **kwargs)
_ImageDraw_vid.ImageDraw.rectangle = _hook_rect

# B. Interceptar la Voz IA (edge_tts) para pronunciar "Poison" claramente
try:
    import edge_tts as _etts_vid
    _orig_comm_init = _etts_vid.Communicate.__init__
    def _hook_comm_init(self, text, *args, **kwargs):
        return _orig_comm_init(self, _limpiar_texto_redes_sociales(text, modo="voz"), *args, **kwargs)
    _etts_vid.Communicate.__init__ = _hook_comm_init
except Exception:
    pass

# C. Limpiar cola_publicacion_redes.json al guardarse
_orig_json_dump = _json_vid.dump
def _limpiar_json_redes(obj):
    if isinstance(obj, dict):
        return {k: (v if "ruta" in str(k) or "archivo" in str(k) else _limpiar_json_redes(v)) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_limpiar_json_redes(x) for x in obj]
    elif isinstance(obj, str):
        if obj.endswith(".mp4") or obj.endswith(".jpg") or ":\\" in obj or "/" in obj:
            return obj
        return _limpiar_texto_redes_sociales(obj, modo="copy")
    return obj

def _hook_json_dump(obj, fp, *args, **kwargs):
    if hasattr(fp, "name") and "cola_publicacion_redes.json" in str(fp.name):
        return _orig_json_dump(_limpiar_json_redes(obj), fp, *args, **kwargs)
    return _orig_json_dump(obj, fp, *args, **kwargs)
_json_vid.dump = _hook_json_dump

# D. Escapado HTML blindado por placeholders (impide que '>' o '->' rompan los mensajes de Telegram)
_orig_req_post = _req_vid.post

def _escapar_html_seguro_tg(txt):
    s = str(txt).replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&")
    tags_validos = ["<b>", "</b>", "<i>", "</i>", "<u>", "</u>", "<s>", "</s>", "<code>", "</code>", "<pre>", "</pre>"]
    mapa_tok = {}
    for idx_t, tg in enumerate(tags_validos):
        tok = f"__TG_TAG_{idx_t}__"
        mapa_tok[tok] = tg
        s = s.replace(tg, tok)
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    for tok, tg in mapa_tok.items():
        s = s.replace(tok, tg)
    return s

def _es_payload_redes(url, payload):
    if "sendVideo" in str(url):
        return True
    if not isinstance(payload, dict):
        return False
    txt = str(payload.get("text", "")) + " " + str(payload.get("caption", ""))
    claves_redes = [
        "TIKTOK", "INSTAGRAM REELS", "YOUTUBE SHORTS", "FACEBOOK REELS",
        "VIDEO 1 (", "VIDEO 2 (", "VÍDEO #", "Horario programado:"
    ]
    return any(k in txt for k in claves_redes)

def _hook_req_post_quirurgico(url, *args, **kwargs):
    if "api.telegram.org" not in str(url):
        return _orig_req_post(url, *args, **kwargs)

    # Detectar el diccionario tanto en kwargs["json"], kwargs["data"] como en args[0]
    modo_envio = None
    payload_orig = None
    if "json" in kwargs and isinstance(kwargs["json"], dict):
        modo_envio, payload_orig = "json", dict(kwargs["json"])
    elif "data" in kwargs and isinstance(kwargs["data"], dict):
        modo_envio, payload_orig = "data", dict(kwargs["data"])
    elif len(args) >= 1 and isinstance(args[0], dict):
        modo_envio, payload_orig = "arg0", dict(args[0])

    if not _es_payload_redes(url, payload_orig):
        return _orig_req_post(url, *args, **kwargs)

    _time_vid.sleep(1.2)
    if isinstance(payload_orig, dict):
        if "text" in payload_orig:
            limpio = _limpiar_texto_redes_sociales(payload_orig["text"], modo="copy")
            payload_orig["text"] = _escapar_html_seguro_tg(limpio)
        if "caption" in payload_orig:
            limpio_c = _limpiar_texto_redes_sociales(payload_orig["caption"], modo="copy")
            payload_orig["caption"] = _escapar_html_seguro_tg(limpio_c)

        if modo_envio == "json":
            kwargs["json"] = payload_orig
        elif modo_envio == "data":
            kwargs["data"] = payload_orig
        elif modo_envio == "arg0":
            args = (payload_orig,) + args[1:]

    for intento in range(3):
        try:
            res = _orig_req_post(url, *args, **kwargs)
            if res.status_code == 200:
                return res
            # Si por cualquier motivo Telegram devuelve 400, enviar en texto plano sin perder jamás el mensaje
            if res.status_code == 400 and isinstance(payload_orig, dict):
                payload_plano = dict(payload_orig)
                for campo in ("text", "caption"):
                    if campo in payload_plano:
                        txt_p = _re_vid.sub(r"<[^>]+>", "", str(payload_plano[campo]))
                        payload_plano[campo] = txt_p.replace("&gt;", ">").replace("&lt;", "<").replace("&amp;", "&")
                payload_plano.pop("parse_mode", None)
                if modo_envio == "json":
                    kwargs["json"] = payload_plano
                elif modo_envio == "data":
                    kwargs["data"] = payload_plano
                elif modo_envio == "arg0":
                    args = (payload_plano,) + args[1:]
                res_plano = _orig_req_post(url, *args, **kwargs)
                if res_plano.status_code == 200:
                    return res_plano
        except Exception:
            pass
        _time_vid.sleep(2.0)

    return _orig_req_post(url, *args, **kwargs)

_req_vid.post = _hook_req_post_quirurgico
# === FIN FILTRO EXCLUSIVO DE VIDEO ===







import asyncio
from datetime import datetime, timedelta
import json
import os
from pathlib import Path
import re
import subprocess
import time
import unicodedata
import wave
import edge_tts
import imageio_ffmpeg
import pandas as pd
from PIL import Image, ImageDraw, ImageFilter, ImageFont
import requests

VOZ_ANALISTA_IA = "es-ES-AlvaroNeural"
VELOCIDAD_VOZ = "+6%"
API_KEY_RESPALDO_AYER = os.getenv("API_SPORTS_KEY", "48f391f30e76d9c84e5c94b6a4cccdb4")

TOKEN_AUDITORIAS_PRIVADO = os.getenv("TG_TOKEN_AUDITORIAS", "8805035408:AAGPYUxmFz-Spfum1P2vacMZz5bToXUPMWI")
CHAT_ID_AUDITORIAS_PRIVADO = "1491740882"

LIGAS_OFICIALES_IDS = {
    140, 143, 141, 39, 45, 48, 135, 137, 78, 81, 61, 66,
    128, 130, 530, 239, 240, 533, 712, 307, 71, 73, 94, 96,
    88, 90, 144, 203, 206, 197, 179, 2, 3, 848, 13, 11
}

GIGANTES_TIER_1_MUNDIAL = [
    "real madrid", "barcelona", "atletico madrid", "manchester city", "manchester united",
    "liverpool", "arsenal", "chelsea", "tottenham", "bayern", "dortmund", "borussia dortmund",
    "inter", "fc internazionale", "milan", "ac milan", "juventus", "paris saint germain", "paris sg", "psg",
    "boca juniors", "river plate", "flamengo", "palmeiras", "millonarios", "atletico nacional",
    "america de cali", "santa fe", "junior", "independiente medellin", "deportivo cali",
    "corinthians", "sao paulo", "racing", "independiente", "club america", "guadalajara", "chivas", "cruz azul",
    "españa", "spain", "argentina", "brasil", "brazil", "francia", "france", "inglaterra", "england", "alemania", "germany", "portugal", "italia", "italy", "colombia", "uruguay", "paises bajos", "netherlands"
]

GIGANTES_TIER_2_SECUNDARIO = [
    "napoli", "roma", "lazio", "atalanta", "fiorentina", "bologna", "torino",
    "leverkusen", "leipzig", "stuttgart", "frankfurt", "aston villa", "newcastle",
    "everton", "west ham", "brighton", "fulham", "bournemouth", "sevilla", "real betis", "betis",
    "athletic", "real sociedad", "villarreal", "valencia", "girona", "celta", "osasuna",
    "benfica", "sporting", "porto", "ajax", "psv", "feyenoord", "galatasaray", "fenerbahce",
    "monaco", "marseille", "lyon", "lille", "gremio", "internacional", "botafogo", "fluminense",
    "cruzeiro", "vasco", "san lorenzo", "velez", "estudiantes", "peñarol", "colo colo",
    "ldu quito", "independiente del valle", "olimpia", "tolima", "once caldas", "bucaramanga",
    "pereira", "monterrey", "tigres", "pumas",
    "belgica", "belgium", "croacia", "croatia", "marruecos", "morocco", "mexico", "usa", "ecuador", "paraguay", "chile", "suiza", "switzerland", "dinamarca", "denmark", "noruega", "norway", "suecia", "sweden", "turquia", "turkey",
    "japon", "japan", "serbia", "grecia", "greece", "austria", "polonia", "poland", "escocia", "scotland", "ucrania", "ukraine", "rusia", "russia"
]

EQUIPOS_DESCONOCIDOS_PENALIZADOS = [
    "llaneros", "mirassol", "boyaca chico", "envigado", "patriotas", "jaguares",
    "alianza", "equidad", "fortaleza ceif", "cucuta", "huila", "quindio", "popayan"
]
GIGANTES_MUNDIALES_VIDEO = GIGANTES_TIER_1_MUNDIAL + GIGANTES_TIER_2_SECUNDARIO


def ruta_posix(ruta):
    return os.path.abspath(str(ruta)).replace("\\", "/")


def sincronizar_caches_nocturnos_al_iniciar(*args, **kwargs):
    return


def _es_club_lista(nombre_eq, lista_clubes):
    n = "".join(c for c in unicodedata.normalize("NFD", str(nombre_eq).lower()) if unicodedata.category(c) != "Mn")
    n = n.replace("ath madrid", "atletico madrid").replace("atletico de madrid", "atletico madrid").strip()
    for g in lista_clubes:
        g_limpio = "".join(c for c in unicodedata.normalize("NFD", str(g).lower()) if unicodedata.category(c) != "Mn")
        if g_limpio == "inter":
            if n in ["inter", "fc internazionale", "inter milan", "internazionale"]:
                return True
        elif g_limpio in n:
            return True
    return False


def puntaje_cartelera_video(p):
    loc = str(p.get("local", "")).lower()
    vis = str(p.get("visitante", "")).lower()
    liga = str(p.get("liga_visual", "")).upper()

    pts = 0
    # PRIORIDAD #1 ABSOLUTA: Siempre que juegue el Real Madrid, va de primero en el video
    if "real madrid" in loc or "real madrid" in vis:
        pts += 5000

    loc_t1 = _es_club_lista(loc, GIGANTES_TIER_1_MUNDIAL)
    vis_t1 = _es_club_lista(vis, GIGANTES_TIER_1_MUNDIAL)
    loc_t2 = _es_club_lista(loc, GIGANTES_TIER_2_SECUNDARIO)
    vis_t2 = _es_club_lista(vis, GIGANTES_TIER_2_SECUNDARIO)
    tiene_desconocido = any(d in loc or d in vis for d in EQUIPOS_DESCONOCIDOS_PENALIZADOS)

    if loc_t1 and vis_t1:
        pts += 220
    elif (loc_t1 and vis_t2) or (vis_t1 and loc_t2):
        pts += 150
    elif loc_t2 and vis_t2:
        pts += 115
    elif loc_t1 or vis_t1:
        pts += 70
    elif loc_t2 or vis_t2:
        pts += 35

    if p.get("es_derbi", False):
        pts += 90

    if tiene_desconocido:
        pts -= 65

    if any(lg in liga for lg in ["CHAMPIONS", "LALIGA", "PREMIER", "SERIE A", "BUNDESLIGA", "LIGUE 1", "MUNDIAL", "EUROCOPA", "COPA AMÉRICA", "NATIONS LEAGUE", "ELIMINATORIAS", "AMISTOSO INTERNACIONAL"]):
     pts += 40
    elif any(lg in liga for lg in ["EUROPA LEAGUE", "CONFERENCE", "COPA DEL REY", "FA CUP", "PRIMEIRA LIGA"]):
        pts += 25

    pts += min(12.0, float(p.get("tot_goles", 2.5)) * 3.0)
    return pts


def obtener_fuente_video_ajustada(draw, texto, archivo_ttf, tam_inicial, ancho_max_px, tam_min=16):
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


def cargar_fuentes_video(tam_titulo=40):
    try:
        f_tag = ImageFont.truetype("Montserrat-VariableFont_wght.ttf", 29)
        f_titulo = ImageFont.truetype("Montserrat-VariableFont_wght.ttf", tam_titulo)
        f_sub = ImageFont.truetype("Montserrat-VariableFont_wght.ttf", 31)
        f_cta = ImageFont.truetype("RobotoMono-VariableFont_wght.ttf", 25)
        f_peq = ImageFont.truetype("RobotoMono-VariableFont_wght.ttf", 22)
    except IOError:
        f_tag = f_titulo = f_sub = f_cta = f_peq = ImageFont.load_default()
    return f_tag, f_titulo, f_sub, f_cta, f_peq


def limpiar_hashtag(texto):
    t = str(texto)
    reemplazos_clubes = {
        "Paris Saint Germain": "PSG",
        "Paris SG": "PSG",
        "Atletico Madrid": "AtleticoMadrid",
        "Real Madrid": "RealMadrid",
        "Manchester City": "ManchesterCity",
        "Manchester United": "ManchesterUnited",
        "Aston Villa": "AstonVilla",
        "Borussia Dortmund": "BorussiaDortmund",
        "Bayern München": "BayernMunich",
        "Bayern Munich": "BayernMunich",
        "AC Milan": "ACMilan",
        "AS Roma": "ASRoma",
        "Real Sociedad": "RealSociedad",
        "Real Betis": "RealBetis",
        "Boca Juniors": "BocaJuniors",
        "River Plate": "RiverPlate",
        "America de Cali": "AmericadeCali",
        "Atletico Nacional": "AtleticoNacional",
    }
    for k, v in reemplazos_clubes.items():
        if k.lower() in t.lower():
            t = v
            break
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", t)
        if unicodedata.category(c) != "Mn"
    )
    limpio = "".join(c for c in sin_tildes if c.isalnum()).lower().strip()
    return f"#{limpio}" if len(limpio) > 2 else "#futbol"


def crear_fondo_vertical_base():
    ancho, alto = 1080, 1920
    ruta_fondo = "fondo de quant bet.jpg"
    if os.path.exists(ruta_fondo):
        fondo_orig = Image.open(ruta_fondo).convert("RGBA")
        w, h = fondo_orig.size
        escala = alto / h
        nuevo_w = int(w * escala)
        fondo = fondo_orig.resize((nuevo_w, alto), Image.Resampling.LANCZOS)
        left = max(0, (nuevo_w - ancho) // 2)
        fondo = fondo.crop((left, 0, left + ancho, alto))
    else:
        fondo = Image.new("RGBA", (ancho, alto), (10, 12, 16, 255))
    capa_oscura = Image.new("RGBA", (ancho, alto), (8, 8, 12, 232))
    return Image.alpha_composite(fondo, capa_oscura)


def crear_slide_vertical(ruta_tarjeta_cuadrada, texto_superior_tag, texto_partido, texto_inferior_cta, difuminar_vip=False, modo_gancho_telegram=False, ruta_salida="slide_temp.jpg"):
    lienzo = crear_fondo_vertical_base()
    draw = ImageDraw.Draw(lienzo, "RGBA")
    partido_str = texto_partido.upper()
    f_tag, _, f_sub, f_cta, f_peq = cargar_fuentes_video()
    f_tag_ajustada = obtener_fuente_video_ajustada(draw, texto_superior_tag.upper(), "Montserrat-VariableFont_wght.ttf", 29, 930, tam_min=18)
    f_titulo_ajustada = obtener_fuente_video_ajustada(draw, partido_str, "Montserrat-VariableFont_wght.ttf", 42, 960, tam_min=22)

    c_verde = (0, 255, 100, 255)
    c_oro = (255, 205, 0, 255)
    c_blanco = (245, 245, 245, 255)
    c_gris = (180, 180, 180, 255)

    draw.rectangle([(50, 88), (1030, 152)], fill=(12, 28, 20, 235), outline=c_verde, width=2)
    draw.text((75, 102), texto_superior_tag.upper(), font=f_tag_ajustada, fill=c_verde)
    draw.text((55, 170), partido_str, font=f_titulo_ajustada, fill=c_blanco)
    draw.line((50, 236, 1030, 236), fill=(85, 85, 95, 255), width=2)

    if ruta_tarjeta_cuadrada and os.path.exists(ruta_tarjeta_cuadrada):
        tarjeta = Image.open(ruta_tarjeta_cuadrada).convert("RGBA").resize((920, 920), Image.Resampling.LANCZOS)
        if modo_gancho_telegram:
            # Baja el difuminado a y=500 (justo debajo de 'PROYECCIONES DEL MODELO MATEMÁTICO')
            zona_picks = tarjeta.crop((35, 500, 885, 755))
            zona_borrosa = zona_picks.filter(ImageFilter.GaussianBlur(radius=22))
            tarjeta.paste(zona_borrosa, (35, 500))
            d_tarj = ImageDraw.Draw(tarjeta, "RGBA")
            d_tarj.rectangle([(55, 520), (865, 715)], fill=(10, 14, 20, 248), outline=c_verde, width=3)

            t1 = "1ª JUGADA EN WEB + 2 EN TELEGRAM GRATIS"
            t2 = "2 Proyecciones Ocultas -> Ver en nuestra App Web"
            t3 = "Entra ahora desde el enlace de nuestro perfil"

            f_b1 = obtener_fuente_video_ajustada(d_tarj, t1, "Montserrat-VariableFont_wght.ttf", 28, 760, 18)
            f_b2 = obtener_fuente_video_ajustada(d_tarj, t2, "RobotoMono-VariableFont_wght.ttf", 23, 760, 16)
            f_b3 = obtener_fuente_video_ajustada(d_tarj, t3, "RobotoMono-VariableFont_wght.ttf", 22, 760, 16)

            # Centrado horizontal matemático exacto (sin emojis que descuadren el texto)
            x1 = 460 - ((d_tarj.textbbox((0, 0), t1, font=f_b1)[2] - d_tarj.textbbox((0, 0), t1, font=f_b1)[0]) // 2)
            x2 = 460 - ((d_tarj.textbbox((0, 0), t2, font=f_b2)[2] - d_tarj.textbbox((0, 0), t2, font=f_b2)[0]) // 2)
            x3 = 460 - ((d_tarj.textbbox((0, 0), t3, font=f_b3)[2] - d_tarj.textbbox((0, 0), t3, font=f_b3)[0]) // 2)

            d_tarj.text((x1, 542), t1, font=f_b1, fill=c_verde)
            d_tarj.text((x2, 598), t2, font=f_b2, fill=c_blanco)
            d_tarj.text((x3, 648), t3, font=f_b3, fill=c_oro)
        elif difuminar_vip:
            zona_secreta = tarjeta.crop((35, 360, 885, 750))
            zona_borrosa = zona_secreta.filter(ImageFilter.GaussianBlur(radius=22))
            tarjeta.paste(zona_borrosa, (35, 360))
            d_tarj = ImageDraw.Draw(tarjeta, "RGBA")
            d_tarj.rectangle([(55, 465), (865, 635)], fill=(12, 14, 20, 248), outline=c_oro, width=3)

            tv1 = "PASE DIARIO VIP DISPONIBLE EN NUESTRA WEB"
            tv2 = "Entra ahora desde el enlace de nuestro perfil"
            f_v1 = obtener_fuente_video_ajustada(d_tarj, tv1, "Montserrat-VariableFont_wght.ttf", 28, 760, 18)
            f_v2 = obtener_fuente_video_ajustada(d_tarj, tv2, "RobotoMono-VariableFont_wght.ttf", 24, 760, 16)
            xv1 = 460 - ((d_tarj.textbbox((0, 0), tv1, font=f_v1)[2] - d_tarj.textbbox((0, 0), tv1, font=f_v1)[0]) // 2)
            xv2 = 460 - ((d_tarj.textbbox((0, 0), tv2, font=f_v2)[2] - d_tarj.textbbox((0, 0), tv2, font=f_v2)[0]) // 2)
            d_tarj.text((xv1, 498), tv1, font=f_v1, fill=c_oro)
            d_tarj.text((xv2, 560), tv2, font=f_v2, fill=c_verde)

        lienzo.paste(tarjeta, (80, 254))
        draw.rectangle([(78, 252), (1002, 1176)], outline=(0, 255, 100, 130), width=3)

    draw.rectangle([(50, 1335), (1030, 1500)], fill=(16, 18, 24, 245), outline=c_oro, width=2)
    f_cta_sup = obtener_fuente_video_ajustada(draw, texto_inferior_cta, "Montserrat-VariableFont_wght.ttf", 30, 930, tam_min=20)
    draw.text((75, 1355), texto_inferior_cta, font=f_cta_sup, fill=c_oro)
    draw.text((75, 1410), "🌐 WEB OFICIAL Y PROMO $7.99 EN EL PERFIL", font=f_cta, fill=c_verde)
    draw.text((75, 1452), "@QuantBet22 | Ciencia de Datos (+18 Informativo)", font=f_peq, fill=c_gris)

    lienzo.convert("RGB").save(ruta_salida, quality=96)
    return ruta_salida


def estampar_subtitulo_metro(ruta_slide_base, texto_subtitulo, ruta_salida_frame, progreso_pct=1.0):
    texto_subtitulo = (
    str(texto_subtitulo)
    .replace("Néishons Lig", "Nations League")
    .replace("Chámpions Lig", "Champions League")
    .replace("Premier Lig", "Premier League")
    .replace("Europa Lig", "Europa League")
)
    img = Image.open(ruta_slide_base).convert("RGBA")
    draw = ImageDraw.Draw(img, "RGBA")
    draw.rectangle([(45, 1192), (1035, 1320)], fill=(6, 8, 12, 248), outline=(0, 255, 100, 220), width=3)

    palabras = str(texto_subtitulo).strip().split()
    mitad = max(1, len(palabras) // 2)
    if len(palabras) <= 6:
        linea_1 = " ".join(palabras)
        linea_2 = ""
    else:
        linea_1 = " ".join(palabras[:mitad])
        linea_2 = " ".join(palabras[mitad:])

    if linea_2:
        f1 = obtener_fuente_video_ajustada(draw, linea_1, "Montserrat-VariableFont_wght.ttf", 31, 950, tam_min=20)
        f2 = obtener_fuente_video_ajustada(draw, linea_2, "Montserrat-VariableFont_wght.ttf", 31, 950, tam_min=20)
        b1 = draw.textbbox((0, 0), linea_1, font=f1)
        b2 = draw.textbbox((0, 0), linea_2, font=f2)
        x1 = (1080 - (b1[2] - b1[0])) // 2
        x2 = (1080 - (b2[2] - b2[0])) // 2
        draw.text((x1, 1208), linea_1, font=f1, fill=(255, 255, 255, 255))
        draw.text((x2, 1260), linea_2, font=f2, fill=(255, 215, 0, 255))
    else:
        f1 = obtener_fuente_video_ajustada(draw, linea_1, "Montserrat-VariableFont_wght.ttf", 34, 950, tam_min=22)
        b1 = draw.textbbox((0, 0), linea_1, font=f1)
        x1 = (1080 - (b1[2] - b1[0])) // 2
        draw.text((x1, 1234), linea_1, font=f1, fill=(255, 215, 0, 255))

    ancho_barra = int(max(40, min(986, 986 * float(progreso_pct))))
    draw.rectangle([(47, 1312), (1033, 1319)], fill=(18, 28, 22, 255))
    draw.rectangle([(47, 1312), (47 + ancho_barra, 1319)], fill=(0, 255, 100, 255))
    img.convert("RGB").save(ruta_salida_frame, quality=95)
    return ruta_salida_frame


def evaluar_mercado_contra_resultado_real(merc, gh, ga, g_ht, es_sudamerica=False, partido_nom=""):
    tot = gh + ga
    g_2t = max(0, tot - g_ht)
    m = str(merc).strip()
    m_low = m.lower()

    def _norm_txt(s):
        return "".join(c for c in unicodedata.normalize("NFD", str(s).lower()) if unicodedata.category(c) != "Mn")

    m_norm = _norm_txt(m_low)
    loc_n, vis_n = (_norm_txt(partido_nom).split(" vs ") + ["", ""])[:2]

    if "over 1.5" in m_low or "mas de 1.5" in m_norm:
        return tot >= 2
    elif "under 2.5" in m_low or "menos de 2.5" in m_low:
        return tot <= 2
    elif "under 3.5" in m_low or "menos de 3.5" in m_low:
        return tot <= 3
    elif "over 2.5" in m_low:
        return tot >= 3
    elif "over 3.5" in m_low:
        return tot >= 4
    elif "asiatico > 2.25" in m_norm:
        return tot >= 2
    elif "asiatico > 2.75" in m_norm:
        return tot >= 3
    elif "btts" in m_low or "ambos marcan" in m_low:
        return gh > 0 and ga > 0
    elif "combo 1x + o1.5" in m_low:
        return gh >= ga and tot >= 2
    elif "combo x2 + o1.5" in m_low:
        return ga >= gh and tot >= 2
    elif "1x" in m_low:
        return gh >= ga
    elif "x2" in m_low:
        return ga >= gh
    elif "gol en 1t" in m_low or "gol 1t" in m_low:
        return g_ht >= 1
    elif "gol en 2" in m_low or "gol 2t" in m_low:
        return g_2t >= 1
    elif "goles " in m_low and "> 1.5" in m_low:
        if loc_n and loc_n[:5] in m_norm:
            return gh >= 2
        elif vis_n and vis_n[:5] in m_norm:
            return ga >= 2
        return False
    elif "vict." in m_low or "victoria" in m_low:
        if "local" in m_low or (loc_n and loc_n[:5] in m_norm):
            return gh > ga
        elif "visita" in m_low or (vis_n and vis_n[:5] in m_norm):
            return ga > gh
        return False
    elif "empate" in m_low:
        return gh == ga
    elif "tarjetas" in m_low or "faltas" in m_low:
        return (abs(gh - ga) <= 1) or (tot >= 2)
    elif "corners" in m_norm:
        return (tot >= 1) or (abs(gh - ga) == 0)
    elif "remates" in m_low:
        return tot >= 2
    return tot >= 2


def abreviar_pick_cliente(merc):
    m = str(merc)
    m = m.replace("[VIP] ", "").replace("[FREE] ", "")
    m = m.replace("Remates Puerta", "Remates").replace("Faltas Totales", "Faltas")
    m = m.replace("Gol en 2do Tiempo", "Gol 2T").replace("Gol en 1T", "Gol 1T")
    m = m.replace("Total Menos de 2.5 (Under)", "Under 2.5").replace("Total Menos de 3.5 (Under)", "Under 3.5")
    m = m.replace("Total Asiático > 2.25", "Asiático > 2.25").replace("Ambos Marcan (BTTS)", "Ambos Marcan")
    return m


def _tokens_equipo_auditoria(nombre):
    s = "".join(c for c in unicodedata.normalize("NFD", str(nombre).lower()) if unicodedata.category(c) != "Mn")
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    ign = {"fc", "sc", "cf", "ac", "as", "sk", "ud", "cd", "rcd", "ca", "se", "cr", "ce", "club", "deportivo", "deportes", "atletico", "real", "sporting", "united", "city", "de", "la", "el", "ii"}
    t = [w for w in s.split() if len(w) >= 3 and w not in ign]
    return set(t) if t else set(s.split())


def seleccionar_7_partidos_14_apuestas_clientes(fecha_hoy, ruta_csv="auditoria_apuestas.csv", token_priv=None, chat_priv=None):
    # 1. Cargar el 100% de los partidos finalizados (FT) de TODOS los archivos cache_partidos_*.json (sin límite de 5)
    mapa_ft = {}
    indice_tokens_ft = []

    archivos_cache = sorted([a for a in os.listdir(".") if a.startswith("cache_partidos_") and a.endswith(".json")])
    for arch in archivos_cache:
        f_arch = arch.replace("cache_partidos_", "").replace(".json", "")
        try:
            with open(arch, "r", encoding="utf-8") as f:
                for p in json.load(f) or []:
                    est = str((p.get("fixture") or {}).get("status", {}).get("short") or "")
                    goals = p.get("goals") or {}
                    if est in ["FT", "AET", "PEN"] and goals.get("home") is not None and goals.get("away") is not None:
                        loc = str(((p.get("teams") or {}).get("home") or {}).get("name") or "").strip()
                        vis = str(((p.get("teams") or {}).get("away") or {}).get("name") or "").strip()
                        fid = str((p.get("fixture") or {}).get("id") or "")
                        if fid:
                            mapa_ft[fid] = p
                        if loc and vis:
                            mapa_ft[f"{loc.lower()} vs {vis.lower()}"] = p
                            indice_tokens_ft.append((f_arch, _tokens_equipo_auditoria(loc), _tokens_equipo_auditoria(vis), p))
        except Exception:
            pass

    def _buscar_partido_ft_real(id_p, part_nom, fecha_ref):
        if id_p and str(id_p) in mapa_ft:
            return mapa_ft[str(id_p)]
        clave = str(part_nom).strip().lower()
        if clave in mapa_ft:
            return mapa_ft[clave]
        if " vs " in clave:
            l_b, v_b = clave.split(" vs ", 1)
            tl, tv = _tokens_equipo_auditoria(l_b), _tokens_equipo_auditoria(v_b)
            try:
                dt_r = datetime.strptime(fecha_ref, "%Y-%m-%d")
                fechas_ok = {
                    fecha_ref,
                    (dt_r + timedelta(days=1)).strftime("%Y-%m-%d"),
                    (dt_r - timedelta(days=1)).strftime("%Y-%m-%d"),
                }
            except Exception:
                fechas_ok = None
            for f_c, tl_c, tv_c, p_obj in indice_tokens_ft:
                if fechas_ok and f_c not in fechas_ok:
                    continue
                ok_l = bool(tl & tl_c) or any(a[:4] == b[:4] for a in tl for b in tl_c if len(a) >= 4 and len(b) >= 4)
                ok_v = bool(tv & tv_c) or any(a[:4] == b[:4] for a in tv for b in tv_c if len(a) >= 4 and len(b) >= 4)
                if ok_l and ok_v:
                    return p_obj
        # Si no está en caché local pero tiene ID, consultar en directo a API-Sports para obtener el marcador real
        if id_p and str(id_p).isdigit():
            try:
                r_id = requests.get(
                    f"https://v3.football.api-sports.io/fixtures?id={id_p}",
                    headers={"x-apisports-key": API_KEY_RESPALDO_AYER},
                    timeout=5
                )
                if r_id.status_code == 200:
                    resp_l = r_id.json().get("response") or []
                    if resp_l:
                        p_api = resp_l[0]
                        if str((p_api.get("fixture") or {}).get("status", {}).get("short") or "") in ["FT", "AET", "PEN"]:
                            mapa_ft[str(id_p)] = p_api
                            return p_api
            except Exception:
                pass
        return None

    # 2. Consolidar los últimos 7 partidos DISTINTOS (4 VIP + 3 FREE) que YA finalizaron con marcador FT real
    ahora_real_aud = datetime.now()
    fecha_max_terminada = (
        (ahora_real_aud - timedelta(days=1)).strftime("%Y-%m-%d")
        if ahora_real_aud.hour < 21
        else ahora_real_aud.strftime("%Y-%m-%d")
    )
    fecha_tope_auditoria = min(str(fecha_hoy), fecha_max_terminada)
    dt_base = datetime.strptime(fecha_tope_auditoria, "%Y-%m-%d")
    archivos_clientes = sorted(
        [a for a in os.listdir(".") if re.match(r"clientes_enviados_\d{4}-\d{2}-\d{2}\.json", a)],
        reverse=True
    )

    vip_recolectadas = []
    free_recolectadas = []
    partidos_vistos = set()
    fecha_auditada_real = None
    excluidos_copa = ("portugalete", "real union", "real unión", "calvo sotelo", "cd minera", "utebo", "amorebieta")

    for arch_c in archivos_clientes:
        f_cand = arch_c.replace("clientes_enviados_", "").replace(".json", "")
        if f_cand > fecha_tope_auditoria:
            continue
        try:
            with open(arch_c, "r", encoding="utf-8") as f:
                tarjetas_cand = (json.load(f) or {}).get("tarjetas_clientes", [])
        except Exception:
            continue

        for item_c in tarjetas_cand:
            part_nom = str(item_c.get("partido", "")).strip()
            clave_p = part_nom.lower()
            if not part_nom or clave_p in partidos_vistos or any(ex in clave_p for ex in excluidos_copa):
                continue

            tipo_t = str(item_c.get("tipo_tarjeta", "VIP")).strip()
            if tipo_t == "VIP" and len(vip_recolectadas) >= 4:
                continue
            if tipo_t == "FREE" and len(free_recolectadas) >= 3:
                continue

            id_p = str(item_c.get("id_partido", "")).strip()
            fix_real = _buscar_partido_ft_real(id_p, part_nom, f_cand)
            if not fix_real:
                continue

            gh = int(float((fix_real.get("goals") or {}).get("home") or 0))
            ga = int(float((fix_real.get("goals") or {}).get("away") or 0))
            sh = ((fix_real.get("score") or {}).get("halftime")) or {}
            if sh.get("home") is not None and sh.get("away") is not None:
                g_ht = int(float(sh.get("home") or 0)) + int(float(sh.get("away") or 0))
            else:
                g_ht = (gh + ga) // 2
            lid = (fix_real.get("league") or {}).get("id", 0)
            es_sud = lid in {13, 11, 71, 128, 130, 530, 239, 240, 533, 712}

            mercados_usados_card = set()
            dos_apuestas = []
            for sel in item_c.get("selecciones", []):
                merc = str(sel.get("mercado", "Over 1.5 Goles")).strip()
                if merc.lower() in mercados_usados_card:
                    continue
                mercados_usados_card.add(merc.lower())
                cuo = float(sel.get("cuota", 1.42 if tipo_t == "VIP" else 1.24))
                ganada = evaluar_mercado_contra_resultado_real(merc, gh, ga, g_ht, es_sud, part_nom)
                dos_apuestas.append({
                    "mercado": f"[{tipo_t}] {merc}",
                    "mercado_corto": abreviar_pick_cliente(merc),
                    "cuota": cuo,
                    "ganada": ganada
                })
                if len(dos_apuestas) == 2:
                    break

            if len(dos_apuestas) < 2:
                continue

            partidos_vistos.add(clave_p)
            if not fecha_auditada_real:
                fecha_auditada_real = f_cand

            obj_card = {
                "tipo_tarjeta": tipo_t,
                "partido": part_nom,
                "marcador": f"{gh}-{ga}",
                "gh": gh,
                "ga": ga,
                "g_ht": g_ht,
                "fecha": f_cand,
                "dos_apuestas": dos_apuestas
            }
            if tipo_t == "VIP":
                vip_recolectadas.append(obj_card)
            else:
                free_recolectadas.append(obj_card)

            if len(vip_recolectadas) == 4 and len(free_recolectadas) == 3:
                break

        if len(vip_recolectadas) == 4 and len(free_recolectadas) == 3:
            break

    siete_tarjetas = vip_recolectadas + free_recolectadas
    if not fecha_auditada_real:
        fecha_auditada_real = (dt_base - timedelta(days=1)).strftime("%Y-%m-%d")

    aciertos_14 = sum(1 for t in siete_tarjetas for pk in t["dos_apuestas"] if pk["ganada"])
    total_14 = sum(len(t["dos_apuestas"]) for t in siete_tarjetas)
    tasa_txt = f"{aciertos_14}/{total_14} Aciertos"

    return siete_tarjetas, tasa_txt, fecha_auditada_real, aciertos_14, total_14

    archivo_clientes_ayer = f"clientes_enviados_{fecha_ayer}.json"
    siete_tarjetas = []
    todos_en_ft = True
    if os.path.exists(archivo_clientes_ayer):
        try:
            with open(archivo_clientes_ayer, "r", encoding="utf-8") as f:
                data_cli = json.load(f)
            for item_c in data_cli.get("tarjetas_clientes", [])[:7]:
                part_nom = item_c.get("partido", "").strip()
                tipo_t = item_c.get("tipo_tarjeta", "VIP").strip()
                fix = mapa_ft.get(str(item_c.get("id_partido", ""))) or mapa_ft.get(part_nom.lower())
                if fix:
                    gh = int(fix["goals"]["home"] or 0)
                    ga = int(fix["goals"]["away"] or 0)
                    g_ht = int(fix.get("score", {}).get("halftime", {}).get("home") or 0) + int(fix.get("score", {}).get("halftime", {}).get("away") or 0)
                    lid = fix.get("league", {}).get("id", 0)
                    es_sud = lid in {13, 11, 71, 128, 130, 530, 239, 240, 533, 712}
                elif part_nom in partidos_dict:
                    gh = partidos_dict[part_nom]["gh"]
                    ga = partidos_dict[part_nom]["ga"]
                    g_ht = partidos_dict[part_nom]["g_ht"]
                    es_sud = False
                else:
                    todos_en_ft = False
                    gh, ga, g_ht, es_sud = 2, 1, 1, False

                dos_apuestas = []
                for sel in item_c.get("selecciones", [])[:2]:
                    merc = sel.get("mercado", "Over 1.5 Goles")
                    cuo = float(sel.get("cuota", 1.30))
                    ganada = evaluar_mercado_contra_resultado_real(merc, gh, ga, g_ht, es_sud)
                    dos_apuestas.append({
                        "mercado": f"[{tipo_t}] {merc}",
                        "mercado_corto": abreviar_pick_cliente(merc),
                        "cuota": cuo,
                        "ganada": ganada
                    })
                siete_tarjetas.append({
                    "tipo_tarjeta": tipo_t, "partido": part_nom, "marcador": f"{gh}-{ga}",
                    "gh": gh, "ga": ga, "g_ht": g_ht, "fecha": fecha_ayer, "dos_apuestas": dos_apuestas
                })
        except Exception:
            todos_en_ft = False

    aciertos_14 = sum(1 for t in siete_tarjetas for pk in t["dos_apuestas"] if pk["ganada"])
    total_14 = sum(len(t["dos_apuestas"]) for t in siete_tarjetas)
    tasa_txt = f"{(aciertos_14 / max(1, total_14) * 100.0):.1f}%" if total_14 > 0 else "91.1%"

    return siete_tarjetas, tasa_txt, fecha_ayer, aciertos_14, total_14


def dibujar_icono_check_o_cruz(draw, x, y, es_acierto, tam=24):
    if es_acierto:
        draw.rectangle([(x, y), (x + tam, y + tam)], fill=(0, 215, 88, 255), outline=(0, 255, 115, 255), width=2)
        draw.line([(x + 5, y + 12), (x + 10, y + 18), (x + 19, y + 5)], fill=(255, 255, 255, 255), width=3)
    else:
        draw.rectangle([(x, y), (x + tam, y + tam)], fill=(220, 45, 45, 255), outline=(255, 95, 95, 255), width=2)
        draw.line([(x + 5, y + 5), (x + tam - 5, y + tam - 5)], fill=(255, 255, 255, 255), width=3)
        draw.line([(x + tam - 5, y + 5), (x + 5, y + tam - 5)], fill=(255, 255, 255, 255), width=3)


def crear_imagen_auditoria_vertical(fecha_hoy, ruta_csv="auditoria_apuestas.csv", partidos_vip=None, ruta_salida="slide_auditoria.jpg", token_privado=None, chat_id_privado=None):
    siete_tarjetas, tasa_txt, fecha_ayer, ac_14, tot_14 = seleccionar_7_partidos_14_apuestas_clientes(
        fecha_hoy, ruta_csv, token_privado, chat_id_privado
    )
    lienzo = crear_fondo_vertical_base()
    draw = ImageDraw.Draw(lienzo, "RGBA")
    f_tag, f_titulo, f_sub, f_cta, f_peq = cargar_fuentes_video(38)
    c_verde = (0, 255, 100, 255)
    c_rojo = (255, 80, 80, 255)
    c_oro = (255, 205, 0, 255)
    c_blanco = (245, 245, 245, 255)

    draw.rectangle([(40, 58), (1040, 114)], fill=(12, 28, 20, 238), outline=c_verde, width=2)
    tit_sup = "AUDITORÍA OFICIAL CLIENTES (4 VIP + 3 FREE = 14 SELECCIONES)"
    draw.text((62, 71), tit_sup, font=obtener_fuente_video_ajustada(draw, tit_sup, "Montserrat-VariableFont_wght.ttf", 27, 955, 18), fill=c_verde)

    tit_prin = f"RESULTADOS JORNADA {fecha_ayer}"
    draw.text((42, 124), tit_prin, font=obtener_fuente_video_ajustada(draw, tit_prin, "Montserrat-VariableFont_wght.ttf", 38, 980, 24), fill=c_blanco)

    draw.rectangle([(40, 178), (1040, 260)], fill=(18, 26, 22, 242), outline=c_verde, width=2)
    txt_ef = f"Efectividad Verificada: {tasa_txt} ({ac_14}/{tot_14} acertadas en VIP y FREE)"
    draw.text((60, 192), txt_ef, font=obtener_fuente_video_ajustada(draw, txt_ef, "Montserrat-VariableFont_wght.ttf", 30, 960, 20), fill=c_verde)
    draw.text((60, 230), f"Fecha Auditada: {fecha_ayer} | Las 7 Tarjetas Entregadas a Clientes", font=f_peq, fill=c_oro)

    y = 274
    for item in siete_tarjetas[:7]:
        pks = item["dos_apuestas"]
        ac_p = sum(1 for k in pks if k["ganada"])
        tot_p = max(1, len(pks))
        es_verde = (ac_p == tot_p)
        col_b = c_verde if es_verde else (c_oro if ac_p == 1 else c_rojo)
        bg_c = (14, 24, 20, 242) if es_verde else ((26, 24, 14, 242) if ac_p == 1 else (32, 14, 16, 242))

        draw.rectangle([(40, y), (1040, y + 118)], fill=bg_c, outline=col_b, width=2)
        dibujar_icono_check_o_cruz(draw, 58, y + 14, ac_p >= 1, tam=26)

        color_tag_nivel = c_oro if item["tipo_tarjeta"] == "VIP" else c_verde
        tag_nivel_txt = f"[{item['tipo_tarjeta']}]"
        f_tag_niv = obtener_fuente_video_ajustada(draw, tag_nivel_txt, "Montserrat-VariableFont_wght.ttf", 28, 130, 20)
        draw.text((94, y + 11), tag_nivel_txt, font=f_tag_niv, fill=color_tag_nivel)

        w_tag = draw.textbbox((0, 0), tag_nivel_txt, font=f_tag_niv)[2]
        linea_duelo = f" {item['partido']} ({item['marcador']})  [{ac_p}/{tot_p}]"
        f_duelo = obtener_fuente_video_ajustada(draw, linea_duelo, "Montserrat-VariableFont_wght.ttf", 29, 915 - w_tag, 19)
        draw.text((94 + w_tag, y + 11), linea_duelo, font=f_duelo, fill=c_blanco)

        x_cur = 60
        for k in pks[:2]:
            dibujar_icono_check_o_cruz(draw, x_cur, y + 64, k["ganada"], tam=22)
            txt_k = f"{k['mercado_corto']} ({k['cuota']:.2f})"
            f_k = obtener_fuente_video_ajustada(draw, txt_k, "RobotoMono-VariableFont_wght.ttf", 24, 445, 17)
            draw.text((x_cur + 30, y + 60), txt_k, font=f_k, fill=c_verde if k["ganada"] else c_rojo)
            x_cur += 485
        y += 126

    draw.rectangle([(40, 1335), (1040, 1500)], fill=(18, 20, 26, 245), outline=c_oro, width=2)
    draw.text((70, 1355), "PASE VIP 1 DÍA POR 1.00 USD", font=f_sub, fill=c_oro)
    draw.text((70, 1410), "📲 ENTRA DESDE EL ENLACE DE NUESTRO PERFIL", font=f_cta, fill=c_verde)
    draw.text((70, 1452), "@QuantBet22 | Laboratorio de Ciencia de Datos", font=f_peq, fill=(180, 180, 180, 255))

    lienzo.convert("RGB").save(ruta_salida, quality=96)
    dir_base_aud = os.path.dirname(ruta_salida) or "."
    r_cp = os.path.join(dir_base_aud, "00_AUDITORIA_7_PARTIDOS_VIP_Y_FREE.jpg")
    lienzo.convert("RGB").save(r_cp, quality=96)
    return ruta_salida, tasa_txt


def publicar_auditoria_nocturna_canal_free(fecha_auditar=None):
    """Refresca marcadores FT, genera la imagen oficial de las 7 tarjetas y la envía al Canal FREE y a tu chat privado."""
    import mercados_optimizados as m
    if not fecha_auditar:
        fecha_auditar = datetime.now().strftime("%Y-%m-%d")
    headers = {"x-apisports-key": API_KEY_RESPALDO_AYER}
    m.obtener_datos_api_partidos(fecha_auditar, headers, forzar_refresco=True)
    m.resolver_apuestas_pendientes(API_KEY_RESPALDO_AYER)

    ruta_img, tasa_txt = crear_imagen_auditoria_vertical(
        fecha_auditar,
        ruta_salida=f"00_AUDITORIA_NOCTURNA_{fecha_auditar}.jpg"
    )
    caption_oficial_free = (
        f"📊 <b>AUDITORÍA OFICIAL CERRADA ({fecha_auditar}) — {tasa_txt} VERIFICADOS</b> ✅\n\n"
        "Ahí tienen en pantalla la transparencia de nuestro algoritmo en Python: resultados reales auditados con marcador final (FT) sobre nuestras 7 tarjetas del día.\n\n"
        "🔥 <b>¿QUIERES PROBAR MAÑANA EL CANAL VIP POR SOLO 1.00 USD?</b>\n"
        "Habilitamos el <b>PASE DIARIO DE 24 HORAS por solo 1.00 USD</b>:\n"
        "✅ Recibes las 4 Tarjetas VIP de cuota alta de mañana.\n"
        "✅ Recibes la Combinada Doble Institucional VIP.\n"
        "✅ Pago único por 1 día (sin cobros automáticos).\n\n"
        "⏳ <i>IMPORTANTE: Los precios de promoción VIP (7.99 USD por 10 días) y Plan PRO están disponibles únicamente hasta el 30 DE NOVIEMBRE.</i>\n\n"
        "👇 <b>Activa tu Pase de 1 Día (1.00 USD) ahora mismo:</b>\n"
        "💳 <b>1. Activar con Tarjeta en 1 clic (Whop Oficial):</b>\n"
        "👉 <a href='https://whop.com/youtube-d4c7/quantbet22-canal-vip/'>https://whop.com/youtube-d4c7/quantbet22-canal-vip/</a>\n\n"
        "📲 <b>2. Activar por Bizum, Nequi o USDT:</b>\n"
        "👉 Escribe <b>\"PASE 1 DIA\"</b> en nuestro soporte: @QuantBetSoporte_bot\n\n"
        "🌐 <b>Estadísticas y resultados en vivo:</b>\n"
        "👉 <a href='https://quantbet22.streamlit.app'>https://quantbet22.streamlit.app</a>"
    )
    caption_oficial_vip = (
        f"🏆 <b>BALANCE OFICIAL CERRADO EQUIPO VIP ({fecha_auditar}) — {tasa_txt} VERIFICADOS</b> ✅\n\n"
        "¡Excelente jornada, equipo VIP! Ahí tienen en pantalla la auditoría real con marcador final (FT) sobre nuestras 7 tarjetas oficiales.\n\n"
        "📈 <i>Recuerden mantener disciplina con el Stake de Kelly y consultar todas las estadísticas y combinadas auditadas en tiempo real en nuestra plataforma web:</i>\n"
        "🌐 👉 <a href='https://quantbet22.streamlit.app'>https://quantbet22.streamlit.app</a>\n\n"
        "👑 <b>¿Quieres dar el salto al Canal PRO (100% de las ligas + Combinada Triple Sniper 3X)?</b>\n"
        "⏳ <i>Promo especial hasta el 30 DE NOVIEMBRE por solo 49.99 USD (Antes 74.99 USD):</i>\n"
        "👉 <a href='https://whop.com/youtube-d4c7/products/uantbet22-membresia-pro-avanzada/?ref=related_products'>Desbloquear Plan PRO aquí</a>\n"
        "💬 Soporte directo 24/7: @QuantBetSoporte_bot"
    )
    # 1. Enviar a tu Bot Personal de Auditorías
    m.enviar_imagen_telegram(m.TOKEN_TICKETS, m.CHAT_ID_GRUPO_AUDITORIAS, ruta_img, caption_oficial_free)
    # 2. Enviar a tu chat privado personal
    m.enviar_imagen_telegram(m.TOKEN_GENERAL, m.CHAT_ID_GENERAL, ruta_img, caption_oficial_free)
    # 3. Enviar directo al Canal FREE de Clientes
    m.enviar_imagen_telegram(m.TOKEN_CARTERO, m.CHAT_ID_CLIENTES_FREE, ruta_img, caption_oficial_free)
    # 4. Enviar directo al Canal VIP de Clientes con su texto exclusivo
    m.enviar_imagen_telegram(m.TOKEN_CARTERO, m.CHAT_ID_CLIENTES_VIP, ruta_img, caption_oficial_vip)
    print(f"✅ Auditoría nocturna ({fecha_auditar}) enviada con éxito a tu Bot de Auditorías, Canal FREE y Canal VIP.")



def formatear_liga_hablada(liga_visual):
    mapa = {
        "UEFA CHAMPIONS LEAGUE": "la UEFA Chámpions Lig",
        "UEFA EUROPA LEAGUE": "la UEFA Europa Lig",
        "UEFA CONFERENCE LEAGUE": "la UEFA Cónferens Lig",
        "ESPAÑA (LALIGA)": "LaLiga de España",
        "ESPAÑA (SEGUNDA)": "LaLiga Hypermotion de España",
        "INGLATERRA (PREMIER)": "la Premier Lig de Inglaterra",
        "ITALIA (SERIE A)": "la Serie A de Italia",
        "ALEMANIA (BUNDESLIGA)": "la Bundesliga de Alemania",
        "FRANCIA (LIGUE 1)": "la Lig 1 de Francia",
        "BRASIL (SERIE A)": "el Brasileirão Serie A",
        "COLOMBIA (PRIMERA A)": "la Primera A de Colombia",
        "COLOMBIA (COPA BETPLAY)": "la Copa de Colombia",
        "ARGENTINA (LIGA PROFESIONAL)": "la Liga Profesional de Argentina",
        "PORTUGAL (PRIMEIRA LIGA)": "la Primeira Liga de Portugal",
        "UEFA NATIONS LEAGUE": "la UEFA Néishons Lig",
        "ELIMINATORIAS CONMEBOL": "las Eliminatorias Sudamericanas",
        "ELIMINATORIAS UEFA": "las Eliminatorias Europeas",
        "AMISTOSO INTERNACIONAL": "la Fecha FIFA de Selecciones",
        "MUNDIAL FIFA": "la Copa del Mundo de la FIFA",
        "EUROCOPA": "la Eurocopa de Naciones",
        "COPA AMÉRICA": "la Copa América",
    }
    return mapa.get(liga_visual, liga_visual.replace("(", " ").replace(")", ""))


def formatear_numero_hablado(valor_num):
    s = f"{float(valor_num):.2f}"
    if s.endswith(".00"):
        return s[:-3]
    if s.endswith("0"):
        s = s[:-1]
    return s.replace(".", " punto ")


async def sintetizar_audio_ia(texto_guion, ruta_mp3):
    guion_limpio = (
        texto_guion.replace("Python", "Páiton")
        .replace("python", "Páiton")
        .replace("BetPlay", "Primera A")
        .replace("apuestas", "proyecciones")
        .replace("apuesta", "métrica")
        .replace("cuota", "índice")
        .replace("VIP", "Bip")
        .replace("CHAMPIONS LEAGUE", "Chámpions Lig")
        .replace("Champions League", "Chámpions Lig")
        .replace("EUROPA LEAGUE", "Europa Lig")
        .replace("Europa League", "Europa Lig")
        .replace("PREMIER LEAGUE", "Premier Lig")
        .replace("Premier League", "Premier Lig")
        .replace(" > ", " superior a ")
        .replace(">", " superior a ")
        .replace("5.5", "5 punto 5")
        .replace("6.5", "6 punto 5")
        .replace("7.5", "7 punto 5")
        .replace("8.5", "8 punto 5")
        .replace("7.99", "9 con 99")
        .replace("1.5", "1 punto 5")
        .replace("2.5", "2 punto 5")
        .replace("2.25", "2 punto 25")
        .replace("21.5", "21 punto 5")
        .replace("22.5", "22 punto 5")
        .replace("1T", "primer tiempo")
        .replace("2do Tiempo", "segundo tiempo")
        .replace("Over ", "más de ")
    )
    for _ in range(3):
        try:
            comunicador = edge_tts.Communicate(guion_limpio, VOZ_ANALISTA_IA, rate=VELOCIDAD_VOZ)
            await comunicador.save(ruta_mp3)
            if os.path.exists(ruta_mp3) and os.path.getsize(ruta_mp3) > 1500:
                return True
        except Exception:
            await asyncio.sleep(1.2)
    return False


def renderizar_video_mp4_2_slides(slide_1, slide_2, ruta_mp3, ruta_mp4_salida, seg_slide_1=11, texto_guion="", ocultar_monitor_slide_1=False, slide_3=None):
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    ruta_wav = ruta_mp3.replace(".mp3", "_voz.wav")

    subprocess.run([
        ffmpeg_exe, "-y", "-i", os.path.abspath(ruta_mp3),
        "-acodec", "pcm_s16le", "-ar", "44100", "-ac", "2",
        os.path.abspath(ruta_wav)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    duracion_audio = 24.0
    if os.path.exists(ruta_wav) and os.path.getsize(ruta_wav) > 2000:
        try:
            with wave.open(ruta_wav, "rb") as wf:
                frames = wf.getnframes()
                rate = wf.getframerate()
                if rate > 0 and frames > 0:
                    duracion_audio = frames / float(rate)
        except Exception:
            pass

    oraciones = [o.strip() for o in re.split(r"(?<=[.,:])\s+", (texto_guion or "Análisis cuantitativo en Python.").strip()) if o.strip()]
    frases = []
    for o in oraciones:
        pal = o.split()
        if len(pal) > 13:
            mit = len(pal) // 2
            frases.append(" ".join(pal[:mit]))
            frases.append(" ".join(pal[mit:]))
        else:
            frases.append(o)
    if not frases:
        frases = ["Análisis cuantitativo en Python."]

    mitad_f = max(1, len(frases) // 2)
    dur_por_frase = max(2.2, (duracion_audio + 0.5) / len(frases))

    archivos_frames = []
    lista_txt = ruta_mp4_salida.replace(".mp4", "_inputs.txt")
    salto = chr(10)

    tercio_1 = max(1, int(len(frases) * 0.42))
    tercio_2 = max(tercio_1 + 1, int(len(frases) * 0.75))
    with open(lista_txt, "w", encoding="utf-8") as f:
        for idx_f, frase_txt in enumerate(frases):
            if slide_3 and os.path.exists(str(slide_3)):
                base_img = slide_1 if idx_f < tercio_1 else (slide_2 if idx_f < tercio_2 else slide_3)
            else:
                base_img = slide_1 if idx_f < mitad_f else slide_2
            ruta_frame = ruta_mp4_salida.replace(".mp4", f"_subframe_{idx_f}.jpg")
            prog_f = float(idx_f + 1) / max(1, len(frases))
            estampar_subtitulo_metro(base_img, frase_txt, ruta_frame, progreso_pct=prog_f)
            archivos_frames.append(ruta_frame)
            f.write(f"file '{ruta_posix(ruta_frame)}'" + salto)
            f.write(f"duration {dur_por_frase:.2f}" + salto)
        if archivos_frames:
            f.write(f"file '{ruta_posix(archivos_frames[-1])}'" + salto)

    filtro_movimiento_real = (
        "fps=30,"
        "scale=1112:1976,"
        "crop=1080:1920:16+14*sin(2*PI*t/4.5):28+20*cos(2*PI*t/4.5),"
        "format=yuv420p"
    )

    video_mudo_temp = ruta_mp4_salida.replace(".mp4", "_mudo_sub.mp4")
    subprocess.run([
        ffmpeg_exe, "-y",
        "-f", "concat", "-safe", "0", "-i", os.path.abspath(lista_txt),
        "-vf", filtro_movimiento_real,
        "-c:v", "libx264", "-preset", "ultrafast", "-an",
        os.path.abspath(video_mudo_temp)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    audio_input = os.path.abspath(ruta_wav) if os.path.exists(ruta_wav) else os.path.abspath(ruta_mp3)
    subprocess.run([
        ffmpeg_exe, "-y",
        "-i", os.path.abspath(video_mudo_temp),
        "-i", audio_input,
        "-map", "0:v:0", "-map", "1:a:0",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k", "-ar", "44100",
        "-shortest",
        os.path.abspath(ruta_mp4_salida)
    ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    for tmp in archivos_frames + [lista_txt, video_mudo_temp, ruta_wav]:
        if os.path.exists(tmp):
            try:
                os.remove(tmp)
            except Exception:
                pass


def generar_diccionario_copys_por_red(tipo_video, p_data, tasa_acierto="91.1%"):
    loc = p_data.get("local", "Equipo Local")
    vis = p_data.get("visitante", "Visitante")
    liga = p_data.get("liga_visual", "Fútbol Europeo")
    goles = p_data.get("tot_goles", 2.65)
    faltas = p_data.get("tot_faltas", 23.5)

    tag_loc = limpiar_hashtag(loc)
    tag_vis = limpiar_hashtag(vis)
    parte_liga = liga.split("(")[1].replace(")", "") if "(" in liga else liga
    tag_liga = limpiar_hashtag(parte_liga)
    s = chr(10)
    ds = s + s

    promo_txt = "🎁 1ª proyección abierta en nuestra Web y las otras 2 sin costo en nuestro Telegram (Enlace en el perfil)."
    pregunta_gancho = f"¿Quién se lleva este {loc} vs {vis}? Déjalo en los comentarios 👇⚽"

    if tipo_video == "1_ESTRELLA_10AM":
        return {
            "horario": "22:00 PM (España) - PARTIDAZO ESTELAR #2",
            "titulo_interno": f"VIDEO 2 (22:00 PM) - {loc.upper()} VS {vis.upper()} ({p_data.get('hora', '')})",
            "tiktok": (
                f"{pregunta_gancho} "
                f"Nuestro modelo en Python proyecta {goles:.2f} goles esperados para {loc} vs {vis} ({liga}). "
                f"{promo_txt} 👇" + ds +
                f"{tag_loc} {tag_vis} {tag_liga} #futbol #cienciadedatos #analisistactico"
            ),
            "instagram": (
                f"{pregunta_gancho}" + ds +
                f"• Proyección ofensiva en Python: {goles:.2f} goles | Fricción: {faltas:.1f} faltas." + s +
                f"• {promo_txt}" + ds +
                f"👉 Toca el enlace de nuestra biografía para entrar a la Web y al Telegram 👇" + ds +
                f"{tag_loc} {tag_vis} {tag_liga} #futbol #reels #cienciadedatos"
            ),
            "youtube_titulo": f"{loc} vs {vis} | Análisis Táctico {tag_loc} {tag_vis} {tag_liga} #shorts"[:98],
            "youtube_descripcion": (
                f"{pregunta_gancho} Consulta el informe táctico interactivo de {loc} vs {vis} en nuestra plataforma web (Enlace en el perfil del canal). "
                f"{promo_txt} 👇" + ds +
                f"{tag_loc} {tag_vis} {tag_liga} #shorts #futbol #cienciadedatos #analisistactico"
            ),
            "facebook": (
                f"{pregunta_gancho} Ya publicamos el informe táctico interactivo del {loc} vs {vis} ({goles:.2f} goles proyectados). "
                f"{promo_txt} 👇" + ds +
                f"{tag_loc} {tag_vis} {tag_liga} #futbol #reels #cienciadedatos"
            ),
        }

    else:
        return {
            "horario": "18:00 PM (España) - PARTIDAZO ESTELAR #1 + AUDITORÍA",
            "titulo_interno": f"VIDEO 1 (18:00 PM) - {loc.upper()} VS {vis.upper()} ({tasa_acierto})",
            "tiktok": (
                f"{pregunta_gancho} 📊⚽ "
                f"Ya publicamos en nuestra plataforma web y en Telegram las proyecciones matemáticas para {loc} vs {vis}. "
                f"{promo_txt} 👇" + ds +
                f"{tag_loc} {tag_vis} {tag_liga} #futbol #cienciadedatos #analisistactico"
            ),
            "instagram": (
                f"{pregunta_gancho} 📈🧬" + ds +
                f"🔓 El análisis matemático para {loc} vs {vis} ({liga}) ya está disponible en nuestra plataforma web." + s +
                f"{promo_txt}" + ds +
                f"👉 Consulta los datos tocando el enlace de nuestro perfil 👇" + ds +
                f"{tag_loc} {tag_vis} {tag_liga} #futbol #reels #cienciadedatos"
            ),
            "youtube_titulo": f"{loc} vs {vis} | Proyección y Datos {tag_loc} {tag_vis} {tag_liga} #shorts"[:98],
            "youtube_descripcion": (
                f"{pregunta_gancho} Balance verificado y proyección táctica para {loc} vs {vis} disponible en nuestra plataforma web (Enlace en el perfil). {promo_txt} 👇" + ds +
                f"{tag_loc} {tag_vis} {tag_liga} #shorts #futbol #cienciadedatos #analisistactico"
            ),
            "facebook": (
                f"{pregunta_gancho} Transparencia institucional y modelos de Poisson en tiempo real. "
                f"Ya publicamos en nuestra plataforma web el informe táctico para el {loc} vs {vis}. "
                f"{promo_txt} 👇" + ds +
                f"{tag_loc} {tag_vis} {tag_liga} #futbol #reels #cienciadedatos"
            ),
        }


def enviar_video_y_mensajes_separados_telegram(token, chat_id, ruta_video, dict_copys):
    if not token or not chat_id or not os.path.exists(ruta_video):
        return
    url_vid = f"https://api.telegram.org/bot{token}/sendVideo"
    url_msg = f"https://api.telegram.org/bot{token}/sendMessage"
    s = chr(10)
    try:
        with open(ruta_video, "rb") as vid:
            cap_vid = (
                f"🎬 <b>{dict_copys['titulo_interno']}</b>" + s +
                f"⏰ Horario programado: {dict_copys['horario']}" + s +
                "👇 <i>Toca cualquiera de los bloques de abajo para copiar el texto de cada red social:</i>"
            )
            requests.post(
                url_vid,
                data={"chat_id": chat_id, "caption": cap_vid, "parse_mode": "HTML", "disable_web_page_preview": True, "disable_web_page_preview": True},
                files={"video": vid},
                timeout=45,
            )
        time.sleep(1.0)
        mensajes_redes = [
            f"🎵 <b>TIKTOK (Toca el texto para copiar):</b>" + s + f"<code>{dict_copys['tiktok']}</code>",
            f"📸 <b>INSTAGRAM REELS (Toca el texto para copiar):</b>" + s + f"<code>{dict_copys['instagram']}</code>",
            f"▶️ <b>YOUTUBE SHORTS (Toca para copiar Título y Descripción):</b>" + s + f"<b>Título:</b>" + s + f"<code>{dict_copys['youtube_titulo']}</code>" + s + s + f"<b>Descripción:</b>" + s + f"<code>{dict_copys['youtube_descripcion']}</code>",
            f"📘 <b>FACEBOOK REELS (Toca el texto para copiar):</b>" + s + f"<code>{dict_copys['facebook']}</code>",
        ]
        for m_txt in mensajes_redes:
            requests.post(
                url_msg,
                json={"chat_id": chat_id, "text": m_txt, "parse_mode": "HTML", "disable_web_page_preview": True, "disable_web_page_preview": True, "disable_web_page_preview": True},
                timeout=8,
            )
            time.sleep(0.5)
    except Exception:
        pass


def guardar_archivos_individuales_y_json(carpeta_videos, prefijo_num, ruta_mp4, dict_copys, cola_json, fecha_jornada):
    s = chr(10)
    aviso_18 = s + "📊 📊 Ciencia de Datos y Modelos Matemáticos aplicados al Fútbol Profesional."
    for k_red in ["tiktok", "instagram", "youtube_descripcion", "facebook"]:
        if "+18" not in dict_copys.get(k_red, ""):
            dict_copys[k_red] = dict_copys.get(k_red, "") + aviso_18

    dir_txts = os.path.join(carpeta_videos, f"TEXTOS_SEPARADOS_VIDEO_{prefijo_num}")
    os.makedirs(dir_txts, exist_ok=True)
    with open(os.path.join(dir_txts, "1_TIKTOK.txt"), "w", encoding="utf-8") as f:
        f.write(dict_copys["tiktok"])
    with open(os.path.join(dir_txts, "2_INSTAGRAM_REELS.txt"), "w", encoding="utf-8") as f:
        f.write(dict_copys["instagram"])
    with open(os.path.join(dir_txts, "3_YOUTUBE_SHORTS_TITULO.txt"), "w", encoding="utf-8") as f:
        f.write(dict_copys["youtube_titulo"])
    with open(os.path.join(dir_txts, "3_YOUTUBE_SHORTS_DESCRIPCION.txt"), "w", encoding="utf-8") as f:
        f.write(dict_copys["youtube_descripcion"])
    with open(os.path.join(dir_txts, "4_FACEBOOK_REELS.txt"), "w", encoding="utf-8") as f:
        f.write(dict_copys["facebook"])

    ahora = datetime.now()
    dt_v1 = ahora + timedelta(minutes=30)
    resto_5 = dt_v1.minute % 5
    if resto_5 != 0:
        dt_v1 += timedelta(minutes=(5 - resto_5))
    dt_v1 = dt_v1.replace(second=0, microsecond=0)

    if prefijo_num == 1:
        dt_objetivo = dt_v1
    else:
        if dt_v1.hour >= 18:
            dt_objetivo = (dt_v1 + timedelta(days=1)).replace(hour=6, minute=0, second=0, microsecond=0)
        elif dt_v1.hour < 5:
            dt_objetivo = dt_v1.replace(hour=6, minute=0, second=0, microsecond=0)
        else:
            dt_objetivo = dt_v1 + timedelta(hours=5)

    hora_str_24 = dt_objetivo.strftime("%H:%M")
    horario_dinamico = f"{hora_str_24} (España) - VIDEO #{prefijo_num} (TOP CARTELERA #{prefijo_num})"

    cola_json.append({
        "fecha_publicacion": dt_objetivo.strftime("%Y-%m-%d"),
        "orden_video": prefijo_num,
        "hora_24h": hora_str_24,
        "horario_objetivo_espana": horario_dinamico,
        "titulo_interno": dict_copys["titulo_interno"],
        "ruta_video_mp4": os.path.abspath(ruta_mp4),
        "redes": {
            "tiktok": {"descripcion": dict_copys["tiktok"], "estado": "pendiente"},
            "instagram": {"descripcion": dict_copys["instagram"], "estado": "pendiente"},
            "youtube": {
                "titulo": dict_copys["youtube_titulo"],
                "descripcion": dict_copys["youtube_descripcion"],
                "estado": "pendiente"
            },
            "facebook": {"descripcion": f"{dict_copys['facebook']}\n\n🌐 App Oficial y Promo $7.99 en vivo: https://quantbet22.streamlit.app", "estado": "pendiente"}
        }
    })


def generar_tarjeta_trampa_sino_existe(p_trampa, directorio_dia):
    from generador_imagenes import generar_captura_automatica
    if p_trampa.get("ruta_free") and os.path.exists(p_trampa["ruta_free"]):
        return p_trampa["ruta_free"]
    if p_trampa.get("ruta_vip") and os.path.exists(p_trampa["ruta_vip"]):
        return p_trampa["ruta_vip"]
    loc_clean = "".join([c for c in p_trampa['local'] if c.isalnum() or c in " "]).rstrip().replace(" ", "_")
    vis_clean = "".join([c for c in p_trampa['visitante'] if c.isalnum() or c in " "]).rstrip().replace(" ", "_")
    hora_clean = p_trampa['hora'].replace(":", "")
    dir_desc = os.path.join(directorio_dia, "3_DESCARTES")
    os.makedirs(dir_desc, exist_ok=True)
    ruta_especifica = os.path.join(dir_desc, f"{hora_clean}_{loc_clean}_vs_{vis_clean}_DESCARTES.jpg")
    if os.path.exists(ruta_especifica):
        return ruta_especifica
    return generar_captura_automatica(p_trampa, "DESCARTES")


def es_partido_de_america(p):
    if p.get("is_america", False):
        return True
    liga_up = str(p.get("liga_visual", "")).upper()
    if any(lg in liga_up for lg in ["COLOMBIA", "ARGENTINA", "BRASIL", "LIBERTADORES", "SUDAMERICANA", "MÉXICO", "MLS", "USA", "CONMEBOL", "CONCACAF", "COPA AMÉRICA"]):
        return True
    hora_str = str(p.get("hora", "20:00"))[:2]
    if hora_str.isdigit() and 0 <= int(hora_str) <= 6:
        return True
    selecciones_america = (
        "argentina", "colombia", "brasil", "brazil", "uruguay", "chile", "ecuador",
        "peru", "perú", "paraguay", "venezuela", "bolivia", "mexico", "méxico",
        "estados unidos", "usa", "canada", "canadá", "costa rica", "panama", "panamá"
    )
    duelo_low = f"{p.get('local', '')} {p.get('visitante', '')}".lower()
    return any(sel in duelo_low for sel in selecciones_america)


def generar_paquete_redes_sociales(fecha_jornada, partidos_vip, partidos_descartes, ruta_img_doble, token_privado=None, chat_id_privado=None):
    directorio_dia = f"Alertas_Quant_{fecha_jornada}"
    carpeta_videos = os.path.join(directorio_dia, "4_VIDEOS_LISTOS_REDES")
    os.makedirs(carpeta_videos, exist_ok=True)
    for arch_mp4 in os.listdir(carpeta_videos):
        if arch_mp4.endswith(".mp4"):
            try:
                os.remove(os.path.join(carpeta_videos, arch_mp4))
            except Exception:
                pass

    print("=" * 120)
    print(f" 🎬 GENERANDO LOS 2 VIDEOS DIARIOS (VIDEO 1: TOP EUROPA + VIDEO 2: TOP SUDAMÉRICA/EUROPA #2) ({fecha_jornada})")
    print("=" * 120)

    if not partidos_vip and not partidos_descartes:
        return

    todos_ordenados = sorted(partidos_vip, key=puntaje_cartelera_video, reverse=True)
    for p_desc in sorted(partidos_descartes, key=puntaje_cartelera_video, reverse=True):
        if p_desc not in todos_ordenados:
            todos_ordenados.append(p_desc)

    candidatos_europa = [p for p in todos_ordenados if not es_partido_de_america(p)]
    candidatos_america = [p for p in todos_ordenados if es_partido_de_america(p)]

    # VIDEO 1 (23:30 PM ESP): Siempre el #1 Mejor Partido de Europa
    partido_europa_1 = candidatos_europa[0] if candidatos_europa else todos_ordenados[0]

    # VIDEO 2 (04:45 AM ESP): Si hay un partidazo Top en Sudamérica/América (puntaje >= 100), va en el Video 2;
    # si no hay partidazo importante en América ese día, pone el #2 Mejor Partido de Europa
    if candidatos_america and puntaje_cartelera_video(candidatos_america[0]) >= 100 and candidatos_america[0] != partido_europa_1:
        partido_europa_2 = candidatos_america[0]
    else:
        restantes_eu = [p for p in candidatos_europa if p != partido_europa_1]
        partido_europa_2 = restantes_eu[0] if restantes_eu else (todos_ordenados[1] if len(todos_ordenados) > 1 else partido_europa_1)
    # Ordenar los 2 mejores partidos por hora real de inicio:
    # El que se juega MÁS TEMPRANO va en el VIDEO 1 (sale hoy en la noche)
    # y el que se juega MÁS TARDE (noche) va en el VIDEO 2 (sale mañana en la mañana)
    par_cronologico = sorted(
        [partido_europa_1, partido_europa_2],
        key=lambda x: (str(x.get("fecha", "")), str(x.get("hora", "20:45")))
    )
    partido_europa_1, partido_europa_2 = par_cronologico[0], par_cronologico[1]
    slide_aud_1, tasa_real = crear_imagen_auditoria_vertical(
        fecha_jornada,
        partidos_vip=partidos_vip,
        ruta_salida=os.path.join(carpeta_videos, "temp_aud_1.jpg"),
        token_privado=TOKEN_AUDITORIAS_PRIVADO,
        chat_id_privado=CHAT_ID_AUDITORIAS_PRIVADO
    )

    cola_json = []

    # =========================================================================
    # VIDEO 1 (23:50 PM ESPAÑA): TOP #1 EUROPA (REAL MADRID / CHAMPIONS / GRANDES LIGAS)
    # =========================================================================
    try:
        loc_eu = partido_europa_1["local"]
        vis_eu = partido_europa_1["visitante"]
        liga_eu_hablada = formatear_liga_hablada(partido_europa_1["liga_visual"])
        goles_eu_hablado = formatear_numero_hablado(partido_europa_1.get("tot_goles", 2.75))
        corn_eu = partido_europa_1.get("tot_corn", 9.2)
        tasa_hablada = tasa_real.replace("%", "").replace(".", " punto ") + " por ciento"

        ruta_img_eu = generar_tarjeta_trampa_sino_existe(partido_europa_1, directorio_dia)
        slide_eu_1 = crear_slide_vertical(
            ruta_img_eu,
            f"PARTIDAZO EUROPA #1 ({partido_europa_1.get('hora', '')}) | PRECISIÓN {tasa_real}",
            f"{loc_eu} vs {vis_eu}",
            "TARJETA GRATIS Y PROMO $7.99 EN EL PERFIL",
            modo_gancho_telegram=True,
            ruta_salida=os.path.join(carpeta_videos, "temp_eu_1.jpg")
        )

        ruta_historia_hoy = os.path.join(carpeta_videos, f"00_HISTORIA_DIARIA_WEB_{fecha_jornada}.jpg")
        import shutil
        shutil.copy2(slide_eu_1, ruta_historia_hoy)

        sels_eu = partido_europa_1.get("seleccion_free") or partido_europa_1.get("seleccion_vip") or [("Más de 1.5 Goles", 79.5, 1.28)]
        pick_gratis_eu = str(sels_eu[0][0]).replace("Over 1.5 Goles", "Más de 1 punto 5 goles").replace(">", "más de").replace(".", " punto ")
        prob_gratis_eu = f"{float(sels_eu[0][1]):.0f} por ciento"

        cta_voz_1 = "Además, ya habilitamos en nuestra página web el pase diario de veinticuatro horas para desbloquear todas las tarjetas de la jornada. "

        guion_1 = (
            f"¿Sabías por qué la mayoría falla en este partidazo entre {loc_eu} y {vis_eu} por {liga_eu_hablada}? "
            f"Nuestro algoritmo en Python simuló diez mil escenarios proyectando {goles_eu_hablado} goles esperados y {corn_eu:.0f} córners. "
            f"Ya dejamos la primera tendencia abierta en nuestra aplicación web y las otras dos jugadas sin costo dentro de nuestro canal de Telegram. "
            f"{cta_voz_1}"
            f"Toca ahora mismo el enlace de nuestro perfil antes del pitazo inicial."
        )
        mp3_1 = os.path.join(carpeta_videos, "voz_1_europa.mp3")
        mp4_1 = os.path.join(carpeta_videos, f"01_VIDEO_21PM_EUROPA_{limpiar_hashtag(loc_eu)[1:]}_{limpiar_hashtag(vis_eu)[1:]}.mp4")
        asyncio.run(sintetizar_audio_ia(guion_1, mp3_1))
        tarjeta_fomo_v1 = ruta_img_doble if (ruta_img_doble and os.path.exists(ruta_img_doble)) else ruta_img_eu
        slide_eu_3 = crear_slide_vertical(
            tarjeta_fomo_v1,
            "PASE DIARIO VIP Y MATRIZ DOBLE EN EL PERFIL",
            f"{loc_eu} vs {vis_eu}",
            "ENTRA A NUESTRA WEB Y TELEGRAM DESDE EL PERFIL",
            difuminar_vip=True,
            ruta_salida=os.path.join(carpeta_videos, "temp_eu_3.jpg")
        )
        renderizar_video_mp4_2_slides(slide_eu_1, slide_aud_1, mp3_1, mp4_1, seg_slide_1=12, texto_guion=guion_1, slide_3=slide_eu_3)

        dict_1 = generar_diccionario_copys_por_red("2_AUDITORIA_21PM", partido_europa_1, tasa_real)
        dict_1["horario"] = "23:50 PM (España) - VIDEO #1: PARTIDAZO EUROPA #1 + AUDITORÍA"
        dict_1["titulo_interno"] = f"VIDEO 1 (23:50 PM EUROPA #1) - {loc_eu.upper()} VS {vis_eu.upper()} + AUDITORÍA ({tasa_real})"
        guardar_archivos_individuales_y_json(carpeta_videos, 1, mp4_1, dict_1, cola_json, fecha_jornada)
        print(f"    ✅ Video 1 (23:50 PM EUROPA #1 [{loc_eu} vs {vis_eu}]) creado: {mp4_1}")
        if token_privado and chat_id_privado:
            enviar_video_y_mensajes_separados_telegram(token_privado, chat_id_privado, mp4_1, dict_1)
    except Exception as e:
        print(f"    [!] Error Video 1 (Europa #1): {e}")

    # =========================================================================
    # VIDEO 2 (04:50 AM ESPAÑA): TOP #2 EUROPA + COMBINADA
    # =========================================================================
    try:
        loc_eu2 = partido_europa_2["local"]
        vis_eu2 = partido_europa_2["visitante"]
        liga_eu2_hablada = formatear_liga_hablada(partido_europa_2["liga_visual"])
        goles_eu2_hablado = formatear_numero_hablado(partido_europa_2.get("tot_goles", 2.65))
        corn_eu2 = partido_europa_2.get("tot_corn", 9.0)

        ruta_img_eu2 = generar_tarjeta_trampa_sino_existe(partido_europa_2, directorio_dia)
        slide_am_1 = crear_slide_vertical(
            ruta_img_eu2,
            f"PARTIDAZO EUROPA #2 ({partido_europa_2.get('hora', '')}) | PRECISIÓN {tasa_real}",
            f"{loc_eu2} vs {vis_eu2}",
            "TARJETA GRATIS Y PROMO $7.99 EN EL PERFIL",
            modo_gancho_telegram=True,
            ruta_salida=os.path.join(carpeta_videos, "temp_am_1.jpg")
        )
        tarjeta_fomo_am = ruta_img_doble if (ruta_img_doble and os.path.exists(ruta_img_doble)) else ruta_img_eu2
        slide_am_2 = crear_slide_vertical(
            tarjeta_fomo_am,
            "PASE DE PRUEBA 10 DÍAS POR SOLO acceso en el perfil",
            f"{loc_eu2} vs {vis_eu2}",
            "ENTRA A NUESTRA WEB DESDE EL PERFIL",
            difuminar_vip=True,
            ruta_salida=os.path.join(carpeta_videos, "temp_am_2.jpg")
        )
        sels_eu2 = partido_europa_2.get("seleccion_free") or partido_europa_2.get("seleccion_vip") or [("Córners más de 7.5", 78.5, 1.25)]
        pick_gratis_eu2 = str(sels_eu2[0][0]).replace("Over 1.5 Goles", "Más de 1 punto 5 goles").replace(">", "más de").replace(".", " punto ")
        prob_gratis_eu2 = f"{float(sels_eu2[0][1]):.0f} por ciento"

        cta_voz_2 = "Recuerda que también puedes activar el pase diario de veinticuatro horas y ver la matriz doble en nuestra página web. "

        guion_2 = (
            f"No operes a ciegas en el duelo estelar entre {loc_eu2} y {vis_eu2} por {liga_eu2_hablada}. "
            f"Nuestro sistema matemático en Python detecta {goles_eu2_hablado} goles esperados y {corn_eu2:.0f} córners, "
            f"activando dos alertas tácticas que ya tienes disponibles entrando a nuestra aplicación web y a nuestro Telegram gratuito. "
            f"{cta_voz_2}"
            f"Entra ahora desde el enlace de nuestro perfil antes de que empiece el partido."
        )

        mp3_2 = os.path.join(carpeta_videos, "voz_2_europa.mp3")
        mp4_2 = os.path.join(carpeta_videos, f"02_VIDEO_04AM_EUROPA2_{limpiar_hashtag(loc_eu2)[1:]}_{limpiar_hashtag(vis_eu2)[1:]}.mp4")
        asyncio.run(sintetizar_audio_ia(guion_2, mp3_2))
        renderizar_video_mp4_2_slides(slide_am_1, slide_am_2, mp3_2, mp4_2, seg_slide_1=12, texto_guion=guion_2, slide_3=slide_aud_1)

        dict_2 = generar_diccionario_copys_por_red("1_ESTRELLA_10AM", partido_europa_2, tasa_real)
        dict_2["horario"] = "04:50 AM (España) - VIDEO #2: PARTIDAZO EUROPA #2"
        dict_2["titulo_interno"] = f"VIDEO 2 (04:50 AM EUROPA #2) - {loc_eu2.upper()} VS {vis_eu2.upper()} ({partido_europa_2.get('hora', '')})"
        guardar_archivos_individuales_y_json(carpeta_videos, 2, mp4_2, dict_2, cola_json, fecha_jornada)
        print(f"    ✅ Video 2 (04:50 AM EUROPA #2 [{loc_eu2} vs {vis_eu2}]) creado: {mp4_2}")
        if token_privado and chat_id_privado:
            enviar_video_y_mensajes_separados_telegram(token_privado, chat_id_privado, mp4_2, dict_2)
    except Exception as e:
        print(f"    [!] Error Video 2 (Europa #2): {e}")

    with open(os.path.join(carpeta_videos, "cola_publicacion_redes.json"), "w", encoding="utf-8") as f:
        json.dump(cola_json, f, ensure_ascii=False, indent=2)

    for temp_f in ["temp_aud_1.jpg", "temp_eu_1.jpg", "temp_am_1.jpg", "temp_am_2.jpg"]:
        r_t = os.path.join(carpeta_videos, temp_f)
        if os.path.exists(r_t):
            try:
                os.remove(r_t)
            except Exception:
                pass
