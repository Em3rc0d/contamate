'use strict';
const $ = id => document.getElementById(id);
let token = '';
let currentReview = null;
let lastAnswer = '';
let recorder = null;
let recorded = [];
function notify(text, error=false) { $('feedback').textContent=text; $('feedback').className = error?'feedback error':'feedback'; }
function company(){ const value=$('company').value; if(!value) throw Error('Primero selecciona una empresa.'); return value; }
function period(){ const value=$('period').value; if(!/^\d{4}-\d{2}$/.test(value)) throw Error('Selecciona un período.'); return value; }
async function api(path,opts={}){
  if(!token) throw Error('Ingresa la clave local y pulsa Conectar.');
  let headers = {'X-ContaMate-Token':token,...opts.headers};
  if(opts.body && typeof opts.body==='object' && !(opts.body instanceof FormData)){headers['Content-Type']='application/json';opts.body=JSON.stringify(opts.body);}
  const response=await fetch(path,{...opts,headers,cache:'no-store'});
  if(!response.ok){let error;try{error=(await response.json()).detail;}catch{}throw Error(typeof error==='string'?error:`Error HTTP ${response.status}`);}
  return response;
}
async function json(path,opts){return (await api(path,opts)).json();}
async function run(action){try{await action();}catch(e){notify(e.message,true);}}
async function loadCompanies(){
  const old=$('company').value;
  let items=await json('/api/companies');const select=$('company');
  select.replaceChildren(new Option('Selecciona una empresa',''));
  items.forEach(c=>select.add(new Option(`${c.name} · ${c.ruc}`,c.ruc)));
  if(items.some(c=>c.ruc===old))select.value=old;else if(items.length)select.value=items[0].ruc;
  await loadTasks();
}
async function loadRuntime(){const info=await json('/api/runtime');$('runtimeBadge').textContent=`● Ollama: ${info.ollama} · ${info.installed_models.length} modelo(s) · Voz: ${typeof info.voice==='object'?'conectada':'opcional'}`;}
async function loadTasks(){let r;try{r=company();}catch{return;}
 const tasks=await json(`/api/companies/${r}/tasks`);const parent=$('taskList');parent.replaceChildren();
 if(!tasks.length){const p=document.createElement('p');p.className='placeholder';p.textContent='No hay tareas registradas.';parent.append(p);return;}
 for(const t of tasks){let row=document.createElement('div');row.className='task';let info=document.createElement('div');
  let span=document.createElement('span');span.textContent=t.title; if(t.done)span.className='done';let small=document.createElement('small');small.textContent=` · ${t.due_date||'Sin vencimiento'}`;info.append(span,small);row.append(info);
  if(!t.done){let b=document.createElement('button');b.className='secondary';b.textContent='Completar';b.onclick=()=>run(async()=>{await json(`/api/companies/${r}/tasks/${t.id}/done`,{method:'POST'});await loadTasks();});row.append(b);}parent.append(row);
 }
}
function setCounts(r){$('xmlCount').textContent=r.xml_records;$('regCount').textContent=r.register_records;$('matchCount').textContent=r.matched_keys;$('issueCount').textContent=r.issues.length;}
function renderIssues(r){const list=$('issueList');list.replaceChildren();
 if(!r.issues.length){const p=document.createElement('p');p.className='placeholder';p.textContent='Sin diferencias detectadas en el alcance del motor. Esto no demuestra conformidad SUNAT.';list.append(p);return;}
 for(const issue of r.issues){const card=document.createElement('div');card.className='issue-card';const head=document.createElement('div');head.className='issue-head';
  const name=document.createElement('b');name.textContent=`${issue.voucher_id} · ${issue.issuer_ruc}`;const code=document.createElement('small');code.textContent=issue.code;head.append(name,code);card.append(head);
  const p=document.createElement('p');p.textContent=issue.description;card.append(p);
  const evid=document.createElement('div');evid.className='evidence';for(const e of issue.evidence){const div=document.createElement('div');div.textContent=`${e.source.toUpperCase()} — ${e.file} (${e.location}) · ${e.amount} ${e.currency} · ${e.date}`;evid.append(div);}card.append(evid);list.append(card);
 }
}
async function review(){let r=await json(`/api/companies/${company()}/review?period=${encodeURIComponent(period())}`);currentReview=r;setCounts(r);renderIssues(r);notify(`Revisión completada: ${r.issues.length} hallazgo(s).`);}
$('connect').onclick=()=>run(async()=>{token=$('token').value.trim();await Promise.all([loadCompanies(),loadRuntime()]);$('token').value='';notify('Sesión local autenticada.');});
$('refresh').onclick=()=>run(async()=>{await loadCompanies();await loadRuntime();notify('Datos actualizados.');});
$('company').onchange=()=>run(loadTasks);
$('addCompany').onclick=()=>run(async()=>{await json('/api/companies',{method:'POST',body:{ruc:$('newRuc').value,name:$('newName').value}});await loadCompanies();$('company').value=$('newRuc').value;notify('Empresa registrada. Autoriza una carpeta para leer documentos.');});
$('allow').onclick=()=>run(async()=>{await json(`/api/companies/${company()}/roots`,{method:'POST',body:{folder:$('folder').value}});notify('Carpeta autorizada para lectura. Los archivos originales permanecen intactos.');});
$('scan').onclick=()=>run(async()=>{notify('Escaneando documentos locales…');const result=await json(`/api/companies/${company()}/scan`,{method:'POST'});notify(`Escaneo: ${result.imported} importados, ${result.unchanged} sin cambios, ${result.errors} errores.`);await review();});
$('review').onclick=()=>run(review);
$('report').onclick=()=>run(async()=>{const resp=await api(`/api/companies/${company()}/report?period=${encodeURIComponent(period())}`);const blob=await resp.blob();const a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download=`contamate-${company()}-${period()}.md`;a.click();setTimeout(()=>URL.revokeObjectURL(a.href),5000);});
$('ask').onclick=()=>run(async()=>{const question=$('question').value.trim();if(!question)throw Error('Escribe una pregunta.');$('answer').textContent='Consultando modelo local…';const answer=await json(`/api/companies/${company()}/ask`,{method:'POST',body:{period:period(),question}});lastAnswer=answer.answer;$('answer').textContent=lastAnswer;notify(`Consulta terminada. Fuentes locales recuperadas: ${answer.sources.length}.`);});
$('taskForm').onsubmit=e=>{e.preventDefault();run(async()=>{await json(`/api/companies/${company()}/tasks`,{method:'POST',body:{title:$('taskTitle').value,due:$('taskDate').value||null}});$('taskTitle').value='';$('taskDate').value='';await loadTasks();notify('Pendiente agregado.');});};
$('mic').onclick=()=>run(async()=>{
 if(recorder&&recorder.state==='recording'){recorder.stop();$('mic').textContent='🎙 Dictar';return;}
 if(!window.MediaRecorder || !navigator.mediaDevices)throw Error('Grabación no disponible. Abre la web en http://localhost:8765.');
 let stream=await navigator.mediaDevices.getUserMedia({audio:true});
 try{recorded=[];recorder=new MediaRecorder(stream);recorder.ondataavailable=e=>{if(e.data.size)recorded.push(e.data);};
 recorder.onstop=()=>run(async()=>{stream.getTracks().forEach(t=>t.stop());let blob=new Blob(recorded,{type:recorder.mimeType||'audio/webm'});if(blob.size>8*1024*1024)throw Error('Grabación mayor a 8 MiB.');
 const data=new FormData();data.append('file',blob,'audio.webm');notify('Transcribiendo voz local…');const r=await json('/api/voice/transcribe',{method:'POST',body:data});$('question').value=r.text;notify('Transcripción lista. Revísala antes de consultar.');});
 recorder.start();$('mic').textContent='■ Detener';notify('Grabando únicamente durante esta pulsación.');
 }catch(e){stream.getTracks().forEach(t=>t.stop());throw e;}
});
$('speak').onclick=()=>run(async()=>{if(!lastAnswer)throw Error('Consulta primero al asistente.');notify('Generando voz local…');let resp=await api('/api/voice/speak',{method:'POST',body:{text:lastAnswer.slice(0,1800)}});let blob=await resp.blob();let audio=new Audio(URL.createObjectURL(blob));audio.onended=()=>URL.revokeObjectURL(audio.src);await audio.play();notify('Reproduciendo respuesta local.');});
