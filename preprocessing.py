# LIBRARY
import pandas as pd
import numpy as np
import re, string
import nltk
# nltk.download('punkt')

from Sastrawi.StopWordRemover.StopWordRemoverFactory import StopWordRemoverFactory
from Sastrawi.Stemmer.StemmerFactory import StemmerFactory
from gensim.models import FastText, Phrases

# insert data
def remove_null_data(data):
    data.dropna(subset = ['username', 'komentar'], inplace=True)
    return data

def remove_duplicates(data):
    data = data.drop_duplicates(subset = ['tanggal', 'username', 'komentar'], keep = 'first').reset_index(drop = True)
    return data

def remove_transpadang_comments(data):
    data = data.drop(data.loc[data['username'] == "official_transpadang.psm"].index, inplace = False).reset_index(drop = True)
    return data

# preprocessing for classification
def remove_url(text):
    return re.sub(r"http\S+", " ", text)

def remove_hashtag(text):
    return re.sub(r'#\w+', ' ', text)

def casefolding(text):
    text = text.lower()   
    return text

def remove_username_mention(text):
    text = re.sub('@[^\s]+',' ', text)
    return text

def remove_emoji(text):
    emoji_pattern = re.compile("["
                               u"\U0001F600-\U0001F64F"  # emoticons
                               u"\U0001F680-\U0001F6FF"  # transport & map symbols
                               u"\U00002702-\U000027B0"
                               u"\U000024C2-\U0001F251"
                               u"\U0001f926-\U0001f937"
                               u"\U00010000-\U0010ffff"
                               "]+", flags=re.UNICODE)
    return emoji_pattern.sub(' ', text)

def remove_punctuation(text):
    for punctuation in string.punctuation:
        text = text.replace(punctuation, ' ')
    text = text.strip()
    return text

def text_normalize(text):
    key_norm = pd.read_csv("static/dictionary/normalisasi.csv", delimiter=";")

    text = ' '.join([key_norm[key_norm['tidak_baku'] == word]['baku'].values[0] if (key_norm['tidak_baku'] == word).any() else word for word in text.split()])
    text = str.lower(text)
    
    kata = text.split()
    i = 0
    while i < len(kata) - 1:
        if kata[i] == kata[i+1] and kata[i] == 'padang':
            kata.pop(i)
        else:
            i += 1
    text = " ".join(kata)
    return text

def remove_number(text):
    text = re.sub(r'\d+', ' ', text)
    text = re.sub(r'²', '', text)
    return text

def remove_short_word(text):
    clean_words = []
    text = text.split()
    for word in text:
        if len(word) > 2:
            clean_words.append(word)
    return ' '.join(clean_words)

def stopwords_opini(text):
    stopword_ind = StopWordRemoverFactory()
    add_stopword = pd.read_csv("static/dictionary/stopwords_opini.csv", delimiter=';')
    more_stopword = add_stopword['stopwords'].values.tolist()

    stopwords_ind = stopword_ind.get_stop_words()+more_stopword+['nan']
    stopwords_ind = [i for i in stopwords_ind if i not in ("belum", "tidak", "jangan", "ada", "kenapa", "mengapa", "begitu")]

    clean_words = []
    text = text.split()
    for word in text:
        if word not in stopwords_ind:
            clean_words.append(word)
    return ' '.join(clean_words)

def stopwords_topik(text):
    stopword_ind = StopWordRemoverFactory()
    add_stopword = pd.read_csv("static/dictionary/stopwords_topik.csv", delimiter=';')
    more_stopword = add_stopword['stopwords'].values.tolist()

    stopwords_ind = stopword_ind.get_stop_words()+more_stopword+['nan']
    stopwords_ind = [i for i in stopwords_ind]

    clean_words = []
    text = text.split()
    for word in text:
        if word not in stopwords_ind:
            clean_words.append(word)
    return ' '.join(clean_words)

def stopwords_sentimen(text):
    stopword_ind = StopWordRemoverFactory()
    add_stopword = pd.read_csv("static/dictionary/stopwords_topik.csv", delimiter=';')
    more_stopword = add_stopword['stopwords'].values.tolist()
    stopwords_ind = stopword_ind.get_stop_words()+more_stopword+['nan']
    stopwords_ind = [i for i in stopwords_ind]

    clean_words = []
    text = text.split()
    for word in text:
        if word not in stopwords_ind:
            clean_words.append(word)
    return ' '.join(clean_words)

def stemming(text):
    stemmer_factory = StemmerFactory()
    ina_stemmer = stemmer_factory.create_stemmer()
    return ina_stemmer.stem(text)
    
def tokenizing(text):
    return nltk.word_tokenize(text.lower())

def word_vectorize(text):
    wv_model = FastText.load("static/dictionary/fasttext/fasttext_model_7.fasttext")

    vector=[]
    for sent in (text):
        sent_vec=np.zeros(100)
        count = 0
        for word in sent: 
            if word in wv_model.wv.index_to_key:
                vec = wv_model.wv[word]
                sent_vec += vec 
                count += 1
        if count != 0:
            sent_vec /= count #normalize
        vector.append(sent_vec)
    return vector

# ====== function untuk df ==========
def apply_remove_url(df, column_name):
    df.loc[:, column_name] = df[column_name].apply(remove_url)
    return df

def apply_remove_hashtag(df, column_name):
    df.loc[:, column_name] = df[column_name].apply(remove_hashtag)
    return df

def apply_casefolding(df, column_name):
    df.loc[:, column_name] = df[column_name].apply(casefolding)
    return df

def apply_remove_emoji(df, column_name):
    df.loc[:, column_name] = df[column_name].apply(remove_emoji)
    return df

def apply_remove_username(df, column_name):
    df.loc[:, column_name] = df[column_name].apply(remove_username_mention)
    return df

def apply_remove_punctuation(df, column_name):
    df.loc[:, column_name] = df[column_name].apply(remove_punctuation)
    return df

def apply_normalize(df, column_name):
    df.loc[:, column_name] = df[column_name].apply(text_normalize)
    return df

def apply_remove_number(df, column_name):
    df.loc[:, column_name] = df[column_name].apply(remove_number)
    return df

def apply_short_word(df, column_name):
    df.loc[:, column_name] = df[column_name].apply(remove_short_word)
    return df

def apply_stopwords(df, column_name, classification):
    if (classification == "opini"):
        df.loc[:, column_name] = df[column_name].apply(stopwords_opini)
        return df
    elif (classification == "sentimen"):
        df.loc[:, column_name] = df[column_name].apply(stopwords_sentimen)
        return df
    elif (classification == "topik"):
        df.loc[:, column_name] = df[column_name].apply(stopwords_topik)
        return df

def apply_stemming(df, column_name):
    df.loc[:, column_name] = df[column_name].apply(stemming)
    return df
    
def apply_tokenizing(df, column_name):
    df.loc[:, column_name] = df[column_name].apply(tokenizing)
    return df

def apply_bigram_trigram(df, column_name):
    bigram = Phrases(df[column_name], min_count=5, threshold=30)
    trigram = Phrases(bigram[df[column_name]])

    df.loc[:, column_name] = df[column_name].apply(lambda x: bigram.__getitem__(x))
    df.loc[:, column_name] = df[column_name].apply(lambda x: trigram.__getitem__(x))
    return df

# ------------------

def alokasi_topik(df, mgp, threshold, topic_dict):
    for i in range(len(df)):
        prob = mgp.choose_best_label(df['komentar'][i])
        if prob[1] >= threshold:
            df.loc[i, 'topik'] = topic_dict[prob[0]]
        else:
            df.loc[i, 'topik'] = 0
    return df