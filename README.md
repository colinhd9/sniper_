# Sniper Range

3D-Ego-Sandbox: frei bewegen, Ziele suchen, Entfernung messen, Kugelfall und Wind ausgleichen.

Maßstab: 1 Einheit = 1 Meter. Die Kugel ist kein Hitscan — Gravitation und Wind wirken über die Flugzeit.

## Umgebung

Miniconda liegt in `~/miniconda3` — der iCloud-Projektpfad enthält Leerzeichen, die der Installer nicht akzeptiert. Env-Name: `sniper_range`.

```bash
source ~/miniconda3/etc/profile.d/conda.sh
conda activate sniper_range
python main.py
```

Ballistik-Tests ohne Engine:

```bash
conda activate sniper_range
pytest
```

## Steuerung

- **WASD** bewegen
- **Maus** umsehen
- **Shift** sprinten
- **C** ducken (Umschalter)
- **RMB** Visier
- **Mausrad** Zoomstufen im Visier, sonst Waffe wechseln
- **1 / 2** Waffe wählen
- **LMB** schießen
- **R** Entfernungsmesser
- **Esc** Pause / Maus freigeben
- **Tab** Editor-Kamera (Map prüfen)

## Waffen

- **SR-500** (Taste 1): Repetierer, 500 m/s. Im Visier schaltet das Mausrad 5x / 10x / 20x.
- **AK-47** (Taste 2): Vollautomat, 715 m/s, 600 Schuss/min. Kimme und Korn (~1.8x), mehr Streuung und Rückstoß. Der schnellere Flug verkürzt die Vorhaltezeit gegenüber dem SR-500 deutlich.

## Dorf und laufende Ziele

Drei kleine Adobe-Cluster stehen seitlich der Stahlplatten: ein Nahdorf bei ~130 m, ein Hof bei ~340 m und ein Fernposten mit Turm bei ~545 m. Dazwischen laufen orangefarbene Trainingspuppen auf festen Routen — eine davon quert die Bahn bei ~400 m, damit Vorhalten geübt werden kann.

- Kopf- und Körpertreffer werden getrennt angezeigt; nach einem Treffer steht die Puppe nach zehn Sekunden am Startwegpunkt wieder auf.
- Ein Einschlag in 25 m Nähe schickt sie im Sprint hinter die nächste Tür oder Mauer. Nach sechs Sekunden in Deckung patrouillieren sie weiter.

## Ballistik

- Mündungsgeschwindigkeit: 500 m/s
- Fall: 9.81 m/s² nach unten
- Wind: konstante Horizontalbeschleunigung, pro Sitzung neu

## Web

Die Seite unter Vercel ist der **atColin-Hub**, nicht das Spiel. Ursina/Panda3D läuft nur lokal (`python main.py`).

- Hub: [sniper-jade.vercel.app](https://sniper-jade.vercel.app/)
- Sniper Range: [sniper-jade.vercel.app/sniper](https://sniper-jade.vercel.app/sniper/)
- Landing: Ordner [`web/`](web/) — neue Projekte als Icon in `web/index.html` plus Seite unter `web/<name>/`
- Vercel: Framework **Other**, Root Directory **`web`**
- Repo: [github.com/colinhd9/sniper_](https://github.com/colinhd9/sniper_)
