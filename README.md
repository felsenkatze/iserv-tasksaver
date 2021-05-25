# Iserv Tasksaver

A small python script to download task data from the school server Iserv and save it to the internal caldav server of it so the data can be viewed by any CalDAV compatible client.

This script is designed to work with Iserv in English, in the German version the date format may be different.

## Usage

First, install all needed dependencies, calling

```
pip3 install -r requirements.txt
```

Just copy `credentials.json.example` to `credentials.json` and change the values in the file to their appropriate value.

| value    | describtion                                                             |
| -------- | ----------------------------------------------------------------------- |
| domain   | domain of your Iserv with trailing 'https://' and ending slash '/'      |
| url      | location of the caldav calendar with trailing 'https://' and ending '/' |
| tasklist | the name for the tasklist (choose one on your own)                      |
| username | Iserv username                                                          |
| password | should be obvious                                                       |

Then, you have only to start the script with

```
python3 get-tasks.py
```

and get all your tasks saved on the caldav server.

## Reason

You can have darkmode - I should'nt have to say more.

# TODO

- [x] Download Tasklist
- [x] Upload to CalDAV server
- [x] Ignore done tasks
- [x] Save whole information
- [ ] Meaningful README
