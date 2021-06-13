import mechanize
import http.cookiejar as cookielib
from bs4 import BeautifulSoup

import caldav

from datetime import datetime
import json
import pandas as pd


class taskpage:
    # function to get taskpage content and save it to 'content'
    def extract_task_data(self):
        # download and save task page
        output = br.open(self.url)
        self.content = output.read().decode("utf-8")

        # extract data
        # returns summary, description, start, end
        soup = BeautifulSoup(self.content, features='html.parser')

        # save rows of description
        description_html = []
        description = ""
        div = soup.find_all(class_='text-break-word p-3')
        for div in soup.find_all(class_='text-break-word p-3'):
            for p in div.find_all('p'):
                description_html.append(p.get_text())
        for line in description_html:
            description += "\\n" + line
        self.description = description

        # extract start and end time from table
        table_of_time = soup.find(class_='bb0').find_all('tr')
        self.start = table_of_time[1].find('td').get_text()
        self.end = table_of_time[2].find('td').get_text()

        # get summary from title
        # remove trailing 'Details for'
        self.summary = soup.find('h1').get_text()[len('Details for '):]

    # escape special characters
    def escape_chars(self):
        # ',' causes errors, therefore replace it with '\\,'
        self.summary.replace(',', '\\,')
        self.description.replace(',', '\\,')
        # TODO: somehow not escaping

    def adjust_time(self):
        # convert date time format for caldav
        self.start = pd.to_datetime(self.start).strftime('%Y%m%dT%H%M%SZ')
        self.end = pd.to_datetime(self.end).strftime('%Y%m%dT%H%M%SZ')

    def publish(self, now, tasklist):
        # create caldav data for task
        created = "\nCREATED:" + str(now)
        # last-modified = "LAST-MODIFIED:" + str(now)
        dtstamp = "\nDTSTAMP:" + str(now)
        dtstart = "\nDTSTART;VALUE=DATE:" + str(self.start)
        due = "\nDUE;VALUE=DATE:" + str(self.end)
        summary = "\nSUMMARY:" + str(self.summary)
        description = "\nDESCRIPTION:" + str(self.description)
        uid = "\nUID:" + str(hash(self.start + summary))
        # priority = "PRIORITY:" + '1'
        caldav_data = "BEGIN:VCALENDAR\nVERSION:2.0\nBEGIN:VTODO" + dtstart + created + dtstamp + summary + due + uid + description + "\nEND:VTODO\nEND:VCALENDAR"

        # save to caldav server
        tasklist.add_todo(caldav_data)

    def is_inexistent(self, tasks):
        for task in tasks:
            if task.vobject_instance.vtodo.summary.value == self.summary:
                # TODO
                # add something like this to check if the var for start time is the same
                # and task.vobject_instance.vtodo.start.value == start
                # or maybe with url
                return False
        return True

    # instance attribute
    def __init__(self, url) -> None:
        self.url = url
        self.start = None
        self.end = None
        self.summary = None
        self.description = None


# load credentials from file
credentials_file = json.loads(open('credentials.json').read())


# Browser
br = mechanize.Browser()

# Cookie Jar (for session cookie)
cj = cookielib.LWPCookieJar()
br.set_cookiejar(cj)

# Browser options
br.set_handle_equiv(True)
br.set_handle_gzip(True)
br.set_handle_redirect(True)
br.set_handle_referer(True)
br.set_handle_robots(False)
br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)

br.addheaders = [('User-agent', 'Chrome')]

# Site to login
br.open(credentials_file['domain'] + 'iserv/login')

# Select the login form
br.select_form(nr=0)

# User credentials
br.form['_username'] = credentials_file['username']
br.form['_password'] = credentials_file['password']

# Login
br.submit()

with open('tasklist.html', 'w') as output_file:
    output = br.open(credentials_file['domain'] + 'iserv/exercise')
    output_file.write(output.read().decode("utf-8"))

# save all links to the specific task page in target_links
target_links = []
with open('tasklist.html', 'r') as f:
    content = f.read()
    soup = BeautifulSoup(content, 'html.parser')
    for link in soup.find_all('a'):
        target = link.get('href')
        if target.startswith(credentials_file['domain'] + 'iserv/exercise/show/'):
            target_links.append(target)


# Connection to school server
client = caldav.DAVClient(url=credentials_file['url'],
                          username=credentials_file['username'], password=credentials_file['password'])

principal = client.principal()

# connect to Tasklist specified in credentials.json if existent
# otherwise create it
try:
    tasklist = principal.calendar(name=credentials_file['tasklist'])
except caldav.error.NotFoundError:
    tasklist = principal.make_calendar(name=credentials_file['tasklist'])

# include_completed to overcome adding already done tasks
tasks = tasklist.todos(include_completed=True)

for target in target_links:
    now = datetime.now()
    now = now.strftime("%Y%m%dT%H%M%SZ")

    task = taskpage(target)
    task.extract_task_data()
    task.escape_chars()
    task.adjust_time()

    # test if task is already present
    if task.is_inexistent(tasks):
        # create the new task
        task.publish(now, tasklist)
        print("Task added (" + task.summary + ")")
    else:
        print("Task already exists (" + task.summary + ")")
