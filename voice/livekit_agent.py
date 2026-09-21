"""LiveKit realtime voice front-end for Jarvis.

LiveKit owns realtime audio, turn detection, interruption handling, STT and TTS.
Jarvis Core remains the source of truth for reasoning, tools, security and memory.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()
load_dotenv(".env.local")

from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession, TurnHandlingOptions
from livekit.agents import ChatContext, ChatMessage
from livekit.agents import inference
from livekit.agents.llm import StopResponse
from livekit.plugins import openai

from core.main import Jarvis
from security.authentication import AuthenticationManager


AGENT_NAME = os.getenv("LIVEKIT_AGENT_NAME", "jarvis")
STT_MODEL = os.getenv("LIVEKIT_STT_MODEL", "deepgram/nova-3")
STT_LANGUAGE = os.getenv("LIVEKIT_STT_LANGUAGE", "en")
TTS_MODEL = os.getenv("LIVEKIT_TTS_MODEL", "inworld/inworld-tts-2")
TTS_VOICE = os.getenv("LIVEKIT_TTS_VOICE", "Ashley")
LOCAL_LLM_URL = os.getenv("LOCAL_LLM_URL", "http://127.0.0.1:8080/v1")
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "local-model")
LOCAL_LLM_API_KEY = os.getenv("LOCAL_LLM_API_KEY", "local")


class JarvisVoiceAgent(Agent):
    def __init__(self, jarvis: Jarvis) -> None:
        self.jarvis = jarvis
        super().__init__(
            instructions=(
                "You are the realtime voice interface for Jarvis. "
                "Do not invent capabilities. Jarvis Core executes commands, "
                "applies security policy, manages memory and controls the computer. "
                "Keep spoken responses concise and natural."
            )
        )

    async def on_user_turn_completed(
        self, turn_ctx: ChatContext, new_message: ChatMessage
    ) -> None:
        text = (new_message.text_content or "").strip()
        if not text:
            raise StopResponse()

        print(f"[USER] {text}", flush=True)

        try:
            response = self.jarvis.handle(text)
        except SystemExit:
            response = "Goodbye."
        except Exception as exc:
            print(f"[JARVIS ERROR] {exc}", flush=True)
            response = "I ran into an error while handling that request."

        response = " ".join(str(response or "").split()).strip()
        print(f"[JARVIS] {response}", flush=True)

        if response:
            await self.session.say(response, allow_interruptions=True)

        # Jarvis Core already generated the response. Prevent the session LLM
        # from generating a second response for the same turn.
        raise StopResponse()


server = AgentServer()


@server.rtc_session(agent_name=AGENT_NAME)
async def jarvis_voice(ctx: agents.JobContext):
    jarvis = Jarvis()

    session = AgentSession(
        stt=inference.STT(
            model=STT_MODEL,
            language=STT_LANGUAGE,
        ),
        llm=openai.LLM(
            model=LOCAL_LLM_MODEL,
            base_url=LOCAL_LLM_URL,
            api_key=LOCAL_LLM_API_KEY,
        ),
        tts=inference.TTS(
            model=TTS_MODEL,
            voice=TTS_VOICE,
        ),
        turn_handling=TurnHandlingOptions(
            turn_detection=inference.TurnDetector(),
        ),
    )

    await session.start(
        room=ctx.room,
        agent=JarvisVoiceAgent(jarvis),
    )

    await session.say(
        "Jarvis is ready. How can I help?",
        allow_interruptions=True,
    )


def main() -> None:
    if not AuthenticationManager().authenticate():
        print("Authentication failed. Jarvis locked.")
        return

    print("=" * 64)
    print("JARVIS — LIVEKIT VOICE MODE")
    print("=" * 64)
    print(f"Agent : {AGENT_NAME}")
    print(f"STT   : {STT_MODEL} ({STT_LANGUAGE})")
    print(f"TTS   : {TTS_MODEL} / {TTS_VOICE}")
    print(f"Brain : {LOCAL_LLM_MODEL} @ {LOCAL_LLM_URL}")
    print("LiveKit handles realtime audio, turns and interruptions.")
    print("=" * 64)

    agents.cli.run_app(server)


if __name__ == "__main__":
    main()
