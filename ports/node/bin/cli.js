#!/usr/bin/env node
'use strict';
const fs = require('fs'), path = require('path');
const { gate } = require('../lib/gate.js');
const argv = process.argv.slice(2);
if (argv[0] === '--request') { process.stdout.write(JSON.stringify(gate(JSON.parse(argv[1] || '{}'))) + '\n'); process.exit(0); }
const vpath = argv[0] || path.join(__dirname, '..', '..', 'conformance', 'vectors.json');
const v = JSON.parse(fs.readFileSync(vpath, 'utf8'));
const results = v.cases.map(c => Object.assign({ name: c.name }, gate(c.request || {})));
process.stdout.write(JSON.stringify({ results }, null, 2) + '\n');
