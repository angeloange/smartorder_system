from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import requests

load_dotenv()

#for DB
weather_dict = {
                 "sunny": ['晴', '多雲時晴', '晴時多雲'],
                 "cloudy": ['多雲', '多雲時陰', '陰', '陰時多雲', '陰時多雲有短暫雨', '多雲時陰有短暫雨', '短暫陣雨', '霾', '多雲有霾', '陰有霾', '陰有霧','霧', '多雲有霧'],
                 "rainy": ['短暫雨', '多雲時晴有短暫雨', '雨', '陣雨', '雷雨', '雷陣雨'],
                 "stormy": ['多雲有雷陣雨', '陰有雷陣雨','雷陣雨伴有冰雹', '多雲有雷陣雨伴冰雹', '陰有雷陣雨伴冰雹','雪', '多雲有雪', '陰有雪', '雨夾雪', '多雲有雨夾雪', '陰有雨夾雪']
                 }

def classify_weather(weather: str, weather_dict: list[dict]):
    for category, conditions in weather_dict.items():
        if weather in conditions:
            return category
    return 'unknown'





# 中央氣象局API設定
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")  # 請確認這是您的有效金鑰
WEATHER_API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0001-001"      #now
FORECAST_WEATHER_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-091" #tomorrow

def get_weather_data(station_ID="467490", target_station="后里"):
    try:
        params = {
            "Authorization": WEATHER_API_KEY,
            "stationId": station_ID,  # 查詢台中站 ID
            "elementName": "TEMP"  # 取得溫度與天氣狀況
        }

        response = requests.get(WEATHER_API_URL, params=params)

        if response.status_code != 200:
            print(f"HTTP錯誤: {response.status_code}")
            return {"error": "API 請求失敗"}

        data = response.json()

        if data.get("success") != "true":
            print("API回應失敗:", data.get("error", "未知錯誤"))
            return None

        locations = data["records"]["Station"]

        station_weather = None
        for station in locations:
            if station["StationName"] == target_station:
                station_weather = station
                break

        if station_weather:
            weather_elements = station_weather["WeatherElement"]
            temperature = float(weather_elements["AirTemperature"])
            weather = weather_elements["Weather"]
            timestamp = station_weather["ObsTime"]["DateTime"]

            # 回傳四個資訊 (台中站, 后里站, 天氣狀況, 溫度)
            return "台中站", target_station, weather, temperature

        else:
            print(f"未找到 {target_station} 的天氣資料！")
            return None

    except requests.RequestException as e:
        print(f"網路請求錯誤: {e}")
        return None
    except KeyError as e:
        print(f"鍵錯誤: {e} 不存在於回應中")
        return None
    except ValueError as e:
        print(f"數據解析錯誤: {e}")
        return None
    except Exception as e:
        print(f"其他錯誤: {e}")
        return None

def get_tomorrow_weather(location_name="臺中市"):
    """獲取隔日一整天的天氣與氣溫預報"""
    try:
        params = {
            "Authorization": WEATHER_API_KEY,
            "locationName": location_name,  # 嘗試使用 "臺中市"
            "elementName": "Wx,MaxT,MinT"  # 預報天氣、最高溫、最低溫
        }
        response = requests.get(FORECAST_WEATHER_URL, params=params, timeout=10)

        if response.status_code != 200:
            # logger.error(f"HTTP錯誤: {response.status_code}, 回應: {response.text}")
            return None, None, None

        data = response.json()
        # logger.debug(f"完整 API 回應: {data}")  # 記錄完整回應以供診斷

        if data.get("success") != "true":
            # logger.error(f"API回應失敗: {data.get('error', '未知錯誤')}")
            return None, None, None

        # 檢查 records 結構
        if "records" not in data:
            # logger.error("API 回應缺少 'records' 鍵")
            return None, None, None

        # 獲取地點數據
        locations = data["records"]["Locations"][0]["Location"]
        if not locations:
            # logger.warning("API 回應中無 'location' 數據")
            return None, None, None

        forecast_data = None
        available_locations = [loc.get("LocationName", "未知") for loc in locations]
        # logger.debug(f"可用地點名稱: {available_locations}")  # 記錄可用地點名稱

        for location in locations:
            if location.get("LocationName") == location_name:
                forecast_data = location
                break
        if not forecast_data:
            # logger.warning(f"未找到指定地點 '{location_name}' 的預報資料，可用地點: {available_locations}")
            return None, None, None

        # 提取隔日一整天數據
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        weather_elements = forecast_data.get("WeatherElement", [])

        # 查找隔日天氣（Wx），取第一個有效時間段
        weather_data = None
        for elem in weather_elements:
            if elem.get("ElementName") == "天氣現象":
                for time_period in elem.get("Time", []):
                    start_time = datetime.strptime(time_period.get("StartTime", ""), "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d")
                    if start_time == tomorrow:
                        weather_data = time_period["ElementValue"][0]["Weather"]
                        break
                if weather_data:
                    break

        # 查找隔日最高溫（MaxT）與最低溫（MinT），取整天範圍
        max_temp = None
        min_temp = None
        for elem in weather_elements:
            if elem.get("ElementName") == "最高溫度":
                for time_period in elem.get("Time", []):
                    start_time = datetime.strptime(time_period.get("StartTime", ""), "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d")
                    if start_time == tomorrow:
                        max_temp = float(time_period["ElementValue"][0]["MaxTemperature"])
                        break
            if elem.get("ElementName") == "最低溫度":
                for time_period in elem.get("Time", []):
                    start_time = datetime.strptime(time_period.get("StartTime", ""), "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d")
                    if start_time == tomorrow:
                        min_temp = float(time_period["ElementValue"][0]["MinTemperature"])
                        break

        if weather_data and max_temp is not None and min_temp is not None:
            # logger.info(f"后里隔日天氣: {weather_data}, 最高溫: {max_temp}°C, 最低溫: {min_temp}°C")
            return weather_data, max_temp, min_temp, tomorrow
        else:
            # logger.warning("無法提取完整的隔日預報數據")
            return None, None, None

    except requests.RequestException as e:
        # logger.error(f"網路請求錯誤: {e}")
        return None, None, None
    except (KeyError, ValueError) as e:
        # logger.error(f"數據解析錯誤: {e}")
        return None, None, None
    except Exception as e:
        # logger.error(f"其他錯誤: {e}")
        return None, None, None

if __name__ == "__main__":
    # a=get_weather_data("467490", "后里")
    # print(a)
    print(get_tomorrow_weather())
    # print(get_forecast_weather())