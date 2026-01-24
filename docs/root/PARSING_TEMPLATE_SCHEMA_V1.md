## ParsingTemplate JSON Schema v1 (backend-compatible)

This schema matches the backend `ParsingTemplate` dataclass (`backend/app/infrastructure/pdf/parsers/template.py`)
and the template store format (`backend/data/templates/{subject}_{name}.json`).

### Top-level

- **name**: string (required)  
  Template identifier, e.g. `ebs_수능특강_literature_2026`
- **subject**: string (required)  
  One of: `literature`, `math1`, `english`
- **version**: string (optional, default `""`)  
  E.g. `2026`
- **description**: string (optional, default `""`)
- **patterns**: object (required)
- **config**: object (required)
- **confidence**: number (optional, default `0.0`)  
  Used as baseline for template matching.
- **sample_texts**: string[] (optional)  
  Usually first TOC lines or early-page sample lines.
- **created_at**: string | null (optional)  
  ISO8601 recommended.
- **updated_at**: string | null (optional)  
  ISO8601 recommended.

### patterns

All regexes must be compatible with Python `re`.

- **lecture_title_patterns**: string[]  
  Used to detect lecture headers in content pages (if needed).
- **toc_lecture_patterns**: string[]  
  The most important field for deterministic lecture list extraction from TOC pages.
- **concept_title_patterns**: string[]
- **content_header_patterns**: string[]
- **section_title_patterns**: string[]
- **problem_number_pattern**: string  
  Regex for problem numbering (e.g. `^\\d+\\.` or `^[①②③④⑤]`).

### config

- **toc_end_page**: number  
  Last TOC page (1-based).
- **start_content_page**: number  
  First content page (1-based).
- **paragraph_y_threshold**: number  
  Used for line/paragraph grouping (pixel space in extractor DPI).

Optional (allowed, ignored by older code if unused):

- **unit_order**: string[]  
  E.g. `["concept","passage","problem"]`  
  Order of units within a lecture. Used by the new master prompt system.  
  Note: Previously documented as `units_order` but implementation uses `unit_order`.
- **region_hints**: object  
  Optional heuristics for page region constraints.  
  Format: `{"concept": {"y_min": 0.05, "y_max": 0.35}, "passage": {...}, "problem": {...}}`  
  Normalized page ratios (0.0-1.0) indicating typical vertical positions of each unit type.  
  Generated from parsing guide regions (bbox annotations) or provided by LLM.

