"""
과목별 파싱 전략 모듈
"""
from .math import MathParser
from .math1 import Math1Parser
from .korean import KoreanParser
from .literature import LiteratureParser
from .english import EnglishParser

__all__ = [
    "MathParser",
    "Math1Parser",
    "KoreanParser",
    "LiteratureParser",
    "EnglishParser",
]
