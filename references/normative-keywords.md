# RFC Normative Keywords Reference Guide

Based on **RFC 2119** (*Key words for use in RFCs to Indicate Requirement Levels*) and **RFC 8174** (*Ambiguity of Uppercase vs Lowercase in RFC 2119 Key Words*).

---

## 1. The Capitalization Rule (RFC 8174)

Under RFC 8174, RFC 2119 keywords are **only normative when they appear in all uppercase**:
- `MUST`, `MUST NOT`, `REQUIRED`, `SHALL`, `SHALL NOT`, `SHOULD`, `SHOULD NOT`, `RECOMMENDED`, `NOT RECOMMENDED`, `MAY`, `OPTIONAL`.
- Lowercase versions ("must", "should", "may") represent ordinary English prose and do not carry formal protocol compliance obligations unless explicitly stated in historical legacy RFCs prior to RFC 8174.

---

## 2. Normative Level Breakdown & Engineering Translation

| Keyword | Standards Meaning | Code / Architecture Translation | Conformance Test Requirement |
| :--- | :--- | :--- | :--- |
| **MUST** / **REQUIRED** / **SHALL** | Absolute requirement of the specification. Interoperability or correctness is compromised if omitted. | Hard assertions, runtime invariant checks, compulsory message fields, strict validation. Non-compliance results in rejected frames/requests or fatal connection termination. | Mandatory positive tests. Every `MUST` must have at least one test verifying standard behavior. |
| **MUST NOT** / **SHALL NOT** | Absolute prohibition of the specification. Generating or allowing this compromises security, stability, or interoperability. | Boundary checks, sanitizers, rejection filters. Emit explicit RFC-defined error codes (e.g., HTTP `400 Bad Request`, WebSocket `1002 Protocol Error`, QUIC `PROTOCOL_VIOLATION`). | Negative tests. Malformed inputs matching the prohibition must trigger immediate error/rejection without crash or leak. |
| **SHOULD** / **RECOMMENDED** | Strong default. Valid reasons may exist in particular circumstances to ignore, but the full implications must be understood and weighed. | Enabled by default in the implementation. If bypassed or disabled, expose a configuration flag with clear documentation of risks. | Default-path tests plus tests verifying the documented alternative behavior under configuration. |
| **SHOULD NOT** / **NOT RECOMMENDED** | Strong antipattern. Valid reasons may exist to permit this behavior, but the risks and consequences must be weighed. | Blocked or avoided by default. If permitted for backwards compatibility, require an explicit opt-in toggle (e.g., `allow_legacy_unsafe_header_folding=true`). | Tests ensuring that by default the behavior is inhibited, and enabled only when the toggle is active. |
| **MAY** / **OPTIONAL** | Truly optional feature or behavior. An implementation can choose to include or omit without penalty. | Feature flags, pluggable extensions, optional fields. When omitted, the implementation MUST gracefully interoperate with peers that do implement it. | Interop tests: test behavior both when the option is enabled and when disabled. Verify peer tolerance. |

---

## 3. Idiomatic Language Implementations

### Go
```go
// RFC 9110 Section 8.8.1: An entity tag MUST be sent in quotes.
func FormatETag(tag string, weak bool) (string, error) {
    if tag == "" {
        return "", ErrInvalidETag // Enforce MUST
    }
    prefix := ""
    if weak {
        prefix = "W/"
    }
    return fmt.Sprintf("%s\"%s\"", prefix, tag), nil
}

// RFC 9110 Section 5.6.2: A sender MUST NOT generate a Transfer-Encoding header
// field in any request with a method that does not allow a message body.
func ValidateHeaders(method string, h http.Header) error {
    if (method == http.MethodGet || method == http.MethodHead) && h.Get("Transfer-Encoding") != "" {
        return ErrIllegalTransferEncoding // Reject prohibited framing
    }
    return nil
}
```

### Rust
```rust
// RFC 6455 Section 5.2: A client MUST mask all frames that it sends to the server.
// A server MUST close the connection upon receiving an unmasked frame (code 1002).
pub fn process_incoming_frame(frame: &Frame, is_server: bool) -> Result<(), ProtocolError> {
    if is_server && !frame.is_masked() {
        // RFC 6455 Section 5.1: Close code 1002 (Protocol error)
        return Err(ProtocolError::CloseConnection {
            code: 1002,
            reason: "Client frame must be masked",
        });
    }
    Ok(())
}
```

### Python
```python
# RFC 7230 Section 3.2.4: A recipient MUST NOT accept CRLF within a header field-name.
def parse_header_line(line: bytes) -> tuple[str, str]:
    if b"\r" in line or b"\n" in line:
        raise ProtocolViolation("CRLF injection detected in header line")
    # ...
```

### TypeScript
```typescript
// RFC 8259 Section 8.1: JSON text exchanged between systems MUST be encoded using UTF-8.
export function decodeJsonPayload(buffer: Uint8Array): unknown {
  const decoder = new TextDecoder("utf-8", { fatal: true }); // fatal: true rejects invalid UTF-8
  const text = decoder.decode(buffer);
  return JSON.parse(text);
}
```

---

## 4. Tracking Divergences & Intentional Non-Compliance

In rare scenarios, real-world constraints require deviating from a `SHOULD` or accommodating non-standard legacy clients:

1. **Document Every Deviation**:
   Maintain an `RFC_COMPLIANCE.md` or Conformance Matrix in the repository explaining:
   - Specific RFC Clause (`RFC 9110 Section 7.6.1`).
   - The normative text (`A sender SHOULD include...`).
   - The reason for divergence (e.g. browser compatibility quirks, internal low-latency bus invariants).
   - How the divergence is contained or guarded.
2. **Never Silently Violate `MUST` or `MUST NOT`**:
   Violating a `MUST` or `MUST NOT` without peer negotiation creates protocol corruption and vulnerabilities (e.g. HTTP request smuggling, cache poisoning).
