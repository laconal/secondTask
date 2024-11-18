from sqlalchemy import (and_, create_engine, Table, Column, Integer, String, 
                        MetaData, BigInteger, delete, update, DateTime, select, Boolean)
from typing import List, Tuple, Union, Any
from bs4 import BeautifulSoup
import requests
from datetime import datetime
from database.NotionDB import getNotionRow, addRowToNotion

engine = create_engine('sqlite:///../tables.db')

metadata = MetaData()


### comment about mappings(), if it gets one row (using fetchone) - it gets as SQLAlchemy object, not as dict or list
### if gets more than one (using fetchall) - then object is list of dicts (even if gets one row)


table = Table(
    "MessagesURL", metadata,
    Column("ID", Integer, primary_key = True, autoincrement = True),
    Column("userID", BigInteger),
    Column("URL", String),
    Column("Title", String, default = None),
    Column("Source", String, default = None),
    Column("Category", String),
    Column("Priority", Integer, default = None),
    Column("inNotion", Boolean, default = False),
    Column("timestamp", DateTime)
)
metadata.create_all(engine)

table = Table("MessagesURL", metadata, autoload_with = engine)

### testing
# from NotionDB import getNotionRow, addRowToNotion
# with engine.connect() as conn:
#     # q = conn.execute(table.select())
#     q = conn.execute(table.select())
#     result = q.mappings().fetchall()
#     print(type(result))


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
                                  Title = title, Source = source, inNotion = False, timestamp = datetime.now(),)
        )
        connection.commit()
        if check.rowcount == 1:
            resultText = "Successfully saved in local database"
            notionCheck, notionValues = await getNotionRow(userID)
            # user's notionValues: [2] - Notion API, [3] - Database ID
            
            lastID = connection.execute(select(table).order_by(table.c.ID.desc()).limit(1)).fetchone()[0]

            if await addRowToNotion(lastID, userID, URL, source):
                resultText = "Successfully saveв in local and default Notion databases"
            # add to default Notion database

            if notionCheck: # add URL to Notion
                addedToNotion = await addRowToNotion(lastID, userID, URL, source,
                                                     notionValues[2], notionValues[3])
                if addedToNotion: 
                    resultText = "Successfully saved in local and  Notion (default and yours) database"
                    connection.execute(update(table).
                                                where(table.c.ID == lastID).
                                                values({"inNotion": True}))
                    connection.commit()
            connection.close()
            return True, resultText
        else:
            connection.close()
            return False, "There occurs error while adding your url(s) to database."
    
async def getRow(urlID: int) -> Union[dict, bool]:
    with engine.connect() as connection:
        global table
        row = connection.execute(select(table).
                                 where(table.c.ID == urlID))
        result = row.mappings().fetchone()
        if result is None: return False
        connection.close()
        return dict(result)

async def getRowsBy(userID: int, property: str, propertyValue: str | int | bool = None) -> Union[List, bool]:
    global table
    with engine.connect() as connection:
        result = []
        rows: Any
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
        elif property == "inNotion":
            rows = connection.execute(select(table).
                                      where(and_(
                                          table.c.userID == userID,
                                          table.c.inNotion == propertyValue
                                      )))
        
        result = rows.mappings().fetchall()
        if result is None: return False
        return result

# get all rows with user ID
async def userLinksList(userID: int) -> Union[list, bool]:
    with engine.connect() as connection:
        global table
        result = [] 
        rows = connection.execute(select(table).
                                  where(table.c.userID == userID))
        result = rows.mappings().fetchall()
        if not result: return False
        connection.close()
        return result

async def change(ID: str, property: str, value: str | int | bool) -> bool:
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
                                    where(table.c.ID == ID).
                                    values(newValue))
            connection.commit()
            connection.close()
            if check.rowcount == 1: return True
            else: return False
        elif property in ["Title", "Category", "Priority", "inNotion"]:
            newValue = {property: value}
            check = connection.execute(update(table).
                                    where(table.c.ID == ID).
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
