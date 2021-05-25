import mechanize
import http.cookiejar as cookielib
from bs4 import BeautifulSoup

import caldav

from datetime import datetime
import json
import pandas as pd

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


def extract_task_data(url):
    # download task page
    with open('taskpage.html', 'w') as output_file:
        output = br.open(target)
        output_file.write(output.read().decode("utf-8"))

    # extract data
    # returns summary, description, start, end
    with open('taskpage.html', 'r') as f:
        content = f.read()
        soup = BeautifulSoup(content, features='html.parser')

        # save rows of description
        description_html = []
        description = ""
        div = soup.find_all(class_='text-break-word p-3')
        for div in soup.find_all(class_='text-break-word p-3'):
            for p in div.find_all('p'):
                description_html.append(p.get_text())
        for line in description_html:
            description += "\\n" + line

        # extract start and end time from table
        table_of_time = soup.find(class_='bb0').find_all('tr')
        start = table_of_time[1].find('td').get_text()
        end = table_of_time[2].find('td').get_text()

        # get summary from title
        # remove trailing 'Details for'
        summary = soup.find('h1').get_text()[len('Details for '):]

        return summary, description, start, end


def create_task(start='', end='', summary='', now='', description=''):
    created = "\nCREATED:" + str(now)
    # last-modified = "LAST-MODIFIED:" + str(now)
    dtstamp = "\nDTSTAMP:" + str(now)
    dtstart = "\nDTSTART;VALUE=DATE:" + str(start)
    due = "\nDUE;VALUE=DATE:" + str(end)
    summary = "\nSUMMARY:" + str(summary)
    description = "\nDESCRIPTION:" + str(description)
    uid = "\nUID:" + str(hash(start + summary))
    # priority = "PRIORITY:" + '1'
    return "BEGIN:VCALENDAR\nVERSION:2.0\nBEGIN:VTODO" + dtstart + created + dtstamp + summary + due + uid + description + "\nEND:VTODO\nEND:VCALENDAR"

# check if task exists, based on title
def task_is_inexistent(summary, start, tasks):
    for task in tasks:
        if task.vobject_instance.vtodo.summary.value == summary:
            # TODO
            # add something like this to check if the var for start time is the same
            # and task.vobject_instance.vtodo.start.value == start
            # or maybe with url
            return False
    return True


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

    summary, description, start, end = extract_task_data(target)

    start = pd.to_datetime(start).strftime('%Y%m%dT%H%M%SZ')
    end = pd.to_datetime(end).strftime('%Y%m%dT%H%M%SZ')

    # ',' causes errors, therefore replace it with '\\,'
    summary = summary.replace(',', '\\,')
    description = description.replace(',', '\\,')

    # test if task is already present
    if task_is_inexistent(summary, start, tasks):
        # create the new task
        task = create_task(start=start, end=end, summary=summary, now=now, description=description)
        tasklist.add_todo(task)
        print("Task added (" + summary + ")")
    else:
        print("Task already exists (" + summary + ")")
