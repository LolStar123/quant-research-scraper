import test from 'node:test';
import assert from 'node:assert/strict';
import * as m from './model.mjs';
test('workflow invariants and boundary cases',()=>{
const r=m.collect(m.defaults.records);assert.equal(r.length,4);assert.equal(m.collect(m.defaults.records,'options').length,2);assert.equal(r.find(r=>r.doi==='10.example/momentum').sources.length,2);assert.throws(()=>m.collect([{title:'bad',url:'javascript:alert(1)'}]));
});
