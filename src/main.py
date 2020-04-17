"""
The main file for the API
"""

import os
from fastapi import FastAPI, File, UploadFile, Depends
from fastapi.responses import RedirectResponse as Redirect
from fastapi.staticfiles import StaticFiles
import aiofiles

from post import Post
from comment import Comment
from db_actions import initialize, select, close_db


# Initializing the API app
app = FastAPI(
    redoc_url=None,
    title="CBoard API",
    version="1.0.0",
    openapi_prefix="/api/v1/",
    breaks=True,
)

# Static file serving for the images
if not os.path.exists("img"):
    os.makedirs("img")
app.mount("/img", StaticFiles(directory="img"), name="img")


# ----------Startup/Shutodwn functions-----------
@app.on_event("startup")
def startup():
    """
    Initializing the DB on startup
    """
    print("Starting up...")
    initialize()


@app.on_event("shutdown")
async def shutdown():
    """
    Closing down the DB connection on shutdown
    """
    print("Closing connection to DB...")
    await close_db()


# ---------------------------------------


# ----------Content related functions-----------
async def init_content(img, con):
    """
    Initializes the content it receives:
    1. saves the image of one is sent
    2. adds the post/comment to the DB
    3. returns the new post/comment ID

    Args:
        img: the image sent,
        con: the content (post/comment)

    Returns:
        The new content's ID, None if bad filename
    """
    if img.filename:
        if not img.filename.find(".") == -1:
            ext = img.filename.split(".")[1].lower()
            if ext in ["jpg", "jpeg", "gif", "png"]:
                con_id = await con.add_to_db(ext)
                img_bytes = await img.read()
                await save_image(img_bytes, con_id, ext)
                return con_id
    else:
        con_id = await con.add_to_db()
        return con_id


async def save_image(img_bytes, img_id, ext):
    """
    Saves an image to to img directory

    Args:
        img_bytes: the byte content of the image
        filename: image filename
        img_id: the post ID of the post,
        will be the images new filename

    Returns:
        None
    """
    save_path = f"./img/{img_id}.{ext}"
    async with aiofiles.open(save_path, "wb") as img_file:
        await img_file.write(img_bytes)


# ---------------------------------------


# ----------HTTP POST functions-----------
@app.post("/newpost")
async def new_post(img: UploadFile = File(...), post: Post = Depends(Post.as_form)):
    """
    Get a new post,
    adds it to the DB
    and its image to the fileserver

    Args:
        title: the title of the post,
        content: the content of the post,
        board: the board number of the post,
        img: the image of the post

    Returns:
        Redirect: Redirect to the post's page
        or to / if error occured
    """

    post_id = await init_content(img, post)
    if post_id:
        url = f"/post/{post_id}"
        return Redirect(url=url, status_code=301)
    return Redirect(url="/", status_code=301)


@app.post("/newcomment")
async def new_comment(
    img: UploadFile = File(...), com: Comment = Depends(Comment.as_form),
):
    """
    Inserts a new comment into the DB
    and its image to the fileserver

    Args:
        img: the image of the post,
        com: the Comment, parsed from JSON

    Returns:
        Redirect: Redirect to the comment page
        or to / if error occured
    """

    com_id = await init_content(img, com)
    if com_id:
        url = f"/post/{com.parent}#c{com_id}"
        return Redirect(url=url, status_code=301)
    return Redirect(url="/", status_code=301)


# ---------------------------------------

# ----------HTTP GET functions-----------
# Docstrings have \n to format Swagger docs
@app.get("/board/{num}")
async def get_board(num: int = 1):
    """
    Gets a request for posts in a board and
    returns the last 10 posts in that board

    Args:
        num: the number of the board

    Returns:
        JSON list of the last 10 posts in that board
    """
    posts = [{}]
    attrs = "*"
    conds = "where board = %s order by bumped_at desc limit 10"
    params = (num,)
    posts = await select("posts", attrs, conds, params)
    if posts:
        posts = [Post(**p).dict() for p in posts]
    return posts


@app.get("/post/{post_id}")
async def get_post(post_id: int = 1):
    """
    Gets a request for a post
    and returns its json (including comments)

    Args:
        post_id: the ID of the post

    Returns:
        dict: json containing the post and its comments
    """
    post = await Post.from_db(post_id)
    if post:
        post_json = post.dict()
        comments = await Comment.get_comments(parent_id=post_id)
        comments_json = [c.dict() for c in comments] if comments else [{}]
        return {"post": post_json, "comments": comments_json}
    else:
        return {"post": {}, "comments": [{}]}


# ---------------------------------------
