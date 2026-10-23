"""lit_<n>_*.md의 문헌 표에서 DOI를 뽑아 refs_<n>_*.tsv에 없는 행을 더한다.

- 표 머리글이 "| # | 저자(연도) | 제목 | 학술지 ... | DOI | ... | 확인 수준 |" 꼴인 표만 읽는다.
- 기존 TSV 행은 그대로 둔다(같은 DOI가 있으면 건너뜀).
- 사용: python3 docs/research/sync_refs.py 2 4 6   (주제 번호)
"""
import glob
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DOI_RE = re.compile(r"10\.\d{4,9}/[^\s|,;]+")


def cells(line):
    parts = [c.strip() for c in line.strip().strip("|").split("|")]
    return parts


def parse_md(path):
    rows, head = [], None
    for line in open(path, encoding="utf-8"):
        if not line.startswith("|"):
            head = None if not line.strip() else head
            continue
        c = cells(line)
        if c and c[0] == "#" and any("DOI" in x for x in c):
            head = c
            continue
        if head is None or set("".join(c)) <= set("-: "):
            continue
        rec = dict(zip(head, c + [""] * (len(head) - len(c))))
        rows.append(rec)
    return rows


def main(topics):
    for t in topics:
        mds = glob.glob(os.path.join(HERE, f"lit_{t}_*.md"))
        if not mds:
            print(f"주제 {t}: md 없음")
            continue
        md = mds[0]
        slug = os.path.basename(md)[4:-3]
        tsv = os.path.join(HERE, f"refs_{slug}.tsv")
        have = set()
        lines = []
        if os.path.exists(tsv):
            lines = open(tsv, encoding="utf-8").read().splitlines()
            for ln in lines[1:]:
                d = ln.split("\t")[0].strip().lower()
                if d:
                    have.add(d)
        else:
            lines = ["doi\tfirst_author\tyear\tshort_title\tlevel\tnote"]
        added = 0
        for r in parse_md(md):
            doi_cell = next((v for k, v in r.items() if "DOI" in k), "")
            m = DOI_RE.search(doi_cell)
            if not m:
                continue
            doi = m.group(0).rstrip(".)]").lower()
            if doi in have:
                continue
            au = next((v for k, v in r.items() if "저자" in k), "")
            ym = re.search(r"\((\d{4})", au)
            first = re.split(r"[,(&]| et al", au)[0].strip()
            title = next((v for k, v in r.items() if k.startswith("제목")), "")[:140]
            level = next((v for k, v in r.items() if "확인" in k), "").split(" ")[0]
            journal = next((v for k, v in r.items() if "학술지" in k), "")
            note = f"{journal}; md 표에서 추가({os.path.basename(md)} #{r.get('#', '')})"
            lines.append("\t".join(x.replace("\t", " ") for x in
                                   [doi, first, ym.group(1) if ym else "", title, level, note]))
            have.add(doi)
            added += 1
        open(tsv, "w", encoding="utf-8").write("\n".join(lines) + "\n")
        print(f"주제 {t}: {os.path.basename(tsv)} +{added}행 (총 {len(lines) - 1})")


if __name__ == "__main__":
    main(sys.argv[1:])
