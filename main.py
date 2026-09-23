"""Punto de entrada: ejecutar este archivo desde PyCharm o la terminal."""
from app.application import App
import sys


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == '--self-test':
        from app.self_test import run
        raise SystemExit(run(sys.argv[2]))
    App().mainloop()
