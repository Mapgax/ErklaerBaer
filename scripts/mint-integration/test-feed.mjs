import assert from 'node:assert/strict';
import { createHandler } from '../../../MINT-Bot/api/production-favorites.js';
import { checkMintRequest } from '../../../MINT-Bot/lib/db.js';
const read='r'.repeat(40),write='w'.repeat(40);
const env={ERKLAERBAER_READ_TOKEN:read,MINT_WRITE_TOKEN:write,MINT_DB_URL:'mock'};
let queries=0;
const rows=Array.from({length:83},(_,i)=>({id:`topic-${String(i).padStart(3,'0')}`}));
const handler=createHandler(async sql=>{queries++;assert.match(sql,/status = 'nochmal'/);assert.match(sql,/nochmal_tauglich = TRUE/);assert.doesNotMatch(sql,/LIMIT|tage|history/i);return rows;},env);
function response(){return {headers:{},statusCode:0,setHeader(k,v){this.headers[k]=v},status(c){this.statusCode=c;return this},json(v){this.body=v;return this}}}
for(const method of ['POST','PUT','PATCH','DELETE','HEAD']){
 const res=response();await handler({method,headers:{'x-erklaerbaer-read-token':read}},res);assert.equal(res.statusCode,405);
}
for(const headers of [{},{'x-mint-token':write},{'x-erklaerbaer-read-token':write}]){
 const res=response();await handler({method:'GET',headers},res);assert.equal(res.statusCode,403);
}
assert.equal(queries,0);
const first=response();await handler({method:'GET',headers:{'x-erklaerbaer-read-token':read}},first);
assert.equal(first.statusCode,200);assert.equal(first.body.topic_ids.length,83);
assert.deepEqual(Object.keys(first.body).sort(),['revision','schema_version','topic_ids']);assert.match(first.headers['Cache-Control'],/no-store/);
const second=response();await handler({method:'GET',headers:{'x-erklaerbaer-read-token':read}},second);assert.equal(first.body.revision,second.body.revision);
process.env.ERKLAERBAER_READ_TOKEN=read;process.env.MINT_WRITE_TOKEN=write;process.env.MINT_DB_URL='mock';
const denied=response();assert.equal(checkMintRequest({method:'POST',headers:{'x-mint-token':read}},denied,{method:'POST'}),false);assert.equal(denied.statusCode,403);
process.env.MINT_WRITE_TOKEN=read;const same=response();assert.equal(checkMintRequest({method:'POST',headers:{'x-mint-token':read}},same,{method:'POST'}),false);assert.equal(same.statusCode,403);
const fail=createHandler(async()=>{throw Error('secret')},env),failed=response();await fail({method:'GET',headers:{'x-erklaerbaer-read-token':read}},failed);assert.equal(failed.statusCode,502);assert.ok(!JSON.stringify(failed.body).includes('secret'));
console.log('PASS: 83 topics; GET-only; auth isolation; stable revision; no history; sanitized failure; no database/network calls');
