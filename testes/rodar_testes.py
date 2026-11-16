# -*- coding: utf-8 -*-
"""
Roda todos os testes automáticos do VL Flooring.

    venv\Scripts\python.exe testes\rodar_testes.py

Os testes que gravam dados usam uma CÓPIA temporária do banco
(vl_jobs_test_tmp), apagada no final — o banco real não é alterado.
Os outros só leem do banco real. Rode no notebook (servidor MySQL),
com o app fechado de preferência.
"""
import glob
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
results = []
for path in sorted(glob.glob(os.path.join(HERE, "teste_*.py"))):
    name = os.path.basename(path)
    print(f"\n=== {name}", flush=True)
    t = time.perf_counter()
    proc = subprocess.run([sys.executable, path], env=env, capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=900)
    lines = [l for l in proc.stdout.splitlines() + proc.stderr.splitlines()
             if l.startswith(("PASS", "FAIL", "[", "RESULT", "Traceback", "  File", "    ")) or "Error" in l]
    print("\n".join(lines[-40:]))
    ok = proc.returncode == 0 and "RESULT: ALL OK" in proc.stdout
    results.append((name, ok, time.perf_counter() - t))

print("\n=== resumo")
for name, ok, secs in results:
    print(f"  {'OK   ' if ok else 'FALHOU'}  {name}  ({secs:.0f}s)")
sys.exit(0 if all(ok for _, ok, _ in results) else 1)
