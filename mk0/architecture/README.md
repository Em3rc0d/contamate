# Architecture · Restricciones tempranas

- Local-first y datos separados por RUC/periodo, sin sincronización obligatoria.
- Lectura de archivos autorizados, originales inmutables, índices y SHA-256.
- Adaptadores explícitos por formato, más ejecución determinística para conciliación monetaria (`decimal`).
- Modelo lingüístico opcional, RAG local con fuentes versionadas; sin garantía normativa global.
- Docker Compose piloto monousuario en localhost; controles para la operación real pendientes.
- Conectores SUNAT y otros canales únicamente futuros, por autorización y alcance definido.

Ver [ADR](../../docs/DECISIONS.md).
