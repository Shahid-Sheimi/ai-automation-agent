import logging
import re
from typing import Any

from src.config import settings
from src.schemas import TrackingPackageRequest
from src.utils import (
    get_interactions_from_db,
    get_langfuse_client,
    get_latest_tracking_info,
    get_openai_client,
    save_interaction_to_db,
)

# Access the clients
openai_client = get_openai_client()
langfuse_client = get_langfuse_client()


def extract_tracking_code(text: str) -> str | None:
    """
    Extract a UUID or PKGxxxxxx tracking code directly from raw text.
    This runs BEFORE the LLM to catch codes the LLM might miss or strip.

    Args:
        text (str): Raw user message.

    Returns:
        str | None: Extracted tracking code or None.
    """
    # Match UUID format (order_id)
    uuid_pattern = r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}'
    uuid_match = re.search(uuid_pattern, text)
    if uuid_match:
        return uuid_match.group()

    # Match PKGxxxxxx format (package_tracking)
    pkg_pattern = r'PKG\d{6,}'
    pkg_match = re.search(pkg_pattern, text, re.IGNORECASE)
    if pkg_match:
        return pkg_match.group().upper()

    return None


def process_tracking_package_request(
    user_input: str, client: Any = openai_client, model_name: str = settings.MODEL_NAME
) -> str:
    """Process and track package requests using LLM and database queries.

    Args:
        user_input (str): User's query containing tracking information.
        client (Any): OpenAI client for LLM interaction.
        model_name (str): Model name for LLM processing.

    Returns:
        str: A formatted tracking response message or an error message.
    """
    logging.info("Processing tracking request.")

    # Retrieve last 5 interactions from the database
    interactions = get_interactions_from_db()

    try:
        # -------------------------------------------------------
        # Step 1: Try extracting tracking code directly from text
        # (handles UUID order IDs which LLM prompt was missing)
        # -------------------------------------------------------
        tracking_code = extract_tracking_code(user_input)
        logging.info(f"Regex extracted tracking code: {tracking_code}")

        # -------------------------------------------------------
        # Step 2: If regex didn't find it, fall back to LLM
        # -------------------------------------------------------
        if not tracking_code:
            completion = client.beta.chat.completions.parse(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Extract the tracking code from the user message. "
                            "It can be either:\n"
                            "1. A UUID format like: a1a98641-7d3f-4f59-8fd9-73044341f20a\n"
                            "2. A PKG code like: PKG123456\n"
                            "Return only the tracking code, nothing else."
                        ),
                    },
                    {
                        "role": "system",
                        "content": (
                            "These are the last five messages of previous conversation "
                            "but you do not need to use these if not relevant:\n"
                            + "\n".join(
                                [
                                    f"User: {interaction[0]}\nAssistant: {interaction[1]}"
                                    for interaction in interactions
                                ]
                            )
                            + "\n\n(End of previous conversation)"
                        ),
                    },
                    {"role": "user", "content": f"Current conversation: {user_input}"},
                ],
                response_format=TrackingPackageRequest,
            )

            result = completion.choices[0].message.parsed
            tracking_code = result.tracking_code
            logging.info(f"LLM extracted tracking code: {tracking_code}")

            # Save LLM interaction
            save_interaction_to_db(question=user_input, response=result.description)
        else:
            # Save interaction with regex-extracted code
            save_interaction_to_db(question=user_input, response=tracking_code)

        print(f"Final tracking_code: {tracking_code}")

        # -------------------------------------------------------
        # Step 3: Fetch tracking info from DB
        # -------------------------------------------------------
        output_query = get_latest_tracking_info(tracking_code)
        print(f"DB result: {output_query}")

        # -------------------------------------------------------
        # Step 4: Return formatted response
        # -------------------------------------------------------
        if output_query:
            response = (
                f"📦 *Package Tracking Details*\n\n"
                f"🔍 *Tracking Code:* {tracking_code}\n"
                f"🚀 *Status:* {output_query['status']}\n"
                f"📍 *Location:* {output_query['location']}\n"
                f"📦 *Shipping Type:* {output_query['shipping_type']}\n"
                f"🕒 *Last Update:* {output_query['last_update']}\n\n"
                f"Check back for real-time updates!"
            )
        else:
            response = (
                "❌ *Tracking Not Found*\n\n"
                f"No record found for: {tracking_code}\n"
                "Please double-check the code and try again."
            )

        logging.info("Tracking response generated successfully.")
        return response

    except Exception as e:
        logging.error(f"Error processing tracking request: {e}", exc_info=True)
        return "⚠️ An error occurred while processing your request. Please try again later."