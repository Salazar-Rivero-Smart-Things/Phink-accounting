from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
import hashlib
import hmac
import base64
import json
import secrets

from app.config import settings
from app.database import get_db
from app.models.accounting import User, CompanySetting, AuditLog, SubscriptionOrder, SupportTicket, TicketMessage
from datetime import timedelta as _td
import uuid as _uuid

PROFILE_CHANGE_FEE_EX_VAT = 150.0

router = APIRouter(prefix="/auth", tags=["Authentication"])

VALID_ENTITY_TYPES = {"PRIVATE", "ENK", "AS", "FORENING", "INSTITUSJON"}

ENTITY_TYPE_LABELS = {
    "PRIVATE": "Privatperson",
    "ENK": "Enkeltpersonforetak (ENK)",
    "AS": "Aksjeselskap (AS)",
    "FORENING": "Forening / Lag",
    "INSTITUSJON": "Institusjon / Stiftelse",
}


def validate_norwegian_orgnr(orgnr: str) -> tuple[bool, str]:
    """
    Validerer norsk 9-sifret organisasjonsnummer med MOD11 kontrollsiffer
    (Brønnøysundregistrene-standarden).
    """
    digits = "".join(c for c in (orgnr or "") if c.isdigit())
    if len(digits) != 9:
        return False, "Organisasjonsnummer må bestå av nøyaktig 9 siffer."
    weights = [3, 2, 7, 6, 5, 4, 3, 2]
    total = sum(int(digits[i]) * weights[i] for i in range(8))
    remainder = total % 11
    control = 0 if remainder == 0 else 11 - remainder
    if control == 10 or control != int(digits[8]):
        return False, "Organisasjonsnummeret har ugyldig MOD11 kontrollsiffer."
    return True, digits


def validate_norwegian_national_id(fnr: str) -> tuple[bool, str]:
    """
    Validerer format på norsk 11-sifret fødselsnummer / D-nummer.
    """
    digits = "".join(c for c in (fnr or "") if c.isdigit())
    if len(digits) != 11:
        return False, "Fødselsnummer må bestå av nøyaktig 11 siffer."
    day = int(digits[0:2])
    month = int(digits[2:4])
    # D-nummer har dag + 40 (41-71)
    effective_day = day - 40 if day > 40 else day
    if not (1 <= effective_day <= 31 and 1 <= month <= 12):
        return False, "Ugyldig dato i fødselsnummer (DDMMÅÅXXXXX)."
    return True, digits


def mask_national_id(fnr: Optional[str]) -> Optional[str]:
    if not fnr:
        return None
    digits = "".join(c for c in fnr if c.isdigit())
    if len(digits) >= 6:
        return f"{digits[:6]} *****"
    return "***********"


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"pbkdf2_sha256${salt}${dk.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        scheme, salt, hex_dk = stored_hash.split("$", 2)
        if scheme != "pbkdf2_sha256":
            return False
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
        return hmac.compare_digest(dk.hex(), hex_dk)
    except Exception:
        return False


def create_access_token(user: User) -> str:
    exp = int((datetime.utcnow() + timedelta(hours=settings.ACCESS_TOKEN_EXPIRE_HOURS)).timestamp())
    payload = {
        "sub": user.id,
        "email": user.email,
        "role": user.role,
        "entity_type": user.entity_type,
        "exp": exp,
    }
    raw = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")).decode("ascii")
    sig = hmac.new(settings.AUTH_SECRET.encode("utf-8"), raw.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{raw}.{sig}"


def decode_access_token(token: str) -> Optional[dict]:
    try:
        raw, sig = token.split(".", 1)
        expected = hmac.new(settings.AUTH_SECRET.encode("utf-8"), raw.encode("ascii"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(sig, expected):
            return None
        payload = json.loads(base64.urlsafe_b64decode(raw.encode("ascii")).decode("utf-8"))
        if payload.get("exp", 0) < int(datetime.utcnow().timestamp()):
            return None
        return payload
    except Exception:
        return None


def is_owner_email(email: Optional[str]) -> bool:
    if not email:
        return False
    allowed = {e.strip().lower() for e in (settings.OWNER_EMAILS or "").split(",") if e.strip()}
    return email.strip().lower() in allowed


def serialize_user(user: User) -> dict:
    owner_match = is_owner_email(user.email)
    is_admin = owner_match or user.role in ("OWNER", "ADMIN")
    is_support_agent = is_admin or user.role == "SUPPORT_AGENT"
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": "OWNER" if owner_match else user.role,
        "is_admin": is_admin,
        "is_support_agent": is_support_agent,
        "is_customer_account": True,
        "billing_exempt": is_admin,
        "plan_label": (
            "Gratis Administrator, Kundeservice & Kundekonto (Ubegrenset)"
            if is_admin
            else "Standard kundekonto"
        ),
        "entity_type": user.entity_type,
        "entity_type_label": ENTITY_TYPE_LABELS.get(user.entity_type, user.entity_type),
        "company_name": user.company_name,
        "org_number": user.org_number,
        "national_id_masked": mask_national_id(user.national_id),
        "is_active": user.is_active,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=4, max_length=200)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: str = Field(..., min_length=2, max_length=200)
    entity_type: str = Field(default="AS", description="PRIVATE | ENK | AS | FORENING | INSTITUSJON")
    company_name: Optional[str] = None
    org_number: Optional[str] = None
    national_id: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


def seed_default_owner(db: Session):
    """
    Oppretter eier/administrator fra miljøvariablene OWNER_EMAILS og ADMIN_SEED_PASSWORD
    dersom brukertabellen er tom. (Ingen hardkodede passord i kildekoden.)
    """
    if db.query(User).count() > 0:
        return
    if not settings.ADMIN_SEED_PASSWORD:
        return
    primary_email = next((e.strip().lower() for e in settings.OWNER_EMAILS.split(",") if e.strip()), None)
    if not primary_email:
        return
    owner = User(
        email=primary_email,
        password_hash=hash_password(settings.ADMIN_SEED_PASSWORD),
        full_name="Phink Administrator",
        role="OWNER",
        entity_type="AS",
        company_name="Phink Accounting",
        is_active=True,
    )
    db.add(owner)
    db.commit()


@router.post("/register")
def register_user(req: RegisterRequest, db: Session = Depends(get_db)):
    """
    Registrerer ny bruker — enten som Privatperson (fødselsnummer) eller
    Firma/Organisasjon (ENK, AS, Forening, Institusjon med orgnr/fødselsnummer).
    """
    entity_type = (req.entity_type or "AS").strip().upper()
    if entity_type not in VALID_ENTITY_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Ugyldig kontotype '{entity_type}'. Gyldige valg: PRIVATE, ENK, AS, FORENING, INSTITUSJON.",
        )

    email = req.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="E-postadressen er allerede registrert.")

    clean_orgnr = None
    clean_fnr = None

    if entity_type == "PRIVATE":
        if not req.national_id:
            raise HTTPException(status_code=400, detail="Privatperson må oppgi 11-sifret fødselsnummer.")
        ok, val = validate_norwegian_national_id(req.national_id)
        if not ok:
            raise HTTPException(status_code=400, detail=val)
        clean_fnr = val
    elif entity_type == "ENK":
        # ENK kan registreres med organisasjonsnummer (9 siffer) og/eller innehavers fødselsnummer (11 siffer)
        if not req.org_number and not req.national_id:
            raise HTTPException(
                status_code=400,
                detail="ENK må oppgi organisasjonsnummer (9 siffer) eller fødselsnummer (11 siffer).",
            )
        if req.org_number:
            ok, val = validate_norwegian_orgnr(req.org_number)
            if not ok:
                raise HTTPException(status_code=400, detail=val)
            clean_orgnr = val
        if req.national_id:
            ok, val = validate_norwegian_national_id(req.national_id)
            if not ok:
                raise HTTPException(status_code=400, detail=val)
            clean_fnr = val
    else:
        # AS, FORENING, INSTITUSJON krever 9-sifret organisasjonsnummer
        if not req.org_number:
            raise HTTPException(
                status_code=400,
                detail=f"{ENTITY_TYPE_LABELS[entity_type]} må oppgi gyldig 9-sifret organisasjonsnummer.",
            )
        ok, val = validate_norwegian_orgnr(req.org_number)
        if not ok:
            raise HTTPException(status_code=400, detail=val)
        clean_orgnr = val
        if req.national_id:
            ok, val = validate_norwegian_national_id(req.national_id)
            if not ok:
                raise HTTPException(status_code=400, detail=val)
            clean_fnr = val

    company_name = (req.company_name or "").strip() or (
        req.full_name.strip() if entity_type == "PRIVATE" else f"{req.full_name.strip()} {entity_type}"
    )

    is_first = db.query(User).count() == 0
    user = User(
        email=email,
        password_hash=hash_password(req.password),
        full_name=req.full_name.strip(),
        role="OWNER" if (is_first or is_owner_email(email)) else "USER",
        entity_type=entity_type,
        company_name=company_name,
        org_number=clean_orgnr,
        national_id=clean_fnr,
        is_active=True,
    )
    db.add(user)

    # Synkroniser aktiv bedriftsprofil med nyregistrert selskap/privatprofil
    setting = db.query(CompanySetting).first()
    if not setting:
        setting = CompanySetting()
        db.add(setting)
    setting.company_name = company_name
    setting.entity_type = entity_type
    if clean_orgnr:
        setting.org_number = clean_orgnr
    if clean_fnr:
        setting.national_id = clean_fnr
    setting.email = email

    db.add(AuditLog(
        action="USER_REGISTER",
        details=f"Ny konto registrert: {email} ({ENTITY_TYPE_LABELS[entity_type]} - {company_name})",
        ai_assisted=False,
    ))
    db.commit()
    db.refresh(user)

    token = create_access_token(user)
    return {
        "ok": True,
        "access_token": token,
        "token_type": "bearer",
        "user": serialize_user(user),
    }


@router.post("/login")
def login_user(req: LoginRequest, db: Session = Depends(get_db)):
    email = req.email.strip().lower()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Feil e-postadresse eller passord.")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Brukerkontoen er deaktivert.")

    token = create_access_token(user)
    return {
        "ok": True,
        "access_token": token,
        "token_type": "bearer",
        "user": serialize_user(user),
    }


@router.get("/me")
def get_current_user(
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Ikke innlogget.")
    token = authorization[7:].strip()
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Ugyldig eller utløpt innloggingstoken.")
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=401, detail="Bruker ikke funnet.")
    return {"ok": True, "user": serialize_user(user)}


@router.get("/users")
def list_registered_users(
    q: Optional[str] = None,
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    """
    Henter registrerte brukere/kunder.
    Støtter søk (?q=...) på navn, firmanavn, e-post, organisasjonsnummer
    og (for innlogget Administrator) fødsels- og personnummer.
    """
    is_admin_caller = False
    if authorization and authorization.lower().startswith("bearer "):
        payload = decode_access_token(authorization[7:].strip())
        if payload:
            actor = db.query(User).filter(User.id == payload.get("sub")).first()
            if actor and (is_owner_email(actor.email) or actor.role in ("OWNER", "ADMIN")):
                is_admin_caller = True

    users = db.query(User).order_by(User.created_at.desc()).all()
    if q and q.strip():
        needle = q.strip().lower()
        needle_digits = "".join(c for c in needle if c.isdigit())
        filtered = []
        for u in users:
            haystack = " ".join([
                u.full_name or "",
                u.company_name or "",
                u.email or "",
                u.entity_type or "",
                ENTITY_TYPE_LABELS.get(u.entity_type, ""),
            ]).lower()
            org_digits = "".join(c for c in (u.org_number or "") if c.isdigit())
            fnr_digits = "".join(c for c in (u.national_id or "") if c.isdigit()) if is_admin_caller else ""
            if (
                needle in haystack
                or (needle_digits and needle_digits in org_digits)
                or (is_admin_caller and needle_digits and needle_digits in fnr_digits)
            ):
                filtered.append(u)
        users = filtered
    return [serialize_user(u) for u in users]


class ProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = None
    company_name: Optional[str] = None
    entity_type: Optional[str] = None
    org_number: Optional[str] = None
    national_id: Optional[str] = None
    payment_method: str = Field(default="VIPPS_BEDRIFT", description="VIPPS_BEDRIFT eller FAKTURA (for kundegebyr 150 kr)")
    target_user_id: Optional[int] = None  # Kun for administrator som skal rette profilen til en kunde


@router.put("/profile")
def update_user_profile(
    req: ProfileUpdateRequest,
    authorization: Optional[str] = Header(default=None),
    db: Session = Depends(get_db),
):
    """
    Lar både kunde og administrator korrigere/oppdatere profilopplysninger ved feil.
    - Kunde: koster 150 kr eks. MVA (187,50 kr inkl. 25 % MVA) via Vipps Bedrift eller tilsendt faktura.
    - Administrator (OWNER/ADMIN): 0 kr (gratis), kan også oppdatere kunders profiler via target_user_id.
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Du må være innlogget for å endre profilen.")
    payload = decode_access_token(authorization[7:].strip())
    if not payload:
        raise HTTPException(status_code=401, detail="Ugyldig eller utløpt innloggingstoken.")

    actor = db.query(User).filter(User.id == payload.get("sub")).first()
    if not actor:
        raise HTTPException(status_code=401, detail="Bruker ikke funnet.")

    actor_is_admin = is_owner_email(actor.email) or actor.role in ("OWNER", "ADMIN")
    target = actor
    if req.target_user_id and req.target_user_id != actor.id:
        if not actor_is_admin:
            raise HTTPException(status_code=403, detail="Kun administrator kan endre andre brukeres profiler.")
        target = db.query(User).filter(User.id == req.target_user_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="Kundebruker ikke funnet.")

    new_entity = (req.entity_type or target.entity_type or "AS").strip().upper()
    if new_entity not in VALID_ENTITY_TYPES:
        raise HTTPException(status_code=400, detail=f"Ugyldig kontotype '{new_entity}'.")

    validated_orgnr = None
    if req.org_number is not None and req.org_number.strip():
        ok, val = validate_norwegian_orgnr(req.org_number)
        if not ok:
            raise HTTPException(status_code=400, detail=val)
        validated_orgnr = val

    validated_fnr = None
    if req.national_id is not None and req.national_id.strip():
        ok, val = validate_norwegian_national_id(req.national_id)
        if not ok:
            raise HTTPException(status_code=400, detail=val)
        validated_fnr = val

    # VANLIG KUNDE: Profilen er låst etter registrering — kunden sender en betalt forespørsel (150 kr)
    # direkte til Administrator i Kundeservice Desk, slik at KUN Administrator redigerer profilen!
    if not actor_is_admin:
        method = (req.payment_method or "VIPPS_BEDRIFT").strip().upper()
        if method not in ("VIPPS_BEDRIFT", "FAKTURA"):
            raise HTTPException(status_code=400, detail="Endringsgebyr (150 kr) kan kun betales med VIPPS_BEDRIFT eller FAKTURA.")
        setting = db.query(CompanySetting).first()
        vat_amt = round(PROFILE_CHANGE_FEE_EX_VAT * 0.25, 2)
        total_inc = round(PROFILE_CHANGE_FEE_EX_VAT + vat_amt, 2)
        ref = f"PROFIL-{_uuid.uuid4().hex[:6].upper()}"
        order = SubscriptionOrder(
            customer_name=target.company_name or target.full_name,
            customer_email=target.email,
            org_number=target.org_number,
            plan_id="PROFILE_CHANGE",
            plan_name="Forespørsel om profilendring av Administrator (150 kr eks. MVA)",
            payment_method=method,
            amount_ex_vat=PROFILE_CHANGE_FEE_EX_VAT,
            vat_amount=vat_amt,
            total_amount=total_inc,
            vipps_number=(setting.vipps_number if setting and method == "VIPPS_BEDRIFT" else None),
            payment_reference=ref,
            status="INVOICE_SENT" if method == "FAKTURA" else "PENDING",
            due_date=datetime.utcnow() + _td(days=14),
        )
        db.add(order)

        # Opprett kundeservice-sak til Administrator med de ønskede endringene
        change_summary = (
            f"Kunde {target.email} ber Administrator om å endre låst profil (Gebyr: 150 kr eks. MVA / {total_inc:.2f} kr inkl. MVA via {method}, Ref: {ref}):\n"
            f"- Navn: {target.full_name} -> {req.full_name or target.full_name}\n"
            f"- Firma: {target.company_name} -> {req.company_name or target.company_name}\n"
            f"- Selskapsform: {target.entity_type} -> {new_entity}\n"
            f"- Orgnr: {target.org_number or '—'} -> {validated_orgnr or target.org_number or '—'}"
        )
        ticket = SupportTicket(
            customer_name=target.full_name,
            customer_email=target.email,
            subject=f"Profilendring (150 kr) — {target.company_name or target.full_name}",
            category="PROFILE_CHANGE",
            status="ESCALATED_TO_HUMAN",
            priority="HIGH",
            assigned_to="Administrator (Deg)",
        )
        db.add(ticket)
        db.flush()
        db.add(TicketMessage(
            ticket_id=ticket.id,
            sender="CUSTOMER",
            sender_name=target.full_name,
            message=change_summary,
        ))
        db.add(AuditLog(
            action="PROFILE_CHANGE_REQUESTED",
            details=f"Kunde {target.email} sendte forespørsel om profilendring (150 kr, Ref: {ref}, Sak #{ticket.id}).",
            ai_assisted=False,
        ))
        db.commit()

        return {
            "ok": True,
            "pending_admin_approval": True,
            "ticket_id": ticket.id,
            "user": serialize_user(target),
            "fee": {
                "fee_ex_vat": PROFILE_CHANGE_FEE_EX_VAT,
                "vat_amount": vat_amt,
                "total_inc_vat": total_inc,
                "payment_method": method,
                "payment_reference": ref,
            },
            "message": (
                f"Forespørsel om profilendring er sendt til Administrator (Sak #{ticket.id})! "
                f"Endringsgebyr: 150 kr eks. MVA ({total_inc:.2f} kr inkl. MVA) via {method} (Ref: {ref}). "
                f"Kun Administrator kan åpne og oppdatere profilen din."
            ),
        }

    # ADMINISTRATOR: Utfører profilendring umiddelbart (0 kr) — på egen eller kundes konto!
    if validated_orgnr:
        target.org_number = validated_orgnr
    if validated_fnr:
        target.national_id = validated_fnr
    if req.full_name and req.full_name.strip():
        target.full_name = req.full_name.strip()
    if req.company_name and req.company_name.strip():
        target.company_name = req.company_name.strip()
    target.entity_type = new_entity

    setting = db.query(CompanySetting).first()
    if setting and target.id == actor.id:
        if target.company_name:
            setting.company_name = target.company_name
        setting.entity_type = target.entity_type
        if target.org_number:
            setting.org_number = target.org_number
        if target.national_id:
            setting.national_id = target.national_id

    fee_info = {"fee_ex_vat": 0.0, "vat_amount": 0.0, "total_inc_vat": 0.0, "payment_reference": "ADMIN-FREE"}
    db.add(AuditLog(
        action="PROFILE_UPDATED_BY_ADMIN",
        details=f"Administrator ({actor.email}) oppdaterte profilen til {target.email} (0 kr).",
        ai_assisted=False,
    ))
    db.commit()
    db.refresh(target)

    return {
        "ok": True,
        "pending_admin_approval": False,
        "user": serialize_user(target),
        "fee": fee_info,
        "message": f"Administrator oppdaterte profilen for {target.email} (0 kr).",
    }
