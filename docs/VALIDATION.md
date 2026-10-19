# Validación ejecutada — 16 de octubre de 2026

**Entorno de construcción:** Linux, Python 3.13.5. Se ejecutó la instalación editable sin descargar dependencias, el ejecutable `contamate`, pruebas pytest y demo offline.

```text
pytest -q
22 passed
```

```text
python scripts/demo.py
DEMO OFFLINE OK: 2 hallazgos A, 1 hallazgo B
```

**Escenarios cubiertos:** conciliación con evidencia por fila, separación entre dos empresas, RUC incorrecto, DTD XML bloqueada, reinicio sin duplicar, modificaciones y eliminaciones de documentos, recuperación de duplicado, importes CSV ambiguos, PDF solo indexado, XLSX, expansión excesiva, tarea ligada al RUC, selección simulada del modelo y protocolo Ollama localhost, fuentes normativas con vigencia declarada y briefing sin modelo.

**No se probó:** equipo Windows real, ejecución de modelo Ollama real, GPU, whisper.cpp, Piper, SUNAT/SIRE en vivo, OCR, contadores reales, corpus oficial actualizado, conectores de terceros y carga industrial. Por ello, no se declara un MVP listo para clientes.

**Seguridad:** no se usaron datos de clientes. Las muestras RUC y comprobantes son ficticios, diseñados para demostrar discrepancias.
