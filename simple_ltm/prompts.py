from datetime import datetime, timezone

from meta_prompts import META_CONTEXT, DOWNSTREAM_USE_CASES, TOOL_INSTRUCTIONS


# System prompt agent sees throughout conversation
def format_agent_system_prompt(existing_user_memory: str = "", tool_instructions: str = TOOL_INSTRUCTIONS, meta_context: str = META_CONTEXT, downstream_use_cases: str = DOWNSTREAM_USE_CASES):
    return f"""
    <meta_context>
    {meta_context}
    </meta_context>

    <downstream_use_cases>
    {downstream_use_cases}
    </downstream_use_cases>

    <tool_instructions>
    {tool_instructions}
    </tool_instructions>

    <existing_user_memory>
    {existing_user_memory}
    </existing_user_memory>    
    """


def format_memory_update_system_prompt(meta_context: str, downstream_use_cases: str):
    return f"""
    <meta_context>
    {meta_context}
    </meta_context>

    <downstream_use_cases>
    {downstream_use_cases}
    </downstream_use_cases>

    <instructions>
    Incorporate instructions and any new information to add, update, or delete information in the user's existing memory. The updated memory can be as long as it needs to be to capture all information that is likely to be valuable in future interactions.  
    If new information conflicts with old information, assume that the new information is correct and remove anything conflicting. Make absolutely sure not to remove any information that is likely to be valuable in the future.
    
    IMPORTANT: Write the updated memory from a first-person user perspective, using "I", "my", "me", etc. For example: "I have a dog named Max" not "The user has a dog named Max".
    
    Use temporal markers flexibly to capture time-related context:
    - [recorded:YYYY-MM-DD] - When information was mentioned to you
    - [since:YYYY-MM-DD] - When something started
    - [until:YYYY-MM-DD] - When something ended/will end
    - [on:YYYY-MM-DD] - For specific dates
    - [scheduled:YYYY-MM-DD] - For future events
    - [as_of:YYYY-MM-DD] - For information true at a specific time
    - [expires:YYYY-MM-DD] - When information becomes outdated
    - Combine markers as needed for clarity
    
    Examples:
    - "I work at Google [recorded:2025-01-30][since:2023-06-01]"
    - "I have a trip to Japan [recorded:2025-01-30][scheduled:2025-03-15 to 2025-03-25]"
    - "My dog Max is 5 years old [recorded:2025-01-30][as_of:2025-01-30]"
    - "I'm taking Spanish lessons [since:2024-09-01][until:2025-06-30]"
    - "My gym membership [expires:2025-12-31]"
    - "I graduated from MIT [on:2020-05-15]"
    </instructions>

    <current_datetime_utc>
    {datetime.now(timezone.utc).strftime("%B %d, %Y %H:%M:%S")}
    </current_date_utc>
"""


def format_update_prompt(existing_memory: str, new_info: str) -> str:
    """Create prompt for memory updates."""
    
    return f"""<existing_memory>
    {existing_memory if existing_memory else "(empty)"}
    </existing_memory>

    <new_information>
    {new_info}
    </new_information>

    <current_datetime_utc>
    {datetime.now(timezone.utc).strftime("%B %d, %Y %H:%M:%S")}
    </current_date_utc>
    
    <reminders>
    - Ensure NO valuable details are lost from the existing memory unless explicitly contradicted
    - Use temporal markers appropriately: [recorded:], [since:], [until:], [on:], [scheduled:], [as_of:], [expires:]
    - Always add [recorded:today's date] to new information
    - Update temporal markers when information changes (e.g., job change: add [until:] to old job, [since:] to new)
    - Keep historical information with proper markers rather than deleting
    - Use the current UTC datetime above for "today" in markers
    - Write everything from first-person perspective (I, my, me)
    - Be precise with dates when known, use month/year when day unknown, year when month unknown
    </reminders>
"""