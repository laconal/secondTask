from sqlalchemy import (and_, create_engine, Table, Column, Integer, String, 
                        MetaData, BigInteger, delete, update, DateTime, select)
import asyncio
from typing import List, Tuple, Union
from bs4 import BeautifulSoup
import requests
from datetime import datetime
from database.NotionDB import getNotionRow, addRowToNotion

engine = create_engine('sqlite:///tables.db')

metadata = MetaData()

table = Table(
    "MessagesURL", metadata,
    Column("ID", Integer, primary_key = True, autoincrement = True),
    Column("userID", BigInteger),
    Column("URL", String),
    Column("Title", String, default = None),
    Column("Source", String, default = None),
    Column("Category", String),
    Column("Priority", Integer, default = None),
    Column("timestamp", DateTime)
)
metadata.create_all(engine)


table = Table("MessagesURL", metadata, autoload_with = engine)

async def addURL(userID: int, URL: str, source: str) -> Tuple[bool, str]:
    with engine.connect() as connection:
        global table
        if not URL.startswith("http://") or URL.startswith("https://"):
            URL = f"http://{URL}"
        title = ''

        try:
            response = requests.get(URL)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, "html.parser")
                title = soup.title.string if soup.title else None
        except requests.exceptions.ConnectionError as connectionErrorURL:
            title = None

        check = connection.execute(
            table.insert().values(userID = userID, URL = URL,
                                  Title = title, Source = source, timestamp = datetime.now())
        )
        connection.commit()
        if check.rowcount == 1:
            resultText = "Successfully saved in local database"
            notionCheck, notionValues = await getNotionRow(userID)
            # notionValues [2] - Notion API, [3] - Database ID

            lastID = connection.execute(select(table).order_by(table.c.ID.desc()).limit(1)).fetchone()[0]
            if notionCheck: # add URL to Notion
                addedToNotion = await addRowToNotion(lastID, userID, URL, source,
                                                     notionValues[2], notionValues[3])
                if addedToNotion: resultText = "Successfully saved in local and Notion database"
            connection.close()
            return True, resultText
        else:
            connection.close()
            return False, "There occurs error while adding your url(s) to database."
    
async def getRow(urlID: int) -> Union[dict, bool]:
    with engine.connect() as connection:
        global table
        result = {}
        row = connection.execute(select(table).
                                 where(table.c.ID == urlID))
        rowValues = row.fetchone()
        if rowValues is None: return False
        columns = table.columns.keys()
        rowIterator = 0
        for col in columns:
            result[col] = rowValues[rowIterator] or "Not specified"
            rowIterator += 1
        connection.close()
        return result
    
async def getRows(rows, columns) -> List:
    result = []
    for row in rows:
        rowIterator = 0
        row_dict = {}
        for col in columns:
            row_dict[col] = row[rowIterator]
            rowIterator += 1
        result.append(row_dict)
    return result


async def getRowsBy(userID: int, property: str, propertyValue: str | int = None) -> Union[List, bool]:
    global table
    with engine.connect() as connection:
        result = []
        if property == "Category":
            if propertyValue is None:
                rows = connection.execute(select(table).
                                    where(and_(
                                        table.c.userID == userID,
                                        table.c.Category.is_(None)
                                    )))
            else: rows = connection.execute(select(table).
                                    where(and_(
                                        table.c.userID == userID,
                                        table.c.Category == propertyValue
                                    )))
        elif property == "Source":
            if propertyValue is None:
                rows = connection.execute(select(table).
                                    where(and_(
                                        table.c.userID == userID,
                                        table.c.Source.is_(None)
                                    )))
            else: rows = connection.execute(select(table).
                                    where(and_(
                                        table.c.userID == userID,
                                        table.c.Source == propertyValue
                                    )))
        elif property == "Priority":
            if propertyValue is None:
                rows = connection.execute(select(table).
                                    where(and_(
                                        table.c.userID == userID,
                                        table.c.Priority.is_(None)
                                    )))
            else: rows = connection.execute(select(table).
                                    where(and_(
                                        table.c.userID == userID,
                                        table.c.Priority == propertyValue
                                    )))
        
        rowsValues = rows.fetchall()
        if rowsValues is None: return False
        columns = table.columns.keys()
        result = await getRows(rowsValues, columns)
        return result

# get all rows with user ID
async def userLinksList(userID: int) -> Union[list, bool]:
    with engine.connect() as connection:
        global table
        result = [] 
        rows = connection.execute(select(table).
                                  where(table.c.userID == userID))
        values = rows.fetchall()
        if not values: return False
        columns = table.columns.keys()
        result = await getRows(values, columns)
        connection.close()
        return result

async def change(urlID: str, property: str, value: str | int) -> bool:
    global table
    with engine.connect() as connection:
        if property == "URL":
            if not value.startswith("http://") or value.startswith("https://"):
                value = f"http://{value}"
            title = ''
            try:
                response = requests.get(value)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, "html.parser")
                    title = soup.title.string if soup.title else None
            except requests.exceptions.ConnectionError as connectionErrorURL:
                title = None

            newValue = {property: value, "Title": title}
            check = connection.execute(update(table).
                                    where(table.c.ID == urlID).
                                    values(newValue))
            connection.commit()
            connection.close()
            if check.rowcount == 1: return True
            else: return False
        elif property in ["Title", "Category", "Priority"]:
            newValue = {property: value}
            check = connection.execute(update(table).
                                    where(table.c.ID == urlID).
                                    values(newValue))
            connection.commit()
            connection.close()
            if check.rowcount == 1: return True
            else: return False

async def removeURL(urlID: int) -> bool:
    with engine.connect() as connection:
        global table
        check = connection.execute(delete(table).
                                   where(table.c.ID == urlID))
        connection.commit()
        connection.close()
        if check.rowcount == 1:return True
        else: return False

async def deleteAllURLs(userID: int) -> Union[bool, int]:
    global table
    with engine.connect() as connection:
        check = connection.execute(delete(table).
                                   where(table.c.userID == userID))
        connection.commit()
        connection.close()
        if check.rowcount >= 1:
            return True, check.rowcount
        else:
            return False, 0

#### dropping Table
# with engine.connect() as connection:
#     a = Table('MessagesURL', metadata, autoload_with = engine)
#     a.drop(connection)
#     connection.commit()
#     connection.close()
