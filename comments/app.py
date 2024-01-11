import asyncio
import json
from urllib.parse import urlparse
from datetime import datetime, timedelta

from quart import Quart, websocket, render_template, jsonify, request, redirect
from peewee import fn

from comments import config
from comments.broker import Broker
from comments.models import Comment


app = Quart(__name__)
broker = Broker()


@app.get('/')
async def dashboard():
    """
    Dashboard with links for administration (soon).
    """
    comments_approved = Comment.select().where(Comment.approved == True).order_by(Comment.datestamp.desc())
    comments_pending = Comment.select().where(Comment.approved == False).order_by(Comment.datestamp.desc())
    urls = Comment.select().group_by(Comment.url)
    names = Comment.select().group_by(Comment.name)
    comments_by_date = {}
    oldest_comment_date = Comment.select().order_by(Comment.datestamp.asc()).first().datestamp
    today = datetime.today()
    days = today - oldest_comment_date
    date_list = list(reversed([(today - timedelta(days=x)).strftime('%Y-%m-%d') for x in range(days.days + 5)]))
    print(date_list)
    for comment in Comment.select():
        s = comment.datestamp.strftime('%Y-%m-%d')
        if s not in comments_by_date:
            comments_by_date[s] = 0
        comments_by_date[s] += 1
    return await render_template(
        "dashboard.html",
        comments_approved=comments_approved,
        comments_pending=comments_pending,
        urls=urls,
        comments_by_date=comments_by_date,
        names=names
    )


@app.get('/example')
async def example():
    """
    HTML table showing approved messages in the database.
    """
    messages = Comment.select().where(
        Comment.approved == True
    ).order_by(Comment.datestamp.desc())
    return await render_template(
        "example.html",
        messages=messages
    )


@app.get('/demo')
async def demo():
    """
    Demo page for posting messages.
    """
    if request.args.get('token') == config.ADMIN_TOKEN:
        return await render_template('demo.html')
    else:
        return redirect('/')


@app.get('/api/v1/replay')
async def replay():
    """
    RPC endpoint to allow a client to fetch 
    all approved messages for a given URL.
    """
    url = request.args.get('url')
    if not url:
        return jsonify({'message': 'please provide a url'}), 400
    data = list()
    messages = Comment.select().where(
        Comment.url == url,
        Comment.approved == True
    ).order_by(Comment.datestamp.asc()).limit(100)
    for m in messages:
        data.append({
            'message': m.message,
            'name': m.name,
            'datestamp': m.datestamp
        })
    res = jsonify(data)
    res.headers.add('Access-Control-Allow-Origin', '*')
    return res


@app.websocket('/api/v1/ws')
async def ws() -> None:
    """
    Websocket endpoint which brokers messages
    to and from connected clients.
    """
    try:
        task = asyncio.ensure_future(_receive())
        async for message in broker.subscribe():
            await websocket.send(message)
    finally:
        task.cancel()
        await task


async def _receive() -> None:
    """
    Internal function which handles logic
    for accepting messages over websockets.

    Does not post if messages are too long,
    are an invalid format, or the provided 
    URL is not setup as an allowed domain.
    """
    while True:
        message = await websocket.receive()
        try:
            message = json.loads(message)
            assert(message['name'])
            assert(message['url'])
            assert(message['message'])
        except Exception as e:
            await websocket.send(json.dumps({
                'message': 'invalid format'
            }))
            return False
        if urlparse(message['url']).hostname not in config.ACCEPT_DOMAINS:
            print('invalid domain: ', urlparse(message['url']).hostname)
            break
        if len(message) > 200:
            print('too long, skipping')
            break
        await broker.publish(message['name'], message['url'], message['message'])


def run() -> None:
    app.run(debug=True, use_reloader=True)