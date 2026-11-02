from types import SimpleNamespace
from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session
from app.core.auth import get_current_user, get_optional_user
from app.core.database import get_db
from app.models.user import User
from app.models.expense import Expense
from app.routers.auth import require_trusted_origin
from app.routers.expenses import RecordID
from app.schemas.accountability import AccountabilitySnapshot, BudgetVarianceResponse, ExpenseVerification, ReviewCreate, ReviewResponse
from app.services import accountability, expenses

router=APIRouter(prefix='/api',tags=['Financial accountability'])


def actor(user):
    return SimpleNamespace(id=user.id) if user else None


def no_cache(response):
    response.headers['Cache-Control']='no-store'
    response.headers['Referrer-Policy']='no-referrer'


@router.get('/projects/{project_id}/accountability',response_model=AccountabilitySnapshot)
def project_accountability(project_id: RecordID,response: Response,db: Session=Depends(get_db),user: User | None=Depends(get_optional_user)):
    no_cache(response)
    caller=actor(user)
    with accountability.read_snapshot(db) as reader:
        project=expenses.project_for_expenses(reader,project_id,caller)
        return accountability.snapshot(reader,project,caller)


@router.get('/projects/{project_id}/budget-variance',response_model=BudgetVarianceResponse)
def budget_variance(project_id: RecordID,response: Response,db: Session=Depends(get_db),user: User | None=Depends(get_optional_user)):
    no_cache(response);caller=actor(user)
    with accountability.read_snapshot(db) as reader:
        project=expenses.project_for_expenses(reader,project_id,caller)
        result=accountability.snapshot(reader,project,caller)
        return dict(project_id=project.id,currency=project.currency,categories=result['budget_variance'],calculated_at=result['calculated_at'])


@router.get('/expenses/{expense_id}/verification',response_model=ExpenseVerification)
def expense_verification(expense_id: RecordID,response: Response,db: Session=Depends(get_db),user: User | None=Depends(get_optional_user)):
    no_cache(response);caller=actor(user)
    with accountability.read_snapshot(db) as reader:
        expense=expenses.get(reader,expense_id,caller)
        return accountability.verification(reader,expense,caller)


@router.post('/extraction-findings/{finding_id}/review',response_model=ReviewResponse,dependencies=[Depends(require_trusted_origin)])
def review_finding(finding_id: str,data: ReviewCreate,response: Response,db: Session=Depends(get_db),user: User=Depends(get_current_user)):
    no_cache(response)
    return accountability.review(db,finding_id,user,data)


@router.get('/expenses/{expense_id}/review-history',response_model=list[ReviewResponse])
def expense_review_history(expense_id: RecordID,response: Response,db: Session=Depends(get_db),user: User=Depends(get_current_user)):
    no_cache(response)
    expense=expenses.get(db,expense_id,user,write=True)
    return accountability.review_history(db,expense,user)
