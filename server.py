from flask import Flask, jsonify, request
import utils.utils as utils
import pymysql
import json, datetime
from flask_cors import CORS
import jwt

SECRET_KEY='secret_key'

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

@app.route('/boardlist/<searchWordKey>/<searchWord>', methods=['GET'])
def search(searchWordKey:str, searchWord:str) :

  con = getCon()
  cursor = con.cursor()
  cursor.execute("select b.boardId, b.title, u.userId, u.ID, b.content, b.location, date_format(b.createAt, '%Y-%m-%d') AS createAt FROM board as b LEFT OUTER JOIN user as u on u.userId = b.userId WHERE {} LIKE '%{}%' ORDER BY b.createAt DESC;".format(searchWordKey, searchWord) )
  data = cursor.fetchall()

  return json.dumps(data, default=json_default)

# boardContent.js 게시물 상세정보
@app.route('/board/detail/<boardId>/<token>', methods=['GET'])
def getboardId(boardId : int, token : str):

  payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
  print(payload)

  con = getCon()
  cursor = con.cursor()

  # cursor.execute("SELECT status FROM board WHERE boardId = {};".format(boardId)) 
  cursor.execute("SELECT b.status , r.rent FROM board as b, rent as r WHERE b.boardId ={};".format(boardId)) 
  
  dataStatus = cursor.fetchall()
  # boardStatus - unactive
  print("========================================================")
  print(dataStatus)
  if dataStatus[0]["status"] == 'unactive' :
    return "DELETE"
  
  # boardStatus - active
  else :
    cursor.execute("SELECT b.boardId, b.title, u.userId, u.ID, b.content, b.location, date_format(b.createAt, '%Y-%m-%d') AS createAt, r.rent, r.userId AS rentusreId  FROM board as b LEFT JOIN user as u on u.userId = b.userId LEFT JOIN rent as r on r.boardId = b.boardId WHERE b.boardId = {} ORDER BY b.createAt DESC;".format(boardId))
    
    data = cursor.fetchone()
    cursor.close()
      
    # 반환할 때 json형식으로 반환
    return { "boardData" : data,
            "userData" : payload}

#Mypage.js 대여목록조회
@app.route('/mypage/<token>', methods=['GET'])
def getRentList(token : str):
  print("getRentList",token)

  payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])

  con = getCon()
  cursor = con.cursor()
  cursor.execute("SELECT b.boardId, b.title, u.userId, u.ID, b.location, date_format(b.createAt, '%Y-%m-%d') AS createAt, r.rentId, r.rent ,date_format(r.rentAt, '%Y-%m-%d') AS rentAt, date_format(r.returnAt, '%Y-%m-%d') AS returnAt FROM board as b LEFT JOIN user as u on u.userId = b.userId LEFT JOIN rent as r on r.boardId = b.boardId WHERE r.userId={} and rent ='inactive' ORDER BY b.createAt DESC;".format(payload['userId']))
    
  data = cursor.fetchall()
  cursor.close()
      
  # 반환할 때 json형식으로 반환
  return json.dumps(data, default=json_default)

#Mypage.js 사용자 ID => name
@app.route('/mypage/chageName/<token>', methods=['GET'])
def chageIdToName(token : str):
  payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
  con = getCon()
  cursor = con.cursor()
  cursor.execute("SELECT name FROM user WHERE userId = {};".format(payload['userId']))
  data = cursor.fetchone()
  cursor.close()
  
  return data
  
# boardViewContent.js 게시물 수정
@app.route('/boardEdit/<boardId>', methods=['PUT'])
def boardEdit(boardId : int) :
  boardData = request.get_json()
  print(boardData)
  con = getCon()
  cursor = con.cursor()

  cursor.execute("UPDATE board SET title = '{}',content = '{}' WHERE boardId = {};".format(boardData['title'], boardData['content'], boardId))
  cursor.connection.commit()

  cursor.execute("SELECT b.boardId, b.title, u.userId, u.ID, b.content, b.location, date_format(b.createAt, '%Y-%m-%d') AS createAt, r.rentId, r.rent  FROM board as b LEFT JOIN user as u on u.userId = b.userId LEFT JOIN rent as r on r.boardId = b.boardId WHERE b.boardId = {} ORDER BY b.createAt DESC;".format(boardId))
    
  data = cursor.fetchall()
  cursor.close()
      
    # 반환할 때 json형식으로 반환
  return json.dumps(data, default=json_default)
  # return '성공적으로 수정되었습니다:)'

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
  print("boardData['userId']1 : ", boardData['userId'])


  con = getCon()
  cursor = con.cursor()
  sql = "INSERT INTO board (userId, title, content, location) VALUES (%s, %s, %s, %s);"
  cursor.execute(sql, (boardData['userId'], boardData['title'], boardData['content'], boardData['location']))
  cursor.connection.commit()

  sql = "SELECT boardId FROM board ORDER BY boardId DESC LIMIT 1;"
  cursor.execute(sql)
  boardId = cursor.fetchone()
  
  sql = "INSERT INTO rent (boardId) values (%s);"
  cursor.execute(sql, (boardId['boardId']))
  cursor.connection.commit()

  if boardData['userId'] == '1' :
    print("boardData['userId']2 : ", boardData['userId'])
    sql = "UPDATE rent SET rent='disable' WHERE boardId=%s;"
    cursor.execute(sql, (boardId['boardId']))
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
  print(user)

  try :
    if user['status'] == 'active':
      if ID == user['ID'] and  utils.verfifyPwd(password, user['password']):
        payload = {'userId' : user['userId'],
                   'ID' : user['ID']}
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        print(token)
        return {'token' : token}
      else :
        return 'WRONG'
    else :
      return 'SINGOUT'
  except :
    return "NON"
  
  
# userid체크
@app.route('/checkid/<token>', methods=['GET'])
def checkid(token: str) :

  payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
  print(payload)

  con = getCon()
  cursor = con.cursor()
  sql = "SELECT ID, userId FROM user WHERE userId = %s"
  cursor.execute(sql, payload['userId'])
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
  
@app.route('/signout/<token>', methods=['DELETE'])
def signout(token:str) :

  payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
  print(payload)
  
  con = getCon()
  cursor = con.cursor()
  sql = "UPDATE user SET status = 'inactive' WHERE userId = %s and status = 'active';"
  cursor.execute(sql, payload['userId'])
  cursor.connection.commit()

  return "성공적으로 회원탈퇴되었습니다."

@app.route('/commentWrite', methods=['POST'])
def commentwrite() :
  commentData = request.get_json()
  payload = jwt.decode(commentData['token'], SECRET_KEY, algorithms=['HS256'])
  print(payload)

  con = getCon()
  cursor = con.cursor()
  cursor.execute("INSERT INTO comment(userId, boardId, content) VALUES (%s, %s, %s)", 
                  (payload['userId'], commentData['boardId'], commentData['content']))
  cursor.connection.commit()
  return '댓글이 정상적으로 입력되었습니다.'

@app.route('/boardlist/<boardId>/commentlist', methods=['GET'])
def commentlist(boardId:int):
  con = getCon()
  cursur = con.cursor()
  cursur.execute("SELECT c.commentId, c.userId, u.ID, c.content, date_format(c.createAt, '%Y-%m-%d') AS createAt FROM comment as c LEFT OUTER JOIN user as u on u.userId=c.userId WHERE c.boardId = {} AND c.status = 'active' ORDER BY c.createAt DESC;".format(boardId))
  commentData = cursur.fetchall()
  # print("commentData: ", commentData)

  return json.dumps(commentData, default=json_default)

@app.route('/commentdelete/<commentId>', methods=['DELETE'])
def commentdelete(commentId:int) :
  print(commentId)

  con = getCon()
  cursur = con.cursor()
  cursur.execute("UPDATE comment SET status = 'inactive' WHERE commentId = {};".format(commentId))
  cursur.connection.commit()

  return "삭제완료"

@app.route('/checkpassword/<token>', methods=['POST'])
def checkpassword(token: str) :
  
  payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
  print("checkpassword payload", payload)

  password = request.get_json()
  
  con = getCon()
  cursor = con.cursor()
  sql = "SELECT password FROM user WHERE userId=%s;"
  cursor.execute(sql, payload['userId'])
  data = cursor.fetchone()
  print(data['password'], type(data['password']))

  

  print(utils.verfifyPwd(password['constpassword'], data['password']))
  
  if utils.verfifyPwd(password['constpassword'], data['password']) :
    return "CORRECT"
  else :
    return "WRONG"

@app.route('/changepassword/<token>', methods=['PUT'])
def changepassword(token:str):
  data = request.get_json()

  payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
  print("payload", payload)
  print(data['newPassword'])

  hash_newpassword = utils.hash_password(str(data['newPassword']))
  print(hash_newpassword)

  con = getCon()
  cursor = con.cursor()
  sql = "UPDATE user SET password=%s WHERE userId=%s;"
  cursor.execute(sql, (hash_newpassword, payload['userId']))
  cursor.connection.commit()

  return "SUCCESS"

@app.route('/boardrent/<userId>', methods=['PUT'])
def boardrent(userId:int) :
  data = request.get_json()
  returnAt = data['returnDate'][:10].replace('-','')
  # returndate = datetime.datetime.strptime(returnAt, '%Y-%m-%d')
  
  print(returnAt)
  # print("UPDATE rent SET userId={},rentAt=now(),returnAt=date_format({}, '%y-%m-%d'),rent='inactive' WHERE boardId={};".format(userId, returnAt, data['boardId']))

  con = getCon()
  cursor = con.cursor()
  cursor.execute("UPDATE rent SET userId={},rentAt=now(),returnAt=date_format({}, '%y-%m-%d'),rent='inactive' WHERE boardId={};".format(userId, returnAt, data['boardId']))
  cursor.connection.commit()

  return 'SUCCESS'

@app.route('/boardreturn/<boardId>', methods=['DELETE'])
def boardreturn(boardId:int) :

  con = getCon()
  cursor = con.cursor()
  sql = "UPDATE rent SET rent='active', userId=null, rentAt=null, returnAt=null WHERE boardId=%s;"
  cursor.execute(sql, (boardId))
  cursor.connection.commit()

  return "SUCCESS"

if __name__ == "__main__" :
    app.run(debug=True)