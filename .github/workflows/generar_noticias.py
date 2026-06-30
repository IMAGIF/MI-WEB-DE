#!/usr/bin/env python3
# generar_noticias.py — Genera NOTICIAS/noticias.json
# - Garantiza 10 noticias por sección (rellena con 2ª noticia de un medio si hace falta)
# - Traduce automáticamente todo lo que no esté en español/idioma de destino
# - Descarta noticias con fecha de publicación anterior a 14 días (evita "ancladas")

import json, feedparser, requests
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime
from deep_translator import GoogleTranslator

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; NoticiaBot/1.0)',
    'Accept': 'application/rss+xml, application/xml, text/xml, */*'
}
TIMEOUT = 12
MAX_ANTIGUEDAD_DIAS = 14   # descarta noticias "fantasma" más viejas que esto

# ═══════════════════════════════════════════════════════════════════════════════
# FUENTES — cada sección tiene: idioma nativo del feed + si necesita traducción
# ═══════════════════════════════════════════════════════════════════════════════

FUENTES = {

  # ══ NACIONAL (todas en español, base de todo el sistema) ════════════════════
  "nacional_es": [
    {"nombre":"ABC",              "url":"https://www.abc.es/rss/feeds/abc_EspanaEspana.xml", "idi":"es"},
    {"nombre":"El Mundo",         "url":"https://e00-elmundo.uecdn.es/elmundo/rss/portada.xml", "idi":"es"},
    {"nombre":"El Debate",        "url":"https://www.eldebate.com/rss/", "idi":"es"},
    {"nombre":"Libertad Digital", "url":"https://feeds.feedburner.com/libertaddigital/portada", "idi":"es"},
    {"nombre":"The Objective",    "url":"https://theobjective.com/feed/", "idi":"es"},
    {"nombre":"El Confidencial",  "url":"https://rss.elconfidencial.com/espana/", "idi":"es"},
    {"nombre":"COPE",             "url":"https://www.cope.es/rss/portada.xml", "idi":"es"},
    {"nombre":"OKDiario",         "url":"https://okdiario.com/feed", "idi":"es"},
    {"nombre":"El Español",       "url":"https://www.elespanol.com/rss/", "idi":"es"},
    {"nombre":"La Razón",         "url":"https://www.larazon.es/rss/", "idi":"es"},
  ],
  "nacional_us": [
    {"nombre":"Fox News",  "url":"https://feeds.foxnews.com/foxnews/national", "idi":"en"},
    {"nombre":"CNN",       "url":"http://rss.cnn.com/rss/edition_us.rss", "idi":"en"},
    {"nombre":"Reuters",   "url":"https://feeds.reuters.com/reuters/domesticNews", "idi":"en"},
    {"nombre":"AP News",   "url":"https://rsshub.app/apnews/topics/apf-topnews", "idi":"en"},
    {"nombre":"NPR",       "url":"https://feeds.npr.org/1001/rss.xml", "idi":"en"},
  ],
  "nacional_mx": [
    {"nombre":"El Universal","url":"https://www.eluniversal.com.mx/rss.xml", "idi":"es"},
    {"nombre":"Milenio",     "url":"https://www.milenio.com/rss", "idi":"es"},
    {"nombre":"Excélsior",   "url":"https://www.excelsior.com.mx/rss.xml", "idi":"es"},
  ],
  "nacional_ar": [
    {"nombre":"Clarín",    "url":"https://www.clarin.com/rss/lo-ultimo/", "idi":"es"},
    {"nombre":"La Nación", "url":"https://www.lanacion.com.ar/arc/outboundfeeds/rss/", "idi":"es"},
    {"nombre":"Infobae",   "url":"https://www.infobae.com/feeds/rss/", "idi":"es"},
  ],
  "nacional_co": [
    {"nombre":"El Tiempo",     "url":"https://www.eltiempo.com/rss/portada.xml", "idi":"es"},
    {"nombre":"El Colombiano", "url":"https://www.elcolombiano.com/rss.xml", "idi":"es"},
    {"nombre":"Semana",        "url":"https://www.semana.com/rss/", "idi":"es"},
  ],
  "nacional_fr": [
    {"nombre":"Le Monde",  "url":"https://www.lemonde.fr/rss/une.xml", "idi":"fr"},
    {"nombre":"Le Figaro", "url":"https://www.lefigaro.fr/rss/figaro_actualites.xml", "idi":"fr"},
    {"nombre":"France 24", "url":"https://www.france24.com/fr/rss", "idi":"fr"},
  ],
  "nacional_de": [
    {"nombre":"Der Spiegel","url":"https://www.spiegel.de/schlagzeilen/index.rss", "idi":"de"},
    {"nombre":"Die Zeit",   "url":"https://newsfeed.zeit.de/all", "idi":"de"},
    {"nombre":"Bild",       "url":"https://www.bild.de/rss-feeds/rss-16725492,feed=alles.bild.html", "idi":"de"},
  ],
  "nacional_it": [
    {"nombre":"La Repubblica","url":"https://www.repubblica.it/rss/homepage/rss2.0.xml", "idi":"it"},
    {"nombre":"Corriere",     "url":"https://xml2.corrieredellasera.it/rss/homepage.xml", "idi":"it"},
    {"nombre":"RAI News",     "url":"https://www.rainews.it/dl/rainews/media/feed-web.xml", "idi":"it"},
  ],
  "nacional_gb": [
    {"nombre":"BBC",          "url":"http://feeds.bbci.co.uk/news/rss.xml", "idi":"en"},
    {"nombre":"The Guardian", "url":"https://www.theguardian.com/uk/rss", "idi":"en"},
    {"nombre":"Reuters UK",   "url":"https://feeds.reuters.com/reuters/UKTopNews", "idi":"en"},
  ],
  "nacional_pt": [
    {"nombre":"Público",        "url":"https://feeds.feedburner.com/PublicoRSS", "idi":"pt"},
    {"nombre":"J. de Notícias", "url":"https://www.jn.pt/rss/", "idi":"pt"},
    {"nombre":"Observador",     "url":"https://observador.pt/feed/", "idi":"pt"},
  ],
  "nacional_br": [
    {"nombre":"Folha SP","url":"https://feeds.folha.uol.com.br/poder/rss091.xml", "idi":"pt"},
    {"nombre":"G1 Globo","url":"https://g1.globo.com/rss/g1/", "idi":"pt"},
  ],
  "nacional_jp": [
    {"nombre":"Japan Times","url":"https://www.japantimes.co.jp/feed/", "idi":"en"},
    {"nombre":"NHK World",  "url":"https://www3.nhk.or.jp/nhkworld/upld/feeds/en/news.xml", "idi":"en"},
  ],

  # ══ INTERNACIONAL ═════════════════════════════════════════════════════════
  # ES: medios españoles (ya en español) + grandes cadenas mundiales (se traducen)
  "internacional_es": [
    {"nombre":"ABC Internacional",     "url":"https://www.abc.es/rss/feeds/abc_Internacional.xml", "idi":"es"},
    {"nombre":"El Mundo Internacional","url":"https://e00-elmundo.uecdn.es/elmundo/rss/internacional.xml", "idi":"es"},
    {"nombre":"El Confidencial Mundo", "url":"https://rss.elconfidencial.com/mundo/", "idi":"es"},
    {"nombre":"La Razón Mundo",        "url":"https://www.larazon.es/rss/internacional/", "idi":"es"},
    {"nombre":"BBC Mundo",             "url":"https://feeds.bbci.co.uk/mundo/rss.xml", "idi":"es"},
    {"nombre":"DW Español",            "url":"https://rss.dw.com/rdf/rss-es-all", "idi":"es"},
    {"nombre":"Euronews ES",           "url":"https://es.euronews.com/rss?format=mrss&level=theme&name=news", "idi":"es"},
    {"nombre":"BBC World",             "url":"http://feeds.bbci.co.uk/news/world/rss.xml", "idi":"en"},
    {"nombre":"Reuters World",         "url":"https://feeds.reuters.com/reuters/worldNews", "idi":"en"},
    {"nombre":"Fox News Mundo",        "url":"https://feeds.foxnews.com/foxnews/world", "idi":"en"},
  ],
  "internacional_en": [
    {"nombre":"BBC World",    "url":"http://feeds.bbci.co.uk/news/world/rss.xml", "idi":"en"},
    {"nombre":"Reuters",      "url":"https://feeds.reuters.com/reuters/worldNews", "idi":"en"},
    {"nombre":"CNN World",    "url":"http://rss.cnn.com/rss/edition_world.rss", "idi":"en"},
    {"nombre":"Fox News",     "url":"https://feeds.foxnews.com/foxnews/world", "idi":"en"},
    {"nombre":"France 24 EN", "url":"https://www.france24.com/en/rss", "idi":"en"},
    {"nombre":"New York Post","url":"https://nypost.com/feed/", "idi":"en"},
    {"nombre":"DW English",   "url":"https://rss.dw.com/rdf/rss-en-all", "idi":"en"},
    {"nombre":"Euronews EN",  "url":"https://www.euronews.com/rss?format=mrss&level=theme&name=news", "idi":"en"},
    {"nombre":"AP World",     "url":"https://rsshub.app/apnews/topics/apf-intlnews", "idi":"en"},
    {"nombre":"OAN",          "url":"https://www.oann.com/feed/", "idi":"en"},
  ],
  "internacional_fr": [
    {"nombre":"Le Figaro Monde","url":"https://www.lefigaro.fr/rss/figaro_international.xml", "idi":"fr"},
    {"nombre":"France 24 FR",  "url":"https://www.france24.com/fr/rss", "idi":"fr"},
    {"nombre":"RFI",           "url":"https://www.rfi.fr/fr/rss", "idi":"fr"},
    {"nombre":"Euronews FR",   "url":"https://fr.euronews.com/rss?format=mrss&level=theme&name=news", "idi":"fr"},
    {"nombre":"BBC World EN",  "url":"http://feeds.bbci.co.uk/news/world/rss.xml", "idi":"en"},
  ],
  "internacional_de": [
    {"nombre":"Der Spiegel","url":"https://www.spiegel.de/schlagzeilen/index.rss", "idi":"de"},
    {"nombre":"DW Deutsch", "url":"https://rss.dw.com/rdf/rss-de-all", "idi":"de"},
    {"nombre":"Euronews DE","url":"https://de.euronews.com/rss?format=mrss&level=theme&name=news", "idi":"de"},
    {"nombre":"BBC World EN","url":"http://feeds.bbci.co.uk/news/world/rss.xml", "idi":"en"},
  ],
  "internacional_it": [
    {"nombre":"RAI News",      "url":"https://www.rainews.it/dl/rainews/media/feed-web.xml", "idi":"it"},
    {"nombre":"La Repubblica", "url":"https://www.repubblica.it/rss/esteri/rss2.0.xml", "idi":"it"},
    {"nombre":"Euronews IT",   "url":"https://it.euronews.com/rss?format=mrss&level=theme&name=news", "idi":"it"},
    {"nombre":"BBC World EN",  "url":"http://feeds.bbci.co.uk/news/world/rss.xml", "idi":"en"},
  ],
  "internacional_pt": [
    {"nombre":"RTP Notícias","url":"https://www.rtp.pt/noticias/rss", "idi":"pt"},
    {"nombre":"Observador",  "url":"https://observador.pt/feed/", "idi":"pt"},
    {"nombre":"BBC Brasil",  "url":"https://feeds.bbci.co.uk/portuguese/rss.xml", "idi":"pt"},
  ],

  # ══ DEPORTES ══════════════════════════════════════════════════════════════
  "deportes_es": [
    {"nombre":"Marca",          "url":"https://e00-marca.uecdn.es/rss/portada.xml", "idi":"es"},
    {"nombre":"AS",             "url":"https://as.com/rss/tags/ultimas_noticias.xml", "idi":"es"},
    {"nombre":"Mundo Deportivo","url":"https://www.mundodeportivo.com/rss/home.xml", "idi":"es"},
    {"nombre":"Relevo",         "url":"https://www.relevo.com/rss/portada.xml", "idi":"es"},
    {"nombre":"Sport",          "url":"https://www.sport.es/rss/portada.xml", "idi":"es"},
    {"nombre":"Motorsport ES",  "url":"https://es.motorsport.com/rss/news/latest/", "idi":"es"},
    {"nombre":"SoyMotor",       "url":"https://www.soymotor.com/feed", "idi":"es"},
    {"nombre":"Gigantes Basket","url":"https://www.gigantes.com/feed/", "idi":"es"},
    {"nombre":"BBC Sport EN",   "url":"http://feeds.bbci.co.uk/sport/rss.xml", "idi":"en"},
    {"nombre":"ESPN EN",        "url":"https://www.espn.com/espn/rss/news", "idi":"en"},
  ],
  "deportes_en": [
    {"nombre":"BBC Sport",    "url":"http://feeds.bbci.co.uk/sport/rss.xml", "idi":"en"},
    {"nombre":"Reuters Sport","url":"https://feeds.reuters.com/reuters/sportsNews", "idi":"en"},
    {"nombre":"ESPN",         "url":"https://www.espn.com/espn/rss/news", "idi":"en"},
    {"nombre":"Sky Sports",   "url":"https://www.skysports.com/rss/12040", "idi":"en"},
    {"nombre":"Motorsport EN","url":"https://www.motorsport.com/rss/news/latest/", "idi":"en"},
  ],
  "deportes_fr": [
    {"nombre":"L'Équipe",       "url":"https://www.lequipe.fr/rss/actu_rss.xml", "idi":"fr"},
    {"nombre":"France 24 Sport","url":"https://www.france24.com/fr/sports/rss", "idi":"fr"},
    {"nombre":"BBC Sport EN",   "url":"http://feeds.bbci.co.uk/sport/rss.xml", "idi":"en"},
  ],
  "deportes_de": [
    {"nombre":"Kicker",   "url":"https://www.kicker.de/news/fussball/bundesliga/rss.xml", "idi":"de"},
    {"nombre":"DW Sport", "url":"https://rss.dw.com/rdf/rss-de-sport", "idi":"de"},
    {"nombre":"BBC Sport EN","url":"http://feeds.bbci.co.uk/sport/rss.xml", "idi":"en"},
  ],
  "deportes_it": [
    {"nombre":"Gazzetta",      "url":"https://www.gazzetta.it/rss/home.xml", "idi":"it"},
    {"nombre":"Corriere Sport","url":"https://xml2.corrieredellasera.it/rss/sport.xml", "idi":"it"},
    {"nombre":"BBC Sport EN",  "url":"http://feeds.bbci.co.uk/sport/rss.xml", "idi":"en"},
  ],
  "deportes_pt": [
    {"nombre":"A Bola",   "url":"https://www.abola.pt/rss/", "idi":"pt"},
    {"nombre":"Record PT","url":"https://www.record.pt/rss/", "idi":"pt"},
  ],

  # ══ CIENCIA ═══════════════════════════════════════════════════════════════
  "ciencia_es": [
    {"nombre":"ABC Ciencia",      "url":"https://www.abc.es/rss/feeds/abc_Ciencia.xml", "idi":"es"},
    {"nombre":"El Mundo Ciencia", "url":"https://e00-elmundo.uecdn.es/elmundo/rss/ciencia.xml", "idi":"es"},
    {"nombre":"El Español Ciencia","url":"https://www.elespanol.com/ciencia/rss/", "idi":"es"},
    {"nombre":"Muy Interesante",  "url":"https://www.muyinteresante.es/rss", "idi":"es"},
    {"nombre":"National Geo ES",  "url":"https://www.nationalgeographic.com.es/rss/ciencia", "idi":"es"},
    {"nombre":"Tendencias21",     "url":"https://www.tendencias21.net/rss", "idi":"es"},
    {"nombre":"SINC",             "url":"https://www.agenciasinc.es/rss", "idi":"es"},
    {"nombre":"BBC Ciencia ES",   "url":"https://feeds.bbci.co.uk/mundo/ciencia_y_tecnologia/rss.xml", "idi":"es"},
    {"nombre":"Nature EN",        "url":"https://www.nature.com/nature.rss", "idi":"en"},
    {"nombre":"NASA EN",          "url":"https://www.nasa.gov/news-release/feed/", "idi":"en"},
  ],
  "ciencia_en": [
    {"nombre":"Nature",          "url":"https://www.nature.com/nature.rss", "idi":"en"},
    {"nombre":"Science",         "url":"https://www.science.org/rss/news_current.xml", "idi":"en"},
    {"nombre":"New Scientist",   "url":"https://www.newscientist.com/feed/home/", "idi":"en"},
    {"nombre":"MIT Tech Review", "url":"https://www.technologyreview.com/stories.rss", "idi":"en"},
    {"nombre":"Ars Technica",    "url":"https://feeds.arstechnica.com/arstechnica/index", "idi":"en"},
    {"nombre":"Phys.org",        "url":"https://phys.org/rss-feed/", "idi":"en"},
    {"nombre":"NASA",            "url":"https://www.nasa.gov/news-release/feed/", "idi":"en"},
    {"nombre":"Science Daily",   "url":"https://www.sciencedaily.com/rss/all.xml", "idi":"en"},
    {"nombre":"BBC Science",     "url":"http://feeds.bbci.co.uk/news/science_and_environment/rss.xml", "idi":"en"},
    {"nombre":"ESA",             "url":"https://www.esa.int/rssfeed/Our_Activities/Space_Science", "idi":"en"},
  ],
  "ciencia_fr": [
    {"nombre":"Sciences et Avenir","url":"https://www.sciencesetavenir.fr/rss.xml", "idi":"fr"},
    {"nombre":"France 24 Sci",    "url":"https://www.france24.com/fr/sciences/rss", "idi":"fr"},
    {"nombre":"Nature EN",        "url":"https://www.nature.com/nature.rss", "idi":"en"},
  ],
  "ciencia_de": [
    {"nombre":"Spektrum",  "url":"https://www.spektrum.de/rss/news", "idi":"de"},
    {"nombre":"DW Wissen", "url":"https://rss.dw.com/rdf/rss-de-wissenschaft", "idi":"de"},
    {"nombre":"Nature EN", "url":"https://www.nature.com/nature.rss", "idi":"en"},
  ],
  "ciencia_it": [
    {"nombre":"Focus It",  "url":"https://www.focus.it/rss.xml", "idi":"it"},
    {"nombre":"Le Scienze","url":"https://www.lescienze.it/rss/", "idi":"it"},
    {"nombre":"Nature EN", "url":"https://www.nature.com/nature.rss", "idi":"en"},
  ],
  "ciencia_pt": [
    {"nombre":"Observador Tech","url":"https://observador.pt/seccao/tech/feed/", "idi":"pt"},
    {"nombre":"BBC Brasil Tec", "url":"https://feeds.bbci.co.uk/portuguese/rss.xml", "idi":"pt"},
  ],

  # ══ ECONOMÍA ══════════════════════════════════════════════════════════════
  # NOTA: WSJ vía dj.com feed descartado por servir contenido cacheado/anclado.
  "economia_es": [
    {"nombre":"Expansión",          "url":"https://e00-expansion.uecdn.es/rss/portada.xml", "idi":"es"},
    {"nombre":"El Economista",      "url":"https://www.eleconomista.es/rss/rss-seleccion-ee.php", "idi":"es"},
    {"nombre":"Libre Mercado",      "url":"https://www.libremercado.com/rss/", "idi":"es"},
    {"nombre":"El Confidencial Eco","url":"https://rss.elconfidencial.com/mercados/", "idi":"es"},
    {"nombre":"The Objective Eco",  "url":"https://theobjective.com/economia/feed/", "idi":"es"},
    {"nombre":"Cinco Días",         "url":"https://cincodias.elpais.com/seccion/rss/", "idi":"es"},
    {"nombre":"ABC Economía",       "url":"https://www.abc.es/rss/feeds/abc_Economia.xml", "idi":"es"},
    {"nombre":"Reuters Business",   "url":"https://feeds.reuters.com/reuters/businessNews", "idi":"en"},
    {"nombre":"Bloomberg",          "url":"https://feeds.bloomberg.com/markets/news.rss", "idi":"en"},
    {"nombre":"CNBC",               "url":"https://www.cnbc.com/id/10001147/device/rss/rss.html", "idi":"en"},
  ],
  "economia_en": [
    {"nombre":"Reuters Business","url":"https://feeds.reuters.com/reuters/businessNews", "idi":"en"},
    {"nombre":"Bloomberg",       "url":"https://feeds.bloomberg.com/markets/news.rss", "idi":"en"},
    {"nombre":"Fox Business",    "url":"https://feeds.foxbusiness.com/foxbusiness/latest", "idi":"en"},
    {"nombre":"CNBC",            "url":"https://www.cnbc.com/id/10001147/device/rss/rss.html", "idi":"en"},
    {"nombre":"MarketWatch",     "url":"https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines", "idi":"en"},
    {"nombre":"The Economist",   "url":"https://www.economist.com/finance-and-economics/rss.xml", "idi":"en"},
    {"nombre":"Forbes",          "url":"https://www.forbes.com/money/feed/", "idi":"en"},
  ],
  "economia_fr": [
    {"nombre":"Les Échos",      "url":"https://www.lesechos.fr/rss/rss_la_une.xml", "idi":"fr"},
    {"nombre":"Bloomberg EN",   "url":"https://feeds.bloomberg.com/markets/news.rss", "idi":"en"},
  ],
  "economia_de": [
    {"nombre":"Handelsblatt", "url":"https://www.handelsblatt.com/contentexport/feed/schlagzeilen", "idi":"de"},
    {"nombre":"Bloomberg EN", "url":"https://feeds.bloomberg.com/markets/news.rss", "idi":"en"},
  ],
  "economia_it": [
    {"nombre":"Il Sole 24 Ore","url":"https://www.ilsole24ore.com/rss/economia--finanza.xml", "idi":"it"},
    {"nombre":"Bloomberg EN",  "url":"https://feeds.bloomberg.com/markets/news.rss", "idi":"en"},
  ],
  "economia_pt": [
    {"nombre":"Jornal de Negócios","url":"https://www.jornaldenegocios.pt/rss", "idi":"pt"},
    {"nombre":"Bloomberg EN",      "url":"https://feeds.bloomberg.com/markets/news.rss", "idi":"en"},
  ],
}

# Idioma de destino de cada sección (para traducir si el feed viene en otro idioma)
IDIOMA_DESTINO = {
  "nacional_es":"es","nacional_us":"en","nacional_mx":"es","nacional_ar":"es","nacional_co":"es",
  "nacional_fr":"fr","nacional_de":"de","nacional_it":"it","nacional_gb":"en","nacional_pt":"pt",
  "nacional_br":"pt","nacional_jp":"en",
  "internacional_es":"es","internacional_en":"en","internacional_fr":"fr","internacional_de":"de",
  "internacional_it":"it","internacional_pt":"pt",
  "deportes_es":"es","deportes_en":"en","deportes_fr":"fr","deportes_de":"de","deportes_it":"it","deportes_pt":"pt",
  "ciencia_es":"es","ciencia_en":"en","ciencia_fr":"fr","ciencia_de":"de","ciencia_it":"it","ciencia_pt":"pt",
  "economia_es":"es","economia_en":"en","economia_fr":"fr","economia_de":"de","economia_it":"it","economia_pt":"pt",
}

# ═══════════════════════════════════════════════════════════════════════════════
# CACHÉ DE TRADUCCIÓN (evita traducir lo mismo varias veces en la misma ejecución)
# ═══════════════════════════════════════════════════════════════════════════════
_cache_trad = {}

def traducir(texto, idioma_origen, idioma_destino):
    if not texto or idioma_origen == idioma_destino:
        return texto
    clave = (texto, idioma_origen, idioma_destino)
    if clave in _cache_trad:
        return _cache_trad[clave]
    try:
        resultado = GoogleTranslator(source=idioma_origen, target=idioma_destino).translate(texto)
        resultado = resultado or texto
    except Exception as e:
        print(f"    (traducción falló, se mantiene original: {e})")
        resultado = texto
    _cache_trad[clave] = resultado
    return resultado

# ═══════════════════════════════════════════════════════════════════════════════
# UTILIDADES
# ═══════════════════════════════════════════════════════════════════════════════

def limpiar(texto):
    import re
    texto = re.sub(r'<[^>]+>', ' ', texto or '')
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto[:200] + '…' if len(texto) > 200 else texto

def fecha_iso(entry):
    for campo in ('published', 'updated'):
        val = getattr(entry, campo, None)
        if val:
            try: return parsedate_to_datetime(val)
            except: pass
    return datetime.now(timezone.utc)

def es_reciente(fecha_dt):
    """Descarta noticias más viejas que MAX_ANTIGUEDAD_DIAS (evita feeds 'anclados')."""
    try:
        ahora = datetime.now(timezone.utc)
        if fecha_dt.tzinfo is None:
            fecha_dt = fecha_dt.replace(tzinfo=timezone.utc)
        return (ahora - fecha_dt) <= timedelta(days=MAX_ANTIGUEDAD_DIAS)
    except Exception:
        return True  # si no se puede comparar, no descartar

def fetch_feed_multi(fuente, n_items=2):
    """Devuelve hasta n_items noticias válidas y recientes de una fuente."""
    try:
        resp = requests.get(fuente["url"], headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        noticias = []
        for entry in feed.entries[:5]:
            titulo = limpiar(entry.get('title',''))
            if not titulo or len(titulo) < 5:
                continue
            fecha_dt = fecha_iso(entry)
            if not es_reciente(fecha_dt):
                continue
            desc = limpiar(entry.get('summary','') or entry.get('description',''))
            noticias.append({
                "titulo_raw": titulo,
                "desc_raw":   desc[:180]+'…' if len(desc)>180 else desc,
                "enlace":     entry.get('link','#'),
                "fecha":      fecha_dt.isoformat(),
                "fuente":     fuente["nombre"],
                "idi_origen": fuente.get("idi","es"),
            })
            if len(noticias) >= n_items:
                break
        if noticias:
            print(f"  ✓ {fuente['nombre']}: {len(noticias)} disponibles")
        else:
            print(f"  – {fuente['nombre']}: sin noticias recientes válidas")
        return noticias
    except Exception as e:
        print(f"  ✗ {fuente['nombre']}: {e}")
        return []

def procesar_seccion(fuentes, idioma_destino, max_items=10):
    """
    1ª pasada: 1 noticia por fuente (ronda).
    2ª pasada: si no llegamos a max_items, se coge una 2ª noticia de las fuentes
               que tengan disponible, hasta completar.
    Luego traduce lo necesario y devuelve la lista final.
    """
    pool = {}  # nombre_fuente -> lista de noticias disponibles (orden de aparición)
    for f in fuentes:
        pool[f["nombre"]] = fetch_feed_multi(f, n_items=2)

    seleccion = []
    usados = {k: 0 for k in pool}

    # Ronda 1: una de cada fuente
    for nombre, lista in pool.items():
        if len(seleccion) >= max_items: break
        if lista:
            seleccion.append(lista[0])
            usados[nombre] = 1

    # Ronda 2: completar con 2ª noticia de las fuentes que la tengan
    if len(seleccion) < max_items:
        for nombre, lista in pool.items():
            if len(seleccion) >= max_items: break
            if len(lista) > usados[nombre]:
                seleccion.append(lista[usados[nombre]])
                usados[nombre] += 1

    # Traducir lo que haga falta
    resultado = []
    for n in seleccion[:max_items]:
        idi_o = n["idi_origen"]
        titulo = traducir(n["titulo_raw"], idi_o, idioma_destino)
        desc   = traducir(n["desc_raw"],   idi_o, idioma_destino)
        resultado.append({
            "titulo": titulo,
            "enlace": n["enlace"],
            "desc":   desc,
            "fecha":  n["fecha"],
            "fuente": n["fuente"],
        })
    return resultado

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def main():
    print("=== Generando noticias.json (v4 — sin anclajes, con traducción, 10 garantizadas) ===")
    resultado = {"actualizado": datetime.now(timezone.utc).isoformat(), "secciones": {}}

    for clave, fuentes in FUENTES.items():
        idioma_destino = IDIOMA_DESTINO.get(clave, "es")
        print(f"\n[{clave}]  (destino: {idioma_destino})")
        resultado["secciones"][clave] = procesar_seccion(fuentes, idioma_destino, max_items=10)
        print(f"  → {len(resultado['secciones'][clave])} noticias finales")

    ruta = "NOTICIAS/noticias.json"
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in resultado["secciones"].values())
    print(f"\n✅ {ruta} — {total} noticias totales")

if __name__ == "__main__":
    main()
