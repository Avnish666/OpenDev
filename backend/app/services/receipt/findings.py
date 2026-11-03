"""Read-only deterministic comparisons. All flags require human review."""
from sqlalchemy import select, func
from app.models.expense import Expense
from app.models.expense_document import ExpenseDocument
from app.models.receipt_extraction import ReceiptExtraction
from app.models.project import Project
from app.schemas.extraction import Finding
from app.services import expenses


def snapshot(expense):
    return {key:(getattr(expense,key).isoformat() if key=='expense_date' else getattr(expense,key)) for key in ['id','project_id','category','amount_cents','currency','vendor','expense_date']}


def normalize(value):
    return ' '.join(value.strip().casefold().split())


def detect(db, doc, expense, receipt):
    findings=[]
    def add(code,reported,extracted,explanation,reference,severity='info'):
        findings.append(Finding(finding_code=code,severity=severity,reported_value=reported,extracted_value=extracted,explanation=explanation,evidence_reference=reference).model_dump(mode='json'))
    for name in ['vendor_name','document_date','currency','total_cents']:
        field=getattr(receipt,name)
        if field.value is None:
            add('MISSING_'+name.upper(),None,None,'Field could not be identified reliably; review the original document.',{'field':name})
    for field_name,reported in [('total_cents',expense.amount_cents),('currency',expense.currency),('vendor_name',expense.vendor),('document_date',expense.expense_date.isoformat())]:
        field=getattr(receipt,field_name)
        value=field.value.isoformat() if field_name=='document_date' and field.value is not None else field.value
        if value is None: continue
        same=normalize(str(reported))==normalize(str(value))
        if not same:
            code={'total_cents':'AMOUNT_MISMATCH','currency':'CURRENCY_MISMATCH','vendor_name':'VENDOR_MISMATCH','document_date':'DATE_MISMATCH'}[field_name]
            add(code,reported,value,f'Reported and extracted values differ ({field.confidence} extraction confidence). This is not proof of fraud.',{'field':field_name,'sources':[e.model_dump() for e in field.evidence]},'warning' if field.confidence=='high' else 'info')
    subtotal,tax,total=receipt.subtotal_cents,receipt.tax_cents,receipt.total_cents
    if all(field.value is not None for field in [subtotal,tax,total]):
        calculated=subtotal.value+tax.value-(receipt.discount_cents.value or 0)
        if calculated!=total.value:
            add('POSSIBLE_ARITHMETIC_INCONSISTENCY',calculated,total.value,'Subtotal plus tax minus identified discounts differs exactly from total. Unextracted fees or discounts may explain the difference.',{'fields':['subtotal_cents','tax_cents','discount_cents','total_cents']},'warning' if all(f.confidence=='high' for f in [subtotal,tax,total]) else 'info')
    duplicates=db.scalar(select(func.count()).select_from(ExpenseDocument).join(Expense).where(Expense.project_id==expense.project_id,ExpenseDocument.sha256_hash==doc.sha256_hash,ExpenseDocument.id!=doc.id))
    if duplicates:
        add('DUPLICATE_FILE',None,duplicates,'Identical file content exists elsewhere in this project; duplication does not establish duplicate payment.',{'kind':'project_file_hash'})
    if receipt.invoice_number.value and receipt.vendor_name.value:
        from app.services.receipt.provider import EXTRACTION_VERSION
        others=db.execute(select(ReceiptExtraction,ExpenseDocument.expense_id).join(ExpenseDocument).join(Expense).where(Expense.project_id==expense.project_id,ReceiptExtraction.extraction_status=='completed',ReceiptExtraction.extraction_version.in_(['local-rules-v1',EXTRACTION_VERSION]),ExpenseDocument.expense_id!=expense.id)).all()
        for other,other_expense in others:
            value=other.extracted_json or {}
            if normalize(str(value.get('invoice_number',{}).get('value','')))==normalize(receipt.invoice_number.value) and normalize(str(value.get('vendor_name',{}).get('value','')))==normalize(receipt.vendor_name.value):
                add('DUPLICATE_INVOICE_NUMBER',None,receipt.invoice_number.value,'The same vendor/invoice identifier appears on another expense in this project. Human review is required.',{'field':'invoice_number','other_expense_id':other_expense},'warning' if receipt.invoice_number.confidence=='high' and receipt.vendor_name.confidence=='high' else 'info')
                break
    summary=expenses.summary(db,db.get(Project,expense.project_id))
    category=next((c for c in summary['categories'] if c['category']==expense.category.strip().casefold()),None)
    if category and category['overspend_cents']>0:
        add('CATEGORY_BUDGET_OVERRUN',category['allocated_cents'],category['reported_spending_cents'],'Published reported expenses exceed the category allocation. Draft expenses are not included; these reports do not verify actual transfers.',{'kind':'project_budget','category':category['category']},'warning')
    return findings
