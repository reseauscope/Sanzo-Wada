'use strict';
const assert=require('node:assert/strict');
require('../snapshot.js');
const {verifySnapshot}=require('../app.js');
(async()=>{
 const s=globalThis.WADA_SNAPSHOT;
 assert.equal((await verifySnapshot(s)).length,159);
 for(const key of Object.keys(s.files)){
  const copy=structuredClone(s);const b=Buffer.from(copy.files[key],'base64');b[0]^=1;copy.files[key]=b.toString('base64');
  await assert.rejects(verifySnapshot(copy),/divergente/);
 }
 const missing=structuredClone(s);delete missing.receipt.sha256['wada.py'];await assert.rejects(verifySnapshot(missing));
 const version=structuredClone(s);version.receipt.source_version='0';await assert.rejects(verifySnapshot(version));
 console.log('Snapshot valid; 8 corrupted files, missing entry and wrong version refused: OK');
})().catch(e=>{console.error(e);process.exitCode=1;});
