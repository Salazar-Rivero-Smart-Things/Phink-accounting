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
from app.models.accounting import User, CompanySetting, AuditLog

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


def serialize_user(user: User) -> dict:
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
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
    """Oppretter en lokal standard administrator-bruker dersom brukertabellen er tom."""
    if db.query(User).count() > 0:
        return
    owner = User(
        email="admin@phink-acounting.no",
        password_hash=hash_password("Phink2026!"),
        full_name="Phink Administrator",
        role="OWNER",
        entity_type="AS",
        company_name="Phink Regnskap AS",
        org_number="999888777",
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
        role="OWNER" if is_first else "USER",
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
def list_registered_users(db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [serialize_user(u) for u in users]
