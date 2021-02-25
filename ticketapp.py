# https://bottickett.herokuapp.com/callback

import os
import sys
from config import line_secret, line_access_token
from flask import Flask, request, abort, send_from_directory, render_template
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage,FollowEvent,QuickReply,QuickReplyButton,MessageAction
from line_notify import LineNotify
from reply import reply_msg , SetMessage_Object
from flex_stock import *
from dialogflow_uncle import detect_intent_texts
from datetime import datetime,date

app = Flask(__name__)

channel_secret = line_secret
channel_access_token = line_access_token

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

set_value = '1465.76'
#Quarter

today = date.today()
end = datetime.now()
current_time = end.strftime("%H:%M %p")
current_hrs = end.strftime("%H")

if int(current_hrs) > 18:
	say = f'Night {current_time}'
elif int(current_hrs) > 12:
	say = f'Afternoon {current_time}'
else:
	say = f'Morning {current_time}'

start_year = today.year - 1
start_year = '{}-{}-01'.format(start_year,today.month)

yearly = '{}-01-01'.format(today.year)
monthly = '{}-{}-01'.format(today.year,today.month)

def linechat(text):    
    ACCESS_TOKEN = "12CiN1mDzj3q93N5aTYvtWX63XlQOqDs6FWizTRUx1y"
    notify = LineNotify(ACCESS_TOKEN)
    notify.send(text)

@app.route("/callback", methods=['POST'])
def callback():
	signature = request.headers['X-Line-Signature']
	body = request.get_data(as_text=True)
	app.logger.info("Request body: " + body)
	try:
		handler.handle(body, signature)
	except InvalidSignatureError:
		abort(400)
	return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    text_from_user = event.message.text
    reply_token = event.reply_token
    userid = event.source.user_id
    
    disname = line_bot_api.get_profile(user_id=userid).display_name
    request_text= ('ticket'+'\n' + '>> {} : {}').format(disname,text_from_user)
    print(request_text)
    linechat(request_text)

    result_from_dialogflow = detect_intent_texts(project_id="worldstock-iardyn",
                                        session_id=userid ,
                                        text=text_from_user , 
                                        language_code="th")
    
    action = result_from_dialogflow["action"]
    response = result_from_dialogflow["fulfillment_messages"] #as list

    print("action : " + action)
    print("response : " + str(response))

    try:
        if 'Hello Bot' in text_from_user:    
            text_list = [
                'สวัสดีจ้า คุณ {} '.format(disname),
                'สวัสดีจ้า คุณ {} วันนี้จะเล่นตัวไหนดี'.format(disname),
            ]

            from random import choice
            word_to_reply = choice(text_list)
            text_to_reply = TextSendMessage(text = word_to_reply)
            line_bot_api.reply_message(
                    event.reply_token,
                    messages=[text_to_reply]
                )
            return 'OK'

        else:
            from bs4 import BeautifulSoup as soup
            from urllib.request import urlopen as req
            from pandas_datareader import data
            from datetime import datetime, date
                    
            code = text_from_user
            ticket = [text_from_user]
            symbols = list(map(lambda e: e + '.bk', ticket))
                        
            def checkmarket(code):
                url = 'https://www.settrade.com/C04_01_stock_quote_p1.jsp?txtSymbol={}&ssoPageId=9&selectPage=1'.format(code)
                webopen = req(url)
                page_html = webopen.read()
                webopen.close()

                data = soup(page_html, 'html.parser')
                price = data.findAll('div',{'class':'col-xs-6'})
                title = price[0].text
                stockprice = price[2].text
                stockprice = stockprice.replace('\n','')
                change = price[3].text
                change = change.replace('\n','')
                change = change.replace('\r','')
                change = change[87:]
                change = change.replace('\n','')
                change = change.replace('(','')
                comvlue = data.findAll('div',{'class':'col-xs-4'})
                comvlue = comvlue[6].text
                comvlue = comvlue.replace(',','')
                comvlue = format(float(comvlue),'')
                comvluee = format(float(comvlue),',')
                return [title,stockprice,change,comvlue,comvluee]
            def free(code):
                url = 'https://www.settrade.com/C04_05_stock_majorshareholder_p1.jsp?txtSymbol={}&ssoPageId=14&selectPage=5'.format(code)
                webopen = req(url)
                page_html = webopen.read()
                webopen.close()
                data = soup(page_html, 'html.parser')
                freefloat = data.findAll('div',{'class':'row separate-content'})
                freefloat = freefloat[0].text
                freefloat = freefloat.replace('\n','')
                freefloat = freefloat.replace('\r','')
                freefloat = freefloat[-6:]
                freefloat = freefloat.replace('%','')
                return [freefloat]

            class ticket:
                def __init__(self,stock):
                    self.stock = stock
                    list = self.stock
                def bull(self):
                    list = self.stock

                    dfall = data.DataReader(f'{list}', data_source="yahoo",start=start_year, end=end)

                    try:
                        dfY = data.DataReader(f'{list}', data_source="yahoo", start=yearly, end=end)
                    except ValueError:
                        dfY = data.DataReader(f'{list}', data_source="yahoo", start=start_year, end=end)

                    try:
                        dfM = data.DataReader(f'{list}', data_source="yahoo", start=monthly, end=end)
                    except ValueError:
                        dfM = data.DataReader(f'{list}', data_source="yahoo", start=start_year, end=end)

                    list = list.replace('.bk','')
                    stock = f'{list}'
                    dfall.dropna(inplace=True)

                    st = checkmarket(stock)
                    fr = free(stock)
                    freefloat = fr[0]

                    try:
                        Close = float(st[1])
                    except ValueError:
                        Close = dfall['Close'].iloc[-1]

                    Close  = '%.2f'%Close
                    Close = str(Close) 

                    Open_all = dfall['Open'].iloc[0]
                    Open_all  = '%.2f'%Open_all
                    Open_all = str(Open_all)

                    Chg_all = ((float(Close) - float(Open_all))/ float(Open_all))*100
                    Chg_all = '%.2f'%Chg_all
                    Chg_all = str(Chg_all)

                    OpenY = dfY['Open'].iloc[0]
                    OpenY  = '%.2f'%OpenY
                    OpenY = str(OpenY)

                    CloseY = dfY['Close'].iloc[0]
                    CloseY  = '%.2f'%CloseY
                    CloseY = str(CloseY)

                    ChgY = ((float(Close) - float(OpenY)) / float(OpenY) )*100
                    ChgY = '%.2f'%ChgY
                    ChgY = str(ChgY)

                    Chg_closeY = ((float(Close) - float(CloseY)) / float(CloseY) )*100
                    Chg_closeY = '%.2f'%Chg_closeY
                    Chg_closeY = str(Chg_closeY)

                    OpenM = dfM['Open'].iloc[0]
                    OpenM  = '%.2f'%OpenM
                    OpenM = str(OpenM)

                    CloseM = dfM['Close'].iloc[0]
                    CloseM  = '%.2f'%CloseM
                    CloseM = str(CloseM)

                    ChgM = ((float(Close) - float(CloseM)) / float(CloseM) )*100
                    ChgM = '%.2f'%ChgM
                    ChgM = str(ChgM)

                    try:
                        today_chg = float(st[2])
                    except ValueError:
                        today_chg = float(dfall['Close'].iloc[-1]) - float(dfall['Close'].iloc[-2])

                    today_chg  = '%.2f'%today_chg
                    today_chg = str(today_chg)

                    def computeRSI (data, time_window):
                        diff = data.diff(1).dropna()
                        up_chg = 0 * diff
                        down_chg = 0 * diff

                        up_chg[diff > 0] = diff[ diff>0 ]    
                        down_chg[diff < 0] = diff[ diff < 0 ]

                        up_chg_avg   = up_chg.ewm(com=time_window-1 , min_periods=time_window).mean()
                        down_chg_avg = down_chg.ewm(com=time_window-1 , min_periods=time_window).mean()

                        rs = abs(up_chg_avg/down_chg_avg)
                        rsi = 100 - 100/(1+rs)
                        return rsi

                    dfall['RSI'] = computeRSI(dfall['Close'], 14)
                    m_RSI = dfall['RSI'].iloc[-1]
                    m_RSI = '%.2f'%m_RSI
                    m_RSI = str(m_RSI)
                            
                    #copy dataframeY
                    dfall = dfall.copy()
                    dfall['date_id'] = ((dfall.index.date - dfall.index.date.min())).astype('timedelta64[D]')
                    dfall['date_id'] = dfall['date_id'].dt.days + 1

                    # high trend lineY
                    dfall_mod = dfall.copy()

                    while len(dfall_mod)>3:

                        reg = linregress(x=dfall_mod['date_id'],y=dfall_mod['Close'],)
                        dfall_mod = dfall_mod.loc[dfall_mod['Close'] > reg[0] * dfall_mod['date_id'] + reg[1]]

                    reg = linregress(x=dfall_mod['date_id'],y=dfall_mod['Close'],)
                    dfall['high_trend'] = reg[0] * dfall['date_id'] + reg[1]

                    # low trend lineY
                    dfall_mod = dfall.copy()

                    while len(dfall_mod)>3:

                        reg = linregress(x=dfall_mod['date_id'],y=dfall_mod['Close'],)
                        dfall_mod = dfall_mod.loc[dfall_mod['Close'] < reg[0] * dfall_mod['date_id'] + reg[1]]

                    reg = linregress(x=dfall_mod['date_id'],y=dfall_mod['Close'],)
                    dfall['low_trend'] = reg[0] * dfall['date_id'] + reg[1]
                    
                    min_Y = dfall.nsmallest(1, columns='Low')
                    min_Y = min_Y['Low'].iloc[-1]
                    min_Y = '%.2f'%min_Y
                    min_Y = str(min_Y)

                    max_Y = dfall.nlargest(1, columns='High')
                    max_Y = max_Y['High'].iloc[-1]
                    max_Y = '%.2f'%max_Y
                    max_Y = str(max_Y)

                    dfall['min_Y'] = float(min_Y)
                    dfall['max_Y'] = float(max_Y)
                    
                    #copy dataframe prevQ
                    dfY = dfY.copy()
                    dfY['date_id'] = ((dfY.index.date - dfY.index.date.min())).astype('timedelta64[D]')
                    dfY['date_id'] = dfY['date_id'].dt.days + 1

                    # high trend line prevQ
                    dfY_mod = dfY.copy()

                    while len(dfY_mod)>3:

                        reg = linregress(x=dfY_mod['date_id'],y=dfY_mod['Close'],)
                        dfY_mod = dfY_mod.loc[dfY_mod['Close'] > reg[0] * dfY_mod['date_id'] + reg[1]]

                    reg = linregress(x=dfY_mod['date_id'],y=dfY_mod['Close'],)
                    dfY['high_trendQ'] = reg[0] * dfY['date_id'] + reg[1]

                    # low trend line prevQ
                    dfY_mod = dfY.copy()

                    while len(dfY_mod)>3:

                        reg = linregress(x=dfY_mod['date_id'],y=dfY_mod['Close'],)
                        dfY_mod = dfY_mod.loc[dfY_mod['Close'] < reg[0] * dfY_mod['date_id'] + reg[1]]

                    reg = linregress(x=dfY_mod['date_id'],y=dfY_mod['Close'],)
                    dfY['low_trendQ'] = reg[0] * dfY['date_id'] + reg[1]
                    dfY['low_trendQ'] = dfY['low_trendQ'].replace(np.nan, dfY['Close'].iloc[0])

                    candle_start = dfY['low_trendQ'].iloc[0]
                    candle_start = '%.2f'%candle_start
                    candle_start = str(candle_start)

                    candle_end = dfY['low_trendQ'].iloc[-1]
                    candle_end = '%.2f'%candle_end
                    candle_end = str(candle_end)

                    if float(candle_start) > float(candle_end):
                        pattern = 'Lower low'
                    else:
                        pattern = 'Lower high'

                    Volume = dfY['Volume'].iloc[-1]
                    Volume = str(Volume)

                    vol_buy = (float(budget) / float(OpenY))
                    vol_buy = round(vol_buy,-2)

                    vol_key = float(vol_buy) / 2
                    vol_key = round(vol_key,-2)
                    vol_key = str(int(vol_key))

                    trade_val = float(Close) * float(Volume)
                    trade_val = int(float(trade_val))
                    trade_value = '{:,}'.format(trade_val)

                    dfall['Open_all'] = dfall['Open'].iloc[0]
                    dfall['high_trendQ'] = dfY['high_trendQ']
                    dfall['low_trendQ'] = dfY['low_trendQ']

                    dfY['OpenY'] = dfY['Open'].iloc[0]
                    dfY['CloseY'] = dfY['Close'].iloc[0]
                    dfM['CloseM'] = dfM['Close'].iloc[0]

                    dfall['ema'] = dfall['Close'].rolling(35).mean()
                    dfall['ema'] = dfall['ema'].replace(np.nan, dfY['Close'].iloc[0])
                    dfall['emas'] = dfall['Close'].rolling(10).mean()
                    dfall['emas'] = dfall['emas'].replace(np.nan, dfY['Close'].iloc[0])

                    ema = dfall['ema'].iloc[-1]
                    ema = float(ema)

                    if ema >= 100:
                        ema = (round(ema/0.5) * 0.5)
                    elif ema >= 25:
                        ema = (round(ema/0.25) * 0.25)
                    elif ema >= 10:
                        ema = (round(ema/0.1) * 0.1)
                    elif ema >= 5:
                        ema = (round(ema/0.05) * 0.05)
                    else:
                        ema = (round(ema/0.02) * 0.02)

                    ema = '%.2f'%ema
                    ema = str(ema)

                    emas = dfall['emas'].iloc[-1]
                    emas = float(emas)

                    if emas >= 100:
                        emas = (round(emas/0.5) * 0.5)
                    elif emas >= 25:
                        emas = (round(emas/0.25) * 0.25)
                    elif emas >= 10:
                        emas = (round(emas/0.1) * 0.1)
                    elif emas >= 5:
                        emas = (round(emas/0.05) * 0.05)
                    else:
                        emas = (round(emas/0.02) * 0.02)

                    emas = '%.2f'%emas
                    emas = str(emas)

                    pema = dfall['ema'].iloc[-1]
                    pema = ((float(Close) - float(pema)) / float(pema))*100
                    pema = '%.2f'%pema
                    pema = str(pema)

                    high_trend = dfall['high_trend'].iloc[-1]
                    high_trend = '%.2f'%high_trend
                    high_trend = str(high_trend)

                    high_trendQ = dfall['high_trendQ'].iloc[-1]
                    high_trendQ = '%.2f'%high_trendQ
                    high_trendQ = str(high_trendQ)

                    comvlue = float(st[3])
                    comvluee = str(st[4])

                    if float(ChgM) >= 0.0 :
                        trendM = ' '
                    else:
                        trendM = 'X'

                    if float(ChgY) >= 0 :
                        trendAll = '▲'
                        if float(Close) >= float(CloseM) :
                            if float(Close) >= float(ema):
                                trendY = '©'
                            else:
                                trendY = ' '
                        else:
                            trendY = ' '
                    else:
                        trendAll = '▼'
                        if float(Close) >= float(CloseM) :
                            if float(Close) >= float(ema):
                                trendY = '℗'
                            else:
                                trendY = ' '
                        else:
                            trendY = ' '
			        
                    if float(today_chg) >= 0:
                        if float(Close) > float(CloseY):
                            if float(Close) >= float(CloseM) :
                                if float(Close) >= float(ema):
                                    notice = f'หุ้นขาใหญ่เก็บ {CloseM}'
                                else:
                                    notice = f'หุ้นขาใหญ่ขาย {ema}'
                            else:
                                notice = f'หุ้นขาใหญ่ปล่อยไหล {CloseM}'
                        elif float(Close) >= float(CloseM) :
                            if float(Close) >= float(ema):
                                notice = f'หุ้นกลับตัวมีแรงซื้อ {CloseM}'
                            else:
                                notice = f'หุ้นไหลเมื่อหลุด {ema}'
                        elif float(Close) >= float(ema):
                            notice = f'หุ้นกลับตัวระยะสั้น เมื่อผ่าน {ema}'
                        else:
                            notice = f'หุ้นไม่มีใครเก็บ {ema}'
                    else:
                        notice = f'กำลังย่อ/ปรับฐาน ไม่หลุด {CloseM} ห่อกลับ'
                    
                    text = f'ตอนนี้ {list} \nราคา {Close} ({today_chg}) \n{notice} \nแนวต้าน {max_Y}  \nแนวรับ {min_Y}  \nFree Float {freefloat}%'

                    word_to_reply = str('{}'.format(text))
                    linechat(word_to_reply)
                    text_to_reply = TextSendMessage(text = word_to_reply)
                    line_bot_api.reply_message(event.reply_token,messages=[text_to_reply])
                    return 'OK'
            
            for code in codes:
                ticket(code).bull()

    except:
        text_list = ['คุณ {} รอสักครู่นะคะ กำลังค้นหา {} ในฐานข้อมูล'.format(disname, text_from_user),
            '{} สะกด {} ไม่ถูกต้อง ลองใหม่อีกครั้ง'.format(disname, text_from_user),]

        from random import choice
        word_to_reply = choice(text_list)
        text_to_reply = TextSendMessage(text = word_to_reply)
        line_bot_api.reply_message(event.reply_token,messages=[text_to_reply])

@handler.add(FollowEvent)
def RegisRichmenu(event):
    userid = event.source.user_id
    disname = line_bot_api.get_profile(user_id=userid).display_name
    line_bot_api.link_rich_menu_to_user(userid,'richmenu-f90b8248dcba881183ab69d8d0441bfd')

    button_1 = QuickReplyButton(action=MessageAction(lable='IQUSTB',text='IQUSTB'))
    button_2 = QuickReplyButton(action=MessageAction(lable='IQXGL',text='IQXGL'))
    button_3 = QuickReplyButton(action=MessageAction(lable='IQXBRT',text='IQXBRT'))
    button_4 = QuickReplyButton(action=MessageAction(lable='SET',text='SET'))
    button_5 = QuickReplyButton(action=MessageAction(lable='TFEX',text='TFEX'))
    button_6 = QuickReplyButton(action=MessageAction(lable='Hello Bot',text='Hello Bot'))
    answer_button = QuickReply(items=[button_1,button_2,button_3,button_4,button_5,button_6])

if __name__ == '__main__':
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "Credentials.json"
    os.environ["DIALOGFLOW_PROJECT_ID"] = "worldstock-iardyn"
    port = int(os.getenv('PORT', 2000))
    app.run(debug=False, port=port, host='0.0.0.0', threaded=True)