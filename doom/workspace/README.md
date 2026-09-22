# DOOM Phase 3 — Distributed Workspace

Phase 3 adds the first provider-neutral workspace layer.

It provides project manifests, SHA-256 content addressing, a provider-neutral
object-store contract, a local object store for development/testing, and
policy-aware push/pull synchronization.

NORMAL files may synchronize. PROTECTED files are rejected by synchronization.
CONTROLLED files currently follow the normal transport rule until a later
explicit approval workflow is implemented.

The protected local vault remains separate from distributed workspace storage.
Secrets should not be placed in project workspaces.

Future Oracle, S3-compatible, private-server, or other storage backends can
implement the same ObjectStore contract without changing JARVIS or DOOM.
Phase 3 does not expose storage to the Internet and does not implement
multi-device conflict resolution yet.
