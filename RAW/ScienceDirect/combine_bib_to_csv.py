from __future__ import annotations

import csv
import re
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
COMBINED_BIB_NAME = "sciencedirect_combined.bib"
FULL_CSV_NAME = "sciencedirect_all_columns.csv"
FILTERED_CSV_NAME = "sciencedirect_selected_columns.csv"

TARGET_COLUMNS = [
	"search_index",
	"Selected",
	"Title",
	"abstract",
	"Authors",
	"Year",
	"index_keywords",
	"Author Keywords",
	"Publisher",
	"DOI",
	"Link",
	"Document Type",
]


def find_bib_files(base_dir: Path) -> list[Path]:
	bib_files = sorted(
		p
		for p in base_dir.glob("*.bib")
		if p.name.lower() != COMBINED_BIB_NAME.lower()
	)
	return bib_files


def combine_bib_files(bib_files: list[Path], output_path: Path) -> None:
	with output_path.open("w", encoding="utf-8") as out:
		for index, bib_path in enumerate(bib_files):
			if index > 0:
				out.write("\n\n")
			out.write(bib_path.read_text(encoding="utf-8", errors="ignore").strip())


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

		entry_type = m.group(1).strip()
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
			"entry_type": entry_type,
			"citation_key": citation_key,
		}

		for field_line in parts[1:]:
			if "=" not in field_line:
				continue
			k, v = field_line.split("=", 1)
			key = k.strip().lower()
			value = strip_wrapping(v)
			fields[key] = value

		entries.append(fields)

	return entries


def normalize_authors(author_field: str) -> str:
	if not author_field:
		return ""

	authors = [a.strip() for a in re.split(r"\s+and\s+", author_field) if a.strip()]
	normalized: list[str] = []

	for author in authors:
		if "," in author:
			last, first = [p.strip() for p in author.split(",", 1)]
			normalized.append(f"{first} {last}".strip())
		else:
			normalized.append(author)

	return "; ".join(normalized)


def to_target_row(entry: dict[str, str]) -> dict[str, str]:
	title = entry.get("title", "")
	abstract = entry.get("abstract", "")
	authors = normalize_authors(entry.get("author", ""))
	year = entry.get("year", "")

	index_keywords = (
		entry.get("index_keywords", "")
		or entry.get("indexterms", "")
		or entry.get("index terms", "")
	)
	author_keywords = entry.get("author_keywords", "") or entry.get("keywords", "")

	publisher = (
		entry.get("publisher", "")
		or entry.get("journal", "")
		or entry.get("booktitle", "")
	)

	doi = entry.get("doi", "")
	link = entry.get("url", "")
	document_type = entry.get("document_type", "") or entry.get("entry_type", "")

	return {
		"search_index": "ScienceDirect",
		"Selected": "",
		"Title": title,
		"abstract": abstract,
		"Authors": authors,
		"Year": year,
		"index_keywords": index_keywords,
		"Author Keywords": author_keywords,
		"Publisher": publisher,
		"DOI": doi,
		"Link": link,
		"Document Type": document_type,
	}


def write_full_csv(entries: list[dict[str, str]], output_path: Path) -> list[str]:
	all_keys = sorted({k for e in entries for k in e.keys()})
	with output_path.open("w", newline="", encoding="utf-8") as f:
		writer = csv.DictWriter(f, fieldnames=all_keys)
		writer.writeheader()
		writer.writerows(entries)
	return all_keys


def write_filtered_csv(rows: list[dict[str, str]], output_path: Path) -> None:
	with output_path.open("w", newline="", encoding="utf-8") as f:
		writer = csv.DictWriter(f, fieldnames=TARGET_COLUMNS)
		writer.writeheader()
		writer.writerows(rows)


def main() -> None:
	bib_files = find_bib_files(BASE_DIR)
	if not bib_files:
		raise FileNotFoundError("No .bib files found in this folder.")

	combined_bib_path = BASE_DIR / COMBINED_BIB_NAME
	full_csv_path = BASE_DIR / FULL_CSV_NAME
	filtered_csv_path = BASE_DIR / FILTERED_CSV_NAME

	combine_bib_files(bib_files, combined_bib_path)
	combined_text = combined_bib_path.read_text(encoding="utf-8", errors="ignore")
	entries = parse_bib_entries(combined_text)

	if not entries:
		raise ValueError("No BibTeX entries could be parsed from the combined file.")

	write_full_csv(entries, full_csv_path)
	target_rows = [to_target_row(entry) for entry in entries]
	write_filtered_csv(target_rows, filtered_csv_path)

	print(f"Combined .bib file saved: {combined_bib_path.name}")
	print(f"Full CSV saved: {full_csv_path.name}")
	print(f"Filtered CSV saved: {filtered_csv_path.name}")
	print(f"Entries processed: {len(entries)}")


if __name__ == "__main__":
	main()
