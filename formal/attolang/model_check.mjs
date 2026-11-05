// Additional bounded reference model, not a Rust/TS runtime refinement.
import assert from 'node:assert/strict';
const init={phase:'accepting',raw:false,redacted:false,exports:0,secret_export:false};
const actions=['ingest','redact','export','stop'];
const key=s=>JSON.stringify(s);
function step(s,a){
  if(a==='ingest'&&s.phase==='accepting')return {...s,raw:true,redacted:false};
  if(a==='redact'&&s.phase==='accepting')return {...s,raw:false,redacted:true};
  if(a==='export'&&s.phase==='accepting'&&s.redacted&&!s.raw&&s.exports<2)
    return {...s,exports:s.exports+1};
  if(a==='stop')return {...s,phase:'stopped'};
  return s;
}
const check=(s,n)=>!n.secret_export&&!(n.raw&&n.redacted)&&
  (s.phase!=='stopped'||n.exports===s.exports)&&n.exports>=s.exports;
function verify(next){
 const seen=new Map([[key(init),init]]),q=[init];
 for(let i=0;i<q.length;i++)for(const a of actions){
   const s=q[i],n=next(s,a);
   assert.ok(check(s,n),`unsafe ${a}: ${key(n)}`);
   if(!seen.has(key(n))){assert.ok(seen.size<128,'state bound');seen.set(key(n),n);q.push(n);}
 }
 return [...seen.values()];
}
const states=verify(step);
assert.ok(states.length>=5 && states.some(s=>s.exports===2));
assert.ok(states.some(s=>s.phase==='stopped'&&s.raw));
assert.throws(()=>verify((s,a)=>a==='export'&&s.raw?{...s,secret_export:true}:step(s,a)),/unsafe/);
console.log(`model=otel_redaction_gate states=${states.length} negative_controls=1 status=PASS scope=abstract`);
