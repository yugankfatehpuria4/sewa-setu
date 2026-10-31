"""Reproducible analysis of the Sewa Setu production logs (Jan-Jun 2026).

Usage: python -I analysis/analyze_logs.py <extracted-logs-dir>
"""
import gzip, re, sys, collections, statistics, os

d = sys.argv[1]
NG = re.compile(r'^(\S+) \S+ \S+ \[(\d\d)/(\w+)/(\d{4}):(\d\d):(\d\d):(\d\d) [^\]]+\] "(\S+) (\S+) [^"]*" (\d{3}) (\d+) "[^"]*" "([^"]*)" rt=([\d.]+)')
MON = {m: i for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split(), 1)}

def norm(path):
    p = path.split("?")[0]
    p = re.sub(r"/application/\d+", "/application/<id>", p)
    p = re.sub(r"/ack/\d+\.pdf", "/ack/<id>.pdf", p)
    p = re.sub(r"/admin/(approve|reject|application)/\d+", r"/admin/\1/<id>", p)
    p = re.sub(r"/form/\d+", "/form/<n>", p)
    return p

per_route = collections.defaultdict(collections.Counter)
lat = collections.defaultdict(list)
per_sec = collections.Counter()
per_day = collections.Counter()
per_month_status = collections.defaultdict(collections.Counter)
ip_app_ids = collections.defaultdict(set)
admin_actions = collections.Counter()
inj = collections.Counter()
inj_examples = []
total = 0
for line in gzip.open(os.path.join(d, "nginx-access.log.gz"), "rt", errors="replace"):
    m = NG.match(line)
    if not m:
        continue
    total += 1
    ip, dd, mon, yy, hh, mi, ss, meth, path, st, size, ua, rt = m.groups()
    r = meth + " " + norm(path)
    per_route[r][st] += 1
    lat[r].append(float(rt))
    per_sec["%s-%02d-%s %s:%s:%s" % (yy, MON[mon], dd, hh, mi, ss)] += 1
    per_day["%s-%02d-%s" % (yy, MON[mon], dd)] += 1
    per_month_status[MON[mon]][st] += 1
    am = re.match(r"/application/(\d+)", path)
    if am:
        ip_app_ids[ip].add(am.group(1))
    if re.match(r"/admin/(approve|reject)/", path):
        admin_actions[(meth, st)] += 1
    low = path.lower()
    if any(k in low for k in ("%27", "'", "union", "select", "--", "or%201=1", "../", "%2e%2e")):
        inj[r] += 1
        if len(inj_examples) < 8:
            inj_examples.append(line.strip()[:220])

def pct(v, p):
    v = sorted(v); return v[min(len(v) - 1, int(len(v) * p))]

print("=== NGINX: %d requests ===" % total)
print("\n--- Status by route (top 30 by volume) ---")
for r, c in sorted(per_route.items(), key=lambda x: -sum(x[1].values()))[:30]:
    n = sum(c.values())
    print("%-34s n=%7d  %s  p50=%.3f p95=%.3f p99=%.3f" % (r, n, dict(c.most_common(5)), pct(lat[r], .5), pct(lat[r], .95), pct(lat[r], .99)))
print("\n--- 5xx by route ---")
for r, c in sorted(per_route.items(), key=lambda x: -sum(v for k, v in x[1].items() if k[0] == "5")):
    n5 = sum(v for k, v in c.items() if k[0] == "5")
    if n5: print("%-34s 5xx=%d / %d (%.1f%%)" % (r, n5, sum(c.values()), 100.0 * n5 / sum(c.values())))
print("\n--- Peak RPS (top 10 seconds) ---")
for k, v in per_sec.most_common(10): print(k, v)
print("\n--- Busiest days ---")
for k, v in per_day.most_common(12): print(k, v)
print("\n--- Status by month ---")
for mth in sorted(per_month_status): print(mth, dict(per_month_status[mth].most_common()))
print("\n--- IPs viewing many distinct application ids (enumeration) ---")
enum = sorted(((len(s), ip) for ip, s in ip_app_ids.items()), reverse=True)[:10]
for n, ip in enum: print(ip, n)
print("IPs with >20 distinct ids:", sum(1 for s in ip_app_ids.values() if len(s) > 20))
print("\n--- approve/reject hits ---", dict(admin_actions))
print("\n--- Injection-looking requests by route ---", dict(inj))
for e in inj_examples: print("  ", e)

print("\n=== APP LOG ===")
levels = collections.Counter(); msgs = collections.Counter(); exc = collections.Counter(); loc = collections.Counter()
otp_exp_age = []
lines = gzip.open(os.path.join(d, "sewasetu-app.log.gz"), "rt", errors="replace").read().splitlines()
for i, l in enumerate(lines):
    m = re.match(r"^\S+ \S+ (\w+) in app: (.*)$", l)
    if m:
        levels[m.group(1)] += 1
        msg = re.sub(r"\d+", "N", m.group(2))[:90]
        msgs[(m.group(1), msg)] += 1
        a = re.search(r"otp expired .* age=(\d+)s", l)
        if a: otp_exp_age.append(int(a.group(1)))
    elif re.match(r"^\w+(Error|Exception)[:\s]", l) or re.match(r"^[\w.]+Error:", l):
        exc[l[:120]] += 1
    fm = re.match(r'^\s+File "([^"]+)", line (\d+), in (\w+)', l)
    if fm and "/app/" in fm.group(1): loc["%s:%s %s" % fm.groups()] += 1
print("levels", dict(levels))
print("\n--- top messages ---")
for (lv, m), c in msgs.most_common(25): print("%6d %-7s %s" % (c, lv, m))
print("\n--- exceptions ---")
for k, c in exc.most_common(15): print("%6d %s" % (c, k))
print("\n--- app code locations in tracebacks ---")
for k, c in loc.most_common(15): print("%6d %s" % (c, k))
if otp_exp_age:
    print("\nOTP expired events: %d, age min=%d median=%d max=%d" % (len(otp_exp_age), min(otp_exp_age), statistics.median(otp_exp_age), max(otp_exp_age)))

print("\n=== CRON ===")
ok = fail = 0; first_fail = None; last_ok = None; approved = 0
for l in open(os.path.join(d, "cron.log"), errors="replace"):
    m = re.match(r"(\d{4}-\d\d-\d\d) \S+ deemed approval: (\d+)", l)
    if m: ok += 1; last_ok = m.group(1); approved += int(m.group(2))
    if l.startswith("FileNotFoundError"):
        fail += 1
print("successful runs=%d (last %s), total deemed-approved=%d, FileNotFoundError lines=%d" % (ok, last_ok, approved, fail))
