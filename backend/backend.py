import random
import time
import os
import requests
import folium
from geopy.distance import geodesic
from geopy.geocoders import Nominatim

map_opened = False  # 控制地圖只開一次

def generate_user_location():
    lat = 25.0418 + random.uniform(-0.01, 0.01)
    lon = 121.5431 + random.uniform(-0.01, 0.01)
    return (lat, lon)

def generate_vehicles(user_loc, n=5):
    return [{
        "id": f"car_{i+1:03d}",
        "location": (
            user_loc[0] + random.uniform(-0.05, 0.05),
            user_loc[1] + random.uniform(-0.05, 0.05)
        )
    } for i in range(n)]

def get_eta_osrm(origin, destination):
    url = f"http://router.project-osrm.org/route/v1/driving/{origin[1]},{origin[0]};{destination[1]},{destination[0]}?overview=false"
    res = requests.get(url)
    data = res.json()
    if res.status_code == 200 and "routes" in data:
        duration = round(data["routes"][0]["duration"] / 60, 1)
        distance = round(data["routes"][0]["distance"] / 1000, 2)
        return f"{duration} 分鐘", f"{distance} 公里", distance
    return "未知", "未知", 0.0

def display_all_vehicles_map(user_loc, vehicles):
    global map_opened
    m = folium.Map(location=user_loc, zoom_start=13)
    m.get_root().header.add_child(folium.Element('<meta http-equiv="refresh" content="2">'))

    folium.Marker(user_loc, tooltip="你的位置", icon=folium.Icon(color='blue')).add_to(m)
    for v in vehicles:
        eta, dist, _ = get_eta_osrm(v['location'], user_loc)
        folium.Marker(v['location'],
                      tooltip=f"{v['id']} - ETA: {eta}, 距離: {dist}",
                      icon=folium.Icon(color='green')).add_to(m)
    m.save("map.html")
    if not map_opened:
        os.system("open map.html")
        map_opened = True

def display_map(start, end, labels=("你的位置", "目的地"), colors=("blue", "red"), auto_refresh=True):
    global map_opened
    m = folium.Map(location=start, zoom_start=13)
    if auto_refresh:
        m.get_root().header.add_child(folium.Element('<meta http-equiv="refresh" content="2">'))
    folium.Marker(start, tooltip=labels[0], icon=folium.Icon(color=colors[0])).add_to(m)
    folium.Marker(end, tooltip=labels[1], icon=folium.Icon(color=colors[1])).add_to(m)
    m.save("map.html")
    if not map_opened:
        os.system("open map.html")
        map_opened = True

def geocode_address(address):
    geolocator = Nominatim(user_agent="ride_app")
    location = geolocator.geocode(address)
    return (location.latitude, location.longitude) if location else None

def calculate_fare(distance_km):
    return 50 + distance_km * 20

def move_toward(current, target, ratio=0.08):
    return (
        current[0] + (target[0] - current[0]) * ratio,
        current[1] + (target[1] - current[1]) * ratio
    )

def simulate():
    user_location = generate_user_location()
    vehicles = generate_vehicles(user_location)

    print(f"🧍 使用者位置: {user_location}")
    print("🚗 附近車輛：")
    for i, v in enumerate(vehicles):
        eta, dist, _ = get_eta_osrm(v['location'], user_location)
        print(f"[{i}] {v['id']} - ETA: {eta}, 距離: {dist}")

    display_all_vehicles_map(user_location, vehicles)

    try:
        idx = int(input("\n👉 選擇車輛編號："))
        car = vehicles[idx]
    except:
        print("⚠️ 輸入錯誤，取消配對。")
        return

    address = input("📍 請輸入目的地（例如 台北車站）：")
    dest = geocode_address(address)
    if not dest:
        print("⚠️ 找不到此地址")
        return

    _, _, trip_distance = get_eta_osrm(user_location, dest)
    fare = calculate_fare(trip_distance)
    print(f"💰 距離：{trip_distance:.2f} 公里，預估費用：${fare:.0f} 元")

    # 車輛 → 使用者
    print(f"\n🚕 {car['id']} 正在前往你的位置...")
    while geodesic(car['location'], user_location).km > 0.3:
        eta, dist, _ = get_eta_osrm(car['location'], user_location)
        display_map(user_location, car['location'],
                    labels=("你的位置", f"{car['id']} - ETA: {eta}, 距離: {dist}"),
                    colors=("blue", "red"))
        print(f"🚗 ETA: {eta}, 距離: {dist}")
        time.sleep(0.5)
        car['location'] = move_toward(car['location'], user_location)

    print(f"\n🎉 {car['id']} 已抵達，開始出發至目的地：{address}")

    # 使用者 → 目的地（正確縮排 + 地圖顯示）
    current = user_location
    while True:
        eta, dist, dist_km = get_eta_osrm(current, dest)
        if dist_km <= 0.3:
            break
        print(f"前往目的地中… ETA: {eta}, 距離: {dist}")
        display_map(current, dest,
                    labels=(f"{car['id']} 移動中", f"{address}"),
                    colors=("red", "green"),
                    auto_refresh=True)
        time.sleep(0.5)
        current = move_toward(current, dest)

    # 抵達後地圖（不再刷新）
    display_map(
        current,
        dest,
        labels=(f"{car['id']} 抵達位置", f"抵達：{address}"),
        colors=("purple", "darkblue"),
        auto_refresh=False
    )

    print(f"\n✅ 已抵達目的地：{address}")
    print(f"💰 總費用：${fare:.0f} 元，感謝使用！")

# 執行
simulate()