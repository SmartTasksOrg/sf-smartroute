// SmartRoute - native Go port. Reproduces smartroute.core.gate exactly.
// Standard library only (RE2 + encoding/json).
package main

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
)

var (
	danger   = regexp.MustCompile(`(?i)\b(delete|drop|truncate|exec|shell|sudo|rm|rmdir|wire|transfer|payment|refund|deploy|shutdown|revoke|grant|chmod|chown|purge)\b`)
	write    = regexp.MustCompile(`(?i)\b(write|update|insert|create|modify|patch|put|post|send|email)\b`)
	secret   = regexp.MustCompile(`(?i)(sk-[A-Za-z0-9]{12,}|AKIA[0-9A-Z]{12,}|-----BEGIN|password\s*=|api[_-]?key\s*=)`)
	external = regexp.MustCompile(`(?i)(https?://|ftp://|@[\w.-]+\.\w+|\bexternal\b)`)
)

var safeTools = map[string]bool{"search": true, "fetch_data": true, "read": true, "list": true, "get": true,
	"lookup": true, "retrieve": true, "summarize": true, "describe": true, "count": true}

const rateLimit = 60
const minScore = 0.5

type Signal struct {
	Rule   string  `json:"rule"`
	Weight float64 `json:"weight"`
	Reason string  `json:"reason"`
}
type Decision struct {
	Name     string   `json:"name,omitempty"`
	Granted  bool     `json:"granted"`
	Score    float64  `json:"score"`
	Risk     string   `json:"risk"`
	Signals  []Signal `json:"signals"`
}

func stringify(v interface{}) string {
	if v == nil {
		return ""
	}
	if s, ok := v.(string); ok {
		return s
	}
	b, _ := json.Marshal(v)
	return string(b)
}

func truthy(v interface{}, ok bool) bool {
	if !ok || v == nil {
		return false
	}
	if s, is := v.(string); is {
		return s != ""
	}
	if b, is := v.(bool); is {
		return b
	}
	return true
}

func gate(req map[string]interface{}) Decision {
	agent := strings.TrimSpace(stringify(req["agent"]))
	tool := strings.ToLower(strings.TrimSpace(stringify(req["tool"])))
	action := stringify(req["action"])
	payload := stringify(req["payload"])
	callCount := 0
	if v, ok := req["call_count"]; ok {
		switch t := v.(type) {
		case float64:
			callCount = int(t)
		case string:
			callCount, _ = strconv.Atoi(t)
		}
	}
	signals := []Signal{}
	if agent == "" {
		signals = append(signals, Signal{"ROUTE-NO-IDENTITY", 0.4, "no agent identity on the request"})
	}
	if tool != "" && !safeTools[tool] {
		signals = append(signals, Signal{"ROUTE-UNLISTED-TOOL", 0.25, fmt.Sprintf("tool '%s' is not on the read-only allowlist", tool)})
	}
	if danger.MatchString(action) {
		signals = append(signals, Signal{"ROUTE-DANGEROUS-ACTION", 0.5, "action is destructive / high blast-radius"})
	} else if write.MatchString(action) {
		signals = append(signals, Signal{"ROUTE-WRITE-ACTION", 0.2, "action mutates state"})
	}
	if secret.MatchString(payload) {
		signals = append(signals, Signal{"ROUTE-SECRET-IN-PAYLOAD", 0.6, "a secret/credential is present in the payload"})
	}
	if external.MatchString(payload) && (danger.MatchString(action) || write.MatchString(action)) {
		signals = append(signals, Signal{"ROUTE-EXFIL", 0.3, "state-changing action with an external destination"})
	}
	if callCount > rateLimit {
		signals = append(signals, Signal{"ROUTE-RATE", 0.2, fmt.Sprintf("call_count %d exceeds rate limit %d", callCount, rateLimit)})
	}
	if !truthy(req["scope"], func() bool { _, ok := req["scope"]; return ok }()) {
		signals = append(signals, Signal{"ROUTE-UNSCOPED", 0.15, "no scope/permission declared"})
	}
	raw := 0.0
	for _, s := range signals {
		raw += s.Weight
	}
	score := math.Max(0, math.Round((1-raw)*1000)/1000)
	hard := false
	for _, s := range signals {
		if s.Rule == "ROUTE-SECRET-IN-PAYLOAD" {
			hard = true
		}
	}
	granted := score >= minScore && !hard
	risk := "high"
	if score >= 0.75 {
		risk = "low"
	} else if score >= minScore {
		risk = "medium"
	}
	return Decision{Granted: granted, Score: score, Risk: risk, Signals: signals}
}

func main() {
	vpath := filepath.Join("..", "conformance", "vectors.json")
	if len(os.Args) > 1 {
		vpath = os.Args[1]
	}
	raw, _ := os.ReadFile(vpath)
	var v struct {
		Cases []struct {
			Name    string                 `json:"name"`
			Request map[string]interface{} `json:"request"`
		} `json:"cases"`
	}
	json.Unmarshal(raw, &v)
	results := []Decision{}
	for _, c := range v.Cases {
		d := gate(c.Request)
		d.Name = c.Name
		results = append(results, d)
	}
	b, _ := json.MarshalIndent(map[string]interface{}{"results": results}, "", "  ")
	fmt.Println(string(b))
}
