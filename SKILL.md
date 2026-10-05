---
name: rfc-refine
description: Search, retrieve, implement, and iteratively refine implementations against IETF RFC standards from rfc-editor.org. Covers RFC lifecycle/status, fetching formats (txt, html, xml), normative keyword interpretation (RFC 2119/8174), ABNF grammar extraction, wire protocol parsing, state machines, errata checking, and conformance test refinement loops.
---

# RFC Refine (`rfc-refine`)

A comprehensive engineering guide and workflow for discovering, retrieving, implementing, and iteratively refining software systems against official **IETF Request for Comments (RFC)** standards published at [rfc-editor.org](https://www.rfc-editor.org/) and tracked via [datatracker.ietf.org](https://datatracker.ietf.org/).

---

## Core Philosophy

Standard specifications are contractual, inter-vendor promises. RFC implementations succeed or fail on three pillars:

1. **Document Grounding & Lifecycle Hygiene**:
   Never implement an RFC without verifying its current status (Standard vs Informational), whether it has been **Obsoleted** or **Updated**, and whether active **Errata** exist.
2. **Normative Strictness**:
   RFC specifications use formal requirement levels (RFC 2119 / RFC 8174: `MUST`, `SHOULD`, `MAY`). Every `MUST` is an architectural invariant; every `MUST NOT` is a security or protocol boundary.
3. **Iterative Refinement Against Conformance**:
   Compliance is achieved through systematic refinement loops: syntax validation -> state machine transitions -> interop test suites -> security/errata hardening.

---

## Quick Reference: CLI Tool (`rfc_tool.py`)

A standalone helper utility is bundled in this skill at `scripts/rfc_tool.py`:

```bash
# Fetch and cache RFC locally in ~/.cache/rfcs/ (supports txt, html, xml)
python3 ~/.agents/skills/rfc-refine/scripts/rfc_tool.py get 9110

# Search RFCs by title / keywords via datatracker API
python3 ~/.agents/skills/rfc-refine/scripts/rfc_tool.py search "websocket"

# Check RFC metadata, standard level, obsoleted/updated status, and errata count
python3 ~/.agents/skills/rfc-refine/scripts/rfc_tool.py info 9110

# Extract normative statements (MUST, SHOULD, etc.) with section and line numbers
python3 ~/.agents/skills/rfc-refine/scripts/rfc_tool.py normative 9110 --level MUST

# Extract ABNF grammar definitions
python3 ~/.agents/skills/rfc-refine/scripts/rfc_tool.py abnf 5234

# Generate a Markdown Conformance Matrix starter checklist
python3 ~/.agents/skills/rfc-refine/scripts/rfc_tool.py matrix 9110 --limit 30
```

---

## Phase 1: Searching and Retrieving RFCs

### 1. Authoritative Sources

| Resource | URL | Best For |
| :--- | :--- | :--- |
| **RFC Editor** | `https://www.rfc-editor.org/` | Official repository, canonical text/html/xml, official Errata system |
| **IETF Datatracker** | `https://datatracker.ietf.org/` | Document history, working group context, active drafts, metadata API |
| **RFC Search Engine** | `https://www.rfc-editor.org/search/rfc_search_detail.php` | Detailed multi-criteria search (status, stream, WG, author) |

### 2. Direct Retrieval URLs

For any RFC number `XXXX` (e.g., 9110, 6455, 7540):

- **Plain Text (Canonical Reference)**:
  ```
  https://www.rfc-editor.org/rfc/rfcXXXX.txt
  ```
- **HTML (Rendered with Section Anchors & Deep Links)**:
  ```
  https://www.rfc-editor.org/rfc/rfcXXXX.html
  ```
- **XML (RFCXML v3 / v2 Source)**:
  ```
  https://www.rfc-editor.org/rfc/rfcXXXX.xml
  ```
- **PDF (Formally Formatted)**:
  ```
  https://www.rfc-editor.org/rfc/pdfrfc/rfcXXXX.txt.pdf
  ```

### 3. Understanding RFC Maturity Levels

Always check the **Category / Status** in the document header:

- **Standards Track**:
  - `Internet Standard (STD)`: Highest maturity level. Extensively deployed, proven interoperability (e.g. STD 97 = RFC 9110).
  - `Proposed Standard`: Standard track specification with consensus; normative for implementers.
- **Non-Standards Track**:
  - `Best Current Practice (BCP)`: Recommended operational guidelines or administration policies (e.g., BCP 14 = RFC 2119/8174).
  - `Informational`: General information or educational material; does not establish an official standard.
  - `Experimental`: Testing concepts; not intended for production standard compliance unless participating in experiments.
  - `Historic`: Obsolete protocols retired from the standards track.

### 4. The Lifecycle Trap: Obsoletes & Updates

Check the first 40 lines of the RFC or run `rfc_tool.py info <RFC>`:

- **"Obsoleted by: RFC YYYY"**:
  **DO NOT implement an obsoleted RFC for modern greenfield systems.** For example, RFC 2616 (HTTP/1.1) was obsoleted by RFC 7230–7235, which were obsoleted by RFC 9110–9114.
- **"Updates: RFC XXXX"**:
  The new RFC modifies or amends parts of RFC XXXX without replacing the entire document. You must consult both.
- **"Updated by: RFC ZZZZ"**:
  The RFC you are reading has downstream amendments. Check the updating RFC for security patches, deprecations, or syntax corrections.

### 5. Checking Official Errata (Mandatory)

Errata contain corrections verified by IETF stream chairs for mistakes made during editing or publication:

- **Errata URL**: `https://www.rfc-editor.org/errata/rfcXXXX` or search at `https://www.rfc-editor.org/errata_search.php?rfc=XXXX`
- **Status Types**:
  - `Verified`: Formally approved technical or editorial fix. **You must implement the verified correction.**
  - `Reported`: Under review. Read to understand potential ambiguities or bugs in the specification text.
  - `Rejected`: Clarification that the specification text is intentional as written.
  - `Held for Document Update`: Acknowledged issue, scheduled to be fixed in the next revision of the RFC.

---

## Phase 2: Implementing RFCs

### 1. Decoding Normative Keywords (RFC 2119 & RFC 8174)

Normative keywords are **only binding when capitalized** (RFC 8174):

- **`MUST` / `REQUIRED` / `SHALL`**:
  - *Engineering translation*: Strict validation invariants, non-optional struct fields, explicit error returns, hard connection termination on protocol errors.
  - *Testing*: Dedicated positive unit and integration tests.
- **`MUST NOT` / `SHALL NOT`**:
  - *Engineering translation*: Boundary guards, input sanitizers, protocol violation flags (e.g. closing with code `1002 Protocol Error`).
  - *Testing*: Negative test cases verifying malformed or illegal payloads are rejected cleanly without crashes.
- **`SHOULD` / `RECOMMENDED`**:
  - *Engineering translation*: Default behavior in the implementation. If your application needs to diverge, document the architectural justification in an `RFC_COMPLIANCE.md` file and provide an opt-in/opt-out configuration flag.
- **`SHOULD NOT` / `NOT RECOMMENDED`**:
  - *Engineering translation*: Disabled by default. If allowed for legacy compatibility, require explicit user enablement.
- **`MAY` / `OPTIONAL`**:
  - *Engineering translation*: Pluggable extensions, feature flags. The code must gracefully interoperate with peers regardless of whether the peer implements the feature.

### 2. Parsing ABNF (Augmented BNF - RFC 5234 & RFC 7405)

Most modern internet protocols define message syntax using ABNF:

#### Core ABNF Rules (RFC 5234 Appendix B.1):
```text
ALPHA          =  %x41-5A / %x61-7A   ; A-Z / a-z
DIGIT          =  %x30-39            ; 0-9
HEXDIG         =  DIGIT / "A" / "B" / "C" / "D" / "E" / "F"
CRLF           =  %d13.10            ; Internet standard newline (\r\n)
SP             =  %x20               ; Space
HTAB           =  %x09               ; Horizontal tab
WSP            =  SP / HTAB          ; White space
VCHAR          =  %x21-7E            ; Visible (printing) characters
OCTET          =  %x00-FF            ; Any 8-bit byte
```

#### ABNF Operators:
- `1*DIGIT`: One or more digits (like `\d+`).
- `*1rule`: Zero or one occurrence (optional, equivalent to `[ rule ]`).
- `3*5rule`: Between 3 and 5 occurrences.
- `rule1 / rule2`: Alternative (either `rule1` or `rule2`).
- `%s"case-sensitive"`: RFC 7405 explicit case-sensitive string.
- `%i"case-insensitive"`: Default ABNF string literal behavior.

#### Production Parser Guidelines:
1. **Zero-copy slices**: Parse byte slices (`&[u8]`, `[]byte`, `string_view`) rather than allocating new strings for every token.
2. **Defensive bounds**: Always check input slice length before indexing. Guard against off-by-one errors on CRLF delimiters.
3. **Strict rejection of invalid characters**: Reject non-VCHAR characters, unexpected null bytes (`%x00`), and naked CR or LF outside of CRLF sequences.

### 3. Wire Protocols & Binary Framing

When implementing binary RFCs (e.g., DNS RFC 1035, WebSocket RFC 6455, TLS RFC 8446, QUIC RFC 9000):

1. **Network Byte Order (Big-Endian)**:
   - All multi-byte integers in IETF RFCs are **Big-Endian** unless explicitly specified otherwise.
   - Always use explicit conversion functions: `ntohl`/`htonl`, `binary.BigEndian`, `u32::from_be_bytes()`, or `int.from_bytes(b, byteorder='big')`.
2. **Bitmasking & Offsets**:
   - Trace diagrams bit by bit: Bit 0 is the most significant bit (MSB) in network diagrams.
3. **Variable-Length Integers (Varints)**:
   - Watch for custom integer encodings (e.g. QUIC varints where the first 2 bits indicate length: 1, 2, 4, or 8 bytes).
4. **Length Precedence**:
   - Always validate that payload length headers match actual received bytes. Reject frames where payload length exceeds maximum configured buffer sizes *before* reading the payload into memory to prevent Denial of Service.

### 4. State Machines & Protocol Lifecycles

Internet protocols are inherently stateful:

1. **Define Explicit States**:
   Represent protocol states using typed enums (e.g., `State::Connecting`, `State::Open`, `State::Closing`, `State::Closed`).
2. **Strict Transition Matrix**:
   Reject illegal transitions with explicit protocol errors. For example:
   - Receiving a data frame before handshake completion -> immediate connection abort.
   - Receiving a second handshake frame -> protocol violation.
3. **Timers & Deadlines**:
   Every state that waits on network I/O must have a deadline (handshake timeout, idle timeout, ping/pong interval). Never allow a connection state to block indefinitely.

### 5. The Modern Postel's Principle (RFC 9413)

Historically, Postel's Principle stated: *"Be conservative in what you send, and liberal in what you accept"* (RFC 793).

**Modern Standard Practice (RFC 9413):**
- Being "liberal in what you accept" leads to parser differentials, HTTP request smuggling, cache poisoning, and security vulnerabilities.
- **Rule for modern implementations:**
  - **Be conservative in what you send**: Strict adherence to the generation rules.
  - **Be conservative in what you accept**: Reject malformed inputs, illegal header characters, ambiguous lengths, and syntax variations.

### 6. Security Considerations (RFC 3552)

Every modern RFC includes a mandatory "Security Considerations" section. You must audit and implement its requirements:

- **Resource Exhaustion / DoS**: Enforce max limits on request lines, headers, frames, decompression ratios (zip bombs), and concurrent streams.
- **Timing Attacks**: Use constant-time comparison for all HMACs, tokens, authentication tags, and signatures (`crypto/subtle`, `hmac.compare_digest`).
- **Canonicalization**: Normalize paths and names before making security or access-control decisions.
- **Input Sanitization**: Strip or reject control characters, null bytes, and path traversal sequences (`../`).

---

## Phase 3: Refining Implementations Under an RFC

The **RFC Refinement Loop** is an iterative, 4-round engineering process to audit, harden, and achieve verified compliance.

```
       ┌────────────────────────────────────────────────────────┐
       │ Pre-Flight: Status Check, Errata, Conformance Matrix  │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │ Round 1: Syntactic, Framing, and ABNF Parsing          │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │ Round 2: State Machine, Boundary Limits & Error Codes  │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │ Round 3: Interoperability & Golden Conformance Vectors │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │ Round 4: Security (RFC 3552), Errata & Hardening       │
       └───────────────────────────┬────────────────────────────┘
                                   │
                                   ▼
       ┌────────────────────────────────────────────────────────┐
       │ Sign-off: Traceable Annotations & Compliance Report    │
       └────────────────────────────────────────────────────────┘
```

### The 4 Refinement Rounds

#### Round 1: Syntactic & Framing Precision
- **Focus**: Wire serialization, deserialization, ABNF parsing correctness.
- **Actions**:
  1. Extract ABNF rules using `rfc_tool.py abnf <RFC>`.
  2. Implement strict parsers for every grammar token.
  3. Verify byte order, separators (CRLF vs LF), and case-sensitivity handling.
  4. Write unit tests for every valid syntax variant and verify rejection of invalid syntax.

#### Round 2: State Machines, Limits & Error Transitions
- **Focus**: Lifecycle transitions, boundary values, error status propagation.
- **Actions**:
  1. Verify all state transitions. Test out-of-order frames, unexpected packet arrival, and duplicate headers.
  2. Test zero-length, minimum, and maximum boundaries (e.g. 0-byte frame, $2^{16}-1$ byte frame, max header size).
  3. Verify that error conditions emit the exact numeric status code or error frame specified in the RFC (not generic 500 or silent drops).

#### Round 3: Interoperability & Golden Conformance Test Vectors
- **Focus**: Real-world interop and golden vectors.
- **Actions**:
  1. Extract official test vectors from the RFC's Appendices (e.g., sample vectors for HMAC, cryptographic handshakes, wire hex dumps).
  2. Run official or recognized compliance suites if available:
     - WebSocket: Autobahn Testsuite (`wstest`).
     - HTTP/2: `h2spec`.
     - TLS: Google Project Wycheproof.
     - ACME: Boulder / Pebble test environments.
  3. Fuzz test parser entrypoints with mutated inputs.

#### Round 4: Security, Robustness & Errata Hardening
- **Focus**: RFC 3552 security review, verified errata, defensive limits.
- **Actions**:
  1. Audit against every Verified Erratum from `rfc_tool.py info <RFC>`.
  2. Enforce strict allocation caps to prevent out-of-memory DoS.
  3. Constant-time operations for cryptographic checks.
  4. Verify strict rejection of smuggled payloads and ambiguous frames.

---

## Traceability & Documentation Standards

Every RFC implementation should maintain clear, auditable traceability between the specification and the codebase:

### 1. In-Code Annotations
Directly cite the RFC number, section, and normative requirement above relevant functions:

```python
# RFC 9110 Section 8.8.3: Comparison
# "A weak validator ought not be considered equivalent to an entity-tag
#  validator in an If-Match or If-None-Match condition unless explicitly permitted."
def compare_etags(target: str, candidate: str, strong: bool = True) -> bool:
    if strong:
        # RFC 9110 Section 8.8.3.2: Strong comparison requires exact match
        # and neither validator may be weak (prefixed by 'W/').
        if target.startswith("W/") or candidate.startswith("W/"):
            return False
        return target == candidate
    # Weak comparison (RFC 9110 Section 8.8.3.1)
    return target.removeprefix("W/") == candidate.removeprefix("W/")
```

### 2. Conformance Test Naming
Name tests after the corresponding section:

```go
func TestRFC9110_Section_8_8_3_StrongETagComparison(t *testing.T) { ... }
func TestRFC6455_Section_5_2_MaskKeyEnforcement(t *testing.T) { ... }
```

### 3. Conformance Matrix Table
Generate and maintain a matrix in `RFC_COMPLIANCE.md`:

```markdown
| RFC Section | Requirement Level | Clause Summary | Code Reference | Conformance Status | Test Case |
| :--- | :---: | :--- | :--- | :---: | :--- |
| Section 5.2 | **MUST** | Client frames must be masked | `frame.go:42` | Compliant | `TestMaskEnforcement` |
| Section 5.4 | **MUST NOT** | Control frames must not be fragmented | `parser.go:88` | Compliant | `TestFragmentedControl` |
| Section 7.1 | **SHOULD** | Include descriptive close reason | `conn.go:120` | Compliant | `TestCloseReason` |
```

---

## Associated References & Files

- `scripts/rfc_tool.py`: CLI tool for searching, retrieving, inspecting errata, and generating matrices.
- `references/normative-keywords.md`: Complete guide to RFC 2119 / RFC 8174 keywords, legal/technical interpretations, and code examples.
- `references/refinement-checklist.md`: Printable audit and PR checklist for executing the 4-round refinement protocol.
