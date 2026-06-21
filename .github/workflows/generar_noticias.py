#!/usr/bin/env python3
# generar_noticias.py — genera NOTICIAS/noticias.json con secciones multiidioma

import json, feedparser, requests
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (compatible; NoticiaBot/1.0)',
    'Accept': 'application/rss+xml, application/xml, text/xml, */*'
}
TIMEOUT = 12

# ═══════════════════════════════════════════════════════════════════════════════
# FUENTES RSS organizadas por sección e idioma
# ═══════════════════════════════════════════════════════════════════════════════

FUENTES = {

  # ── NACIONAL ──────────────────────────────────────────────────────────────
  "nacional_es": [
    {"nombre":"COPE",             "url":"https://www.cope.es/rss/portada.xml"},
    {"nombre":"Libertad Digital", "url":"https://feeds.feedburner.com/libertaddigital/portada"},
    {"nombre":"El Debate",        "url":"https://www.eldebate.com/rss/"},
    {"nombre":"El Mundo",         "url":"https://e00-elmundo.uecdn.es/elmundo/rss/portada.xml"},
    {"nombre":"OKDiario",         "url":"https://okdiario.com/feed"},
    {"nombre":"El Confidencial",  "url":"https://rss.elconfidencial.com/espana/"},
    {"nombre":"The Objective",    "url":"https://theobjective.com/feed/"},
    {"nombre":"La Razón",         "url":"https://www.larazon.es/rss/"},
    {"nombre":"El Español",       "url":"https://www.elespanol.com/rss/"},
    {"nombre":"ABC",              "url":"https://www.abc.es/rss/feeds/abc_EspanaEspana.xml"},
  ],
  "nacional_en": [
    {"nombre":"Fox News",  "url":"https://feeds.foxnews.com/foxnews/national"},
    {"nombre":"CNN",       "url":"http://rss.cnn.com/rss/edition_us.rss"},
    {"nombre":"Reuters",   "url":"https://feeds.reuters.com/reuters/domesticNews"},
    {"nombre":"AP News",   "url":"https://rsshub.app/apnews/topics/apf-topnews"},
    {"nombre":"NPR",       "url":"https://feeds.npr.org/1001/rss.xml"},
  ],
  "nacional_us": [  # alias de en para EEUU
    {"nombre":"Fox News",  "url":"https://feeds.foxnews.com/foxnews/national"},
    {"nombre":"CNN",       "url":"http://rss.cnn.com/rss/edition_us.rss"},
    {"nombre":"Reuters",   "url":"https://feeds.reuters.com/reuters/domesticNews"},
    {"nombre":"AP News",   "url":"https://rsshub.app/apnews/topics/apf-topnews"},
    {"nombre":"NPR",       "url":"https://feeds.npr.org/1001/rss.xml"},
  ],
  "nacional_mx": [
    {"nombre":"El Universal","url":"https://www.eluniversal.com.mx/rss.xml"},
    {"nombre":"Milenio",     "url":"https://www.milenio.com/rss"},
    {"nombre":"Excélsior",   "url":"https://www.excelsior.com.mx/rss.xml"},
  ],
  "nacional_ar": [
    {"nombre":"Clarín",    "url":"https://www.clarin.com/rss/lo-ultimo/"},
    {"nombre":"La Nación", "url":"https://www.lanacion.com.ar/arc/outboundfeeds/rss/"},
    {"nombre":"Infobae",   "url":"https://www.infobae.com/feeds/rss/"},
  ],
  "nacional_co": [
    {"nombre":"El Tiempo",     "url":"https://www.eltiempo.com/rss/portada.xml"},
    {"nombre":"El Colombiano", "url":"https://www.elcolombiano.com/rss.xml"},
    {"nombre":"Semana",        "url":"https://www.semana.com/rss/"},
  ],
  "nacional_fr": [
    {"nombre":"Le Monde",  "url":"https://www.lemonde.fr/rss/une.xml"},
    {"nombre":"Le Figaro", "url":"https://www.lefigaro.fr/rss/figaro_actualites.xml"},
    {"nombre":"France 24", "url":"https://www.france24.com/fr/rss"},
  ],
  "nacional_de": [
    {"nombre":"Der Spiegel","url":"https://www.spiegel.de/schlagzeilen/index.rss"},
    {"nombre":"Die Zeit",   "url":"https://newsfeed.zeit.de/all"},
    {"nombre":"Bild",       "url":"https://www.bild.de/rss-feeds/rss-16725492,feed=alles.bild.html"},
  ],
  "nacional_it": [
    {"nombre":"La Repubblica","url":"https://www.repubblica.it/rss/homepage/rss2.0.xml"},
    {"nombre":"Corriere",     "url":"https://xml2.corrieredellasera.it/rss/homepage.xml"},
    {"nombre":"RAI News",     "url":"https://www.rainews.it/dl/rainews/media/feed-web.xml"},
  ],
  "nacional_gb": [
    {"nombre":"BBC",          "url":"http://feeds.bbci.co.uk/news/rss.xml"},
    {"nombre":"The Guardian", "url":"https://www.theguardian.com/uk/rss"},
    {"nombre":"Reuters UK",   "url":"https://feeds.reuters.com/reuters/UKTopNews"},
  ],
  "nacional_pt": [
    {"nombre":"Público",        "url":"https://feeds.feedburner.com/PublicoRSS"},
    {"nombre":"J. de Notícias", "url":"https://www.jn.pt/rss/"},
    {"nombre":"Observador",     "url":"https://observador.pt/feed/"},
  ],
  "nacional_br": [
    {"nombre":"Folha SP", "url":"https://feeds.folha.uol.com.br/poder/rss091.xml"},
    {"nombre":"G1 Globo", "url":"https://g1.globo.com/rss/g1/"},
  ],
  "nacional_jp": [
    {"nombre":"Japan Times","url":"https://www.japantimes.co.jp/feed/"},
    {"nombre":"NHK World",  "url":"https://www3.nhk.or.jp/nhkworld/upld/feeds/en/news.xml"},
  ],

  # ── INTERNACIONAL por idioma ───────────────────────────────────────────────
  "internacional_es": [
    {"nombre":"El País Global",  "url":"https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/portada"},
    {"nombre":"BBC Mundo",       "url":"https://feeds.bbci.co.uk/mundo/rss.xml"},
    {"nombre":"France 24 ES",    "url":"https://www.france24.com/es/rss"},
    {"nombre":"DW Español",      "url":"https://rss.dw.com/rdf/rss-es-all"},
    {"nombre":"RT en Español",   "url":"https://actualidad.rt.com/rss"},
    {"nombre":"Euronews ES",     "url":"https://es.euronews.com/rss?format=mrss&level=theme&name=news"},
    {"nombre":"Reuters ES",      "url":"https://feeds.reuters.com/reuters/MXTopNews"},
  ],
  "internacional_en": [
    {"nombre":"BBC World",    "url":"http://feeds.bbci.co.uk/news/world/rss.xml"},
    {"nombre":"Reuters",      "url":"https://feeds.reuters.com/reuters/worldNews"},
    {"nombre":"CNN World",    "url":"http://rss.cnn.com/rss/edition_world.rss"},
    {"nombre":"Fox News",     "url":"https://feeds.foxnews.com/foxnews/world"},
    {"nombre":"France 24 EN", "url":"https://www.france24.com/en/rss"},
    {"nombre":"OAN",          "url":"https://www.oann.com/feed/"},
    {"nombre":"AP World",     "url":"https://rsshub.app/apnews/topics/apf-intlnews"},
  ],
  "internacional_fr": [
    {"nombre":"Le Monde Monde","url":"https://www.lemonde.fr/rss/une.xml"},
    {"nombre":"France 24 FR",  "url":"https://www.france24.com/fr/rss"},
    {"nombre":"RFI",           "url":"https://www.rfi.fr/fr/rss"},
    {"nombre":"Euronews FR",   "url":"https://fr.euronews.com/rss?format=mrss&level=theme&name=news"},
  ],
  "internacional_de": [
    {"nombre":"Der Spiegel Int","url":"https://www.spiegel.de/schlagzeilen/index.rss"},
    {"nombre":"DW Deutsch",     "url":"https://rss.dw.com/rdf/rss-de-all"},
    {"nombre":"Euronews DE",    "url":"https://de.euronews.com/rss?format=mrss&level=theme&name=news"},
  ],
  "internacional_it": [
    {"nombre":"RAI News",      "url":"https://www.rainews.it/dl/rainews/media/feed-web.xml"},
    {"nombre":"La Repubblica", "url":"https://www.repubblica.it/rss/homepage/rss2.0.xml"},
    {"nombre":"Euronews IT",   "url":"https://it.euronews.com/rss?format=mrss&level=theme&name=news"},
  ],
  "internacional_pt": [
    {"nombre":"RTP Notícias","url":"https://www.rtp.pt/noticias/rss"},
    {"nombre":"Público",     "url":"https://feeds.feedburner.com/PublicoRSS"},
    {"nombre":"BBC Brasil",  "url":"https://feeds.bbci.co.uk/portuguese/rss.xml"},
  ],

  # ── DEPORTES por idioma ────────────────────────────────────────────────────
  "deportes_es": [
    {"nombre":"Marca",           "url":"https://e00-marca.uecdn.es/rss/portada.xml"},
    {"nombre":"AS",              "url":"https://as.com/rss/tags/ultimas_noticias.xml"},
    {"nombre":"Mundo Deportivo", "url":"https://www.mundodeportivo.com/rss/home.xml"},
    {"nombre":"Sport",           "url":"https://www.sport.es/rss/portada.xml"},
    {"nombre":"Relevo",          "url":"https://www.relevo.com/rss/portada.xml"},
  ],
  "deportes_en": [
    {"nombre":"BBC Sport",    "url":"http://feeds.bbci.co.uk/sport/rss.xml"},
    {"nombre":"Reuters Sport","url":"https://feeds.reuters.com/reuters/sportsNews"},
    {"nombre":"ESPN",         "url":"https://www.espn.com/espn/rss/news"},
    {"nombre":"Sky Sports",   "url":"https://www.skysports.com/rss/12040"},
  ],
  "deportes_fr": [
    {"nombre":"L'Équipe",    "url":"https://www.lequipe.fr/rss/actu_rss.xml"},
    {"nombre":"France 24 Sport","url":"https://www.france24.com/fr/sports/rss"},
  ],
  "deportes_de": [
    {"nombre":"Kicker",      "url":"https://www.kicker.de/news/fussball/bundesliga/rss.xml"},
    {"nombre":"DW Sport",    "url":"https://rss.dw.com/rdf/rss-de-sport"},
  ],
  "deportes_it": [
    {"nombre":"Gazzetta",    "url":"https://www.gazzetta.it/rss/home.xml"},
    {"nombre":"Corriere Sport","url":"https://xml2.corrieredellasera.it/rss/sport.xml"},
  ],
  "deportes_pt": [
    {"nombre":"A Bola",      "url":"https://www.abola.pt/rss/"},
    {"nombre":"Record PT",   "url":"https://www.record.pt/rss/"},
  ],

  # ── CIENCIA / TECNOLOGÍA / SALUD por idioma ────────────────────────────────
  "ciencia_es": [
    {"nombre":"Muy Interesante", "url":"https://www.muyinteresante.es/rss"},
    {"nombre":"National Geo ES", "url":"https://www.nationalgeographic.com.es/rss/ciencia"},
    {"nombre":"Tendencias21",    "url":"https://www.tendencias21.net/rss"},
    {"nombre":"El País Ciencia", "url":"https://feeds.elpais.com/mrss-s/pages/ep/site/elpais.com/section/ciencia/portada"},
    {"nombre":"BBC Ciencia ES",  "url":"https://feeds.bbci.co.uk/mundo/ciencia_y_tecnologia/rss.xml"},
    {"nombre":"ABC Ciencia",     "url":"https://www.abc.es/rss/feeds/abc_Ciencia.xml"},
  ],
  "ciencia_en": [
    {"nombre":"Science Daily",   "url":"https://www.sciencedaily.com/rss/all.xml"},
    {"nombre":"NASA",            "url":"https://www.nasa.gov/news-release/feed/"},
    {"nombre":"MIT Tech Review", "url":"https://www.technologyreview.com/stories.rss"},
    {"nombre":"BBC Science",     "url":"http://feeds.bbci.co.uk/news/science_and_environment/rss.xml"},
    {"nombre":"Reuters Tech",    "url":"https://feeds.reuters.com/reuters/technologyNews"},
    {"nombre":"New Scientist",   "url":"https://www.newscientist.com/feed/home/"},
    {"nombre":"Nat. Geographic", "url":"https://www.nationalgeographic.com/latest-stories/rss"},
  ],
  "ciencia_fr": [
    {"nombre":"Sciences et Avenir","url":"https://www.sciencesetavenir.fr/rss.xml"},
    {"nombre":"France 24 Sci",    "url":"https://www.france24.com/fr/sciences/rss"},
  ],
  "ciencia_de": [
    {"nombre":"Spektrum",  "url":"https://www.spektrum.de/rss/news"},
    {"nombre":"DW Wissen", "url":"https://rss.dw.com/rdf/rss-de-wissenschaft"},
  ],
  "ciencia_it": [
    {"nombre":"Focus It",    "url":"https://www.focus.it/rss.xml"},
    {"nombre":"Le Scienze",  "url":"https://www.lescienze.it/rss/"},
  ],
  "ciencia_pt": [
    {"nombre":"Ciência Hoje","url":"https://cienciahoje.pt/rss.xml"},
    {"nombre":"Público Ciência","url":"https://feeds.feedburner.com/PublicoRSS"},
  ],
}

# ═══════════════════════════════════════════════════════════════════════════════
# PROCESADO
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
            try: return parsedate_to_datetime(val).isoformat()
            except: pass
    return datetime.now(timezone.utc).isoformat()

def fetch_feed(fuente):
    try:
        resp = requests.get(fuente["url"], headers=HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        feed = feedparser.parse(resp.content)
        noticias = []
        for entry in feed.entries[:3]:
            titulo = limpiar(entry.get('title',''))
            if not titulo or len(titulo) < 5: continue
            desc = limpiar(entry.get('summary','') or entry.get('description',''))
            noticias.append({
                "titulo": titulo,
                "enlace": entry.get('link','#'),
                "desc":   desc[:180]+'…' if len(desc)>180 else desc,
                "fecha":  fecha_iso(entry),
                "fuente": fuente["nombre"]
            })
        print(f"  ✓ {fuente['nombre']}: {len(noticias)}")
        return noticias
    except Exception as e:
        print(f"  ✗ {fuente['nombre']}: {e}")
        return []

def procesar(fuentes, max_items=10):
    todas = []
    for f in fuentes: todas.extend(fetch_feed(f))
    listas = {}
    for n in todas: listas.setdefault(n['fuente'],[]).append(n)
    resultado, i = [], 0
    claves = list(listas.keys())
    while len(resultado) < max_items:
        avance = False
        for k in claves:
            if i < len(listas[k]):
                resultado.append(listas[k][i]); avance = True
            if len(resultado) >= max_items: break
        if not avance: break
        i += 1
    return resultado[:max_items]

def main():
    print("=== Generando noticias.json ===")
    resultado = {"actualizado": datetime.now(timezone.utc).isoformat(), "secciones": {}}

    for clave, fuentes in FUENTES.items():
        print(f"\n[{clave}]")
        resultado["secciones"][clave] = procesar(fuentes)

    ruta = "NOTICIAS/noticias.json"
    with open(ruta,"w",encoding="utf-8") as f:
        json.dump(resultado, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in resultado["secciones"].values())
    print(f"\n✅ {ruta} — {total} noticias totales")

if __name__ == "__main__":
    main()
