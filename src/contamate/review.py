"""Reglas de comparación determinísticas. No valida aceptación tributaria SUNAT."""
from collections import defaultdict
from datetime import date
from decimal import Decimal


def compare(conn, company, period):
    try:
        year, month = map(int, period.split('-'))
        assert len(period) == 7 and 1 <= month <= 12
        first = date(year, month, 1).isoformat()
        last = date(year + (month == 12), (month % 12) + 1, 1).isoformat()
    except (ValueError, AssertionError) as exc:
        raise ValueError('Período esperado YYYY-MM') from exc
    cid = company['id']
    found = conn.execute('''SELECT r.*, d.path FROM records r JOIN documents d ON r.document_id=d.id
                            WHERE r.company_id=? AND d.company_id=? AND d.status='ok'
                              AND r.issue_date >= ? AND r.issue_date < ?''', (cid,cid,first,last)).fetchall()
    sources = defaultdict(lambda: {'xml': [], 'registro': []})
    for row in found:
        # Only compras: emisor distinto de la empresa y receptor coincidente o no consignado en registro.
        if row['issuer_ruc'] == company['ruc']:
            continue
        if row['receiver_ruc'] and row['receiver_ruc'] != company['ruc']:
            continue
        key = (row['issuer_ruc'], row['voucher_id'], row['voucher_type'])
        sources[key][row['source_kind']].append(row)
    issues = []
    checked = 0
    for (issuer, voucher, kind), sides in sorted(sources.items()):
        xml, reg = sides['xml'], sides['registro']
        evidence = [{'source': r['source_kind'], 'file': r['path'],
                     'location': r['source_location'], 'amount': r['total'],
                     'currency': r['currency'], 'date': r['issue_date']}
                    for r in xml + reg]
        if len(xml) > 1 or len(reg) > 1:
            issues.append({'code':'DUPLICATE_KEY','issuer_ruc':issuer,'voucher_id':voucher,
                           'description':'Hay más de una fila/archivo con la misma clave en una fuente; revisar duplicados.',
                           'evidence':evidence})
            continue
        if not xml or not reg:
            issues.append({'code':('MISSING_XML' if reg else 'MISSING_REGISTER'),
                           'issuer_ruc':issuer,'voucher_id':voucher,
                           'description':('Registro importado sin XML correspondiente.' if reg else 'XML sin fila de registro correspondiente.'),
                           'evidence':evidence})
            continue
        checked += 1
        for field, code, label in [('total','AMOUNT_MISMATCH','Monto'),('currency','CURRENCY_MISMATCH','Moneda'),('issue_date','DATE_MISMATCH','Fecha')]:
            left, right = xml[0][field], reg[0][field]
            equal = Decimal(left) == Decimal(right) if field == 'total' else left == right
            if not equal:
                issues.append({'code':code,'issuer_ruc':issuer,'voucher_id':voucher,
                               'description':f'{label} no coincide: XML={left}; registro={right}.',
                               'evidence':evidence})
    error_docs = [dict(row) for row in conn.execute(
        "SELECT path,status,note FROM documents WHERE company_id=? AND status <> 'ok'", (cid,))]
    return {
        'company': {'ruc':company['ruc'],'name':company['name']},'period':period,
        'xml_records':sum(len(v['xml']) for v in sources.values()),
        'register_records':sum(len(v['registro']) for v in sources.values()),
        'matched_keys':checked, 'issues':issues, 'unprocessed_documents':error_docs,
        'limitations':[
            'No se ha consultado SUNAT. XML presente no implica validez o aceptación tributaria.',
            'Solo se comparan facturas de compras del mismo período por RUC emisor, número y tipo.',
            'La ausencia de observaciones no demuestra cierre tributario correcto.',
            'No se interpretan PDF como comprobantes ni se reconoce OCR.',
            'Los registros CSV/XLSX requieren cabeceras conocidas y datos no ambiguos.'
        ]
    }


def report_md(review, tasks=None):
    ruc, name = review['company']['ruc'], review['company']['name']
    lines = [f'# Informe local ContaMate — {name}',f'RUC: {ruc}  |  Período: {review["period"]}',
             '', '**Estado: REQUIERE REVISIÓN HUMANA. NO ES UNA VALIDACIÓN DE SUNAT.**','',
             f'- XML de compras: {review["xml_records"]}',
             f'- Registros importados: {review["register_records"]}',
             f'- Claves comparadas: {review["matched_keys"]}',
             f'- Hallazgos: {len(review["issues"])}','', '## Hallazgos']
    if not review['issues']:
        lines.append('Sin diferencias detectadas en el alcance de esta comparación; no equivale a conformidad tributaria.')
    for n,i in enumerate(review['issues'],1):
        lines.extend(['',f'### {n}. {i["code"]}: {i["voucher_id"]} / {i["issuer_ruc"]}',
                      i['description'], '**Evidencia:**'])
        for e in i['evidence']:
            lines.append(f'- {e["source"]}: `{e["file"]}` ({e["location"]}), {e["amount"]} {e["currency"]}, {e["date"]}')
    lines.extend(['','## Archivos no procesados'])
    for d in review['unprocessed_documents']:
        lines.append(f'- `{d["path"]}`: {d["status"]}: {d["note"]}')
    if not review['unprocessed_documents']:
        lines.append('No hay errores de importación registrados en las carpetas escaneadas.')
    if tasks is not None:
        lines.extend(['','## Pendientes configurados'])
        for t in tasks:
            if not t['done']:
                lines.append(f'- {t["title"]} (vencimiento {t["due_date"] or "sin fecha"})')
        if not any(not t['done'] for t in tasks):
            lines.append('Sin tareas abiertas.')
    lines.extend(['','## Limitaciones conocidas',*['- '+s for s in review['limitations']],
                  '', 'Documento de trabajo generado localmente. Revisión profesional obligatoria.'])
    return '\n'.join(lines) + '\n'
