# Design · Requisitos acotados MVP-001

Cada requisito referencia una implementación o un bloqueo en [matriz de evidencia](../../docs/TRACEABILITY.md). Para contratos de datos ver [MVP_CONTRACT](../../docs/MVP_CONTRACT.md).

| ID | Tipo | Requisito | Estado |
| --- | --- | --- | --- |
| RF-01 | Funcional | Crear/consultar expedientes por RUC | Implementado/prueba local |
| RF-02 | Funcional | Autorizar carpetas sin superposiciones | Implementado/prueba local |
| RF-03 | Funcional | Indexar UBL Invoice, CSV/XLSX, PDF digital | Cobertura parcial delimitada |
| RF-04 | Funcional | Contrastar montos/ausencias/duplicados con evidencias | Implementado en fixtures |
| RF-05 | Funcional | Registrar tareas y exportar informe | Implementado/prueba local |
| RF-06 | Funcional | Asistir mediante Ollama sin cálculos generativos | Implementado/inferencia real pendiente |
| RF-07 | Funcional | Voz bajo demanda | Servicio implementado/audio real pendiente |
| RF-08 | Funcional | Escaneo periódico habilitable | Scheduler implementado/prueba operacional pendiente |
| RNF-01 | No funcional | No modificar documentos originales | Volúmenes `ro`; verificar amenazas |
| RNF-02 | No funcional | Separar datos por RUC y no exponer API públicamente | Tests + binding a localhost |
| RNF-03 | No funcional | Ejecutar en Docker Desktop Windows y Linux | Diseño listo, aceptación pendiente |
| RNF-04 | No funcional | Adaptarse a recursos y no bloquear PC | Heurística presente; benchmarks pendientes |
| RNF-05 | No funcional | No afirmar verificaciones SUNAT no realizadas | Regla de producto; revisar continuamente |

**Escenarios fuera:** notas de crédito, boletas UBL genéricas, imágenes OCR confiable, SIRE online, multiusuario, nube, cargas elevadas, seguridad comercial o certificación tributaria.
