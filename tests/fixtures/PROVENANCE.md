# Herkunft der Fixtures

**Erzeugt von `scripts/record_fixtures.py`. Nicht von Hand pflegen.**

Aufgezeichnet am **2026-08-08**.

Ohne Datum ist «gemessen» nach zwei Jahren von «angenommen» nicht mehr
zu unterscheiden — die Datei sieht gleich aus.

## Was hier aufgezeichnet ist, ist nicht eine Antwort

Dieser Server hat keine API, aus der sich eine Fixture ziehen liesse.
Im ganzen Modul steht **ein** ausgehender HTTP-Aufruf, und der trifft
eine Single-Page-App. Aufgezeichnet ist deshalb der Gegenstand, an dem
seine Aussagen haengen: ob die Adressen, die er als «offizielle
Quelle» weitergibt, etwas liefern — und ob die Rechtsverweise stimmen.

## Ohne die Kontrollen belegt nichts davon etwas

Zu jeder Messung gehoert ein frei erfundenes Gegenstueck:

| Kontrolle | Antwort | Was sie traegt |
|---|---|---|
| erfundener Pfad unter `sl.bag.admin.ch/api/` | 200 + `text/html` | dort liegt keine API, sondern die App |
| erfundener Pfad unter `www.bag.admin.ch/bag/de/` | 404 | die 404 der drei Seiten sind echt |
| erfundene ELI bei der Fedlex | 200 | ein 200 dort ist wertlos |
| erfundene SR-Nummer im SPARQL-Endpunkt | kein Treffer | die Abfrage unterscheidet |

Ohne sie belegte jede Messung nur, was **ich** bekommen habe — nicht,
was die Quelle fuehrt. Dieses Portfolio hat den Unterschied bereits
dreimal verwechselt.

Das Aufzeichnungsskript bricht ab, wenn eine Kontrolle nicht mehr
traegt, wenn ein Einstiegspunkt stirbt, wenn eine der toten Seiten
zurueckkehrt oder wenn ein Rechtsverweis vom Register abweicht. Ein
Befund, der still veraltet, ist schlimmer als keiner.

## `quellen_adressen.json`

- **Quelle:** `www.bag.admin.ch, sl.bag.admin.ch`
- **Aufgezeichnet:** 2026-08-08
- **Auswahl:** Statuscode, Content-Type und Groesse je Adresse, die dieser Server als Quelle weitergibt — samt zweier Kontrollen mit erfundenen Pfaden. Erst die Kontrollen machen aus «ich bekomme 404» die Aussage «diese Seite gibt es nicht», und aus «ich bekomme 200» die Aussage «hier liegt die App-Huelle, keine API»
- **Groesse:** 2415 B
- **SHA-256:** `def883c0b9c359afb8416b0af2f3e1a537613c304e34d6ee2dec4d2bfe8f6b86`

## `fedlex_register.json`

- **Quelle:** `https://fedlex.data.admin.ch/sparqlendpoint (jolux:historicalLegalId)`
- **Aufgezeichnet:** 2026-08-08
- **Auswahl:** die Zuordnung SR-Nummer -> ELI aus dem Register der Fedlex, fuer jedes Gesetz, das `epl_rechtskontext` ausgibt. Der Weg ueber die Weboberflaeche traegt hier nicht: Sie antwortet fuer JEDE ELI mit 200 und derselben Byte-Zahl, auch fuer eine frei erfundene. Genau so blieb ein falscher GgV-Verweis unbemerkt
- **Groesse:** 1404 B
- **SHA-256:** `54816d1268dde99b1cc7df7959326b38e471760ebe22e0de81d399073a3ef3d3`

## `fedlex_eli_ununterscheidbar.json`

- **Quelle:** `https://www.fedlex.admin.ch/eli/cc/…`
- **Aufgezeichnet:** 2026-08-08
- **Auswahl:** zwei ELI-Abrufe ueber die Weboberflaeche: der frueher verlinkte und der richtige. Beide HTTP 200. DAS ist der Befund — ein Statuscode konnte den falschen Rechtsverweis nicht zeigen, und ohne dieses Paar liesse sich das nicht mehr nachvollziehen
- **Groesse:** 192 B
- **SHA-256:** `a1829e33a556ed7f2fcefe299c5b511fb65361214af8acb09d648718365df165`
