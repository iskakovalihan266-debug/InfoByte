"""In-memory repository for a single Uvicorn worker."""
import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass
from threading import RLock
from uuid import UUID, uuid4

from .schemas import Login, PlanItem, Problem, Profile, Registration

SHORT_SESSION = 8 * 3600
LONG_SESSION = 7 * 24 * 3600


def derive(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode(), salt=salt, n=2**15, r=8, p=1, maxmem=64*1024*1024)


def token_key(token: str) -> bytes:
    return hashlib.sha256(token.encode()).digest()


@dataclass
class Account:
    profile: Profile
    salt: bytes
    digest: bytes


class Store:
    def __init__(self):
        self.lock = RLock()
        self.accounts: dict[UUID, Account] = {}
        self.by_email: dict[str, UUID] = {}
        self.sessions: dict[bytes, tuple[UUID, float]] = {}
        self.plans: dict[UUID, dict[UUID, PlanItem]] = {}

    def register(self, data: Registration) -> Profile:
        salt = secrets.token_bytes(16)
        digest = derive(data.password.get_secret_value(), salt)
        with self.lock:
            if data.email in self.by_email:
                raise Problem(409, "Бұл пошта бұрын тіркелген.")
            user = Profile(id=uuid4(), **data.model_dump(exclude={"password"}))
            self.accounts[user.id] = Account(user, salt, digest)
            self.by_email[user.email] = user.id
            self.plans[user.id] = {}
            return user

    def login(self, data: Login):
        with self.lock:
            account = self.accounts.get(self.by_email.get(data.email))
        salt = account.salt if account else bytes(16)
        candidate = derive(data.password.get_secret_value(), salt)
        if not account or not hmac.compare_digest(account.digest, candidate):
            raise Problem(401, "Пошта немесе құпиясөз қате.")
        token = secrets.token_urlsafe(32)
        ttl = LONG_SESSION if data.remember else SHORT_SESSION
        now = time.time()
        with self.lock:
            for key in [k for k, (_, end) in self.sessions.items() if end <= now]:
                del self.sessions[key]
            self.sessions[token_key(token)] = (account.profile.id, now + ttl)
        return account.profile, token, ttl

    def current(self, token: str) -> Profile:
        key = token_key(token)
        with self.lock:
            session = self.sessions.get(key)
            if not session or session[1] <= time.time():
                self.sessions.pop(key, None)
                raise Problem(401, "Аккаунтқа кіріңіз.")
            return self.accounts[session[0]].profile

    def logout(self, token: str):
        with self.lock:
            self.sessions.pop(token_key(token), None)

    def add_topic(self, owner: UUID, title: str) -> PlanItem:
        with self.lock:
            items = self.plans[owner]
            if any(not t.done and t.title.casefold() == title.casefold() for t in items.values()):
                raise Problem(409, "Бұл тақырып жоспарыңызда бар.")
            item = PlanItem(id=uuid4(), title=title)
            items[item.id] = item
            return item

    def list_topics(self, owner: UUID, done: bool | None):
        with self.lock:
            return [t for t in self.plans[owner].values() if done is None or t.done == done]

    def change_topic(self, owner: UUID, key: UUID, done: bool):
        with self.lock:
            items = self.plans[owner]
            item = self.find_topic(owner, key)
            if not done and any(t.id != key and not t.done and t.title.casefold() == item.title.casefold() for t in items.values()):
                raise Problem(409, "Осы тақырыптың белсенді жоспары бар.")
            items[key] = item.model_copy(update={"done": done})
            return items[key]

    def find_topic(self, owner: UUID, key: UUID):
        item = self.plans[owner].get(key)
        if not item:
            raise Problem(404, "Тақырып табылмады.")
        return item

    def delete_topic(self, owner: UUID, key: UUID):
        with self.lock:
            self.find_topic(owner, key)
            del self.plans[owner][key]


store = Store()
