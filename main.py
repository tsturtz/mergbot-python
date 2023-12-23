import json
import logging
import requests
from os import getenv
from dotenv import load_dotenv
from typing import List, Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

load_dotenv()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("webhook")


app = FastAPI()

class Sender(BaseModel):
    id: str

class Recipient(BaseModel):
    id: str

class Message(BaseModel):
    mid: str
    text: str

class MessageMeta(BaseModel):
    sender: Sender
    recipient: Recipient
    timestamp: int
    message: Message

class Entry(BaseModel):
    id: str
    time: int
    messaging: List[MessageMeta]

class Body(BaseModel):
    object: str
    entry: List[Entry]


@app.get("/")
def root():
    return {"message": "root"}

@app.get("/health")
def health():
    return {"status": "UP"}

@app.get("/webhook")
def verify(
    verify_token: Optional[str] = Query(None, alias="hub.verify_token", regex="^[A-Za-z1-9-_]*$"),
    challenge: Optional[str] = Query(None, alias="hub.challenge"),
    mode: Optional[str] = Query("subscribe", alias="hub.mode", regex="^[A-Za-z1-9-_]*$"),
) -> Optional[str]:
    token = getenv("VERIFY_TOKEN")
    if verify_token == token and mode == "subscribe":
        logger.info("WEBHOOK_VERIFIED")
        # Respond with the challenge token from the request
        return PlainTextResponse(f"{challenge}")
    else:
        raise HTTPException(status_code=403, detail="Token invalid.")

@app.post("/webhook")
def event(body: Body):
    try:
        sender_id = body.entry[0].messaging[0].sender.id
        sender_msg = body.entry[0].messaging[0].message.text;
        logger.info("incoming message: " + sender_msg)
        outgoing_msg = "wassup"
        if sender_msg == "merg":
            outgoing_msg = "merg is the word"
        request_body = {
            "recipient": {"id": sender_id},
            "message": {"text": outgoing_msg},
            "messaging_type": "RESPONSE",
            "access_token": getenv("PAT"),
        }
        logger.info(request_body)

        response = requests.post(
            "https://graph.facebook.com/v18.0/" + getenv("PAGE_ID") + "/messages",
            json=request_body,
        ).json()
        logger.info(response)
    except KeyError:
        logger.info("Message sent and received by recipient. ✅")
        pass
    return None

