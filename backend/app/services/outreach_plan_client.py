import concurrent.futures
import logging
from datetime import datetime, timezone

from app.core.config import settings
from app.schemas.outreach_plan import OutreachPlanCandidate, OutreachPlanResponse
from app.services.outreach_plan_agent import generate_plan

logger = logging.getLogger(__name__)

DEFAULT_AGENT_TIMEOUT_SECONDS = 90.0


class OutreachAgentUnavailable(Exception):
    pass


def _run_agent(candidate_payload: list[dict], owner_id: object) -> dict:
    """Run the agent with a hard timeout so a hung Bedrock call cannot hold
    a request worker indefinitely."""
    timeout = getattr(
        settings, "outreach_agent_timeout_seconds", DEFAULT_AGENT_TIMEOUT_SECONDS
    )
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    try:
        future = pool.submit(generate_plan, candidate_payload, owner_id)
        try:
            return future.result(timeout=timeout)
        except TimeoutError:
            logger.warning("Outreach agent timed out after %s seconds.", timeout)
            raise OutreachAgentUnavailable() from None
    finally:
        pool.shutdown(wait=False, cancel_futures=True)


def invoke_outreach_agent(
    candidates: list[OutreachPlanCandidate],
    owner_id: object = None,
) -> OutreachPlanResponse:
    if not settings.bedrock_model_id:
        raise OutreachAgentUnavailable()

    authorized_student_ids = {str(candidate.student_id) for candidate in candidates}
    candidate_payload = [
        candidate.model_dump(mode="json") for candidate in candidates
    ]
    try:
        payload = _run_agent(candidate_payload, owner_id)
        response = OutreachPlanResponse(
            generated_at=datetime.now(timezone.utc),
            source="agent",
            items=payload["items"],
        )
    except OutreachAgentUnavailable:
        raise
    except Exception:
        logger.warning("Outreach agent failed.", exc_info=True)
        raise OutreachAgentUnavailable() from None

    if any(
        str(item.student_id) not in authorized_student_ids for item in response.items
    ):
        logger.error(
            "Outreach agent returned a student outside the authorized "
            "candidate set; rejecting the plan."
        )
        raise OutreachAgentUnavailable()
    return response
