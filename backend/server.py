from fastapi import (
    FastAPI,
    APIRouter,
    HTTPException,
    Depends,
    Header,
    Request,
    Response,
)
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import secrets
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr, validator
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import json
import re

# Optional integrations - handle missing modules gracefully
try:
    from emergentintegrations.llm.chat import LlmChat, UserMessage

    EMERGENT_LLM_AVAILABLE = True
except ImportError:
    EMERGENT_LLM_AVAILABLE = False
    LlmChat = None
    UserMessage = None

try:
    from emergentintegrations.payments.stripe.checkout import (
        StripeCheckout,
        CheckoutSessionResponse,
        CheckoutStatusResponse,
        CheckoutSessionRequest,
    )

    STRIPE_CHECKOUT_AVAILABLE = True
except ImportError:
    STRIPE_CHECKOUT_AVAILABLE = False
    StripeCheckout = None
    CheckoutSessionResponse = None
    CheckoutStatusResponse = None
    CheckoutSessionRequest = None

# Rate limiting imports
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Security middleware imports
from starlette.middleware.base import BaseHTTPMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

# MongoDB connection
mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

# JWT Configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "reach_jwt_secret_key")
JWT_ALGORITHM = os.environ.get("JWT_ALGORITHM", "HS256")
JWT_EXPIRY_HOURS = int(os.environ.get("JWT_EXPIRY_HOURS", 24))

# CSRF Configuration
CSRF_SECRET = os.environ.get("CSRF_SECRET", secrets.token_hex(32))
CSRF_TOKEN_NAME = "x-csrf-token"
CSRF_COOKIE_NAME = "csrf_token"

# Cookie Configuration
ACCESS_TOKEN_COOKIE_NAME = "access_token"
REFRESH_TOKEN_COOKIE_NAME = "refresh_token"
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "true").lower() == "true"
COOKIE_HTTPONLY = True
COOKIE_SAMESITE_RAW = os.environ.get("COOKIE_SAMESITE", "lax")
# Validate SameSite value - use typing.cast to satisfy type checker
from typing import Literal, cast

if COOKIE_SAMESITE_RAW in ["lax", "strict", "none"]:
    COOKIE_SAMESITE = cast(Literal["lax", "strict", "none"], COOKIE_SAMESITE_RAW)
else:
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
COOKIE_DOMAIN = os.environ.get("COOKIE_DOMAIN", None)

# LLM Configuration
EMERGENT_LLM_KEY = os.environ.get("EMERGENT_LLM_KEY")

# Stripe Configuration
STRIPE_API_KEY = os.environ.get("STRIPE_API_KEY")

# Sentry Configuration
SENTRY_DSN = os.environ.get("SENTRY_DSN")

# Setup logging
logger = logging.getLogger(__name__)

# Initialize Sentry if DSN is provided
if SENTRY_DSN:
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        from sentry_sdk.integrations.starlette import StarletteIntegration

        sentry_sdk.init(
            dsn=SENTRY_DSN,
            integrations=[
                FastApiIntegration(),
                StarletteIntegration(),
            ],
            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for performance monitoring.
            traces_sample_rate=0.1,
            # Set profiles_sample_rate to 1.0 to profile 100%
            # of sampled transactions.
            profiles_sample_rate=0.1,
            environment=os.environ.get("ENVIRONMENT", "development"),
            release=f"reach@{os.environ.get('VERSION', '1.0.0')}",
        )
        logger.info("Sentry initialized for error tracking")
    except ImportError:
        logger.warning("Sentry SDK not installed. Install with: pip install sentry-sdk")
    except Exception as e:
        logger.error(f"Failed to initialize Sentry: {e}")
else:
    logger.info("Sentry DSN not provided, error tracking disabled")

# Create the main app
app = FastAPI(title="Reach API", description="AI-powered reachability platform")

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Rate limit decorator
rate_limit = limiter.limit

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Configure structured logging
import json
from pythonjsonlogger import jsonlogger


class StructuredLogger:
    """Structured logger that outputs JSON for machine parsing"""

    def __init__(self, name):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Remove existing handlers
        self.logger.handlers.clear()

        # Create JSON formatter
        formatter = jsonlogger.JsonFormatter(
            "%(asctime)s %(name)s %(levelname)s %(message)s",
            rename_fields={"asctime": "timestamp", "levelname": "level"},
            datefmt="%Y-%m-%dT%H:%M:%SZ",
        )

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)

        # File handler for structured logs
        try:
            file_handler = logging.FileHandler("app_structured.log")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            print(f"Could not create structured log file: {e}")

    def _create_log_record(self, level, message, **kwargs):
        """Create structured log record"""
        extra = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level.upper(),
            **kwargs,
        }
        return extra

    def info(self, message, **kwargs):
        extra = self._create_log_record("info", message, **kwargs)
        self.logger.info(message, extra=extra)

    def error(self, message, **kwargs):
        extra = self._create_log_record("error", message, **kwargs)
        self.logger.error(message, extra=extra)

    def warning(self, message, **kwargs):
        extra = self._create_log_record("warning", message, **kwargs)
        self.logger.warning(message, extra=extra)

    def debug(self, message, **kwargs):
        extra = self._create_log_record("debug", message, **kwargs)
        self.logger.debug(message, extra=extra)


# Initialize structured logger
try:
    logger = StructuredLogger(__name__)
    logger.info("Structured logging initialized")
except Exception as e:
    # Fallback to basic logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)
    logger.warning(f"Structured logging failed, using basic logging: {e}")

# Audit logger
audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)

# Create file handler for audit logs
try:
    audit_handler = logging.FileHandler("audit.log")
    audit_handler.setLevel(logging.INFO)
    audit_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - AUDIT - %(levelname)s - %(message)s"
    )
    audit_handler.setFormatter(audit_formatter)
    audit_logger.addHandler(audit_handler)
except Exception as e:
    logger.warning(f"Could not create audit log file: {e}")


def log_audit_event(
    event_type: str,
    user_id: Optional[str],
    ip_address: Optional[str],
    details: Dict[str, Any],
):
    """Log audit event with structured data"""
    audit_data = {
        "event_type": event_type,
        "user_id": user_id,
        "ip_address": ip_address,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details,
    }
    audit_logger.info(json.dumps(audit_data))


def get_client_ip(request: Request) -> str:
    """Get client IP address from request"""
    if request.client:
        return request.client.host
    return "unknown"


# ==================== MODELS ====================


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str

    @validator("password")
    def validate_password(cls, v):
        if len(v) < 12:
            raise ValueError("Password must be at least 12 characters long")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one number")
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in v):
            raise ValueError("Password must contain at least one special character")
        # Check for common passwords
        common_passwords = ["password", "123456", "qwerty", "letmein", "welcome"]
        if v.lower() in common_passwords:
            raise ValueError("Password is too common")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    name: str
    created_at: str


class TokenResponse(BaseModel):
    user: UserResponse
    csrf_token: Optional[str] = None


class IdentityCreate(BaseModel):
    handle: str
    type: str = "person"  # person or org
    bio: Optional[str] = None

    @validator("handle")
    def validate_handle(cls, v):
        if len(v) < 3:
            raise ValueError("Handle must be at least 3 characters long")
        if len(v) > 30:
            raise ValueError("Handle must be at most 30 characters long")
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Handle can only contain letters, numbers, underscores, and hyphens"
            )
        if v.lower() in ["admin", "root", "system", "api", "auth", "login", "register"]:
            raise ValueError("Handle is reserved")
        return v.lower()

    @validator("type")
    def validate_type(cls, v):
        if v not in ["person", "org"]:
            raise ValueError("Type must be either 'person' or 'org'")
        return v

    @validator("bio")
    def validate_bio(cls, v):
        if v and len(v) > 500:
            raise ValueError("Bio must be at most 500 characters long")
        # Basic HTML/script sanitization
        if v and ("<script>" in v.lower() or "javascript:" in v.lower()):
            raise ValueError("Bio contains invalid content")
        return v


class FaceCreate(BaseModel):
    handle: str
    display_name: str
    headline: str
    current_focus: str
    availability_signal: str
    prompt: str
    photo_url: Optional[str] = None
    links: Optional[List[Dict[str, str]]] = None

    @validator("handle")
    def validate_handle(cls, v):
        if len(v) < 3:
            raise ValueError("Handle must be at least 3 characters long")
        if len(v) > 30:
            raise ValueError("Handle must be at most 30 characters long")
        if not re.match(r"^[a-zA-Z0-9_-]+$", v):
            raise ValueError(
                "Handle can only contain letters, numbers, underscores, and hyphens"
            )
        if v.lower() in ["admin", "root", "system", "api", "auth", "login", "register"]:
            raise ValueError("Handle is reserved")
        return v.lower()

    @validator("display_name")
    def validate_display_name(cls, v):
        if len(v) < 2:
            raise ValueError("Display name must be at least 2 characters long")
        if len(v) > 50:
            raise ValueError("Display name must be at most 50 characters long")
        if "<script>" in v.lower() or "javascript:" in v.lower():
            raise ValueError("Display name contains invalid content")
        return v.strip()

    @validator("headline")
    def validate_headline(cls, v):
        if len(v) < 10:
            raise ValueError("Headline must be at least 10 characters long")
        if len(v) > 100:
            raise ValueError("Headline must be at most 100 characters long")
        if "<script>" in v.lower() or "javascript:" in v.lower():
            raise ValueError("Headline contains invalid content")
        return v.strip()

    @validator("current_focus")
    def validate_current_focus(cls, v):
        if len(v) < 20:
            raise ValueError("Current focus must be at least 20 characters long")
        if len(v) > 300:
            raise ValueError("Current focus must be at most 300 characters long")
        if "<script>" in v.lower() or "javascript:" in v.lower():
            raise ValueError("Current focus contains invalid content")
        return v.strip()

    @validator("availability_signal")
    def validate_availability_signal(cls, v):
        if len(v) < 10:
            raise ValueError("Availability signal must be at least 10 characters long")
        if len(v) > 200:
            raise ValueError("Availability signal must be at most 200 characters long")
        if "<script>" in v.lower() or "javascript:" in v.lower():
            raise ValueError("Availability signal contains invalid content")
        return v.strip()

    @validator("prompt")
    def validate_prompt(cls, v):
        if len(v) < 10:
            raise ValueError("Prompt must be at least 10 characters long")
        if len(v) > 200:
            raise ValueError("Prompt must be at most 200 characters long")
        if "<script>" in v.lower() or "javascript:" in v.lower():
            raise ValueError("Prompt contains invalid content")
        return v.strip()

    @validator("photo_url")
    def validate_photo_url(cls, v):
        if v:
            if len(v) > 500:
                raise ValueError("Photo URL is too long")
            if not v.startswith(("http://", "https://")):
                raise ValueError("Photo URL must start with http:// or https://")
            if "<script>" in v.lower() or "javascript:" in v.lower():
                raise ValueError("Photo URL contains invalid content")
        return v

    @validator("links")
    def validate_links(cls, v):
        if v:
            if len(v) > 2:
                raise ValueError("Maximum 2 links allowed")
            for link in v:
                if "label" not in link or "url" not in link:
                    raise ValueError("Each link must have 'label' and 'url' fields")
                if len(link["label"]) > 30:
                    raise ValueError("Link label must be at most 30 characters long")
                if len(link["url"]) > 500:
                    raise ValueError("Link URL is too long")
                if not link["url"].startswith(("http://", "https://")):
                    raise ValueError("Link URL must start with http:// or https://")
                if (
                    "<script>" in link["url"].lower()
                    or "javascript:" in link["url"].lower()
                ):
                    raise ValueError("Link URL contains invalid content")
        return v


class IdentityResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    handle: str
    type: str
    bio: Optional[str] = None
    public_url: str
    created_at: str
    face_completed: bool = False
    display_name: Optional[str] = None
    headline: Optional[str] = None
    current_focus: Optional[str] = None
    availability_signal: Optional[str] = None
    prompt: Optional[str] = None
    photo_url: Optional[str] = None
    links: Optional[List[Dict[str, str]]] = None
    modules_config: Optional[Dict[str, Any]] = None


class SlotCreate(BaseModel):
    name: str
    description: str
    visibility: str = "public"  # public, private, link-only


class SlotUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    visibility: Optional[str] = None


class SlotResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    identity_id: str
    name: str
    description: str
    visibility: str
    reach_policy: Optional[Dict[str, Any]] = None
    created_at: str


class PolicyUpdate(BaseModel):
    conditions: List[Dict[str, Any]]
    actions: Dict[str, Any]
    fallback: str = "reject"
    payment_amount: Optional[float] = None


class FaceReachAttemptCreate(BaseModel):
    """Model for Face-based reach attempts with module data"""

    message: str
    challenge_answer: Optional[str] = None
    time_requirement: Optional[str] = None
    intent_category: Optional[str] = None

    @validator("message")
    def validate_message(cls, v):
        if len(v) < 10:
            raise ValueError("Message must be at least 10 characters long")
        if len(v) > 2000:
            raise ValueError("Message must be at most 2000 characters long")
        # Basic sanitization
        v = v.strip()
        if "<script>" in v.lower() or "javascript:" in v.lower():
            raise ValueError("Message contains invalid content")
        return v


class ReachAttemptCreate(BaseModel):
    intent: str
    reason: str
    message: Optional[str] = None
    sender_email: Optional[str] = None
    sender_name: Optional[str] = None

    @validator("intent")
    def validate_intent(cls, v):
        valid_intents = [
            "business",
            "personal",
            "collaboration",
            "question",
            "feedback",
            "other",
        ]
        if v not in valid_intents:
            raise ValueError(f"Intent must be one of: {', '.join(valid_intents)}")
        return v

    @validator("reason")
    def validate_reason(cls, v):
        if len(v) < 5:
            raise ValueError("Reason must be at least 5 characters long")
        if len(v) > 200:
            raise ValueError("Reason must be at most 200 characters long")
        # Basic sanitization
        v = v.strip()
        if "<script>" in v.lower() or "javascript:" in v.lower():
            raise ValueError("Reason contains invalid content")
        return v

    @validator("message")
    def validate_message(cls, v):
        if v and len(v) > 5000:
            raise ValueError("Message must be at most 5000 characters long")
        if v and ("<script>" in v.lower() or "javascript:" in v.lower()):
            raise ValueError("Message contains invalid content")
        return v

    @validator("sender_email")
    def validate_sender_email(cls, v):
        if v:
            # Basic email validation
            if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", v):
                raise ValueError("Invalid email format")
            if len(v) > 254:
                raise ValueError("Email is too long")
        return v

    @validator("sender_name")
    def validate_sender_name(cls, v):
        if v and len(v) > 100:
            raise ValueError("Sender name must be at most 100 characters long")
        if v and ("<script>" in v.lower() or "javascript:" in v.lower()):
            raise ValueError("Sender name contains invalid content")
        return v


class ReachAttemptResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    identity_id: str
    slot_id: Optional[str] = None
    sender_context: Dict[str, Any]
    payload: Dict[str, Any]
    ai_classification: Optional[Dict[str, Any]] = None
    decision: str
    rationale: str
    auto_response: Optional[str] = None
    payment_status: Optional[str] = None
    payment_amount: Optional[float] = None
    checkout_url: Optional[str] = None
    created_at: str


class PaymentCheckoutRequest(BaseModel):
    reach_attempt_id: str
    origin_url: str


# ==================== MODULE SYSTEM MODELS ====================


class ModuleConfigBase(BaseModel):
    enabled: bool = False


class IntentCategoriesConfig(ModuleConfigBase):
    categories: List[str] = []


class TimeSignalConfig(ModuleConfigBase):
    pass  # No configuration needed, just enabled/disabled


class ChallengeQuestionConfig(ModuleConfigBase):
    question: str = ""


class WaitingPeriodConfig(ModuleConfigBase):
    seconds: int = 30  # 30, 60, or 90


class DepositConfig(ModuleConfigBase):
    amount_usd: float = 5.0
    response_days: int = 7


class RulesEngineConfig(ModuleConfigBase):
    rules: List[str] = []


class CapacityControlsConfig(ModuleConfigBase):
    max_approved_per_week: Optional[int] = None
    handle_expiry_date: Optional[str] = None  # ISO format date
    sender_cooldown_days: Optional[int] = None
    daily_submission_cap: Optional[int] = None


class ModulesConfig(BaseModel):
    intent_categories: IntentCategoriesConfig = IntentCategoriesConfig()
    time_signal: TimeSignalConfig = TimeSignalConfig()
    challenge_question: ChallengeQuestionConfig = ChallengeQuestionConfig()
    waiting_period: WaitingPeriodConfig = WaitingPeriodConfig()
    deposit: DepositConfig = DepositConfig()
    rules_engine: RulesEngineConfig = RulesEngineConfig()
    capacity_controls: CapacityControlsConfig = CapacityControlsConfig()


class ModulesConfigUpdate(BaseModel):
    intent_categories: Optional[IntentCategoriesConfig] = None
    time_signal: Optional[TimeSignalConfig] = None
    challenge_question: Optional[ChallengeQuestionConfig] = None
    waiting_period: Optional[WaitingPeriodConfig] = None
    deposit: Optional[DepositConfig] = None
    rules_engine: Optional[RulesEngineConfig] = None
    capacity_controls: Optional[CapacityControlsConfig] = None


# ==================== COOKIE & CSRF UTILITIES ====================


def create_csrf_token() -> str:
    """Create a CSRF token"""
    return secrets.token_urlsafe(32)


def verify_csrf_token(csrf_token: str, csrf_cookie: str) -> bool:
    """Verify CSRF token matches cookie"""
    return csrf_token == csrf_cookie


def set_auth_cookies(
    response: Response,
    access_token: str,
    csrf_token: str,
    max_age: int = JWT_EXPIRY_HOURS * 3600,
):
    """Set authentication cookies"""
    # Set access token cookie (httpOnly, secure)
    response.set_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        value=access_token,
        max_age=max_age,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        domain=COOKIE_DOMAIN,
    )

    # Set CSRF token cookie (not httpOnly, for JavaScript access)
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        max_age=max_age,
        httponly=False,  # JavaScript needs to read this
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        domain=COOKIE_DOMAIN,
    )


def clear_auth_cookies(response: Response):
    """Clear authentication cookies on logout"""
    response.delete_cookie(
        key=ACCESS_TOKEN_COOKIE_NAME,
        httponly=COOKIE_HTTPONLY,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        domain=COOKIE_DOMAIN,
    )
    response.delete_cookie(
        key=CSRF_COOKIE_NAME,
        httponly=False,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        domain=COOKIE_DOMAIN,
    )


async def get_current_user_from_cookie(request: Request) -> dict:
    """Get current user from access token cookie"""
    access_token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        payload = jwt.decode(access_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def verify_csrf_header(request: Request):
    """Verify CSRF token from header matches cookie"""
    csrf_token = request.headers.get(CSRF_TOKEN_NAME)
    csrf_cookie = request.cookies.get(CSRF_COOKIE_NAME)

    if not csrf_token or not csrf_cookie:
        raise HTTPException(status_code=403, detail="CSRF token missing")

    if not verify_csrf_token(csrf_token, csrf_cookie):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")


# ==================== AUTH UTILITIES ====================


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_token(user_id: str, email: str) -> str:
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.now(timezone.utc) + timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


async def get_current_user(request: Request, authorization: str = Header(None)):
    """Get current user from either cookie (preferred) or Authorization header (legacy)"""
    # Try cookie first
    access_token = request.cookies.get(ACCESS_TOKEN_COOKIE_NAME)
    if access_token:
        try:
            payload = jwt.decode(access_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0})
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            return user
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    # Fall back to Authorization header for backward compatibility
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user = await db.users.find_one({"id": payload["user_id"]}, {"_id": 0})
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            return user
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")

    raise HTTPException(status_code=401, detail="Not authenticated")


def get_user_rate_limit_key(request: Request):
    """Get rate limit key based on user ID for user-specific rate limiting"""
    # This is a placeholder - in a real implementation, we'd need to
    # get the user from the request context somehow
    # For now, just use IP address
    return get_remote_address(request)


# ==================== AI SERVICE ====================


async def classify_reach_attempt(slot: dict, attempt: ReachAttemptCreate) -> dict:
    """Use AI to classify the reach attempt and determine outcome"""
    if not EMERGENT_LLM_AVAILABLE:
        # Fallback classification if LLM not available
        return {
            "classification": {"intent_type": "unknown", "confidence": 0.5},
            "decision": "queue",
            "reason": "LLM service not available, queued for manual review",
        }

    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"reach-{uuid.uuid4()}",
            system_message="""You are the Reach AI Operator. Your job is to classify incoming reach attempts and determine the appropriate outcome based on the slot's policy.

You must analyze the sender's intent, reason, and message, then return a JSON response with:
- classification: object with "intent_type" (business, personal, spam, urgent, unknown) and "confidence" (0-1)
- decision: one of "deliver_to_human", "deliver_to_ai", "queue", "reject", "request_payment", "request_more_info", "auto_respond"
- rationale: brief explanation of your decision (1-2 sentences)
- auto_response: if decision is auto_respond, include the response text

IMPORTANT: Return ONLY valid JSON, no markdown or extra text.""",
        ).with_model("openai", "gpt-5.2")

        policy = slot.get("reach_policy", {})
        policy_text = (
            json.dumps(policy)
            if policy
            else "No specific policy set. Default: accept business inquiries, reject spam, queue personal."
        )

        user_message = UserMessage(
            text=f"""Evaluate this reach attempt for slot "{slot.get("name", "unknown")}":

Slot Description: {slot.get("description", "No description")}
Slot Policy: {policy_text}

Sender Intent: {attempt.intent}
Sender Reason: {attempt.reason}
Message: {attempt.message or "No message provided"}
Sender Email: {attempt.sender_email or "Anonymous"}
Sender Name: {attempt.sender_name or "Unknown"}

Return your classification as JSON."""
        )

        response = await chat.send_message(user_message)

        # Parse AI response
        try:
            # Clean response if needed
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            result = json.loads(cleaned)
        except json.JSONDecodeError:
            # Fallback response
            result = {
                "classification": {"intent_type": "unknown", "confidence": 0.5},
                "decision": "queue",
                "rationale": "Unable to parse AI response, queuing for human review.",
            }

        return result

    except Exception as e:
        logger.error(f"AI classification error: {e}")
        return {
            "classification": {"intent_type": "unknown", "confidence": 0},
            "decision": "queue",
            "rationale": f"AI service unavailable, queuing for human review.",
        }


async def evaluate_rules_simple_keyword_matching(
    rules: List[str], submission_data: Dict[str, Any], identity_name: str
) -> Dict[str, Any]:
    """
    Evaluate submission against rules using simple keyword matching.
    Used when LLM is not available.

    Supports simple patterns like:
    - "message contains 'quick sync'"
    - "reject messages about spam"
    - "auto_approve if message has 'urgent'"
    """
    import re  # Move import to top of function

    message = submission_data.get("message", "").lower()
    triggered_rules = []

    # Parse each rule (stored as JSON string)
    for rule_str in rules:
        try:
            rule = json.loads(rule_str)
            rule_text = rule.get("condition", "").lower()
            rule_action = rule.get("action", "").lower()
            rule_reason = rule.get("reason", "")
            rule_enabled = rule.get("enabled", True)

            if not rule_enabled:
                continue

            # Simple keyword matching for "message contains 'keyword'"
            if "message contains" in rule_text:
                # Extract keyword between quotes
                matches = re.findall(r"message contains ['\"]([^'\"]+)['\"]", rule_text)
                for keyword in matches:
                    if keyword.lower() in message:
                        triggered_rules.append(
                            {
                                "rule": rule_str,
                                "applies": True,
                                "action": rule_action,
                                "confidence": 0.9,
                                "reasoning": f"Message contains keyword '{keyword}'",
                                "suggested_response": rule_reason,
                            }
                        )
                        break

        except (json.JSONDecodeError, KeyError):
            # Skip malformed rules
            continue

            # Simple keyword matching for "message contains 'keyword'"
            if "message contains" in rule_text:
                # Extract keyword between quotes
                import re

                matches = re.findall(r"message contains ['\"]([^'\"]+)['\"]", rule_text)
                for keyword in matches:
                    if keyword.lower() in message:
                        triggered_rules.append(
                            {
                                "rule": rule_str,
                                "applies": True,
                                "action": rule_action,
                                "confidence": 0.9,
                                "reasoning": f"Message contains keyword '{keyword}'",
                                "suggested_response": rule_reason,
                            }
                        )
                        break

        except (json.JSONDecodeError, KeyError):
            # Skip malformed rules
            continue

    # Determine final decision based on triggered rules
    # Priority: reject > ask_for_more_context > queue_for_review > auto_approve
    final_decision = "queue_for_review"
    reasoning_summary = "No rules triggered, queuing for review"

    if triggered_rules:
        actions = [rule.get("action") for rule in triggered_rules]
        if "reject" in actions:
            final_decision = "auto_reject"
            reasoning_summary = "Message rejected by keyword matching rule"
        elif "ask_for_more_context" in actions:
            final_decision = "ask_for_more_context"
            reasoning_summary = "More context requested by rule"
        elif "auto_approve" in actions:
            final_decision = "auto_approve"
            reasoning_summary = "Message auto-approved by keyword matching rule"

    return {
        "final_decision": final_decision,
        "triggered_rules": triggered_rules,
        "reasoning_summary": reasoning_summary,
        "llm_failed": True,  # Mark as LLM failed since we're using fallback
    }


async def evaluate_rules_with_llm(
    rules: List[str], submission_data: Dict[str, Any], identity_name: str
) -> Dict[str, Any]:
    """
    Evaluate submission against owner's plain language rules using LLM.
    Falls back to simple keyword matching when LLM is not available.

    Returns:
    {
        "final_decision": "auto_approve" | "auto_reject" | "ask_for_more_context" | "queue_for_review",
        "triggered_rules": [
            {
                "rule": "original rule text",
                "applies": True/False,
                "action": "auto_approve" | "auto_reject" | "ask_for_more_context" | "queue_for_review" | "none",
                "confidence": 0.0-1.0,
                "reasoning": "plain English explanation",
                "suggested_response": "optional response text if action requires it"
            }
        ],
        "reasoning_summary": "Overall reasoning for final decision",
        "llm_failed": False
    }
    """
    if not EMERGENT_LLM_AVAILABLE:
        # Fall back to simple keyword matching when LLM is not available
        return await evaluate_rules_simple_keyword_matching(
            rules, submission_data, identity_name
        )

    if not rules:
        return {
            "final_decision": "queue_for_review",
            "triggered_rules": [],
            "reasoning_summary": "No rules configured, queuing for manual review",
            "llm_failed": False,
        }

    try:
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"rules-engine-{uuid.uuid4()}",
            system_message="""You are the Reach Rules Engine. Your job is to evaluate a submission against the owner's plain language rules.

OWNER'S PRIORITIES:
1. Protect the owner's attention - err on the side of caution
2. Most restrictive rule wins in case of conflict
3. Be transparent about reasoning

RULE ACTIONS:
- auto_approve: Goes straight to approved queue (use sparingly, only for high-trust signals)
- auto_reject: Sender receives rejection message immediately (for clear violations)
- ask_for_more_context: Sender sees follow-up question before submission completes
- queue_for_review: Default, goes to owner's decision surface
- none: Rule doesn't apply, no action taken

EVALUATION PROCESS:
1. For each rule, determine if it applies to this submission
2. If it applies, determine what action it triggers
3. Provide confidence (0.0-1.0) and brief reasoning
4. If action requires a response (reject or ask for context), suggest appropriate text

CONFLICT RESOLUTION:
If multiple rules trigger different actions, apply this priority (most restrictive wins):
1. auto_reject (most restrictive)
2. ask_for_more_context
3. queue_for_review
4. auto_approve (least restrictive)

RESPONSE FORMAT:
Return ONLY valid JSON with this exact structure:
{
  "final_decision": "auto_approve" | "auto_reject" | "ask_for_more_context" | "queue_for_review",
  "triggered_rules": [
    {
      "rule": "original rule text",
      "applies": true/false,
      "action": "auto_approve" | "auto_reject" | "ask_for_more_context" | "queue_for_review" | "none",
      "confidence": 0.0-1.0,
      "reasoning": "plain English explanation",
      "suggested_response": "optional response text if action requires it"
    }
  ],
  "reasoning_summary": "Overall reasoning for final decision"
}

IMPORTANT: Return ONLY valid JSON, no markdown or extra text.""",
        ).with_model("openai", "gpt-5.2")

        # Prepare submission context
        message = submission_data.get("message", "")
        intent_category = submission_data.get("intent_category")
        time_requirement = submission_data.get("time_requirement")
        challenge_answer = submission_data.get("challenge_answer")

        submission_context = f"""Submission to evaluate for {identity_name}:

Message: {message}
Word count: {len(message.split())}
Intent category: {intent_category or "Not specified"}
Time requirement: {time_requirement or "Not specified"}
Challenge answer: {challenge_answer or "Not provided"}"""

        user_message = UserMessage(
            text=f"""Evaluate this submission against the owner's rules:

OWNER'S RULES (one per line):
{chr(10).join(f"- {rule}" for rule in rules)}

SUBMISSION CONTEXT:
{submission_context}

Return your evaluation as JSON."""
        )

        response = await chat.send_message(user_message)

        # Parse AI response
        try:
            # Extract JSON from response
            response_text = response.text.strip()

            # Try to find JSON in the response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1

            if json_start >= 0 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                result = json.loads(json_str)
            else:
                # If no JSON found, try parsing the whole response
                result = json.loads(response_text)

            # Validate required fields
            if "final_decision" not in result:
                result["final_decision"] = "queue_for_review"

            if "triggered_rules" not in result:
                result["triggered_rules"] = []

            if "reasoning_summary" not in result:
                result["reasoning_summary"] = "LLM response missing required fields"

            result["llm_failed"] = False
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return {
                "final_decision": "queue_for_review",
                "triggered_rules": [],
                "reasoning_summary": f"Failed to parse LLM response: {str(e)[:100]}",
                "llm_failed": True,
            }

    except Exception as e:
        logger.error(f"Rules engine LLM error: {e}")
        return {
            "final_decision": "queue_for_review",
            "triggered_rules": [],
            "reasoning_summary": f"Rules engine error: {str(e)[:100]}",
            "llm_failed": True,
        }


# ==================== AUTH ROUTES ====================


@api_router.post("/auth/register", response_model=TokenResponse)
@rate_limit("5/minute")  # 5 registrations per minute per IP
async def register(data: UserCreate, response: Response, request: Request):
    # Check if user exists
    existing = await db.users.find_one({"email": data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = str(uuid.uuid4())
    user = {
        "id": user_id,
        "email": data.email,
        "password": hash_password(data.password),
        "name": data.name,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.users.insert_one(user)

    # Audit log
    log_audit_event(
        event_type="user_registered",
        user_id=user_id,
        ip_address=get_client_ip(request),
        details={
            "email": data.email,
            "name": data.name,
            "user_agent": request.headers.get("user-agent", "unknown"),
        },
    )

    # Create tokens
    access_token = create_token(user_id, data.email)
    csrf_token = create_csrf_token()

    # Set cookies
    set_auth_cookies(response, access_token, csrf_token)

    return TokenResponse(
        user=UserResponse(
            id=user_id, email=data.email, name=data.name, created_at=user["created_at"]
        ),
        csrf_token=csrf_token,  # Return CSRF token in response for initial setup
    )


@api_router.post("/auth/login", response_model=TokenResponse)
@rate_limit("10/minute")  # 10 login attempts per minute per IP
async def login(request: Request, data: UserLogin, response: Response):
    user = await db.users.find_one({"email": data.email}, {"_id": 0})
    if not user or not verify_password(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Create tokens
    access_token = create_token(user["id"], user["email"])
    csrf_token = create_csrf_token()

    # Set cookies
    set_auth_cookies(response, access_token, csrf_token)

    return TokenResponse(
        user=UserResponse(
            id=user["id"],
            email=user["email"],
            name=user["name"],
            created_at=user["created_at"],
        ),
        csrf_token=csrf_token,  # Return CSRF token in response for initial setup
    )


@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(request: Request, user: dict = Depends(get_current_user)):
    return UserResponse(
        id=user["id"],
        email=user["email"],
        name=user["name"],
        created_at=user["created_at"],
    )


@api_router.post("/auth/logout")
async def logout(response: Response):
    """Logout user by clearing auth cookies"""
    clear_auth_cookies(response)
    return {"message": "Logged out successfully"}


@api_router.get("/auth/csrf")
async def get_csrf_token(response: Response):
    """Get a CSRF token for initial requests"""
    csrf_token = create_csrf_token()

    # Set CSRF token in cookie
    response.set_cookie(
        key=CSRF_COOKIE_NAME,
        value=csrf_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite=COOKIE_SAMESITE,
        max_age=3600,  # 1 hour
    )

    return {"csrf_token": csrf_token}


# ==================== HEALTH CHECKS ====================


@api_router.get("/health")
async def health_check():
    """Comprehensive health check endpoint"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "services": {},
    }

    # Check MongoDB
    try:
        await db.command("ping")
        health_status["services"]["mongodb"] = {
            "status": "healthy",
            "latency_ms": 0,  # Would measure actual latency in production
        }
    except Exception as e:
        health_status["status"] = "degraded"
        health_status["services"]["mongodb"] = {"status": "unhealthy", "error": str(e)}

    # Check AI service (if configured)
    if EMERGENT_LLM_KEY and EMERGENT_LLM_AVAILABLE:
        try:
            # Simple check - try to create a chat instance
            chat = LlmChat(api_key=EMERGENT_LLM_KEY, session_id="health-check")
            health_status["services"]["ai"] = {
                "status": "healthy",
                "provider": "openai",
            }
        except Exception as e:
            health_status["status"] = "degraded"
            health_status["services"]["ai"] = {
                "status": "unhealthy",
                "error": str(e)[:100],  # Limit error length
            }
    elif EMERGENT_LLM_KEY and not EMERGENT_LLM_AVAILABLE:
        health_status["status"] = "degraded"
        health_status["services"]["ai"] = {
            "status": "unhealthy",
            "error": "emergentintegrations module not installed",
        }
    else:
        health_status["services"]["ai"] = {"status": "not_configured"}

    # Check Stripe (if configured)
    if STRIPE_API_KEY:
        try:
            import stripe

            stripe.api_key = STRIPE_API_KEY
            # Simple API call to check connectivity
            stripe.Balance.retrieve()
            health_status["services"]["stripe"] = {"status": "healthy"}
        except Exception as e:
            health_status["status"] = "degraded"
            health_status["services"]["stripe"] = {
                "status": "unhealthy",
                "error": str(e)[:100],
            }
    else:
        health_status["services"]["stripe"] = {"status": "not_configured"}

    # System metrics
    try:
        import psutil

        health_status["system"] = {
            "cpu_percent": psutil.cpu_percent(interval=0.1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage("/").percent,
        }
    except ImportError:
        health_status["system"] = {
            "cpu_percent": "unknown",
            "memory_percent": "unknown",
            "disk_percent": "unknown",
            "note": "psutil not installed",
        }

    return health_status


@api_router.get("/health/live")
async def liveness_probe():
    """Simple liveness probe for Kubernetes/load balancers"""
    return {"status": "alive"}


@api_router.get("/health/ready")
async def readiness_probe():
    """Readiness probe - checks if service can accept traffic"""
    try:
        # Check MongoDB
        await db.command("ping")
        return {"status": "ready"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service not ready: {e}")


# ==================== IDENTITY ROUTES ====================


@api_router.post("/identity", response_model=IdentityResponse)
# Temporarily remove rate limiting to fix the bug
# @rate_limit(
#     "3/minute", key_func=get_user_rate_limit_key
# )  # 3 identities per minute per user
async def create_identity(
    request: Request, data: FaceCreate, user: dict = Depends(get_current_user)
):
    # Check if handle is taken
    existing = await db.identities.find_one({"handle": data.handle.lower()})
    if existing:
        raise HTTPException(status_code=400, detail="Handle already taken")

    # Check if user already has an identity
    existing_user = await db.identities.find_one({"user_id": user["id"]})
    if existing_user:
        raise HTTPException(status_code=400, detail="You already have an identity")

    identity_id = str(uuid.uuid4())
    identity = {
        "id": identity_id,
        "user_id": user["id"],
        "handle": data.handle.lower(),
        "type": "person",  # Default to person for now
        "bio": None,  # bio is deprecated, use headline + current_focus instead
        "public_url": f"/{data.handle.lower()}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "face_completed": True,
        "display_name": data.display_name,
        "headline": data.headline,
        "current_focus": data.current_focus,
        "availability_signal": data.availability_signal,
        "prompt": data.prompt,
        "photo_url": data.photo_url,
        "links": data.links,
        "modules_config": {
            "challenge_question": {"enabled": False},
            "time_signal": {"enabled": True},
            "waiting_period": {"enabled": False},
            "deposit": {"enabled": False},
            "intent_categories": {
                "enabled": True,
                "categories": ["Collaboration", "Question", "Feedback", "Opportunity"],
            },
            "capacity_controls": {"enabled": False},
            "rules_engine": {"enabled": False, "rules": []},
        },
    }

    await db.identities.insert_one(identity)

    # Note: No default slot created - using Face-based system instead
    # Slots are deprecated in favor of Face-based reach

    return IdentityResponse(**{k: v for k, v in identity.items() if k != "_id"})


@api_router.get("/identity", response_model=Optional[IdentityResponse])
async def get_my_identity(user: dict = Depends(get_current_user)):
    identity = await db.identities.find_one({"user_id": user["id"]}, {"_id": 0})
    if not identity:
        return None
    return IdentityResponse(**identity)


@api_router.get("/identity/{handle}", response_model=IdentityResponse)
async def get_identity_by_handle(handle: str):
    identity = await db.identities.find_one({"handle": handle.lower()}, {"_id": 0})
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")
    return IdentityResponse(**identity)


# ==================== MODULE ROUTES ====================


@api_router.get("/modules", response_model=ModulesConfig)
async def get_modules_config(user: dict = Depends(get_current_user)):
    """Get module configuration for current user's identity"""
    identity = await db.identities.find_one({"user_id": user["id"]}, {"_id": 0})
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    # Get modules config from identity or return defaults
    modules_config = identity.get("modules_config", {})

    # Merge with defaults
    default_config = ModulesConfig()
    merged_config = default_config.model_dump()

    for module_name, module_config in modules_config.items():
        if module_name in merged_config:
            # Update with saved config
            for key, value in module_config.items():
                if key in merged_config[module_name]:
                    merged_config[module_name][key] = value

    return ModulesConfig(**merged_config)


@api_router.put("/modules", response_model=ModulesConfig)
async def update_modules_config(
    data: ModulesConfigUpdate, user: dict = Depends(get_current_user)
):
    """Update module configuration for current user's identity"""
    identity = await db.identities.find_one({"user_id": user["id"]}, {"_id": 0})
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    # Get current modules config
    current_modules = identity.get("modules_config", {})

    # Update with new data
    update_data = data.model_dump(exclude_unset=True)

    for module_name, module_update in update_data.items():
        if module_update is not None:
            if module_name not in current_modules:
                current_modules[module_name] = {}

            # Update module config
            for key, value in module_update.items():
                if value is not None:
                    current_modules[module_name][key] = value

    # Save to database
    await db.identities.update_one(
        {"user_id": user["id"]}, {"$set": {"modules_config": current_modules}}
    )

    # Return updated config
    return await get_modules_config(user)


# ==================== SLOT ROUTES ====================


@api_router.post("/slots", response_model=SlotResponse)
async def create_slot(data: SlotCreate, user: dict = Depends(get_current_user)):
    identity = await db.identities.find_one({"user_id": user["id"]}, {"_id": 0})
    if not identity:
        raise HTTPException(status_code=400, detail="Create an identity first")

    # Check if slot name exists for this identity
    existing = await db.slots.find_one(
        {"identity_id": identity["id"], "name": data.name.lower()}
    )
    if existing:
        raise HTTPException(status_code=400, detail="Slot name already exists")

    slot_id = str(uuid.uuid4())
    slot = {
        "id": slot_id,
        "identity_id": identity["id"],
        "name": data.name.lower(),
        "description": data.description,
        "visibility": data.visibility,
        "reach_policy": {
            "conditions": [],
            "actions": {"default": "queue"},
            "fallback": "queue",
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.slots.insert_one(slot)
    return SlotResponse(**{k: v for k, v in slot.items() if k != "_id"})


@api_router.get("/slots", response_model=List[SlotResponse])
async def get_my_slots(user: dict = Depends(get_current_user)):
    identity = await db.identities.find_one({"user_id": user["id"]}, {"_id": 0})
    if not identity:
        return []

    slots = await db.slots.find({"identity_id": identity["id"]}, {"_id": 0}).to_list(
        100
    )
    return [SlotResponse(**slot) for slot in slots]


@api_router.get("/slots/{slot_id}", response_model=SlotResponse)
async def get_slot(slot_id: str, user: dict = Depends(get_current_user)):
    identity = await db.identities.find_one({"user_id": user["id"]}, {"_id": 0})
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    slot = await db.slots.find_one(
        {"id": slot_id, "identity_id": identity["id"]}, {"_id": 0}
    )
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")
    return SlotResponse(**slot)


@api_router.put("/slots/{slot_id}", response_model=SlotResponse)
async def update_slot(
    slot_id: str, data: SlotUpdate, user: dict = Depends(get_current_user)
):
    identity = await db.identities.find_one({"user_id": user["id"]}, {"_id": 0})
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    slot = await db.slots.find_one(
        {"id": slot_id, "identity_id": identity["id"]}, {"_id": 0}
    )
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    if update_data:
        await db.slots.update_one({"id": slot_id}, {"$set": update_data})

    slot = await db.slots.find_one({"id": slot_id}, {"_id": 0})
    return SlotResponse(**slot)


@api_router.put("/slots/{slot_id}/policy", response_model=SlotResponse)
async def update_slot_policy(
    slot_id: str, data: PolicyUpdate, user: dict = Depends(get_current_user)
):
    identity = await db.identities.find_one({"user_id": user["id"]}, {"_id": 0})
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    slot = await db.slots.find_one(
        {"id": slot_id, "identity_id": identity["id"]}, {"_id": 0}
    )
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    policy = {
        "conditions": data.conditions,
        "actions": data.actions,
        "fallback": data.fallback,
        "payment_amount": data.payment_amount,
    }

    await db.slots.update_one({"id": slot_id}, {"$set": {"reach_policy": policy}})

    slot = await db.slots.find_one({"id": slot_id}, {"_id": 0})
    return SlotResponse(**slot)


@api_router.delete("/slots/{slot_id}")
async def delete_slot(slot_id: str, user: dict = Depends(get_current_user)):
    identity = await db.identities.find_one({"user_id": user["id"]}, {"_id": 0})
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    slot = await db.slots.find_one(
        {"id": slot_id, "identity_id": identity["id"]}, {"_id": 0}
    )
    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    if slot["name"] == "open":
        raise HTTPException(
            status_code=400, detail="Cannot delete the default 'open' slot"
        )

    await db.slots.delete_one({"id": slot_id})
    return {"message": "Slot deleted"}


# ==================== PUBLIC REACH ROUTES ====================


@api_router.get("/reach/{handle}", response_model=Dict[str, Any])
async def get_public_reach_page(handle: str):
    identity = await db.identities.find_one({"handle": handle.lower()}, {"_id": 0})
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    # Check if Face is completed
    if not identity.get("face_completed", False):
        raise HTTPException(
            status_code=404, detail="This person hasn't set up their Reach yet"
        )

    # Return Face data for sender page
    response_data = {
        "identity": {
            "handle": identity["handle"],
            "display_name": identity.get("display_name"),
            "headline": identity.get("headline"),
            "current_focus": identity.get("current_focus"),
            "availability_signal": identity.get("availability_signal"),
            "prompt": identity.get("prompt"),
            "photo_url": identity.get("photo_url"),
            "links": identity.get("links", []),
            "face_completed": identity.get("face_completed", False),
        }
    }

    # Include enabled modules configuration for sender page
    modules_config = identity.get("modules_config", {})
    if modules_config:
        # Filter to only include enabled modules
        enabled_modules = {}
        for module_name, config in modules_config.items():
            if config.get("enabled", False):
                # Create a clean copy without internal fields if needed
                enabled_modules[module_name] = {
                    k: v for k, v in config.items() if k != "_id"
                }

        if enabled_modules:
            response_data["modules"] = enabled_modules

    return response_data


@api_router.post("/reach/{handle}/message", response_model=Dict[str, Any])
async def submit_face_reach_attempt(
    handle: str, data: FaceReachAttemptCreate, request: Request
):
    """Submit a Face-based reach attempt with module data"""
    # Check if identity exists and Face is completed
    identity = await db.identities.find_one({"handle": handle.lower()}, {"_id": 0})
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    if not identity.get("face_completed", False):
        raise HTTPException(
            status_code=404, detail="This person hasn't set up their Reach yet"
        )

    # Check for empty message (edge case)
    if not data.message or not data.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # Get modules config
    modules_config = identity.get("modules_config", {})

    # Apply capacity controls if enabled
    if modules_config.get("capacity_controls", {}).get("enabled", False):
        capacity_config = modules_config["capacity_controls"]

        # Check daily submission cap
        if capacity_config.get("daily_submission_cap"):
            today_start = datetime.now(timezone.utc).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            today_count = await db.reach_attempts.count_documents(
                {
                    "identity_id": identity["id"],
                    "created_at": {"$gte": today_start.isoformat()},
                }
            )
            if today_count >= capacity_config["daily_submission_cap"]:
                raise HTTPException(
                    status_code=429,
                    detail="Daily submission limit reached for this handle",
                )

        # Check handle expiry date
        if capacity_config.get("handle_expiry_date"):
            expiry_date = datetime.fromisoformat(
                capacity_config["handle_expiry_date"].replace("Z", "+00:00")
            )
            if datetime.now(timezone.utc) > expiry_date:
                raise HTTPException(
                    status_code=410, detail="This reach handle has expired"
                )

    # Apply rules engine if enabled
    decision = "queued"
    rationale = "Submitted via Face page"
    auto_response = None
    triggered_rules = []
    rule_evaluation_result = None
    llm_failed = False

    if modules_config.get("rules_engine", {}).get("enabled", False):
        rules = modules_config["rules_engine"].get("rules", [])
        if rules:
            # Prepare submission data for rules engine
            submission_data = {
                "message": data.message,
                "intent_category": data.intent_category,
                "time_requirement": data.time_requirement,
                "challenge_answer": data.challenge_answer,
            }

            # Evaluate rules with LLM
            rule_evaluation_result = await evaluate_rules_with_llm(
                rules=rules,
                submission_data=submission_data,
                identity_name=identity.get("display_name", identity["handle"]),
            )

            llm_failed = rule_evaluation_result.get("llm_failed", False)

            # Map LLM decision to our internal decision types
            llm_decision = rule_evaluation_result.get(
                "final_decision", "queue_for_review"
            )

            # Convert LLM decision to our decision types
            if llm_decision == "auto_approve":
                decision = "deliver_to_human"  # Goes to approved queue
                rationale = rule_evaluation_result.get(
                    "reasoning_summary", "Auto-approved by rules engine"
                )
            elif llm_decision == "auto_reject":
                decision = "reject"
                rationale = rule_evaluation_result.get(
                    "reasoning_summary", "Auto-rejected by rules engine"
                )
            elif llm_decision == "ask_for_more_context":
                decision = "request_more_context"
                rationale = rule_evaluation_result.get(
                    "reasoning_summary", "More context requested by rules engine"
                )
            else:  # queue_for_review or any other
                decision = "queued"
                rationale = rule_evaluation_result.get(
                    "reasoning_summary", "Queued for review by rules engine"
                )

            # Get triggered rules and auto-response
            triggered_rules_data = rule_evaluation_result.get("triggered_rules", [])
            for rule_data in triggered_rules_data:
                if rule_data.get("applies", False):
                    triggered_rules.append(
                        {
                            "rule": rule_data.get("rule", ""),
                            "action": rule_data.get("action", "none"),
                            "confidence": rule_data.get("confidence", 0.0),
                            "reasoning": rule_data.get("reasoning", ""),
                        }
                    )

            # Find auto-response from triggered rules
            for rule_data in triggered_rules_data:
                if rule_data.get("applies", False) and rule_data.get(
                    "suggested_response"
                ):
                    auto_response = rule_data["suggested_response"]
                    break

    # Create attempt with module data
    attempt_id = str(uuid.uuid4())
    attempt = {
        "id": attempt_id,
        "identity_id": identity["id"],
        "slot_id": None,  # No slot for Face-based attempts
        "sender_context": {
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        },
        "payload": {
            "message": data.message,
            "type": "face_attempt",
            "challenge_answer": data.challenge_answer,
            "time_requirement": data.time_requirement,
            "intent_category": data.intent_category,
        },
        "ai_classification": {
            "rules_evaluated": True,
            "triggered_rules": triggered_rules,
            "rule_evaluation_result": rule_evaluation_result,
            "llm_failed": llm_failed,
            "final_decision": rule_evaluation_result.get(
                "final_decision", "queue_for_review"
            )
            if rule_evaluation_result
            else None,
            "reasoning_summary": rule_evaluation_result.get("reasoning_summary", "")
            if rule_evaluation_result
            else "",
        }
        if rule_evaluation_result
        else None,
        "decision": decision,
        "rationale": rationale,
        "auto_response": auto_response,
        "payment_status": "pending" if decision == "request_payment" else None,
        "payment_amount": modules_config.get("deposit", {}).get("amount_usd")
        if decision == "request_payment"
        else None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    await db.reach_attempts.insert_one(attempt)

    # Return success response
    response_data = {
        "success": True,
        "attempt_id": attempt_id,
        "message": "Message submitted successfully",
        "confirmation": f"Your message reached {identity.get('display_name', identity['handle'])}.",
    }

    # Include auto-response if any
    if auto_response:
        response_data["auto_response"] = auto_response

    # Include payment info if required
    if decision == "request_payment":
        response_data["payment_required"] = True
        response_data["payment_amount"] = modules_config.get("deposit", {}).get(
            "amount_usd"
        )
        response_data["message"] = "Payment required to complete submission"

    return response_data


@api_router.get("/reach/{handle}/{slot_name}", response_model=Dict[str, Any])
async def get_public_slot(handle: str, slot_name: str):
    identity = await db.identities.find_one({"handle": handle.lower()}, {"_id": 0})
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    slot = await db.slots.find_one(
        {"identity_id": identity["id"], "name": slot_name.lower()}, {"_id": 0}
    )

    if not slot:
        raise HTTPException(status_code=404, detail="Slot not found")

    if slot["visibility"] == "private":
        raise HTTPException(status_code=403, detail="This slot is private")

    # Get policy info for display (without sensitive data)
    policy = slot.get("reach_policy", {})
    policy_display = {
        "requires_payment": policy.get("payment_amount") is not None,
        "payment_amount": policy.get("payment_amount"),
    }

    return {
        "identity": {
            "handle": identity["handle"],
            "type": identity["type"],
            "bio": identity.get("bio"),
        },
        "slot": {
            "id": slot["id"],
            "name": slot["name"],
            "description": slot["description"],
            "policy": policy_display,
        },
    }


# ==================== REACH ATTEMPTS (OWNER VIEW) ====================


@api_router.get("/attempts")
async def get_my_reach_attempts(user: dict = Depends(get_current_user)):
    import sys

    print(f"DEBUG: get_my_reach_attempts called", file=sys.stderr, flush=True)
    print(f"DEBUG: user keys = {list(user.keys())}", file=sys.stderr, flush=True)

    try:
        identity = await db.identities.find_one({"user_id": user["id"]}, {"_id": 0})
        if not identity:
            print(
                f"DEBUG: No identity found for user_id={user.get('id')}",
                file=sys.stderr,
                flush=True,
            )
            return []

        attempts = (
            await db.reach_attempts.find({"identity_id": identity["id"]}, {"_id": 0})
            .sort("created_at", -1)
            .to_list(100)
        )

        print(
            f"DEBUG: Found {len(attempts)} attempts for identity_id={identity['id']}",
            file=sys.stderr,
            flush=True,
        )

        # Convert BSON documents to JSON-serializable dicts
        import bson.json_util
        import json

        serializable_attempts = []
        for attempt in attempts:
            # Convert BSON document to JSON string and back to dict
            # This handles ObjectId, datetime, Decimal, etc.
            attempt_json = bson.json_util.dumps(attempt)
            attempt_dict = json.loads(attempt_json)
            serializable_attempts.append(attempt_dict)

        return serializable_attempts
    except Exception as e:
        print(f"ERROR in get_my_reach_attempts: {e}", file=sys.stderr, flush=True)
        import traceback

        traceback.print_exc(file=sys.stderr)
        return []


@api_router.get("/attempts/{attempt_id}", response_model=ReachAttemptResponse)
async def get_reach_attempt(attempt_id: str, user: dict = Depends(get_current_user)):
    identity = await db.identities.find_one({"user_id": user["id"]}, {"_id": 0})
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    attempt = await db.reach_attempts.find_one(
        {"id": attempt_id, "identity_id": identity["id"]}, {"_id": 0}
    )

    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    # Convert BSON document to JSON-serializable dict
    import bson.json_util
    import json

    attempt_json = bson.json_util.dumps(attempt)
    attempt_dict = json.loads(attempt_json)

    return ReachAttemptResponse(**attempt_dict)


@api_router.put("/attempts/{attempt_id}/decision")
async def update_attempt_decision(
    attempt_id: str, decision: str, user: dict = Depends(get_current_user)
):
    identity = await db.identities.find_one({"user_id": user["id"]}, {"_id": 0})
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    valid_decisions = ["deliver_to_human", "reject", "queue", "request_more_context"]
    if decision not in valid_decisions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid decision. Must be one of: {valid_decisions}",
        )

    result = await db.reach_attempts.update_one(
        {"id": attempt_id, "identity_id": identity["id"]},
        {"$set": {"decision": decision, "manual_override": True}},
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Attempt not found")

    return {"message": "Decision updated"}


@api_router.post("/attempts/{attempt_id}/block")
async def block_sender(attempt_id: str, user: dict = Depends(get_current_user)):
    """Block sender permanently from this handle"""
    identity = await db.identities.find_one({"user_id": user["id"]}, {"_id": 0})
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    # Get the attempt
    attempt = await db.reach_attempts.find_one(
        {"id": attempt_id, "identity_id": identity["id"]}, {"_id": 0}
    )
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    # Get sender email from attempt
    sender_email = attempt.get("sender_context", {}).get("email")
    if not sender_email:
        raise HTTPException(status_code=400, detail="No sender email found to block")

    # Create or update blocked_senders collection
    await db.blocked_senders.update_one(
        {"identity_id": identity["id"], "email": sender_email},
        {
            "$set": {
                "blocked_at": datetime.now(timezone.utc).isoformat(),
                "attempt_id": attempt_id,
                "reason": "manual_block",
            }
        },
        upsert=True,
    )

    # Also reject the attempt
    await db.reach_attempts.update_one(
        {"id": attempt_id, "identity_id": identity["id"]},
        {"$set": {"decision": "reject", "manual_override": True}},
    )

    return {"message": "Sender blocked and attempt rejected"}


@api_router.post("/attempts/{attempt_id}/ask")
async def ask_followup_question(
    attempt_id: str, user: dict = Depends(get_current_user)
):
    """Send follow-up question to sender"""
    identity = await db.identities.find_one({"user_id": user["id"]}, {"_id": 0})
    if not identity:
        raise HTTPException(status_code=404, detail="Identity not found")

    # Get the attempt
    attempt = await db.reach_attempts.find_one(
        {"id": attempt_id, "identity_id": identity["id"]}, {"_id": 0}
    )
    if not attempt:
        raise HTTPException(status_code=404, detail="Attempt not found")

    # Update attempt to request more context
    result = await db.reach_attempts.update_one(
        {"id": attempt_id, "identity_id": identity["id"]},
        {"$set": {"decision": "request_more_context", "manual_override": True}},
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Attempt not found")

    # TODO: Actually send the follow-up question via email or other channel
    # For now, just update the status

    return {"message": "Follow-up question requested"}


# ==================== PAYMENT ROUTES ====================


@api_router.post("/payments/checkout")
async def create_payment_checkout(data: PaymentCheckoutRequest, request: Request):
    attempt = await db.reach_attempts.find_one(
        {"id": data.reach_attempt_id}, {"_id": 0}
    )
    if not attempt:
        raise HTTPException(status_code=404, detail="Reach attempt not found")

    if attempt["decision"] != "request_payment":
        raise HTTPException(
            status_code=400, detail="This reach attempt does not require payment"
        )

    if not attempt.get("payment_amount"):
        raise HTTPException(status_code=400, detail="No payment amount specified")

    # Create Stripe checkout session
    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"

    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)

    success_url = (
        f"{data.origin_url}/payment/success?session_id={{CHECKOUT_SESSION_ID}}"
    )
    cancel_url = f"{data.origin_url}/payment/cancel"

    checkout_request = CheckoutSessionRequest(
        amount=float(attempt["payment_amount"]),
        currency="usd",
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"reach_attempt_id": data.reach_attempt_id, "type": "reach_payment"},
    )

    session = await stripe_checkout.create_checkout_session(checkout_request)

    # Store transaction
    transaction = {
        "id": str(uuid.uuid4()),
        "session_id": session.session_id,
        "reach_attempt_id": data.reach_attempt_id,
        "amount": attempt["payment_amount"],
        "currency": "usd",
        "payment_status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    await db.payment_transactions.insert_one(transaction)

    # Update attempt with checkout URL
    await db.reach_attempts.update_one(
        {"id": data.reach_attempt_id},
        {"$set": {"checkout_session_id": session.session_id}},
    )

    return {"checkout_url": session.url, "session_id": session.session_id}


@api_router.get("/payments/status/{session_id}")
async def get_payment_status(session_id: str, request: Request):
    # First check if this session exists in our records
    transaction = await db.payment_transactions.find_one(
        {"session_id": session_id}, {"_id": 0}
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Payment session not found")

    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"

    try:
        stripe_checkout = StripeCheckout(
            api_key=STRIPE_API_KEY, webhook_url=webhook_url
        )
        status = await stripe_checkout.get_checkout_status(session_id)

        # Update transaction and attempt if paid
        if status.payment_status == "paid":
            await db.payment_transactions.update_one(
                {"session_id": session_id}, {"$set": {"payment_status": "completed"}}
            )

            if transaction:
                await db.reach_attempts.update_one(
                    {"id": transaction["reach_attempt_id"]},
                    {
                        "$set": {
                            "payment_status": "completed",
                            "decision": "deliver_to_human",
                        }
                    },
                )

        return {
            "status": status.status,
            "payment_status": status.payment_status,
            "amount": status.amount_total / 100,  # Convert from cents
        }
    except Exception as e:
        logger.error(f"Stripe status check error: {e}")
        raise HTTPException(status_code=400, detail="Unable to check payment status")


@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("Stripe-Signature", "")

    host_url = str(request.base_url).rstrip("/")
    webhook_url = f"{host_url}/api/webhook/stripe"

    stripe_checkout = StripeCheckout(api_key=STRIPE_API_KEY, webhook_url=webhook_url)

    try:
        event = await stripe_checkout.handle_webhook(body, signature)

        if event.payment_status == "paid":
            await db.payment_transactions.update_one(
                {"session_id": event.session_id},
                {"$set": {"payment_status": "completed"}},
            )

            transaction = await db.payment_transactions.find_one(
                {"session_id": event.session_id}, {"_id": 0}
            )
            if transaction:
                await db.reach_attempts.update_one(
                    {"id": transaction["reach_attempt_id"]},
                    {
                        "$set": {
                            "payment_status": "completed",
                            "decision": "deliver_to_human",
                        }
                    },
                )

        return {"received": True}
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return {"received": True}


# ==================== STATS ====================


@api_router.get("/stats")
async def get_stats(user: dict = Depends(get_current_user)):
    identity = await db.identities.find_one({"user_id": user["id"]}, {"_id": 0})
    if not identity:
        return {
            "total_attempts": 0,
            "blocked": 0,
            "delivered": 0,
            "pending": 0,
            "paid": 0,
        }

    # Use aggregation pipeline for efficient stats computation
    pipeline = [
        {"$match": {"identity_id": identity["id"]}},
        {
            "$facet": {
                "total": [{"$count": "count"}],
                "blocked": [{"$match": {"decision": "reject"}}, {"$count": "count"}],
                "delivered": [
                    {"$match": {"decision": "deliver_to_human"}},
                    {"$count": "count"},
                ],
                "pending": [
                    {"$match": {"decision": {"$in": ["queue", "request_payment"]}}},
                    {"$count": "count"},
                ],
                "paid": [
                    {"$match": {"payment_status": "completed"}},
                    {"$count": "count"},
                ],
            }
        },
    ]

    result = await db.reach_attempts.aggregate(pipeline).to_list(1)
    data = result[0] if result else {}

    return {
        "total_attempts": data.get("total", [{}])[0].get("count", 0)
        if data.get("total")
        else 0,
        "blocked": data.get("blocked", [{}])[0].get("count", 0)
        if data.get("blocked")
        else 0,
        "delivered": data.get("delivered", [{}])[0].get("count", 0)
        if data.get("delivered")
        else 0,
        "pending": data.get("pending", [{}])[0].get("count", 0)
        if data.get("pending")
        else 0,
        "paid": data.get("paid", [{}])[0].get("count", 0) if data.get("paid") else 0,
    }


# ==================== ROOT ROUTES ====================


@api_router.get("/")
async def root():
    return {"message": "Reach API - Reachability as Logic"}


# Include the router
app.include_router(api_router)

# Rate limiting middleware (must be before CORS)
app.add_middleware(SlowAPIMiddleware)


# Security headers middleware
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)

        # Add security headers
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # HSTS - only in production with HTTPS
        if COOKIE_SECURE:  # Only add HSTS if using HTTPS
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # CSP - Content Security Policy
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self' http://localhost:3000 http://localhost:8001 https://api.stripe.com; "
            "frame-src https://js.stripe.com; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp_policy

        return response


app.add_middleware(SecurityHeadersMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get("CORS_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
