# DOOM Mobile Client
This Flutter package is the mobile-side lifecycle shell. Transport/authentication is intentionally injected by the application; protected vault data is never part of the mobile client state. Add a platform background service for Android/iOS only after the authenticated DOOM transport is configured.
