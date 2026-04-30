from __future__ import annotations

import csv
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
INPUT_BIB = BASE_DIR / "zotero.bib"
OUTPUT_TITLES_CSV = BASE_DIR / "zotero_titles.csv"
OUTPUT_ALL_COLUMNS_CSV = BASE_DIR / "zotero_all_columns_clean.csv"


def split_top_level(text: str, delimiter: str = ",") -> list[str]:
	parts: list[str] = []
	current: list[str] = []
	brace_depth = 0
	quote_open = False
	escape = False

	for ch in text:
		if escape:
			current.append(ch)
			escape = False
			continue

		if ch == "\\":
			current.append(ch)
			escape = True
			continue

		if ch == '"' and brace_depth == 0:
			quote_open = not quote_open
			current.append(ch)
			continue

		if ch == "{" and not quote_open:
			brace_depth += 1
			current.append(ch)
			continue

		if ch == "}" and not quote_open and brace_depth > 0:
			brace_depth -= 1
			current.append(ch)
			continue

		if ch == delimiter and brace_depth == 0 and not quote_open:
			part = "".join(current).strip()
			if part:
				parts.append(part)
			current = []
			continue

		current.append(ch)

	tail = "".join(current).strip()
	if tail:
		parts.append(tail)

	return parts


def strip_wrapping(value: str) -> str:
	value = value.strip().rstrip(",").strip()
	if (value.startswith("{") and value.endswith("}")) or (
		value.startswith('"') and value.endswith('"')
	):
		value = value[1:-1]
	value = re.sub(r"\s+", " ", value).strip()
	return value


def parse_bib_entries(text: str) -> list[dict[str, str]]:
	entries: list[dict[str, str]] = []
	i = 0
	n = len(text)

	while i < n:
		at = text.find("@", i)
		if at == -1:
			break

		m = re.match(r"@\s*([A-Za-z]+)\s*\{", text[at:])
		if not m:
			i = at + 1
			continue

		body_start = at + m.end()

		depth = 1
		j = body_start
		while j < n and depth > 0:
			if text[j] == "{":
				depth += 1
			elif text[j] == "}":
				depth -= 1
			j += 1

		body = text[body_start : j - 1].strip()
		i = j

		if not body:
			continue

		parts = split_top_level(body)
		if not parts:
			continue

		citation_key = parts[0].strip()
		fields: dict[str, str] = {
			"entry_type": m.group(1).strip().lower(),
			"citation_key": citation_key,
		}
		for field_line in parts[1:]:
			if "=" not in field_line:
				continue
			k, v = field_line.split("=", 1)
			key = k.strip().lower()
			fields[key] = strip_wrapping(v)

		entries.append(fields)

	return entries


def write_titles_csv(titles: list[str], output_path: Path) -> None:
	with output_path.open("w", newline="", encoding="utf-8-sig") as f:
		writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
		writer.writerow(["title"])
		for title in titles:
			writer.writerow([title])


def clean_text(value: str) -> str:
	value = re.sub(r"[{}]", "", value)
	value = re.sub(r"\s+", " ", value).strip()
	return value


def write_all_columns_csv(entries: list[dict[str, str]], output_path: Path) -> None:
	fieldnames = sorted({key for entry in entries for key in entry.keys()})
	with output_path.open("w", newline="", encoding="utf-8-sig") as f:
		writer = csv.DictWriter(
			f,
			fieldnames=fieldnames,
			quoting=csv.QUOTE_MINIMAL,
		)
		writer.writeheader()
		for entry in entries:
			cleaned_row = {k: clean_text(v) for k, v in entry.items()}
			writer.writerow(cleaned_row)


def main() -> None:
	if not INPUT_BIB.exists():
		raise FileNotFoundError(f"Input file not found: {INPUT_BIB}")

	text = INPUT_BIB.read_text(encoding="utf-8", errors="ignore")
	entries = parse_bib_entries(text)
	titles = []
	for entry in entries:
		raw_title = entry.get("title", "").strip()
		if not raw_title:
			continue
		clean_title = clean_text(raw_title)
		titles.append(clean_title)

	if not titles:
		raise ValueError("No title fields were found in the BibTeX file.")

	write_titles_csv(titles, OUTPUT_TITLES_CSV)
	write_all_columns_csv(entries, OUTPUT_ALL_COLUMNS_CSV)
	print(f"Saved {len(titles)} titles to: {OUTPUT_TITLES_CSV.name}")
	print(f"Saved {len(entries)} records to: {OUTPUT_ALL_COLUMNS_CSV.name}")


if __name__ == "__main__":
	main()
