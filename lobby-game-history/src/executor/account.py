from dataclasses import dataclass

@dataclass(frozen=True)
class Account:
    nick: str
    password: str
    email: str


