# ContaMate Local · MVP-001 (v0.2.0)

**Copiloto documental local para contadores peruanos.** Revisa facturas UBL contra registros de compras CSV/XLSX, permite investigación con un LLM descargado en Ollama, conserva tareas y evidencias por RUC y proporciona una interfaz web local. Todo se distribuye mediante **Docker Compose**, sin Python instalado en el host. La voz tiene un perfil independiente y opcional.

> **Estado real:** código y API verificados con pruebas locales; archivos Docker/imagen, inferencia Ollama y audio necesitan validación en una máquina con Docker. No hay garantía de precisión normativa, estado SUNAT ni aptitud comercial. No contiene información contable de terceros.

## Inicio rápido (Windows con Docker Desktop + WSL2; Linux con Docker Engine + Compose)

Abre una terminal en la carpeta donde se encuentra `compose.yaml`:

**PowerShell**

```powershell
.\scripts\bootstrap.ps1
docker compose build
docker compose up -d
docker compose exec ollama ollama pull qwen3:1.7b
docker compose exec app python scripts/seed.py
docker compose ps
```

**Linux / Bash**

```bash
./scripts/bootstrap.sh
docker compose build
docker compose up -d
docker compose exec ollama ollama pull qwen3:1.7b
docker compose exec app python scripts/seed.py
docker compose ps
```

Abre **http://localhost:8765**. En el campo "Clave de acceso local" introduce el valor `CONTAMATE_API_TOKEN` que figura en `.env` y pulsa **Conectar**. Elige "Comercial Ejemplo A" y período **2026-09**; pulsa **Revisar**. Aparecerán 2 hallazgos (`AMOUNT_MISMATCH`, `MISSING_XML`). "Servicios Ejemplo B" presenta `MISSING_REGISTER`. Los datos son inventados y ninguna prueba consulta SUNAT.

El primer arranque requiere internet para descargar imágenes Docker y el modelo Ollama. La revisión documental funciona sin conexión posteriormente; la disponibilidad offline de voz depende de tener sus pesos descargados.

## Comandos de operación dockerizados

```bash
# Leer recursos (Ollama interno / RAM vista por app)
docker compose exec app contamate doctor
# Probar algoritmo y separación de RUC sin IA
docker compose exec app python scripts/demo.py --out /data/isolated-demo
# Ejecutar las pruebas en Docker, SIN red y sin tocar las bases persistentes
docker compose --profile test run --rm --build tests
# Benchmark real del modelo (NO benchmark simulado)
docker compose exec app python scripts/benchmark.py --model qwen3:1.7b --trials 3
# Abrir terminal CLI
docker compose exec app contamate company list
# Reiniciar solo el frontend/API sin borrar los volúmenes
docker compose restart app
```

### Usar archivos del contador

1. Copia **documentos de prueba anonimizados** a `imports/mi_empresa/` del host. El volumen se monta como `/imports/mi_empresa` **solo lectura**.
2. En el panel, registra RUC y empresa; autoriza `/imports/mi_empresa` para ese RUC.
3. Escanea, revisa el mes en formato `YYYY-MM`, exporta informe y valida manualmente cada hallazgo.
4. No autorices una carpeta compartida por distintos RUC; el sistema rechaza rutas solapadas para evitar contaminaciones entre expedientes.

**Registros CSV/XLSX esperados:** columnas `ruc_emisor,ruc_receptor,serie_numero,fecha_emision,moneda,total,tipo_comprobante`, importes `1180.00` sin miles, fecha `YYYY-MM-DD`. `ruc_receptor` y `tipo_comprobante` son opcionales. El XML reconoce únicamente facturas UBL Invoice del caso cubierto; PDF digital se indexa como evidencia, no como factura interpretada. No se interpretan automáticamente SIRE oficial, notas de crédito, PDF escaneados o imágenes.

### Uso de Ollama

- Llama al servicio `http://ollama:11434` en Compose, sin publicar el puerto 11434.
- Modelo inicial `qwen3:1.7b` (~1.4 GB de descarga), de lenguaje general; **no entrenado ni certificado para normativa peruana**. No calcula importes ni cambia registros.
- La selección automática existe **si no se define `CONTAMATE_MODEL`** y hay varios modelos descargados; usa tamaño + presupuesto declarado (`CONTAMATE_OLLAMA_BUDGET_GIB`) como heurística. No es calibración de GPU ni garantía de respuesta. Para pasar a otro modelo: `docker compose exec ollama ollama pull qwen3:4b`, cambiar `CONTAMATE_MODEL` en `.env`, y `docker compose up -d --force-recreate app`.
- CPU por defecto. Si dispones de NVIDIA Toolkit con GPU usable por Docker, ejecutar `docker compose -f compose.yaml -f compose.gpu.yaml up -d --build`, tras validar el soporte de la GPU y límites de VRAM. En Windows, Docker Desktop + WSL2 + driver compatible es necesario.
- Configuración inicial: `app` 1 GiB/1.5 CPU, Ollama 4 GiB/4 CPU. Son **límites máximos declarados, no reservas**, ajustables según RAM; 8 GiB de RAM del host no garantizan respuesta rápida. CPU/GPU y latencia deben medirse con `scripts/benchmark.py`.

### Voz en contenedor opcional

```bash
# Inicia servicio voice además de app y ollama
docker compose --profile voice up -d --build
# Visita la web y usa Dictar: el navegador grabará tras un clic.
```

La primera transcripción descargará un modelo STT (default `tiny`) al volumen `voice_models`, lo que requiere conexión a internet. El usuario debe revisar la transcripción antes de pedir análisis al agente. No hay micrófono siempre activo. Para voz sintetizada Piper, incorpora **dos archivos de una voz española legítimamente licenciada** en `voices/es.onnx` y `voices/es.onnx.json`, reinicia `voice`, y usa "Escuchar". No se incluyen pesos/archivos de voz en el paquete. El contenedor Piper depende de GPL-3.0-or-later, revisar implicancias de distribución.

### Volúmenes y copias de seguridad

- `contamate_data` → SQLite, informes y estado.
- `ollama_models` → pesos descargados.
- `voice_models` → pesos STT opcionales.
- `imports/` → documentos originales del operador (solo lectura en contenedor).
- Evitar `docker compose down -v` porque **elimina datos y modelos**. Usar `docker compose down` para apagar sin perder los volúmenes. Documentar y cifrar respaldos antes de uso real.

### Requisitos de seguridad

Solo **localhost, monousuario, equipo controlado**. Token generado aleatoriamente en `.env`, sin acceso público al puerto. Imágenes base deben fijarse a digest para producción; no hay autenticación multiusuario ni cifrado SQLite en aplicación. Consulta [docs/DOCKER_SECURITY.md](docs/DOCKER_SECURITY.md).

## Qué es demostrable y qué no

- Motor PoC: 22 pruebas previas.
- API MVP: 7 pruebas nuevas, incluido token, varias empresas, revisión y tareas.
- Python en entorno creador: `PYTHONPATH=src python -m pytest -q` (29 pruebas) y comprobación estática de JS.
- Docker `build/up`, inferencia real, GPU y voz: **NO probados en este entorno** porque no dispone de Docker. Ver [MVP001_ACCEPTANCE.md](docs/MVP001_ACCEPTANCE.md).

## Fuentes técnicas

- [Ollama en Docker](https://registry.ollama.com/blog/ollama-is-now-available-as-an-official-docker-image)
- [API Ollama](https://github.com/ollama/ollama/blob/main/docs/api.md)
- [Qwen3 1.7B](https://ollama.com/library/qwen3:1.7b)
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper)
- [Piper (CLI)](https://github.com/OHF-Voice/piper1-gpl/blob/main/docs/CLI.md)

---

**Diseño:** primero fidelidad documental y resultados reproducibles, después inferencia y voz. Ninguna respuesta de un LLM reemplaza el juicio profesional de un contador.

### Escaneo residente opcional (daemon Docker)

```bash
docker compose --profile watch up -d --build
docker compose --profile watch logs -f scheduler
```

El scheduler ejecuta escaneo incremental de las carpetas autorizadas cada 300 segundos y registra tareas vencidas en logs locales. No activa el micrófono ni hace consultas al LLM. Se puede ejecutar junto con voz usando `docker compose --profile watch --profile voice up -d --build`. Las escrituras SQLite se serializan y tienen tiempo de espera; validar concurrencia con carga real antes de producción.
