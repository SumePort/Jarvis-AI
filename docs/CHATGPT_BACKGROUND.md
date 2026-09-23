# JARVIS + ChatGPT Background Voice

JARVIS can optionally use the ChatGPT web Voice experience as a conversational
voice layer while JARVIS V2 remains the local computer-control authority.

## What it does

- Starts a separate persistent Chromium profile for ChatGPT.
- Keeps the ChatGPT window minimized after startup.
- Grants microphone permission to that browser context.
- Prefers ChatGPT Temporary Chat.
- Asks ChatGPT to emit explicit JARVIS action markers for computer-control
  requests.
- JARVIS executes those requests through the existing V2 runtime and security
  boundary.
- Sends the action result back to the voice conversation.
- Never automates passwords, PINs, OTPs, CVVs, recovery codes, API keys or
  other secrets.

Temporary Chat is preferable to creating and deleting a normal chat. OpenAI
states that Temporary Chats do not appear in chat history and do not create or
update memories while temporary. OpenAI may retain a copy for up to 30 days
for safety purposes.

## Setup

From the repository root:

    .\\.venv\\Scripts\\Activate.ps1
    pip install playwright
    playwright install chromium

Then start the local brain if you want JARVIS actions to use the local model.

Start the bridge:

    python -m jarvis_v2.voice.chatgpt_background

On the first run:

1. A Chromium window opens.
2. Sign in to ChatGPT manually.
3. The bridge enables Temporary Chat.
4. The bridge starts Voice.
5. The window is minimized.
6. Speak normally into the PC microphone.

The browser profile is stored under
data/jarvis_v2/chatgpt_profile and is ignored by Git. Do not copy or commit
that directory.

## Action flow

    Microphone
       |
    ChatGPT Voice
       |
    natural conversation
       |
    JARVIS action marker
       |
    JARVIS V2 runtime + security
       |
    Windows / Chrome / files
       |
    result sent back to ChatGPT Voice

For example:

"Jarvis, open Chrome."

ChatGPT can answer naturally while also emitting the machine instruction.
JARVIS executes open Chrome, then sends the result back into the same
conversation.

## Important limitation

The ChatGPT website does not expose its Voice UI as a supported local
automation API. This bridge uses Playwright against the web interface, so it is
more fragile than a first-party API. If the ChatGPT UI changes, JARVIS reports
the bridge error rather than silently switching to a normal saved chat.

This bridge is intentionally replaceable. The local JARVIS V2 brain, security
engine and DOOM layers do not depend on ChatGPT.
