from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

from app.database import get_db
from app.models.accounting import (
    Account, Voucher, TransactionLine, Supplier, SupplierInvoice,
    Customer, CustomerInvoice, UploadedDocument, CompanySetting,
    Department, Project, AuditLog, User, BankTransaction, SupportTicket, SubscriptionOrder
)
from app.api.auth import validate_norwegian_orgnr, validate_norwegian_national_id

router = APIRouter(prefix="/accounting", tags=["Archive, Reports, SAF-T & Compliance"])

SAFT_NS = "urn:StandardAuditFile-Taxation-Financial:NO"


# -------------------------------------------------------------
# 1. AVDELINGER & PROSJEKTER (DIMENSJONER)
# -------------------------------------------------------------

class DepartmentCreate(BaseModel):
    code: str
    name: str


class ProjectCreate(BaseModel):
    code: str
    name: str
    customer_name: Optional[str] = None
    budget: float = 0.0


def seed_default_dimensions(db: Session):
    if db.query(Department).count() == 0:
        for code, name in [
            ("ADM", "Administrasjon og ledelse"),
            ("SALG", "Salg og marked"),
            ("DRIFT", "Drift og produksjon"),
            ("IT", "IT og utvikling"),
        ]:
            db.add(Department(code=code, name=name))
    if db.query(Project).count() == 0:
        for code, name, cust, budget in [
            ("FELLES", "Felleskostnad / Drift", None, 0.0),
            ("PROJ-2026-01", "Kundeprosjekt Digitalisering 2026", "Nordic Tech Solutions AS", 250000.0),
            ("PROJ-2026-02", "Drifts- og vedlikeholdsavtale", "Fjord Logistics AS", 120000.0),
        ]:
            db.add(Project(code=code, name=name, customer_name=cust, budget=budget))
    db.commit()


@router.get("/dimensions")
def get_dimensions(db: Session = Depends(get_db)):
    depts = db.query(Department).filter(Department.is_active == True).order_by(Department.code).all()
    projs = db.query(Project).order_by(Project.code).all()
    return {
        "departments": [{"id": d.id, "code": d.code, "name": d.name} for d in depts],
        "projects": [
            {
                "id": p.id,
                "code": p.code,
                "name": p.name,
                "customer_name": p.customer_name,
                "budget": p.budget,
                "status": p.status,
            }
            for p in projs
        ],
    }


@router.post("/departments")
def create_department(d: DepartmentCreate, db: Session = Depends(get_db)):
    code = d.code.strip().upper()
    if db.query(Department).filter(Department.code == code).first():
        raise HTTPException(status_code=400, detail=f"Avdeling '{code}' finnes allerede.")
    row = Department(code=code, name=d.name.strip())
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"ok": True, "id": row.id, "code": row.code, "name": row.name}


@router.post("/projects")
def create_project(p: ProjectCreate, db: Session = Depends(get_db)):
    code = p.code.strip().upper()
    if db.query(Project).filter(Project.code == code).first():
        raise HTTPException(status_code=400, detail=f"Prosjekt '{code}' finnes allerede.")
    row = Project(code=code, name=p.name.strip(), customer_name=p.customer_name, budget=p.budget)
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"ok": True, "id": row.id, "code": row.code, "name": row.name}


# -------------------------------------------------------------
# 2. BILAGSARKIV (BOKFØRINGSLOVEN § 13 - 5 ÅRS OPPBEVARING)
# -------------------------------------------------------------

@router.get("/archive")
def get_voucher_archive(
    q: Optional[str] = None,
    department: Optional[str] = None,
    project: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Komplett søkbart bilagsarkiv som samler alle bokførte bilag, posteringer,
    tilhørende opplastede vedlegg (PDF/bilde) og lovpålagt 5-års oppbevaringsdato.
    """
    vouchers = db.query(Voucher).order_by(Voucher.voucher_number.desc()).all()
    docs_by_voucher = {
        d.voucher_id: d
        for d in db.query(UploadedDocument).filter(UploadedDocument.voucher_id != None).all()
    }
    accounts_map = {a.account_number: a.name for a in db.query(Account).all()}

    query_lower = (q or "").strip().lower()
    dept_filter = (department or "").strip().upper()
    proj_filter = (project or "").strip().upper()

    dt_from = datetime.fromisoformat(from_date) if from_date else None
    dt_to = datetime.fromisoformat(to_date) if to_date else None

    items = []
    for v in vouchers:
        if dt_from and v.date < dt_from:
            continue
        if dt_to and v.date > dt_to + timedelta(days=1):
            continue

        line_depts = {l.department_code for l in v.lines if l.department_code}
        if v.department_code:
            line_depts.add(v.department_code)
        line_projs = {l.project_code for l in v.lines if l.project_code}
        if v.project_code:
            line_projs.add(v.project_code)

        if dept_filter and dept_filter not in line_depts:
            continue
        if proj_filter and proj_filter not in line_projs:
            continue

        doc = docs_by_voucher.get(v.id)
        doc_url = v.source_document or (doc.file_path if doc else None)

        if query_lower:
            haystack = " ".join([
                str(v.voucher_number),
                v.description or "",
                doc.original_name if doc else "",
                " ".join(l.description or "" for l in v.lines),
                " ".join(str(l.account_number) for l in v.lines),
            ]).lower()
            if query_lower not in haystack:
                continue

        total_debit = round(sum(l.debit for l in v.lines), 2)
        total_credit = round(sum(l.credit for l in v.lines), 2)
        retention_until = f"{v.date.year + 5}-12-31" if v.date else None

        items.append({
            "id": v.id,
            "voucher_number": v.voucher_number,
            "date": v.date.isoformat() if v.date else None,
            "description": v.description,
            "status": v.status,
            "department_code": v.department_code or (next(iter(line_depts), None)),
            "project_code": v.project_code or (next(iter(line_projs), None)),
            "document_url": doc_url,
            "document_name": doc.original_name if doc else (v.source_document.split("/")[-1] if v.source_document else None),
            "document_type": doc.file_type if doc else None,
            "total_debit": total_debit,
            "total_credit": total_credit,
            "is_balanced": abs(total_debit - total_credit) < 0.01,
            "retention_until": retention_until,
            "lines": [
                {
                    "account_number": l.account_number,
                    "account_name": accounts_map.get(l.account_number, ""),
                    "description": l.description,
                    "debit": l.debit,
                    "credit": l.credit,
                    "department_code": l.department_code,
                    "project_code": l.project_code,
                }
                for l in v.lines
            ],
        })

    return {
        "total_vouchers": len(items),
        "with_attachments": sum(1 for i in items if i["document_url"]),
        "items": items,
    }


# -------------------------------------------------------------
# 3. UTVIDEDE RAPPORTER: SALDOBALANSE & PROSJEKT/AVDELING
# -------------------------------------------------------------

@router.get("/reports/trial-balance")
def get_trial_balance(db: Session = Depends(get_db)):
    """Saldobalanse (Trial Balance) for alle bokførte kontoer i NS 4102."""
    rows = (
        db.query(TransactionLine, Account)
        .join(Account, TransactionLine.account_number == Account.account_number)
        .all()
    )
    acc_map = {}
    for line, acc in rows:
        entry = acc_map.setdefault(
            acc.account_number,
            {
                "account_number": acc.account_number,
                "account_name": acc.name,
                "account_type": acc.account_type,
                "debit": 0.0,
                "credit": 0.0,
            },
        )
        entry["debit"] += line.debit
        entry["credit"] += line.credit

    lines = []
    tot_debit = 0.0
    tot_credit = 0.0
    for acc_no in sorted(acc_map.keys()):
        e = acc_map[acc_no]
        d = round(e["debit"], 2)
        c = round(e["credit"], 2)
        tot_debit += d
        tot_credit += c
        lines.append({
            "account_number": e["account_number"],
            "account_name": e["account_name"],
            "account_type": e["account_type"],
            "debit": d,
            "credit": c,
            "balance": round(d - c, 2),
        })

    tot_debit = round(tot_debit, 2)
    tot_credit = round(tot_credit, 2)
    return {
        "lines": lines,
        "total_debit": tot_debit,
        "total_credit": tot_credit,
        "is_balanced": abs(tot_debit - tot_credit) < 0.01,
    }


@router.get("/reports/dimensions")
def get_dimensions_report(db: Session = Depends(get_db)):
    """Resultat fordelt per avdeling og per prosjekt."""
    rows = db.query(TransactionLine, Voucher).join(Voucher, TransactionLine.voucher_id == Voucher.id).all()
    by_dept = {}
    by_proj = {}

    for line, voucher in rows:
        is_rev = 3000 <= line.account_number < 4000
        is_exp = 4000 <= line.account_number < 8000
        if not (is_rev or is_exp):
            continue

        dept = line.department_code or voucher.department_code or "UFORDELT"
        proj = line.project_code or voucher.project_code or "FELLES"

        d_bucket = by_dept.setdefault(dept, {"code": dept, "revenue": 0.0, "expenses": 0.0})
        p_bucket = by_proj.setdefault(proj, {"code": proj, "revenue": 0.0, "expenses": 0.0})

        if is_rev:
            val = line.credit - line.debit
            d_bucket["revenue"] += val
            p_bucket["revenue"] += val
        elif is_exp:
            val = line.debit - line.credit
            d_bucket["expenses"] += val
            p_bucket["expenses"] += val

    def finalize(bucket_map):
        out = []
        for code in sorted(bucket_map.keys()):
            b = bucket_map[code]
            rev = round(b["revenue"], 2)
            exp = round(b["expenses"], 2)
            out.append({"code": code, "revenue": rev, "expenses": exp, "net": round(rev - exp, 2)})
        return out

    return {
        "by_department": finalize(by_dept),
        "by_project": finalize(by_proj),
    }


# -------------------------------------------------------------
# 4. SAF-T FINANCIAL XML v1.30 — EKSPORT OG IMPORT
# -------------------------------------------------------------

def build_saft_xml_bytes(db: Session) -> tuple[bytes, str]:
    """
    Bygger ekte norsk SAF-T Financial XML v1.30 (Skatteetaten standard).
    """
    setting = db.query(CompanySetting).first()
    accounts = db.query(Account).order_by(Account.account_number).all()
    customers = db.query(Customer).order_by(Customer.id).all()
    suppliers = db.query(Supplier).order_by(Supplier.id).all()
    vouchers = db.query(Voucher).order_by(Voucher.voucher_number).all()

    now = datetime.utcnow()
    clean_org = "".join(c for c in (setting.org_number if setting else "999888777") if c.isdigit()) or "999888777"
    company_name = setting.company_name if setting else "Phink Regnskap AS"

    ET.register_namespace("", SAFT_NS)
    root = ET.Element(f"{{{SAFT_NS}}}AuditFile")

    def sub(parent, tag, text_val=None):
        el = ET.SubElement(parent, f"{{{SAFT_NS}}}{tag}")
        if text_val is not None:
            el.text = str(text_val)
        return el

    # --- Header ---
    header = sub(root, "Header")
    sub(header, "AuditFileVersion", "1.30")
    sub(header, "AuditFileCountry", "NO")
    sub(header, "AuditFileDateCreated", now.strftime("%Y-%m-%d"))
    sub(header, "SoftwareCompanyName", "Phink Accounting")
    sub(header, "SoftwareID", "Phink Accounting Web")
    sub(header, "SoftwareVersion", "1.0.0")

    company = sub(header, "Company")
    sub(company, "RegistrationNumber", clean_org)
    sub(company, "Name", company_name)
    addr = sub(company, "Address")
    sub(addr, "StreetName", setting.address if setting and setting.address else "Storgata 1")
    sub(addr, "City", setting.city if setting and setting.city else "Oslo")
    sub(addr, "PostalCode", setting.postal_code if setting and setting.postal_code else "0182")
    sub(addr, "Country", "NO")
    contact = sub(company, "Contact")
    person = sub(contact, "ContactPerson")
    sub(person, "FirstName", "Regnskap")
    sub(person, "LastName", "Ansvarlig")
    sub(contact, "Telephone", setting.phone if setting and setting.phone else "+47 22 00 00 00")
    sub(contact, "Email", setting.email if setting and setting.email else "post@phink-acounting.no")
    if setting and setting.bank_account:
        bank = sub(company, "BankAccount")
        sub(bank, "BankAccountNumber", setting.bank_account)

    sub(header, "DefaultCurrencyCode", "NOK")
    sel = sub(header, "SelectionCriteria")
    dates = [v.date for v in vouchers if v.date]
    start_dt = min(dates) if dates else datetime(now.year, 1, 1)
    end_dt = max(dates) if dates else now
    sub(sel, "SelectionStartDate", start_dt.strftime("%Y-%m-%d"))
    sub(sel, "SelectionEndDate", end_dt.strftime("%Y-%m-%d"))
    sub(header, "TaxAccountingBasis", "A")

    # --- MasterFiles ---
    master = sub(root, "MasterFiles")

    # Kontoplan (GeneralLedgerAccounts)
    gl_accounts = sub(master, "GeneralLedgerAccounts")
    acc_balances = {}
    for v in vouchers:
        for l in v.lines:
            b = acc_balances.setdefault(l.account_number, [0.0, 0.0])
            b[0] += l.debit
            b[1] += l.credit

    for a in accounts:
        acc_el = sub(gl_accounts, "Account")
        sub(acc_el, "AccountID", a.account_number)
        sub(acc_el, "AccountDescription", a.name)
        sub(acc_el, "StandardAccountID", a.account_number)
        sub(acc_el, "AccountType", "GL")
        deb, cred = acc_balances.get(a.account_number, (0.0, 0.0))
        net = round(deb - cred, 2)
        sub(acc_el, "OpeningDebitBalance", "0.00")
        sub(acc_el, "OpeningCreditBalance", "0.00")
        sub(acc_el, "ClosingDebitBalance", f"{net:.2f}" if net >= 0 else "0.00")
        sub(acc_el, "ClosingCreditBalance", f"{abs(net):.2f}" if net < 0 else "0.00")

    # Kunder
    if customers:
        custs_el = sub(master, "Customers")
        for c in customers:
            c_el = sub(custs_el, "Customer")
            sub(c_el, "RegistrationNumber", "".join(ch for ch in (c.org_number or "") if ch.isdigit()) or "000000000")
            sub(c_el, "Name", c.name)
            sub(c_el, "CustomerID", f"C{c.id}")

    # Leverandører
    if suppliers:
        sups_el = sub(master, "Suppliers")
        for s in suppliers:
            s_el = sub(sups_el, "Supplier")
            sub(s_el, "RegistrationNumber", "".join(ch for ch in (s.org_number or "") if ch.isdigit()) or "000000000")
            sub(s_el, "Name", s.name)
            sub(s_el, "SupplierID", f"S{s.id}")

    # Norsk MVA-tabell (TaxTable)
    tax_table = sub(master, "TaxTable")
    tt_entry = sub(tax_table, "TaxTableEntry")
    sub(tt_entry, "TaxType", "MVA")
    sub(tt_entry, "Description", "Merverdiavgift Norge")
    for code, desc, pct in [
        ("3", "Utgående MVA høy sats 25%", "25.00"),
        ("31", "Utgående MVA middels sats 15%", "15.00"),
        ("33", "Utgående MVA lav sats 12%", "12.00"),
        ("1", "Inngående MVA høy sats 25%", "25.00"),
        ("11", "Inngående MVA middels sats 15%", "15.00"),
        ("13", "Inngående MVA lav sats 12%", "12.00"),
        ("0", "Ingen MVA-behandling / 0%", "0.00"),
    ]:
        det = sub(tt_entry, "TaxCodeDetails")
        sub(det, "TaxCode", code)
        sub(det, "Description", desc)
        sub(det, "TaxPercentage", pct)
        sub(det, "Country", "NO")
        sub(det, "StandardTaxCode", code)

    # --- GeneralLedgerEntries ---
    gle = sub(root, "GeneralLedgerEntries")
    total_debit = round(sum(l.debit for v in vouchers for l in v.lines), 2)
    total_credit = round(sum(l.credit for v in vouchers for l in v.lines), 2)
    sub(gle, "NumberOfEntries", len(vouchers))
    sub(gle, "TotalDebit", f"{total_debit:.2f}")
    sub(gle, "TotalCredit", f"{total_credit:.2f}")

    journal = sub(gle, "Journal")
    sub(journal, "JournalID", "GL")
    sub(journal, "Description", "Hovedbok Phink Accounting")
    sub(journal, "Type", "GL")

    for v in vouchers:
        tx = sub(journal, "Transaction")
        sub(tx, "TransactionID", v.voucher_number)
        tx_dt = v.date or now
        sub(tx, "Period", tx_dt.month)
        sub(tx, "PeriodYear", tx_dt.year)
        sub(tx, "TransactionDate", tx_dt.strftime("%Y-%m-%d"))
        sub(tx, "Description", v.description)
        sub(tx, "SystemEntryDate", (v.created_at or tx_dt).strftime("%Y-%m-%d"))
        sub(tx, "GLPostingDate", tx_dt.strftime("%Y-%m-%d"))

        for idx, l in enumerate(v.lines, start=1):
            ln = sub(tx, "Line")
            sub(ln, "RecordID", f"{v.voucher_number}-{idx}")
            sub(ln, "AccountID", l.account_number)
            sub(ln, "ValueDate", tx_dt.strftime("%Y-%m-%d"))
            sub(ln, "Description", l.description or v.description)
            if l.debit > 0:
                da = sub(ln, "DebitAmount")
                sub(da, "Amount", f"{l.debit:.2f}")
            if l.credit > 0:
                ca = sub(ln, "CreditAmount")
                sub(ca, "Amount", f"{l.credit:.2f}")
            if l.department_code:
                an = sub(ln, "Analysis")
                sub(an, "AnalysisType", "DEPT")
                sub(an, "AnalysisID", l.department_code)
            if l.project_code:
                an = sub(ln, "Analysis")
                sub(an, "AnalysisType", "PROJ")
                sub(an, "AnalysisID", l.project_code)

    ET.indent(root, space="  ")
    xml_bytes = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    filename = f"SAF-T_Financial_{clean_org}_{now.strftime('%Y%m%d')}.xml"
    return xml_bytes, filename


@router.get("/saft/export")
def export_saft_xml(db: Session = Depends(get_db)):
    """Laster ned ekte norsk SAF-T Financial v1.30 XML-fil for Skatteetaten / revisor."""
    xml_bytes, filename = build_saft_xml_bytes(db)
    db.add(AuditLog(
        action="SAFT_EXPORT",
        details=f"Eksporterte norsk SAF-T Financial XML ({filename}, {len(xml_bytes)} bytes)",
        ai_assisted=False,
    ))
    db.commit()
    return Response(
        content=xml_bytes,
        media_type="application/xml; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _local_tag(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _find_child_text(parent: ET.Element, name: str) -> Optional[str]:
    for child in parent:
        if _local_tag(child.tag) == name and child.text:
            return child.text.strip()
    return None


def _iter_by_name(parent: ET.Element, name: str):
    for el in parent.iter():
        if _local_tag(el.tag) == name:
            yield el


@router.post("/saft/import")
async def import_saft_xml(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Importerer en norsk SAF-T Financial XML-fil (fra f.eks. Conta, Fiken, Tripletex eller Phink).
    - Oppretter manglende kontoer i NS 4102
    - Importerer kunder og leverandører
    - Validerer dobbel bokføring (sum debet == sum kredit) på hvert eneste bilag før import
    """
    if not (file.filename or "").lower().endswith(".xml"):
        raise HTTPException(status_code=400, detail="SAF-T import krever en .xml-fil.")

    raw = await file.read()
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as err:
        raise HTTPException(status_code=400, detail=f"Ugyldig XML-fil: {err}")

    if _local_tag(root.tag) != "AuditFile":
        raise HTTPException(status_code=400, detail="XML-filen mangler rot-element <AuditFile> (ikke gyldig SAF-T).")

    accounts_created = 0
    customers_created = 0
    suppliers_created = 0
    vouchers_imported = 0
    skipped_unbalanced = []

    # 1. Importer kontoplan (GeneralLedgerAccounts)
    existing_acc_nums = {a.account_number for a in db.query(Account).all()}
    for gl_acc in _iter_by_name(root, "Account"):
        acc_id_str = _find_child_text(gl_acc, "AccountID")
        acc_desc = _find_child_text(gl_acc, "AccountDescription") or "Importert SAF-T konto"
        if not acc_id_str or not acc_id_str.isdigit():
            continue
        acc_num = int(acc_id_str)
        if acc_num in existing_acc_nums:
            continue
        acc_type = (
            "ASSET" if 1000 <= acc_num < 2000 else
            "LIABILITY" if 2000 <= acc_num < 3000 else
            "REVENUE" if 3000 <= acc_num < 4000 else
            "EXPENSE"
        )
        db.add(Account(account_number=acc_num, name=acc_desc[:250], account_type=acc_type, vat_code="NONE"))
        existing_acc_nums.add(acc_num)
        accounts_created += 1

    # 2. Importer kunder
    existing_cust_names = {c.name.lower() for c in db.query(Customer).all()}
    for cust_el in _iter_by_name(root, "Customer"):
        name = _find_child_text(cust_el, "Name")
        orgnr = _find_child_text(cust_el, "RegistrationNumber")
        if name and name.lower() not in existing_cust_names:
            db.add(Customer(name=name[:200], org_number=orgnr))
            existing_cust_names.add(name.lower())
            customers_created += 1

    # 3. Importer leverandører
    existing_sup_names = {s.name.lower() for s in db.query(Supplier).all()}
    for sup_el in _iter_by_name(root, "Supplier"):
        name = _find_child_text(sup_el, "Name")
        orgnr = _find_child_text(sup_el, "RegistrationNumber")
        if name and name.lower() not in existing_sup_names:
            db.add(Supplier(name=name[:200], org_number=orgnr))
            existing_sup_names.add(name.lower())
            suppliers_created += 1

    db.flush()

    # 4. Importer hovedbokstransaksjoner (GeneralLedgerEntries -> Transaction -> Line)
    next_voucher_num = (db.query(func.max(Voucher.voucher_number)).scalar() or 0) + 1

    for tx_el in _iter_by_name(root, "Transaction"):
        tx_id = _find_child_text(tx_el, "TransactionID") or str(next_voucher_num)
        desc = _find_child_text(tx_el, "Description") or f"SAF-T import #{tx_id}"
        date_str = _find_child_text(tx_el, "TransactionDate") or _find_child_text(tx_el, "GLPostingDate")
        try:
            tx_date = datetime.strptime(date_str[:10], "%Y-%m-%d") if date_str else datetime.utcnow()
        except Exception:
            tx_date = datetime.utcnow()

        parsed_lines = []
        for child in tx_el:
            if _local_tag(child.tag) != "Line":
                continue
            acc_id_str = _find_child_text(child, "AccountID")
            if not acc_id_str or not acc_id_str.isdigit():
                continue
            acc_num = int(acc_id_str)
            if acc_num not in existing_acc_nums:
                acc_type = (
                    "ASSET" if 1000 <= acc_num < 2000 else
                    "LIABILITY" if 2000 <= acc_num < 3000 else
                    "REVENUE" if 3000 <= acc_num < 4000 else
                    "EXPENSE"
                )
                db.add(Account(account_number=acc_num, name=f"SAF-T konto {acc_num}", account_type=acc_type))
                existing_acc_nums.add(acc_num)
                accounts_created += 1

            debit_val = 0.0
            credit_val = 0.0
            dept = None
            proj = None
            for sub_el in child:
                t = _local_tag(sub_el.tag)
                if t == "DebitAmount":
                    amt = _find_child_text(sub_el, "Amount")
                    debit_val = round(float(amt or 0.0), 2)
                elif t == "CreditAmount":
                    amt = _find_child_text(sub_el, "Amount")
                    credit_val = round(float(amt or 0.0), 2)
                elif t == "Analysis":
                    at = (_find_child_text(sub_el, "AnalysisType") or "").upper()
                    aid = _find_child_text(sub_el, "AnalysisID")
                    if at in ("DEPT", "AVD", "DEPARTMENT"):
                        dept = aid
                    elif at in ("PROJ", "PROSJEKT", "PROJECT"):
                        proj = aid

            line_desc = _find_child_text(child, "Description") or desc
            if debit_val > 0 or credit_val > 0:
                parsed_lines.append({
                    "account_number": acc_num,
                    "description": line_desc[:250],
                    "debit": debit_val,
                    "credit": credit_val,
                    "department_code": dept,
                    "project_code": proj,
                })

        if len(parsed_lines) < 2:
            continue

        s_deb = round(sum(l["debit"] for l in parsed_lines), 2)
        s_cred = round(sum(l["credit"] for l in parsed_lines), 2)
        if abs(s_deb - s_cred) >= 0.01:
            skipped_unbalanced.append({"transaction_id": tx_id, "debit": s_deb, "credit": s_cred})
            continue

        v = Voucher(
            voucher_number=next_voucher_num,
            date=tx_date,
            description=f"[SAF-T] {desc}"[:490],
            status="POSTED",
        )
        db.add(v)
        db.flush()
        for l in parsed_lines:
            db.add(TransactionLine(voucher_id=v.id, **l))
        next_voucher_num += 1
        vouchers_imported += 1

    db.add(AuditLog(
        action="SAFT_IMPORT",
        details=(
            f"Importerte SAF-T fil '{file.filename}': {vouchers_imported} bilag, "
            f"{accounts_created} nye kontoer, {customers_created} kunder, {suppliers_created} leverandører."
        ),
        ai_assisted=False,
    ))
    db.commit()

    return {
        "ok": True,
        "filename": file.filename,
        "accounts_created": accounts_created,
        "customers_created": customers_created,
        "suppliers_created": suppliers_created,
        "vouchers_imported": vouchers_imported,
        "skipped_unbalanced_count": len(skipped_unbalanced),
        "skipped_unbalanced": skipped_unbalanced[:10],
    }


# -------------------------------------------------------------
# 5. REGNSKAPSFAGLIG KONTROLL (FØR EKTE KUNDEDATA)
# -------------------------------------------------------------

@router.get("/compliance-check")
def run_accounting_compliance_check(db: Session = Depends(get_db)):
    """
    Automatisk regnskapsfaglig kontroll etter norsk bokføringslov, MVA-lov,
    skattebetalingslov og SAF-T-standard — bør kjøres og godkjennes av
    regnskapsfører/revisor før produksjonsbruk med ekte kundedata.
    """
    checks = []

    # 1. Dobbel bokføring på hvert enkelt bilag (Bokføringsloven § 7)
    vouchers = db.query(Voucher).order_by(Voucher.voucher_number).all()
    unbalanced_vouchers = []
    for v in vouchers:
        deb = round(sum(l.debit for l in v.lines), 2)
        cred = round(sum(l.credit for l in v.lines), 2)
        if abs(deb - cred) >= 0.01 or len(v.lines) < 2:
            unbalanced_vouchers.append(v.voucher_number)

    checks.append({
        "id": "double_entry",
        "title": "Dobbel bokføring (Bokføringsloven § 7)",
        "status": "PASS" if len(unbalanced_vouchers) == 0 else "FAIL",
        "details": (
            f"Alle {len(vouchers)} bilag balanserer eksakt (Sum Debet == Sum Kredit)."
            if not unbalanced_vouchers
            else f"Fant ubalanserte bilag: {unbalanced_vouchers}"
        ),
    })

    # 2. Hovedbok-balanse & Saldobalanse
    all_lines = db.query(TransactionLine).all()
    tot_deb = round(sum(l.debit for l in all_lines), 2)
    tot_cred = round(sum(l.credit for l in all_lines), 2)
    checks.append({
        "id": "ledger_balance",
        "title": "Total hovedbokbalanse (Saldobalanse)",
        "status": "PASS" if abs(tot_deb - tot_cred) < 0.01 else "FAIL",
        "details": f"Total Debet: {tot_deb:,.2f} kr | Total Kredit: {tot_cred:,.2f} kr | Diff: {round(tot_deb - tot_cred, 2):,.2f} kr.",
    })

    # 3. Ubrytelig bilagsnummerering uten hull (Bokføringsloven § 7)
    nums = [v.voucher_number for v in vouchers if v.voucher_number is not None]
    gaps = []
    for i in range(1, len(nums)):
        if nums[i] != nums[i - 1] + 1:
            gaps.append(f"{nums[i - 1]}->{nums[i]}")
    checks.append({
        "id": "voucher_sequence",
        "title": "Fortløpende bilagsnummerering uten hull",
        "status": "PASS" if len(gaps) == 0 else "WARNING",
        "details": (
            f"Bilagsnumre {nums[0]}–{nums[-1]} er fortløpende uten hull."
            if nums and not gaps
            else ("Ingen bilag bokført ennå." if not nums else f"Oppdaget hull i bilagsserien: {', '.join(gaps)}")
        ),
    })

    # 4. Skattetrekkskonto 1950 vs. skyldig forskuddstrekk 2600 (Skattebetalingsloven § 5-12)
    bal_1950 = round(sum(l.debit - l.credit for l in all_lines if l.account_number == 1950), 2)
    bal_2600 = round(sum(l.credit - l.debit for l in all_lines if l.account_number == 2600), 2)
    tax_ok = bal_1950 + 0.01 >= bal_2600
    checks.append({
        "id": "tax_withholding_account",
        "title": "Skattetrekkskonto 1950 dekker forskuddstrekk 2600 (§ 5-12)",
        "status": "PASS" if tax_ok else "FAIL",
        "details": f"Saldo 1950 (Skattetrekkskonto): {bal_1950:,.2f} kr vs. 2600 (Skyldig forskuddstrekk): {bal_2600:,.2f} kr.",
    })

    # 5. Norske MVA-kontoer i kontoplanen (NS 4102)
    existing_accs = {a.account_number for a in db.query(Account).all()}
    required_vat = {2700, 2701, 2702, 2710, 2711, 2712, 2740}
    missing_vat = sorted(required_vat - existing_accs)
    checks.append({
        "id": "norwegian_vat_accounts",
        "title": "Norske MVA-kontoer (25 %, 15 %, 12 % og 2740 oppgjør)",
        "status": "PASS" if not missing_vat else "FAIL",
        "details": (
            "Alle lovpålagte MVA-kontoer (2700–2712, 2740) er korrekt konfigurert etter NS 4102."
            if not missing_vat
            else f"Mangler MVA-kontoer: {missing_vat}"
        ),
    })

    # 6. Bedrifts- / Privatidentitet (MOD11 orgnr / 11-sifret fødselsnummer)
    setting = db.query(CompanySetting).first()
    id_status = "WARNING"
    id_detail = "Bedriftsprofil mangler."
    if setting:
        etype = (setting.entity_type or "AS").upper()
        if etype == "PRIVATE":
            ok, msg = validate_norwegian_national_id(setting.national_id or "")
            id_status = "PASS" if ok else "WARNING"
            id_detail = "Gyldig 11-sifret fødselsnummer registrert for privatprofil." if ok else f"Privatprofil: {msg}"
        else:
            ok, msg = validate_norwegian_orgnr(setting.org_number or "")
            id_status = "PASS" if ok else "WARNING"
            id_detail = (
                f"Gyldig MOD11 organisasjonsnummer ({msg}) for {setting.company_name} ({etype})."
                if ok
                else f"{setting.company_name} ({etype}): {msg} Oppdater med ekte Brønnøysund-orgnr før produksjon."
            )
    checks.append({
        "id": "entity_identity",
        "title": "Organisasjonsnummer (MOD11) / Fødselsnummer & Selskapsform",
        "status": id_status,
        "details": id_detail,
    })

    # 7. Reskontro mot hovedbok (1500 Kundefordringer & 2400 Leverandørgjeld)
    gl_1500 = round(sum(l.debit - l.credit for l in all_lines if l.account_number == 1500), 2)
    gl_2400 = round(sum(l.credit - l.debit for l in all_lines if l.account_number == 2400), 2)
    open_cust = round(
        db.query(func.sum(CustomerInvoice.total_amount)).filter(CustomerInvoice.status != "PAID").scalar() or 0.0, 2
    )
    open_sup = round(
        db.query(func.sum(SupplierInvoice.total_amount)).filter(SupplierInvoice.status == "UNPAID").scalar() or 0.0, 2
    )
    resk_ok = abs(gl_1500 - open_cust) < 1.0 and abs(gl_2400 - open_sup) < 1.0
    checks.append({
        "id": "subledger_reconciliation",
        "title": "Avstemming kunde- (1500) og leverandørreskontro (2400)",
        "status": "PASS" if resk_ok else "WARNING",
        "details": (
            f"1500 Hovedbok: {gl_1500:,.2f} kr vs. åpne kundefakturaer: {open_cust:,.2f} kr | "
            f"2400 Hovedbok: {gl_2400:,.2f} kr vs. åpne leverandørfakturaer: {open_sup:,.2f} kr."
        ),
    })

    # 8. SAF-T Financial XML v1.30 generering & syntakskontroll
    try:
        xml_bytes, filename = build_saft_xml_bytes(db)
        ET.fromstring(xml_bytes)
        saft_status = "PASS"
        saft_detail = f"SAF-T Financial v1.30 XML generert og syntaksvalidert OK ({len(xml_bytes):,} bytes)."
    except Exception as err:
        saft_status = "FAIL"
        saft_detail = f"SAF-T XML-feil: {err}"

    checks.append({
        "id": "saft_xml_valid",
        "title": "SAF-T Financial v1.30 XML-eksport (Skatteetaten)",
        "status": saft_status,
        "details": saft_detail,
    })

    fail_count = sum(1 for c in checks if c["status"] == "FAIL")
    warn_count = sum(1 for c in checks if c["status"] == "WARNING")
    pass_count = sum(1 for c in checks if c["status"] == "PASS")

    return {
        "overall_status": "FAIL" if fail_count > 0 else ("WARNING" if warn_count > 0 else "PASS"),
        "passed": pass_count,
        "warnings": warn_count,
        "failed": fail_count,
        "total_checks": len(checks),
        "checked_at": datetime.utcnow().isoformat(),
        "registered_users": db.query(User).count(),
        "advisory_note": (
            "Før systemet tas i bruk med ekte kundedata anbefales en avsluttende gjennomgang "
            "med statsautorisert regnskapsfører/revisor for å bekrefte selskapets MVA-kodeoppsett, "
            "skattetrekkskonto, A-melding-rapportering og 5-års bilagsoppbevaring etter Bokføringsloven."
        ),
        "checks": checks,
    }


# -------------------------------------------------------------
# 6. VARSLINGER (HVA SOM TRENGER OPPMEKSOMHET)
# -------------------------------------------------------------

@router.get("/notifications")
def get_notifications(db: Session = Depends(get_db)):
    """
    Samler alle live varslinger for kunden når noe trenger oppmerksomhet:
    forfalte fakturaer, uavstemte bankposter, ubehandlede bilag, skattetrekkskonto,
    manglende orgnr/fødselsnummer og åpne kundeservice-saker.
    """
    now = datetime.utcnow()
    soon = now + timedelta(days=7)
    alerts = []

    # 1. Leverandørfakturaer som er forfalt eller forfaller innen 7 dager
    unpaid_sup = db.query(SupplierInvoice).filter(SupplierInvoice.status != "PAID").all()
    overdue_sup = [i for i in unpaid_sup if i.due_date and i.due_date < now]
    due_soon_sup = [i for i in unpaid_sup if i.due_date and now <= i.due_date <= soon]

    if overdue_sup:
        tot = round(sum(i.total_amount for i in overdue_sup), 2)
        alerts.append({
            "id": "sup-overdue",
            "severity": "CRITICAL",
            "category": "Leverandører",
            "title": f"{len(overdue_sup)} forfalt(e) leverandørfaktura(er)",
            "message": f"Totalt {tot:,.2f} kr har passert forfallsdato og bør betales umiddelbart for å unngå purregebyr.",
            "action_tab": "suppliers",
            "action_label": "Gå til Leverandører",
            "created_at": now.isoformat(),
        })
    if due_soon_sup:
        tot = round(sum(i.total_amount for i in due_soon_sup), 2)
        alerts.append({
            "id": "sup-due-soon",
            "severity": "WARNING",
            "category": "Leverandører",
            "title": f"{len(due_soon_sup)} regning(er) forfaller innen 7 dager",
            "message": f"Totalt {tot:,.2f} kr forfaller snart. Kontroller dekning på driftskonto 1920.",
            "action_tab": "suppliers",
            "action_label": "Se forfallsliste",
            "created_at": now.isoformat(),
        })

    # 2. Uoppgjorte og forfalte kundefakturaer (KID-oppfølging & varsling)
    unpaid_cust = db.query(CustomerInvoice).filter(CustomerInvoice.status != "PAID").all()
    overdue_cust = [i for i in unpaid_cust if i.due_date and i.due_date < now]
    open_not_overdue_cust = [i for i in unpaid_cust if not (i.due_date and i.due_date < now)]
    if overdue_cust:
        tot = round(sum(i.total_amount for i in overdue_cust), 2)
        kids = ", ".join(filter(None, [i.kid for i in overdue_cust[:5]]))
        alerts.append({
            "id": "cust-overdue",
            "severity": "CRITICAL",
            "category": "Uoppgjorte fakturaer (KID)",
            "title": f"{len(overdue_cust)} forfalt(e) uoppgjort(e) kundefaktura(er)",
            "message": f"Du har {tot:,.2f} kr over forfall som ikke er betalt (KID: {kids or '—'}). Send purring eller sjekk bank/KID-innbetaling.",
            "action_tab": "invoices",
            "action_label": "Følg opp fakturaer",
            "created_at": now.isoformat(),
        })
    if open_not_overdue_cust:
        tot = round(sum(i.total_amount for i in open_not_overdue_cust), 2)
        alerts.append({
            "id": "cust-unsettled",
            "severity": "INFO",
            "category": "Uoppgjorte fakturaer (KID)",
            "title": f"{len(open_not_overdue_cust)} uoppgjort(e) kundefaktura(er) venter på betaling",
            "message": f"Totalt {tot:,.2f} kr venter på innbetaling. Ved KID-innbetaling fra banken føres og avstemmes fakturaen automatisk.",
            "action_tab": "invoices",
            "action_label": "Se åpne fakturaer",
            "created_at": now.isoformat(),
        })

    # 3. Uavstemte banktransaksjoner
    unreconciled_cnt = db.query(func.count(BankTransaction.id)).filter(BankTransaction.reconciled == False).scalar() or 0
    if unreconciled_cnt > 0:
        alerts.append({
            "id": "bank-unreconciled",
            "severity": "WARNING",
            "category": "Bankavstemning",
            "title": f"{unreconciled_cnt} uavstemte banktransaksjoner",
            "message": "Kjør automatisk avstemming eller hurtigbokfør åpne bankposter slik at konto 1920 stemmer med banken.",
            "action_tab": "bank",
            "action_label": "Åpne Bankavstemning",
            "created_at": now.isoformat(),
        })

    # 4. Ubehandlede bilag i bilagsmottak
    pending_docs = db.query(func.count(UploadedDocument.id)).filter(UploadedDocument.status == "PENDING").scalar() or 0
    if pending_docs > 0:
        alerts.append({
            "id": "inbox-pending",
            "severity": "INFO",
            "category": "Bilagsmottak",
            "title": f"{pending_docs} bilag venter på bokføring",
            "message": "Opplastede kvitteringer/PDF-er ligger i bilagsmottaket og er klare for AI-tolking og bokføring.",
            "action_tab": "inbox",
            "action_label": "Åpne Bilagsmottak",
            "created_at": now.isoformat(),
        })

    # 5. Skattetrekkskonto 1950 vs 2600 (Skattebetalingsloven § 5-12)
    all_lines = db.query(TransactionLine).all()
    bal_1950 = round(sum(l.debit - l.credit for l in all_lines if l.account_number == 1950), 2)
    bal_2600 = round(sum(l.credit - l.debit for l in all_lines if l.account_number == 2600), 2)
    if bal_2600 > bal_1950 + 0.01:
        diff = round(bal_2600 - bal_1950, 2)
        alerts.append({
            "id": "tax-account-shortfall",
            "severity": "CRITICAL",
            "category": "Lønn & Skattetrekk",
            "title": "Skattetrekkskonto 1950 mangler dekning!",
            "message": f"Det mangler {diff:,.2f} kr på sperret skattetrekkskonto 1950 for å dekke skyldig forskuddstrekk (2600).",
            "action_tab": "payroll",
            "action_label": "Gå til Lønnskjøring",
            "created_at": now.isoformat(),
        })

    # 6. Bedrifts- / Privatidentitet (MOD11 orgnr / fødselsnummer)
    setting = db.query(CompanySetting).first()
    if setting:
        etype = (setting.entity_type or "AS").upper()
        if etype == "PRIVATE":
            ok, msg = validate_norwegian_national_id(setting.national_id or "")
        else:
            ok, msg = validate_norwegian_orgnr(setting.org_number or "")
        if not ok:
            alerts.append({
                "id": "identity-invalid",
                "severity": "WARNING",
                "category": "Innstillinger",
                "title": "Kontroller organisasjonsnummer / fødselsnummer",
                "message": f"{msg} Oppdater profilen før produksjonsbruk og SAF-T-eksport.",
                "action_tab": "settings",
                "action_label": "Åpne Innstillinger",
                "created_at": now.isoformat(),
            })

    # 7. Eskalerte kundeservice-saker
    open_tickets = db.query(func.count(SupportTicket.id)).filter(SupportTicket.status == "ESCALATED_TO_HUMAN").scalar() or 0
    if open_tickets > 0:
        alerts.append({
            "id": "support-escalated",
            "severity": "INFO",
            "category": "Kundeservice",
            "title": f"{open_tickets} kundehenvendelse(r) krever svar",
            "message": "AI-en har eskalert saker som venter på kundebehandler i Kundeservice Desk.",
            "action_tab": "support",
            "action_label": "Åpne Kundeservice",
            "created_at": now.isoformat(),
        })

    # 8. Månedlig påminnelse om å sende abonnementsfakturaer (Vipps Bedrift / Faktura)
    current_month = now.strftime("%Y-%m")
    all_orders = db.query(SubscriptionOrder).all()
    billed_emails = {
        (o.customer_email or "").strip().lower()
        for o in all_orders
        if o.created_at and o.created_at.strftime("%Y-%m") == current_month
    }
    all_emails = {(o.customer_email or "").strip().lower() for o in all_orders if o.customer_email}
    due_monthly = all_emails - billed_emails
    if due_monthly:
        alerts.append({
            "id": f"monthly-invoice-{current_month}",
            "severity": "WARNING",
            "category": "Månedlig fakturering",
            "title": f"Påminnelse ({current_month}): Send månedlig faktura til {len(due_monthly)} kunde(r)",
            "message": "Det er en ny måned — klikk for å sende og bokføre månedens fakturaer (25 % MVA & KID) eller Vipps Bedrift-krav.",
            "action_tab": "billing",
            "action_label": "Send månedens fakturaer",
            "created_at": now.isoformat(),
        })
    elif len(billed_emails) == 0:
        alerts.append({
            "id": f"monthly-invoice-reminder-{current_month}",
            "severity": "INFO",
            "category": "Månedlig fakturering",
            "title": f"Månedlig fakturapåminnelse ({current_month})",
            "message": "Husk å sende månedens abonnementsfakturaer eller Vipps Bedrift-betalinger for inneværende måned.",
            "action_tab": "billing",
            "action_label": "Åpne Vipps & Faktura",
            "created_at": now.isoformat(),
        })

    severity_rank = {"CRITICAL": 0, "WARNING": 1, "INFO": 2}
    alerts.sort(key=lambda a: severity_rank.get(a["severity"], 9))

    return {
        "total": len(alerts),
        "critical": sum(1 for a in alerts if a["severity"] == "CRITICAL"),
        "warnings": sum(1 for a in alerts if a["severity"] == "WARNING"),
        "info": sum(1 for a in alerts if a["severity"] == "INFO"),
        "items": alerts,
    }
