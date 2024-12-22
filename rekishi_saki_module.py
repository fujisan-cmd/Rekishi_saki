from googleapiclient.discovery import build
import json
import requests
import streamlit as st

def run_gpt(client, prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "user", "content": prompt},
        ],
    )
    output_content = response.choices[0].message.content.strip()
    return output_content

def read_text(text):
    # VOICEVOXエンジンのAPIエンドポイント（ローカル起動の場合の例）
    voicevox_engine_url = "http://localhost:50021"
    speaker = 0  # 話者ID (ex. 0: 四国めたん(あまあま))

    # 1. audio_queryエンドポイントで合成用クエリを作成
    query_response = requests.post(
        f"{voicevox_engine_url}/audio_query",
        params={"text": text, "speaker": speaker}
    )
    if query_response.status_code != 200:
        raise Exception("VOICEVOX audio_query API request failed")

    query_data = query_response.json()

    # 2. synthesisエンドポイントで実際に音声合成
    synthesis_response = requests.post(
        f"{voicevox_engine_url}/synthesis",
        params={"speaker": speaker},
        data=json.dumps(query_data),
        headers={"Content-Type": "application/json"}
    )
    if synthesis_response.status_code != 200:
        raise Exception("VOICEVOX synthesis API request failed")

    # synthesis_response.content にはWAV形式のバイナリデータが返ってくる
    audio_bytes = synthesis_response.content
    return audio_bytes

def google_image_search(query, api_key, cse_id, num=5):
    service = build("customsearch", "v1", developerKey=api_key)
    result = service.cse().list(q=query, cx=cse_id, searchType='image', num=num).execute()
    image_urls = []
    if 'items' in result:
        for item in result['items']:
            if 'link' in item:
                image_urls.append(item['link'])
    return image_urls

# ホテル検索関数
def get_nearby_hotels(client, API_KEY, destination):
    try:
        # Google Maps APIで緯度・経度を取得
        geocode_result = client.geocode(destination)

        # 緯度・経度を取得
        location = geocode_result[0]["geometry"]["location"]
        latitude = location["lat"]
        longitude = location["lng"]

        # 楽天トラベルAPIでホテル情報を取得
        rakuten_url = "https://app.rakuten.co.jp/services/api/Travel/SimpleHotelSearch/20170426"
        params = {
            "applicationId": API_KEY,
            "format": "json",
            "latitude": latitude,
            "longitude": longitude,
            "searchRadius": 3,  # 半径3km
            "hits": 5,          # 最大5件取得
            "datumType": 1,
            "sort": "standard",  # 標準順
        }

        response = requests.get(rakuten_url, params=params)
        rakuten_response = response.json()

        # ホテルリスト作成
        hotels = []
        for hotel in rakuten_response.get("hotels", []):
            info = hotel["hotel"][0]["hotelBasicInfo"]
            hotels.append({
                "hotelName": info["hotelName"],
                "hotelMinCharge": info.get("hotelMinCharge", "N/A"),
                "reviewAverage": info.get("reviewAverage", "N/A"),
                "hotelSpecial": info.get("hotelSpecial", ""),
                "access": info["access"],
                "parkingInformation": info.get("parkingInformation", "N/A"),
                "planListUrl": info["planListUrl"],
                "latitude": info["latitude"],
                "longitude": info["longitude"],
            })
        return hotels, (latitude, longitude)
    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
        return [], None

def decode_polyline(enc: str):
    """
        Parameters
        ----------
        enc : str
            encoded string of polyline, which can be aquired via Google Maps API.

        Returns
        -------
        result : list
            each element in `result` contains pair of latitude and longitude.
    """
    if enc == None or enc == '':
        return [[0, 0]]

    result = []
    polyline_chars = list(enc.encode())
    current_latitude = 0
    current_longitude = 0

    try:
        index = 0
        while index < len(polyline_chars):
            # calculate next latitude
            total = 0
            shifter = 0

            while True:
                next5bits = int(polyline_chars[index]) - 63
                index += 1
                total |= (next5bits & 31) << shifter
                shifter += 5
                if not(next5bits >= 32 and index < len(polyline_chars)):
                    break

            if (index >= len(polyline_chars)):
                break

            if((total & 1) == 1):
                current_latitude += ~(total >> 1)
            else:
                current_latitude += (total >> 1)

            # calculate next longitude
            total = 0
            shifter = 0
            while True:
                next5bits = int(polyline_chars[index]) - 63
                index += 1
                total |= (next5bits & 31) << shifter
                shifter += 5
                if not(next5bits >= 32 and index < len(polyline_chars)):
                    break

            if (index >= len(polyline_chars) and next >= 32):
                break

            if((total & 1) == 1):
                current_longitude += ~(total >> 1)
            else:
                current_longitude += (total >> 1)

            # add to return value
            pair = [current_latitude / 100000, current_longitude / 100000]
            result.append(pair)
    except:
        pass
    return result