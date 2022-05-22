import sqlite3

connection = sqlite3.connect("polybot.db")
cur = connection.cursor()

cur.execute("CREATE TABLE qpr (asker numeric, asked numeric, confirmed numeric)")
cur.execute("CREATE TABLE dating (asker numeric, asked numeric, confirmed numeric)")
cur.execute("CREATE TABLE fwb (asker numeric, asked numeric, confirmed numeric)")

connection.commit()
connection.close()

print("successfully created database")
