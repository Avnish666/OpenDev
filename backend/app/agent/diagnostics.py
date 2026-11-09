"""Development-only metadata. Never serialize exception strings or model data."""
import logging

logger = logging.getLogger(__name__)
STAGES = frozenset({'provider_setup', 'availability', 'context_budget', 'model_request',
    'tool_selection', 'tool_validation', 'tool_execution', 'tool_result',
    'answer_validation', 'turn_budget'})
CATEGORIES = frozenset({'provider_unavailable', 'provider_timeout', 'provider_http_error',
    'provider_response_too_large', 'provider_invalid_json', 'provider_invalid_message',
    'provider_incomplete_response', 'model_output_truncated', 'tool_model_unavailable',
    'missing_tool_calls', 'invalid_tool_arguments', 'unknown_tool', 'repeated_tool_call',
    'tool_call_budget', 'tool_result_budget', 'context_budget', 'turn_budget',
    'model_timeout', 'tool_timeout', 'request_timeout', 'database_error',
    'tool_access_rejected', 'malformed_structured_output', 'invalid_answer_schema',
    'invalid_citation_or_fact', 'invalid_model_output'})


def record_failure(failures, stage, category, turn):
    from app.core.config import settings
    if settings.APP_ENV != 'development':
        return
    entry = {'stage': stage if stage in STAGES else 'model_request',
             'category': category if category in CATEGORIES else 'invalid_model_output',
             'turn': max(0, min(int(turn), 6))}
    failures.append(entry)
    # Fixed format + finite codes only: no question, IDs, arguments, evidence,
    # endpoint, prompt, raw model output, exception details or traceback.
    logger.info('Agent validation failure stage=%s category=%s turn=%d',
                entry['stage'], entry['category'], entry['turn'])
