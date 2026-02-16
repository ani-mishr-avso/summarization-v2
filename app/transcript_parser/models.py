from dataclasses import dataclass, field


@dataclass(slots=True)
class TurnEntry:
    id: int
    start_time: float
    end_time: float
    duration: float
    text: str
    speaker_label: str
    sentiment_label: str | None = field(default=None)
    sentiment_score: float | None = field(default=None)
    sentiment_span: str | None = field(default=None)


@dataclass(slots=True)
class Speaker:
    turns: list[TurnEntry] = field(default_factory=list)
    num_turns: int = field(default=0)
    total_duration: float = field(default=0.0)
    longest_turn_duration: float = field(default=0.0)
    talk_percentage: float = field(default=0.0)
