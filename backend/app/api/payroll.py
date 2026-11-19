from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.models.accounting import (
    Account, Employee, PayrollRun, PayrollLine, Voucher, TransactionLine, AuditLog
)

router = APIRouter(prefix="/payroll", tags=["Payroll"])

# Offisielle norske arbeidsgiveravgiftssoner (Skatteetaten)
AGA_ZONE_RATES = {
    1: 14.1,   # Sone 1 (Oslo, Bergen, Trondheim, Stavanger m.fl.)
    2: 10.6,   # Sone 2
    3: 6.4,    # Sone 3
    4: 5.1,    # Sone 4
    5: 0.0,    # Sone 5 (Tiltakssonen: Finnmark og Nord-Troms)
}


class EmployeeCreate(BaseModel):
    employee_number: Optional[str] = None
    full_name: str = Field(..., min_length=2, max_length=200)
    national_id: Optional[str] = None
    email: Optional[str] = None
    bank_account: Optional[str] = None
    position: str = "Ansatt"
    monthly_gross_salary: float = Field(..., gt=0)
    tax_percent: float = Field(default=30.0, ge=0.0, le=60.0)
    holiday_pay_percent: float = Field(default=12.0, ge=10.2, le=15.0)
    aga_zone: int = Field(default=1, ge=1, le=5)
    otp_percent: float = Field(default=2.0, ge=2.0, le=7.0)
    department_code: Optional[str] = "ADM"
    project_code: Optional[str] = "FELLES"


class PayrollEmployeeOverride(BaseModel):
    employee_id: int
    gross_salary: Optional[float] = None
    overtime_pay: float = 0.0
    bonus_pay: float = 0.0
    tax_percent: Optional[float] = None


class PayrollRunRequest(BaseModel):
    period: str = Field(..., description="Lønnsperiode, f.eks. '2026-11'")
    pay_date: Optional[datetime] = None
    auto_transfer_tax_account: bool = True
    employees: Optional[List[PayrollEmployeeOverride]] = None


def calculate_employee_payroll(emp: Employee, override: Optional[PayrollEmployeeOverride] = None) -> dict:
    """
    Beregner ALLE punkter i norsk lønnskjøring med eksakt øre-presisjon:
    - Fastlønn (5000), Overtid (5010), Bonus (5020)
    - Forskuddstrekk (2600 -> overføres 1950 Skattetrekkskonto)
    - Nettolønn utbetalt (2930)
    - Feriepenger avsatt (5180 / 2940)
    - OTP Obligatorisk tjenestepensjon (5420 / 2960)
    - Arbeidsgiveravgift av lønn + OTP (5400 / 2770)
    - Påløpt AGA på feriepenger (5190 / 2780)
    """
    gross = round(override.gross_salary if (override and override.gross_salary is not None) else emp.monthly_gross_salary, 2)
    overtime = round(override.overtime_pay if override else 0.0, 2)
    bonus = round(override.bonus_pay if override else 0.0, 2)
    taxable_gross = round(gross + overtime + bonus, 2)

    tax_pct = override.tax_percent if (override and override.tax_percent is not None) else emp.tax_percent
    tax_withholding = round(taxable_gross * (tax_pct / 100.0), 2)
    net_pay = round(taxable_gross - tax_withholding, 2)

    holiday_pct = emp.holiday_pay_percent
    holiday_pay = round(taxable_gross * (holiday_pct / 100.0), 2)

    otp_pct = emp.otp_percent
    otp_amount = round(taxable_gross * (otp_pct / 100.0), 2)

    aga_pct = AGA_ZONE_RATES.get(emp.aga_zone, 14.1)
    # AGA beregnes av lønn + arbeidsgivers pensjonstilskudd (OTP) etter folketrygdloven § 23-2
    aga_amount = round((taxable_gross + otp_amount) * (aga_pct / 100.0), 2)
    # Påløpt AGA på opptjente feriepenger
    aga_holiday_amount = round(holiday_pay * (aga_pct / 100.0), 2)

    total_employer_cost = round(taxable_gross + holiday_pay + otp_amount + aga_amount + aga_holiday_amount, 2)

    return {
        "employee_id": emp.id,
        "employee_number": emp.employee_number,
        "employee_name": emp.full_name,
        "bank_account": emp.bank_account,
        "position": emp.position,
        "department_code": emp.department_code or "ADM",
        "project_code": emp.project_code or "FELLES",
        "gross_salary": gross,
        "overtime_pay": overtime,
        "bonus_pay": bonus,
        "taxable_gross": taxable_gross,
        "tax_percent": tax_pct,
        "tax_withholding": tax_withholding,
        "net_pay": net_pay,
        "holiday_pay_percent": holiday_pct,
        "holiday_pay": holiday_pay,
        "otp_percent": otp_pct,
        "otp_amount": otp_amount,
        "aga_zone": emp.aga_zone,
        "aga_percent": aga_pct,
        "aga_amount": aga_amount,
        "aga_holiday_amount": aga_holiday_amount,
        "total_employer_cost": total_employer_cost,
    }


def build_payroll_journal_entries(period: str, employee_calcs: List[dict]) -> dict:
    """
    Fordeler alle lønnspunkter automatisk til balanserte NS 4102 hovedboksposter:
    1) Hovedbilag lønnskjøring (Sum Debet == Sum Kredit på øret)
    2) Lovpålagt overføring til skattetrekkskonto 1950 fra 1920
    """
    tot_gross = round(sum(c["gross_salary"] for c in employee_calcs), 2)
    tot_overtime = round(sum(c["overtime_pay"] for c in employee_calcs), 2)
    tot_bonus = round(sum(c["bonus_pay"] for c in employee_calcs), 2)
    tot_tax = round(sum(c["tax_withholding"] for c in employee_calcs), 2)
    tot_net = round(sum(c["net_pay"] for c in employee_calcs), 2)
    tot_holiday = round(sum(c["holiday_pay"] for c in employee_calcs), 2)
    tot_otp = round(sum(c["otp_amount"] for c in employee_calcs), 2)
    tot_aga = round(sum(c["aga_amount"] for c in employee_calcs), 2)
    tot_aga_holiday = round(sum(c["aga_holiday_amount"] for c in employee_calcs), 2)
    tot_cost = round(sum(c["total_employer_cost"] for c in employee_calcs), 2)

    # Debet-linjer (fordelt per ansatt/avdeling/prosjekt på kostnadskontoer for nøyaktig prosjekt-/avdelingsregnskap)
    journal_lines = []
    for c in employee_calcs:
        dept = c["department_code"]
        proj = c["project_code"]
        if c["gross_salary"] > 0:
            journal_lines.append({
                "account_number": 5000,
                "account_name": "Lønn til ansatte",
                "description": f"Fastlønn {period} - {c['employee_name']}",
                "debit": c["gross_salary"],
                "credit": 0.0,
                "department_code": dept,
                "project_code": proj,
            })
        if c["overtime_pay"] > 0:
            journal_lines.append({
                "account_number": 5010,
                "account_name": "Overtidslønn",
                "description": f"Overtid {period} - {c['employee_name']}",
                "debit": c["overtime_pay"],
                "credit": 0.0,
                "department_code": dept,
                "project_code": proj,
            })
        if c["bonus_pay"] > 0:
            journal_lines.append({
                "account_number": 5020,
                "account_name": "Bonus og provisjon",
                "description": f"Bonus {period} - {c['employee_name']}",
                "debit": c["bonus_pay"],
                "credit": 0.0,
                "department_code": dept,
                "project_code": proj,
            })
        if c["holiday_pay"] > 0:
            journal_lines.append({
                "account_number": 5180,
                "account_name": "Feriepenger avsatt",
                "description": f"Feriepenger {c['holiday_pay_percent']}% {period} - {c['employee_name']}",
                "debit": c["holiday_pay"],
                "credit": 0.0,
                "department_code": dept,
                "project_code": proj,
            })
        if c["aga_amount"] > 0:
            journal_lines.append({
                "account_number": 5400,
                "account_name": "Arbeidsgiveravgift (AGA)",
                "description": f"AGA sone {c['aga_zone']} ({c['aga_percent']}%) {period} - {c['employee_name']}",
                "debit": c["aga_amount"],
                "credit": 0.0,
                "department_code": dept,
                "project_code": proj,
            })
        if c["aga_holiday_amount"] > 0:
            journal_lines.append({
                "account_number": 5190,
                "account_name": "Påløpt AGA på feriepenger",
                "description": f"Påløpt AGA feriepenger {period} - {c['employee_name']}",
                "debit": c["aga_holiday_amount"],
                "credit": 0.0,
                "department_code": dept,
                "project_code": proj,
            })
        if c["otp_amount"] > 0:
            journal_lines.append({
                "account_number": 5420,
                "account_name": "Pensjonskostnad (OTP)",
                "description": f"OTP {c['otp_percent']}% {period} - {c['employee_name']}",
                "debit": c["otp_amount"],
                "credit": 0.0,
                "department_code": dept,
                "project_code": proj,
            })

    # Kredit-linjer (balansekontoer gjeld/trekk)
    if tot_net > 0:
        journal_lines.append({
            "account_number": 2930,
            "account_name": "Skyldig lønn (Netto utbetalt)",
            "description": f"Skyldig nettolønn {period}",
            "debit": 0.0,
            "credit": tot_net,
            "department_code": "ADM",
            "project_code": "FELLES",
        })
    if tot_tax > 0:
        journal_lines.append({
            "account_number": 2600,
            "account_name": "Forskuddstrekk (Skattetrekk ansatte)",
            "description": f"Trukket skattetrekk {period}",
            "debit": 0.0,
            "credit": tot_tax,
            "department_code": "ADM",
            "project_code": "FELLES",
        })
    if tot_holiday > 0:
        journal_lines.append({
            "account_number": 2940,
            "account_name": "Skyldige feriepenger",
            "description": f"Avsatte feriepenger {period}",
            "debit": 0.0,
            "credit": tot_holiday,
            "department_code": "ADM",
            "project_code": "FELLES",
        })
    if tot_aga > 0:
        journal_lines.append({
            "account_number": 2770,
            "account_name": "Skyldig arbeidsgiveravgift (AGA)",
            "description": f"Skyldig AGA {period}",
            "debit": 0.0,
            "credit": tot_aga,
            "department_code": "ADM",
            "project_code": "FELLES",
        })
    if tot_aga_holiday > 0:
        journal_lines.append({
            "account_number": 2780,
            "account_name": "Påløpt AGA på feriepenger",
            "description": f"Avsatt AGA feriepenger {period}",
            "debit": 0.0,
            "credit": tot_aga_holiday,
            "department_code": "ADM",
            "project_code": "FELLES",
        })
    if tot_otp > 0:
        journal_lines.append({
            "account_number": 2960,
            "account_name": "Påløpt kostnad (inkl. OTP pensjon)",
            "description": f"Skyldig OTP tjenestepensjon {period}",
            "debit": 0.0,
            "credit": tot_otp,
            "department_code": "ADM",
            "project_code": "FELLES",
        })

    sum_debit = round(sum(l["debit"] for l in journal_lines), 2)
    sum_credit = round(sum(l["credit"] for l in journal_lines), 2)

    tax_transfer_lines = []
    if tot_tax > 0:
        tax_transfer_lines = [
            {
                "account_number": 1950,
                "account_name": "Bankinnskudd for skattetrekk (Skattetrekkskonto)",
                "description": f"Lovpålagt overføring forskuddstrekk {period} til skattetrekkskonto",
                "debit": tot_tax,
                "credit": 0.0,
                "department_code": "ADM",
                "project_code": "FELLES",
            },
            {
                "account_number": 1920,
                "account_name": "Bankinnskudd drift",
                "description": f"Overføring fra driftskonto til skattetrekkskonto {period}",
                "debit": 0.0,
                "credit": tot_tax,
                "department_code": "ADM",
                "project_code": "FELLES",
            },
        ]

    return {
        "totals": {
            "total_gross": tot_gross,
            "total_overtime": tot_overtime,
            "total_bonus": tot_bonus,
            "total_tax_withholding": tot_tax,
            "total_net_pay": tot_net,
            "total_holiday_pay": tot_holiday,
            "total_aga": tot_aga,
            "total_aga_holiday": tot_aga_holiday,
            "total_otp": tot_otp,
            "total_employer_cost": tot_cost,
            "sum_debit": sum_debit,
            "sum_credit": sum_credit,
            "is_balanced": abs(sum_debit - sum_credit) < 0.01,
        },
        "journal_lines": journal_lines,
        "tax_transfer_lines": tax_transfer_lines,
    }


def seed_demo_employees(db: Session):
    """Legger inn 2 realistiske demo-ansatte hvis ansattregisteret er tomt."""
    if db.query(Employee).count() > 0:
        return
    demo = [
        Employee(
            employee_number="ANS-001",
            full_name="Ola Nordmann",
            email="ola@phink-acounting.no",
            bank_account="1234.56.78910",
            position="Daglig leder / Utvikler",
            monthly_gross_salary=58000.0,
            tax_percent=32.0,
            holiday_pay_percent=12.0,
            aga_zone=1,
            otp_percent=2.0,
            department_code="ADM",
            project_code="FELLES",
        ),
        Employee(
            employee_number="ANS-002",
            full_name="Kari Hansen",
            email="kari@phink-acounting.no",
            bank_account="1234.56.78921",
            position="Salgs- og konsulentansvarlig",
            monthly_gross_salary=48750.50,
            tax_percent=30.0,
            holiday_pay_percent=12.0,
            aga_zone=1,
            otp_percent=3.0,
            department_code="SALG",
            project_code="PROJ-2026-01",
        ),
    ]
    for e in demo:
        db.add(e)
    db.commit()


@router.get("/employees")
def get_employees(db: Session = Depends(get_db)):
    emps = db.query(Employee).filter(Employee.is_active == True).order_by(Employee.employee_number).all()
    return [
        {
            "id": e.id,
            "employee_number": e.employee_number,
            "full_name": e.full_name,
            "email": e.email,
            "bank_account": e.bank_account,
            "position": e.position,
            "monthly_gross_salary": e.monthly_gross_salary,
            "tax_percent": e.tax_percent,
            "holiday_pay_percent": e.holiday_pay_percent,
            "aga_zone": e.aga_zone,
            "aga_percent": AGA_ZONE_RATES.get(e.aga_zone, 14.1),
            "otp_percent": e.otp_percent,
            "department_code": e.department_code,
            "project_code": e.project_code,
            "is_active": e.is_active,
        }
        for e in emps
    ]


@router.post("/employees")
def create_employee(emp_in: EmployeeCreate, db: Session = Depends(get_db)):
    count = db.query(Employee).count()
    emp_num = (emp_in.employee_number or "").strip() or f"ANS-{count + 1:03d}"
    if db.query(Employee).filter(Employee.employee_number == emp_num).first():
        raise HTTPException(status_code=400, detail=f"Ansattnummer {emp_num} finnes allerede.")

    emp = Employee(
        employee_number=emp_num,
        full_name=emp_in.full_name.strip(),
        national_id=emp_in.national_id,
        email=emp_in.email,
        bank_account=emp_in.bank_account,
        position=emp_in.position,
        monthly_gross_salary=round(emp_in.monthly_gross_salary, 2),
        tax_percent=emp_in.tax_percent,
        holiday_pay_percent=emp_in.holiday_pay_percent,
        aga_zone=emp_in.aga_zone,
        otp_percent=emp_in.otp_percent,
        department_code=emp_in.department_code or "ADM",
        project_code=emp_in.project_code or "FELLES",
    )
    db.add(emp)
    db.commit()
    db.refresh(emp)
    return {
        "ok": True,
        "id": emp.id,
        "employee_number": emp.employee_number,
        "full_name": emp.full_name,
        "aga_percent": AGA_ZONE_RATES.get(emp.aga_zone, 14.1),
    }


@router.delete("/employees/{employee_id}")
def deactivate_employee(employee_id: int, db: Session = Depends(get_db)):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Ansatt ikke funnet.")
    emp.is_active = False
    db.commit()
    return {"ok": True, "message": f"{emp.full_name} er deaktivert fra lønnskjøring."}


def _resolve_employee_calcs(req: PayrollRunRequest, db: Session) -> List[dict]:
    if req.employees and len(req.employees) > 0:
        calcs = []
        for ov in req.employees:
            emp = db.query(Employee).filter(Employee.id == ov.employee_id, Employee.is_active == True).first()
            if not emp:
                raise HTTPException(status_code=404, detail=f"Ansatt ID {ov.employee_id} finnes ikke.")
            calcs.append(calculate_employee_payroll(emp, ov))
        return calcs

    active = db.query(Employee).filter(Employee.is_active == True).order_by(Employee.employee_number).all()
    if not active:
        raise HTTPException(status_code=400, detail="Ingen aktive ansatte registrert for lønnskjøring.")
    return [calculate_employee_payroll(emp) for emp in active]


@router.post("/preview")
def preview_payroll(req: PayrollRunRequest, db: Session = Depends(get_db)):
    """Forhåndsviser komplett fordeling av alle poster i lønnskjøringen før bokføring."""
    calcs = _resolve_employee_calcs(req, db)
    entries = build_payroll_journal_entries(req.period, calcs)
    return {
        "ok": True,
        "period": req.period,
        "employee_breakdown": calcs,
        **entries,
    }


@router.post("/run")
def execute_payroll_run(req: PayrollRunRequest, db: Session = Depends(get_db)):
    """
    Kjører lønn og fordeler automatisk ALLE poster i hovedbok:
    - Bilag 1: Brutto (5000), Overtid (5010), Bonus (5020), Feriepenger (5180/2940),
               AGA (5400/2770), AGA feriepenger (5190/2780), OTP (5420/2960),
               Forskuddstrekk (2600) og Nettolønn (2930).
    - Bilag 2: Lovpålagt overføring av skattetrekk til sperret Skattetrekkskonto (1950) fra Drift (1920).
    """
    calcs = _resolve_employee_calcs(req, db)
    entries = build_payroll_journal_entries(req.period, calcs)
    totals = entries["totals"]

    if not totals["is_balanced"]:
        raise HTTPException(
            status_code=500,
            detail=f"Intern balansefeil i lønnskjøring: Debet {totals['sum_debit']} != Kredit {totals['sum_credit']}",
        )

    pay_date = req.pay_date or datetime.utcnow()

    # Kontroller at alle kontoer i lønnsposteringen finnes i NS 4102 kontoplanen
    needed_accounts = {l["account_number"] for l in entries["journal_lines"] + entries["tax_transfer_lines"]}
    existing_accounts = {a.account_number for a in db.query(Account).filter(Account.account_number.in_(needed_accounts)).all()}
    missing = needed_accounts - existing_accounts
    if missing:
        raise HTTPException(status_code=400, detail=f"Mangler konto(er) i kontoplanen: {sorted(missing)}")

    # 1. Bokfør hovedbilag for lønnskjøringen
    max_num = db.query(func.max(Voucher.voucher_number)).scalar() or 0
    main_voucher = Voucher(
        voucher_number=max_num + 1,
        date=pay_date,
        description=f"Lønnskjøring periode {req.period} ({len(calcs)} ansatte)",
        department_code="ADM",
        project_code="FELLES",
        status="POSTED",
    )
    db.add(main_voucher)
    db.flush()

    for line in entries["journal_lines"]:
        db.add(TransactionLine(
            voucher_id=main_voucher.id,
            account_number=line["account_number"],
            description=line["description"],
            debit=line["debit"],
            credit=line["credit"],
            department_code=line["department_code"],
            project_code=line["project_code"],
        ))

    # 2. Bokfør lovpålagt overføring til sperret skattetrekkskonto 1950 (Skattebetalingsloven § 5-12)
    tax_voucher = None
    if req.auto_transfer_tax_account and entries["tax_transfer_lines"]:
        tax_voucher = Voucher(
            voucher_number=max_num + 2,
            date=pay_date,
            description=f"Overføring forskuddstrekk til skattetrekkskonto 1950 ({req.period})",
            department_code="ADM",
            project_code="FELLES",
            status="POSTED",
        )
        db.add(tax_voucher)
        db.flush()
        for line in entries["tax_transfer_lines"]:
            db.add(TransactionLine(
                voucher_id=tax_voucher.id,
                account_number=line["account_number"],
                description=line["description"],
                debit=line["debit"],
                credit=line["credit"],
                department_code=line["department_code"],
                project_code=line["project_code"],
            ))

    # 3. Lagre lønnskjøring + linjer per ansatt (for lønnsslipp & historikk)
    run = PayrollRun(
        period=req.period,
        pay_date=pay_date,
        status="POSTED",
        total_gross=totals["total_gross"],
        total_overtime=totals["total_overtime"],
        total_bonus=totals["total_bonus"],
        total_tax_withholding=totals["total_tax_withholding"],
        total_net_pay=totals["total_net_pay"],
        total_holiday_pay=totals["total_holiday_pay"],
        total_aga=totals["total_aga"],
        total_aga_holiday=totals["total_aga_holiday"],
        total_otp=totals["total_otp"],
        total_employer_cost=totals["total_employer_cost"],
        voucher_id=main_voucher.id,
        tax_transfer_voucher_id=tax_voucher.id if tax_voucher else None,
    )
    db.add(run)
    db.flush()

    for c in calcs:
        db.add(PayrollLine(
            payroll_run_id=run.id,
            employee_id=c["employee_id"],
            employee_name=c["employee_name"],
            gross_salary=c["gross_salary"],
            overtime_pay=c["overtime_pay"],
            bonus_pay=c["bonus_pay"],
            tax_percent=c["tax_percent"],
            tax_withholding=c["tax_withholding"],
            net_pay=c["net_pay"],
            holiday_pay_percent=c["holiday_pay_percent"],
            holiday_pay=c["holiday_pay"],
            aga_percent=c["aga_percent"],
            aga_amount=c["aga_amount"],
            aga_holiday_amount=c["aga_holiday_amount"],
            otp_percent=c["otp_percent"],
            otp_amount=c["otp_amount"],
            total_employer_cost=c["total_employer_cost"],
            department_code=c["department_code"],
            project_code=c["project_code"],
        ))

    db.add(AuditLog(
        action="PAYROLL_RUN",
        details=(
            f"Lønnskjøring {req.period} bokført (Bilag #{main_voucher.voucher_number}"
            + (f", Skattetrekkskonto Bilag #{tax_voucher.voucher_number}" if tax_voucher else "")
            + f"): Brutto {totals['total_gross']} kr, Netto {totals['total_net_pay']} kr, Skatt {totals['total_tax_withholding']} kr."
        ),
        ai_assisted=False,
    ))
    db.commit()
    db.refresh(run)

    return {
        "ok": True,
        "payroll_run_id": run.id,
        "period": run.period,
        "voucher_number": main_voucher.voucher_number,
        "tax_transfer_voucher_number": tax_voucher.voucher_number if tax_voucher else None,
        "totals": totals,
        "employee_breakdown": calcs,
        "journal_lines": entries["journal_lines"],
        "tax_transfer_lines": entries["tax_transfer_lines"],
    }


@router.get("/runs")
def list_payroll_runs(db: Session = Depends(get_db)):
    runs = db.query(PayrollRun).order_by(PayrollRun.created_at.desc()).all()
    voucher_map = {v.id: v.voucher_number for v in db.query(Voucher).all()}
    return [
        {
            "id": r.id,
            "period": r.period,
            "pay_date": r.pay_date.isoformat() if r.pay_date else None,
            "status": r.status,
            "total_gross": r.total_gross,
            "total_overtime": r.total_overtime,
            "total_bonus": r.total_bonus,
            "total_tax_withholding": r.total_tax_withholding,
            "total_net_pay": r.total_net_pay,
            "total_holiday_pay": r.total_holiday_pay,
            "total_aga": r.total_aga,
            "total_aga_holiday": r.total_aga_holiday,
            "total_otp": r.total_otp,
            "total_employer_cost": r.total_employer_cost,
            "voucher_number": voucher_map.get(r.voucher_id),
            "tax_transfer_voucher_number": voucher_map.get(r.tax_transfer_voucher_id),
            "lines": [
                {
                    "id": l.id,
                    "employee_id": l.employee_id,
                    "employee_name": l.employee_name,
                    "gross_salary": l.gross_salary,
                    "overtime_pay": l.overtime_pay,
                    "bonus_pay": l.bonus_pay,
                    "tax_percent": l.tax_percent,
                    "tax_withholding": l.tax_withholding,
                    "net_pay": l.net_pay,
                    "holiday_pay_percent": l.holiday_pay_percent,
                    "holiday_pay": l.holiday_pay,
                    "aga_percent": l.aga_percent,
                    "aga_amount": l.aga_amount,
                    "aga_holiday_amount": l.aga_holiday_amount,
                    "otp_percent": l.otp_percent,
                    "otp_amount": l.otp_amount,
                    "total_employer_cost": l.total_employer_cost,
                    "department_code": l.department_code,
                    "project_code": l.project_code,
                }
                for l in r.lines
            ],
        }
        for r in runs
    ]
