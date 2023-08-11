from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import requests

from pymongo import MongoClient
import certifi

# Authentication
import jwt
import datetime
import hashlib

SECRET_KEY = 'SPARTA'


app = Flask(__name__)

ca = certifi.where()


# <pssword> 지우고 '테스트' 하세요
client = MongoClient(
    'mongodb+srv://sparta:test@cluster1.rnrelan.mongodb.net/?retryWrites=true&w=majority', tlsCAFILE=ca)
db = client.dbsparta


@app.route("/")
def home():
    token_receive = request.cookies.get("usertoken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.user.find_one({"username": payload["username"]}, {'_id': False, 'userpw': False})
        return render_template('main.html', user=user_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
        print("here")
        return redirect(url_for("login", msg="로그인 정보가 존재하지 않습니다."))


def token_sender(token):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        user_info = db.user.find_one({"username": payload["username"]}, {
                                     '_id': False, 'userpw': False})
        return user_info
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))

# 정우용
# 로그인/회원가입
# Page indexing
@app.route("/login")
def login():
    token_receive = request.cookies.get("usertoken")
    if token_receive is not None:
        return render_template("main.html", user=token_sender(token_receive))
    return render_template("login.html")


@app.route("/signup")
def signup():
    token_receive = request.cookies.get("usertoken")
    if token_receive is not None:
        return render_template("main.html", user=token_sender(token_receive))
    return render_template("signup.html")


# api
# for Authentication
@app.route("/api/register", methods=["POST"])
def api_register():
    userid = request.form.get("userid", False)
    username = request.form.get("username", False)
    userpw = request.form.get("userpw", False)

    pw_hash = hashlib.sha256(userpw.encode("utf-8")).hexdigest()
    db.user.insert_one(
        {"userid": userid, "username": username, "userpw": pw_hash})
    return jsonify({"result": "success"})


@app.route("/api/login", methods=["POST"])
def api_login():
    userid = request.form.get("userid", False)
    userpw = request.form.get("userpw", False)
    print("여기는 뭐나오니",userid,userpw)
    pw_hash = hashlib.sha256(userpw.encode('utf-8')).hexdigest()
    result = db.user.find_one({'userid': userid, 'userpw': pw_hash})

    if result is not None:
        payload = {
            'username': result['username'],
            'userid': userid,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        return jsonify({'result': 'success', 'token': token})
    else:
        return jsonify({'result': 'fail', 'msg': '아이디/비밀번호가 일치하지 않습니다.'})


# 강다온
# 미세먼지 조회
@app.route("/api/check", methods=["POST"])
def dust_post():
    city = request.form['city']
    # Dear, 다온님 
    # url은 https 가 아닌 http이어야합니다.
    # 그리고 ssl 통신관련해서 .get(url=url, verify=False)해야한다고 합니다.
    # 이유는 몰라요
    url = 'http://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty?serviceKey=NoJIHUETtC3dz34URMbrqaNvB%2BzRaDjly51j1TcQqVEvO9aSO3JWj4UcBeAKBFmRvvjOEuUL9D%2ByIp7xuWSkhw%3D%3D&returnType=json&numOfRows=100&pageNo=1&sidoName=%EC%84%9C%EC%9A%B8&ver=1.0'
    data = requests.get(url=url, verify=False)
    result = data.json()
    rows = result['response']['body']['items']
    # rows는 배열입니다
    for a in rows:
        station = a['stationName']
        dust = a['pm10Value']
        if station == city:
            return jsonify({'dust': dust}, {'city': station})


# 박나원
# 게시글 등록
@app.route("/post/create", methods=["POST"])
def post_create():
    token_receive = request.cookies.get("usertoken")
    user_info = token_sender(token_receive)
    userid = user_info['userid']
    username = user_info['username']
    userobject_id = str(db.user.find_one({'userid':userid, 'username': username})['_id'])
    doc = {
        'userid': userid,
        'username': username,
        'content': request.form.get('content',False),
        'postid': userobject_id,
        'city': request.form.get('city',False)
    }
    db.posts.insert_one(doc)
    return jsonify({"msg": "saved!"})

# 박나원
# 게시글 보기
@app.route("/post", methods=["GET"])
def post_get():
    token_receive = request.cookies.get("usertoken")
    user_info = token_sender(token_receive)
    rows =list(db.posts.find({},{'_id':False}))
    return jsonify({'rows': rows, "user_info": user_info})

# 박나원
@app.route("/api/post", methods=["GET"])
def post_apiGet():
    return render_template('post.html')

# 박나원
@app.route("/post/delete", methods=["POST"])
def post_delete():
    temp = request.form.get('postid')
    result = db.posts.delete_one({'postid':temp})
    if (result is not None):
        return jsonify({"msg": "Deleted"})
    else:
        return jsonify({"msg": "Not deleted"})

if __name__ == "__main__":
    app.run("0.0.0.0", port=5001, debug=True)
