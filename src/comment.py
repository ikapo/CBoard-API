"""
Class for a comment
"""

from datetime import datetime
from fastapi import Form
from pydantic import BaseModel
from db_actions import gen_new_id, format_time, select, insert


class Comment(BaseModel):
    """
    BaseModel for a comment
    """

    content: str
    board: int
    parent: int
    ext: str = ""  # The extension of the image sent
    com_id: int = 1
    created_at: datetime = datetime.utcnow()

    @classmethod
    def as_form(
        cls, content: str = Form(...), board: int = Form(...), parent: int = Form(...)
    ):
        """
        Creates a comment from a HTTP POST form

        Args:
            cls: the comment class
            content: the comment's content
            board: the comment's board
            parent: the comment's parent
        Returns:
            A new comment object
        """
        return cls(content=content, board=board, parent=parent)

    async def add_to_db(self, ext=""):
        """
        Adds a new comment to DB

        Args:
            self: the comment object
            ext: the comment's image extension
        Returns:
            The ID of the new comment
        """
        self.created_at = format_time(datetime.now().utcnow())
        self.com_id = await gen_new_id()
        self.ext = ext
        await insert("comments", tuple(self.dict().values()))
        return self.com_id

    @classmethod
    async def get_comments(cls, parent_id):
        """
        Returns list of all comments
        containing the same parent_id

        Args:
            cls: the comment class
            parent_id: the commnts' parent ID
        Returns:
            all the comment objects as a list
        """
        conds = "where parent = %s order by created_at asc"
        result = await select("comments", "*", conds, (parent_id,))
        if result:
            return [Comment(**comment) for comment in result]
