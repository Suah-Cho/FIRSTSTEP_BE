# SSG_PROJECT_02

### FLASK → REACT 데이터 전송

package.json

```json
"proxy": "받아올 데이터 주소"
예) "proxt" : "http://localhost:5000"
```

server.py

```python
from flask import Flask, jsonify
import pymysql

app = Flask(__name__)

# 데이터 베이스 연결
db = pymysql.connect(host="localhost", 
                     user="root", password="passwd", 
                     db="test3",
                     charset="utf8")

cursor = db.cursor()

// 날짜를 json형식으로
def json_default(value):
  if isinstance(value, datetime.date):
    return value.strftime('%Y-%m-%d')
  raise TypeError('not JSON serializable')  

// 데이터를 json으로 바꿔주는 함수
def query_db(query, args=(), one=False):
    cur = db.cursor()
    cur.execute(query, args)
    r = [dict((cur.description[i][0], value) \
               for i, value in enumerate(row)) for row in cur.fetchall()]
    cur.connection.close()
    return (r[0] if r else None) if one else r

@app.route("/members", methods=['GET', 'POST'])
def members():

    cursor.execute("select * from user;")
    data = cursor.fetchall()

    ## 반환할 때 json형식으로 반환
    return jsonify(data)

if __name__ == "__main__" :
    app.run(debug=True)
```

App.js → useEffect&axios를 이용해 데이터 받아오기

```jsx
useEffect(() => {
    axios.get('/members')
    .then(res => {
      console.log(res);
      setData(res.data);
      console.log(data[0][0]);
    }).catch(err => console.log(err));
  }, []);
```

데이터를 화면에 표기할 때 형식을 맞춰야 한다. → (ERROR : Objects are not valid as a React child (found: object with keys {}). If you meant to render a collection of children, use an array instead.)
