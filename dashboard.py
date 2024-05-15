import pandas as pd
import plotly, numpy as np, json, locale
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
import base64
from io import BytesIO
from matplotlib.colors import LinearSegmentedColormap

from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

import preprocessing as pr

# setting
locale.setlocale(locale.LC_TIME, 'id_ID.UTF-8') # mengubah pengaturan lokal ke bahasa Indonesia
# mengatur warna
# colors = ["#dc3545", "#5f3159", "#7d3254", "#213063", "#4e6797", "#809dc9", "#b3c4df"]
colors = ["#E59BE9", "#D862BC", "#8644A2", "#FF6969", "#C70039", "#50C4ED", "#387ADF", "#1B3C73"]

def count_komentar_opini_nonopini(data):
    data = data[data["opini"].notnull()]
    count_opini = (data['opini'] == 1).sum()
    count_nonopini = (data['opini'] == 0).sum()
    count_komentar = (len(data))
    count_pos = (data['sentimen'] == 1).sum()
    count_neg = (data['sentimen'] == 0).sum()

    return count_komentar, count_opini, count_nonopini, count_pos, count_neg

def komentar_per_hari(data, start, end):
    data = data[data["opini"].notnull()]
    data['tanggal'] = pd.to_datetime(data['tanggal'])
    selisih = relativedelta(end, start)

    # jika perbedaan <= 12 bulan
    if selisih.years==0 and (selisih.months >= 1 and selisih.months <=12):
        data['bulan_tahun'] = data['tanggal'].dt.strftime('%B %Y')

        df = data.groupby(['bulan_tahun', 'opini']).size().unstack().reindex(columns=[0, 1], fill_value=0)
        df.reset_index(inplace=True)

        # Ubah 'bulan_tahun' menjadi datetime untuk pengurutan
        df['bulan_tahun_dt'] = pd.to_datetime(df['bulan_tahun'], format='%B %Y')

        # Urutkan berdasarkan 'bulan_tahun_dt'
        df.sort_values('bulan_tahun_dt', inplace=True)
        df['komentar'] = df.sum(axis=1)
        df.set_index("bulan_tahun", inplace=True)

        satuan = "Bulan Posting"

    # jika selisih > 1 tahun
    elif selisih.years>0:
        data['tahun'] = data['tanggal'].dt.strftime('%Y')
        df = data.groupby(["tahun", "opini"]).size().unstack().reindex(columns=[0, 1], fill_value=0)
        df['komentar'] = df.sum(axis=1)

        satuan = "Tahun Posting"

    else:
        if(data['tanggal'].nunique()>10):
            # Buat rentang tanggal dengan 5 titik (untuk membuat 4 interval)
            date_range = pd.date_range(start=start, end=end + timedelta(days=1), periods=5)
            date_range = date_range[:-1].append(pd.Index([end]))

            # Cetak kelompok tanggal
            kelompok_tanggal = []
            for i in range(4):
                # Kurangi satu hari dari batas atas setiap interval
                upper_bound = date_range[i+1] - timedelta(days=1) if i < 3 else date_range[i+1]
                kelompok_tanggal.append(f"{date_range[i].date()} - {upper_bound.date()}")

            # Ubah kolom 'tanggal' menjadi tipe data datetime
            data['tanggal_only'] = pd.to_datetime(data['tanggal']).dt.date

            # Buat kolom baru 'kelompok_tanggal' yang berisi kelompok tanggal untuk setiap tanggal
            data['kelompok'] = data['tanggal_only'].apply(lambda x: assign_to_group(x, kelompok_tanggal))

            # Buat DataFrame untuk semua kelompok tanggal
            df_kelompok = pd.DataFrame({'kelompok': kelompok_tanggal})

            # Gabungkan DataFrame asli dengan DataFrame kelompok
            data = pd.merge(data, df_kelompok, how='right', on='kelompok')

            # Isi nilai NaN dengan 0
            data = data.fillna(0)

            # memisahkan kolom 'kelompok' menjadi dua kolom 'start_date' dan 'end_date'
            data[['start_date','end_date']] = data.kelompok.str.split(' - ',expand=True)

            # mengubah string menjadi datetime
            data['start_date'] = pd.to_datetime(data['start_date'])
            data['end_date'] = pd.to_datetime(data['end_date'])

            # ubah ke format baru 'd Mmm yyyy'
            data['start_date'] = data['start_date'].dt.strftime('%d %b %Y')
            data['end_date'] = data['end_date'].dt.strftime('%d %b %Y')

            # menggabungkan 'start_date' dan 'end_date' menjadi kolom 'kelompok' baru
            data['kelompok'] = data['start_date'] + " -<br>" + data['end_date']

            df = data.groupby(["kelompok", "opini"]).size().unstack(fill_value=0)
            df['komentar'] = df.sum(axis=1)

        else:
            data['tanggal_only'] = pd.to_datetime(data['tanggal']).dt.date
            df = data.groupby(["tanggal_only", "opini"]).size().unstack().reindex(columns=[0, 1], fill_value=0)
            # Isi nilai NaN dengan 0
            df = df.fillna(0)
            df['komentar'] = df.sum(axis=1)
        
        satuan = "Tanggal Posting"

    fig = go.Figure()
    fig.add_trace(go.Bar(x=df.index, y=(df['komentar']), name='Total Komentar', marker=dict(color="rgba(122, 156, 201, 0.8)"), text=df['komentar'], textposition="outside", textfont=dict(size=11)))
    fig.add_trace(go.Scatter(x=df.index, y=df[1], mode='lines+markers+text', name='Opini', line=dict(color='rgb(33, 48, 99)', width=2), text=df[1], textposition="middle right", textfont=dict(size=11)))
    fig.add_trace(go.Scatter(x=df.index, y=df[0], mode='lines+markers+text', name='Non Opini', line=dict(color='#dc3545', width=2), text=df[0], textposition="middle right", textfont=dict(size=11)))

    fig.update_layout(
        yaxis=dict(
            title='Jumlah Data',
            titlefont_size=14,
            tickfont_size=14,
        ),
        xaxis=dict(
            title=satuan,
            titlefont_size=14,
            tickfont_size=14,
        ),
        font=dict(
                family='Plus Jakarta Sans',
                size=14,
                color='black'
        ),
        legend=dict(
            x=1,
            y=1,
            traceorder='normal',
        ),
        autosize=True,
        height = 350,
        margin=dict(l=10, r=10, b=10, t=15)
        )

    fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return fig_json

def assign_to_group(date, date_groups):
    for i, group in enumerate(date_groups):
        start, end = [datetime.strptime(d, "%Y-%m-%d").date() for d in group.split(" - ")]
        if start <= date <= end:
            return group
    return None

def distribusi_aspek_layanan(data):
    data = data[data['opini'] == 1]

    # labelling
    label_topik = {0:"Lainnya", 1: 'Isu Waktu Operasional', 2: 'Isu Halte', 3: 'Isu Rute', 4: 'Isu Pembayaran', 5: 'Isu Perawatan Bus', 6: 'Isu Transit', 7: 'Isu Petugas'}
    # Melakukan encoding label dengan mapping
    data['label_topik'] = data['topik'].map(label_topik)

    # grouping
    df = data['label_topik'].value_counts().reset_index()
    df.sort_values('label_topik', inplace=True)

    fig = go.Figure(data=[
        go.Pie(labels=df['index'], values=df['label_topik'], marker=dict(colors=colors), textinfo='percent')
    ])

    fig.update_layout(
        font=dict(
            family="Plus Jakarta Sans",  # Ganti dengan jenis font yang Anda inginkan
            size=12
        ),
        legend=dict(
            x=1,
            y=1,
            traceorder='normal',
            font=dict(
                family='Plus Jakarta Sans',
                size=12,
                color='black'
            ),
        ),
        autosize=True,
        height = 220,
        margin=dict(l=10, r=10, b=10, t=15) 
    )

    fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return fig_json

def komposisi_topik_sentimen(data):
    # ambil data opini saja
    data = data[data['opini'] == 1]

    # labelling
    label_topik = {0:"Lainnya", 1: 'Isu Waktu Operasional', 2: 'Isu Halte', 3: 'Isu Rute', 4: 'Isu Pembayaran', 5: 'Isu Perawatan Bus', 6: 'Isu Transit', 7: 'Isu Petugas'}
    # Melakukan encoding label dengan mapping
    data['label_topik'] = data['topik'].map(label_topik)

    # Grouping data
    df = data.groupby('label_topik')['sentimen'].value_counts().unstack().reindex(columns=[0, 1], fill_value=0)
    df['opini'] = df.sum(axis=1)
    df.sort_values('opini', inplace=True)

    # Create traces
    fig = go.Figure(data=[
        go.Bar(name='Positif', y=df.index, x=df[1], orientation='h', marker=dict(color="rgb(33, 48, 99)"), text=df[1], textposition="inside", textangle=0, textfont=dict(size=11)),
        go.Bar(name='Negatif', y=df.index, x=df[0], orientation='h', marker=dict(color="#dc3545"), text=df[0], textposition="inside", textangle=0, textfont=dict(size=11))
    ])

    # Change the bar mode
    fig.update_layout(
        barmode = 'stack',
        yaxis=dict(
            title='Aspek Layanan',
            titlefont_size=14,
            tickfont_size=14,
        ),
        xaxis=dict(
            title='Jumlah Data',
            titlefont_size=14,
            tickfont_size=14,
        ),
        font=dict(
                family='Plus Jakarta Sans',
                size=14,
                color='black'
        ),
        legend=dict(
            x=1,
            y=1,
            traceorder='normal',
        ),
        autosize=True,
        height = 310,
        margin=dict(l=10, r=10, b=10, t=15)
        )

    fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return fig_json

def sentimen_per_hari(data, start, end):
    selisih = relativedelta(end, start)
    data = data[data['opini'] == 1]
    data['tanggal'] = pd.to_datetime(data['tanggal'])

    # jika perbedaan <= 12 bulan
    if selisih.years==0 and (selisih.months >= 1 and selisih.months <=12):
        data['bulan_tahun'] = data['tanggal'].dt.strftime('%B %Y')

        df = data.groupby(['bulan_tahun', 'sentimen']).size().unstack().reindex(columns=[0, 1], fill_value=0)
        df.reset_index(inplace=True)

        # Ubah 'bulan_tahun' menjadi datetime untuk pengurutan
        df['bulan_tahun_dt'] = pd.to_datetime(df['bulan_tahun'], format='%B %Y')

        # Urutkan berdasarkan 'bulan_tahun_dt'
        df.sort_values('bulan_tahun_dt', inplace=True)
        # Isi nilai NaN dengan 0
        df = df.fillna(0)
        df.set_index("bulan_tahun", inplace=True)

        satuan = "Bulan Posting"

    # jika selisih > 1 tahun
    elif selisih.years>0:
        data['tahun'] = data['tanggal'].dt.strftime('%Y')
        df = data.groupby(["tahun", "sentimen"]).size().unstack().reindex(columns=[0, 1], fill_value=0)
        # Isi nilai NaN dengan 0
        df = df.fillna(0)

        satuan = "Tahun Posting"

    else:
        if(data['tanggal'].nunique()>10):
            # Buat rentang tanggal dengan 5 titik (untuk membuat 4 interval)
            date_range = pd.date_range(start=start, end=end + timedelta(days=1), periods=5)
            date_range = date_range[:-1].append(pd.Index([end]))

            # Cetak kelompok tanggal
            kelompok_tanggal = []
            for i in range(4):
                # Kurangi satu hari dari batas atas setiap interval
                upper_bound = date_range[i+1] - timedelta(days=1) if i < 3 else date_range[i+1]
                kelompok_tanggal.append(f"{date_range[i].date()} - {upper_bound.date()}")

            # Ubah kolom 'tanggal' menjadi tipe data datetime
            data['tanggal_only'] = pd.to_datetime(data['tanggal']).dt.date

            # Buat kolom baru 'kelompok_tanggal' yang berisi kelompok tanggal untuk setiap tanggal
            data['kelompok'] = data['tanggal_only'].apply(lambda x: assign_to_group(x, kelompok_tanggal))

            # Buat DataFrame untuk semua kelompok tanggal
            df_kelompok = pd.DataFrame({'kelompok': kelompok_tanggal})

            # Gabungkan DataFrame asli dengan DataFrame kelompok
            data = pd.merge(data, df_kelompok, how='right', on='kelompok')

            # Isi nilai NaN dengan 0
            data = data.fillna(0)

            # memisahkan kolom 'kelompok' menjadi dua kolom 'start_date' dan 'end_date'
            data[['start_date','end_date']] = data.kelompok.str.split(' - ',expand=True)

            # mengubah string menjadi datetime
            data['start_date'] = pd.to_datetime(data['start_date'])
            data['end_date'] = pd.to_datetime(data['end_date'])

            # ubah ke format baru 'd Mmm yyyy'
            data['start_date'] = data['start_date'].dt.strftime('%d %b %Y')
            data['end_date'] = data['end_date'].dt.strftime('%d %b %Y')

            # menggabungkan 'start_date' dan 'end_date' menjadi kolom 'kelompok' baru
            data['kelompok'] = data['start_date'] + " -<br>" + data['end_date']

            df = data.groupby(["kelompok", "sentimen"]).size().unstack(fill_value=0)

        else:
            data['tanggal_only'] = pd.to_datetime(data['tanggal']).dt.date
            df = data.groupby(["tanggal_only", "sentimen"]).size().unstack().reindex(columns=[0, 1], fill_value=0)
            # Isi nilai NaN dengan 0
            df = df.fillna(0)
        
        satuan = "Tanggal Posting"

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df[1], mode='lines+markers+text', name='Positif', line=dict(color='rgb(33, 48, 99)', width=2), text=df[1], textposition="middle right", textfont=dict(size=11)))
    fig.add_trace(go.Scatter(x=df.index, y=df[0], mode='lines+markers+text', name='Negatif', line=dict(color='#dc3545', width=2), text=df[0], textposition="middle right", textfont=dict(size=11)))

    fig.update_layout(
        yaxis=dict(
            title='Jumlah Data',
            titlefont_size=14,
            tickfont_size=14,
        ),
        xaxis=dict(
            title=satuan,
            titlefont_size=14,
            tickfont_size=14,
        ),
        font=dict(
            family='Plus Jakarta Sans',
            size=14,
            color='black'
        ),
        legend=dict(
            x=1,
            y=1,
            traceorder='normal',
        ),
        autosize=True,
        height = 310,
        margin=dict(l=10, r=10, b=10, t=15)
        )

    fig_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return fig_json

def wordcloud_data(data, topik, sentimen):
    # filter data
    data = data[data['opini'] == 1] 
    data = data[data['sentimen'] == sentimen] 

    if (int(topik) != 99):
        df = data[data['topik'] == int(topik)]   
    else:
        df = data
    return df

def wordcloud(data):
    # mempersiapkan dataframe
    data = (data.pipe(pr.apply_remove_url, "komentar")
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
                        )
    
    text = ' '.join(data['komentar'])

    cmap = LinearSegmentedColormap.from_list("mycmap", colors)

    # membuat objek wordcloud
    wc = WordCloud(background_color='white', colormap=cmap, max_words=30)
    wc.generate(text)

    # Simpan wordcloud sebagai gambar PNG
    img = wc.to_image()
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    img_str = base64.b64encode(buffer.getvalue()).decode()

    return img_str



