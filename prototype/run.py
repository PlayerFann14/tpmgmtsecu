"""Point d'entrée du prototype.

Usage :
    python run.py --case cases/casB_mediconsult.md            # dry-run (sans clé)
    python run.py --case cases/casB_mediconsult.md --provider openai
    python run.py test-injection --case cases/casB_injecte.md
"""

from __future__ import annotations

import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent
sys.path.insert(0, str(RACINE))

from src.cli.main import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())