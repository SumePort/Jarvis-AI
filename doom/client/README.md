# DOOM Client — Windows

The DOOM client connects a PC to the DOOM control plane, enrolls the device, registers the local worker, and sends heartbeats.

## First setup

Start the control plane:

python -m doom.control

In another terminal, enroll the PC:

python -m doom.client enroll --name "My-PC"

Then register the local worker:

python -m doom.client register

Check status:

python -m doom.client status

Or perform the startup handshake:

python -m doom.client start

The client stores its device configuration under `data/doom/client.json`.
Treat this file as a local credential and do not commit it to Git.

## Windows startup

`scripts/doom-client-start.bat` provides a simple launcher. It can be placed in the user's Windows Startup folder after the client has been configured.

Phase 5 intentionally does not install a Windows service, create a scheduled task, expose the control plane publicly, or implement remote device access yet. Those require the secure transport and enrollment design from the next stage.

## Device role

The PC is both a DOOM client/device identity and a local DOOM worker. The client does not replace Windows; it runs alongside the host OS and provides the bridge between Windows resources and the DOOM control plane.
