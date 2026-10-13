<?php
/* SmartRoute - native PHP port. Reproduces smartroute.core.gate. No deps. */
const DANGER = '/\b(delete|drop|truncate|exec|shell|sudo|rm|rmdir|wire|transfer|payment|refund|deploy|shutdown|revoke|grant|chmod|chown|purge)\b/i';
const WRITE_RE = '/\b(write|update|insert|create|modify|patch|put|post|send|email)\b/i';
const SECRET = '/(sk-[A-Za-z0-9]{12,}|AKIA[0-9A-Z]{12,}|-----BEGIN|password\s*=|api[_-]?key\s*=)/i';
const EXTERNAL = '/(https?:\/\/|ftp:\/\/|@[\w.-]+\.\w+|\bexternal\b)/i';
const RATE_LIMIT = 60;
const MIN_SCORE = 0.5;

function atg_stringify($v): string {
    if ($v === null) return '';
    if (is_array($v) || is_object($v)) return json_encode($v);
    if (is_bool($v)) return $v ? '1' : '';
    return (string)$v;
}

function gate(array $req): array {
    $safe = ['search','fetch_data','read','list','get','lookup','retrieve','summarize','describe','count'];
    $agent = trim(atg_stringify($req['agent'] ?? null));
    $tool = strtolower(trim(atg_stringify($req['tool'] ?? null)));
    $action = atg_stringify($req['action'] ?? null);
    $payload = atg_stringify($req['payload'] ?? null);
    $scope = $req['scope'] ?? null;
    $call = isset($req['call_count']) ? (int)$req['call_count'] : 0;
    $signals = [];
    if ($agent === '') $signals[] = ['rule'=>'ROUTE-NO-IDENTITY','weight'=>0.4,'reason'=>'no agent identity on the request'];
    if ($tool !== '' && !in_array($tool, $safe, true)) $signals[] = ['rule'=>'ROUTE-UNLISTED-TOOL','weight'=>0.25,'reason'=>"tool '$tool' is not on the read-only allowlist"];
    if (preg_match(DANGER, $action)) $signals[] = ['rule'=>'ROUTE-DANGEROUS-ACTION','weight'=>0.5,'reason'=>'action is destructive / high blast-radius'];
    elseif (preg_match(WRITE_RE, $action)) $signals[] = ['rule'=>'ROUTE-WRITE-ACTION','weight'=>0.2,'reason'=>'action mutates state'];
    if (preg_match(SECRET, $payload)) $signals[] = ['rule'=>'ROUTE-SECRET-IN-PAYLOAD','weight'=>0.6,'reason'=>'a secret/credential is present in the payload'];
    if (preg_match(EXTERNAL, $payload) && (preg_match(DANGER, $action) || preg_match(WRITE_RE, $action))) $signals[] = ['rule'=>'ROUTE-EXFIL','weight'=>0.3,'reason'=>'state-changing action with an external destination'];
    if ($call > RATE_LIMIT) $signals[] = ['rule'=>'ROUTE-RATE','weight'=>0.2,'reason'=>"call_count $call exceeds rate limit " . RATE_LIMIT];
    if (empty($scope)) $signals[] = ['rule'=>'ROUTE-UNSCOPED','weight'=>0.15,'reason'=>'no scope/permission declared'];
    $raw = array_sum(array_column($signals, 'weight'));
    $score = max(0, round(1 - $raw, 3));
    $hard = false; foreach ($signals as $s) if ($s['rule'] === 'ROUTE-SECRET-IN-PAYLOAD') $hard = true;
    $granted = ($score >= MIN_SCORE) && !$hard;
    $risk = $score >= 0.75 ? 'low' : ($score >= MIN_SCORE ? 'medium' : 'high');
    return ['granted'=>$granted, 'score'=>$score, 'risk'=>$risk, 'signals'=>$signals];
}

$vpath = $argv[1] ?? __DIR__ . '/../conformance/vectors.json';
$v = json_decode(file_get_contents($vpath), true);
$results = [];
foreach ($v['cases'] as $c) $results[] = array_merge(['name'=>$c['name']], gate($c['request'] ?? []));
echo json_encode(['results'=>$results], JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE), "\n";
