
from flask import Flask, jsonify, request
import utils.utils as utils
import pymysql
import json, datetime
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app, resources={r"/*": {"origins": "*"}})

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

# BoardContent.js 게시물 상세정보
@app.route('/boardDetail', methods=[ 'POST'])
def getBoardId():
  # boardId =int(request.get_data())
  boardId = request.get_json()
  id = boardId['id']

  con = getCon()
  cursor = con.cursor()
  # sql = 'SELECT * FROM Board WHERE boardId = %s;'
  # sql = ""
  cursor.execute("SELECT b.boardId, b.title, u.userId, u.ID, b.content, b.location, date_format(b.createAt, '%Y-%m-%d') AS createAt  FROM Board as b LEFT OUTER JOIN User as u on u.userId = b.userId WHERE boardId = {} ORDER BY b.createAt DESC;".format(id))
  data = cursor.fetchall()
  cursor.close()
    
  # 반환할 때 json형식으로 반환
  return json.dumps(data, default=json_default)

# BoardViewContent.js 게시물 수정
@app.route('/boardEdit', methods=['POST'])
def boardEdit() :
  boardData = request.get_json()
  print(boardData)
  con = getCon()
  cursor = con.cursor()

  cursor.execute("UPDATE Board SET title = '{}' WHERE boardId = {};".format(boardData['title'], boardData['boardId']))
  cursor.execute("UPDATE Board SET content = '{}' WHERE boardId = {};".format(boardData['content'], boardData['boardId']))
  cursor.connection.commit()


  return '성공적으로 수정되었습니다:)'

 # BoardViewContent.js 게시물 삭제
@app.route('/boardDelete', methods=['POST'])
def boardDelete() :
  boardData = request.get_json()
  print(boardData)
  con = getCon()
  cursor = con.cursor()

  cursor.execute("UPDATE Board SET status = 'inactive' WHERE boardId = {};".format(boardData['boardId']))
  cursor.connection.commit()


  return '성공적으로 삭제되었습니다'

# BoardWrite.js 게시물 등록
@app.route('/boardWrite', methods=['POST'])
def boardWrite() :
  boardData = request.get_json()
  print(boardData)

  con = getCon()
  cursor = con.cursor()
  sql = "INSERT INTO Board (userId, title, content, location) VALUES (%s, %s, %s, %s);"
  cursor.execute(sql, (boardData['userId'], boardData['title'], boardData['content'], boardData['location']))
  cursor.connection.commit()

  sql = 'SELECT ID FROM User WHERE userId=%s;'
  cursor.execute(sql, (boardData['userId']))
  id = cursor.fetchone()


  return id

# Login.js 로그인
@app.route('/login', methods=['POST'])
def login() :
  userData = request.get_json()
  id_receive = userData['userId']
  pw_receive = userData['userPW']

  con = getCon()
  cursor = con.cursor()
  sql = "SELECT userId, ID, password, status FROM User WHERE ID = %s;"
  cursor.execute(sql, userData['userId'])

  row = cursor.fetchone()

  try :
    if row['status'] == 'active':
      if id_receive == row['ID'] and  utils.verfifyPwd(pw_receive, row['password']):
        return json.dumps(row, default=json_default)
    else :
      return 'SIGNOUTUSER'
  except :
    return "NONUSER"
  
  

@app.route('/checkid', methods=['POST'])
def checkid() :
  userData = request.get_json()

  con = getCon()
  cursor = con.cursor()
  sql = "SELECT ID FROM User WHERE userId = %s"
  cursor.execute(sql, userData['userId'])
  id = cursor.fetchone()
  print(id)

  return id


@app.route('/signup', methods=['POST'])
def createUser():
  con = getCon()
  cursor = con.cursor()

  try:
    userData = request.get_json()
    # print(userData)

    name = userData['name']
    ID = userData['ID']
    password = userData['password']
    phoneNumber =userData['phoneNumber']
    password_confirm = userData['password_confirm']

    # ID existence check
    cursor.execute("SELECT ID from User WHERE ID = %s", ID)
    checkID = cursor.fetchone()

    if checkID:
      msg = "회원 가입에 실패했습니다.\n  -  존재하는 아이디입니다. 다른 아이디를 사용해주세요."
      return { 'msg':  msg, 'status' : 401}, { 'Content-Type': 'application/json' }

    #phoneNumber existence check
    cursor.execute("SELECT phoneNumber from User WHERE phoneNumber = %s", phoneNumber)
    checkPhone= cursor.fetchone()

    if checkPhone :
      msg = "회원 가입에 실패했습니다.\n  -  존재하는 전화번호 입니다. 다시 확인해주세요"
      return { 'msg':  msg, 'status' : 401}, { 'Content-Type': 'application/json' }
    
    if len(ID) < 4 or len(ID) > 16 :
      msg = "회원 가입에 실패했습니다.\n  -  아이디는 4~16자로 작성하세요."
      return { 'msg':  msg, 'status' : 401}, { 'Content-Type': 'application/json' }    
    
    if not utils.onlyalphanum(ID) :
      msg = "회원 가입에 실패했습니다.\n  -  아이디는 영문 대소문자와 숫자로 작성하세요"
      return { 'msg':  msg, 'status' : 401}, { 'Content-Type': 'application/json' }
      
    if not phoneNumber.isdecimal() :
      msg = "회원 가입에 실패했습니다.\n  - 전화번호는 숫자만 작성하세요. "
      return { 'msg':  msg, 'status' : 401}, { 'Content-Type': 'application/json' }
    
    if  not name.isalpha():
      msg = "회원 가입에 실패했습니다.\n  - 이름은 한글 또는 영어로만 작성하세요 "
      return { 'msg':  msg, 'status' : 401}, { 'Content-Type': 'application/json' }
    
    if  password != password_confirm:
      msg = "회원 가입에 실패했습니다.\n  - 비밀번호 확인 란에 동일한 비밀번호를 입력하세요. "
      return { 'msg':  msg, 'status' : 401}, { 'Content-Type': 'application/json' }
        

    hashed_password = utils.hash_password(str(password))

    user_info = [ name , ID , hashed_password, phoneNumber ]

    cursor.execute("INSERT INTO User(name, ID, password, phoneNumber) VALUES (%s, %s, %s, %s)", 
                  (user_info[0], user_info[1], user_info[2], user_info[3]))
    result = cursor.connection.insert_id()	
    cursor.connection.commit()
    msg = "환영합니다. 회원가입에 성공했습니다 :)"
    return { 'msg':  msg, 'status' : 200}
  
  except Exception as e :
      return {'error': str(e)}
  
@app.route('/signout', methods=['POST'])
def signout() :
  userData = request.get_json()
  
  con = getCon()
  cursor = con.cursor()
  sql = "UPDATE User SET status = 'inactive' WHERE userId = %s and status = 'active';"
  cursor.execute(sql, userData['userId'])
  cursor.connection.commit()

  return "성공적으로 회원탈퇴되었습니다."

    
if __name__ == "__main__" :
    app.run(debug=True)