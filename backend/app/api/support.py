from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime

from app.database import get_db
from app.models.accounting import SupportTicket, TicketMessage, AuditLog
from app.schemas.accounting import (
    SupportTicketCreate, SupportTicketResponse,
    TicketMessageCreate, TicketMessageResponse
)

router = APIRouter(prefix="/support", tags=["Kundeservice"])

@router.get("/tickets", response_model=List[SupportTicketResponse])
def get_support_tickets(include_resolved: bool = False, db: Session = Depends(get_db)):
    """
    Henter aktive kundeservicehenvendelser for operatørdashbordet.
    Fullførte saker (status='RESOLVED') fjernes automatisk fra den aktive listen.
    """
    q = db.query(SupportTicket)
    if not include_resolved:
        q = q.filter(SupportTicket.status != "RESOLVED")
    return q.order_by(SupportTicket.updated_at.desc()).all()

@router.post("/tickets", response_model=SupportTicketResponse)
def create_support_ticket(ticket_in: SupportTicketCreate, db: Session = Depends(get_db)):
    """
    Oppretter en henvendelse fra kunde.
    Dersom det gjelder refusjon eller betaling som feilet, eskaleres den automatisk
    til deg som menneskelig kundeserviceoperatør.
    """
    is_urgent = ticket_in.category in ["REFUND", "PAYMENT_FAILED"]
    status = "ESCALATED_TO_HUMAN" if is_urgent else "AI_HANDLING"
    priority = "HIGH" if is_urgent else "MEDIUM"

    db_ticket = SupportTicket(
        customer_name=ticket_in.customer_name,
        customer_email=ticket_in.customer_email,
        subject=ticket_in.subject,
        category=ticket_in.category,
        status=status,
        priority=priority,
        assigned_to="Deg (Kundeserviceoperatør)"
    )
    db.add(db_ticket)
    db.flush()

    # Legg til kundens melding
    cust_msg = TicketMessage(
        ticket_id=db_ticket.id,
        sender="CUSTOMER",
        sender_name=ticket_in.customer_name,
        message=ticket_in.initial_message
    )
    db.add(cust_msg)

    # Llama AI gir et automatisk første svar og bekrefter at menneske er tilkalt
    ai_text = (
        f"Hei {ticket_in.customer_name}! Llama AI her. "
        f"Jeg har registrert henvendelsen din angående '{ticket_in.subject}'. "
    )
    if is_urgent:
        ai_text += (
            "Siden dette gjelder økonomisk refusjon / betalingsfeil, har jeg umiddelbart "
            "koblet på vår menneskelige kundeserviceleder som overtar samtalen nå straks."
        )
    else:
        ai_text += "Jeg analyserer saken din nå. Vår kundeserviceoperatør er også varslet."

    ai_msg = TicketMessage(
        ticket_id=db_ticket.id,
        sender="LLAMA_AI",
        sender_name="Phink Llama 3.1 AI",
        message=ai_text
    )
    db.add(ai_msg)

    # Revisjonsspor
    audit = AuditLog(
        action="SUPPORT_TICKET_CREATED",
        details=f"Sak #{db_ticket.id} opprettet: {ticket_in.subject} ({ticket_in.category}). Tildelt operatør.",
        ai_assisted=True
    )
    db.add(audit)

    db.commit()
    db.refresh(db_ticket)
    return db_ticket

def _is_resolution_question(text: str) -> bool:
    t = (text or "").strip().lower()
    return any(
        phrase in t
        for phrase in [
            "er ditt problem løst nå",
            "er problemet ditt løst",
            "er problemet løst",
            "problem løst nå",
            "saken løst nå",
        ]
    )


def _is_affirmative_yes(text: str) -> bool:
    cleaned = (text or "").strip().lower().strip(".,!? ")
    if not cleaned:
        return False
    yes_exact = {"ja", "ja takk", "jepp", "jep", "yes", "ok ja", "ja det er løst", "ja, det er løst", "ja det er det", "ja nå er det løst", "ja, nå er det løst"}
    if cleaned in yes_exact:
        return True
    return cleaned.startswith("ja ") or cleaned.startswith("ja,") or cleaned.startswith("ja!")


@router.post("/tickets/{ticket_id}/reply", response_model=TicketMessageResponse)
@router.post("/tickets/{ticket_id}/messages", response_model=TicketMessageResponse)
def reply_to_ticket(ticket_id: int, reply_in: TicketMessageCreate, db: Session = Depends(get_db)):
    """
    Du (operatør) eller kunden sender et svar i saken.
    AUTO-FULLFØRING: Dersom operatør/AI nettopp spurte «Er ditt problem løst nå?»
    og kunden svarer «ja», markeres saken automatisk som RESOLVED og fjernes fra aktiv kø.
    """
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Kundeservicesak ikke funnet.")

    # Sjekk siste melding fra operatør/AI før vi legger til den nye meldingen
    last_staff_msg = (
        db.query(TicketMessage)
        .filter(TicketMessage.ticket_id == ticket.id, TicketMessage.sender != "CUSTOMER")
        .order_by(TicketMessage.id.desc())
        .first()
    )

    # Oppdater status til aktiv operatør
    if reply_in.sender == "OPERATOR_YOU":
        ticket.status = "OPERATOR_ACTIVE"
        ticket.updated_at = datetime.utcnow()

    msg = TicketMessage(
        ticket_id=ticket.id,
        sender=reply_in.sender,
        sender_name=reply_in.sender_name,
        message=reply_in.message
    )
    db.add(msg)

    # Hvis kunden svarer "ja" på "Er ditt problem løst nå?", avslutt og fjern fra aktiv kø automatisk!
    if (
        reply_in.sender == "CUSTOMER"
        and last_staff_msg is not None
        and _is_resolution_question(last_staff_msg.message)
        and _is_affirmative_yes(reply_in.message)
    ):
        ticket.status = "RESOLVED"
        ticket.updated_at = datetime.utcnow()
        db.add(TicketMessage(
            ticket_id=ticket.id,
            sender="SYSTEM",
            sender_name="Phink Kundeservice",
            message="Takk for bekreftelsen! Saken er nå fullført og automatisk fjernet fra aktiv kundeservicekø.",
        ))
        db.add(AuditLog(
            action="SUPPORT_TICKET_AUTO_RESOLVED",
            details=f"Sak #{ticket.id} ({ticket.subject}) ble automatisk fullført og fjernet etter kundens «ja»-bekreftelse.",
            ai_assisted=False,
        ))

    db.commit()
    db.refresh(msg)
    return msg


@router.post("/tickets/resolve-all")
def resolve_all_tickets(db: Session = Depends(get_db)):
    """Markerer alle åpne kundeservicesaker som RESOLVED slik at aktiv kø tømmes."""
    open_tickets = db.query(SupportTicket).filter(SupportTicket.status != "RESOLVED").all()
    count = len(open_tickets)
    now = datetime.utcnow()
    for t in open_tickets:
        t.status = "RESOLVED"
        t.updated_at = now
    if count > 0:
        db.add(AuditLog(
            action="SUPPORT_TICKETS_RESOLVED_ALL",
            details=f"{count} kundeservicesaker ble markert som fullført (RESOLVED) og fjernet fra aktiv kø.",
            ai_assisted=False,
        ))
    db.commit()
    return {"ok": True, "resolved_count": count, "message": f"{count} samtale(r) ble fullført og fjernet fra aktiv kø."}

@router.post("/tickets/{ticket_id}/status")
def update_ticket_status(ticket_id: int, status: str, db: Session = Depends(get_db)):
    """Oppdaterer status på henvendelsen (f.eks. RESOLVED, OPERATOR_ACTIVE, ESCALATED_TO_HUMAN)."""
    ticket = db.query(SupportTicket).filter(SupportTicket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Sak ikke funnet.")
    ticket.status = status
    ticket.updated_at = datetime.utcnow()
    db.commit()
    return {"status": "success", "ticket_id": ticket_id, "new_status": status}

@router.post("/seed-demo")
def seed_demo_support_cases(db: Session = Depends(get_db)):
    """Legger inn eksempelsaker klare for operatøren (deg) å svare på."""
    if db.query(SupportTicket).count() > 0:
        return {"message": "Saker finnes allerede."}

    demo_cases = [
        {
            "customer_name": "Ola Nordmann (Tech AS)",
            "customer_email": "ola@techas.no",
            "subject": "Faktura trakk dobbelt - ønsker refusjon",
            "category": "REFUND",
            "msg": "Hei! Vi oppdaget at lisensfakturaen for november ble trukket to ganger fra bankkontoen vår (kr 2 490,- x 2). Kan dere refundere det overskytende beløpet raskt?",
            "ai_msg": "Hei Ola! Jeg har oppdaget at dette gjelder en refusjon for duplikatbetaling. Jeg har flagget dette som HØY prioritet og sendt saken rett til kundeserviceoperatør for godkjenning av refusjonen."
        },
        {
            "customer_name": "Kari Entreprenør",
            "customer_email": "kari@byggepartner.no",
            "subject": "Betaling av MVA-termin gikk ikke gjennom",
            "category": "PAYMENT_FAILED",
            "msg": "Hei, når jeg forsøkte å godkjenne MVA-oppgjøret i morges fikk jeg feilmeldingen 'Bank gateway timeout'. Har pengene gått ut eller må jeg prøve igjen?",
            "ai_msg": "Hei Kari! Jeg har sjekket transaksjonsloggen; feilen skyldtes en midlertidig timeout hos banken, og ingen penger er trukket. Operatøren vår er koblet på for å bistå deg med ny autorisering."
        }
    ]

    for item in demo_cases:
        ticket = SupportTicket(
            customer_name=item["customer_name"],
            customer_email=item["customer_email"],
            subject=item["subject"],
            category=item["category"],
            status="ESCALATED_TO_HUMAN",
            priority="HIGH",
            assigned_to="Deg (Kundeserviceoperatør)"
        )
        db.add(ticket)
        db.flush()

        msg1 = TicketMessage(
            ticket_id=ticket.id,
            sender="CUSTOMER",
            sender_name=item["customer_name"],
            message=item["msg"]
        )
        msg2 = TicketMessage(
            ticket_id=ticket.id,
            sender="LLAMA_AI",
            sender_name="Phink Llama 3.1 AI",
            message=item["ai_msg"]
        )
        db.add_all([msg1, msg2])

    db.commit()
    return {"message": "Demotilfeller opprettet for operatør."}
