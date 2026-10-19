# Arquitectura técnica v0.1

```
Contador (CLI / voz externa opcional)
       |
       v
Comandos Python ---- consulta opcional Ollama localhost (solo lectura)
       |
       +--> SQLite: empresas, carpetas, fuentes, comprobantes, tareas, FTS5
       |
       +--> Importadores: UBL Invoice XML seguro / CSV / XLSX / PDF digital
       |        |
       |        v
       +--> Normalizador a esquema interno estricto
       |        |
       |        v
       +--> Conciliador determinístico (Decimal / identidad por clave)
       |
       +--> Informe Markdown con referencias y limitaciones
```

- SQLite guarda hechos y procedencia; Ollama **no** es base de datos, calculadora ni autoridad tributaria.
- La carpeta leída se autoriza por RUC. Solo se lee; nunca se escribe en ella durante scan. El informe se genera en carpeta de estado o destino explícito.
- Los comprobantes están asociados a un solo identificador interno de empresa y se filtran por RUC emisor + serie/número + tipo + período.
- La evidencia conserva rutas locales. No se copian documentos a la base: al eliminar un archivo, sus registros se retiran del cómputo y se marca ausente.
- La búsqueda FTS es un prototipo textual, no un RAG semántico complejo ni un sistema de verificación legal de vigencia.
- El motor de IA recibe resumen estructurado e incidencias limitadas (máx. 30), no directorios completos. No dispone de tools para ejecutar acciones.
- Adaptadores externos de voz invocados como procesos con argumentos, sin shell ni captura permanente.

## Decisiones importantes

- Elegir `pypdf` (BSD-3-Clause) para evitar dependencia comercial/AGPL adicional de PyMuPDF en el baseline. La exactitud de extracción PDF debe validarse por separado.
- `defusedxml` para bloquear entidades y DTD, en lugar de tolerar XML no confiable.
- Las representaciones monetarias son `Decimal`, persistidas como strings, nunca `float` para sumas.
- Sin servicios distribuidos; una CLI + SQLite con watcher foreground opcional.
- Ningún agente escribe en ERP, modifica XML, paga tributos ni envía información a nube.

## Restricciones conocidas

- Paginación y procesamiento de XLSX limitados a 50 hojas × 50 000 filas × 100 columnas; máximo 20 MiB comprimidos/por archivo, 80 MiB expansión XLSX.
- Si hay cambios externos en la fuente, hay que re-escanear; reportes antiguos son instantáneas, no vistas vivas.
- Una factura con misma clave pero discrepancias entre múltiples archivos se reporta como duplicado para revisión, sin resolver automáticamente cuál es válida.
- No hay motores de reconocimiento OCR ni evaluación semántica documental. Los PDFs son evidencia, no registros contables estructurados.
- Heurística de selección Ollama basada en RAM/tamaño de modelo es preliminar; faltan control de VRAM, latencia real, throughput y cambios por presión de recursos.
