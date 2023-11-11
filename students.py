import discord
from discord.ext import commands
from discord import app_commands
import requests, sqlite3, json, datetime
from bs4 import BeautifulSoup

now = datetime.datetime.now()
bot = commands.Bot(command_prefix='~', intents=discord.Intents.all())  #Discord bot

dbFile = 'database/studentData.db'  #DB路徑
conn = sqlite3.connect(dbFile)  #連接到指定路徑的DB
cursorObject = conn.cursor()
table_name = "All_Students"  #資料表的名稱

#設定要爬資料的url
url = 'https://bluearchive.wikiru.jp/?%E3%82%AD%E3%83%A3%E3%83%A9%E3%82%AF%E3%82%BF%E3%83%BC%E4%B8%80%E8%A6%A7'
r = requests.get(url)
sp = BeautifulSoup(r.text, 'html.parser')

table1 = sp.find('table', id='sortabletable1') #用id找到特定div中的table來爬資料
tbody1 = table1.find('tbody') #找到裡面名為tbody的標籤
trs = tbody1.find_all('tr') #裡面所有名為tr的標籤, 即每個學生的資料

#檢查資料表是否存在, 沒有的話就創建一個
def Check_Table():
    query_sql = "SELECT * FROM sqlite_master WHERE type = 'table' AND name = ?"
    listOfTable = cursorObject.execute(query_sql, (table_name,)).fetchall()
    if listOfTable == []:
        print("Table %s Not exists\n" % table_name)
        Create_Table()
        print("Created table %s." % table_name)
    else:
        print("Table %s exists\n" % table_name)

#創建table的function
def Create_Table():
    createTable_cmd = '''CREATE TABLE IF NOT EXISTS {} (
                        Name text,
                        School text,
                        Age text,
                        Club text,
                        Height text,
                        Birthday text,
                        Hobbies text,
                        Star text,
                        isUnique text,
                        Role text,
                        Position text,
                        Class text,
                        Weapon text,
                        Attack_Type text,
                        Armor text )'''.format(table_name)
    cursorObject.execute(createTable_cmd)

#導入學生資料
def Import_Students_Data():
    #找每個學生的資料
    for tr in trs:
        name = tr.find('td').find_next_sibling().find_next_sibling()
        student = name.find('a') #找到第三個column裡學生名稱的超連結
        #第18個column
        unique = name.find_next_sibling().find_next_sibling().find_next_sibling().find_next_sibling().find_next_sibling().find_next_sibling().find_next_sibling().find_next_sibling().find_next_sibling().find_next_sibling().find_next_sibling().find_next_sibling().find_next_sibling().find_next_sibling().find_next_sibling()
        '''
        for i in range(15):
            unique = unique.find_next_sibling()
        '''
        isUnique = unique.getText()

        #找出是否為限定角色
        uniqueLevel = ''
        if isUnique == '☆' :
            uniqueLevel = 'Unique'
        elif isUnique == '-' :
            uniqueLevel = 'Event'
        else:
            uniqueLevel = 'Normal'
        
        #學生個別的資料
        try:
            student_Name = student.getText() #學生名字
            if not '（' in student_Name or not '）' in student_Name: #跳過特殊衣裝版本
                student_Url = 'https://bluearchive.wikiru.jp' + student.get('href')[1:] #從主介面連至個別學生詳細資料的url
                #重複一開始的設定url步驟, 只是對象換成學生個別的頁面
                stu_r = requests.get(student_Url)
                stu_sp = BeautifulSoup(stu_r.text, 'html.parser')

                #重複找到table
                stu_td = stu_sp.find('td', valign='top')
                stu_table = stu_td.find('table', class_='style_table')  #通常在h2後面的div下面
                stu_trs = stu_table.find_all('tr', limit=17)  #limit表示只找出符合結果的前幾個標籤

                #從每一個tr開始爬關鍵資料
                for feature in stu_trs:
                    featureText = feature.find('th').getText()  #從每個th的名稱, 即所有資料的標題開始找

                    if featureText == 'フルネーム':
                        full_name = feature.find('td').getText()
                        print(f'found {full_name}, ', end='')
                    elif featureText == 'レアリティ':
                        star = feature.find('td').getText()
                    elif featureText == '役割':
                        role = feature.find('td').getText()
                    elif featureText == 'ポジション':
                        position = feature.find('td').getText()
                    elif featureText == 'クラス':
                        stu_class = feature.find('td').getText()
                    elif featureText == '武器種':
                        weapon = feature.find('td').getText()
                    elif featureText == '攻撃タイプ':
                        attack_type = feature.find('td').getText()
                    elif featureText == '防御タイプ':
                        armor = feature.find('td').getText()
                    elif featureText == '学園':
                        school = feature.find('td').getText()
                    elif featureText == '部活':
                        club = feature.find('td').getText()
                    elif featureText == '年齢':
                        age = feature.find('td').getText()
                    elif featureText == '誕生日':
                        birthday = feature.find('td').getText()
                    elif featureText == '身長':
                        height = feature.find('td').getText()
                    elif featureText == '趣味':
                        hobbies = feature.find('td').getText()

                print(full_name,school,age,club,height,birthday,hobbies,star,uniqueLevel,role,position,stu_class,weapon,attack_type,armor)
                insertData_cmd = '''INSERT INTO %s (
                            Name,School,Age,Club,Height,Birthday,Hobbies,
                            Star,isUnique,Role,Position,Class,Weapon,Attack_Type,Armor) 
                            VALUES (\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\',\'{}\');
                            '''.format(full_name,school,age,club,height,birthday,hobbies,star,uniqueLevel,role,position,stu_class,weapon,attack_type,armor) % table_name
                
                print(f'loding {full_name}...')
                cursorObject.execute(insertData_cmd)  #執行SQL程式
                print('done.')
                conn.commit()
        except:
            if student_Name == None : break #遇到None value就結束

Check_Table()
#Import_Students_Data()

@bot.event
async def on_ready():
    print(f'{bot.user} is ready, {now}.')
    try:
        synced = await bot.tree.sync()
        print(f'Synced {len(synced)} command(s)')
        await bot.change_presence(status=discord.Status.online, activity=discord.Game(name='Slash commands'))
    except Exception as e:
        print(e)

@bot.event
async def on_message(msg):
    if msg.author.bot:
        return

@bot.tree.command(name='greeting') #The name of the shown command
async def greet(interaction : discord.Interaction):
    await interaction.response.send_message(f'Hello, {interaction.user.name}.', ephemeral=False)
#If ephemeral = True, that means only you can see the reply.

@bot.tree.command(name='speak')
@app_commands.describe(ctx = '114514')
async def speak(interaction: discord.Interaction, ctx: str):
    await interaction.response.send_message(f'{interaction.user.name} said : `{ctx}`.')

bot.run(json.load(open('bot_token.json', 'r'))['launchKey'])