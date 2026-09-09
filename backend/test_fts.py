import sqlite3
conn = sqlite3.connect(':memory:')
conn.execute('CREATE VIRTUAL TABLE t USING fts5(x)')
conn.execute('INSERT INTO t VALUES ("Next.js.")')
print(list(conn.execute("SELECT * FROM t WHERE x MATCH '"Next.js."'")))
