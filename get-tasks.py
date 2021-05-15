import mechanize
import http.cookiejar as cookielib
from bs4 import BeautifulSoup

import caldav

from datetime import datetime
import csv
import json

# load credentials from file
credentials_file = json.loads(open('credentials.json').read())


def download_data():
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

    # save export data of iserv tasks
    with open('downloaded-tasks.csv', 'w') as output_file:
        output = br.open(
            credentials_file['domain'] + 'iserv/exercise.csv?sort%5Bby%5D=enddate&sort%5Bdir%5D=DESC')
        output_file.write(output.read().decode("utf-8"))

    # TODO
    #   add option to save describtion of task


def create_task(start='', end='', summary='', now=''):
    created = "\nCREATED:" + str(now)
    # last-modified = "LAST-MODIFIED:" + str(now)
    dtstamp = "\nDTSTAMP:" + str(now)
    dtstart = "\nDTSTART;VALUE=DATE:" + str(start)
    due = "\nDUE;VALUE=DATE:" + str(end)
    summary = "\nSUMMARY:" + str(summary)
    uid = "\nUID:" + str(hash(start + summary))
    # priority = "PRIORITY:" + '1'
    return "BEGIN:VCALENDAR\nVERSION:2.0\nBEGIN:VTODO" + dtstart + created + dtstamp + summary + due + uid + "\nEND:VTODO\nEND:VCALENDAR"

# check if task exists, based on title
def task_is_inexistent(summary, start, tasks):
    for task in tasks:
        if task.vobject_instance.vtodo.summary.value == summary:
            # TODO
            # add something like this to check if the var for start time is the same
            # and task.vobject_instance.vtodo.start.value == start
            return False
    return True


# Download csv of iserv tasks
download_data()

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

# transfer the info from csv to caldav
with open('downloaded-tasks.csv', 'r') as csv_file:
    reader = csv.reader(csv_file, delimiter=';')

    # skip header column
    next(reader, None)
    for row in reader:
        now = datetime.now()
        now = now.strftime("%Y%m%dT%H%M%SZ")

        # Convert the date format from export format to caldav one
        # Attention:
        # This works only if the date in the csv is in the format m/d/Y
        start = datetime.strptime(row[1], '%m/%d/%Y')
        start = start.strftime('%Y%m%dT%H%M%SZ')
        end = datetime.strptime(row[2], '%m/%d/%Y')
        end = end.strftime('%Y%m%dT%H%M%SZ')

        # ',' causes errors, therefore replace it with ' - '
        summary = row[0].replace(',', ' - ')

        # test if task is already present
        if task_is_inexistent(summary, start, tasks):
            # create the new task
            task = create_task(start=start, end=end, summary=summary, now=now)
            tasklist.add_todo(task)
        else:
            print("Task already exists (" + summary + ")")
