# Evaluación de componentes contables peruanos — 2026-10-21

**Hito:** MK0/MK1 external candidate intake. **Decisión:** NO GO de integración. ContaMate es un asistente documental *local y de apoyo*, NO un emisor tributario ni ERP, de acuerdo con [MVP_CONTRACT](MVP_CONTRACT.md). No se ha agregado dependencia, código, acceso SUNAT, transmisión de datos ni runtime nuevo.

## Alternativas estudiadas y frontera de responsabilidad

| Repositorio externo | Qué afirma ofrecer su propia documentación | Posible uso delimitado | Gate bloqueante |
|---|---|---|---|
| [ContaPerú](https://github.com/contaperu/contaperu) | Motor contable stateless, SIRE/PLE/PCGE, adapters y validadores | Comparación de exportaciones y reglas contables **detrás del control del contador** | Licencia, formatos reales, correctness con contadores y versionado legal; **NO emisión CPE** |
| [SUNAT-cpe Node](https://github.com/davcito/sunat-cpe) | Emisión directa UBL/CDATA/CDR + conciliación de cobros | Solo referencia de estados y errores documentales, no funcionalidad núcleo | Fuera de MVP; jamás incorporar emisión o Clave SOL por analogía |
| [Greenter](https://github.com/thegreenter/greenter) y [Kembec](https://github.com/Kembec/facturacion-electronica-sunat-sdk) | Generación/transporte de XML SUNAT | Lista de campos y tipos para validar importación de XML; no integración operativa | Transferir XML recibidos, no firmar/enviar documentos |
| [Finbot](https://github.com/Eiaell/Finbot) | README de portfolio describe arquitectura evidencia→candidato→transacción con reconciliación explicable | Patrón conceptual de *preservar evidencia y explicación*, con implementación propia | **Repositorio público tipo showcase, no motor productivo reutilizable** |
| [Static Padrón RUC](https://github.com/joelibaceta/static-padron-ruc) | Lookup estático con shards compactos en navegador | Verificación futura de identificadores SIN lookup remoto de expedientes | Derechos/actualizaciones del padrón y conservación mínima de datos |
| [PeruFinDocs](https://github.com/JavierPachas/perufindocs) | Propuesta RAG con citaciones y evals | Referencia para protocolos de evaluación de recuperación | README **under active development**; citas fabricadas/ejemplo no son normas verificadas |
| [Trámites-RAG](https://github.com/acm02-a/tramites-rag) | Set de 50 preguntas con gold labels, recall@k y MRR | Método de evaluación medible para retrieval local y grounding | Dataset distinto; las 116 fichas no representan régimen tributario |

## Propuesta de arquitectura, NO código integrado

```
Archivo original UBL/CSV/XLSX/PDF
  ↓ intake safe / file sha256 / authorized path / RUC declared
Evidence (inmutable por contenido, con versión, fecha y origen)
  ↓ parser determinístico, rechaza ambigüedad
DocumentCandidate (tipo, emisor, receptor, serie, número, importes, errores)
  ↓ matching: RUC + periodo + tipo + documento + montos / moneda
MatchDecision (matched | conflicting | pending | unknown; explicación)
  ↓ revisión humana en conflictos y valores fuera del alcance
Finding (severidad, pruebas, fuentes, contexto y limitaciones)
  ↓ informe *local* — nunca posteo contable ni fiscal automático
```

Esta es una **hipótesis de mejora** del motor existente, no un diagnóstico de gaps basado en tests nuevos. No se debe duplicar la base `documents.py`, `review.py` o los registros actuales por defecto. Realizar diff por capas, no reescritura.

## Gates de aceptación antes de tocar código

| ID | Caso determinístico / negativo | Evidencia exigible |
|---|---|---|
| CA-01 | Dos empresas con documentos de misma serie/número | Cero cruce de expediente/RUC incluso por cache e índice |
| CA-02 | Archivo repetido, misma factura desde XLSX/UBL | Un solo hecho; conservar 2 evidencias sin doble contabilización |
| CA-03 | Reimportación, archivo renombrado, modificación parcial | Fingerprint, versiones y reescaneo idempotente |
| CA-04 | XML con DTD, entidad externa, zip bomb, importes NaN o malformados | Rechazo controlado sin red ni ejecución de entidad externa |
| CA-05 | Factura 01, boleta 03, nota 07/08 como tipos distintos | No mezclar comprobantes originarios y notas, revisar documento origen |
| CA-06 | IGV gravado 18%, exonerado, inafecto, operaciones mixtas | No inferir automáticamente un solo régimen; marcar `UNSUPPORTED` |
| CA-07 | Redondeo y moneda en XML vs registro; diferencias 0.01 | Decimal exacto, decisión de tolerancia documentada por contador |
| CA-08 | Archivo SUNAT SIRE con cambios de columna, encoding o signo | Adaptador versionado, errores con filas y fuentes reproducibles |
| CA-09 | PDF escaneado, dato ausente, OCR incierto | No inventar CPE ni elevar OCR a dato certificado |
| CA-10 | Retrieval normativo: cita no encontrada, norma desactualizada, texto contradice fuente | Respuesta `NO EVIDENCE`, fuente oficial y revisión humana |
| CA-11 | Fallo de Ollama/voz, equipo Windows sin GPU o sin conectividad | Flujo documental sigue operativo sin inferencia |
| CA-12 | Backups/restauración/borrado por empresa, rutas fuera de allowlist | Datos sensibles nunca salen del equipo; recuperar o fallar cerrado |
| CA-13 | XML de prueba sintético; nunca cargar documentos de contribuyentes reales a GitHub | Redacción verificable + procedencia ficticia |
| CA-14 | Comparación a motor externo via una interfaz local simulada | Inputs/outputs versionados, errores deterministas, cero solicitudes a SUNAT |

## Contrato opcional de `AccountingRuleProvider` (propuesto)

Entrada *read only*, estrictamente tipada: `issuer_ruc`, `tax_period`, `document_kind`, `document_series`, `document_number`, `currency`, `tax_amounts`, `evidence_ids[]`, `schema_version`. Sin Clave SOL, certificados, OAuth ni PDFs en peticiones externas.

Salida sin efecto lateral: `rule_id`, `rule_version`, `verdict: pass|fail|unsupported|unknown`, `issues[]`, `citation_ids[]`, `provider_id`, `evaluated_at`. `unknown` debe mantenerse independiente de `pass`; campos no cubiertos no generan `COMPLIANT`.

**No** seleccionar/instalar motores sin (1) formatos SUNAT y contables reproducibles, (2) autorización del contador y prueba negativa, (3) licencia y dependencias aclaradas, (4) necesidad concreta en piloto, (5) costo CPU/RAM y mantenimiento local aceptable.

## Prioridad estratégica

El MVP-001 debe seguir demostrando que encuentra faltantes y diferencias *mejor o más rápido que revisión manual* con una tasa aceptable de falsos positivos/negativos. Una integración contable externa antes de ese ensayo aumenta superficie de mantenimiento y puede desdibujar el producto. **HOLD** hasta evidencia de 2 contadores, 3 expedientes ficticios o anonimizados y resultados comparables.

**Fuente y provenance:** observación de READMEs de repositorios nombrados, revisión acotada previa en [personal_knowledge](https://github.com/Em3rc0d/personal_knowledge/tree/main/research-corpora/github-peru-2026-10-21) y contratos internos. No se ejecutaron tests propios en esta investigación ni se verificó compatibilidad/licencia de terceros para redistribución.
