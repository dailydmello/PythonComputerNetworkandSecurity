
import socket, sys, threading, json,time,os,ssl
import os.path
import glob
import json
import optparse


#Validate the IP address of the correct format
def validate_ip(s):
    """
    Arguments:
    s -- dot decimal IP address in string

    Returns:
    True if valid; False otherwise
    """

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

#Validate the port number is in range [0, 2^16-1]
def validate_port(x):
    """
    Arguments:
    x -- port number

    Returns:
    True if valid; False, otherwise
    """

    if not x.isdigit():
        return False
    i = int(x)
    if i < 0 or i > 65535:
            return False
    return True


#Get file info in the local directory (subdirectories are ignored)
#NOTE: Exclude files with .so, .py, .dll suffixes
def get_file_info():
    """
    Return: a JSON array of {"name":file,"mtime":mtime}
    """
    files =[]
    for f in os.listdir('.'):
        filename,file_ext = os.path.splitext(f)
        if ( file_ext == '.txt'):
            fobj = {'name':f,'mtime':os.path.getmtime(f)}
            files.append(fobj)
    print files
response_msg = json.dumps(files)

#Check if a port is available
def check_port_avaliable(check_port):
    """
    Arguments:
    check_port -- port number

    Returns:
    True if valid; False otherwise
    """
    if str(check_port) in os.popen("netstat -na").read():
        return False
    return True

#Get the next available port by searching from initial_port to 2^16 - 1
#Hint: use check_port_avaliable() function
def get_next_avaliable_port(initial_port):
    """
    Arguments:
    initial_port -- the first port to check

    Return:
    port found to be available; False if no port is available.
    """

    if check_port_available(initial_port):
        return initial_port
    else:
        for x in range(intial_port,2**16):
            if(check_port_available(x)):
                return x
    return -1 #-1 means false

class FileSynchronizer(threading.Thread):
    def __init__(self, trackerhost,trackerport,port, host='0.0.0.0'):

        threading.Thread.__init__(self)
        #Port for serving file requests
        self.port = port
        self.host = host

        #Tracker IP/hostname and port
        self.trackerhost = trackerhost
        self.trackerport = trackerport

        self.BUFFER_SIZE = 8192

        #Create a TCP socket to communicate with tracker
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(180)

        #Store the message to be sent to tracker. Initialize to Init message
        #that contains port number and local file info.
        self.msg = {'port':self.port,'files':get_file_info()}

        #Create a TCP socket to serve file requests
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            self.server.bind((self.host, self.port))
        except socket.error:
            print('Bind failed %s' % (socket.error))
            sys.exit()
        self.server.listen(10)

    # Not currently used. Ensure sockets are closed on disconnect
    def exit(self):
        self.server.close()

    #Handle file request from a peer
    def process_message(self, conn,addr):
        """
        Arguments:
        self -- self object
        conn -- socket object for an accepted connection from a peer
        addr -- address bound to the socket of the accepted connection
        """

        #Step 1. read the file name contained in the request
        fname = ''
        while True:
            part = conn.recv(self.BUFFER_SIZE)
            fname = fname + part
            if len(part) < self.BUFFER_SIZE:
                break
            
        #Step 2. read the file from local directory (assuming binary file < 4MB)
        for f in os.listdir('.'):
            if (f==fname):
                file_obj = open(fname,"r")
                content=file_obj.read() 
            
        #Step 3. send the file to the requester
        conn.sendall(content)

    def run(self):
        self.client.connect((self.trackerhost,self.trackerport))
        t = threading.Timer(2, self.sync)
        t.start()
        print('Waiting for connections on port %s' % (self.port))
        while True:
            conn, addr = self.server.accept()
            threading.Thread(target=self.process_message, args=(conn,addr)).start()

    #Send Init or KeepAlive message to tracker, handle directory response message
    #and call self.syncfile() to request files from peers

    def sync(self):
        print 'connect to:'+self.trackerhost,self.trackerport
        #Step 1. send Init msg to tracker

        self.client.send(self.msg)

        #Step 2. receive a directory response message from tracker
        directory_response_message = ''

        while True:
            data = self.client.recv(self.BUFFER_SIZE)
            directory_response_message = directory_response_message + data
            if len(data) < self.BUFFER_SIZE:
                break

        try:
            files_dic = json.loads(data)
        except ValueError:
            print("files_dic works")
'''
        requests=[]
        

        for fname,meta in files_dic.iteritems():
            found = False
            for files in os.listdir('.'):
                if fname == files:
                    print("there is a file with the same name")
                    print os.path.getmtime(files)
                    found = True
                    if (files_dic[fname]['mtime']>os.path.getmtime(files)):
                        print("it has a higher mtime")
                        requests.append(fname)
                        print requests
                    else:
                        found = False
                        requests.append(files)
'''

        #check if files in cuurent synchronizer have the latest mtime
        
        #check for new files

        #Step 3. parse the directory response message. if it contains new or
        #more up-to-date files, request the files from the respective peers.
        #NOTE: compare the modified time of the files in the message and
        #that of local files of the same name.


        #Step 4. construct the KeepAlive message
        self.msg = {'port':self.port}

        #Step 4. start a timer
        t = threading.Timer(5, self.sync)
        t.start()

if __name__ == '__main__':
    #parse commmand line arguments
    parser = optparse.OptionParser(usage="%prog ServerIP ServerPort")
    options, args = parser.parse_args()
    if len(args) < 1:
        parser.error("No ServerIP and ServerPort")
    elif len(args) < 2:
        parser.error("No ServerIP or ServerPort")
    else:
        if validate_ip(args[0]) and validate_port(args[1]):
            tracker_ip = args[0]
            tracker_port = int(args[1])

        else:
            parser.error("Invalid ServerIP or ServerPort")

    #get the next available port
    synchronizer_port = get_next_avaliable_port(8000)
    synchronizer_thread = FileSynchronizer(tracker_ip,tracker_port,synchronizer_port)
    synchronizer_thread.start()
ffff
