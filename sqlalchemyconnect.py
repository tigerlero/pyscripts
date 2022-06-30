from sqlalchemy import schema, types
from sqlalchemy.engine import create_engine
from sqlalchemy.sql import select
from sqlalchemy.sql import and_, or_, not_
from sqlalchemy import update
from sqlalchemy import delete
#from passlib.hash import pbkdf2_sha256
from sqlalchemy import *
metadata = schema.MetaData()
engine = create_engine("sqlite:///my.db",echo=True)
metadata.bind=engine

#hash = pbkdf2_sha256.encrypt("dummy_pass", round=20000, salt_size=16)

users = schema.Table("users", metadata,
schema.Column("id",types.Integer, primary_key=True),
schema.Column("name", types.Unicode(255), default=u''),
schema.Column('address', types.Unicode(255), default=u'Untitled Page'),
schema.Column('password', types.Text(), default="hash"),)

#phones= schema.Table('phones'.metadata,
#schema,Column('phone_id',types.Integer, primary_key=
#schema.Column('

metadata.create_all(checkfirst=True)
connection = engine.connect()
ins = users.insert(values=dict(name=u'tade',address=u'karaoli and dimitriou',password=u'qazxsw212'))
print ins
result = connection.execute(ins)
print result
i = users.insert()
i.execute(name="Mary",address="dfjbdsjh",password='secret')
i.execute(name="Peter",address="dnfuibd",password="secret2")
query=select([users])
result=connection.execute(query)
for row in result:
	print row

query = select([users],and_(users.c.id<=10,users.c.name.like(u"t%")))
query=query.order_by(users.c.name.desc(),users.c.id)
result=connection.execute(query)
print result.fetchall()
print select([func.count()]).select_from(users)
u = update(users, users.c.address==u"karaoli kai dimitriou")
connection.execute(u, address=u"grigoriou kai lampraki")

d=delete(users, users.c.id==1)
connection.execute(d)
connection.close()

