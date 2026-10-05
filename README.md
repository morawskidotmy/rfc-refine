# RFC Refine (`rfc-refine`)

> **Comprehensive engineering guide and automation toolkit for discovering, retrieving, implementing, and iteratively refining software systems against official IETF Request for Comments (RFC) standards.**

---

## Overview

Implementing protocol specifications correctly requires rigorous attention to document lifecycles, normative semantics, and conformance validation. **RFC Refine** provides a structured methodology and CLI utility (`rfc_tool.py`) to streamline working with specifications from [rfc-editor.org](https://www.rfc-editor.org/) and the [IETF Datatracker](https://datatracker.ietf.org/).

---

## Key Features

- **Lifecycle Hygiene**: Automatically check document status (Standards Track, Informational, Experimental), detect whether an RFC has been **Obsoleted** or **Updated**, and review official **Errata**.
- **Normative Keyword Extraction**: Parse and filter RFCs for RFC 2119 / RFC 8174 normative requirements (`MUST`, `MUST NOT`, `SHOULD`, `MAY`) with section and line numbers.
- **ABNF Grammar Parsing**: Isolate and extract Augmented Backus-Naur Form grammar definitions (RFC 5234 / RFC 7405) for protocol wire implementation.
- **Conformance Matrix Generation**: Instantly bootstrap Markdown compliance checklists and audit trackers for any RFC.
- **Multi-Format Caching**: Retrieve and cache canonical TXT, HTML, and RFCXML formats locally.

---

## CLI Reference (`rfc_tool.py`)

The toolkit includes a standalone Python utility located at `scripts/rfc_tool.py`.

### 1. Fetching & Caching RFCs
Download and cache an RFC document locally in `~/.cache/rfcs/`:
```bash
python3 scripts/rfc_tool.py get 9110
```

### 2. Searching RFCs
Search RFC titles and metadata via the IETF Datatracker API:
```bash
python3 scripts/rfc_tool.py search "websocket"
```

### 3. Inspecting Metadata & Lifecycle Status
Check standard maturity level, obsoleted/updated relationships, and verified errata counts:
```bash
python3 scripts/rfc_tool.py info 9110
```

### 4. Extracting Normative Requirements
Extract specific requirement levels (`MUST`, `SHOULD`, etc.) with section annotations:
```bash
python3 scripts/rfc_tool.py normative 9110 --level MUST
```

### 5. Extracting ABNF Grammars
Isolate formal syntax definitions for protocol parsers:
```bash
python3 scripts/rfc_tool.py abnf 5234
```

### 6. Generating Conformance Checklists
Generate a structured Markdown compliance checklist for test-driven implementation:
```bash
python3 scripts/rfc_tool.py matrix 9110 --limit 30
```

---

## Engineering Workflow

### Phase 1: Grounding & Lifecycle Check
> [!IMPORTANT]
> Never implement an obsolete standard in greenfield development. Always verify that the RFC has not been superseded (e.g., HTTP/1.1 RFC 2616 $\rightarrow$ RFC 7230 $\rightarrow$ RFC 9110).

1. **Verify Status**: Check if the document is an Internet Standard, Proposed Standard, BCP, or Informational.
2. **Check Obsoleted/Updated**: Inspect header metadata for replacement references.
3. **Review Errata**: Ensure verified technical corrections are integrated into your implementation design.

### Phase 2: Normative Strictness
- **`MUST` / `REQUIRED` / `SHALL`**: Treat as strict validation invariants and uncompromised error boundaries.
- **`MUST NOT` / `SHOULD NOT`**: Enforce defensive rejection guards with clear protocol error codes.
- **`SHOULD` / `RECOMMENDED`**: Implement as default behavior; document architectural divergences if necessary.

### Phase 3: Iterative Conformance Refinement
- Validate message parsers against extracted ABNF rules using zero-copy byte slices.
- Test against edge cases, malformed framing, and state machine transitions.
- Track implementation progress using generated conformance matrices.

---

## Included Resources

- **`SKILL.md`**: Complete agent skill definition and prompt guide.
- **`references/normative-keywords.md`**: Detailed mapping of RFC 2119 keywords to engineering patterns.
- **`references/refinement-checklist.md`**: Step-by-step conformance audit checklist.
- **`scripts/rfc_tool.py`**: Standalone Python CLI automation tool.
