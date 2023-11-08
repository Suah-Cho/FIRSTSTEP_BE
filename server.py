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
                     db="firststep",
                     charset="utf8",
                     cursorclass=pymysql.cursors.DictCursor)

def json_default(value):
  if isinstance(value, datetime.date):
    return value.strftime('%Y-%m-%d')
  raise TypeError('not JSON serializable')  

@app.route('/boardlist', methods=['GET'])
def boardlist() :
    con = getCon()
    cursor = con.cursor()
    cursor.execute("SELECT b.boardId, b.title, u.ID, b.location, date_format(b.createAt, '%Y-%m-%d') AS createAt FROM board as b LEFT OUTER JOIN user as u on u.userId = b.userId WHERE b.status = 'active' ORDER BY b.createAt DESC;")
    data = cursor.fetchall()

    # 반환할 때 json형식으로 반환
    return json.dumps(data, default=json_default)

# boardContent.js 게시물 상세정보
@app.route('/board/detail/<boardId>', methods=['GET'])
def getboardId(boardId : int):

  con = getCon()
  cursor = con.cursor()

  cursor.execute("SELECT status FROM board WHERE boardId = {};".format(boardId)) 
  status = cursor.fetchone()
  print(status['status']) 

  if status['status'] == 'active' :
    cursor.execute("SELECT b.boardId, b.title, u.userId, u.ID, b.content, b.location, date_format(b.createAt, '%Y-%m-%d') AS createAt  FROM board as b LEFT OUTER JOIN user as u on u.userId = b.userId WHERE boardId = {} ORDER BY b.createAt DESC;".format(boardId))
    data = cursor.fetchall()
    cursor.close()
      
    # 반환할 때 json형식으로 반환
    return json.dumps(data, default=json_default)
  else :
    return "DELETE"

  

# boardViewContent.js 게시물 수정
@app.route('/boardEdit/<boardId>', methods=['PUT'])
def boardEdit(boardId : int) :
  boardData = request.get_json()
  print(boardData)
  con = getCon()
  cursor = con.cursor()

  cursor.execute("UPDATE board SET title = '{}' WHERE boardId = {};".format(boardData['title'], boardId))
  cursor.execute("UPDATE board SET content = '{}' WHERE boardId = {};".format(boardData['content'], boardId))
  cursor.connection.commit()


  return '성공적으로 수정되었습니다:)'

 # boardViewContent.js 게시물 삭제
@app.route('/boardDelete/<boardId>', methods=['DELETE'])
def boardDelete(boardId : int) :

  con = getCon()
  cursor = con.cursor()

  cursor.execute("UPDATE board SET status = 'inactive' WHERE boardId = {};".format(boardId))
  cursor.connection.commit()


  return '성공적으로 삭제되었습니다'

# boardWrite.js 게시물 등록
@app.route('/boardWrite', methods=['POST'])
def boardWrite() :
  boardData = request.get_json()

  con = getCon()
  cursor = con.cursor()
  sql = "INSERT INTO board (userId, title, content, location) VALUES (%s, %s, %s, %s);"
  cursor.execute(sql, (boardData['userId'], boardData['title'], boardData['content'], boardData['location']))
  cursor.connection.commit()

  sql = 'SELECT ID FROM user WHERE userId=%s;'
  cursor.execute(sql, (boardData['userId']))
  id = cursor.fetchone()


  return id

# Login.js 로그인
@app.route('/login/<ID>/<password>', methods=['GET'])
def login(ID:str, password:str) :

  con = getCon()
  cursor = con.cursor()
  sql = "SELECT userId, ID, password, status FROM user WHERE ID = %s;"
  cursor.execute(sql, ID)

  user = cursor.fetchone()

  try :
    if user['status'] == 'active':
      if ID == user['ID'] and  utils.verfifyPwd(password, user['password']):
        return json.dumps(user, default=json_default)
    else :
      return 'SIGNOUTuser'
  except :
    return "NONuser"
  
  
# userid체크
@app.route('/checkid/<userId>', methods=['GET'])
def checkid(userId: int) :

  con = getCon()
  cursor = con.cursor()
  sql = "SELECT ID FROM user WHERE userId = %s"
  cursor.execute(sql, userId)
  id = cursor.fetchone()

  return id


@app.route('/signup', methods=['POST'])
def createuser():
  con = getCon()
  cursor = con.cursor()

  try:
    userData = request.get_json()

    name = userData['name']
    ID = userData['ID']
    password = userData['password']
    phoneNumber =userData['phoneNumber']
    password_confirm = userData['password_confirm']

    # ID existence check
    cursor.execute("SELECT ID from user WHERE ID = %s", ID)
    checkID = cursor.fetchone()

    if checkID:
      msg = "회원 가입에 실패했습니다.\n  -  존재하는 아이디입니다. 다른 아이디를 사용해주세요."
      return { 'msg':  msg, 'status' : 401}, { 'Content-Type': 'application/json' }

    # phoneNumber existence check
    cursor.execute("SELECT phoneNumber from user WHERE phoneNumber = %s", phoneNumber)
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

    cursor.execute("INSERT INTO user(name, ID, password, phoneNumber) VALUES (%s, %s, %s, %s)", 
                  (user_info[0], user_info[1], user_info[2], user_info[3]))
    result = cursor.connection.insert_id()	
    cursor.connection.commit()
    msg = "환영합니다. 회원가입에 성공했습니다 :)"
    return { 'msg':  msg, 'status' : 200}
  
  except Exception as e :
      return {'error': str(e)}
  
@app.route('/signout/<userId>', methods=['DELETE'])
def signout(userId:int) :
  
  con = getCon()
  cursor = con.cursor()
  sql = "UPDATE user SET status = 'inactive' WHERE userId = %s and status = 'active';"
  cursor.execute(sql, userId)
  cursor.connection.commit()

  return "성공적으로 회원탈퇴되었습니다."


@app.route('/search', methods=['GET'])
def search() :
  return '' 

if __name__ == "__main__" :
    app.run(debug=True)