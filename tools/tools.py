from datetime import datetime


def convert_order_date_for_db(orders_list):
    sugar_map = {'全糖': 'full', '無糖': 'free'}
    ice_map = {'熱': 'hot', '去冰': 'room_temp'}

    for drink in orders_list:
        drink['sugar'] = sugar_map.get(drink['sugar'], 'half')
        drink['ice'] = ice_map.get(drink['ice'], 'iced')
    return orders_list

def get_now_time():
    now = datetime.now()
    # print(f"now: {now}")
    date = now.date()
    time = now.strftime("%H:%M:%S")
    return date, time