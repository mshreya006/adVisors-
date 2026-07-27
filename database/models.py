from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional

@dataclass
class Article:
    url: str
    title: str
    description: str
    source_name: str
    published_at: str
    predicted_industry: Optional[str] = None
    industry_confidence: Optional[float] = None
    fake_news_prediction: Optional[str] = None
    fake_news_confidence: Optional[float] = None
    is_bookmarked: int = 0
    fetched_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_row(cls, row) -> "Article":
        """Helper to create an Article object from a SQLite row."""
        return cls(
            url=row[0],
            title=row[1],
            description=row[2],
            source_name=row[3],
            published_at=row[4],
            predicted_industry=row[5],
            industry_confidence=row[6],
            fake_news_prediction=row[7],
            fake_news_confidence=row[8],
            is_bookmarked=row[9],
            fetched_at=row[10]
        )
