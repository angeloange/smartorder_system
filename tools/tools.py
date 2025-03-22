from datetime import datetime


def convert_order_date_for_db(orders_list):
    sugar_map = {'七分糖': 'seventy', '半糖': 'half', '微糖': 'light', '無糖': 'free'}
    ice_map = {'熱飲': 'hot', '去冰': 'room', '微冰': 'light', '少冰': 'less'}

    for drink in orders_list:
        drink['sugar'] = sugar_map.get(drink['sugar'], 'full')
        drink['ice'] = ice_map.get(drink['ice'], 'iced')
    return orders_list

def get_now_time():
    now = datetime.now()
    # print(f"now: {now}")
    date = now.date()
    time = now.strftime("%H:%M:%S")
    return date, time

