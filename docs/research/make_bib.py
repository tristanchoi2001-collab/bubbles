"""refs_*.tsv의 DOI를 Crossref로 다시 대조하고 docs/refs_microgap.bib를 만든다.

쓰는 것: Crossref 공개 API(무료, 키 없음, mailto 없음). 요청 사이 0.35 s 쉰다.
응답은 --cache 파일에 저장해 다시 묻지 않는다.

대조 규칙
- OK   : DOI가 Crossref에 있고 첫 저자 성과 연도(±1)가 TSV와 맞는다.
- WARN : DOI는 있지만 저자 또는 연도가 다르다 → bib note에 적는다.
- FAIL : DOI가 Crossref에 없다 / DOI 없음 → bib 끝의 "미대조" 절에 @misc로 둔다.

사용: python3 docs/research/make_bib.py [--cache PATH] [--out docs/refs_microgap.bib]
"""
import argparse
import glob
import html
import json
import os
import re
import sys
import tempfile
import time
import unicodedata
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
UA = "bubbles-research/0.1 (literature check; no contact address)"

# 사람이 확인한 예외: DOI가 맞지만 Crossref 서지(연도·저자)가 TSV와 다른 이유가 분명한 것
ACCEPT = {
    "10.1615/0-8493-9925-4.70": "Crossref 연도 2023은 Begell 디지털화 연도. 학회 발표는 1988-07",
    "10.2172/60784": "OSTI 보고서라 Crossref 저자가 기관(LBL). 실제 저자 Zimmerman & Bodvarsson",
    "10.1103/pm4m-18nt": "PRF 2026 게재 예정판이라 Crossref 저자가 'Anonymous'. 제목·학술지는 일치. 저자는 미확인(arXiv 1910.04327로 추정)",
    "10.2172/10180933": "OSTI 보고서라 Crossref 저자가 기관(Purdue Univ.). 개인 저자는 미확인(점검 에이전트 I1 근거, 원문 미확인)",
}


def fold(s):
    s = unicodedata.normalize("NFKD", s or "")
    return "".join(c for c in s if not unicodedata.combining(c)).lower()


def norm_doi(d):
    d = (d or "").strip()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d, flags=re.I)
    return d.lower() if d.startswith("10.") else ""


def fetch(doi, cache):
    if doi in cache:
        return cache[doi]
    url = "https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/()")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    msg = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=40) as r:
                msg = json.load(r)["message"]
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                msg = {"_error": 404}
                break
            time.sleep(2 + 3 * attempt)
        except Exception:
            time.sleep(2 + 3 * attempt)
    time.sleep(0.35)
    if msg is None:
        return None  # 네트워크 실패는 캐시하지 않는다
    cache[doi] = msg
    return msg


def year_of(m):
    for k in ("published-print", "published-online", "issued", "created"):
        dp = (m.get(k) or {}).get("date-parts") or [[None]]
        if dp and dp[0] and dp[0][0]:
            return int(dp[0][0])
    return None


def clean(s):
    s = html.unescape(re.sub(r"<[^>]+>", "", s or ""))
    return re.sub(r"\s+", " ", s).strip()


def tex(s):
    s = clean(s)
    rep = {"\\": r"\textbackslash{}", "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
           "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}", "^": r"\^{}"}
    return "".join(rep.get(c, c) for c in s)


TYPE = {"journal-article": "article", "proceedings-article": "inproceedings", "book": "book",
        "monograph": "book", "edited-book": "book", "book-chapter": "incollection",
        "report": "techreport", "dissertation": "phdthesis", "posted-content": "misc"}


def make_key(m, used):
    a = (m.get("author") or [{}])[0]
    fam = fold(a.get("family") or a.get("name") or "anon")
    fam = re.sub(r"[^a-z]", "", fam) or "anon"
    y = year_of(m) or 0
    words = [w for w in re.findall(r"[a-z]+", fold(clean((m.get("title") or [""])[0])))
             if w not in {"a", "an", "the", "on", "of", "in", "for", "and", "to", "with"}]
    base = f"{fam}{y}{words[0] if words else ''}"
    key, i = base, 0
    while key in used:
        i += 1
        key = base + "abcdefghijklmnopqrstuvwxyz"[i - 1]
    used.add(key)
    return key


def bib_entry(m, key, note):
    typ = TYPE.get(m.get("type"), "misc")
    f = []
    authors = []
    for a in m.get("author") or []:
        if a.get("family"):
            authors.append(f"{a['family']}, {a.get('given', '')}".strip().rstrip(","))
        elif a.get("name"):
            authors.append("{" + a["name"] + "}")
    if authors:
        f.append(("author", " and ".join(tex(x) if not x.startswith("{") else x for x in authors)))
    f.append(("title", "{" + tex((m.get("title") or [""])[0]) + "}"))
    ct = clean((m.get("container-title") or [""])[0])
    if typ == "article" and ct:
        f.append(("journal", tex(ct)))
    elif typ in ("inproceedings", "incollection") and ct:
        f.append(("booktitle", tex(ct)))
    for k_src, k_bib in (("volume", "volume"), ("issue", "number"), ("page", "pages")):
        if m.get(k_src):
            v = str(m[k_src]).replace("-", "--") if k_bib == "pages" else str(m[k_src])
            f.append((k_bib, tex(v)))
    if typ in ("book", "incollection", "techreport") and m.get("publisher"):
        f.append(("publisher", tex(m["publisher"])))
    if year_of(m):
        f.append(("year", str(year_of(m))))
    f.append(("doi", m.get("DOI", "")))
    f.append(("note", note))
    body = ",\n".join(f"  {k} = {{{v}}}" for k, v in f)  # 제목은 {{...}}로 대소문자 유지
    return f"@{typ}{{{key},\n{body}\n}}\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", default=os.path.join(tempfile.gettempdir(), "bubbles_crossref_cache.json"))
    ap.add_argument("--out", default=os.path.join(ROOT, "docs", "refs_microgap.bib"))
    ap.add_argument("--check", default=os.path.join(HERE, "refs_check.tsv"))
    args = ap.parse_args()
    cache = {}
    if os.path.exists(args.cache):
        cache = json.load(open(args.cache, encoding="utf-8"))

    rows = []
    for path in sorted(glob.glob(os.path.join(HERE, "refs_*.tsv"))):
        topic = os.path.basename(path)[5:-4]
        lines = open(path, encoding="utf-8").read().splitlines()
        if not lines:
            continue
        head = [h.strip() for h in lines[0].split("\t")]
        for ln in lines[1:]:
            if not ln.strip():
                continue
            parts = ln.split("\t")
            r = dict(zip(head, parts + [""] * (len(head) - len(parts))))
            r["topic"] = topic
            rows.append(r)

    by_doi, nodoi = {}, []
    for r in rows:
        d = norm_doi(r.get("doi"))
        if d:
            by_doi.setdefault(d, []).append(r)
        else:
            nodoi.append(r)

    used, ok_entries, warn_entries, fail_entries, check = set(), [], [], [], []
    for d in sorted(by_doi):
        rs = by_doi[d]
        m = fetch(d, cache)
        topics = ",".join(sorted({r["topic"] for r in rs}))
        levels = ",".join(sorted({r.get("level", "").strip() for r in rs if r.get("level")}))
        if m is None or m.get("_error"):
            st = "FAIL" if m is not None else "NETFAIL"
            check.append([d, st, "", "", "", "", topics])
            fail_entries.append((d, rs, st))
            continue
        cfa = fold((m.get("author") or [{}])[0].get("family") or (m.get("author") or [{}])[0].get("name") or "")
        cy = year_of(m)
        probs = []
        for r in rs:
            fa = fold(r.get("first_author", "")).split()[0] if r.get("first_author") else ""
            if fa and cfa and fa not in cfa and cfa not in fa:
                probs.append(f"저자 {r.get('first_author')}≠{cfa}")
            try:
                ty = int(str(r.get("year", "")).strip()[:4])
                if cy and abs(ty - cy) > 1:
                    probs.append(f"연도 {ty}≠{cy}")
            except ValueError:
                pass
        probs = sorted(set(probs))
        if probs and d in ACCEPT:
            probs = []
            levels = (levels + "; " if levels else "") + "확인된 예외: " + ACCEPT[d]
        st = "OK" if not probs else "WARN"
        title = clean((m.get("title") or [""])[0])
        check.append([d, st, cfa, str(cy or ""), title[:120],
                      clean((m.get("container-title") or [""])[0]), topics + (" | " + "; ".join(probs) if probs else "")])
        key = make_key(m, used)
        note = f"Crossref 대조 2026-10; 확인 수준 {levels or '?'}; 주제 {topics}"
        if probs:
            note += "; 확인 필요: " + "; ".join(probs)
        (ok_entries if st == "OK" else warn_entries).append(bib_entry(m, key, tex(note)))

    json.dump(cache, open(args.cache, "w", encoding="utf-8"), ensure_ascii=False)

    out = ["% docs/refs_microgap.bib — docs/research/make_bib.py가 Crossref 메타데이터로 생성. 직접 고치지 말고 refs_*.tsv를 고친 뒤 다시 만든다.",
           f"% OK {len(ok_entries)}건, WARN(서지 불일치 확인 필요) {len(warn_entries)}건, 미대조 {len(fail_entries) + len(nodoi)}건", ""]
    out += ok_entries
    if warn_entries:
        out += ["", "% ===== WARN: DOI는 Crossref에 있으나 TSV의 저자·연도와 다름 (note 확인) =====", ""] + warn_entries
    if fail_entries or nodoi:
        out += ["", "% ===== 미대조: Crossref로 확인하지 못함. 인용 전에 원문으로 확인할 것 =====", ""]
        for d, rs, st in fail_entries:
            r = rs[0]
            k = re.sub(r"[^a-z]", "", fold(r.get("first_author", "anon"))) + str(r.get("year", ""))[:4] + "unverified"
            out.append(f"@misc{{{k},\n  title = {{{tex(r.get('short_title', ''))}}},\n  author = {{{tex(r.get('first_author', ''))}}},\n"
                       f"  year = {{{str(r.get('year', ''))[:4]}}},\n  doi = {{{d}}},\n  note = {{Crossref 미대조({st}); {tex(r.get('note', ''))}}}\n}}\n")
        for r in nodoi:
            k = re.sub(r"[^a-z]", "", fold(r.get("first_author", "anon"))) + str(r.get("year", ""))[:4] + "nodoi"
            out.append(f"@misc{{{k},\n  title = {{{tex(r.get('short_title', ''))}}},\n  author = {{{tex(r.get('first_author', ''))}}},\n"
                       f"  year = {{{str(r.get('year', ''))[:4]}}},\n  note = {{DOI 없음, Crossref 미대조; {tex(r.get('note', ''))}}}\n}}\n")
    open(args.out, "w", encoding="utf-8").write("\n".join(out))
    with open(args.check, "w", encoding="utf-8") as fh:
        fh.write("doi\tstatus\tcrossref_first_author\tcrossref_year\tcrossref_title\tjournal\ttopics_and_problems\n")
        for c in check:
            fh.write("\t".join(x.replace("\t", " ") for x in c) + "\n")
    n_ok = sum(1 for c in check if c[1] == "OK")
    print(f"DOI {len(by_doi)}개: OK {n_ok}, WARN {sum(1 for c in check if c[1] == 'WARN')}, "
          f"FAIL {sum(1 for c in check if c[1] == 'FAIL')}, NETFAIL {sum(1 for c in check if c[1] == 'NETFAIL')}; DOI 없음 {len(nodoi)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
