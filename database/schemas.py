from typing import List, Optional

from pydantic import BaseModel


class TweetIN(BaseModel):
    tweet_data: str
    tweet_media_ids: Optional[List[int]]
