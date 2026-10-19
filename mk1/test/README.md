# Test · Evidencia y límites

**Ejecución local verificada el 2026-10-19:** `PYTHONPATH=src python -m pytest -q` → **29 passed**. También pasaron `compileall` y sintaxis JavaScript. Estas pruebas utilizan fixtures inventados y no prueban un entorno Docker real.

| Escenario | Resultado |
| --- | --- |
| Ingesta y conciliación básica | PASS (fixtures) |
| Separación multiempresa y rutas | PASS (tests) |
| API con token y endpoints | PASS (tests) |
| Docker `build/up` | BLOCKED: no hay Docker en el entorno de verificación |
| Ollama Qwen real | NOT RUN |
| Voz STT/TTS real | NOT RUN |
| Windows WSL2 y GPU | NOT RUN |
| Normativa/SUNAT real | OUT OF SCOPE / NOT RUN |

Para instrucciones de pruebas leer [`docs/MVP001_ACCEPTANCE.md`](../../docs/MVP001_ACCEPTANCE.md). No convertir los tests `PASS` en reclamaciones de confiabilidad comercial.
