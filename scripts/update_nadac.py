"""Download the newest CMS NADAC file and save the latest price per NDC to data/nadac.json.

Runs weekly from GitHub Actions. No third-party packages.
"""
import csv, io, json, os, re, sys, urllib.request
from datetime import date, datetime

DATASET_ID_2026 = "fbb83258-11c7-47f5-8b18-5f8e79f7e704"
META = "https://data.medicaid.gov/api/1/metastore/schemas/dataset/items"
OUT = os.path.join(os.path.dirname(__file__), "..", "data", "nadac.json")
UA = {"User-Agent": "PharmacyProfitFinder-NADAC-updater"}


def get(url, timeout=120):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def csv_urls(obj):
    """Find every .csv download link anywhere inside a dataset's metadata."""
    found = []
    if isinstance(obj, dict):
        for v in obj.values():
            found += csv_urls(v)
    elif isinstance(obj, list):
        for v in obj:
            found += csv_urls(v)
    elif isinstance(obj, str) and obj.lower().endswith(".csv") and obj.startswith("http"):
        found.append(obj)
    return found


def find_dataset():
    """Return (title, csv_url) for the newest yearly NADAC dataset."""
    try:
        items = json.loads(get(META))
        best = None
        for it in items:
            t = str(it.get("title", ""))
            m = re.fullmatch(r"NADAC \(National Average Drug Acquisition Cost\) (\d{4})", t.strip())
            if m and (best is None or int(m.group(1)) > best[0]):
                best = (int(m.group(1)), it)
        if best:
            urls = csv_urls(best[1])
            if urls:
                return best[1]["title"], sorted(urls)[-1]
    except Exception as e:
        print("Catalog lookup failed, falling back to 2026 dataset:", e)
    it = json.loads(get(f"{META}/{DATASET_ID_2026}"))
    urls = csv_urls(it)
    if not urls:
        sys.exit("No CSV link found for the NADAC dataset.")
    return it.get("title", "NADAC 2026"), sorted(urls)[-1]


def norm_ndc(s):
    d = re.sub(r"\D", "", str(s or ""))
    return d.zfill(11)[:11] if d else ""


def parse_date(s):
    s = str(s or "").strip()
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%m/%d/%y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s[:19] if "T" in s else s, fmt).date()
        except ValueError:
            pass
    return None


def col(headers, *names):
    low = {h.strip().lower(): h for h in headers}
    for n in names:
        if n in low:
            return low[n]
    return None


def build(text):
    rdr = csv.DictReader(io.StringIO(text))
    h = rdr.fieldnames or []
    c = {k: col(h, *v) for k, v in {
        "ndc": ("ndc",), "desc": ("ndc description",), "unit": ("nadac per unit", "nadac_per_unit"),
        "eff": ("effective date",), "pu": ("pricing unit",), "asof": ("as of date",)}.items()}
    if not c["ndc"] or not c["unit"]:
        sys.exit(f"Unexpected NADAC columns: {h}")
    latest, as_of_max = {}, None
    for r in rdr:
        ndc = norm_ndc(r[c["ndc"]])
        try:
            unit = float(str(r[c["unit"]]).replace("$", "").replace(",", ""))
        except ValueError:
            continue
        if not ndc:
            continue
        asof = parse_date(r.get(c["asof"])) if c["asof"] else None
        eff = parse_date(r.get(c["eff"])) if c["eff"] else None
        key = (asof or date.min, eff or date.min)
        if ndc not in latest or key >= latest[ndc][0]:
            latest[ndc] = (key, unit, (r.get(c["desc"]) or "").strip() if c["desc"] else "",
                           (r.get(c["pu"]) or "").strip() if c["pu"] else "", eff)
        if asof and (as_of_max is None or asof > as_of_max):
            as_of_max = asof
    return latest, as_of_max


def main():
    title, url = find_dataset()
    print("Dataset:", title, "\nDownloading:", url)
    text = get(url, timeout=600).decode("utf-8-sig", errors="replace")
    latest, as_of = build(text)
    print(f"{len(latest):,} NDCs, as of {as_of}")

    prev, old = {}, {}
    if os.path.exists(OUT):
        try:
            old = json.load(open(OUT))
            prev = {r[0]: r[1] for r in old.get("rows", [])}
        except Exception:
            old = {}
    prev_as_of = old.get("asOf")
    new_as_of = as_of.isoformat() if as_of else None

    rows, changes = [], []
    for ndc, (_, unit, desc, pu, eff) in sorted(latest.items()):
        rows.append([ndc, round(unit, 5), desc, pu, eff.isoformat() if eff else ""])
        old = prev.get(ndc)
        if old and old > 0 and abs(unit - old) / old >= 0.01:
            changes.append([ndc, old, round(unit, 5)])

    since = prev_as_of
    if prev_as_of and prev_as_of == new_as_of:
        # Same CMS week as last run: keep last week's change list instead of wiping it
        print("No new NADAC week since last run.")
        changes, since = old.get("changes", []), old.get("changesSince")
    out = {"source": url, "dataset": title, "asOf": new_as_of,
           "updated": date.today().isoformat(), "count": len(rows),
           "changesSince": since, "changes": changes, "rows": rows}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print(f"Wrote {OUT} ({os.path.getsize(OUT)/1e6:.1f} MB), {len(changes)} price changes")


if __name__ == "__main__":
    main()
