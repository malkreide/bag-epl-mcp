#!/usr/bin/env bash
#
# SessionStart-Hook: meldet, wie viele Commits der ausgecheckte Stand hinter
# origin/<Default-Branch> liegt. Bei 0 schweigt er.
#
# WARUM (siehe auch .claude/hooks/README.md):
# Ein veralteter Klon hat am 3.8.2026 zweimal eine rote CI erzeugt, deren
# Ursache nicht im Diff stand — die fehlenden Commits waren jeweils genau die,
# die das Gate einfuehrten, an dem der Branch scheiterte. Die Pruefung kostet
# eine Sekunde und ersetzt eine Fehlersuche in den falschen Dateien.
#
# OBERSTE REGEL: Dieser Hook blockiert die Session NIEMALS.
# Kein Netz, kein Remote, detached HEAD, flatterndes DNS, Credential-Prompt,
# fehlendes `timeout`, gesperrtes .git — jeder dieser Faelle geht still durch
# und endet mit Exit-Code 0. Ein Hook, der bei Netzproblemen die Arbeit anhaelt,
# wird nach dem zweiten Mal abgeschaltet und schuetzt danach gar nichts.
#
# Deshalb bewusst KEIN `set -e` / `set -o pipefail`: ein fehlschlagender Befehl
# darf hier nicht zum Abbruch mit Fehlerstatus fuehren. Jeder Pfad endet in
# `exit 0`.

# Sekunden, die Netzoperationen (fetch, ls-remote) hoechstens dauern duerfen.
FETCH_TIMEOUT="${CLAUDE_STALENESS_TIMEOUT:-5}"

# Git darf unter keinen Umstaenden interaktiv nachfragen — ein Credential- oder
# Host-Key-Prompt haengt sonst am Sessionstart, bis das Timeout greift.
export GIT_TERMINAL_PROMPT=0
export GIT_ASKPASS=true
export SSH_ASKPASS=true
export SSH_ASKPASS_REQUIRE=never
export GIT_SSH_COMMAND="${GIT_SSH_COMMAND:-ssh -o BatchMode=yes -o ConnectTimeout=5}"

# Fuehrt einen Befehl mit harter Zeitschranke aus. Faellt auf eine eigene
# Watchdog-Schleife zurueck, wenn coreutils' `timeout` fehlt.
run_limited() {
  if command -v timeout >/dev/null 2>&1; then
    timeout -k 1 "$FETCH_TIMEOUT" "$@"
    return $?
  fi
  "$@" &
  watched=$!
  waited=0
  while kill -0 "$watched" 2>/dev/null && [ "$waited" -lt "$FETCH_TIMEOUT" ]; do
    sleep 1
    waited=$((waited + 1))
  done
  if kill -0 "$watched" 2>/dev/null; then
    kill -9 "$watched" 2>/dev/null
    wait "$watched" 2>/dev/null
    return 124
  fi
  wait "$watched"
}

cd "${CLAUDE_PROJECT_DIR:-$PWD}" 2>/dev/null || exit 0

# Kein Repo, kein Remote, leeres Repo (unborn HEAD) -> nichts zu vergleichen.
git rev-parse --git-dir >/dev/null 2>&1 || exit 0
git remote get-url origin >/dev/null 2>&1 || exit 0
git rev-parse --verify --quiet HEAD >/dev/null 2>&1 || exit 0

# Default-Branch ERMITTELN, nicht "main" annehmen: mindestens ein Repo im
# Portfolio nutzt "master", und genau diese Annahme hat schon einmal einen
# Branch 15 Commits alt werden lassen.
# Zuerst lokal (kostenlos), dann als Rueckfall ueber das Netz.
default_branch=""
head_ref="$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null)"
[ -n "$head_ref" ] && default_branch="${head_ref#origin/}"

if [ -z "$default_branch" ]; then
  ls_remote="$(run_limited git ls-remote --symref origin HEAD 2>/dev/null)"
  default_branch="$(printf '%s\n' "$ls_remote" |
    sed -n 's|^ref: refs/heads/\([^[:space:]]*\).*|\1|p' | head -n 1)"
fi

# Nicht ermittelbar (offline und kein origin/HEAD lokal) -> stillschweigend raus.
# Hier auf "main" zu raten waere genau der Fehler, den dieser Hook verhindert.
[ -n "$default_branch" ] || exit 0

run_limited git fetch --quiet --no-tags origin "$default_branch" >/dev/null 2>&1 || exit 0

behind="$(git rev-list --count HEAD..FETCH_HEAD 2>/dev/null)"
case "$behind" in
  '' | *[!0-9]*) exit 0 ;;
esac
[ "$behind" -gt 0 ] || exit 0   # aktuell -> schweigen

if current="$(git symbolic-ref --quiet --short HEAD 2>/dev/null)"; then
  position="Branch '${current}'"
else
  position="detached HEAD $(git rev-parse --short HEAD 2>/dev/null)"
fi

plural="Commits"
[ "$behind" -eq 1 ] && plural="Commit"

cat <<MSG
[Klon-Aktualitaet] ${position} liegt ${behind} ${plural} hinter origin/${default_branch}.
  Auffrischen:  git fetch origin ${default_branch} && git merge FETCH_HEAD
  Warum das zaehlt: ein veralteter Klon erzeugt eine rote CI, deren Ursache
  nicht im Diff steht — es fehlen die Commits, die das Gate einfuehrten.
MSG

exit 0
