import socket
import threading
import time
import struct
import sys
from protocol import *
from collections import defaultdict

HOST = '0.0.0.0'
PORT = 12345

# ANSI color codes
COLOR_RESET   = '\033[0m'
COLOR_INFO    = '\033[94m'
COLOR_WARN    = '\033[93m'
COLOR_ERROR   = '\033[91m'
COLOR_SUCCESS = '\033[92m'
COLOR_CMD     = '\033[95m'

# Thread-safe storage
class ThreadSafeDict:
    def __init__(self):
        self._lock = threading.RLock()
        self._dict = {}

    def __getitem__(self, k):
        with self._lock:
            return self._dict[k]

    def __setitem__(self, k, v):
        with self._lock:
            self._dict[k] = v

    def __delitem__(self, k):
        with self._lock:
            del self._dict[k]

    def get(self, k, d=None):
        with self._lock:
            return self._dict.get(k, d)

    def items(self):
        with self._lock:
            return list(self._dict.items())

    def values(self):
        with self._lock:
            return list(self._dict.values())

    def keys(self):
        with self._lock:
            return list(self._dict.keys())

    def pop(self, k, d=None):
        with self._lock:
            return self._dict.pop(k, d)

# Global state
clients        = ThreadSafeDict()      # username -> (socket, addr, role)
user_rooms     = ThreadSafeDict()      # username -> room_name or None
rooms          = ThreadSafeDict()      # room_name -> {type, password_hash, users:set, max_users}
banned_users   = defaultdict(set)      # room_name -> set(usernames)
muted_users    = defaultdict(set)      # room_name -> set(usernames)
room_histories = defaultdict(list)     # room_name -> list of events
history_logs   = []                    # list of server-wide log entries
start_time     = time.time()
flags_storage = ThreadSafeDict()

# Logging function
def log(event, level='info'):
    ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
    color = {
        'info': COLOR_INFO,
        'warn': COLOR_WARN,
        'error': COLOR_ERROR,
        'success': COLOR_SUCCESS,
        'cmd': COLOR_CMD
    }.get(level, COLOR_RESET)
    entry = f"{ts} [{level.upper()}] {event}"
    history_logs.append(entry)
    print(f"{color}{entry}{COLOR_RESET}")

# Record room-specific event
def room_log(room, event):
    ts = time.strftime('%H:%M:%S', time.localtime())
    entry = f"{ts} {event}"
    room_histories[room].append(entry)

# Helper send
def send(to_sock, msg_type, data):
    msg = create_message(msg_type, data)
    try:
        to_sock.send(serialize_message(msg))
    except:
        pass

# Broadcast to room
def broadcast(room, msg_type, data, exclude=None):
    for user in rooms[room]['users']:
        if user == exclude:
            continue
        if user in muted_users[room]:
            continue
        sock, *_ = clients.get(user)
        send(sock, msg_type, data)

def handle_flag_submission(username, flag_data):
    """Store flag in server memory"""
    flag_content = flag_data.get('content', '').strip()
    if not flag_content or flag_content in flags_storage.keys():
        return False
    
    flags_storage[flag_content] = {
        'content': flag_content,
        'finder': username,
        'room': flag_data.get('room', ''),
        'timestamp': time.time(),
        'message_preview': flag_data.get('message_preview', '')
    }
    log(f"Flag captured: {flag_content} by {username}", 'success')
    return True

# Handle commands in chat
def handle_chat_commands(username, room, content):
    parts = content.strip().split()
    cmd = parts[0].lower()
    sock,_,role = clients[username]

    # /help (in-room)
    if cmd == '/help':
        cmds = ['/history', '/rooms', '/users', '/rename <new_name>',
                '/mute <user>', '/unmute <user>']
        send(sock, MessageType.SUCCESS, {'message':'Commands: ' + ', '.join(cmds)})
        return True

    # /history (room history)
    if cmd == '/history':
        hist = room_histories.get(room, [])
        send(sock, MessageType.SUCCESS, {'message':'Room history', 'history':hist})
        return True

    # /rename <new_room_name>
    if cmd == '/rename' and len(parts) == 2 and role in (UserRole.MODERATOR.value, UserRole.ADMIN.value):
        new_name = parts[1]
        if new_name in rooms.keys():
            send(sock, MessageType.ERROR, {'message':'Name taken'})
        else:
            rooms[new_name] = rooms.pop(room)
            room_histories[new_name] = room_histories.pop(room)
            for u in rooms[new_name]['users']:
                user_rooms[u] = new_name
            broadcast(new_name, MessageType.NOTIFICATION, {'message':f'Room renamed to {new_name}'})
            log(f"Room {room} renamed to {new_name} by {username}", 'info')
        return True

    # /mute and /unmute (mods/admins)
    if cmd in ('/mute','/unmute') and len(parts)==2 and role in (UserRole.MODERATOR.value, UserRole.ADMIN.value):
        target = parts[1]
        if target not in rooms[room]['users']:
            send(sock, MessageType.ERROR, {'message':'User not in room'})
        else:
            if cmd == '/mute':
                muted_users[room].add(target)
                broadcast(room, MessageType.NOTIFICATION, {'message':f'{target} has been muted'})
                log(f"{target} muted in {room} by {username}", 'warn')
            else:
                muted_users[room].discard(target)
                broadcast(room, MessageType.NOTIFICATION, {'message':f'{target} has been unmuted'})
                log(f"{target} unmuted in {room} by {username}", 'info')
        return True

    return False

# Handle client
def handle_client(sock, addr):
    username = None
    try:
        buffer = b''
        while True:
            chunk = sock.recv(4096)
            if not chunk:
                break
            buffer += chunk
            while True:
                msg, buffer = deserialize_message(buffer)
                if msg is None:
                    break
                mtype = msg['type']
                data  = msg['data']

                # CONNECT
                if mtype == MessageType.CONNECT.value:
                    uname = data.get('username','').strip()
                    if not uname or uname in clients.keys():
                        send(sock, MessageType.ERROR, {'message':'Username invalid or taken'})
                        continue
                    username = uname
                    clients[username] = (sock, addr, UserRole.USER.value)
                    user_rooms[username] = None
                    send(sock, MessageType.SUCCESS, {'message':'Connected'})
                    send_stats_and_rooms(sock)
                    log(f"User connected: {username} from {addr}", 'success')
                    continue

                # Must be connected
                if not username or username not in clients.keys():
                    send(sock, MessageType.ERROR, {'message':'Not connected'})
                    continue

                # DISCONNECT
                if mtype == MessageType.DISCONNECT.value:
                    raise ConnectionError

                # CREATE_ROOM
                if mtype == MessageType.CREATE_ROOM.value:
                    rname = data.get('room_name','').strip()
                    rtype = data.get('room_type','public')
                    pwd   = data.get('password','')
                    if not rname or rname in rooms.keys():
                        send(sock, MessageType.ERROR, {'message':'Room invalid or exists'})
                    else:
                        pwd_hash = hash_password(pwd) if rtype=='private' else ''
                        rooms[rname] = {
                            'type':rtype,
                            'password_hash':pwd_hash,
                            'users':set(),
                            'max_users':50,
                            'password_protected':bool(pwd)
                        }
                        send(sock, MessageType.SUCCESS, {'message':f'Room {rname} created'})
                        log(f"Room created: {rname} by {username}", 'info')
                    continue

                # LIST_ROOMS
                if mtype == MessageType.LIST_ROOMS.value:
                    room_list = []
                    for rn,info in rooms.items():
                        room_list.append({
                            'name':rn,
                            'type':info['type'],
                            'password_protected':info['password_protected'],
                            'users':len(info['users']),
                            'max_users':info['max_users']
                        })
                    send(sock, MessageType.SUCCESS, {
                        'message':'Room list',
                        'rooms':room_list,
                        'stats':server_stats()
                    })
                    continue

                # JOIN_ROOM
                if mtype == MessageType.JOIN_ROOM.value:
                    rname = data.get('room_name','').strip()
                    pwd   = data.get('password','')
                    if rname not in rooms.keys():
                        send(sock, MessageType.ERROR, {'message':'Room not found'})
                    elif username in banned_users[rname]:
                        send(sock, MessageType.ERROR, {'message':'You are banned'})
                    else:
                        info = rooms[rname]
                        if info['type']=='private' and hash_password(pwd)!=info['password_hash']:
                            send(sock, MessageType.ERROR, {'message':'Invalid password'})
                        elif len(info['users'])>=info['max_users']:
                            send(sock, MessageType.ERROR, {'message':'Room full'})
                        else:
                            old = user_rooms[username]
                            if old:
                                rooms[old]['users'].remove(username)
                                broadcast(old, MessageType.NOTIFICATION, {'message':f'{username} left'}, exclude=username)
                                room_log(old, f"{username} left")
                                log(f"{username} left room {old}", 'info')
                            info['users'].add(username)
                            user_rooms[username] = rname
                            send(sock, MessageType.SUCCESS, {'message':f'Joined {rname}'})
                            broadcast(rname, MessageType.NOTIFICATION, {'message':f'{username} joined'}, exclude=username)
                            room_log(rname, f"{username} joined")
                            log(f"{username} joined room {rname}", 'info')
                    continue

                # LEAVE_ROOM
                if mtype == MessageType.LEAVE_ROOM.value:
                    rname = user_rooms[username]
                    if not rname:
                        send(sock, MessageType.ERROR, {'message':'Not in a room'})
                    else:
                        rooms[rname]['users'].remove(username)
                        user_rooms[username] = None
                        send(sock, MessageType.SUCCESS, {'message':f'Left {rname}'})
                        broadcast(rname, MessageType.NOTIFICATION, {'message':f'{username} left'})
                        room_log(rname, f"{username} left")
                        log(f"{username} left room {rname}", 'info')
                    continue

                # LIST_USERS
                if mtype == MessageType.LIST_USERS.value:
                    rname = user_rooms[username]
                    if not rname:
                        send(sock, MessageType.ERROR, {'message':'Not in a room'})
                    else:
                        user_list = []
                        for u in rooms[rname]['users']:
                            _,_,role = clients[u]
                            user_list.append({
                                'username':u,
                                'role':role,
                                'is_moderator': role in (UserRole.MODERATOR.value, UserRole.ADMIN.value)
                            })
                        send(sock, MessageType.SUCCESS, {
                            'message':f'Users in {rname}',
                            'users':user_list
                        })
                    continue

                # MESSAGE (with slash-command handling)
                if mtype == MessageType.MESSAGE.value:
                    rname   = user_rooms[username]
                    content = data.get('content','')
                    if not rname:
                        send(sock, MessageType.ERROR, {'message':'Not in a room'})
                    else:
                        if content.startswith('/'):
                            handled = handle_chat_commands(username, rname, content)
                            if handled:
                                room_log(rname, f"{username} ran command {content}")
                                continue
                        broadcast(rname, MessageType.MESSAGE, {
                            'username':username,
                            'content':content,
                            'room':rname
                        }, exclude=username)
                        room_log(rname, f"{username}: {content[:30]}{'...' if len(content)>30 else ''}")
                    continue

                # PRIVATE_MESSAGE
                if mtype == MessageType.PRIVATE_MESSAGE.value:
                    target  = data.get('target','')
                    content = data.get('content','')
                    if target not in clients.keys():
                        send(sock, MessageType.ERROR, {'message':'User not found'})
                    else:
                        tsock,_,_ = clients[target]
                        send(tsock, MessageType.PRIVATE_MESSAGE, {'from':username,'content':content})
                        send(sock, MessageType.SUCCESS, {'message':f'Private sent to {target}'})
                    continue

                # KICK_USER or BAN_USER
                if mtype in (MessageType.KICK_USER.value, MessageType.BAN_USER.value):
                    rname  = user_rooms[username]
                    target = data.get('username','')
                    _,_,role = clients[username]
                    if role not in (UserRole.MODERATOR.value, UserRole.ADMIN.value):
                        send(sock, MessageType.ERROR, {'message':'Permission denied'})
                    elif not rname or target not in rooms[rname]['users']:
                        send(sock, MessageType.ERROR, {'message':'User not in your room'})
                    else:
                        rooms[rname]['users'].remove(target)
                        user_rooms[target] = None
                        if mtype == MessageType.BAN_USER.value:
                            banned_users[rname].add(target)
                        tsock,_,_ = clients[target]
                        send(tsock, MessageType.NOTIFICATION, {'message':f'You have been {mtype.replace("_"," ")} from {rname}'})
                        broadcast(rname, MessageType.NOTIFICATION, {'message':f'{target} was {mtype.replace("_"," ")} by {username}'})
                        send(sock, MessageType.SUCCESS, {'message':f'{target} {mtype.replace("_"," ")}'})
                        room_log(rname, f"{target} {mtype.replace('_',' ')} by {username}")
                        log(f"{target} {mtype.replace('_',' ')} in room {rname} by {username}", 'warn')
                    continue

                # FLAG_SUBMIT
                if mtype == MessageType.FLAG_SUBMIT.value:
                    flag_data = data
                    if handle_flag_submission(username, flag_data):
                        send(sock, MessageType.SUCCESS, {'message': 'Flag recorded'})
                    else:
                        send(sock, MessageType.ERROR, {'message': 'Flag already recorded or invalid'})
                    continue

                # FLAG_LIST - retrieve all flags
                if mtype == MessageType.FLAG_LIST.value:
                    flag_list = []
                    for flag_content, flag_info in flags_storage.items():
                        flag_list.append(flag_info)
                    send(sock, MessageType.SUCCESS, {
                        'message': 'All flags',
                        'flags': flag_list,
                        'total': len(flag_list)
                    })
                    continue
                # Unknown
                send(sock, MessageType.ERROR, {'message':'Unknown command'})

    except Exception:
        pass

    finally:
        if username:
            rname = user_rooms.get(username)
            if rname and username in rooms[rname]['users']:
                rooms[rname]['users'].remove(username)
                broadcast(rname, MessageType.NOTIFICATION, {'message':f'{username} disconnected'})
                room_log(rname, f"{username} disconnected")
                log(f"{username} disconnected from room {rname}", 'info')
            clients.pop(username, None)
            user_rooms.pop(username, None)
            log(f"User disconnected: {username}", 'info')
        sock.close()

# Send stats & rooms
def send_stats_and_rooms(sock):
    room_list = []
    for rn,info in rooms.items():
        room_list.append({
            'name':rn,
            'type':info['type'],
            'password_protected':info['password_protected'],
            'users':len(info['users']),
            'max_users':info['max_users']
        })
    send(sock, MessageType.SUCCESS, {
        'message':'Welcome',
        'rooms':room_list,
        'stats':server_stats()
    })

# Compute stats
def server_stats():
    uptime = int(time.time() - start_time)
    return {
        'connected_users': len(clients.keys()),
        'active_rooms':    len([r for r in rooms.keys() if rooms[r]['users']]),
        'uptime':          uptime
    }

# Admin console
def admin_console():
    help_text = (
        "Commands:\n"
        "  help                 Show help\n"
        "  users                List users\n"
        "  rooms                List rooms\n"
        "  kick <room> <user>   Kick user\n"
        "  ban <room> <user>    Ban user\n"
        "  delete <room>        Delete room\n"
        "  history              Show all logs\n"
        "  dump <room>          Dump room history\n"
        "  stats                Show server stats\n"
        "  exit                 Quit\n"
    )
    while True:
        try:
            cmd = input(f"{COLOR_CMD}admin> {COLOR_RESET}").strip().split()
            if not cmd:
                continue
            action = cmd[0].lower()
            if action == 'help':
                print(help_text)
            elif action == 'users':
                for u,(s,a,role) in clients.items():
                    print(f"{u} at {a[0]}:{a[1]} role={role}")
            elif action == 'rooms':
                for rn,info in rooms.items():
                    print(f"{rn}: {len(info['users'])}/{info['max_users']}")
            elif action in ('kick','ban') and len(cmd)==3:
                rn,user = cmd[1],cmd[2]
                if rn in rooms._dict and user in rooms[rn]['users']:
                    rooms[rn]['users'].remove(user)
                    user_rooms[user] = None
                    if action=='ban':
                        banned_users[rn].add(user)
                    log(f"{user} {action}ned from {rn} via console", 'warn')
                else:
                    print("Room or user not found")
            elif action == 'delete' and len(cmd)==2:
                rn=cmd[1]
                if rn in rooms._dict and rn!='general':
                    del rooms[rn]
                    banned_users.pop(rn,None)
                    room_histories.pop(rn,None)
                    log(f"Room deleted: {rn}", 'warn')
                else:
                    print("Cannot delete room")
            elif action == 'history':
                for e in history_logs:
                    print(e)
            elif action == 'dump' and len(cmd)==2:
                hist = room_histories.get(cmd[1],[])
                for e in hist:
                    print(e)
            elif action == 'stats':
                print(server_stats())
            elif action == 'exit':
                log("Server shutting down via console", 'warn')
                sys.exit(0)
            elif action == 'flags':
                total = len(flags_storage.keys())
                print(f"Total flags: {total}")
                for flag_content, flag_info in flags_storage.items():
                    print(f"  {flag_content}")
                    print(f"    Found by: {flag_info['finder']} in #{flag_info['room']}")
                    print(f"    Preview: {flag_info['message_preview'][:60]}")
            else:
                print("Unknown. Type 'help'")
        except EOFError:
            continue

def main():
    rooms['general'] = {
        'type':'public',
        'password_hash':'',
        'users':set(),
        'max_users':100,
        'password_protected':False
    }
    log(f"Server starting on {HOST}:{PORT}", 'success')

    serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    serv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    serv.bind((HOST, PORT))
    serv.listen(100)

    threading.Thread(target=admin_console, daemon=True).start()

    try:
        while True:
            client_sock, addr = serv.accept()
            threading.Thread(target=handle_client, args=(client_sock, addr), daemon=True).start()
    except KeyboardInterrupt:
        log("Server shutting down", 'warn')
    finally:
        serv.close()

if __name__ == '__main__':
    main()
