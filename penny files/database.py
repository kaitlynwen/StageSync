#!/usr/bin/env python

#-----------------------------------------------------------------------
# database.py
# Author: Bob Dondero
#-----------------------------------------------------------------------

import os
import sqlalchemy
import sqlalchemy.orm
import dotenv

#-----------------------------------------------------------------------

dotenv.load_dotenv()
_DATABASE_URL = os.environ['DATABASE_URL']
_DATABASE_URL = _DATABASE_URL.replace('postgres://', 'postgresql://')

#-----------------------------------------------------------------------

Base = sqlalchemy.orm.declarative_base()

class Book (Base):
    __tablename__ = 'books'
    isbn = sqlalchemy.Column(sqlalchemy.String, primary_key=True)
    author = sqlalchemy.Column(sqlalchemy.String)
    title = sqlalchemy.Column(sqlalchemy.String)

_engine = sqlalchemy.create_engine(_DATABASE_URL)

#-----------------------------------------------------------------------

def get_books(author):

    books = []

    with sqlalchemy.orm.Session(_engine) as session:

        query = session.query(Book).filter(
            Book.author.ilike(author+'%'))
        table = query.all()
        for row in table:
            book = {'isbn': row.isbn, 'author': row.author,
            	'title': row.title}
            books.append(book)

    return books

#-----------------------------------------------------------------------

# For testing:

def _test():
    books = get_books('ker')
    for book in books:
        print(book['isbn'])
        print(book['author'])
        print(book['title'])
        print()

if __name__ == '__main__':
    _test()
