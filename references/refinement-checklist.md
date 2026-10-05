# RFC Implementation & Refinement Checklist

Use this checklist to audit an existing implementation or guide iterative refinement rounds when building against an IETF RFC standard.

---

## Pre-Flight: RFC Status & Errata Discovery

- [ ] **Maturity Level Confirmed**: Is this RFC on the Standards Track (Internet Standard STD, Proposed Standard), Best Current Practice (BCP), Informational, or Experimental?
- [ ] **Obsoleted By Check**: Check `https://datatracker.ietf.org/doc/rfcXXXX/` to ensure the RFC has not been obsoleted by a newer specification.
- [ ] **Updates Check**: Identify any companion RFCs listed under "Updated by". Incorporate their amendments into the spec model.
- [ ] **Active Errata Sweep**: Check `https://www.rfc-editor.org/errata/rfcXXXX`.
  - [ ] Review all **Verified** errata (these are consensus fixes for document bugs).
  - [ ] Note any **Reported** errata that address known ambiguities.
- [ ] **Conformance Matrix Initialized**: Run `python3 ~/.agents/skills/rfc-refine/scripts/rfc_tool.py matrix <RFC_NUM>` to generate the requirement checklist.

---

## Round 1: Syntactic & Wire Framing Conformance

- [ ] **ABNF Rules Extraction**: Run `python3 ~/.agents/skills/rfc-refine/scripts/rfc_tool.py abnf <RFC_NUM>`.
- [ ] **Core Grammars Verified**: Check terminal rules (`ALPHA`, `DIGIT`, `CRLF`, `OCTET`, `VCHAR`, `WSP`).
- [ ] **Byte Ordering**: Confirm that binary multi-byte integers are serialized in Network Byte Order (Big-Endian) unless explicitly defined otherwise.
- [ ] **Strict Framing & Delimiters**: Reject trailing garbage, unexpected delimiters, or malformed frame lengths.
- [ ] **Case Sensitivity**: Verify if header fields, scheme names, or keywords are defined as case-insensitive (`%i`) or case-sensitive (`%s`).
- [ ] **Character Encoding**: Ensure UTF-8 decoding rejects invalid byte sequences (e.g. `fatal: true` in decoders, rejecting overlong encodings).

---

## Round 2: State Machines & Boundary Conditions

- [ ] **State Machine Model**: Enumerate all valid protocol states and transitions.
- [ ] **Unexpected Frames / Packets**: Define explicit handling for frames received out of state (e.g., receiving data before handshake completes). Does it terminate or send an error frame?
- [ ] **Zero, Minimum & Maximum Bounds**:
  - [ ] 0-length payloads / empty strings.
  - [ ] Max payload / frame size limits enforced before allocating memory.
  - [ ] Max header size / collection count limits.
  - [ ] Integer overflow / 64-bit counter rollovers.
- [ ] **Timeouts & Keep-Alives**:
  - [ ] Handshake timeout.
  - [ ] Idle connection timeout.
  - [ ] PING/PONG or heartbeat deadlines.
- [ ] **Clean Shutdown / Teardown**:
  - [ ] Half-closed connections handled cleanly.
  - [ ] Error codes propagated accurately on termination.

---

## Round 3: Interoperability & Conformance Test Suites

- [ ] **Golden Vectors from Spec**: Extract test vectors from RFC appendices (e.g., cryptographic keys/ciphertexts, sample HTTP messages, wire trace hex dumps) into unit tests.
- [ ] **Official Test Suites**: Run recognized conformance suites where applicable:
  - WebSocket: Autobahn Testsuite (`wstest`).
  - HTTP/1.1 & HTTP/2: h2spec, h2load, curl test harness.
  - TLS: Project Wycheproof, testssl.sh.
  - ACME: Pebble test server.
  - DNS: ldns, Knot DNS test tools.
  - JOSE / JWT: RFC 7515 / 7516 test vectors.
- [ ] **Negative / Mutation Testing**: Test with intentionally corrupted frames, bitflips, truncated payloads, and incomplete handshakes.
- [ ] **Differential Parsing**: Ensure parsing matches the exact semantics of reference peers to prevent smuggling or mismatch attacks.

---

## Round 4: Security, Robustness & Errata Hardening

- [ ] **RFC 3552 Security Considerations Audit**:
  - [ ] Denial of Service (DoS): Are memory allocations bounded before parsing user-controlled lengths?
  - [ ] Amplification attacks: Are responses bounded when unauthenticated?
  - [ ] Timing attacks: Are sensitive tokens, hashes, or signatures compared with constant-time equality?
  - [ ] Replay protection: Are nonces, timestamps, or sequence numbers validated?
  - [ ] Injection & Smuggling: Are delimiters (CRLF, null bytes, comment markers) strictly sanitized or rejected?
- [ ] **Postel's Law (RFC 9413) Modern Compliance**:
  - Avoid overly generous parsing that forgives syntax errors; verify that malformed protocol elements are strictly rejected.
- [ ] **Code Traceability**:
  - [ ] Every parser branch, error check, and state transition references the exact RFC clause (e.g., `// RFC 9110 Section 6.4.1`).
  - [ ] Test cases are named after the corresponding RFC section and clause.
- [ ] **Conformance Matrix Signed Off**:
  - [ ] All `MUST` / `MUST NOT` requirements are marked **Compliant** with test links.
  - [ ] All `SHOULD` / `SHOULD NOT` requirements are marked **Compliant** or have documented, justified exceptions.
