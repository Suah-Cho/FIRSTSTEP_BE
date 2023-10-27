
from flask import Flask, jsonify, request
import utils.utils as utils
import pymysql
import json, datetime

app = Flask(__name__)

# 데이터 베이스 연결
def getCon():
  return pymysql.connect(host="localhost", 
                     user="root", password="passwd", 
                     db="test3",
                     charset="utf8",
                     cursorclass=pymysql.cursors.DictCursor)

def json_default(value):
  if isinstance(value, datetime.date):
    return value.strftime('%Y-%m-%d')
  raise TypeError('not JSON serializable')  


@app.route('/boardlist', methods=['GET', 'POST'])
def boardlist() :
    con = getCon()
    cursor = con.cursor()
    cursor.execute("SELECT b.boardId, b.title, u.ID, b.location, date_format(b.createAt, '%Y-%m-%d') AS date FROM Board as b LEFT OUTER JOIN User as u on u.userId = b.userId WHERE b.status = 'active' ORDER BY b.createAt DESC;")
    data = cursor.fetchall()
    # return_data = json.dumps(data, default=json_default)

    # 반환할 때 json형식으로 반환
    return json.dumps(data, default=json_default)

@app.route('/boardDetail', methods=[ 'POST'])
def boardDetail():
  # boardId =int(request.get_data())
  boardId = request.get_json()
  id = boardId['id']

  con = getCon()
  cursor = con.cursor()
  sql = 'SELECT * FROM Board WHERE boardId = %s;'
  cursor.execute(sql, (id, ))
  data = cursor.fetchall()
  cursor.close()
    
  # 반환할 때 json형식으로 반환
  return json.dumps(data, default=json_default)

@app.route('/boardWrite', methods=['POST'])
def boardWrite() :
  boardData = request.get_json()
  print(boardData)

  con = getCon()
  cursor = con.cursor()
  sql = "INSERT INTO Board (userId, title, content, location) VALUES ((SELECT userId FROM User WHERE ID = %s), %s, %s, %s);"
  cursor.execute(sql, ('test', boardData['title'], boardData['content'], boardData['location']))
  cursor.connection.commit()


  return '성공적으로 등록되었습니다:)'

@app.route('/login', methods=['POST'])
def login() :
  userData = request.get_json()
  id_receive = userData['userId']
  pw_receive = userData['userPW']

  con = getCon()
  cursor = con.cursor()
  sql = "SELECT userId, ID, password FROM User WHERE ID = %s AND status = 'active';"
  cursor.execute(sql, userData['userId'])

  row = cursor.fetchone()
  
  if id_receive == row['ID'] and  utils.verfifyPwd(pw_receive, row['password']):
    return json.dumps(row, default=json_default)
  else :
    return "Login Failed"



    
if __name__ == "__main__" :
    app.run(debug=True)