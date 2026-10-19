# Contrato funcional — PoC → MVP

## Propósito

Un asistente residente **local y de apoyo**, que revisa fuentes contables exportadas por terceros, preserva evidencia y entrega al contador observaciones verificables. No reemplaza sistema contable ni decisiones profesionales.

## Lo que está demostrado en PoC 0.1.0

| Identificador | Criterio de aceptación | Estado |
|---|---|---|
| POC-01 | Registrar 2+ RUC distintos y consultar únicamente su expediente | 22 pruebas, incluyendo aislamiento |
| POC-02 | Importar facturas UBL Invoice y registros de compras CSV/XLSX con formato explícito | Verificado con muestras sintéticas |
| POC-03 | Detectar montos inconsistentes, claves duplicadas, XML sin registro y registro sin XML | Verificado |
| POC-04 | Repetir escaneo sin duplicar contenido y dejar de contar archivos eliminados | Verificado |
| POC-05 | Dar ruta, fila o ruta XML para cada discrepancia | Verificado |
| POC-06 | Rechazar XML con DTD, importes ambiguos y archivos demasiado grandes | Verificado en las pruebas |
| POC-07 | Generar informes Markdown con limitaciones | Verificado |
| POC-08 | Indexar normativa documental con origen y fechas declaradas | Verificado mediante FTS5 |
| POC-09 | Consultar resultados con Ollama solo localhost | Interfaz probada con simulación, sin modelo real |
| POC-10 | Transcribir y sintetizar voz mediante ejecutables externos | Interfaz creada, sin prueba de modelos reales |

## Alcance mínimo recomendado del MVP pilotable

1. **Adapters**: UBL Invoice 2.1 real y notas de crédito; exportación SIRE real de pruebas anonimizadas; mapeos de exportaciones de al menos dos softwares usados por contadores. Validar ejemplos de formatos y actualizaciones.
2. **Conciliación**: particionar por empresa, período y tipo; identificar anulaciones, duplicados y excepciones; tasas de falsos positivos y casos de control firmados por contador.
3. **Corpus jurídico**: ingestión de normas oficiales con identificador de fuente, fecha de publicación, vigencia por disposición y aviso de conflicto; revisión humana de citas y límites de responsabilidad.
4. **AI runtime**: selección de modelo ajustada con benchmarks CPU/GPU reales, límites de RAM, timeout, cola de trabajos, fallback determinístico cuando IA falle.
5. **Experiencia**: conversación de sesión y micrófono push-to-talk configurado explícitamente; voz opcional; tareas persistentes; respuestas citadas; empaquetado Windows portable.
6. **Privacidad**: cifrado/gestión de backups, logs redactados, auditoría de permisos, política de retención y borrado por empresa; DPIA según aplique.
7. **Uso real**: piloto supervisado con al menos 2 contadores y 3 expedientes anónimos, comparado contra revisión manual. No subir datos reales a repositorios ni servicios externos.

## Gate GO del MVP

- Cero cálculos monetarios incorrectos en conjunto etiquetado para las operaciones que la app afirma soportar.
- Cero cruces documentales de RUC en pruebas multiempresa.
- Cobertura y tasas de falsos negativos de hallazgos medidas y explícitas; sin atribuir cumplimiento al resultado vacío.
- No se pierde información tras cierre abrupto, cambio de archivo o repetición de escaneo.
- Latencia/CPU/memoria medidos en portátiles de 8 y 16 GB bajo una carga real; rendimiento mínimo definido según resultados, no antes.
- Integraciones de voz, hardware y Ollama verificadas en Windows real; no considerar mocks como validación de producción.
- Autorizaciones, condiciones tributarias y restricciones legales verificadas por profesional peruano.

## No objetivos del MVP

ERP completo, emisión y declaración ante SUNAT, acceso automático a Clave SOL, registro de asientos contables sin aprobación, OCR confiable para escaneos arbitrarios, reemplazo de un contador, SaaS cloud, RPA sobre escritorios desconocidos y una API universal SUNAT.
