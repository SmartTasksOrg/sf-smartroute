import java.nio.file.*;
import java.util.*;
import java.util.regex.*;

/*
 * SmartRoute - native Java port. Reproduces smartroute.core.gate exactly.
 * JDK-only.  javac SmartRoute.java && java SmartRoute [vectors.json]
 */
public class SmartRoute {

    static final Pattern DANGER = Pattern.compile(
        "\\b(delete|drop|truncate|exec|shell|sudo|rm|rmdir|wire|transfer|payment|refund|deploy|shutdown|revoke|grant|chmod|chown|purge)\\b", Pattern.CASE_INSENSITIVE);
    static final Pattern WRITE = Pattern.compile(
        "\\b(write|update|insert|create|modify|patch|put|post|send|email)\\b", Pattern.CASE_INSENSITIVE);
    static final Pattern SECRET = Pattern.compile(
        "(sk-[A-Za-z0-9]{12,}|AKIA[0-9A-Z]{12,}|-----BEGIN|password\\s*=|api[_-]?key\\s*=)", Pattern.CASE_INSENSITIVE);
    static final Pattern EXTERNAL = Pattern.compile(
        "(https?://|ftp://|@[\\w.-]+\\.\\w+|\\bexternal\\b)", Pattern.CASE_INSENSITIVE);
    static final Set<String> SAFE = Set.of("search", "fetch_data", "read", "list", "get", "lookup", "retrieve", "summarize", "describe", "count");
    static final int RATE_LIMIT = 60;
    static final double MIN_SCORE = 0.5;

    static String str(Object v) {
        if (v == null) return "";
        if (v instanceof String s) return s;
        if (v instanceof Double d) return (d == Math.floor(d) && !d.isInfinite()) ? String.valueOf(d.longValue()) : d.toString();
        return String.valueOf(v);
    }

    static boolean truthy(Object v) {
        if (v == null) return false;
        if (v instanceof String s) return !s.isEmpty();
        if (v instanceof Boolean b) return b;
        return true;
    }

    static Map<String, Object> sig(String rule, double w, String reason) {
        Map<String, Object> m = new LinkedHashMap<>();
        m.put("rule", rule); m.put("weight", w); m.put("reason", reason);
        return m;
    }

    static Map<String, Object> gate(Map<String, Object> req) {
        String agent = str(req.get("agent")).trim();
        String tool = str(req.get("tool")).trim().toLowerCase();
        String action = str(req.get("action"));
        String payload = req.get("payload") instanceof Map || req.get("payload") instanceof List
            ? Json.write(req.get("payload")) : str(req.get("payload"));
        int call = 0;
        Object cc = req.get("call_count");
        if (cc instanceof Double d) call = d.intValue();
        else if (cc instanceof String s) { try { call = Integer.parseInt(s.trim()); } catch (Exception e) {} }

        List<Map<String, Object>> signals = new ArrayList<>();
        if (agent.isEmpty()) signals.add(sig("ROUTE-NO-IDENTITY", 0.4, "no agent identity on the request"));
        if (!tool.isEmpty() && !SAFE.contains(tool)) signals.add(sig("ROUTE-UNLISTED-TOOL", 0.25, "tool '" + tool + "' is not on the read-only allowlist"));
        if (DANGER.matcher(action).find()) signals.add(sig("ROUTE-DANGEROUS-ACTION", 0.5, "action is destructive / high blast-radius"));
        else if (WRITE.matcher(action).find()) signals.add(sig("ROUTE-WRITE-ACTION", 0.2, "action mutates state"));
        if (SECRET.matcher(payload).find()) signals.add(sig("ROUTE-SECRET-IN-PAYLOAD", 0.6, "a secret/credential is present in the payload"));
        if (EXTERNAL.matcher(payload).find() && (DANGER.matcher(action).find() || WRITE.matcher(action).find()))
            signals.add(sig("ROUTE-EXFIL", 0.3, "state-changing action with an external destination"));
        if (call > RATE_LIMIT) signals.add(sig("ROUTE-RATE", 0.2, "call_count " + call + " exceeds rate limit " + RATE_LIMIT));
        if (!truthy(req.get("scope"))) signals.add(sig("ROUTE-UNSCOPED", 0.15, "no scope/permission declared"));

        double raw = 0;
        for (var s : signals) raw += (double) s.get("weight");
        double score = Math.max(0, Math.round((1 - raw) * 1000) / 1000.0);
        boolean hard = signals.stream().anyMatch(s -> s.get("rule").equals("ROUTE-SECRET-IN-PAYLOAD"));
        boolean granted = score >= MIN_SCORE && !hard;
        String risk = score >= 0.75 ? "low" : (score >= MIN_SCORE ? "medium" : "high");
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("granted", granted); out.put("score", score); out.put("risk", risk); out.put("signals", signals);
        return out;
    }

    public static void main(String[] args) throws Exception {
        String vpath = args.length >= 1 ? args[0]
            : Paths.get(System.getProperty("user.dir"), "..", "conformance", "vectors.json").toString();
        Json j = new Json(Files.readString(Paths.get(vpath)));
        Map<String, Object> root = j.parseObject();
        @SuppressWarnings("unchecked")
        List<Object> cases = (List<Object>) root.get("cases");
        List<Object> results = new ArrayList<>();
        for (Object oc : cases) {
            @SuppressWarnings("unchecked")
            Map<String, Object> c = (Map<String, Object>) oc;
            @SuppressWarnings("unchecked")
            Map<String, Object> req = (Map<String, Object>) c.getOrDefault("request", new LinkedHashMap<>());
            Map<String, Object> out = new LinkedHashMap<>();
            out.put("name", c.get("name"));
            out.putAll(gate(req));
            results.add(out);
        }
        Map<String, Object> top = new LinkedHashMap<>();
        top.put("results", results);
        System.out.println(Json.write(top));
    }

    // ---- minimal JSON parse + write ----
    static class Json {
        final String s; int i;
        Json(String s) { this.s = s; }
        void ws() { while (i < s.length() && Character.isWhitespace(s.charAt(i))) i++; }
        Map<String, Object> parseObject() { ws(); return (Map<String, Object>) value(); }
        Object value() { ws(); char c = s.charAt(i);
            return switch (c) { case '{' -> obj(); case '[' -> arr(); case '"' -> str();
                case 't', 'f' -> bool(); case 'n' -> nul(); default -> num(); }; }
        Map<String, Object> obj() { Map<String, Object> m = new LinkedHashMap<>(); i++; ws();
            if (s.charAt(i) == '}') { i++; return m; }
            while (true) { ws(); String k = str(); ws(); i++; m.put(k, value()); ws();
                if (s.charAt(i) == ',') { i++; continue; } i++; break; } return m; }
        List<Object> arr() { List<Object> a = new ArrayList<>(); i++; ws();
            if (s.charAt(i) == ']') { i++; return a; }
            while (true) { a.add(value()); ws(); if (s.charAt(i) == ',') { i++; continue; } i++; break; } return a; }
        String str() { StringBuilder b = new StringBuilder(); i++;
            while (true) { char c = s.charAt(i++); if (c == '"') break;
                if (c == '\\') { char e = s.charAt(i++); switch (e) {
                    case '"' -> b.append('"'); case '\\' -> b.append('\\'); case '/' -> b.append('/');
                    case 'n' -> b.append('\n'); case 'r' -> b.append('\r'); case 't' -> b.append('\t');
                    case 'b' -> b.append('\b'); case 'f' -> b.append('\f');
                    case 'u' -> { b.append((char) Integer.parseInt(s.substring(i, i + 4), 16)); i += 4; }
                    default -> b.append(e); } } else b.append(c); }
            return b.toString(); }
        Object bool() { if (s.startsWith("true", i)) { i += 4; return Boolean.TRUE; } i += 5; return Boolean.FALSE; }
        Object nul() { i += 4; return null; }
        Object num() { int st = i; while (i < s.length() && "+-.eE0123456789".indexOf(s.charAt(i)) >= 0) i++;
            return Double.parseDouble(s.substring(st, i)); }

        static String esc(String s) { StringBuilder b = new StringBuilder();
            for (char c : s.toCharArray()) switch (c) {
                case '"' -> b.append("\\\""); case '\\' -> b.append("\\\\");
                case '\n' -> b.append("\\n"); case '\r' -> b.append("\\r"); case '\t' -> b.append("\\t");
                default -> b.append(c); } return b.toString(); }
        @SuppressWarnings("unchecked")
        static String write(Object o) {
            if (o == null) return "null";
            if (o instanceof String s) return "\"" + esc(s) + "\"";
            if (o instanceof Boolean || o instanceof Integer || o instanceof Long) return o.toString();
            if (o instanceof Double d) return (d == Math.floor(d) && !d.isInfinite()) ? String.valueOf(d.longValue()) + ".0" : d.toString();
            if (o instanceof List<?> l) { StringBuilder b = new StringBuilder("[");
                for (int k = 0; k < l.size(); k++) { if (k > 0) b.append(","); b.append(write(l.get(k))); }
                return b.append("]").toString(); }
            Map<String, Object> m = (Map<String, Object>) o; StringBuilder b = new StringBuilder("{"); boolean f = true;
            for (var e : m.entrySet()) { if (!f) b.append(","); f = false;
                b.append("\"").append(esc(e.getKey())).append("\":").append(write(e.getValue())); }
            return b.append("}").toString();
        }
    }
}
