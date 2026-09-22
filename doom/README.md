# DOOM

DOOM is the persistent hybrid environment in which JARVIS runs.

It is not a VM and is not tied to one device. DOOM presents local PC, private
self-owned infrastructure, and cloud workers as one resource pool while keeping
sensitive secrets inside a PC-local encrypted vault.

## Foundation rules

1. JARVIS runs inside DOOM.
2. Workers can be local, private/self-owned, or cloud.
3. Normal project/workspace data may be distributed.
4. Protected secrets are PC-local by default: passwords, authentication secrets,
   banking/UPI/card PINs, bank/account credentials, financial/legal secrets,
   API/private encryption keys, and recovery codes.
5. Protected data cannot be routed to a remote worker without explicit authorization.
6. Cloud providers are replaceable workers, not DOOM itself.

## Phase 2 — Control Plane

The control plane coordinates DOOM devices and workers.

DOOM Client -> Control Plane -> Worker Registry -> Scheduler -> Worker

The initial server binds to 127.0.0.1:8787 by default. Device enrollment issues
a device token; the control plane stores only a SHA-256 token hash. Remote
exposure is deliberately not enabled yet. Secure transport and explicit device
enrollment must be added before exposing the control plane to a LAN or Internet.

Run locally: python -m doom.control

The current API supports health, device enrollment, worker registration, worker
listing, and policy-aware task planning. It does not execute remote tasks yet.

## Phase 3 — Distributed Workspace

Phase 3 adds persistent, provider-neutral project storage:

DOOM Client -> Workspace Manifest -> Object Store

A workspace manifest records each file by SHA-256 content address, size, path,
and DOOM data classification. The object-store interface is provider-neutral,
so local storage is only the first backend; future private servers, Oracle,
S3-compatible storage, or other providers can implement the same contract.

NORMAL project files may be synchronized. PROTECTED files are rejected by the
workspace sync layer and remain outside distributed storage. The protected vault
is a separate PC-local security boundary.

### Initialize a workspace

python -m doom workspace init my-project data/doom/workspaces/my-project

This creates:

data/doom/workspaces/my-project/.doom/manifest.json

Phase 3 does not expose storage to the Internet and does not yet implement
multi-device conflict resolution. Those are later phases.
