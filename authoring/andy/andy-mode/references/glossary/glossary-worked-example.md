# Glossary worked example

A trimmed excerpt showing the expected format on a PKI domain:

```md
## Global conceptual model

### Relations

- Root CA signs Sub-CAs to delegate issuance without exposing the root key
- Sub-CA issues end-entity certificates under authorized profiles
- Root certificate is distributed to trust stores as the public trust anchor
- CRL, ARL, and OCSP expose revocation state consumed by relying parties

### Definitions

- Root CA : root certification authority
  - Def. : self-signed CA that anchors the trust chain and signs Sub-CA certificates
  - Project note : the private key is HSM-protected and only handled under approved key-ceremony rules
  - Distinct from : root certificate, root key, Sub-CA
  - Avoid : root-ca, root, root alone

- Sub-CA : subordinate certification authority
  - Def. : CA signed by the Root CA, authorized to issue end-entity certificates in the two-tier model
  - Distinct from : Root CA, Sub-CA certificate, intermediate CA
  - Avoid : intermediate CA, issuing CA, sub-ca, issuing-ca

## 0o0o Unresolved terminology

- 0o0o Key rotation
  - Ambiguity : conflated with certificate renewal
  - Recommendation : reserve "key rotation" for planned cryptographic key replacement; use "renewal" for certificates
  - Impact : CP/CPS, lifecycle docs, runbooks
```

What this example shows:

- Relations name two canonical concepts and express a stable structural link
  (*signs*, *issues*, *is distributed to*) — not actions or events.
- Definitions stay one sentence; only the terms with real confusion risk carry a
  `Distinct from` line.
- The `Avoid` line catches casual variants (`root-ca`, `intermediate CA`) that
  would otherwise become accepted aliases.
- `0o0o` flags a real terminology conflict (key rotation vs certificate renewal),
  not a delivery follow-up.
