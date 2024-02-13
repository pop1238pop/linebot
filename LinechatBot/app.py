from flask import Flask, request, send_from_directory
from linebot.models import *
from linebot import *

from werkzeug.middleware.proxy_fix import ProxyFix
import os
import tempfile
import cv2
import numpy as np
from yolo_predictions import YOLO_Pred

app = Flask(__name__)

yolo = YOLO_Pred('best.pt','args.yaml')


line_bot_api = LineBotApi('hylUyImceWYRVvz4fw85flujUzEgt2BKxAeW089WCNgMiNJBSP8ONEQCgIkshTTwAa+jgcEqiRLmyjEX96+TYMJUnVUgneIeI93Q4aAOgbL0NpGSt2ev3a+pz2oAVIjo3vHxo/IFKbQ5awF8Izh/GAdB04t89/1O/w1cDnyilFU=')
handler = WebhookHandler('https://dialogflow.cloud.google.com/v1/integrations/line/webhook/8d1a17aa-1272-48a6-8201-3c9d4d87b7f1')


app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_host=1, x_proto=1)

@app.route("/callback", methods=['POST'])
def callback():
    body = request.get_data(as_text=True)
    # print(body)
    req = request.get_json(silent=True, force=True)
    intent = req["queryResult"]["intent"]["displayName"]
    text = req['originalDetectIntentRequest']['payload']['data']['message']['text']
    reply_token = req['originalDetectIntentRequest']['payload']['data']['replyToken']
    id = req['originalDetectIntentRequest']['payload']['data']['source']['userId']
    disname = line_bot_api.get_profile(id).display_name

    print('id = ' + id)
    print('name = ' + disname)
    print('text = ' + text)
    print('intent = ' + intent)
    print('reply_token = ' + reply_token)

    reply(intent,text,reply_token,id,disname)

    return 'OK'

def send_image(token, text, image_path):
    file_img = {'imageFile': open(image_path, 'rb')}
    LINE_HEADERS = {'content-type':'application/x-www-form-urlencoded','Authorization':'Bearer '+token}
    session_post = requests.post(url, headers=LINE_HEADERS, files=file_img, data= {'message': text})
    print(session_post.text)

def reply(intent,text,reply_token,id,disname):
    if intent == 'intent 5':
        text_message = TextSendMessage(text='ทดสอบสำเร็จ')
        line_bot_api.reply_message(reply_token,text_message)

@handler.add(MessageEvent, message=ImageMessage)
def handle_image_message(event):
    message_content = line_bot_api.get_message_content(event.message.id)
    static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp').replace("\\","/")
    print(static_tmp_path)
    
    with tempfile.NamedTemporaryFile(dir=static_tmp_path, prefix='jpg' + '-', delete=False) as tf:
        for chunk in message_content.iter_content():
            tf.write(chunk)
        tempfile_path = tf.name
        
    dist_path = tempfile_path + '.jpg'  # เติมนามสกุลเข้าไปในชื่อไฟล์เป็น jpg-xxxxxx.jpg
    os.rename(tempfile_path, dist_path) # เปลี่ยนชื่อไฟล์ภาพเดิมที่ยังไม่มีนามสกุลให้เป็น jpg-xxxxxx.jpg

    filename_image = os.path.basename(dist_path) # ชื่อไฟล์ภาพ output (ชื่อเดียวกับ input)
    filename_fullpath = dist_path.replace("\\","/")   # เปลี่ยนเครื่องหมาย \ เป็น / ใน path เต็ม
    
    img = cv2.imread(filename_fullpath)

    # ใส่โค้ดประมวลผลภาพตรงส่วนนี้
    #-------------------------------------------------------------
    pred_image, obj_box = yolo.predictions(img)
    print(obj_box)
    #-------------------------------------------------------------
        
    cv2.imwrite(filename_fullpath,pred_image)
    
    dip_url = request.host_url + os.path.join('static', 'tmp', filename_image).replace("\\","/")
    print(dip_url)
    line_bot_api.reply_message(
        event.reply_token,[
            TextSendMessage(text='result:'),
            ImageSendMessage(dip_url,dip_url)])
    
@app.route('/static/<path:path>')
def send_static_content(path):
    return send_from_directory('static', path)

if __name__ == "__main__":
    app.run()