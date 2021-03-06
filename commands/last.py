# Copyright 2011-2013 orabot Developers
#
# This file is part of orabot, which is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Last Command Module: seen, activity, message, game
"""

import sqlite3
import re
import time
import datetime

def last(self, user, channel):
    command = (self.command).split()
    usage = "Usage: " + self.command_prefix + "last {seen|activity|message|game} args"
    if ( len(command) == 1 ):
        self.send_reply( (usage), user, channel )
        return
    if ( command[1].lower() == 'seen' ):
        if ( len(command) == 3):
            seen(self, user, channel, command[2])
        else:
            self.send_reply( ("Usage: " + self.command_prefix + "last seen <username>"), user, channel )
    elif ( command[1].lower() == 'activity' ):
        if ( len(command) >= 3 and len(command) <= 4 ):
            activity(self, user, channel, command[2:])
        else:
            self.send_reply( ("Usage: " + self.command_prefix + "last activity [-<amount of records>] username"), user, channel )
    elif ( command[1].lower() == 'message' ):
        if ( len(command) >= 2 and len(command) <= 4 ):
            message(self, user, channel, command[2:])
        else:
            self.send_reply( ("Usage: " + self.command_prefix + "last message [-<amount of records>] username"), user, channel )
    elif ( command[1].lower() == 'mention' ):
        if ( len(command) == 3 ):
            mention(self, user, channel, command[2:])
        else:
            self.send_reply( ("Usage: " + self.command_prefix + "last mention word"), user, channel )
    elif ( command[1].lower() == 'game' ):
        if ( len(command) >= 2 and len(command) <= 3 ):
            if ( len(command) == 2 ):
                arg = ''
            else:
                arg = command[2]
            game(self, user, channel, arg)
        else:
            self.send_reply( ("Usage: " + self.command_prefix + "last game [-<amount of records>]"), user, channel )
    else:
        self.send_reply( (usage), user, channel )

def seen_time( last_time, current ):
    last_time = time.mktime(time.strptime( last_time, '%Y-%m-%d-%H-%M-%S'))
    current = time.mktime(time.strptime( current, '%Y-%m-%d-%H-%M-%S'))
    difference = current - last_time
    result = str(datetime.timedelta(seconds = difference))
    result = result.split(', ')
    if ( len(result) == 1 ):
        days = ''
        timest = result[0]
    else:
        days = ' ' + result[0]
        timest = result[1]
    timest = timest.split(':')
    result_string = days
    for i in range(len(timest)-1):
        if int(timest[i]) != 0:
            if ( timest[i] == '1' ):
                end = ''
            else:
                end = 's'
            if i == 0:
                st = 'hour'
            elif i == 1:
                st = 'minute'
            st = st + end
            result_string = result_string + ' ' + str(int(timest[i])) + ' ' + st
    return result_string

def time_result(last_time):
    current = time.strftime('%Y-%m-%d-%H-%M-%S')
    seen_result = seen_time( last_time, current )
    if ( seen_result == '' ):
        result = ' just now'
    else:
        result = seen_result + ' ago'
    return result

def seen(self, user, channel, request_user):
    
    """
    Shows when user was last seen on the channel
    """
    if ( "'" in request_user ):
        self.send_reply( ("Error! No such user in my database"), user, channel)
        return
    conn, cur = self.db_data()
    if re.search("^#", channel):
        user_nicks = self.get_names(channel)
        if request_user in user_nicks:  #reciever is on the channel right now
            self.send_reply( ("User is online!"), user, channel)
            cur.close()
            return
        else:
            sql = """SELECT user,date,state FROM users
                    WHERE user = '"""+request_user+"""'
            """
            cur.execute(sql)
            records = cur.fetchall()
            conn.commit()
            if ( len(records) == 0 ):   #user not found
                self.send_reply( ("Error! No such user in my database"), user, channel)
            else:
                last_time = records[0][1]
                state = records[0][2]
                if state == True:
                    self.send_reply( ("User is somewhere online on IRC Network!"), user, channel)
                    cur.close()
                    return
                if ( last_time == None or last_time == '' ):
                    self.send_reply( ("Sorry, I don't have any record of when user left"), user, channel)
                else:
                    result = time_result(last_time)
                    self.send_reply( (request_user + " was last seen" + result), user, channel)
    else:
        self.send_message_to_channel( ("You can use `]last seen` only on a channel"), user)
    cur.close()

def activity(self, user, channel, command_request):
    
    """
    Shows last user's activity (joins, quits, etc)
    """
    
    conn, cur = self.db_data()
    usage = "Usage: " + self.command_prefix + "last activity [-<amount of records>] username"
    if ( len(command_request) == 1 ):
        username = command_request[0]
        amount_records = '10'
    elif ( len(command_request) == 2 ):
        username = command_request[1]
        if ( command_request[0].startswith('-') ):
            amount_records = command_request[0][1:]
            try:
                trash = int(amount_records)
            except:
                self.send_reply( (usage), user, channel )
                cur.close()
                return
        else:
            self.send_reply( (usage), user, channel )
            cur.close()
            return
    if ( int(amount_records) > 30 ):
        amount_records = '30'
    if ( "'" in username ):
        self.send_notice("User is not found", user)
        cur.close()
        return
    sql = """SELECT act,date_time,channel FROM activity
            WHERE user = '""" + username + """'
            ORDER BY uid DESC
            LIMIT """ + amount_records + """
    """
    cur.execute(sql)
    records = cur.fetchall()
    conn.commit()
    if ( len(records) == 0 ):
        self.send_notice("No records of user's activity", user)
        cur.close()
        return
    else:
        for i in range(len(records)):
            if ( records[i][0] == 'join' ):
                event = "Join"
                chan = ' ' + records[i][2]
            elif ( records[i][0] == 'part' ):
                event = "Part"
                chan = ' ' + records[i][2]
            elif ( records[i][0] == 'quit' ):
                event = "Quit"
                chan = ''
            elif ( records[i][0] == 'nick' ):
                event = "Change nick"
                chan = ''
            elif ( records[i][0] == 'kick' ):
                event = "Kicked from"
                chan = ' ' + records[i][2]
            result = time_result(records[i][1])
            message = event + chan + ":" + result
            self.send_notice(message, user)
    cur.close()

def message(self, user, channel, command_request):
    
    """
    Shows last user's messages
    """
    
    conn, cur = self.db_data()
    usage = "Usage: " + self.command_prefix + "last message [-<amount of records>] [username]"

    def messages_from_channel(self, user, channel, usage, cur, conn, command_request):
        amount_records = command_request[0][1:]
        try:
            amount_records = str(int(amount_records) + 1)
        except:
            self.send_reply( (usage), user, channel )
            cur.close()
            return
        sql = """SELECT message,date_time,channel,user FROM messages
                WHERE channel = '"""+channel+"""'
                ORDER BY uid DESC
                LIMIT """ + amount_records + """
        """
        cur.execute(sql)
        records = cur.fetchall()
        conn.commit()
        if ( len(records) == 0 ):
            self.send_notice("No records for " + channel, user)
            return
        else:
            del records[0]
            for i in range(len(records)):
                result = time_result(records[i][1])
                message = records[i][3] + result + " @ " + records[i][2] + " : " + records[i][0]
                self.send_notice(message, user)

    if ( len(command_request) == 0 ):
        messages_from_channel(self, user, channel, usage, cur, conn, ['-10'])
        return
    if ( len(command_request) == 1 ):
        if ( command_request[0].startswith('-') ):
            messages_from_channel(self, user, channel, usage, cur, conn, command_request)
            return
        else:
            username = command_request[0]
            amount_records = '10'
    elif ( len(command_request) == 2 ):
        username = command_request[1]
        if ( command_request[0].startswith('-') ):
            amount_records = command_request[0][1:]
            try:
                amount_records = str(int(amount_records) + 1)
            except:
                self.send_reply( (usage), user, channel )
                cur.close()
                return
        else:
            self.send_reply( (usage), user, channel )
            cur.close()
            return
    if ( int(amount_records) > 30 ):
        amount_records = '30'
    sql = """SELECT message,date_time,channel FROM messages
            WHERE user = '""" + username + """'
            ORDER BY uid DESC
            LIMIT """ + amount_records + """
    """
    cur.execute(sql)
    records = cur.fetchall()
    conn.commit()
    if ( len(records) == 0 ):
        self.send_notice("No records of user's messages", user)
        cur.close()
        return
    else:
        del records[0]
        for i in range(len(records)):
            result = time_result(records[i][1])
            message = username + result + " @ " + records[i][2] + " : " + records[i][0]
            self.send_notice(message, user)
    cur.close()

def game(self, user, channel, command_request):
    
    """
    Shows last started games
    """
    
    conn, cur = self.db_data()
    usage = "Usage: " + self.command_prefix + "last game [-<amount of records>]"
    if ( command_request == '' ):
        amount_records = '10'
    else:
        if ( command_request.startswith('-') ):
            amount_records = command_request[1:]
            try:
                trash = int(amount_records)
            except:
                self.send_reply( (usage), user, channel )
                cur.close()
                return
        else:
            self.send_reply( (usage), user, channel )
            cur.close()
            return
    if ( int(amount_records) > 30 ):
        amount_records = '30'
    sql = """SELECT name,players,date_time,version FROM games
            ORDER BY uid DESC
            LIMIT """ + amount_records + """
    """
    cur.execute(sql)
    records = cur.fetchall()
    conn.commit()
    if ( len(records) == 0 ):
        self.send_notice("No records of started games", user)
        cur.close()
        return
    else:
        for i in range(len(records)):
            result = time_result(records[i][2])
            if ( records[i][3] == '' ):
                ver = ' |'
            else:
                if ( re.search('.*{DEV_VERSION}', records[i][3]) ):
                    ver = 'DEV'
                else:
                    ver = records[i][3][-4:]
                ver = ' | ver: ' + ver + ' |'
            message = records[i][1] + " players" + ver + result + " | Name: " + records[i][0]
            self.send_notice(message, user)
    cur.close()

def mention(self, user, channel, command_request):
    
    """
    Shows last mentions of the word
    """
    
    conn, cur = self.db_data()
    usage = "Usage: " + self.command_prefix + "last mention word"

    word = command_request[0]
    sql = """SELECT message,date_time,channel,user FROM messages
            WHERE channel = '"""+channel+"""' AND upper(message) LIKE upper('%"""+word+"""%') AND user <> '"""+user+"""'
            ORDER BY uid DESC
            LIMIT 10
    """
    cur.execute(sql)
    records = cur.fetchall()
    conn.commit()
    if ( len(records) == 0 ):
        self.send_notice("No records with "+word, user)
        cur.close()
        return
    else:
        del records[0]
        for i in range(len(records)):
            result = time_result(records[i][1])
            message = records[i][3] + result + " @ " + records[i][2] + " : " + records[i][0]
            self.send_notice(message, user)
    cur.close()
