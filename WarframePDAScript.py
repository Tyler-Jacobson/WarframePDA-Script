import requests
from bs4 import BeautifulSoup
import base64
import json
import time



items = [
    'ash', 'atlas', 'banshee', 'chroma', 'ember',
    'equinox', 'frost', 'hydroid', 'ivara', 'limbo',
    'loki', 'mag', 'mesa', 'mirage', 'nekros',
    'nezha', 'nova', 'nyx', 'oberon', 'rhino',
    'saryn', 'titania', 'trinity', 'valkyr', 'vauban',
    'volt', 'wukong', 'zephyr'
]

# items.sort()



def get_token():
    client_id = "psf328if3bf87bfseyd887esfsudfi0z"
    client_secret = "o8h43rn3qiufb3uq2fb43hvfy3fv4g3w"

    unencoded_key = client_id + ":" + client_secret

#     print(unencoded_key)

    urlSafeEncodedBytes = base64.urlsafe_b64encode(unencoded_key.encode("utf-8"))
    encoded_key = str(urlSafeEncodedBytes, "utf-8")

#     print(encoded_key)

    # "grant_type=password&username=" + username + "&password=" + password


    username = "testuser2"
    password = "password"


    url = "https://warframepda.herokuapp.com/login"
    userAuthData = "grant_type=password&username=" + username + "&password=" + password
    headers = {'Authorization': 'Basic ' + encoded_key,
              'Content-Type': 'application/x-www-form-urlencoded'
              }
    # payload = {'name':'testtim', 'password': 'testpass'}

    response = requests.post(url, userAuthData, headers=headers)

    print(response.json()['access_token'])
    return response.json()['access_token']



def request_data(url):
    headers = {'Content-Type': 'text/html',}
    response = requests.get(url, headers=headers)

    # since the site from which this data is scraped has a very dynamic
    # method for displaying orders, it's easier to simply sort through
    # the raw page source than it is to attempt to sort by xpath or
    # similar method

    # this section sorts through the raw page and pulls what becomes
    # a json object containing all orders for the given item
    page_soup = BeautifulSoup(response.text, 'html.parser')
    page_rough = page_soup.find_all(id = 'application-state')

    page_rough = str(page_rough)
    page_rough_len = len(page_rough)
    page_json = page_rough[56:page_rough_len - 10]

    page_json_loaded = json.loads(page_json)

    # finds the image for the item
    image_rough = page_soup.find(property="og:image")
    image_rough = str(image_rough)
    image_link = image_rough.split('"')[1]


    # parses for sell values
    page_sell_values = []

    for page_line in page_json_loaded['payload']['orders']:

        # checks for users that are set to 'online/ingame', are in the 'en/international' region, and are placing 'sell' orders
        if page_line['user']['status'] == 'ingame' and page_line['user']['region'] == 'en' and page_line['order_type'] == 'sell':

            # pulls out the platinum cost and seller name of each order
            price = int(page_line['platinum'])
            name = str(page_line['user']['ingame_name'])

            # puts the sellername and price into the correct format for the backend, then adds them to a list
            page_sell_values.append({"seller" : name, "price": price})


    temp_orders_list = sorted(page_sell_values, key=lambda k: k['price'])

    orders_list = []

    for order in temp_orders_list:
        orders_list.append(order)
        if len(orders_list) >= 5:
            break

#     print(orders_list)
    return [orders_list, image_link]

token = get_token()

item_part_names = ["neuroptics", "set", "systems", "chassis", "blueprint"]
item_part_names = sorted(item_part_names)

for item in items: # each warframe is an "item"

    constructed_parts_list = []
    for part in item_part_names: # makes a request for each 'part' of the item

        created_link = 'https://warframe.market/items/' + item + '_prime_' + part

        returned_data = request_data(created_link) # makes the request to WarframeMarket using the request_data function

        # appends all 5 parts to the 'constructed_parts_list' (one per loop iteration)
        constructed_parts_list.append({
            "partname": part.capitalize(),
            "orders": returned_data[0]
        })
        print("fetched data for " + item + " prime " + part)
        time.sleep(2)


    constructed_item = {
        "itemname": item.capitalize(),
        "imageurl": returned_data[1],
        "parts": constructed_parts_list
    }

    print(constructed_item)

    post_url = "https://warframepda.herokuapp.com/items/item"
    headers = {'Authorization': 'Bearer ' + token,
              'Content-Type': 'application/JSON'
              }
    response = requests.post(post_url, headers=headers, json=constructed_item)

    print(response)
