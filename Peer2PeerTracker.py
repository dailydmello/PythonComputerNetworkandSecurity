import socket, sys, threading, json,time,optparse,os

def validate_ip(s):
    a = s.split('.')
    if len(a) != 4:
        return False
    for x in a:
        if not x.isdigit():
            return False
        i = int(x)
        if i < 0 or i > 255:
            return False
    return True

def validate_port(x):
    if not x.isdigit():
        return False
    i = int(x)
    if i < 0 or i > 65535:
            return False
    return True

class Tracker(threading.Thread):
    def __init__(self, port, host='0.0.0.0'):
        threading.Thread.__init__(self)
        self.port = port
        self.host = host
        self.BUFFER_SIZE = 8192
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.users = {} # current connections  self.users[(ip,port)] = {'exptime':}
        self.files = {} #{'ip':,'port':,'mtime':}
        self.lock = threading.Lock()
        try:
            #Bind to address and port
            self.server.bind((self.host,self.port))
        except socket.error:
            print('Bind failed %s' % (socket.error))
            sys.exit()
            
        #listen for connections
        self.server.listen(5)

    def check_user(self):
        #checking users are alive
        for user,exptime in self.users.iteritems(): 
            if (exptime < time.time()): #if connection timed out delete user
                del self.users[user]
                
                for fname in self.files.iteritems():
                    if ((user[0] == fname['ip']) and (user[1] == fname['port'])):
                        del self.files[fname]
        
    #Ensure sockets are closed on disconnect
    def exit(self):
        self.server.close()

    def run(self):
        print('Waiting for connections on port %s' % (self.port))
        while True:

            conn, addr = self.server.accept()
            #accept incoming connection and create a thread for receiving messages from FileSynchronizer
            threading.Thread(target=self.proces_messages, args=(conn, addr)).start()

    def proces_messages(self, conn, addr):
        conn.settimeout(180.0)
        print 'Client connected with ' + addr[0] + ':' + str(addr[1])
        while True:
            #recive data
            data = ''
            while True:
                part = conn.recv(self.BUFFER_SIZE)
                data = data + part
                if len(part) < self.BUFFER_SIZE:
                    break
            #load incoming data into a doctionary
            data_dic = json.loads(data)
            print("this is in the dictionary:")
            print(data_dic)

            #check if its an initial message sent by synchronizer
            isInitMsg = 'files' in data_dic

            #if initial message, open 3min window
            if(isInitMsg):
                self.users[(self.host,data_dic['port'])] = time.time() + 180

                #if filename sent by 2 synchronizers is the same compare mtime and keep the file with the larger mtime
                #iterate through list of dictionarys 
                for i in data_dic['files']:
                    #check self.files for same file name as file in data_dic
                    if self.files.has_key(i['name']):
                        print('A file with the same name has arrived')
                        #print(i['mtime'])
                        #print(self.files[i['name']]['mtime'])
                        if i['mtime'] > self.files[i['name']]['mtime']:
                            print("mtime is indeed greater therefore update")
                            self.files[i['name']] = {'ip':self.host,'port':data_dic['port'],'mtime':i['mtime']}

                    else:
                        self.files[i['name']] = {'ip':self.host, 'port':data_dic['port'],'mtime':i['mtime']}

            print("this is in self")
            print(self.files)

            response_msg = json.dumps(self.files)
            conn.sendall(response_msg)

        conn.close() # Close

        self.check_user()

if __name__ == '__main__':
    parser = optparse.OptionParser(usage="%prog ServerIP ServerPort")
    options, args = parser.parse_args()
    if len(args) < 1:
        parser.error("No ServerIP and ServerPort")
    elif len(args) < 2:
        parser.error("No  ServerIP or ServerPort")
    else:
        if validate_ip(args[0]) and validate_port(args[1]):
            server_ip = args[0]
            server_port = int(args[1])
        else:
            parser.error("Invalid ServerIP or ServerPort")
    tracker = Tracker(server_port,server_ip)
    tracker.start()
