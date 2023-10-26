
from flask import Flask, jsonify, request
import pymysql
import json, datetime

app = Flask(__name__)

# 데이터 베이스 연결
db = pymysql.connect(host="localhost", 
                     user="root", password="passwd", 
                     db="test3",
                     charset="utf8",
                     cursorclass=pymysql.cursors.DictCursor)

cursor = db.cursor()

def json_default(value):
  if isinstance(value, datetime.date):
    return value.strftime('%Y-%m-%d')
  raise TypeError('not JSON serializable')  

def query_db(query, args=(), one=False):
    cur = db.cursor()
    cur.execute(query, args)
    r = [dict((cur.description[i][0], value) \
               for i, value in enumerate(row)) for row in cur.fetchall()]
    cur.connection.close()
    return (r[0] if r else None) if one else r

@app.route("/members", methods=['GET', 'POST'])
def members():

    cursor.execute("SELECT b.boardId, b.title, u.ID, b.location, date_format(b.createAt, '%Y-%m-%d') AS date FROM Board as b LEFT OUTER JOIN User as u on u.userId = b.userId WHERE b.status = 'active' ORDER BY b.createAt;")
    data = cursor.fetchall()
    return_data = json.dumps(data, default=json_default)
    return_data = return_data.strip('[')
    return_data = return_data.strip(']')

    print(return_data)

    # 반환할 때 json형식으로 반환
    return json.dumps(data, default=json_default)


@app.route("/insert", methods=['GET', 'POST'])
def datas() :
    userinfo = request.form
    user = request.get_json()

    print('/datas에 들어옴')
    print(user['name'])
    cursor.execute("INSERT INTO User(name, ID, password, phoneNumber) VALUES (%s, %s, %s, %s);",(user['name'], user['ID'], user['password'], user['phoneNumber']) )
    cursor.connection.commit()

    return ''
    
if __name__ == "__main__" :
    app.run(debug=True)