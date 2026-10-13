'use strict';
/*
 * SmartRoute — native Node port.
 * Reproduces smartroute.core.gate exactly: rule IDs, weights, reason strings,
 * ordering, score (1 - sum(weights), clamped, 3dp), fail-closed secret block,
 * MIN_SCORE=0.5 grant boundary, and risk bands. Zero dependencies.
 */
const DANGER = /\b(delete|drop|truncate|exec|shell|sudo|rm|rmdir|wire|transfer|payment|refund|deploy|shutdown|revoke|grant|chmod|chown|purge)\b/i;
const WRITE = /\b(write|update|insert|create|modify|patch|put|post|send|email)\b/i;
const SECRET = /(sk-[A-Za-z0-9]{12,}|AKIA[0-9A-Z]{12,}|-----BEGIN|password\s*=|api[_-]?key\s*=)/i;
const EXTERNAL = /(https?:\/\/|ftp:\/\/|@[\w.-]+\.\w+|\bexternal\b)/i;
const SAFE_TOOLS = new Set(['search', 'fetch_data', 'read', 'list', 'get', 'lookup', 'retrieve', 'summarize', 'describe', 'count']);
const RATE_LIMIT = 60, MIN_SCORE = 0.5, HARD_BLOCK = new Set(['ROUTE-SECRET-IN-PAYLOAD']);

function stringify(p) { if (p == null) return ''; if (typeof p === 'object') return JSON.stringify(p); return String(p); }

function gate(req) {
  const agent = String(req.agent ?? '').trim();
  const tool = String(req.tool ?? '').trim().toLowerCase();
  const action = String(req.action ?? '');
  const payload = stringify(req.payload);
  const scope = req.scope;
  let call_count = parseInt(req.call_count, 10); if (Number.isNaN(call_count)) call_count = 0;

  const signals = [];
  if (!agent) signals.push({ rule: 'ROUTE-NO-IDENTITY', weight: 0.4, reason: 'no agent identity on the request' });
  if (tool && !SAFE_TOOLS.has(tool)) signals.push({ rule: 'ROUTE-UNLISTED-TOOL', weight: 0.25, reason: `tool '${tool}' is not on the read-only allowlist` });
  if (DANGER.test(action)) signals.push({ rule: 'ROUTE-DANGEROUS-ACTION', weight: 0.5, reason: 'action is destructive / high blast-radius' });
  else if (WRITE.test(action)) signals.push({ rule: 'ROUTE-WRITE-ACTION', weight: 0.2, reason: 'action mutates state' });
  if (SECRET.test(payload)) signals.push({ rule: 'ROUTE-SECRET-IN-PAYLOAD', weight: 0.6, reason: 'a secret/credential is present in the payload' });
  if (EXTERNAL.test(payload) && (DANGER.test(action) || WRITE.test(action))) signals.push({ rule: 'ROUTE-EXFIL', weight: 0.3, reason: 'state-changing action with an external destination' });
  if (call_count > RATE_LIMIT) signals.push({ rule: 'ROUTE-RATE', weight: 0.2, reason: `call_count ${call_count} exceeds rate limit ${RATE_LIMIT}` });
  if (!scope) signals.push({ rule: 'ROUTE-UNSCOPED', weight: 0.15, reason: 'no scope/permission declared' });

  const raw = signals.reduce((s, x) => s + x.weight, 0);
  const score = Math.max(0, Math.round((1 - raw) * 1000) / 1000);
  const hard = signals.some(s => HARD_BLOCK.has(s.rule));
  const granted = score >= MIN_SCORE && !hard;
  const risk = score >= 0.75 ? 'low' : (score >= MIN_SCORE ? 'medium' : 'high');
  return { granted, score, risk, signals };
}
module.exports = { gate };
