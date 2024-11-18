from sqlalchemy import (and_, create_engine, Table, Column, Integer, String, 
                        MetaData, BigInteger, delete, update, DateTime, select)
import requests
import asyncio
from datetime import datetime
from typing import Union, Any, Tuple
from data.config import defaultNotionAPI, databaseURL

engine = create_engine("sqlite:///../tables.db")

metadata = MetaData()

table = Table(
    "NotionUsers", metadata,
    Column("ID", Integer, primary_key = True, autoincrement = True),
    Column("userID", BigInteger, unique = True),
    Column("notionAPI", String, default = None),
    Column("databaseID", String, default = None)
)

metadata.create_all(engine)

table = Table ("NotionUsers", metadata, autoload_with = engine)

# check if user already have in NotionDB; also returns row if user exists
async def getNotionRow(userID: int) -> Tuple[bool, dict]:
    with engine.connect() as connection:
        check = connection.execute(select(table).
                                   where(userID == userID))
        result: dict = check.mappings().fetchone()
        connection.close()
        if result is not None:
            return True, dict(result)
        else: return False, None

async def addUserToNotion(userID: int, notionAPI: str, databaseID: str) -> bool:
    with engine.connect() as connection:
        change = connection.execute(table.insert().values(
            userID = userID,
            notionAPI = notionAPI,
            databaseID = databaseID
        ))
        connection.commit()
        connection.close()
        if change.rowcount == 1: return True
        else: return False

async def addRowToNotion(ID: int, userID: int, URL: str,
                         Source: str, notionAPI: str | None = None, databaseID: str | None = None) -> bool:
    headers = {
        "Authorization": f"Bearer {notionAPI or defaultNotionAPI}",
        "Notion-Version": "2022-06-28",
        "Content-Type": "application/json"
    }

    url = f"https://api.notion.com/v1/pages"

    data = {
        "parent": {
            "database_id": databaseID or databaseURL
        },
        "properties": {
            "ID": {
                "title": [
                    {
                        "text": {
                            "content": f"{ID}"
                        }
                    }
                ]
            },
            "userID": {
                "multi_select": [
                    {
                        "name": f"{userID}"
                    }
                ]
            },
            "URL": {
                "url": URL
            },
            "Source": {
                "rich_text": [
                    {
                        "text": {
                            "content": Source
                        }
                    }
                ]
            },
            "timestamp": {
                "rich_text": [
                    {
                        "text": {
                            "content": f"{datetime.now()}"
                        }
                    }
                ]
            }
        }
    }
    
    response = requests.post(url, headers = headers, json = data)

    if response.status_code == 200:
        return True
    else: return False

