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
)
from livekit.plugins import murf, silero, google, deepgram, noise_cancellation
from livekit.plugins.turn_detector.multilingual import MultilingualModel

logger = logging.getLogger("agent")
logger.setLevel(logging.DEBUG)

load_dotenv(".env.local")

# Change this prompt to change what your voice agent does.
# See README.md for example prompts (customer support, language tutor, receptionist).
SYSTEM_PROMPT = """You are 'Arthashathi', an expert Indian financial literacy, banking, and government scheme assistant. 

Your core responsibilities are:
1. Government Scheme Explainer: Clearly and simply explain key Indian government financial schemes (e.g., PM Jan Dhan Yojana, PM Mudra Yojana, Sukanya Samriddhi Yojana, Atal Pension Yojana), including eligibility criteria, benefits, and the application process.
2. Banking Literacy: Teach fundamental banking concepts, safe digital banking (UPI, Netbanking), types of bank accounts, and loans in easy-to-understand terms.
3. Fraud Awareness & Cyber Security: Actively educate users on how to protect themselves from financial frauds, cyber scams, fake OTP calls, phishing links, and investment scams. Advise them to use the national cybercrime helpline 1930 for reporting.

Guidelines for interaction:
- Keep your answers highly concise, structured, and conversational (this is a voice-based AI).
- Use a warm, trustworthy, and authoritative yet empathetic tone.
- Avoid heavy financial jargon; explain things simply so that anyone from any background can understand.
- If a user asks about non-financial topics, politely guide them back to banking, schemes, or financial safety."""


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
            model="nova-2",
            interim_results=True,
            no_delay=True,
            endpointing_ms=25,
            smart_format=False,
            punctuate=False,
        ),
        # LLM: Gemini 1.5 Flash — proven stable model name format
        llm=google.LLM(
            model="models/gemini-flash-latest",
            temperature=0.7,
        ),
        # TTS: Murf with aggressive streaming — synthesize chunk-by-chunk
        tts=murf.TTS(
            voice="en-IN-pooja",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=1),
            text_pacing=False,
            streaming=True,
            min_buffer_size=1,
        ),
        # Turn detection
        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        # Preemptive generation: start generating while user is still finishing
        preemptive_generation=True,
        # Reduced endpointing delays for faster response initiation
        min_endpointing_delay=0.3,
        max_endpointing_delay=1.5,
        # Interruption settings
        min_interruption_duration=0.4,
    )

    # -------------------------------------------------------------------------
    # Deep diagnostic logging — pipeline stage event hooks
    # -------------------------------------------------------------------------
    _pipeline_t0 = {}

    @session.on("user_input_transcribed")
    def on_user_transcribed(transcript):
        _pipeline_t0["stt_end"] = time.perf_counter()
        logger.info(f"[DIAG-STT] User speech transcribed: '{transcript}'")

    @session.on("user_state_changed")
    def on_user_state(evt):
        if evt.new_state == "speaking":
            logger.info("🎤 USER STARTED SPEAKING - STT IS WORKING!")
        elif evt.new_state == "listening":
            logger.info("🛑 USER STOPPED SPEAKING - PROCESSING LLM...")

    @session.on("agent_state_changed")
    def on_agent_state(evt):
        t_stt = _pipeline_t0.get("stt_end")
        latency_msg = ""
        if t_stt and evt.new_state == "speaking":
            latency_msg = f" | time-since-STT={time.perf_counter() - t_stt:.3f}s"
        logger.info(f"[DIAG-STATE] Agent state → {evt.new_state}{latency_msg}")

    @session.on("error")
    def on_error(err: Exception):
        logger.error(f"[DIAG-ERROR] Pipeline error: {err}", exc_info=err)

    @session.on("llm_error")
    def on_llm_error(err: Exception):
        logger.error(f"[DIAG-LLM-ERROR] LLM failed or timed out: {err}", exc_info=err)

    @session.on("tts_error")
    def on_tts_error(err: Exception):
        logger.error(f"[DIAG-TTS-ERROR] TTS failed or timed out: {err}", exc_info=err)

    @session.on("metrics_collected")
    def on_metrics(metrics):
        logger.info(f"[DIAG-METRICS] {metrics}")

    # Raw VAD hook — fires even before STT processes audio
    # This tells us if the microphone data is physically reaching the agent
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
