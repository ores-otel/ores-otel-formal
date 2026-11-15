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
const check=(s,n,a)=>!n.secret_export&&!(n.raw&&n.redacted)&&
  (s.phase!=='stopped'||key(n)===key(s))&&n.exports>=s.exports&&
  (a==='export'||n.exports===s.exports)&&
  (a!=='export'||n.exports===s.exports||
    (s.phase==='accepting'&&s.redacted&&!s.raw&&n.exports<=2));
function verify(next){
 const seen=new Map([[key(init),init]]),q=[init];
 for(let i=0;i<q.length;i++)for(const a of actions){
   const s=q[i],n=next(s,a);
   assert.ok(check(s,n,a),`unsafe ${a}: ${key(n)}`);
   if(!seen.has(key(n))){assert.ok(seen.size<128,'state bound');seen.set(key(n),n);q.push(n);}
 }
 return [...seen.values()];
}
const states=verify(step);
assert.ok(states.length>=5 && states.some(s=>s.exports===2));
assert.ok(states.some(s=>s.phase==='stopped'&&s.raw));
const mutants = [
  // A redaction bypass leaks secret data.
  (s,a)=>a==='export'&&s.raw?{...s,secret_export:true}:step(s,a),
  // Stopping cannot silently emit another item.
  (s,a)=>a==='stop'&&s.phase==='accepting'?{...s,phase:'stopped',exports:s.exports+1}:step(s,a),
  // A stopped pipeline cannot be restarted by another ingest.
  (s,a)=>a==='ingest'&&s.phase==='stopped'?{...s,phase:'accepting',raw:true}:step(s,a),
  // Redacted and raw flags may never be true simultaneously.
  (s,a)=>a==='redact'&&s.raw?{...s,redacted:true}:step(s,a),
  // Export admission requires successful redaction, not merely an ingest.
  (s,a)=>a==='export'&&s.raw?{...s,exports:s.exports+1}:step(s,a),
  // Counters must not roll back between transitions.
  (s,a)=>a==='export'&&s.exports>0?{...s,exports:s.exports-1}:step(s,a),
];
for (const [index, mutant] of mutants.entries()) {
  assert.throws(()=>verify(mutant),/unsafe/, `mutant ${index} should be rejected`);
}
console.log(`model=otel_redaction_gate states=${states.length} negative_controls=${mutants.length} status=PASS scope=abstract`);
