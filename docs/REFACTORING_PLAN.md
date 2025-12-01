# 🛠️ EvoName Refactoring Plan

Dieses Dokument skizziert die Schritte, um die Codebasis von `EvoName` robuster, wartbarer und erweiterbarer zu machen. Basierend auf den jüngsten Erfahrungen (insbesondere dem Typ-Mismatch-Bug) liegt der Fokus auf **Type Safety** und **Modularisierung**.

## 🧹 Priorität 0: Ordnerstruktur & Hygiene (Quick Wins)

Bevor wir den Code anfassen, sollten wir aufräumen. Das schafft Übersicht und verhindert, dass wir uns in Dateien verlieren.

### 1. Ordnerstruktur bereinigen
**Problem:** Das Root-Verzeichnis ist überfüllt mit Skripten, Dokumentation und Debug-Tools.
**Lösung:**
- `docs/`: Alle `.md` Dateien (außer `README.md`, `task.md`).
- `scripts/` (oder `tools/`): Alle Helfer-Skripte (`debug_*.py`, `analyze_champion.py`, `dashboard.py`).
- `src/` (Optional, später): Der eigentliche Quellcode (`trainer.py`, `primitive_set.py`).
- `tests/`: Unit Tests.
- `data/`: Trainingsdaten (bereits vorhanden, aber sicherstellen, dass alles dort landet).

---

## 🚨 Priorität 1: Kritische Verbesserungen (Must-Have)

Diese Punkte adressieren direkte Schmerzpunkte und Fehlerquellen.

### 1. Single Source of Truth für Primitives (`pset`)
**Problem:** Die Definition der Primitives (`primitive_set.py`) und ihre Registrierung (`trainer.py`) waren entkoppelt, was zu dem kritischen Typ-Fehler führte.
**Lösung:**
- Das `gp.PrimitiveSetTyped` sollte **direkt in `primitive_set.py`** (oder einer neuen `gp_config.py`) erstellt und konfiguriert werden.
- `trainer.py` importiert nur noch das fertige `pset`.
- **Vorteil:** Wenn man eine Funktion ändert, ändert man auch direkt ihre Registrierung an der gleichen Stelle.

### 2. Modularisierung von `trainer.py`
**Problem:** `trainer.py` ist ein "Gott-Skript" (>1000 Zeilen), das alles macht: Argument Parsing, GP-Setup, Training Loop, UI, Logging, Evaluation.
**Lösung:** Aufsplitten in spezialisierte Module:
- `config.py`: Alle Hyperparameter, Gewichte, Gates.
- `evolution.py`: Die eigentliche Trainings-Schleife (die Logik für Migration, Cataclysm, etc.).
- `evaluator.py`: Die `evaluate_individual` Logik (ausgelagert, um sie testbar zu machen).
- `ui.py`: Alles was mit `rich`, Progress Bars und Output zu tun hat.
- `main.py`: Nur noch der Einstiegspunkt (CLI Parsing und Aufruf der Komponenten).

### 3. Unit Tests für Primitives & Evaluation
**Problem:** Fehler in Primitives (z.B. Abstürze bei leeren Listen) fallen erst zur Laufzeit auf oder führen zu stiller Fitness=0.0.
**Lösung:**
- `tests/test_primitives.py`: Testet jede Primitive-Funktion auf Edge Cases (leere Inputs, None, falsche Typen).
- `tests/test_evaluation.py`: Testet die Fitness-Funktion mit bekannten Mock-Objekten, um sicherzustellen, dass die Berechnung stimmt.

---

## ⚠️ Priorität 2: Stabilität & Konfiguration

### 4. Konfiguration via YAML/JSON statt Hardcoding
**Problem:** Gewichte, Gates und Swap-Raten sind im Code vergraben. Experimente erfordern Code-Änderungen.
**Lösung:**
- Eine `config.yaml` Datei einführen.
- Laden der Konfiguration beim Start.
- Ermöglicht einfaches Versionieren von Experimenten ("Run A mit config_strict.yaml", "Run B mit config_loose.yaml").

### 5. Robustes Error Handling in der Evaluation
**Problem:** Ein `try...except` Block fängt *alles* ab und gibt 0.0 zurück. Das verschleiert Bugs (wie wir gesehen haben).
**Lösung:**
- Spezifischere Exceptions fangen.
- Bei "System-Fehlern" (z.B. `AttributeError` im Code selbst) sollte das Training **abbrechen** oder zumindest einen lauten Error loggen, statt einfach 0.0 zu geben.
- "Bad Individual" Fehler (z.B. Division durch Null im GP-Baum) können weiterhin bestraft werden.

---

## ✨ Priorität 3: Nice-to-Have (Komfort & Features)

### 6. Integration mit Dashboard
**Idee:** Der `trainer.py` könnte Live-Statistiken (Fitness, Best Individual, Hall of Shame) direkt an das laufende `dashboard.py` (oder eine Datenbank) senden.
- Echtzeit-Graphen im Browser statt nur Terminal-Output.

### 7. Type Hinting & MyPy
**Idee:** Strikte Typ-Prüfung für das gesamte Projekt einführen.
- Verhindert, dass man `StringList` mit `str` verwechselt, bevor der Code überhaupt läuft.

### 8. Checkpointing Verbesserungen
**Idee:** Statt nur `pickle` (was oft Probleme bei Code-Änderungen macht), die besten Individuen auch als **lesbaren Code** oder JSON-Struktur exportieren.
- Ermöglicht das "Retten" von Logik, auch wenn sich Klassen-Definitionen ändern.

### 9. Parallelisierung (Multiprocessing)
**Idee:** Evaluation ist der Flaschenhals. Wir können die Berechnung auf alle CPU-Kerne verteilen.
- **Level 1 (Evaluation):** Innerhalb einer Insel werden die 300 Individuen parallel bewertet (sehr einfach mit `multiprocessing.Pool`).
- **Level 2 (Inseln):** Die 3 Inseln laufen wirklich **gleichzeitig** in eigenen Prozessen.
    - *Vorteil:* Echte Parallelität.
    - *Herausforderung:* Synchronisation für Migration (Austausch von Individuen alle N Generationen).
- **Windows-Besonderheit:** Erfordert sauberes `if __name__ == "__main__":` und pickelbare Objekte (was wir durch Schritt 1 & 2 erreichen).

### 10. Background Execution & Workflow
**Idee:** Training soll "headless" laufen, ohne das Terminal zu blockieren.
- **Detached Process:** Starten via `Start-Process python ... -WindowStyle Hidden` oder als Hintergrund-Job in PowerShell.
- **Logging:** Output muss in Dateien (`logs/training.log`) umgeleitet werden, da kein Terminal mehr da ist.
- **Monitoring:** Das Dashboard (`dashboard.py`) wird dann zur einzigen Überwachungsstelle.

---

## 📅 Empfohlener Ablauf

1.  **Refactor `pset`**: Verschiebe die `pset` Erstellung nach `primitive_set.py`. (**Sofort**)
2.  **Tests schreiben**: Erstelle `tests/` und schreibe Tests für die kritischen Primitives. (**Sofort**)
3.  **Split `trainer.py`**: Extrahiere `evaluate_individual` in `evaluator.py`. (**Bald**)
4.  **Parallelisierung**: Sobald `trainer.py` sauber ist, `multiprocessing` aktivieren.
5.  **Config**: Führe `config.yaml` ein.
