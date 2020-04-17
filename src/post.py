"""
Class for a post
"""

from datetime import datetime
from pydantic import BaseModel
from fastapi import Form
from db_actions import insert, gen_new_id, format_time, select


class Post(BaseModel):
    """
    BaseModel for a post
    """

    title: str
    content: str
    board: int
    ext: str = ""  # The extension of the image sent
    post_id: int = None
    created_at: datetime = None
    bumped_at: datetime = None
    bump_count: int = 0

    @classmethod
    async def from_db(cls, post_id):
        """
        Initializes a post from
        querying the DB, given the ID

        Args:
            cls: the post class
            post_id: the post ID
        Returns:
            The Post object
        """
        conds = "where post_id = %s limit 1"
        result = await select("posts", "*", conds, (post_id,))
        if result:
            return Post(**result[0])

    @classmethod
    def as_form(
        cls, title: str = Form(...), content: str = Form(...), board: int = Form(...)
    ):
        """
        Creates a post from a HTTP POST form

        Args:
            cls: the post class
            title: the post's title
            content: the post's content
            board: the post's board
        Returns:
            A new post object
        """
        return cls(board=board, title=title, content=content)

    async def add_to_db(self, ext=""):
        """
        Adds a new post to the DB

        Args:
            self: the post object
            ext: the post's image extension
        Returns:
            The ID of the new post
        """
        self.bumped_at = self.created_at = format_time(datetime.now().utcnow())
        self.post_id = await gen_new_id()
        self.ext = ext
        await insert("posts", tuple(self.dict().values()))
        return self.post_id
