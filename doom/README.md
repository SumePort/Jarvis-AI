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
listing, heartbeats, and policy-aware task planning.

## Phase 3 — Distributed Workspace

Phase 3 adds persistent, provider-neutral project storage:

DOOM Client -> Workspace Manifest -> Object Store

A workspace manifest records each file by SHA-256 content address, size, path,
and DOOM data classification. NORMAL project files may be synchronized.
PROTECTED files are rejected by the workspace sync layer and remain outside
distributed storage.

Initialize a workspace:

python -m doom workspace init my-project data/doom/workspaces/my-project

## Phase 4 — Cloud Workers

Phase 4 turns cloud/private machines into replaceable DOOM compute workers.

Architecture:

DOOM Control Plane
       |
       +-- Local PC worker
       +-- Private server worker
       +-- Cloud worker
                 |
                 +-- Oracle / AWS / GCP / other provider
                 +-- provider-neutral DOOM worker service

DOOM does not depend on any one cloud provider. A provider only supplies a
machine/network endpoint; the DOOM worker protocol remains the same.

### Worker protocol

A remote worker exposes:

- GET /health
- POST /v1/execute

The worker uses a bearer token and the control plane tracks worker endpoint,
type, capabilities, region, and online state.

Run the reference worker:

DOOM_WORKER_TOKEN=<strong-random-token> python -m doom.cloud

The reference Phase 4 worker intentionally refuses arbitrary command execution.
Remote task executors will be added only for explicitly supported capabilities.

### Routing

A task can request a preferred worker type.

Example:

- normal CPU work -> local by default
- authorized GPU work -> cloud can be preferred
- persistent service -> private worker can be preferred
- protected data -> local only unless explicitly authorized

The scheduler also exposes worker health through heartbeat/offline endpoints.

### Security boundary

Phase 4 does NOT upload protected data automatically.

Remote workers receive no DOOM vault keys. The control plane stores device
token hashes, not raw device tokens. Cloud workers are untrusted compute
resources unless they are explicitly designated as private/trusted by a future
policy layer.

Phase 4 establishes the hybrid compute protocol; it does not yet deploy
provider-specific infrastructure or expose the control plane publicly.


## Phase 5 — DOOM Client

Phase 5 adds the first local device client. A Windows PC can enroll itself with the control plane, register its local resources as a worker, and send heartbeats.

Run:

python -m doom.client enroll --name "My-PC"
python -m doom.client register
python -m doom.client status
python -m doom.client start

The client configuration is stored locally in `data/doom/client.json` and contains the device credential. It must never be committed to Git or copied into the distributed workspace.

A Windows launcher is provided at `scripts/doom-client-start.bat`. Phase 5 does not yet install a Windows service or expose the control plane publicly. Secure remote device connectivity comes before those steps.
