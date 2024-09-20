# SISTEM ANALISIS SENTIMEN BERBASIS ASPEK PADA LAYANAN TRANS PADANG BERDASARKAN KOMENTAR PENGGUNA INSTAGRAM MENGGUNAKAN ALGORITMA RANDOM FOREST DAN GIBBS SAMPLING DIRICHLET MULTINOMIAL MIXTURE

Trans Padang merupakan layanan transportasi dalam kota Padang berbasis Bus Rapid Transit yang beroperasi di Kota Padang, Sumatera Barat, Indonesia sejak tahun 2014. Projek ini dibangun untuk membantu pihak pengelola Trans Padang dalam memahami sentimen masyarakat pengguna layanan Trans Padang di Instagram terhadap masing-masing aspek layanan Trans Padang yang dikomentari, sehingga membantu pihak pengelola untuk mengambil keputusan dalam rangka meningkatkan layanan Trans Padang di masa mendatang. Sistem analisis sentimen berbasis aspek (ABSA) yang dihasilkan dalam projek ini dibagi secara 4 tahapan umum: (1) Pemodelan klasifikasi opini dan non opini dengan `Random Forest`; (2) Pemodelan topic modelling dengan `Gibbs Sampling Dirichlet Multinomial Mixture` untuk mengidentifikasi aspek layanan yang dibahas pengguna; (3) Pemodelan klasifikasi sentimen dengan `Random Forest`; (4) Pembangunan sistem ABSA berbasis website menggunakan `framework Flask`.

## DAFTAR ISI
1. [FITUR UTAMA](#fitur-utama)
2. [INSTALASI](#instalasi)
3. [PROSES PEMBANGUNAN](#proses-pembangunan)

## FITUR UTAMA
Terdapat dua pengguna sistem ini, yakni admin dan staf, yang memiliki fungsional masing-masing:
1. Admin
   - Login ke sistem
   - Melihat, menambahkan, dan menghapus data komentar pada sistem yang tersimpan dalam database
   - Melakukan klasfikasi sentimen berbasis aspek pada data komentar yang telah tersimpan pada database
   - Melihat hasil analisis sentimen berbasis aspek pada layanan Trans Padang pada dashboard yang telah disediakan
   - Logout dari sistem
2. Staf
   - Melihat hasil analisis sentimen berbasis aspek pada layanan Trans Padang pada dashboard yang telah disediakan
   
## INSTALASI
1. Clone repositori ini:
   ```bash
   git clone https://github.com/latifatuzikra-suhairi/analisis_sentimen_layanan_trans_padang.git
2. Instal seluruh requirement project ini:
    ```bash
    pip install -r requirements.txt
3. Instalasi GSDMM melalui:
    ```bash
    pip install git+https://github.com/rwalk/gsdmm.git
4. Download FastText Model dengan:
   Akses [FastText Model](https://drive.google.com/drive/folders/1MX9bRLHPz84abkGGeWxhg_VI4wAnDFBa?usp=sharing) lalu simpan kedua filenya dalam folder:  _static/dictionary/fasttext_
5. Database ada dalam folder _instance_
6. Jalankan aplikasi dengan:
   ```bash
   python app.py
   
## PROSES PEMBANGUNAN
### AKUISISI DATA
Data dikumpulkan dengan melakukan web scraping Instagram dengan tools `Data Miner` pada tanggal 1 Januari 2022 hingga 11 Januari 2024, dengan empat sumber:
- Postingan akun @official_transpadang.psm
- Postingan dengan #transpadang
- Postingan akun @infosumbar mengenai Trans Padang
- Postingan akun @infopadang_ mengenai Trans Padang
Menghasilkan **6242** data

### MODEL KLASIFIKASI OPINI DAN NON OPINI
#### 1. TEXT PREPROCESSING
Text preprocessing yang dilakukan:
- Menggabungkan data dari 4 sumber data
- Menghapus data duplikat
- Menghapus data komentar yang diunggah oleh Instagram Trans Padang
- Memilih atribut data
- Melabeli data: opini dan non opini
- Menghapus URL
- Menghapus hashtag
- Casefolding
- Menghapus tag pengguna
- Menghapus emoji
- Menghapus tanda baca
- Normalization
- Stemming
- Menghapus stopwords
- Menghapus kata yang kurang dari 3 karakter
- Menghapus baris data yang kosong
- Label encoding: (1) Opini dan (0) Non Opini
  Sebaran data opini dan non opini:
  ![Sebaran Data Opini dan Non Opini]()
- Feature selection dengan algoritma Information Gain
- Tokenizing
  
#### 2. WORD EMBEDDING DENGAN FASTTEXT
Dilakukan untuk merepresentasikan kata ke dalam bentuk vektor agar dapat diproses komputer
```python
ft_model=FastText(data['Hasil Tokenisasi'], min_count = 2, 
                  vector_size = 100, window = 5, 
                  sg = 0, workers=4, 
                  hs=1)
ft_model.build_vocab(data['Hasil Tokenisasi'], progress_per=100)
ft_model.train(data['Hasil Tokenisasi'], total_examples= len(data['Hasil Tokenisasi']), epochs=100)
w2v_words = list(ft_model.wv.index_to_key)
```

#### 3. MODEL DEVELOPMENT
Model dibangun menggunakan algoritma `Random Forest Classifier`, dengan menggunakan metode GridSearchCV untuk mencari kombinasi parameter yang mampu menghasilkan model terbaik.
```python
# define models and parameters
model = RandomForestClassifier(random_state = 42)
n_estimators = [390, 400, 410]
max_features = ['log2']
max_depth = [20]
criterion = ['log_loss','entropy']
min_sample_split = [3]
bootstrap = [False]
scoring = ['accuracy', 'recall', 'precision', 'f1']

# define grid search
grid = dict(n_estimators=n_estimators,max_features=max_features, criterion=criterion, max_depth=max_depth,
             min_samples_split=min_sample_split, bootstrap=bootstrap)
cv = RepeatedStratifiedKFold(n_splits=10, n_repeats=3, random_state=123)
grid_search = GridSearchCV(estimator=model, param_grid=grid, n_jobs=10, cv=cv, scoring=scoring, error_score=0, refit='accuracy', verbose=2)
grid_result = grid_search.fit(X_train_sm, y_train_sm)
```
#### 4. MODEL EVALUATION
Evaluasi model klasifikasi opini dan non opini dilakukan menggunakan **Confusion Matrix*** dan **ROC AUC Score**.
- Confusion Matrix
   ```python
   #confusion matrix
   y_proba = grid_result.predict_proba(X_test_vec)
   y_pred = grid_result.predict(X_test_vec)
   
   fig, ax = plt.subplots(figsize=(14,4), dpi=100)
   cm = confusion_matrix(y_test, y_pred)
   disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Non Opini', 'Opini'])
   ax.set(title='Confusion Matrix Model Klasifikasi Opini dan Non Opini Menggunakan Random Forest Classifier')
   disp.plot(ax=ax, cmap=plt.cm.Blues)
   ```
   **Hasil**
   ![Confusion Matrix Klasifikasi Opini dan Non Opini]()
   Dari confusion matrix di atas, dapat dihitung **metrik evaluasi**:
   **1. Accuracy : 81.48%
   2. Precision : 82.48%
   3. Recall : 86.88%
   4. F1-Score : 84.63%**
   
- ROC AUC Score
   ```python
   from sklearn.metrics import roc_auc_score
   auc = roc_auc_score(y_test.ravel(), y_proba[:,1])
   print(f"ROC AUC: ", auc)
   ```
   **Hasil: 0.8813**
  

### TOPIC MODELLING
#### 1. TEXT PREPROCESSING
Text preprocessing yang dilakukan:
- Mengambil data yang bersifat opini saja
- Menghapus data yang tidak relevan dengan layanan Trans Padang
- Casefolding
- Menghapus emoji
- Menghapus hashtag
- Menghapus tag pengguna
- Menghapus tanda baca
- Normalization
- Menghapus angka
- Stemming
- Menghapus stopwords
- Menghapus kata yang kurang dari 3 karakter
- Menghapus baris data yang kosong
- Tokenizing

#### 2. MODEL DEVELOPMENT
Model dibangun menggunakan algoritma `Gibbs Sampling Dirichlet Multinomial Mixture`.
```python
mgp = MovieGroupProcess(n_iters= 30, alpha=0.71, beta=0.36, K=7)
mgp.fit(data_layanan['Hasil BigramTrigram'], n_terms)
```
#### 3. MODEL EVALUATION
Evaluasi model menggunakan metode **coherence score cv dan uci**
```python
def get_coherence_score(topics, dictionary, corpus, texts):
    cs_uci = CoherenceModel(topics=topics, dictionary=dictionary, corpus=corpus, texts=texts, coherence='c_uci')
    cs_cv = CoherenceModel(topics=topics, dictionary=dictionary, corpus=corpus, texts=texts, coherence='c_v')
    
    coherence_cv = cs_cv.get_coherence()
    coherence_uci = cs_uci.get_coherence()
    return coherence_cv, coherence_uci

coherence_cv, coherence_uci = get_coherence_score(topics, dictionary, corpus, data_layanan["Hasil BigramTrigram"])
```
**Hasil**
**1. Coherence score cv : 0.55
2. Coherence score uci :-0.43**

### MODEL KLASIFIKASI SENTIMEN
#### 1. TEXT PREPROCESSING
Text preprocessing yang dilakukan:
- Melabeli data: sentimen positif dan sentimen negatif
- Menghapus hashtag
- Casefolding
- Menghapus tag pengguna
- Menghapus emoji
- Menghapus tanda baca
- Normalization
- Menghapus angka
- Menghapus kata yang kurang dari 3 karakter
- Menghapus stopwords
- Stemming
- Menghapus baris data yang kosong
- Label encoding: (1) Positif dan (0) Negatif
  Sebaran data sentimen positif dan negatif:
  ![Sebaran Data Sentimen Positif dan Negatif]()
- Tokenizing
  
#### 2. MODEL DEVELOPMENT
Model dibangun menggunakan algoritma `Random Forest Classifier`, dengan menggunakan metode GridSearchCV untuk mencari kombinasi parameter yang mampu menghasilkan model terbaik.
```python
# define models and parameters
model = RandomForestClassifier(random_state = 123)
n_estimators = [400, 500, 600]
max_features = ['log2']
max_depth = [14,15,16]
criterion = ['log_loss', 'entropy']
min_sample_split = [2,4,5]
bootstrap = [False]
scoring = ['accuracy', 'recall', 'precision', 'f1']

# define grid search
grid = dict(n_estimators=n_estimators,max_features=max_features, criterion=criterion, max_depth=max_depth,
             min_samples_split=min_sample_split, bootstrap=bootstrap)
cv = RepeatedStratifiedKFold(n_splits=10, n_repeats=5, random_state=42)
grid_search = GridSearchCV(estimator=model, param_grid=grid, n_jobs=10, cv=cv, scoring=scoring, error_score=0, refit='accuracy', verbose=2)
grid_result = grid_search.fit(X_train_sm, y_train_sm)
```
#### 3. MODEL EVALUATION
Evaluasi model klasifikasi sentimen dilakukan menggunakan **Confusion Matrix*** dan **ROC AUC Score**.
- Confusion Matrix
   ```python
   #confusion matrix
   y_proba = grid_result.predict_proba(X_test_vec)
   y_pred = grid_result.predict(X_test_vec)
   
   fig, ax = plt.subplots(figsize=(14,4), dpi=100)
   cm = confusion_matrix(y_test, y_pred)
   disp = ConfusionMatrixDisplay(confusion_matrix=cm, display_labels=['Positif', 'Negatif'])
   ax.set(title='Confusion Matrix Model Klasifikasi Sentimen Menggunakan Random Forest Classifier')
   disp.plot(ax=ax, cmap=plt.cm.Blues)
   ```
   **Hasil**
   ![Confusion Matrix Klasifikasi Sentimen]()
   Dari confusion matrix di atas, dapat dihitung **metrik evaluasi**:
   **1. Accuracy : 84.03%
   2. Precision : 86.86%
   3. Recall : 85.61%
   4. F1-Score : 86.23%**
   
- ROC AUC Score
   ```python
   from sklearn.metrics import roc_auc_score
   auc = roc_auc_score(y_test.ravel(), y_proba[:,1])
   print(f"ROC AUC: ", auc)
   ```
   **Hasil: 0.9167**

### SISTEM ANALISIS SENTIMEN BERBASIS ASPEK PADA TRANS PADANG
Sistem dibangun menggunakan `framework Flask` agar memudahkan pengguna sistem untuk mendapatkah hasil analisis. Berikut tampilan sistem

