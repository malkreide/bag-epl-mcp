# SessionStart-Hook: Klon-Aktualitätsprüfung

`session-start.sh` meldet beim Sessionstart, wie viele Commits der
ausgecheckte Stand hinter `origin/<Default-Branch>` liegt. Liegt er nicht
zurück, sagt er nichts.

## Warum

Ein veralteter Klon hat am 3.8.2026 zweimal eine rote CI erzeugt, deren
Ursache **nicht im Diff stand** — die fehlenden Commits waren jeweils genau
die, die das Gate einführten, an dem der Branch scheiterte. Wer den Diff
liest, sucht in den falschen Dateien. Die Prüfung kostet eine Sekunde und
ersetzt diese Fehlersuche.

Dieselbe Prüfung steht als Handgriff in `CLAUDE.md` («Vor der Arbeit»). Ein
Handgriff, an den man denken muss, wird vergessen; der Hook denkt daran.

## Die Regel, die über allen anderen steht

**Der Hook blockiert die Session niemals.** Kein Netz, kein Remote, detached
HEAD, flatterndes DNS, ein Credential-Prompt, ein fehlendes `timeout`, ein
gesperrtes `.git` — jeder dieser Fälle geht still durch und endet mit
Exit-Code 0.

Der Grund ist nicht Eleganz, sondern Überleben: Ein Hook, der bei
Netzproblemen die Arbeit anhält, wird nach dem zweiten Mal abgeschaltet und
schützt danach gar nichts. Ein Hook, der im Zweifel schweigt, bleibt an.

Deshalb enthält das Skript bewusst **kein** `set -e` / `set -o pipefail`:
ein fehlschlagender Befehl darf hier nicht zum Abbruch mit Fehlerstatus
führen. Jeder Pfad endet in `exit 0`.

## Wie er arbeitet

1. Abbruch, wenn kein Git-Repo, kein `origin` oder ein leeres Repo
   (unborn HEAD) vorliegt.
2. **Default-Branch ermitteln, nicht raten.** Zuerst lokal über
   `refs/remotes/origin/HEAD` (kostet kein Netz), als Rückfall über
   `git ls-remote --symref origin HEAD`. Ist er nicht ermittelbar, schweigt
   der Hook — auf `main` zu raten wäre genau der Fehler, den er verhindern
   soll. Drei Server im Portfolio (`openlex-mcp`, `swiss-courts-mcp`,
   `swisstopo-mcp`) nennen ihren Default-Branch `master`; diese Annahme hat
   schon einmal einen Branch 15 Commits alt werden lassen.
3. `git fetch --no-tags origin <default-branch>` mit harter Zeitschranke.
4. `git rev-list --count HEAD..FETCH_HEAD`. Bei `0` → keine Ausgabe.

## Zeitschranken

| Schranke | Wert | Wo |
|---|---|---|
| Netzoperationen (`fetch`, `ls-remote`) | 5 s | `FETCH_TIMEOUT` im Skript, überschreibbar per `CLAUDE_STALENESS_TIMEOUT` |
| Gesamter Hook | 15 s | `timeout` in `.claude/settings.json` |

Fehlt coreutils' `timeout`, greift eine eigene Watchdog-Schleife mit
derselben Schranke. Interaktive Git-Prompts sind über `GIT_TERMINAL_PROMPT=0`,
`GIT_ASKPASS` und `ssh -o BatchMode=yes` abgeschaltet — ein Passwort-Prompt
wäre sonst genau der Fall, der den Sessionstart hängen lässt.

## Selbst prüfen

```bash
# Aktueller Klon: keine Ausgabe erwartet
.claude/hooks/session-start.sh

# Künstlich veralteter Stand: Meldung erwartet
git checkout --detach HEAD~3 && .claude/hooks/session-start.sh; git checkout -

# Ohne Netz: keine Ausgabe, Exit 0, kein Hängen
GIT_CONFIG_GLOBAL=/dev/null timeout 20 env -u https_proxy -u HTTPS_PROXY \
  .claude/hooks/session-start.sh; echo "exit=$?"
```

Der Hook läuft auch lokal, nicht nur in Claude Code on the web: in der
Web-Session ist der Klon beim Containerstart frisch, veralten kann er vor
allem auf dem Arbeitsrechner — dort also ist die Prüfung überhaupt erst
etwas wert.
