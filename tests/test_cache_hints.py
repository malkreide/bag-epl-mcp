"""SEP-2549: die auflistenden Methoden muessen einen Frischehinweis tragen.

Spec `2026-07-28` gibt jedem cachebaren Resultat `ttlMs` und `cacheScope`. Das
SDK fuellt keines von beiden — `CacheHint()` defaultet auf `ttl_ms=0`,
`scope="private"`, die Drahtform von «schon veraltet, nie teilen». Ein Server
ohne `cache_hints` verhaelt sich also nicht neutral: er laesst jeden Client bei
jeder Verbindung neu auflisten, fuer Verzeichnisse, die beim Import feststehen.

Geprueft ueber eine echte `ClientSession` statt durch Ruecklesen von
`CACHE_HINTS`: `MCPServer` fuellt den Hinweis feldweise und nur, wo der Handler
nichts gesetzt hat — ein Blick ins Dict waere auch dann gruen, wenn das Argument
am Konstruktor verlorenginge.
"""

from __future__ import annotations

from mcp import Client
from mcp.server.caching import CACHEABLE_METHODS
from mcp.server.mcpserver import MCPServer

from bag_epl_mcp.server import CACHE_HINTS, LIST_CACHE_TTL_MS, mcp


async def test_die_werkzeugliste_traegt_die_ttl() -> None:
    async with Client(mcp) as client:
        result = await client.list_tools()

    assert result.ttl_ms == LIST_CACHE_TTL_MS, (
        f"tools/list antwortete mit ttlMs={result.ttl_ms}; bei 0 listet jeder Client "
        "bei jeder Verbindung neu auf"
    )
    assert result.cache_scope == "public"


async def test_die_ressourcen_und_promptlisten_tragen_die_ttl() -> None:
    """Beide werden per Dekorator beim Import registriert und haengen so wenig
    vom Aufrufer ab wie die Werkzeugliste."""
    async with Client(mcp) as client:
        resources = await client.list_resources()
        prompts = await client.list_prompts()

    assert resources.ttl_ms == LIST_CACHE_TTL_MS
    assert prompts.ttl_ms == LIST_CACHE_TTL_MS


async def test_der_inhalt_einer_ressource_traegt_keinen_frischehinweis() -> None:
    """Die einzige negative Zusicherung hier, und die wichtigste.

    Ein Hinweis auf `resources/read` waere eine Aussage ueber den INHALT. Dass
    die beiden Ressourcen heute Literale liefern, ist kein Grund dafuer — die
    naechste kann eine Abfrage sein, und der Hinweis waere dann stillschweigend
    falsch. Faellt dieser Test, hat jemand die Methode aufgenommen.
    """
    async with Client(mcp) as client:
        result = await client.read_resource("epl://uebersicht")

    assert result.ttl_ms == 0
    assert result.cache_scope == "private"


async def test_ein_server_ohne_hinweise_sagt_nichts() -> None:
    """Negativkontrolle: gleiches SDK, gleicher Client, kein `cache_hints`.
    Faengt den Tag ab, an dem das SDK selbst einen Default bekommt."""
    async with Client(MCPServer("kontrolle")) as client:
        result = await client.list_tools()

    assert result.ttl_ms == 0
    assert result.cache_scope == "private"


def test_jede_gehinweiste_methode_ist_nach_spec_cachebar() -> None:
    """`MCPServer` lehnt einen unbekannten Schluessel schon im Konstruktor ab;
    ein Tippfehler taeuchte sonst als Collection-Error an anderer Stelle auf."""
    unknown = sorted(set(CACHE_HINTS) - set(CACHEABLE_METHODS))
    assert not unknown, f"nach Spec 2026-07-28 nicht cachebar: {unknown}"


def test_kein_hinweis_auf_einer_inhalts_methode() -> None:
    """Dieselbe Absicht wie oben, an der Konfiguration statt an der Antwort —
    damit sie sichtbar bleibt, wenn die Ressource `epl://uebersicht` einmal
    verschwindet."""
    assert "resources/read" not in CACHE_HINTS
    assert "prompts/get" not in CACHE_HINTS
