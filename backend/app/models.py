from enum import Enum
from typing import Optional

from pydantic import BaseModel


class SkillLevel(str, Enum):
    UNKNOWN = "unknown"
    WEAK = "weak"
    DEVELOPING = "developing"
    STRONG = "strong"


class SessionResponse(BaseModel):
    session_id: str
    profile: dict[str, SkillLevel]


class LessonResponse(BaseModel):
    topic: str
    content: str
    intro: str
    profile: dict[str, SkillLevel]


class StartPracticeRequest(BaseModel):
    session_id: str
    topic: str


class PracticeProblem(BaseModel):
    problem_id: str
    topic: str
    skill: str
    prompt: str


class StepRequest(BaseModel):
    session_id: str
    problem_id: str
    student_answer: Optional[str] = None
    image_base64: Optional[str] = None


class StepResponse(BaseModel):
    correct: bool
    solved: bool
    attempt_number: int
    reply: str
    profile: dict[str, SkillLevel]


class ChatRequest(BaseModel):
    session_id: str
    message: str
    image_base64: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    profile: dict[str, SkillLevel]
