import test from 'node:test';
import assert from 'node:assert/strict';
import {safeSourceUrl,describeMode,clampScore,decodeResponse} from '../src/services/protocol.mjs';

test('source links reject scripts, local files and embedded credentials',()=>{for(const url of ['javascript:alert(1)','data:text/html,x','file:///etc/passwd','https://user:secret@example.org'])assert.equal(safeSourceUrl(url),null);assert.equal(safeSourceUrl('https://example.org/source'),'https://example.org/source');});
test('fixture labels cannot look like live search',()=>{assert.equal(describeMode('mock'),'Synthetic test data');assert.equal(describeMode('live'),'Live provider mode');assert.equal(describeMode('unconfigured'),'No provider configured');});
test('unavailable scores remain unassessed',()=>{for(const n of [null,undefined,'90',NaN,Infinity])assert.equal(clampScore(n),null);assert.equal(clampScore(80),80);assert.equal(clampScore(-5),0);});
test('API failures retain actionable errors',async()=>{await assert.rejects(decodeResponse(new Response(JSON.stringify({detail:'Provider is not configured.'}),{status:503})),/Provider is not configured/);});
test('validation errors expose field names',async()=>{await assert.rejects(decodeResponse(new Response(JSON.stringify({detail:[{loc:['body','title'],msg:'Required'}]}),{status:422})),/title: Required/);});
test('HTML error pages are not treated as success',async()=>{await assert.rejects(decodeResponse(new Response('<html>error</html>',{status:502})),/unreadable data/);});
test('successful API bodies remain intact',async()=>{const data={status:'insufficient_evidence',citations:[],mode:'unconfigured'};assert.deepEqual(await decodeResponse(new Response(JSON.stringify(data))),data);});
