# LIBRARY
from flask import Flask, redirect, url_for, render_template, request, flash, jsonify, session

# database
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, bindparam, func

# autentikasi
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

# library for data
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, timezone
import pickle
import json
import os, re

import plotly
import plotly.graph_objs as go

# IMPORT FILE
# preprocessing
import preprocessing as pr
import dashboard as ds

# APP CONFIGURATIONS
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///transpadang.db'
app.config['SECRET_KEY'] = 'supersecretkey'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)

# APP INITIALIZE
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.init_app(app)
login_manager.login_message = "Anda harus login terlebih dahulu untuk mengakses halaman ini"
login_manager.login_message_category = "warning"

# APP DATABASE MODEL
class User(UserMixin, db.Model):
    id_user = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    username = db.Column(db.VARCHAR(25), nullable=False, unique=True)
    email = db.Column(db.VARCHAR(25), nullable=False,  unique=True)
    password = db.Column(db.VARCHAR(60), nullable=False)

    def get_id(self):
        return str(self.id_user)
    
    def __repr__(self):
        return '<User %r>' % self.id_user
    
class Komentar(db.Model):
    id_komentar = db.Column(db.Integer, primary_key=True, autoincrement=True, nullable=False)
    id_user = db.Column(db.Integer, db.ForeignKey('user.id_user'), nullable=False)
    username = db.Column(db.VARCHAR(25), nullable=False)
    komentar = db.Column(db.TEXT, nullable=False)
    tanggal = db.Column(db.DateTime, nullable=False)
    opini = db.Column(db.Integer, nullable=True)
    topik = db.Column(db.Integer, nullable=True)
    sentimen = db.Column(db.Integer, nullable=True)
    __table_args__ = (db.UniqueConstraint('username', 'komentar', 'tanggal'),)

    user = db.relationship('User', backref=db.backref('komentar', lazy=True))

    def __repr__(self):
        return '<Komentar %r>' % self.id_komentar
    
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# APP SET SESSION TIMEOUT
@app.before_request
def make_session_permanent():
    session.permanent = True
    if 'last_active' in session and datetime.now(timezone.utc) - session['last_active'] > timedelta(minutes=120):
        logout_user()
        flash('Session Anda habis. Silahkan log in kembali.', "warning")
        return redirect(url_for('login'))
    session['last_active'] = datetime.now(timezone.utc)

# APP LOGIN MANAGER
@login_manager.user_loader
def load_user(id_user):
    return User.query.get(int(id_user))

# APP ROUTE 
@app.route("/", methods=["GET"])
def dashboard():
    if current_user.is_authenticated:
            username = current_user.username
            email = current_user.email
    else :
        username = ""
        email = ""

    return render_template("dashboard.html", 
                            username=username, 
                            email = email)

@app.route("/dashboard_data", methods=["POST"])
def get_data_dashboard():
    start_date = datetime.strptime((request.form.get('start_date')), "%Y/%m/%d")
    end_date = datetime.strptime((request.form.get('end_date')), "%Y/%m/%d")

    # cek isi database
    count_all_data = db.session.query(Komentar).count()
    if(count_all_data > 0):
        data_komentar = get_filtered_data_komentar(start_date, end_date)
        if not data_komentar.empty:
            c_kom, c_op, c_nop, c_pos, c_neg = ds.count_komentar_opini_nonopini(data_komentar)
            fig1 = ds.komentar_per_hari(data_komentar, start_date, end_date)
            fig2 = ds.distribusi_aspek_layanan(data_komentar)
            fig3 = ds.komposisi_topik_sentimen(data_komentar)
            fig4 = ds.sentimen_per_hari(data_komentar, start_date, end_date)
            
            # cuplikan_komentar = db.session.query(
            #     Komentar.komentar,
            #     case(
            #         (Komentar.opini == 1, 'Opini'),
            #         (Komentar.opini == 0, 'Non Opini'),
            #         else_='--'
            #     ).label('opini'),
            #     case(
            #         (Komentar.topik == 1, 'Isu Waktu Operasional'),
            #         (Komentar.topik == 2, 'Isu Halte'),
            #         (Komentar.topik == 3, 'Isu Rute'),
            #         (Komentar.topik == 4, 'Isu Pembayaran'),
            #         (Komentar.topik == 5, 'Isu Perawatan Bus'),
            #         (Komentar.topik == 6, 'Isu Transit'),
            #         (Komentar.topik == 7, 'Isu Petugas'),
            #         (Komentar.topik == 0, 'Lainnya'),
            #         else_='--'
            #     ).label('topik'),
            #     case(
            #         (Komentar.sentimen == 1, 'Positif'),
            #         (Komentar.sentimen == 0, 'Negatif'),
            #         else_='--'
            #     ).label('sentimen')
            # ).filter(
            #     func.date(Komentar.tanggal) >= start_date.date(),
            #     func.date(Komentar.tanggal) <= end_date.date(),
            #     Komentar.opini.isnot(None)  # Filter to ensure opini is not None
            # ).all()

            # # Konversi hasil query ke dalam format JSON
            # data_cuplikan_json = json.dumps([
            #     {
            #         'komentar': komentar,'opini': opini,'topik': topik,'sentimen': sentimen
            #     }
            #     for komentar, opini, topik, sentimen in cuplikan_komentar
            # ], ensure_ascii=False, indent=4)


            # data_cuplikan_komentar = pd.DataFrame([k.to_dict() for k in cuplikan_komentar])
            # data_komentar_json = data_cuplikan_komentar.to_json(orient='records')
            # print(data_komentar_json)

            # filter data yang sudah terklasifikasi saja
            data = data_komentar[data_komentar["opini"].notnull()]
            data_komentar_json = data.to_json(orient='records')
            
            return jsonify({'c_kom': int(c_kom),
                            'c_op' : int(c_op),
                            'c_nop' : int(c_nop),
                            'c_pos' : int(c_pos),
                            'c_neg' : int(c_neg),
                            'fig1' : fig1,
                            'fig2' : fig2,
                            'fig3' : fig3,
                            'fig4' : fig4,
                            'data': data_komentar_json
                            })
        
        # jika tidak ada data dalam rentang tanggal tersebut
        else:
            start_date = start_date.strftime("%d/%m/%Y")
            end_date = end_date.strftime("%d/%m/%Y")
            msg = "Data pada rentang tanggal " + str(start_date) + " - " + str(end_date) +" tidak tersedia"
            action = "warning"
            return jsonify({'msg': msg, 'action': action})
    else:
        if current_user.is_authenticated:
            msg = "Data tidak tersedia, tambahkan data!"
            action = "error"
            user = "auth"
        else:
            msg = "Data tidak tersedia, hubungi admin untuk menambahkan data!"
            action = "error"
            user = "not_auth"
        return jsonify({'msg': msg, 'action': action, 'user':user})
    
@app.route("/dashboard_komentar", methods=["POST"])
def get_data_cuplikan_dashboard():
    start_date_str = request.form.get('start_date')
    end_date_str = request.form.get('end_date')
    filter_opini = request.form.get('filter_opini', '')

    # Konversi tanggal dari string
    start_date = datetime.strptime(start_date_str, "%Y/%m/%d")
    end_date = datetime.strptime(end_date_str, "%Y/%m/%d")

    print(start_date)
    print(end_date)

    # Ambil data yang sudah terklasifikasi
    data_komentar = get_filtered_data_komentar(start_date, end_date)

    # Filter data berdasarkan parameter pencarian
    search_value = request.form.get('search[value]', '')
    if search_value:
        data_komentar = data_komentar[data_komentar.apply(lambda row: search_value.lower() in row.to_string().lower(), axis=1)]
   
    # Filter berdasarkan pilihan opini
    if filter_opini:
        if filter_opini == "Opini":
            data_komentar = data_komentar[data_komentar['opini'] == 1]
        elif filter_opini == "Non Opini":
            data_komentar = data_komentar[data_komentar['opini'] == 0]

    # Filter hanya data yang memiliki opini (not null)
    data = data_komentar[data_komentar["opini"].notnull()]

    # Get pagination parameters from the request
    start = int(request.form.get('start', 0))
    length = int(request.form.get('length', 10))

    # Hitung jumlah total records
    total_records = len(data)

    # Paginate data
    paginated_data = data.iloc[start:start + length]

    # Konversi data menjadi format JSON
    data_komentar_json = paginated_data.to_json(orient='records')
    data_json = json.loads(data_komentar_json)

    # Format data untuk dikembalikan ke DataTables
    response = {
        'draw': int(request.form.get('draw', 1)),
        'recordsTotal': total_records,
        'recordsFiltered': total_records,
        'data': data_json
    }

    return jsonify(response)

@app.route("/wordcloud_pos", methods=["POST"])
def get_wordcloud_pos():
    start_date = datetime.strptime((request.form.get('start_date')), "%Y/%m/%d")
    end_date = datetime.strptime((request.form.get('end_date')), "%Y/%m/%d")
    topik = request.form.get('topik')

    data_komentar = get_filtered_data_komentar(start_date, end_date)

    if not data_komentar.empty:
        data_wordcloud = ds.wordcloud_data(data_komentar, topik, 1)
        if not data_wordcloud.empty:
            wordcloud = ds.wordcloud(data_wordcloud)
            return jsonify({'wordcloud_pos' : wordcloud})
        else:
            return jsonify({'msg' : "Sentimen positif tidak tersedia pada rentang tanggal dan aspek layanan yang anda pilih"})
        
    else:
        start_date = start_date.strftime("%d/%m/%Y")
        end_date = end_date.strftime("%d/%m/%Y")
        msg = "Data pada rentang tanggal " + str(start_date) + " - " + str(end_date) +" tidak tersedia"
        action = "warning"
        return jsonify({'msg': msg, 'action': action})
    
@app.route("/wordcloud_neg", methods=["POST"])
def get_wordcloud_neg():
    start_date = datetime.strptime((request.form.get('start_date')), "%Y/%m/%d")
    end_date = datetime.strptime((request.form.get('end_date')), "%Y/%m/%d")
    topik = request.form.get('topik')

    data_komentar = get_filtered_data_komentar(start_date, end_date)

    if not data_komentar.empty:
        data_wordcloud = ds.wordcloud_data(data_komentar, topik, 0)
        if not data_wordcloud.empty:
            wordcloud = ds.wordcloud(data_wordcloud)
            return jsonify({'wordcloud_neg' : wordcloud})
        else:
            return jsonify({'msg' : "Sentimen negatif tidak tersedia pada rentang tanggal dan aspek layanan yang anda pilih"})
        
    else:
        start_date = start_date.strftime("%d/%m/%Y")
        end_date = end_date.strftime("%d/%m/%Y")
        msg = "Data pada rentang tanggal " + str(start_date) + " - " + str(end_date) +" tidak tersedia"
        action = "warning"
        return jsonify({'msg': msg, 'action': action})

@app.route("/wordcloud", methods=["POST"])
def get_wordcloud():
    wordcloud_pos = get_wordcloud_pos().get_json()
    wordcloud_neg = get_wordcloud_neg().get_json()

    return jsonify({**wordcloud_pos, **wordcloud_neg})

@app.route("/cuplikan-data", methods=["POST"])
def get_cuplikandata():
    start_date = datetime.strptime((request.form.get('start_date')), "%Y/%m/%d")
    end_date = datetime.strptime((request.form.get('end_date')), "%Y/%m/%d")

    data_komentar = get_filtered_data_komentar(start_date, end_date)
    if not data_komentar.empty:
        # filter data yang sudah terklasifikasi saja
        data = data_komentar[data_komentar["opini"].notnull()]
        data_komentar_json = data.to_json(orient='records')

        return jsonify({'data' : data_komentar_json})


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method=="POST":
        email= request.form.get('email')
        password = request.form.get('password')

        # hashed = bcrypt.generate_password_hash(password)
        
        user = User.query.filter_by(email=email).first()
        if user:
            if(bcrypt.check_password_hash(user.password, password)):
                login_user(user)
                next_page = request.form.get('next')
                if not next_page == "None":
                    return redirect(next_page)
                else:
                    return redirect(url_for('dashboard'))
            else:
                flash("Password salah!", "error")
        else:
            flash("Email tidak terdaftar pada sistem!", "error")
        
        return render_template("login.html", title="Analisis Sentimen Berbasis Aspek Pada Layanan Trans Padang")
    else:
        return render_template("login.html", title="Analisis Sentimen Berbasis Aspek Pada Layanan Trans Padang")

@app.route('/logout', methods=["POST"])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/beranda")
@login_required
def beranda():
    count_null_classify = Komentar.query.filter(Komentar.opini == None).count()
    
    komentar = Komentar.query.all()
    for row in komentar:
        if row.tanggal is not None:
            row.tanggal = row.tanggal.date().strftime("%d-%m-%Y")
        else:
            row.tanggal = ""

    return render_template("beranda.html", title="Analisis Sentimen Berbasis Aspek Pada Layanan Trans Padang",
                           username=current_user.username, email = current_user.email, data=komentar, count_nonclassify=count_null_classify)

@app.route("/beranda/add_komentar", methods=["POST"])
@login_required
def add_komentar():
    # check request method
    if request.method == "POST":
        if 'submit_data' in request.form:
            tanggal = request.form['tanggal']
            username = request.form['username']
            komentar = request.form['komentar']

            # check data tidak kosong
            if username and komentar:
                username = re.sub(r'@(\w+)', r'\1', username)

                # masukkan data ke db
                query = text("""INSERT OR IGNORE INTO komentar (id_user, username, komentar, tanggal) 
                                        VALUES (:id, :username, :komentar, :tanggal)""")
                values = {'id':current_user.id_user, 
                          'username': username, 
                          'komentar': komentar,
                          'tanggal' : datetime.strptime(tanggal, "%Y-%m-%d")
                         }
                        
                result = db.session.execute(query, values)
                db.session.commit()

                if result.rowcount > 0:
                    flash("Data Berhasil Ditambahkan", "success")
                else:
                    flash("Data Gagal Ditambahkan", "error")
            else:
               flash("Username dan Komentar tidak boleh kosong!", "error") 

        elif 'submit_file' in request.form:    
            # get file
            file = request.files['file_input']
            filename = secure_filename(file.filename)
            format = str(".")+filename.split(".")[-1]

            # check file format
            if file and (format == ".json"):
                new_filename = f'{filename.split(".")[0]}_{str(datetime.now().strftime("%Y-%m-%d %H%M%S.%f"))}'
                file_path = os.path.join("file_upload", new_filename+format)
                file.save(file_path)

                # open file json
                data_json = json.load(open(file_path, encoding="utf8"))  

                # check data & parse data json to dataframe
                usr = []
                kom = []
                tgl = []

                affected_rows = 0

                keys_to_check = ["ownerUsername", "text", "timestamp"]
                for i in data_json:
                    if 'latestComments' in i:
                        for j in i['latestComments']:
                            if all(key in j for key in keys_to_check):
                                usr.append(j['ownerUsername'])
                                kom.append(j['text'])
                                tgl.append(j['timestamp'])

                df = pd.DataFrame({'username': usr, 'komentar': kom, 'tanggal': tgl})

                if not df.empty:
                    # preprocessing data
                    preprocessing_df = (df.pipe(pr.remove_null_data) 
                                            .pipe(pr.remove_duplicates)
                                            .pipe(pr.remove_transpadang_comments))

                    # insert into db
                    for row in preprocessing_df.iterrows():
                        query = text("""INSERT OR IGNORE INTO komentar (id_user, username, komentar, tanggal) 
                                        VALUES (:id, :username, :komentar, :tanggal)""")
                        values = {'id':current_user.id_user, 
                                    'username': row[1]['username'], 
                                    'komentar': row[1]['komentar'], 
                                    'tanggal' : (datetime.strptime(row[1]['tanggal'], "%Y-%m-%dT%H:%M:%S.%fZ")).strftime('%Y-%m-%d %H:%M:%S')
                            }
                        
                        result = db.session.execute(query, values)
                        affected_rows += result.rowcount
                        db.session.commit()

                    if affected_rows > 0:
                        if affected_rows == len(preprocessing_df):
                            msg = "Seluruh Data Berhasil Ditambahkan"
                            action = "success"
                        else:
                            msg = "Sebagian Data Berhasil Ditambahkan"
                            action = "success"
                    else:
                        msg = "Data Gagal Ditambahkan, Data Sudah Ada"
                        action = "error"
                    
                    # remove file from folder  
                    os.remove(file_path)

                    flash(msg, action)
                else:
                    flash("Data JSON tidak lengkap", "error")
            else:
                flash("Format file yang diterima hanya .json", "error")

    return redirect(url_for('beranda'))

@app.route("/beranda/del_komentar", methods=["POST"])
@login_required
def del_komentar():
    id_komentar = request.get_json()

    query = text("DELETE FROM komentar WHERE id_komentar IN :iddata")
    query = query.bindparams(bindparam('iddata', expanding=True))

    result = db.session.execute(query, {'iddata': tuple(map(int, id_komentar))})

    if result.rowcount > 0:
        msg = "Data Berhasil Dihapus"
        action = "success"
    else:
        msg = "Data Gagal Dihapus"
        action = "error"
    db.session.commit()

    return jsonify({'action': action, 'msg': msg, 'redirect': True, 'redirectURL': url_for('beranda')}), 200

@app.route("/beranda/klasifikasi", methods=["POST"])
@login_required
def klasifikasi():
    komentar = Komentar.query.with_entities(Komentar.id_komentar, Komentar.komentar).filter_by(opini=None).limit(10).all()
    df = pd.DataFrame(komentar)

    if not df.empty:
        # === KLASIFIKASI OPINI ===
        # preprocessing 
        df_pr_opini = df.copy()
        df_pr_opini = (df_pr_opini.pipe(pr.apply_remove_url, "komentar")
                    .pipe(pr.apply_remove_hashtag, "komentar")
                    .pipe(pr.apply_casefolding, "komentar")
                    .pipe(pr.apply_remove_username, "komentar")
                    .pipe(pr.apply_remove_emoji, "komentar")
                    .pipe(pr.apply_remove_punctuation, "komentar")
                    .pipe(pr.apply_normalize, "komentar")
                    .pipe(pr.apply_remove_number, "komentar")
                    .pipe(pr.apply_short_word, "komentar")
                    .pipe(pr.apply_stopwords, "komentar", "opini")
                    .pipe(pr.apply_stemming, "komentar")
                    .pipe(pr.apply_tokenizing, "komentar"))

        # vectorize
        wv_opini = pr.word_vectorize(df_pr_opini['komentar'])

        # load_model
        model_klasifikasi_opini = pickle.load(open("static/model/klasifikasi_opini_nonopini.sav", 'rb'))
        opini_predict = model_klasifikasi_opini.predict(wv_opini)
        df['opini'] = opini_predict

        if (len(df[df["opini"] == 1]) != 0):   
            # === TOPIC MODELLING ===
            #preprocessing
            df_pr_tm = df.copy()   
            df_pr_tm = df_pr_tm[df_pr_tm['opini'] == 1]
            df_pr_tm.reset_index(drop=True, inplace=True)
            df_pr_tm = (df_pr_tm.pipe(pr.apply_remove_url, "komentar")
                            .pipe(pr.apply_remove_hashtag, "komentar")
                            .pipe(pr.apply_casefolding, "komentar")
                            .pipe(pr.apply_remove_username, "komentar")
                            .pipe(pr.apply_remove_emoji, "komentar")
                            .pipe(pr.apply_remove_punctuation, "komentar")
                            .pipe(pr.apply_normalize, "komentar")
                            .pipe(pr.apply_remove_number, "komentar")
                            .pipe(pr.apply_short_word, "komentar")
                            .pipe(pr.apply_stopwords, "komentar", "topik")
                            .pipe(pr.apply_stemming, "komentar")
                            .pipe(pr.apply_tokenizing, "komentar")
                            .pipe(pr.apply_bigram_trigram, "komentar")
                            )

            # load model topic modelling
            with open("static/model/topic_modelling.pkl", 'rb') as f:
                mgp = pickle.load(f)
            doc_count = np.array(mgp.cluster_doc_count)
            top_index = doc_count.argsort()[-7:][::-1]

            topic_dict = {}
            topic_names = [1, 2, 3, 4, 5, 6, 7]
            for i, topic_num in enumerate(top_index):
                topic_dict[topic_num]=topic_names[i]

            df_tm = pr.alokasi_topik(df=df_pr_tm[['id_komentar', 'komentar']], mgp=mgp, threshold=0.475, topic_dict=topic_dict)

            # === KLASIFIKASI SENTIMEN ===
            # # preprocessing 
            df_pr_sentimen = df.copy()   
            df_pr_sentimen = df_pr_sentimen[df_pr_sentimen['opini'] == 1]
            df_pr_sentimen = (df_pr_sentimen.pipe(pr.apply_remove_url, "komentar")
                            .pipe(pr.apply_remove_hashtag, "komentar")
                            .pipe(pr.apply_casefolding, "komentar")
                            .pipe(pr.apply_remove_username, "komentar")
                            .pipe(pr.apply_remove_emoji, "komentar")
                            .pipe(pr.apply_remove_punctuation, "komentar")
                            .pipe(pr.apply_normalize, "komentar")
                            .pipe(pr.apply_remove_number, "komentar")
                            .pipe(pr.apply_short_word, "komentar")
                            .pipe(pr.apply_stopwords, "komentar", "sentimen")
                            .pipe(pr.apply_stemming, "komentar")
                            .pipe(pr.apply_tokenizing, "komentar"))
            # vectorize
            wv_sentimen = pr.word_vectorize(df_pr_sentimen['komentar'])

            # load_model sentimen
            model_klasifikasi_sentimen = pickle.load(open("static/model/klasifikasi_sentimen.sav", 'rb'))

            sentimen_predict = model_klasifikasi_sentimen.predict(wv_sentimen)
            df_pr_sentimen['sentimen'] = sentimen_predict

            df_output = pd.merge(df, df_pr_sentimen[['id_komentar', 'sentimen']], on='id_komentar', how='left')
            df_output = pd.merge(df_output, df_tm[['id_komentar', 'topik']], on='id_komentar', how='left')

            # Mengubah Nan menjadi None
            df_output['sentimen'] = df_output['sentimen'].where(pd.notnull(df_output['sentimen']), None)
            df_output['topik'] = df_output['topik'].where(pd.notnull(df_output['topik']), None)

            for id, opini_value, topik_value, sentimen_value in zip(df_output['id_komentar'], df_output['opini'], df_output['topik'], df_output['sentimen']):
                update_op = db.session.query(Komentar).filter(Komentar.id_komentar == id).update({Komentar.opini: opini_value, Komentar.topik: topik_value, Komentar.sentimen: sentimen_value}, synchronize_session=False)
                db.session.flush()
                
                if update_op > 0:
                    msg = "Klasifikasi Sentimen Berbasis Aspek Berhasil Dilakukan"
                    action = "success"
                else:
                    msg = "Klasifikasi Sentimen Berbasis Aspek Gagal Dilakukan"
                    action = "error"
            db.session.commit()

        else:
            for id, opini_value in zip(df['id_komentar'], df['opini']):
                update_op = db.session.query(Komentar).filter(Komentar.id_komentar == id).update({Komentar.opini: opini_value}, synchronize_session=False)
                db.session.flush()
                
                if update_op > 0:
                    msg = "Klasifikasi Opini Berhasil"
                    action = "success"
                else:
                    msg = "Klasifikasi Opini Gagal"
                    action = "error"
            db.session.commit()

    else:
        msg= "Seluruh Data Komentar Telah Diklasifikasi"
        action = "warning"

    return jsonify({'action': action, 'msg': msg, 'redirect': True, 'redirectURL': url_for('beranda')}), 200
    
def get_filtered_data_komentar(start_date, end_date):
    komentar = Komentar.query.filter(
        func.date(Komentar.tanggal) >= start_date.date(),
        func.date(Komentar.tanggal) <= end_date.date()
    ).all()

    data_komentar = pd.DataFrame([k.to_dict() for k in komentar])
    return data_komentar

@app.route('/get_min_max_dates', methods=['GET'])
def get_min_max_dates():

    # Ambil tanggal min dan max dari tabel 
    min_date = db.session.query(func.min(Komentar.tanggal)).scalar()
    max_date = db.session.query(func.max(Komentar.tanggal)).scalar()

    return jsonify({
        'min_date': min_date.strftime('%Y-%m-%d'),
        'max_date': max_date.strftime('%Y-%m-%d')
    })

# CUSTOM ERROR PAGES
# invalid url
@app.errorhandler(404)
def page_not_found(e):
    return render_template("error_page/404.html"), 404

# internal server error
@app.errorhandler(500)
def internal_server_error(e):
    return render_template("error_page/500.html"), 404

if __name__ == "__main__":
    app.run(debug=True)