"""Motor explicável de prioridade operacional do MaterSphere Silver.

O resultado organiza contatos de agenda. Ele não prevê diagnóstico, urgência ou
condição clínica e deve ser validado pela equipe responsável.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
import unicodedata


RiskLevel = Literal["BAIXO", "MEDIO", "ALTO"]
Sentiment = Literal["POSITIVO", "NEUTRO", "NEGATIVO"]
Action = Literal["CONFIRMACAO_AUTOMATICA", "LEMBRETE_REFORCADO", "LIGACAO_PRIORITARIA"]


@dataclass(frozen=True)
class RiskAssessment:
    score: int
    level: RiskLevel
    sentiment: Sentiment
    risk_terms: tuple[str, ...]
    action: Action
    factors: dict[str, int]


def normalize_text(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text.lower())
    without_accents = "".join(
        char for char in normalized if unicodedata.category(char) != "Mn"
    )
    return " ".join(without_accents.split())


NEGATIVE_TERMS = (
    "nao vou conseguir", "nao consigo", "nao posso", "muito cansad",
    "confus", "ansios", "preocupad", "triste", "dificuldade",
    "sem transporte", "esqueci", "reagendar", "remarcar", "talvez",
)
POSITIVE_TERMS = (
    "confirmo", "confirmada", "confirmado", "vou comparecer",
    "estarei presente", "pode confirmar", "estou bem", "obrigad",
)
RISK_TERMS = (
    "nao vou conseguir", "nao posso", "muito cansad", "confus",
    "sem transporte", "nao tenho quem me leve", "esqueci", "reagendar",
)


def detect_sentiment(message: str) -> Sentiment:
    """Classifica o tom declarado por vocabulário explícito em português."""
    text = normalize_text(message)
    negative_hits = sum(term in text for term in NEGATIVE_TERMS)
    positive_hits = sum(term in text for term in POSITIVE_TERMS)
    if negative_hits > positive_hits and negative_hits:
        return "NEGATIVO"
    if positive_hits > negative_hits and positive_hits:
        return "POSITIVO"
    return "NEUTRO"


def find_risk_terms(message: str) -> tuple[str, ...]:
    text = normalize_text(message)
    return tuple(term for term in RISK_TERMS if term in text)


def calculate_risk(
    *, message: str, age: int, prior_no_shows: int, days_until_appointment: int
) -> RiskAssessment:
    """Aplica os pesos documentados na apresentação do MVP.

    Pesos: sentimento negativo 35, duas ou mais faltas 30, consulta em até dois
    dias 20, idade a partir de 70 anos 10 e palavra-chave 5.
    """
    sentiment = detect_sentiment(message)
    terms = find_risk_terms(message)
    factors = {
        "Sentimento negativo na mensagem": 35 if sentiment == "NEGATIVO" else 0,
        "Histórico de 2 ou mais faltas": 30 if prior_no_shows >= 2 else 0,
        "Consulta em até 2 dias": 20 if days_until_appointment <= 2 else 0,
        "Idade a partir de 70 anos": 10 if age >= 70 else 0,
        "Palavra-chave de risco": 5 if terms else 0,
    }
    score = min(sum(factors.values()), 100)
    if score >= 70:
        level: RiskLevel = "ALTO"
        action: Action = "LIGACAO_PRIORITARIA"
    elif score >= 40:
        level = "MEDIO"
        action = "LEMBRETE_REFORCADO"
    else:
        level = "BAIXO"
        action = "CONFIRMACAO_AUTOMATICA"
    return RiskAssessment(score, level, sentiment, terms, action, factors)
