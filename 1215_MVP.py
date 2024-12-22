from branca.element import Figure
from datetime import datetime
import folium
import googlemaps
from googleapiclient.discovery import build
from io import BytesIO
import json
import numpy as np
from openai import OpenAI
import os
from PIL import Image
import requests
import streamlit as st
from streamlit_folium import st_folium

from rekishi_saki_module import *

# ------------------------------
# APIキーなどの設定
# ------------------------------
# with open('Google_custom_search_api_key.txt', 'r', encoding='UTF-8') as file:
#     API_KEY = file.read()
API_KEY = st.secrets["Google_custom_search"]["api_key"]
# API_KEY = "xxx(あなたのAPIキー)xxx"

# with open('Google_search_ID.txt', 'r', encoding='UTF-8') as file:
#     SEARCH_ENGINE_ID = file.read()
SEARCH_ENGINE_ID = st.secrets["Google_search_ID"]["ID"]
# SEARCH_ENGINE_ID = "xxx(あなたのAPIキー)xxx"

# with open('Google_map_api_key.txt', 'r', encoding='UTF-8') as file:
#     GOOGLE_API_KEY = file.read()
GOOGLE_API_KEY = st.secrets["Google_map_api"]["api_key"]
# GOOGLE_API_KEY = "xxx(あなたのAPIキー)xxx"
gmaps = googlemaps.Client(key=GOOGLE_API_KEY) # Google Mapsクライアント

# with open('Rakuten_api_key.txt', 'r', encoding='UTF-8') as file:
#     RAKUTEN_API_KEY = file.read()
RAKUTEN_API_KEY = st.secrets["Rakuten_api"]["api_key"]
# RAKUTEN_API_KEY = "xxx(あなたのAPIキー)xxx"

# with open('OpenAI_key.txt', 'r', encoding='UTF-8') as file:
#     api_key = file.read()
api_key = st.secrets["openai"]["api_key"]
client = OpenAI(api_key=api_key)
# os.environ["OPENAI_API_KEY"] = "xxx(あなたのAPIキー)xxx"
# client = OpenAI() # OpenAIクライアント

# ------------------------------
# メイン処理
# ------------------------------
st.title('聖地・関連観光スポット検索アプリ（歴史咲の解説付き）')
st.image("rekishi_saki.webp", caption="歴史咲", use_container_width=True)
st.sidebar.write('※このアプリケーションは利用規約を遵守したうえで音声合成にVOICEVOXを使用しています。\
    音声解説にはVOICEVOXをインストールのうえ、アプリ起動時にVOICEVOXも立ち上げておく必要があります。')
name = st.sidebar.text_input("人物名、作品名を入力してください（例：織田信長）", "")

# 変数がリセットされないようst.session_stateで対策
if 'commentary_output' not in st.session_state:
    st.session_state.commentary_output = '解説を聞くには、まず人物か作品名を入力してね！'
if 'seiti_explain' not in st.session_state:
    st.session_state.seiti_explain = ''
if 'seiti_list' not in st.session_state:
    st.session_state.seiti_list = ''

if st.sidebar.button("検索"):
    if name != '':
        # 1回目: 聖地と観光地の説明文を取得
        prompt_list = (
            f"以下の人物または作品名「{name}」に関連する聖地（関連の深い土地や場所）を箇条書きで3つ示し、"
            "それぞれ簡潔な説明をつけてください。その後、それら聖地の近くにある訪れるべき観光地やスポットも、"
            "聖地ごとに箇条書きで列挙してください。"
            "記事形式は不要で、単純なリストでの出力としてください。"
        )
        st.session_state.seiti_explain = run_gpt(client, prompt_list)

        # 2回目: 聖地のリストを取得
        prompt_test = (
            "以下は、ある人物または作品に関連する聖地と観光スポットのリストです。\n"
            "```\n" + st.session_state.seiti_explain + "\n```\n"
            "ここから土地に関する説明やヘッドラインはすべて省いて、"
            "訪れるべき観光地やスポットの名称だけを、単純なリストで出力してください。"
        )
        st.session_state.seiti_list = run_gpt(client, prompt_test)

        # 3回目: "歴史咲"による解説
        prompt_commentary = (
            "以下は、ある人物または作品に関連する聖地と観光スポットのリストです。\n"
            "```\n" + st.session_state.seiti_explain + "\n```\n"
            "あなたは17歳の女子高生「歴史咲（れきし さき）」として、このリストに挙げられた聖地や観光スポットを、"
            "好奇心旺盛で情熱的なおしゃべり口調で、歴史好きな友達に紹介するように解説してください。\n"
            "【キャラクター設定】\n"
            "名前: 歴史咲（れきし さき）\n"
            "年齢: 17歳\n"
            "性格: 好奇心旺盛で情熱的。話し始めると止まらないおしゃべりタイプ。相手が歴史に興味を持つと目を輝かせて丁寧に解説する。"
            "自称「日本史大使」だが、世界史にも詳しい。\n"
            "外見: 黒髪セミロング、赤いリボン、制服に着物風カーディガン、リュックに武将マスコットたくさん。\n"
            "持ち物: 歴史図鑑、城巡りパンフ、城スタンプ帳。\n"
            "趣味: 城巡り、歴史グッズ収集、読書(戦国や幕末)\n"
            "好きな歴史人物: 織田信長、坂本龍馬\n"
            "口癖: 「え、これって歴史的に考えるとね～！」「やっぱり信長公はスゴイよね～！」「歴史はロマンだよ！」\n"
            "特技: 歴史クイズ優勝、友達を歴史好きにさせる\n"
            "小ネタ: 歴史検定マスター、将来は歴史学者か歴史系YouTuber\n\n"
            "これらの設定を踏まえて、上記リストに対する解説文を、キャラクターになりきって出力してください。"
            ""
        )
        st.session_state.commentary_output = run_gpt(client, prompt_commentary)
    else:
        st.write("人物名、作品名を入力してください。")

if st.session_state.seiti_explain:
    st.write("**聖地と周辺観光スポット一覧**")
    st.write(st.session_state.seiti_explain)

if st.session_state.commentary_output:
    st.write("**歴史咲からの解説**")
    st.write(st.session_state.commentary_output)

if st.button('再生'):
    if st.session_state.commentary_output:
        audio_bytes = read_text(st.session_state.commentary_output)
        st.audio(audio_bytes, format='audio/mp3')
    else:
        st.write("まだ解説文がありません。先に「検索」を行ってください。")

selected_land = '東京タワー'

if st.session_state.seiti_list:
    location_list = st.session_state.seiti_list.split('-') 
    location_list = [location for location in location_list if location]

    # 写真の表示
    selected_land = st.sidebar.selectbox("写真を表示する土地を選択してください", location_list)
    photo_urls = google_image_search(selected_land, API_KEY, SEARCH_ENGINE_ID, num=5)

    if len(photo_urls) > 0:
        st.write(f"{selected_land}の写真を表示します。")
        for i, url in enumerate(photo_urls, start=1):
            response = requests.get(url)
            # Content-Typeがimageを含み、HTTPステータスが200の場合のみ画像を表示
            if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
                try:
                    image = Image.open(BytesIO(response.content))
                    st.image(image, caption=f"{selected_land} {i}", use_container_width=True)
                except Exception as e:
                    st.write(f"画像を読み込めませんでした: {e}")
            else:
                st.write(f"画像として取得できないURLが含まれていました: {url}")
    else:
        st.write("指定された場所の写真は見つかりませんでした。")
    
    # 地図の表示: selected_landを利用
    st.write(f"**{selected_land}付近のホテルと地図表示**")
    hotels, destination_coords = get_nearby_hotels(client=gmaps, API_KEY=RAKUTEN_API_KEY, destination=selected_land)

    if not destination_coords:
        st.warning("目的地の緯度・経度を取得できませんでした。")
    elif not hotels:
        st.warning("近隣のホテルが見つかりませんでした。")
    else:
        hotel_names = [hotel["hotelName"] for hotel in hotels]
        selected_hotel = st.sidebar.selectbox("ホテルを選択してください", hotel_names)

        hotel_details = next(hotel for hotel in hotels if hotel["hotelName"] == selected_hotel)
        st.subheader(f"選択中のホテル: {selected_hotel}")
        st.write(f"最低料金: {hotel_details['hotelMinCharge']} 円")
        st.write(f"レビュー平均: {hotel_details['reviewAverage']}")
        st.write(f"特徴: {hotel_details['hotelSpecial']}")
        st.write(f"アクセス: {hotel_details['access']}")
        st.write(f"駐車場情報: {hotel_details['parkingInformation']}")
        st.markdown(f"[プランを確認する]({hotel_details['planListUrl']})")

        # 経路表示
        now = datetime.now()
        directions_result = gmaps.directions(
            selected_land,
            selected_hotel,
            mode="driving",
            departure_time=now
        )

        color_map = {
            'WALKING': '#0000ff',
            'DRIVING': '#ff0000',
        }

        steps = []
        for i,s in enumerate(directions_result[0]['legs'][0]['steps']):
            print(i,s['travel_mode'])
            steps.append({
                'polyline': decode_polyline(s['polyline']['points']),
                'travel_mode': s['travel_mode'],
                'duration': s['duration']['text'],
                'duration_sec': s['duration']['value']
            })

        res = directions_result[0]
        start,end = res['legs'][0]['start_location'],res['legs'][0]['end_location']
        lat,lng = (start['lat']+end['lat'])/2,(start['lng']+end['lng'])/2



        hotel_map = folium.Map(location=destination_coords, zoom_start=16)
        folium.Marker(destination_coords, tooltip=f"目的地: {selected_land}").add_to(hotel_map)
        folium.Marker([hotel_details["latitude"], hotel_details["longitude"]], 
                        tooltip=selected_hotel).add_to(hotel_map)
        

        for step in steps:
            folium.vector_layers.PolyLine(
                locations=step['polyline'], popup=f'{step["travel_mode"]} ({step["duration"]})', color=color_map[step['travel_mode']]
            ).add_to(hotel_map)
        fig = Figure(width=800, height=600)
        fig.add_child(hotel_map)

        st_folium(hotel_map, width=700, height=500)
