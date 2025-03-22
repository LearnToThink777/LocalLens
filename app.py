from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return "Flask 서버 실행 중!"

@app.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json()
    review = data.get("review", "")
    # 여기서 리뷰 분석기 클래스 호출할 예정
    return jsonify({"result": f"리뷰 '{review}' 분석됨"})

if __name__ == "__main__":
    app.run(debug=True)
