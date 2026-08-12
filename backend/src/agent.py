import logging
import time
from typing import Optional

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

    @function_tool
    async def check_scheme_eligibility(
        self, 
        context: RunContext, 
        scheme_name: str,
        annual_income: Optional[int] = None,
        owns_pucca_house: Optional[bool] = None,
        age: Optional[int] = None,
        is_farmer: Optional[bool] = None,
        has_bank_account: Optional[bool] = None,
        is_bpl_or_poor: Optional[bool] = None,
        has_existing_lpg_connection: Optional[bool] = None,
        applicant_is_female: Optional[bool] = None,
        is_indian_citizen: Optional[bool] = None
    ) -> str:
        """Call this whenever the user asks if they qualify/are eligible for a specific
        government scheme, after collecting the relevant details from them in conversation
        first — do not call with guessed or missing critical values, ask the user first
        if you don't have enough information.
        
        Args:
            scheme_name: Internal name of the scheme (e.g. 'pm_awas_yojana', 'pm_vaya_vandana_yojana', etc)
            annual_income: The user's annual household income in INR.
            owns_pucca_house: Whether the user owns a permanent (pucca) house.
            age: The user's age in years.
            is_farmer: Whether the user is a farmer.
            has_bank_account: Whether the user has a bank account.
            is_bpl_or_poor: Whether the user belongs to the Below Poverty Line (BPL) category.
            has_existing_lpg_connection: Whether the user already has an LPG gas connection.
            applicant_is_female: Whether the primary applicant is female.
            is_indian_citizen: Whether the user is an Indian citizen.
        """
        logger.info(f"[TOOL-CALLED] check_scheme_eligibility was invoked with scheme={scheme_name}")
        try:
            from schemes_data import SCHEMES
            
            # Clean up scheme name if the model passes a friendly name
            norm_name = scheme_name.lower().replace(" ", "_")
            if norm_name not in SCHEMES:
                # Fuzzy matching fallback can go here, but for now just exact/normalized
                # Let's check if we can find it as a substring
                found = None
                for key in SCHEMES.keys():
                    if key in norm_name or norm_name in key:
                        found = key
                        break
                
                if found:
                    scheme_key = found
                else:
                    return f"I don't have enough information to check eligibility for '{scheme_name}'. Ask the user to clarify the scheme name."
            else:
                scheme_key = norm_name
                
            scheme = SCHEMES[scheme_key]
            criteria = scheme.get("criteria", {})
            
            missing_fields = []
            eligibility_status = "eligible"
            reasons = []
            
            # Check max annual income
            if "max_annual_income" in criteria:
                if annual_income is None:
                    missing_fields.append("annual household income")
                elif annual_income > criteria["max_annual_income"]:
                    eligibility_status = "not eligible"
                    reasons.append(f"annual income ({annual_income}) exceeds the limit of {criteria['max_annual_income']}")
            
            # Check owns pucca house
            if "must_not_own_pucca_house" in criteria:
                if owns_pucca_house is None:
                    missing_fields.append("whether they own a pucca (permanent) house")
                elif owns_pucca_house:
                    eligibility_status = "not eligible"
                    reasons.append("applicant already owns a pucca house")
                    
            # Check age
            if "min_age" in criteria:
                if age is None:
                    missing_fields.append("age")
                elif age < criteria["min_age"]:
                    eligibility_status = "not eligible"
                    reasons.append(f"age ({age}) is below the minimum required age of {criteria['min_age']}")
            
            if "max_age" in criteria:
                if age is None and "age" not in missing_fields:
                    missing_fields.append("age")
                elif age is not None and age > criteria["max_age"]:
                    eligibility_status = "not eligible"
                    reasons.append(f"age ({age}) is above the maximum allowed age of {criteria['max_age']}")
            
            if "is_farmer" in criteria:
                if is_farmer is None:
                    missing_fields.append("whether they are a farmer")
                elif not is_farmer:
                    eligibility_status = "not eligible"
                    reasons.append("applicant is not a farmer")
                    
            if "is_bpl_or_poor" in criteria:
                if is_bpl_or_poor is None:
                    missing_fields.append("whether they belong to the BPL category")
                elif not is_bpl_or_poor:
                    eligibility_status = "not eligible"
                    reasons.append("applicant does not belong to the BPL category")
                    
            if "has_existing_lpg_connection" in criteria:
                if has_existing_lpg_connection is None:
                    missing_fields.append("whether they already have an LPG connection")
                elif has_existing_lpg_connection:
                    eligibility_status = "not eligible"
                    reasons.append("applicant already has an LPG connection")
                    
            if "applicant_is_female" in criteria:
                if applicant_is_female is None:
                    missing_fields.append("whether the applicant is female")
                elif not applicant_is_female:
                    eligibility_status = "not eligible"
                    reasons.append("the scheme is specifically for women")
                    
            if "has_bank_account" in criteria:
                if has_bank_account is None:
                    missing_fields.append("whether they have a bank account")
                elif not has_bank_account:
                    eligibility_status = "not eligible"
                    reasons.append("applicant does not have a bank account")
                    
            if "is_indian_citizen" in criteria:
                if is_indian_citizen is None:
                    missing_fields.append("whether they are an Indian citizen")
                elif not is_indian_citizen:
                    eligibility_status = "not eligible"
                    reasons.append("applicant is not an Indian citizen")
            
            if missing_fields:
                fields_str = ", ".join(missing_fields)
                return f"I need more information to check eligibility for {scheme['name']}. Please ask the user for their: {fields_str}."
                
            if eligibility_status == "eligible":
                return f"Based on the provided details, the user appears ELIGIBLE for {scheme['name']}. (Note: Data as of {scheme.get('data_as_of')})."
            else:
                reasons_str = "; ".join(reasons)
                return f"Based on the provided details, the user is NOT ELIGIBLE for {scheme['name']} because: {reasons_str}. (Note: Data as of {scheme.get('data_as_of')})."
                
        except Exception as e:
            logger.error(f"[DIAG-TOOL-ERROR] check_scheme_eligibility failed: {e}", exc_info=True)
            return "An error occurred while checking eligibility. Please ask the user for their relevant details again or advise them to verify eligibility at their bank or official portal."

    @function_tool
    async def opt_out_of_calls(self, context: RunContext) -> str:
        """Call this function when a user indicates they want no further outbound calls 
        (e.g., "don't call me again", "stop calling", "remove me").
        This will mark their record so they won't be bothered again.
        """
        user_id = context.userdata.get("user_id", "unknown")
        logger.info(f"[TOOL-CALLED] opt_out_of_calls was invoked for user_id={user_id}")
        try:
            from database import set_do_not_call
            set_do_not_call(user_id)
            return "The user has been marked as DO NOT CALL. Please acknowledge this politely and end the conversation."
        except Exception as e:
            logger.error(f"[DIAG-TOOL-ERROR] opt_out_of_calls failed: {e}", exc_info=True)
            return "Failed to update the database. Just end the conversation politely."

    @function_tool
    async def create_escalation(
        self,
        reason: str,
        summary: str,
        urgency: str,
        caller_language: str,
        preferred_followup: str,
        context: RunContext
    ) -> str:
        """Call this ONLY after (a) identifying the situation genuinely needs human help per the two categories (fraud in progress or decisions needing human authority), AND (b) asking the caller for permission to share their information and getting an explicit yes.
        Never call this for routine questions the agent can already answer.
        The summary must NEVER include OTPs, PINs, passwords, account numbers, card numbers, Aadhaar/PAN numbers, or other sensitive credentials — only the general nature of the issue.
        """
        user_id = context.userdata.get("user_id", "unknown")
        logger.info(f"[TOOL-CALLED] create_escalation invoked for user_id={user_id}, urgency={urgency}")
        try:
            from escalation import send_escalation
            ref_id = await send_escalation(
                reason=reason,
                summary=summary,
                urgency=urgency,
                caller_language=caller_language,
                preferred_followup=preferred_followup,
                caller_id=user_id
            )
            return f"Your request has been logged with reference {ref_id}. A team member will review it, though I can't guarantee an immediate response."
        except Exception as e:
            logger.error(f"[DIAG-TOOL-ERROR] create_escalation failed: {e}", exc_info=True)
            return "An error occurred while escalating. Please advise the user to contact the helpline directly."

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


@server.rtc_session(agent_name="murf-agent")
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # -------------------------------------------------------------------------
    # Pipeline setup — optimized for minimum latency
    # -------------------------------------------------------------------------
    session = AgentSession(
        userdata={},
        # STT: Deepgram Nova-3
        stt=deepgram.STT(
            model="nova-3",
            language="multi",
            interim_results=True,
            no_delay=True,
            endpointing_ms=300,  # Lowered from 800ms for much faster response latency
            smart_format=False,
            punctuate=False,
        ),
        # LLM: LiveKit Inference fallback for reliability
        llm=google.LLM(
            model="gemini-3.1-flash-lite",
        ),
        # TTS: Murf — smooth continuous chunks
        tts=murf.TTS(
            voice="Anisha",
            style="Conversation",
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=5),
            # Removed text_pacing=False to ensure end_of_stream emits properly and pipeline unlocks
        ),

        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=False,
        # Reduced endpointing delays for faster response initiation
        min_endpointing_delay=0.4,
        max_endpointing_delay=1.0,
        # Interruption settings
        min_interruption_duration=0.4, # Lowered from 0.7s so "Wait" interrupts easily
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
                    if getattr(getattr(params, "participant", None), "kind", None)
                    == rtc.ParticipantKind.PARTICIPANT_KIND_SIP
                    else noise_cancellation.BVC()
                ),
            ),
        ),
    )

    logger.info("AGENT JOB RECEIVED - connecting to room")
    await ctx.connect()
    logger.info("ROOM CONNECTED")

    import asyncio
    
    participant_joined = asyncio.Event()
    caller_id = "unknown-participant"
    
    # Check if participant is already present
    for p in ctx.room.remote_participants.values():
        if p.kind in (rtc.ParticipantKind.PARTICIPANT_KIND_SIP, rtc.ParticipantKind.PARTICIPANT_KIND_STANDARD):
            caller_id = p.identity or "unknown-participant"
            participant_joined.set()
            break
            
    # Listen for participant to connect if not already present
    @ctx.room.on("participant_connected")
    def on_participant_connected(p: rtc.RemoteParticipant):
        nonlocal caller_id
        if p.kind in (rtc.ParticipantKind.PARTICIPANT_KIND_SIP, rtc.ParticipantKind.PARTICIPANT_KIND_STANDARD):
            caller_id = p.identity or "unknown-participant"
            participant_joined.set()

        logger.info("WAITING FOR SIP PARTICIPANT TO JOIN...")
    await participant_joined.wait()
    
    session.userdata["user_id"] = caller_id
    logger.info("SIP PARTICIPANT JOINED")

    # Check for outbound call metadata
    is_outbound = False
    reason_for_call = ""
    if ctx.room.metadata:
        import json
        try:
            meta = json.loads(ctx.room.metadata)
            is_outbound = meta.get("outbound", False)
            reason_for_call = meta.get("reason", "")
        except json.JSONDecodeError:
            pass

    logger.info(f"GREETING START (is_outbound={is_outbound}, metadata={ctx.room.metadata})")

    if is_outbound:
        # --- THE MAGIC FIX: WAIT FOR LINPHONE AUDIO CHANNEL TO OPEN ---
        # Give Linphone 2 seconds to fully connect the audio before speaking
        import asyncio
        logger.info("Waiting 2 seconds for SIP audio tracks to fully establish...")
        await asyncio.sleep(2.0)

        # --- STRICT DAY 6 OUTBOUND GREETING ---
        outbound_greeting = (
            "Namaskar, I am Arthashathi, your financial guide. "
            "I am calling to remind you that your PM Awas Yojana application deadline is tomorrow. "
            "If you do not want to receive these calls, please just hang up. "
            "Otherwise, would you like to know the required documents?"
        )
        logger.info("Speaking the outbound greeting...")
        try:
            await session.say(outbound_greeting, allow_interruptions=False)
        except asyncio.CancelledError:
            pass
    else:
        # --- NORMAL BROWSER GREETING ---
        browser_greeting = "Namaskar, I'm Arthashathi. How can I help you today?"
        logger.info("Speaking the browser greeting...")
        import asyncio
        try:
            await session.say(browser_greeting, allow_interruptions=True)
        except asyncio.CancelledError:
            logger.info("Browser greeting was interrupted by the user. Continuing session.")
            pass


    logger.info("KEEPING JOB ALIVE")
    await asyncio.Event().wait()
    logger.info("SESSION ENDED")



if __name__ == "__main__":
    cli.run_app(server)
