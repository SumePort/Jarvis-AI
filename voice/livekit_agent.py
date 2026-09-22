"""Realtime LiveKit voice front-end for JARVIS V2.

LiveKit owns microphone streaming, VAD/turn detection, interruptions, STT and
TTS. JARVIS V2 remains the source of truth for reasoning, tools, security,
memory and DOOM sessions.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()
load_dotenv(".env.local")

from livekit import agents
from livekit.agents import Agent, AgentServer, AgentSession, TurnHandlingOptions
from livekit.agents import ChatContext, ChatMessage, inference
from livekit.agents.llm import StopResponse
from livekit.plugins import openai

from jarvis_v2.personal.assistant import PersonalAssistant
from jarvis_v2.runtime.local import build_local_runtime


AGENT_NAME = os.getenv("LIVEKIT_AGENT_NAME", "jarvis")
STT_MODEL = os.getenv("LIVEKIT_STT_MODEL", "deepgram/nova-3")
STT_LANGUAGE = os.getenv("LIVEKIT_STT_LANGUAGE", "en")
TTS_MODEL = os.getenv("LIVEKIT_TTS_MODEL", "inworld/inworld-tts-2")
TTS_VOICE = os.getenv("LIVEKIT_TTS_VOICE", "Ashley")
LOCAL_LLM_URL = os.getenv("LOCAL_LLM_URL", os.getenv("JARVIS_MODEL_URL", "http://127.0.0.1:8080/v1"))
LOCAL_LLM_MODEL = os.getenv("LOCAL_LLM_MODEL", "local-model")


class JarvisV2VoiceAgent(Agent):
    def __init__(self, runtime, assistant: PersonalAssistant):
        self.runtime = runtime
        self.assistant = assistant
        super().__init__(
            instructions=(
                "You are the realtime voice interface for JARVIS V2. "
                "JARVIS V2 Core is authoritative for actions, security, memory "
                "and computer control. Keep spoken responses concise and natural."
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
            # First give the normal PersonalAssistant conversation path a chance.
            # Action requests are then handled by the full V2 runtime.
            personal = self.assistant.handle(text)
            if personal.mode == "conversation" and personal.conversation:
                response = personal.conversation.response
            else:
                result = self.runtime.run(text)
                response = self._runtime_response(result)
        except PermissionError as exc:
            response = str(exc)
        except Exception as exc:
            print(f"[JARVIS ERROR] {type(exc).__name__}: {exc}", flush=True)
            response = "I ran into an error while handling that request."

        response = " ".join(str(response or "").split()).strip()
        print(f"[JARVIS] {response}", flush=True)

        if response:
            await self.session.say(response, allow_interruptions=True)

        # JARVIS V2 generated the response. Do not let a second session LLM
        # answer the same turn.
        raise StopResponse()

    @staticmethod
    def _runtime_response(result) -> str:
        if getattr(result, "blocked", False):
            return getattr(result, "reason", "") or "I couldn't perform that request."

        execution = getattr(result, "execution", None)
        if execution is None:
            return "I couldn't complete that request."

        # EnvironmentAgentLoop exposes the executed plan and verification.
        plan = getattr(execution, "plan", None)
        steps = getattr(plan, "steps", []) if plan else []
        if not steps:
            return "I'm here. What would you like me to do?"

        state = getattr(execution, "state", None)
        user_message = getattr(execution, "user_message", None)
        if user_message:
            return user_message
        if getattr(state, "value", str(state)) == "waiting_for_user":
            return "I need you to complete the requested step on the screen."

        verification = getattr(execution, "verification", None)
        if verification is not None and not getattr(verification, "success", False):
            return getattr(verification, "message", "") or "The action did not complete."

        return "Done."

server = AgentServer()


@server.rtc_session(agent_name=AGENT_NAME)
async def jarvis_voice(ctx: agents.JobContext):
    # Use the exact same V2 composition root as the desktop runtime.
    runtime, _ = build_local_runtime(LOCAL_LLM_URL)

    # Authenticate the local assistant session for this trusted voice client.
    assistant = PersonalAssistant(runtime.services["brain"])
    assistant.authenticate(os.getenv("JARVIS_VOICE_USER_ID", "default"))

    session = AgentSession(
        stt=inference.STT(
            model=STT_MODEL,
            language=STT_LANGUAGE,
        ),
        # The session LLM is intentionally not used to answer turns. It is
        # still provided because AgentSession expects an LLM in the pipeline;
        # JARVIS V2 generates the actual answer through on_user_turn_completed.
        llm=openai.LLM(
            model=LOCAL_LLM_MODEL,
            base_url=LOCAL_LLM_URL,
            api_key=os.getenv("LOCAL_LLM_API_KEY", "local"),
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
        agent=JarvisV2VoiceAgent(runtime, assistant),
    )

    await session.say(
        "Jarvis is ready. I'm listening.",
        allow_interruptions=True,
    )


def main() -> None:
    print("=" * 64)
    print("JARVIS V2 — REALTIME VOICE MODE")
    print("=" * 64)
    print(f"Agent : {AGENT_NAME}")
    print(f"STT   : {STT_MODEL} ({STT_LANGUAGE})")
    print(f"TTS   : {TTS_MODEL} / {TTS_VOICE}")
    print(f"Brain : local llama-server @ {LOCAL_LLM_URL}")
    print("Turn detection : LiveKit audio turn detector")
    print("Interruptions  : enabled")
    print("=" * 64)
    agents.cli.run_app(server)


if __name__ == "__main__":
    main()
