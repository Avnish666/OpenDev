from datetime import date
from typing import Literal
from pydantic import BaseModel
class DashboardDimensions(BaseModel):
    discrepancy: Literal['all','with','without']='all'
    milestone_status: Literal['all','planned','in_progress','submitted_for_review','delivered','cancelled']='all'
    planned_from: date|None=None
    planned_to: date|None=None
    delivery: Literal['all','delivered','undelivered']='all'
    outcome: Literal['all','on_time','late','unknown','not_currently_delivered']='all'
    github_category: Literal['all','issue','pull_request','milestone','commit']='all'
    github_freshness: Literal['all','stale','current']='all'
