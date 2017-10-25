import os
import sys
import json
from datetime import datetime

import requests
from flask import Flask, request

app = Flask(__name__)

order = {}

menu = {
    "rice": [
        {
        "title": "Rice 1",
        "subtitle": "Price: 100 Tk",
        "image_url": "http://www.simplyrecipes.com/wp-content/uploads/2017/05/2017-05-22-HT-Rice-19.jpg",
        "buttons": [
                {
                "type": "postback",
                "title": "Get This",
                "payload": "get.rice.1",
                }
            ],
        },
        {
        "title": "Rice 2",
        "subtitle": "Price: 120 Tk",
        "image_url": "http://food.fnr.sndimg.com/content/dam/images/food/fullset/2012/10/1/0/WU0308H_garlic-cilantro-lime-rice_s4x3.jpg.rend.hgtvcom.616.462.suffix/1414181933035.jpeg",
        "buttons": [
            {
            "type": "postback",
            "title": "Get This",
            "payload": "get.rice.2",
            }
        ],
        }
    ],
    "fast_food": [
        {
        "title": "Pizza",
        "subtitle": "Price: 100 Tk",
        "image_url": "https://www.cicis.com/media/1138/pizza_trad_pepperoni.png",
        "buttons": [
                {
                "type": "postback",
                "title": "Get This",
                "payload": "get.fast_food.1",
                }
            ],
        },
        {
        "title": "Burger",
        "subtitle": "Price: 120 Tk",
        "image_url": "http://smokeybones.com/wp-content/uploads/2015/11/loaded-bbq-burger.jpg",
        "buttons": [
            {
            "type": "postback",
            "title": "Get This",
            "payload": "get.fast_food.2",
            }
        ],
        }
    ],
    "drink": [
        {
        "title": "Capuchino",
        "subtitle": "Price: 100 Tk",
        "image_url": "https://t2.rg.ltmcdn.com/es/images/2/4/2/img_capuchino_16242_paso_5_600.jpg",
        "buttons": [
                {
                "type": "postback",
                "title": "Get This",
                "payload": "get.drink.1",
                }
            ],
        },
        {
        "title": "Shake",
        "subtitle": "Price: 120 Tk",
        "image_url": "http://supervapestore.com/media/catalog/product/cache/5/thumbnail/650x650/9df78eab33525d08d6e5fb8d27136e95/b/a/bananamilk.jpg",
        "buttons": [
            {
            "type": "postback",
            "title": "Get This",
            "payload": "get.drink.2",
            }
        ],
        }
    ]

}

@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():
    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]  # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text

                    try:
                        payload = messaging_event["message"]["quick_reply"]["payload"]
                    except:
                        payload = ''
                    try:
                        order_id = order[sender_id]
                    except:
                        order_id = ''

                    if 'start' in message_text.lower():
                        # send_message(sender_id, "This is ruhshan")
                        menu_ask(sender_id, 'test')
                    elif payload:
                        if payload == "menu_yes":
                            show_category(sender_id, "you'll see the menu.")
                        elif payload == "menu_no":
                            send_message(sender_id, "Okay, Come again when you are hungry.")
                    elif order_id:
                        print(order)
                        if order[sender_id]['address'] == 'not_set':
                            order[sender_id]['address'] = message_text
                            delivery_charge = 40
                            send_message(sender_id, "Pay {} + {} by bkash and enter the transaction number.".format(
                                    order[sender_id]['food_cost'], delivery_charge))
                            order[sender_id]['bkash']='take_now'
                        elif order[sender_id]['bkash']=='take_now':
                            if message_text=='1221':
                                order[sender_id]['bkash']=message_text
                                send_message(sender_id, "Thank you , you will have your {} at: {}".format(order[sender_id]['food_name'],order[sender_id]['address']))
                            else:
                                order[sender_id]['bkash']='take_now'
                                send_message(sender_id, "Wrong bkash")
                        else:
                            send_message(sender_id,"Hello, type 'start' for ordering food")


                    else:
                        send_message(sender_id, "Hello, type 'start' for ordering food")



                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):
                    sender_id = messaging_event["sender"]["id"]
                    recipient_id = messaging_event["recipient"]["id"]
                    postback_payload = messaging_event["postback"]["payload"]
                    if postback_payload=="menu_rice":
                        send_menu(sender_id, "rice")
                    elif postback_payload=="menu_fast_food":
                        send_menu(sender_id, "fast_food")
                    elif postback_payload=="menu_drinks":
                        send_menu(sender_id, "drink")

                    elif postback_payload.startswith('get'):
                        item, id = postback_payload.split('.')[1:]
                        price = menu[item][int(id)-1]['subtitle'].split(' ')[1]
                        food_name = menu[item][int(id)-1]['title']
                        order[sender_id] = {'food_name':food_name,'food_cost' : price, 'address':'not_set', 'bkash':'not_set'}
                        send_message(sender_id, "Please Type your address")
                    else:
                        send_message(sender_id, "postback bujhina!")

    return "ok", 200


def deliver(params, headers, data):
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def menu_ask(recipient_id, message_text):
    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }

    user_details_url = "https://graph.facebook.com/v2.6/%s" % recipient_id
    user_details_params = {'fields': 'first_name,last_name,profile_pic',
                           'access_token': os.environ["PAGE_ACCESS_TOKEN"]}
    user_details = requests.get(user_details_url, user_details_params).json()
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": "Hello {}, do you want to view the menu? :) ".format(user_details['first_name']),
            "quick_replies": [
                {
                    "content_type": "text",
                    "title": "YEP",
                    "payload": "menu_yes"

                },

                {
                    "content_type": "text",
                    "title": "NOPE",
                    "payload": "menu_no"

                }
            ]
        }
    })
    deliver(params, headers, data)


def show_category(recipient_id, message_text):
    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }

    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": [{
                        "title": "Choose Food Category",

                        "buttons": [{
                            "type": "postback",
                            "title": "Rice",
                            "payload": "menu_rice",
                        },
                            {
                                "type": "postback",
                                "title": "Fast Food",
                                "payload": "menu_fast_food",
                            },
                            {
                                "type": "postback",
                                "title": "Drinks",
                                "payload": "menu_drinks",
                            }
                        ],
                    }, ]
                }
            }
        }
    }
    )
    deliver(params, headers, data)


def send_menu(recipient_id, category):
    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=category))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "attachment": {
                "type": "template",
                "payload": {
                    "template_type": "generic",
                    "elements": menu[category]
                }
            }
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def send_option(recipient_id, message_text):
    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": "Choose Option",
            "quick_replies": [
                {
                    "content_type": "text",
                    "title": "GOOGLE",
                    "payload": "www.google.com"

                },

                {
                    "content_type": "text",
                    "title": "FACEBOOK",
                    "payload": "www.facebook.com"

                }
            ]
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def send_message(recipient_id, message_text):
    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def log(msg, *args, **kwargs):  # simple wrapper for logging to stdout on heroku
    try:
        if type(msg) is dict:
            msg = json.dumps(msg)
        else:
            msg = unicode(msg).format(*args, **kwargs)
        print u"{}: {}".format(datetime.now(), msg)
    except UnicodeEncodeError:
        pass  # squash logging errors in case of non-ascii text
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)
