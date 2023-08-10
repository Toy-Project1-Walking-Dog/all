from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import requests

# URL and headers to crawl
# URL = "URL to crawl"
# headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
# # Request
# data = requests.get(URL, headers=headers)

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
    token_receive = request.cookies.get("usertocken")
    try:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=["HS256"])
        user_info = db.user.find_one({"username": payload["username"]}, {
                                     '_id': False, 'userpw': False})
        return render_template('main.html', user=user_info)
    except jwt.ExpiredSignatureError:
        return redirect(url_for("login", msg="로그인 시간이 만료되었습니다."))
    except jwt.exceptions.DecodeError:
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
@app.route("/check", methods=["POST"])
def mars_post():
    city = request.form['city']
    data = requests.get('https://apis.data.go.kr/B552584/ArpltnInforInqireSvc/getCtprvnRltmMesureDnsty?serviceKey=NoJIHUETtC3dz34URMbrqaNvB%2BzRaDjly51j1TcQqVEvO9aSO3JWj4UcBeAKBFmRvvjOEuUL9D%2ByIp7xuWSkhw%3D%3D&returnType=json&numOfRows=100&pageNo=1&sidoName=%EC%84%9C%EC%9A%B8&ver=1.0')
    result = data.json()
    rows = result['response']['body']['items']

    for a in rows:
        station = a['stationName']
        dust = int(a['pm10Value'])
        status = ""
        if dust >= 0 or dust <= 15:
            status = "좋음"
        elif dust <= 35:
            status = "보통"
        elif dust <= 75:
            status = "나쁨"
        else:
            status = "매우나쁨"

        if station == city:
            return jsonify({'dust': dust}, {'city': station}, {'status': status})


# 박나원
# 게시글 등록
@app.route("/post", methods=["POST"])
def post_create():
    return jsonify({"msg": "whataever you want"})


# 박나원
# 게시글 보기
@app.route("/post", methods=["GET"])
def post_list():
    return jsonify({"msg": "whataever you want"})


# 박나원
# 게시글 삭제
@app.route("/post/delete", methods=["POST"])
def post_delete():
    return jsonify({"msg": "whataever you want"})


if __name__ == "__main__":
    app.run("0.0.0.0", port=5001, debug=True)
