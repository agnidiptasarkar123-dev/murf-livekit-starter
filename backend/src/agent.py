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
from prompt import SYSTEM_PROMPT, SPECIALIST_PROMPT
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
    async def mark_call_completed(self, context: RunContext, reason: str, successful: bool) -> str:
        """Call this tool when the user clearly indicates that their request has been fully resolved (e.g. saying 'thank you', 'that's all', 'okay, bye') OR when the call has naturally concluded.
        Args:
            reason: A short summary of why the call was marked completed.
            successful: True if the user's request was successfully resolved, False if it was unresolved or failed.
        """
        logger.info(f"[TOOL-CALLED] mark_call_completed: {reason} (Success={successful})")
        context.userdata["call_success"] = successful
        context.userdata["outcome_reason"] = reason
        return "Call marked as completed. You may now give a natural closing response."

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
        context.userdata["task_type"] = "Scheme Eligibility"
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
        The summary must NEVER include OTPs, PINs, passwords, account numbers, card numbers, Aadhaar/PAN numbers, or other sensitive credentials -- only the general nature of the issue.
        """
        user_id = context.userdata.get("user_id", "unknown")
        logger.info(f"[TOOL-CALLED] create_escalation invoked for user_id={user_id}, urgency={urgency}")
        context.userdata["task_type"] = "Human Escalation"
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

    @function_tool
    async def handoff_to_scheme_specialist(
        self,
        context: RunContext,
        context_summary: str,
    ) -> str:
        """Transfer the user to the Government Scheme Specialist agent.

        Call this tool ONLY when the user's request genuinely requires detailed
        government-scheme assistance, such as:
          - Checking eligibility for a specific scheme (PM Awas Yojana, PM Ujjwala Yojana, etc.)
          - Asking about benefits or details of a government scheme
          - Asking which scheme they should apply for
          - Any question that requires deep government-scheme expertise

        Do NOT call this for:
          - General banking questions
          - UPI/OTP fraud protection advice
          - General financial guidance
          - Questions you can answer directly with existing knowledge

        IMPORTANT: Before calling this tool, tell the user you are connecting
        them to the government scheme specialist (e.g. 'I'll connect you to our
        government scheme specialist who can help you with that.').

        Args:
            context_summary: A short plain-English summary of what the user is
                asking about (e.g. 'User is asking about eligibility for PM
                Awas Yojana. They are a farmer in UP, age 45.'). This MUST NOT
                contain any sensitive data: no OTPs, PINs, passwords, account
                numbers, card numbers, Aadhaar/PAN numbers, or credentials.
        """
        logger.info(f"[TOOL-CALLED] handoff_to_scheme_specialist invoked")
        try:
            # --- Safety: validate context_summary to block sensitive data ---
            sensitive_keywords = [
                "otp", "pin", "cvv", "password", "account number", "card number",
                "aadhaar", "aadhar", "pan number", "upi pin", "net banking",
                "login", "credential", "passcode",
            ]
            summary_lower = context_summary.lower() if context_summary else ""
            for kw in sensitive_keywords:
                if kw in summary_lower:
                    logger.warning(f"[HANDOFF] context_summary contained sensitive keyword '{kw}' — redacting.")
                    context_summary = "[Context redacted for safety — contains potentially sensitive data.]"
                    break

            # Fallback if empty
            if not context_summary or not context_summary.strip():
                context_summary = "The user is asking about government scheme information or eligibility."

            # Truncate to a reasonable length
            if len(context_summary) > 500:
                context_summary = context_summary[:500] + "..."

            # Build the specialist prompt with injected context
            specialist_instructions = SPECIALIST_PROMPT.replace("{context}", context_summary)

            specialist = GovernmentSchemeSpecialist(
                instructions=specialist_instructions,
            )

            # Change the LLM/Agent brain to the specialist
            session = context.session
            session.update_agent(specialist)
            
            context.userdata["task_type"] = "Scheme Eligibility"
            logger.info("[ARTHASATHI] SPECIALIST ACTIVE → TRUE — specialist is now responding")

            # Interrupt any currently playing speech, then have Pooja introduce herself.
            # update_agent() is synchronous — specialist is already active when say() fires.
            session.interrupt()
            session.say(
                "Hello, my name is Pooja, and I am the Government Scheme Specialist. "
                "I'll help you with the scheme eligibility and details.",
                allow_interruptions=False,
            )

            # Return empty so the main LLM does NOT generate any additional text after the handoff.
            return ""

        except Exception as e:
            logger.error(f"[HANDOFF-ERROR] Handoff to specialist failed: {e}", exc_info=True)
            return (
                "Handoff failed. Tell the user: 'I'm unable to connect you to the specialist "
                "right now, but I can still help with the information I have.' Then continue "
                "helping the user directly using existing scheme knowledge."
            )


# =============================================================
# Day 9: Government Scheme Specialist Agent
# =============================================================
# A genuinely separate Agent subclass. Uses the same TTS voice
# as the main agent but has a distinct persona ('Pooja').
# Reuses existing check_scheme_eligibility logic
# (same schemes_data.SCHEMES dataset) and existing create_escalation
# (same Day 7 escalation system). Does NOT duplicate databases,
# scheme datasets, or Discord webhook calls.
# =============================================================

class GovernmentSchemeSpecialist(Agent):
    """Government Scheme Specialist agent for Arthasathi (Day 9).

    Handles only government-scheme related questions. Uses the existing
    Day 5 scheme eligibility data and Day 7 escalation system without
    duplication. The specialist's TTS voice is identical to the main
    agent's voice.
    """

    def __init__(self, instructions: str) -> None:
        super().__init__(instructions=instructions)

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
        """Check government scheme eligibility using the existing Day 5 scheme dataset.
        Call after collecting the required details from the user.
        Do NOT call with guessed or missing critical values.

        Args:
            scheme_name: Internal name of the scheme (e.g. 'pm_awas_yojana')
            annual_income: The user's annual household income in INR.
            owns_pucca_house: Whether the user owns a permanent (pucca) house.
            age: The user's age in years.
            is_farmer: Whether the user is a farmer.
            has_bank_account: Whether the user has a bank account.
            is_bpl_or_poor: Whether the user belongs to BPL category.
            has_existing_lpg_connection: Whether the user already has an LPG connection.
            applicant_is_female: Whether the primary applicant is female.
            is_indian_citizen: Whether the user is an Indian citizen.
        """
        logger.info(f"[SPECIALIST-TOOL] check_scheme_eligibility called for scheme={scheme_name}")
        context.userdata["task_type"] = "Scheme Eligibility"
        # Delegate entirely to the existing Day 5 eligibility logic
        try:
            from schemes_data import SCHEMES

            norm_name = scheme_name.lower().replace(" ", "_")
            if norm_name not in SCHEMES:
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

            if "max_annual_income" in criteria:
                if annual_income is None:
                    missing_fields.append("annual household income")
                elif annual_income > criteria["max_annual_income"]:
                    eligibility_status = "not eligible"
                    reasons.append(f"annual income ({annual_income}) exceeds the limit of {criteria['max_annual_income']}")

            if "must_not_own_pucca_house" in criteria:
                if owns_pucca_house is None:
                    missing_fields.append("whether they own a pucca (permanent) house")
                elif owns_pucca_house:
                    eligibility_status = "not eligible"
                    reasons.append("applicant already owns a pucca house")

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
            logger.error(f"[SPECIALIST-TOOL-ERROR] check_scheme_eligibility failed: {e}", exc_info=True)
            return "An error occurred while checking eligibility. Please ask the user for their relevant details again or advise them to verify eligibility at their bank or official portal."

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
        """Escalate to a human agent using the existing Day 7 escalation system.
        Call this ONLY after (a) the situation genuinely needs human help
        (fraud in progress or decisions needing human authority), AND (b)
        asking the caller for explicit permission to share their information.
        The summary must NEVER include OTPs, PINs, passwords, account numbers,
        card numbers, Aadhaar/PAN numbers, or other sensitive credentials.
        """
        user_id = context.userdata.get("user_id", "unknown")
        logger.info(f"[SPECIALIST-TOOL] create_escalation invoked for user_id={user_id}, urgency={urgency}")
        context.userdata["task_type"] = "Human Escalation"
        try:
            # Reuse the existing Day 7 escalation system — no duplication
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
            logger.error(f"[SPECIALIST-TOOL-ERROR] create_escalation failed: {e}", exc_info=True)
            return "An error occurred while escalating. Please advise the user to contact the helpline directly."

    @function_tool
    async def mark_call_completed(self, context: RunContext, reason: str, successful: bool) -> str:
        """Call this when the user's scheme question has been fully resolved.
        Args:
            reason: A short summary of why the call was marked completed.
            successful: True if the user's request was successfully resolved.
        """
        logger.info(f"[SPECIALIST-TOOL] mark_call_completed: {reason} (Success={successful})")
        context.userdata["call_success"] = successful
        context.userdata["outcome_reason"] = reason
        return "Call marked as completed. You may now give a natural closing response."


server = AgentServer()


def prewarm(proc: JobProcess):
    # Load VAD with aggressive silence detection (0.3s) for fast end-of-speech detection
    # This is synchronous by design — it runs in a subprocess before the event loop starts
    proc.userdata["vad"] = silero.VAD.load(
        min_silence_duration=0.5, # Increased from 0.15s to 0.5s to allow natural breathing/pauses
        activation_threshold=0.45,
    )
    logger.info("VAD model prewarmed successfully (min_silence_duration=0.5s)")


server.setup_fnc = prewarm


@server.rtc_session(agent_name="murf-agent")
async def my_agent(ctx: JobContext):
    ctx.log_context_fields = {
        "room": ctx.room.name,
    }

    # -------------------------------------------------------------------------
    # Pipeline setup — optimized for minimum latency
    # -------------------------------------------------------------------------
    # Initialize Day 8 Analytics state
    session = AgentSession(
        userdata={"call_success": False},
        # STT: Deepgram Nova-3
        stt=deepgram.STT(
            model="nova-3",
            language="multi",
            interim_results=True,
            no_delay=True,
            endpointing_ms=500,  # Increased from 150ms to 500ms to prevent premature STT cutoff
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
            tokenizer=tokenize.basic.SentenceTokenizer(min_sentence_len=15), # Increased from 2 to 15 to prevent chunking
        ),

        turn_detection=MultilingualModel(),
        vad=ctx.proc.userdata["vad"],
        preemptive_generation=False,
        # Balanced endpointing delays for reliable response initiation
        min_endpointing_delay=0.6,
        max_endpointing_delay=1.2,
        # Interruption settings
        min_interruption_duration=0.8, # Increased to 0.8s to avoid interrupting on short breaths/noises
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
            _pipeline_t0["user_finished_speaking"] = time.perf_counter()

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
            t_finished = _pipeline_t0.get("user_finished_speaking")
            if t_finished and "first_agent_response_latency_ms" not in session.userdata:
                latency = int((time.perf_counter() - t_finished) * 1000)
                session.userdata["first_agent_response_latency_ms"] = latency
                logger.info(f"[ANALYTICS] First response latency: {latency} ms")

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
    
    # Day 8 Analytics Tracking
    from datetime import datetime, timezone
    import uuid
    call_id = f"CALL-{uuid.uuid4().hex[:8].upper()}"
    started_at = datetime.now(timezone.utc).isoformat()

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


    # Fix for Day 8 Lifecycle: Wait for actual disconnection instead of blocking forever
    call_ended = asyncio.Event()
    
    @ctx.room.on("participant_disconnected")
    def on_participant_disconnected(p: rtc.RemoteParticipant):
        if p.identity == caller_id:
            logger.info("Caller disconnected, ending job cleanly.")
            call_ended.set()

    @ctx.room.on("disconnected")
    def on_disconnected():
        logger.info("Room disconnected, ending job cleanly.")
        call_ended.set()

    logger.info("KEEPING JOB ALIVE")
    try:
        await call_ended.wait()
    finally:
        # Day 8 Analytics: Record exactly one row when the call ends
        if not session.userdata.get("analytics_finalized"):
            session.userdata["analytics_finalized"] = True
            
            from database import log_analytics
            from datetime import datetime, timezone
            
            ended_at_dt = datetime.now(timezone.utc)
            ended_at = ended_at_dt.isoformat()
            started_at_dt = datetime.fromisoformat(started_at)
            duration = int((ended_at_dt - started_at_dt).total_seconds())
            
            channel = "outbound" if is_outbound else "browser"
            outcome = "FAILED"
            success_reason = "Abrupt disconnect or unresolved"
            
            if "call_success" in session.userdata:
                outcome = "SUCCESS" if session.userdata["call_success"] else "FAILED"
                success_reason = session.userdata.get("outcome_reason", "")
                
            task_type = session.userdata.get("task_type", "General Query")
            latency = session.userdata.get("first_agent_response_latency_ms")
            
            # Extract language safely if known, else default to English
            # Since language is implicitly handled by the LLM in Prompt.py, we just record Unknown unless explicitly detected.
            language = session.userdata.get("language", "Unknown")
            
            log_analytics(call_id, caller_id, started_at, ended_at, channel, outcome, duration, language, success_reason, task_type, latency)
            logger.info(f"SESSION ENDED (Outcome: {outcome})")


# Day 8 Analytics API (Runs in background, zero dependencies)
import threading
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from database import _get_connection

class AnalyticsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        total = 0; success = 0; failed = 0
        history = []
        task_stats = {}
        try:
            with _get_connection() as conn:
                if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='call_analytics'").fetchone():
                    total = conn.execute("SELECT COUNT(*) FROM call_analytics").fetchone()[0]
                    success = conn.execute("SELECT COUNT(*) FROM call_analytics WHERE outcome = 'SUCCESS'").fetchone()[0]
                    failed = conn.execute("SELECT COUNT(*) FROM call_analytics WHERE outcome = 'FAILED'").fetchone()[0]
                    
                    # Fetch recent history
                    rows = conn.execute("SELECT started_at, duration_seconds, channel, language, task_type, outcome, success_reason FROM call_analytics ORDER BY id DESC LIMIT 20").fetchall()
                    for r in rows:
                        history.append({
                            "started_at": r[0],
                            "duration_seconds": r[1],
                            "channel": r[2],
                            "language": r[3],
                            "task_type": r[4],
                            "outcome": r[5],
                            "success_reason": r[6]
                        })
                        
                    # Fetch task stats
                    task_rows = conn.execute("SELECT task_type, COUNT(*) FROM call_analytics GROUP BY task_type").fetchall()
                    for r in task_rows:
                        task_stats[r[0] or "Unknown"] = r[1]
                        
        except Exception as e:
            logger.error(f"Error querying analytics DB for API: {e}")
            
        rate = round((success / total * 100), 1) if total > 0 else 0
        data = {
            "total_calls": total, 
            "successful_calls": success, 
            "failed_calls": failed,
            "success_rate": rate,
            "history": history,
            "task_stats": task_stats
        }
        self.wfile.write(json.dumps(data).encode())
        
    def log_message(self, format, *args):
        pass # Suppress logs to keep terminal clean

def _start_analytics_server():
    try:
        # Try port 8080
        server = HTTPServer(('127.0.0.1', 8080), AnalyticsHandler)
        logger.info("Day 8 Analytics API running on http://127.0.0.1:8080")
        server.serve_forever()
    except Exception as e:
        logger.error(f"Failed to start Analytics API: {e}")

threading.Thread(target=_start_analytics_server, daemon=True).start()

if __name__ == "__main__":
    cli.run_app(server)
