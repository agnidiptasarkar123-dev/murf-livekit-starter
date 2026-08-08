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
    cli,
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


class Assistant(Agent):
    def __init__(self) -> None:
        super().__init__(instructions=SYSTEM_PROMPT)

    # To add tools, use the @function_tool decorator.
    # Here's an example that adds a simple weather tool.
    # You also have to add `from livekit.agents import function_tool, RunContext` to the top of this file
    # @function_tool
    # async def lookup_weather(self, context: RunContext, location: str):
    #     """Use this tool to look up current weather information in the given location.
    #
    #     If the location is not supported by the weather service, the tool will indicate this. You must tell the user the location's weather is unavailable.
    #
    #     Args:
    #         location: The location to look up weather information for (e.g. city name)
    #     """
    #
    #     logger.info(f"Looking up weather for {location}")
    #
    #     return "sunny with a temperature of 70 degrees."


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
        # STT: Deepgram Nova-2 — broad compatibility, proven stable
        stt=deepgram.STT(
            model="nova-3",
            language="multi",
            interim_results=True,
            no_delay=True,
            endpointing_ms=500,
            smart_format=False,
            punctuate=False,
        ),
        # LLM: LiveKit Inference fallback for reliability
        llm=inference.LLM(
            model="google/gemini-2.5-flash-lite"
        ),
        # TTS: Murf with aggressive streaming — synthesize chunk-by-chunk
        tts=murf.TTS(
            voice="hi-IN-anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=2),
            text_pacing=True
        ),
        # turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=False,
        # Reduced endpointing delays for faster response initiation
        min_endpointing_delay=0.3,
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
    logger.info("[DIAG-INIT] Agent connected to room and pipeline is live")

    # Welcome message to verify TTS pipeline is working
    await session.say("Namaskar, I am Arthashathi, your financial guide. Are you able to hear me?", allow_interruptions=True)


if __name__ == "__main__":
    cli.run_app(server)
