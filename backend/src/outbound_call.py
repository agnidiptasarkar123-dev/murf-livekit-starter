"""
outbound_call.py — Day 6 feature: Proactive Outbound SIP Calling

This script demonstrates how to trigger an outbound SIP call using LiveKit.
It connects the call to the same Assistant agent defined in agent.py by
dispatching the call to a LiveKit room where the agent is (or will be) listening.

NOTE: This script supports dialing a SIP URI directly (e.g., sip:username@sip.linphone.org)
using a free Linphone SIP-to-SIP call for testing/demo purposes, rather than a PSTN number
through Twilio, since Twilio account access was blocked during development. 
For production use, a PSTN-capable trunk (Twilio or similar) would be needed to call real phone numbers.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import uuid

from dotenv import load_dotenv
from livekit import api

from database import get_user

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("outbound_call")

load_dotenv(".env.local")

async def make_outbound_call(phone_number: str, reason: str, caller_id: str):
    # Verify we aren't calling someone who opted out
    user_record = get_user(caller_id)
    if user_record and user_record.get("do_not_call"):
        logger.warning(f"Aborting call: user {caller_id} has opted out of outbound calls.")
        return

    trunk_id = os.getenv("LIVEKIT_SIP_TRUNK_ID")
    if not trunk_id:
        logger.error("LIVEKIT_SIP_TRUNK_ID is not set in .env.local")
        sys.exit(1)

    participant_identity = caller_id

    # 1. Create a unique room name for EVERY call
    safe_target = phone_number.replace(':', '-').replace('@', '-').strip('+')
    room_name = f"outbound-call-{safe_target}-{uuid.uuid4().hex[:6]}"

    room_metadata = json.dumps({
        "outbound": True,
        "reason": reason
    })

    lkapi = api.LiveKitAPI()
    try:
        logger.info(f"Creating room {room_name}...")
        
        # Create the room explicitly first
        await lkapi.room.create_room(
            api.CreateRoomRequest(
                name=room_name,
                empty_timeout=5 * 60,
                metadata=room_metadata
            )
        )
        
        # 2. Create the agent dispatch FIRST
        logger.info(f"DISPATCH CREATED: Dispatching agent 'murf-agent' to room {room_name}...")
        await lkapi.agent_dispatch.create_dispatch(
            api.CreateAgentDispatchRequest(
                agent_name="murf-agent",
                room=room_name,
                metadata=room_metadata,
            )
        )
        
        # 3. Immediately create the SIP participant in that SAME room
        logger.info(f"SIP DIAL START: Dialing {phone_number} via trunk {trunk_id}...")
        sip_participant = await lkapi.sip.create_sip_participant(
            api.CreateSIPParticipantRequest(
                sip_trunk_id=trunk_id,
                sip_call_to=phone_number,
                room_name=room_name,
                participant_identity=participant_identity,
                media_encryption=api.SIPMediaEncryption.SIP_MEDIA_ENCRYPT_ALLOW
            )
        )
        
        _part_id = getattr(sip_participant, 'sip_participant_id', getattr(sip_participant, 'participant_id', getattr(sip_participant, 'id', 'unknown')))
        logger.info(f"SIP PARTICIPANT CREATED: ID {_part_id}")
        logger.info(f"Agent should now connect to room: {room_name}")
        
        # 4. Keep the Python script alive for a short period only if necessary
        logger.info("Keeping script alive for 15 seconds to ensure dispatch propagates...")
        await asyncio.sleep(15)
        logger.info("Outbound script finished.")

    except Exception as e:
        import traceback
        logger.error("Failed to initiate outbound call. Full traceback below:")
        traceback.print_exc()
    finally:
        await lkapi.aclose()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Trigger an outbound call via LiveKit SIP")
    parser.add_argument("phone_number", help="Target phone number (E.164) or SIP URI")
    parser.add_argument("reason", help="Reason for calling, spoken by the agent")
    parser.add_argument("--caller-id", default="outbound_user", help="Caller ID to link with memory database")
    
    args = parser.parse_args()
    
    asyncio.run(make_outbound_call(args.phone_number, args.reason, args.caller_id))
