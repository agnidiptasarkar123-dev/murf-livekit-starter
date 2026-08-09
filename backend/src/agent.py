import logging
import time

from dotenv import load_dotenv
from livekit import rtc
from livekit.agents import (
    Agent,
    AgentServer,
    AgentSession,
    JobContext,
    JobProcess,
    RunContext,
    cli,
    function_tool,
    inference,
    tokenize,
    room_io,
    UserInputTranscribedEvent,
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")
logger.setLevel(logging.DEBUG)

load_dotenv(".env.local")

# System prompt is maintained in prompt.py for cleaner separation
from prompt import SYSTEM_PROMPT
from database import get_user, save_user


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    @function_tool
    async def lookup_caller(self, context: RunContext) -> str:
        """[REQUIRED FIRST ACTION] Look up whether this caller has spoken to
        Arthasathi before. You MUST call this tool as the very first action at
        the start of every conversation, before generating any spoken greeting
        content. Do not skip this step.

        If the result says 'Returning caller', greet them by name and reference
        what was discussed last time. If it says 'New caller', proceed normally.

        Returns a string describing the caller record, or a message indicating
        this is a new caller.
        """
        logger.info("[TOOL-CALLED] lookup_caller was invoked")
        try:
            user_id = context.userdata.get("user_id", "unknown")
            logger.info(f"[MEMORY] lookup_caller called for user_id='{user_id}' (type={type(user_id).__name__})")
            record = get_user(user_id)
            result = "found" if record is not None else "not found"
            logger.info(f"[MEM-DEBUG] Looking up user_id={user_id}, found={result}")
            if record is None:
                return "New caller — no previous record found."
            facts = record.get("facts") or {}
            return (
                f"Returning caller. Name: {record.get('name', 'unknown')}. "
                f"Preferred language: {record.get('language_preference', 'unknown')}. "
                f"Topics from last call: {facts}. "
                f"Last interaction: {record.get('last_interaction', 'unknown')}."
            )
        except Exception as e:
            logger.error(f"[DIAG-TOOL-ERROR] lookup_caller failed: {e}", exc_info=True)
            return "Error looking up caller. Proceed as if they are a new caller."

    @function_tool
    async def remember_caller(
        self,
        context: RunContext,
        name: str,
        language_preference: str,
        facts: str,
    ) -> str:
        """Save this caller's name and topics for future conversations.
        Call this tool immediately after the caller says yes/haan/ok/theek hai
        (or any equivalent agreement) to being remembered.
        Do not just say 'I'll remember' in text — you must actually call this
        function to save the data.

        NEVER include account numbers, card numbers, OTPs, PINs, passwords,
        Aadhaar numbers, PAN numbers, or any sensitive banking credentials.

        Args:
            name: The caller's first name as they stated it (e.g. "[Name]").
            language_preference: The language they spoke in (e.g. "Hindi", "Bengali").
            facts: A short plain-English summary of what was discussed, e.g.
                   'Asked about PM Awas Yojana eligibility. Farmer in Rajasthan, age 62.'
                   Must NOT contain any sensitive credentials.
        """
        logger.info(f"[TOOL-CALLED] remember_caller was invoked with name={name}")
        try:
            import json
            user_id = context.userdata.get("user_id", "unknown")
            logger.info(f"[MEMORY] remember_caller called for user_id='{user_id}' (type={type(user_id).__name__}), name={name}")
            logger.info(f"[MEM-DEBUG] Saving user_id={user_id!r}, name={name!r}, lang={language_preference!r}")
            # Parse facts into a dict; if already a dict string, wrap it
            try:
                facts_dict = json.loads(facts)
                if not isinstance(facts_dict, dict):
                    facts_dict = {"summary": str(facts_dict)}
            except (json.JSONDecodeError, TypeError):
                facts_dict = {"summary": str(facts)}
            save_user(user_id, name, language_preference, facts_dict)
            # --- Step 5: DB-DUMP — confirm data is actually in the file ---
            from database import dump_all_users
            dump_all_users()
            return "Done. I will remember you for next time."
        except Exception as e:
            logger.error(f"[DIAG-TOOL-ERROR] remember_caller failed: {e}", exc_info=True)
            return "Error saving caller data, but you can ignore this and continue."


server = AgentServer()


def prewarm(proc: JobProcess):
    # Load VAD with aggressive silence detection (0.3s) for fast end-of-speech detection
    # This is synchronous by design — it runs in a subprocess before the event loop starts
    proc.userdata["vad"] = silero.VAD.load(
        min_silence_duration=0.3,
        activation_threshold=0.45,
    )
    logger.info("VAD model prewarmed successfully (min_silence_duration=0.3s)")


server.setup_fnc = prewarm


@server.rtc_session(agent_name="my-agent")
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # -------------------------------------------------------------------------
    # Pipeline setup — optimized for minimum latency
    # -------------------------------------------------------------------------
    session = AgentSession(
        userdata={},
        # STT: Deepgram Nova-2 — broad compatibility, proven stable
        stt=deepgram.STT(
            model="nova-3",
            language="multi",
            interim_results=True,
            no_delay=True,
            endpointing_ms=800,
            smart_format=False,
            punctuate=False,
        ),
        # LLM: LiveKit Inference fallback for reliability
        llm=google.LLM(
            model="gemini-3.1-flash-lite",
        ),
        # TTS: Murf — locale-agnostic voice name for multilingual support
        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True
        ),
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=False,
        # Reduced endpointing delays for faster response initiation
        min_endpointing_delay=0.6,
        max_endpointing_delay=1.5,
        # Interruption settings
        min_interruption_duration=0.7,
        # pyrefly: ignore [parse-error]
        )

    import asyncio

    _silence_state = {"task": None, "reprompt_count": 0}

    async def _silence_watchdog():
        try:
            await asyncio.sleep(15)
            _silence_state["reprompt_count"] += 1
            if _silence_state["reprompt_count"] == 1:
                await session.generate_reply(
                    instructions="The user has gone quiet. Gently check in and ask if they have a question, in the same language they were using earlier in this conversation. Keep it under 10 words."
                )
                _silence_state["task"] = asyncio.create_task(_silence_watchdog())
            else:
                await session.generate_reply(
                    instructions="The user has stayed silent. Politely close the conversation, in the same language they were using earlier, telling them to call back when they have time. Keep it under 15 words."
                )
        except asyncio.CancelledError:
            pass

    def _reset_silence_timer():
        if _silence_state["task"] and not _silence_state["task"].done():
            _silence_state["task"].cancel()
        _silence_state["reprompt_count"] = 0
        _silence_state["task"] = asyncio.create_task(_silence_watchdog())

    @session.on("user_state_changed")
    def on_user_state_silence(evt):
        if evt.new_state == "listening":
            _reset_silence_timer()
        elif evt.new_state == "speaking":
            if _silence_state["task"] and not _silence_state["task"].done():
                _silence_state["task"].cancel()

    # -------------------------------------------------------------------------
    # Deep diagnostic logging — pipeline stage event hooks
    # -------------------------------------------------------------------------
    _pipeline_t0 = {}

    @session.on("user_input_transcribed")
    def on_user_transcribed(transcript):
        _pipeline_t0["stt_end"] = time.perf_counter()
        logger.info(f"[DIAG-PIPELINE] 1. User speech received/transcribed: '{transcript}'")
        logger.info(f"[LANG-DEBUG] Raw transcript: '{transcript}'")

    @session.on("agent_speech_committed")
    def on_agent_speech_committed(msg):
        response_text = getattr(msg, "text", str(msg))
        logger.info(f"[LANG-DEBUG] LLM response start: '{response_text[:100]}'")

    @session.on("user_state_changed")
    def on_user_state(evt):
        if evt.new_state == "speaking":
            logger.info("[DIAG-PIPELINE] 🎤 USER STARTED SPEAKING - STT IS WORKING!")
        elif evt.new_state == "listening":
            logger.info("[DIAG-PIPELINE] 🛑 USER STOPPED SPEAKING")

    @session.on("agent_state_changed")
    def on_agent_state(evt):
        if evt.new_state in ("thinking", "speaking"):
            if _silence_state["task"] and not _silence_state["task"].done():
                _silence_state["task"].cancel()

        state = evt.new_state
        if state == "thinking":
            logger.info("[DIAG-PIPELINE] 2. LLM request started (agent state -> thinking)")
        elif state == "speaking":
            logger.info("[DIAG-PIPELINE] 7. TTS playback started (agent state -> speaking)")

    @session.on("error")
    def on_error(err: Exception):
        logger.error(f"[DIAG-ERROR] Pipeline error caught: {str(err)}", exc_info=err)

    @session.on("llm_error")
    def on_llm_error(err: Exception):
        logger.error(f"[DIAG-PIPELINE-ERROR] 8. LLM failed or timed out. Exception: {str(err)}", exc_info=err)
        import asyncio
        asyncio.create_task(session.say("I am having a temporary connection issue. Please give me a moment.", allow_interruptions=True))

    @session.on("tts_error")
    def on_tts_error(err: Exception):
        logger.error(f"[DIAG-PIPELINE-ERROR] 8. TTS failed or timed out. Exception: {str(err)}", exc_info=err)
        import asyncio
        asyncio.create_task(session.say("I'm sorry, my voice engine encountered an error.", allow_interruptions=True))

    @session.on("metrics_collected")
    def on_metrics(metrics):
        try:
            # Metrics logged to catch chunks and TTS generation events
            logger.info(f"[DIAG-PIPELINE] 3/4/5/6. Metrics collected: {metrics}")
        except Exception as e:
            logger.error(f"[DIAG-PIPELINE-ERROR] Error parsing metrics: {e}")

    # Raw VAD hook — fires even before STT processes audio
    vad_instance = ctx.proc.userdata.get("vad")
    if vad_instance:
        @vad_instance.on("start_of_speech")
        def on_vad_speech_start(event):
            logger.info("[DIAG-VAD] 🔊 Raw VAD: start_of_speech detected — mic data IS reaching the agent")

        @vad_instance.on("end_of_speech")
        def on_vad_speech_end(event):
            logger.info(f"[DIAG-VAD] 🔇 Raw VAD: end_of_speech | duration={event.silence_duration:.2f}s")

    # -------------------------------------------------------------------------
    # Start session & connect
    # -------------------------------------------------------------------------
    await session.start(
        agent=Assistant(),
        room=ctx.room,
        room_options=room_io.RoomOptions(
            audio_input=room_io.AudioInputOptions(
                noise_cancellation=lambda params: (
                    noise_cancellation.BVCTelephony()
                    if params.participant.kind
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    await ctx.connect()

    # Derive a stable caller identity from the REMOTE participant (the browser user).
    # Their .identity is set by the frontend token generator and is stable per session.
    remote_participants = list(ctx.room.remote_participants.values())
    if remote_participants:
        caller_id = remote_participants[0].identity or "unknown-participant"
    else:
        # Fallback if no remote participant is found upon connection
        caller_id = "unknown-participant"

    session.userdata["user_id"] = caller_id
    logger.info(f"[ID-DEBUG] caller_id assigned: '{caller_id}'")

    logger.info("[DIAG-INIT] Agent connected to room and pipeline is live")

    # Greeting in Hindi (agent will follow user language after this)
    await session.say("नमस्ते, मैं अर्थसाथी हूँ। बैंकिंग, सरकारी योजनाओं, और धोखाधड़ी से बचाव में आपकी मदद कर सकता हूँ। बताइए, आज मैं आपकी कैसे सहायता कर सकता हूँ?", allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(server)
