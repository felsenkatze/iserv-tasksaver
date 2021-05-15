# Iserv Tasksaver

A small python script to download task data from the school server Iserv and save it to the internal caldav server of it so the data can be viewed by any CalDAV compatible client.

This script is designed to work with Iserv in English, in the German version the csv delimiter and the date format may be different.

## Usage

First, install all needed dependencies, calling 

~~~
pip3 install -r requirements.txt
~~~

Just copy `credentials.json.example` to `credentials.json` and change the values in the file to their appropriate value.

| value    | describtion                                                             |
| -------- | ----------------------------------------------------------------------- |
| domain   | domain of your Iserv with trailing 'https://'                           |
| url      | location of the caldav calendar with trailing 'https://' and ending '/' |
| tasklist | the name for the tasklist (choose one on your own)                      |
| username | Iserv username                                                          |
| password | should be obvious                                                       |

## Reason

You can have darkmode - I should'nt have to say more.

# TODO

- [x] Download Tasklist
- [x] Upload to CalDAV server
- [x] Ignore done tasks
- [ ] Save whole information
- [ ] Meaningful README

