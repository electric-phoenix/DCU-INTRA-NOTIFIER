#Script Developed by Szymon Masternak 2020, slight modification by Ephraim Emmanuel 2020

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import random
import re
import time
import os
import json
import requests




intra_url = "https://www101.dcu.ie/intra/cgi-bin/index2.php"

username_intra = 'REPLACE THIS STRING WITH YOUR STUDENT NUMBER AS INT'#put your details here
password_intra = 'PUT INTRA PASSWORD HERE'

title='Intra Bot'#Name of the notification sender
options = Options()
options.headless = False
PATH = "C:\\bin\\chromedriver.exe"
timeout = 15 # 15 second timeout for login
interval_min = 20 # minimum amount of time it checks the intra page
interval_max = 40 # maximum amount of time it checks the intra page

newjob = 0
newinterview = 0
updatejson = False

jsonfile = {
    "previousjob": 0,
    "previousinterview": 0,
    "offers": {}
}

newoffers = {
}

def pushbullet_message(title, body):
    msg = {"type": "note", "title": title, "body": body}
    TOKEN = 'ENTER PUSHBULLET API TOKEN HERE'
    resp = requests.post('https://api.pushbullet.com/v2/pushes', 
                         data=json.dumps(msg),
                         headers={'Authorization': 'Bearer ' + TOKEN,
                                  'Content-Type': 'application/json'})
    if resp.status_code != 200:
        raise Exception('Error',resp.status_code)
    else:
        print ('Message sent')

def findnumber(string):
    try:
        return int(re.search('\s\d\s+', string).group())
    except:
        return 0

def randomintger(int1, int2):
    return random.randint(int1, int2)

def checkchange(old, fetched):
    tempBool = False
    tempString = ''

    if(fetched == None):
        tempString += ("No available positions\n")
        return (False,tempString)
    
    if(old == fetched):
        print("No Change")
        return (False, tempString)

    if(sorted(old.keys()) == sorted(fetched.keys())):
        print("No new companies have changed")

    for (i,j) in old.items():
        for (k,l) in fetched.items():
            if(i == k and j < l):
                tempString += ("Company " + str(i) + " added " + str(int(l)-int(j)) + " position(s)\n")
                print("Company " + str(i) + " added " + str(int(l)-int(j)) + " position(s)")
                tempBool = True
            if(i == k and j > l):
                tempString += ("Company " + str(i) + " removed " + str(int(j)-int(l)) + " position(s)\n")
                print("Company " + str(i) + " added " + str(int(l)-int(j)) + " position(s)")
    
    diff = list(set(fetched.keys()) - set(old.keys()))
    if(diff):
        for ii in diff:
            tempString += ("Company " + str(ii) + " added " + str(fetched[ii]) + " position(s)\n")
            print("Company " + str(ii) + " added " + str(fetched[ii]) + " position(s)")

        tempString += ("Companies that have been added " + ', '.join(diff) + "\n")
        print("Companies that have been added " + ', '.join(diff))
        tempBool = True
    
    print("")
    return (tempBool,tempString)

try:
    f = open('count.json', 'r' )
    jsonfile = json.loads(f.read())
    print("JSON file")
    print(jsonfile)
    f.close()
except:
    print("File Not Found")
    print("Creating File")
    f = open('count.json', 'w' )
    f.write(json.dumps(jsonfile))
    f.close()

while(True):
    if(not username_intra and not password_intra ):
        print("Enter your INTRA username and password\n")
        quit()

    driver = webdriver.Chrome(PATH,options=options)
    driver.get(intra_url)
    usernamefield = driver.find_element_by_xpath("/html/body/center/form[1]/table/tbody/tr[2]/td[2]/input")
    usernamefield.send_keys(username_intra)

    passwordfield = driver.find_element_by_xpath("/html/body/center/form[1]/table/tbody/tr[3]/td[2]/input")
    passwordfield.send_keys(password_intra)

    current_url = driver.current_url

    loginbutton = driver.find_element_by_xpath("/html/body/center/form[1]/input")
    loginbutton.click()
    
    WebDriverWait(driver, timeout).until(EC.url_changes(current_url))

    text = driver.find_element_by_xpath("/html/body/font/center/table/tbody/tr/td/center/font/p[2]")
    newjob = findnumber(text.text)
    print("Number of Jobs: " + str(newjob))

    text = driver.find_element_by_xpath("/html/body/font/center/table/tbody/tr/td/center/font/p[4]")
    newinterview = findnumber(text.text)
    print("Number of Interviews: " + str(newinterview))

    viewjobs = driver.find_element_by_xpath("/html/body/font/center/table/tbody/tr/td/center/font/form/input[1]")
    viewjobs.click()
    
    table = driver.find_element_by_xpath(".//tr")
    for row in table.find_elements_by_xpath(".//tr"):
        for td1 in row.find_elements_by_xpath(".//td[1]"):
            if(td1.text in newoffers.keys()):
                newoffers[td1.text] = int(newoffers[td1.text]) + 1
            else:
                newoffers[td1.text] = 1

    if(newoffers['Company']):
        newoffers.pop('Company',None)
    
    (changes,stringdesc) = checkchange(jsonfile['offers'], newoffers)
    if(newjob > jsonfile["previousjob"] or changes):
        pushbullet_message(title, stringdesc)
        updatejson = True
        
    if(newinterview > jsonfile["previousinterview"]):
        pushbullet_message(title, stringdesc)
        updatejson = True

    driver.close()

    if(updatejson):
        print("Updating JSON File")
        jsonfile['offers'] = newoffers
        jsonfile['previousjob'] = newjob
        jsonfile['previousinterview'] = newinterview
        f = open( 'count.json', 'w' )
        f.write(json.dumps(jsonfile))
        f.close()
        updatejson = False

    sleeptime = randomintger(interval_min*60,interval_max*60)
    print("Sleeping for " + str(int(sleeptime/60)) + " minutes\n")
    time.sleep(sleeptime)