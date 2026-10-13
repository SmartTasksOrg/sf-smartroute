'use strict';
// Node conformance: reproduce the Python reference for every vector.
const fs = require('fs'), path = require('path'), cp = require('child_process');
const HERE = __dirname, PORTS = path.join(HERE, '..', '..');
const exp = JSON.parse(fs.readFileSync(path.join(PORTS, 'conformance', 'expected.json'), 'utf8'));
const got = JSON.parse(cp.execSync(`node ${path.join(PORTS, 'node', 'bin', 'cli.js')}`).toString());
let fail = 0;
exp.results.forEach((e, k) => {
  const g = got.results[k];
  if (JSON.stringify(e) !== JSON.stringify(g)) { fail++; console.error(`MISMATCH ${e.name}`); }
});
if (fail) { console.error(`FAIL (${fail})`); process.exit(1); }
console.log(`PASS (${exp.results.length} cases)`);
