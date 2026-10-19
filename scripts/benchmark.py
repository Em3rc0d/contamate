"""Medición real contra el contenedor Ollama (no simulada).
Ejecutar: docker compose exec app python scripts/benchmark.py --model qwen3:1.7b --trials 3
"""
import argparse
import json
import os
import statistics
import time
from urllib.request import Request, urlopen


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--model',default=os.getenv('CONTAMATE_MODEL','qwen3:1.7b'))
    p.add_argument('--trials',type=int,default=3)
    args=p.parse_args()
    if not 1 <= args.trials <= 10: raise ValueError('Repeticiones permitidas: 1-10')
    endpoint=os.getenv('CONTAMATE_OLLAMA_URL','http://127.0.0.1:11434')
    if endpoint not in ('http://ollama:11434','http://127.0.0.1:11434'):raise ValueError('Endpoint no autorizado')
    timings=[]
    for i in range(args.trials):
        payload={'model':args.model,'stream':False,'keep_alive':'30s','think':False,
                 'options':{'temperature':0,'num_ctx':2048,'num_predict':100},
                 'messages':[{'role':'system','content':'Responde solo en español en 1 oración.'},
                             {'role':'user','content':'Explica qué significa contrastar dos importes documentales sin afirmar validez tributaria.'}]}
        request=Request(endpoint+'/api/chat',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
        start=time.monotonic()
        with urlopen(request,timeout=240) as resp:data=json.load(resp)
        elapsed=time.monotonic()-start
        tokens=data.get('eval_count',0)
        generate_ns=data.get('eval_duration',0)
        throughput=round(tokens*1e9/generate_ns,2) if generate_ns else None
        record={'trial':i+1,'seconds':round(elapsed,3),'tokens':tokens,'tokens_per_s':throughput,'model':args.model}
        timings.append(elapsed)
        print(json.dumps(record,ensure_ascii=False))
    print(json.dumps({'median_seconds':round(statistics.median(timings),3),
                      'note':'Calibración de rendimiento, no validación de exactitud contable.'},ensure_ascii=False))

if __name__=='__main__':main()
