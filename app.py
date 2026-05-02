from flask import Flask, render_template, request, redirect, session, send_from_directory
import mysql.connector
import pickle
import numpy as np
import os
from utils.email_utils import send_email
from config import Config
from utils.pdf_utils import generate_pdf

app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = "supersecret123"


# ---------------- DB ----------------
def get_db():
    return mysql.connector.connect(
        host=app.config['MYSQL_HOST'],
        user=app.config['MYSQL_USER'],
        password=app.config['MYSQL_PASSWORD'],
        database=app.config['MYSQL_DB']
    )


# ---------------- MODEL ----------------
model = pickle.load(open('model.pkl', 'rb'))


# ---------------- IMAGE MAP ----------------
def get_image(crop):
    crop = str(crop).lower().strip()

    image_map = {
        "rice": "static/crops/rice.jpg",
        "wheat": "static/crops/wheat.jpg",
        "maize": "static/crops/maize.jpg",
        "chickpea": "static/crops/chickpea.jpg",
        "kidneybeans": "static/crops/kidneybeans.jpg",
        "pigeonpeas": "static/crops/pigeonpeas.jpg",
        "mothbeans": "static/crops/mothbeans.jpg",
        "mungbean": "static/crops/mungbean.jpg",
        "blackgram": "static/crops/blackgram.jpg",
        "lentil": "static/crops/lentil.jpg",
        "mango": "static/crops/mango.jpg",
        "apple": "static/crops/apple.jpg",
        "grapes": "static/crops/grapes.jpg",
        "watermelon": "static/crops/watermelon.jpg",
        "muskmelon": "static/crops/muskmelon.jpg",
        "pomegranate": "static/crops/pomegranate.jpg",
        "coconut": "static/crops/coconut.jpg",
        "cotton": "static/crops/cotton.jpg",
        "jute": "static/crops/jute.jpg",
        "coffee": "static/crops/coffee.jpg",
        "papaya": "static/crops/papaya.jpg",
        "banana": "static/crops/banana.jpg",
        "orange": "static/crops/orange.jpg"
    }

    return image_map.get(crop, "static/crops/default.jpg")


# ---------------- HOME ----------------
@app.route('/')
def index():
    return redirect('/dashboard')


# ---------------- LOGIN ----------------
@app.route('/login', methods=['POST'])
def login():
    user = request.form['username']
    pwd = request.form['password']

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (user, pwd))
    result = cur.fetchone()
    conn.close()

    if result:
        session['user'] = user
        return redirect('/dashboard')
    else:
        return redirect('/dashboard?msg=Invalid Login')


# ---------------- REGISTER ----------------
@app.route('/register', methods=['POST'])
def register():
    user = request.form['username']
    pwd = request.form['password']

    conn = get_db()
    cur = conn.cursor()
    cur.execute("INSERT INTO users(username,password) VALUES(%s,%s)", (user, pwd))
    conn.commit()
    conn.close()

    return redirect('/dashboard?msg=Registered Successfully')


# ---------------- DASHBOARD ----------------
@app.route('/dashboard')
def dashboard():
    msg = request.args.get('msg')

    if 'user' not in session:
        return render_template("dashboard.html", data=[], msg=msg)

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    cur.execute("SELECT * FROM predictions WHERE user=%s ORDER BY id DESC",
                (session['user'],))
    data = cur.fetchall()
    conn.close()

    for row in data:
        row['img'] = get_image(row.get('crop', ''))

    crop = request.args.get('crop')
    img = request.args.get('img')
    pdf_file = request.args.get('pdf')

    top3 = []
    if crop:
        crops_list = list(set([
            "rice","wheat","maize","chickpea","kidneybeans","pigeonpeas",
            "mothbeans","mungbean","blackgram","lentil","mango","apple",
            "grapes","watermelon","muskmelon","pomegranate","coconut",
            "cotton","jute","coffee","papaya","banana","orange"
        ]))

        if crop in crops_list:
            crops_list.remove(crop)

        top3 = [crop] + list(np.random.choice(crops_list, 2, replace=False))

    top3_data = [{"name": c, "img": get_image(c)} for c in top3]

    return render_template(
        'dashboard.html',
        data=data,
        crop=crop,
        img=img,
        pdf_file=pdf_file,
        top3=top3_data,
        msg=msg
    )


# ---------------- PREDICT ----------------
@app.route('/predict', methods=['POST'])
def predict():
    if 'user' not in session:
        return redirect('/dashboard?msg=Login First')

    try:
        n = float(request.form['n'])
        p = float(request.form['p'])
        k = float(request.form['k'])
        temp = float(request.form['temp'])
        humidity = float(request.form['humidity'])
        ph = float(request.form['ph'])
        rainfall = float(request.form['rainfall'])

        values = np.array([[n, p, k, temp, humidity, ph, rainfall]])
        crop = str(model.predict(values)[0]).lower().strip()

        img = get_image(crop)

        crops_list = [
            "rice","wheat","maize","chickpea","kidneybeans","pigeonpeas",
            "mothbeans","mungbean","blackgram","lentil","mango","apple",
            "grapes","watermelon","muskmelon","pomegranate","coconut",
            "cotton","jute","coffee","papaya","banana","orange"
        ]

        if crop in crops_list:
            crops_list.remove(crop)

        top3 = [crop] + list(np.random.choice(crops_list, 2, replace=False))

        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO predictions(user,crop,n,p,k,temp,humidity,ph,rainfall)
            VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)
        """, (session['user'], crop, n, p, k, temp, humidity, ph, rainfall))
        conn.commit()
        conn.close()

        # PDF
        pdf_file = generate_pdf(
            session['user'],
            crop,
            os.path.abspath(img),
            n, p, k, temp, humidity, ph, rainfall,
            top3
        )

        # ✅ SAFE EMAIL (FIXED)
        try:
            if app.config.get("EMAIL_USER") and app.config.get("EMAIL_PASS"):
                send_email(session['user'], crop, top3, pdf_file)
                msg = "Prediction successful & Email sent"
            else:
                msg = "Prediction successful (Email not configured)"
        except Exception as e:
            print("Email Error:", e)
            msg = "Prediction successful (Email failed)"

        return redirect(f"/dashboard?crop={crop}&img={img}&pdf={pdf_file}&msg={msg}")

    except Exception as e:
        return f"Prediction Failed: {e}"


# ---------------- DOWNLOAD ----------------
@app.route('/download/<path:filename>')
def download(filename):
    return send_from_directory(
        directory=os.path.dirname(filename),
        path=os.path.basename(filename),
        as_attachment=True
    )


# ---------------- UPDATE ----------------
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    if 'user' not in session:
        return redirect('/dashboard')

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    if request.method == 'GET':
        cur.execute("SELECT * FROM predictions WHERE id=%s AND user=%s",
                    (id, session['user']))
        data = cur.fetchone()
        conn.close()
        return render_template("edit.html", data=data)

    n = float(request.form['n'])
    p = float(request.form['p'])
    k = float(request.form['k'])
    temp = float(request.form['temp'])
    humidity = float(request.form['humidity'])
    ph = float(request.form['ph'])
    rainfall = float(request.form['rainfall'])

    values = np.array([[n, p, k, temp, humidity, ph, rainfall]])
    crop = str(model.predict(values)[0]).lower().strip()

    cur.execute("""
        UPDATE predictions
        SET n=%s, p=%s, k=%s, temp=%s, humidity=%s, ph=%s, rainfall=%s, crop=%s
        WHERE id=%s AND user=%s
    """, (n, p, k, temp, humidity, ph, rainfall, crop, id, session['user']))

    conn.commit()
    conn.close()

    return redirect('/dashboard')


# ---------------- DELETE ----------------
@app.route('/delete/<int:id>')
def delete(id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM predictions WHERE id=%s AND user=%s",
                (id, session.get('user')))
    conn.commit()
    conn.close()

    return redirect('/dashboard')


# ---------------- SEND EMAIL AGAIN ----------------
@app.route('/send/<int:id>')
def send_again(id):
    if 'user' not in session:
        return redirect('/dashboard?msg=Login First')

    conn = get_db()
    cur = conn.cursor(dictionary=True)

    # Fetch record
    cur.execute("SELECT * FROM predictions WHERE id=%s AND user=%s",
                (id, session['user']))
    row = cur.fetchone()
    conn.close()

    if not row:
        return redirect('/dashboard?msg=Record Not Found')

    crop = row['crop']
    img = get_image(crop)

    # Top 3 again
    crops_list = [
        "rice","wheat","maize","chickpea","kidneybeans","pigeonpeas",
        "mothbeans","mungbean","blackgram","lentil","mango","apple",
        "grapes","watermelon","muskmelon","pomegranate","coconut",
        "cotton","jute","coffee","papaya","banana","orange"
    ]

    if crop in crops_list:
        crops_list.remove(crop)

    top3 = [crop] + list(np.random.choice(crops_list, 2, replace=False))

    # Generate PDF again
    pdf_file = generate_pdf(
        session['user'],
        crop,
        os.path.abspath(img),
        row['n'], row['p'], row['k'],
        row['temp'], row['humidity'],
        row['ph'], row['rainfall'],
        top3
    )

    # Send Email
    try:
        if app.config.get("EMAIL_USER") and app.config.get("EMAIL_PASS"):
            send_email(session['user'], crop, top3, pdf_file)
            msg = "Email Sent Successfully"
        else:
            msg = "Email Not Configured"
    except Exception as e:
        print("Email Error:", e)
        msg = "Email Failed"

    return redirect(f"/dashboard?msg={msg}")

# ---------------- LOGOUT ----------------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/dashboard')


if __name__ == "__main__":
    app.run(debug=True)