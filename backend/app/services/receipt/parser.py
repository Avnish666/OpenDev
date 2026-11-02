"""Conservative English-language rules. Receipt text is data, never instructions."""
import re
from datetime import date
from decimal import Decimal
from app.schemas.extraction import Evidence, ExtractedReceipt, Observed

# Require two decimal places and complete numeric boundaries; never round.
MONEY = re.compile(r'(?<![\d.,-])(\d{1,12}(?:,\d{3})*\.\d{2})(?![\d.,])')
LABELS = {
    'total_cents': r'^(?:grand\s+total|invoice\s+total|total)(?:\s*[:=]|\s+)(?!due\b|paid\b|tax\b)',
    'subtotal_cents': r'^sub\s*total\b',
    'tax_cents': r'^(?:tax|vat|sales tax)\b',
    'discount_cents': r'^discount\b',
    'amount_paid_cents': r'^(?:amount paid|paid amount)\b',
    'amount_due_cents': r'^(?:amount due|balance due|total due)\b',
    'previous_balance_cents': r'^previous balance\b',
}


def observed(value, line, strong=True):
    quality = line.get('quality', 100)
    confidence = 'high' if strong and quality >= 85 else 'medium' if quality >= 65 else 'low'
    evidence = Evidence(page=line['page'], snippet=line['text'][:160], bbox=line.get('bbox'), coordinates=line.get('coordinates'))
    return {'value':value, 'confidence':confidence, 'evidence':[evidence.model_dump()]}


def parse(lines, method, pages):
    result = ExtractedReceipt(extraction_method=method, pages_processed=pages).model_dump()
    candidates = {key:[] for key in [*LABELS, 'vendor_name','invoice_number','document_date','currency','payment_status']}
    for line in lines:
        text = line['text'].strip()
        lower = text.casefold()
        # Currency symbols such as $ alone are deliberately not interpreted as USD.
        currencies = set(re.findall(r'\b(USD|EUR|GBP|CAD|AUD|CHF)\b', text.upper()))
        if not (re.match(r'^currency\s*:',text,re.I) or MONEY.search(text)):
            currencies=set()
        for code in sorted(currencies):
            candidates['currency'].append(observed(code,line))
        amounts = MONEY.findall(text)
        for key, pattern in LABELS.items():
            if re.search(pattern, lower) and len(amounts) == 1:
                cents = int(Decimal(amounts[0].replace(',','')) * 100)
                candidates[key].append(observed(cents,line))
        vendor = re.match(r'^(?:vendor|merchant|supplier|sold by)\s*:\s*(.{1,120})$',text,re.I)
        if vendor: candidates['vendor_name'].append(observed(vendor[1].strip(),line))
        invoice = re.match(r'^invoice\s*(?:number|no\.?|id|#)?\s*[:#]\s*([A-Za-z0-9][A-Za-z0-9_./-]{0,79})$',text,re.I)
        if invoice: candidates['invoice_number'].append(observed(invoice[1],line))
        dated = re.match(r'^(?:invoice date|document date|date)\s*:\s*(\d{4}-\d{2}-\d{2})$',text,re.I)
        if dated:
            try: candidates['document_date'].append(observed(date.fromisoformat(dated[1]).isoformat(),line))
            except ValueError: pass
        payment = re.match(r'^(?:payment status\s*:\s*)?(paid|unpaid|partially paid)$',text,re.I)
        if payment: candidates['payment_status'].append(observed(payment[1].lower().replace(' ','_'),line,strong=False))
        # Only explicitly labelled item rows are recognized; arbitrary address/total lines are not items.
        item = re.match(r'^item\s*:\s*(.+?)\s+(?:USD\s*)?(\d{1,12}\.\d{2})$',text,re.I)
        if item and len(result['line_items']) < 100:
            field = observed(int(Decimal(item[2])*100),line,strong=False)
            result['line_items'].append({'description':item[1][:160], 'amount_cents':field['value'],'confidence':field['confidence'],'evidence':field['evidence'][0]})
    for key, values in candidates.items():
        distinct = {str(v['value']) for v in values}
        if len(distinct) == 1:
            # Prefer better OCR evidence without pretending that agreement proves truth.
            rank = {'high':3,'medium':2,'low':1}
            result[key] = max(values,key=lambda value:rank[value['confidence']])
        elif len(distinct) > 1:
            result['uncertainties'].append('ambiguous_' + key)
    if not lines: result['uncertainties'].append('no_readable_text')
    return ExtractedReceipt.model_validate(result)
