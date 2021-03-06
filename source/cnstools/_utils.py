import time
import sys
import os
import threading
import json
import inspect
#hello

def safe_print(content,print_id=None):
    sys.stdout.flush()
    if not hasattr(safe_print, "print_id"): 
        safe_print.print_id = print_id
    elif safe_print.print_id != print_id:
        sys.stderr.write("\n")
        safe_print.print_id = print_id
    sys.stderr.write(str(content)+"\n")
    sys.stdout.flush()

def header_print(header,h_type=0):
    wall = lambda char: char*70
    if h_type==0:
        safe_print("\n%s\n %s \n%s" % (wall(" "),header,wall("~")))
    if h_type==1:
        safe_print("\n%s\n %s \n%s" % (wall("~"),header,wall("~")))
    if h_type==2:
        safe_print("\n%s\n %s \n%s" % (wall("="),header,wall("~")))
    if h_type==3:
        safe_print("\n%s\n %s \n%s" % (wall("="),header,wall("=")))

def get_docstring_info(function,param=None):
    ds = inspect.getdoc(function)
    if param!=None:
        ds_dl = ds.split(":returns")[0]
        list = ds_dl.split(":param")[1:]
        for section in list:
            info,doc = section.split(":")
            info = info.split(" ")
            if info[-1]==param:
                return doc.strip()
        return None
    return ds.split("\n\n")[0].strip()


def create_path(path,name=None,extension=None,overwrite=True):
    try:
        os.makedirs(path)
    except OSError:
        if not os.path.isdir(path):
            raise

    if not path.endswith("/"):
        path+="/"
    if name:
        path+=name
    if extension:
        if not extension.startswith("."):
            path+="."
        path+=extension

    if (not overwrite) and os.path.exists(path):
        raise ValueError("You provided an existing path but asked not to overwrite!")

    return path

def reduce_gaps(seqlist):
    lists = [list(seq) for seq in seqlist]
    for i in range(len(lists[0])-1,-1,-1):
        if all(seq[i]=="-" for seq in lists):
            for seq in lists: del seq[i]
    return ["".join(seq) for seq in lists]

class JSON_saver(object):
    """docstring for JSON_saver"""
    def __init__(self, path):
        self.path = path
    def save(self,data):
        with open(self.path,'w') as out:
            json.dump(data,out,sort_keys=True,indent=4)
        return self

class Progress_tracker():
    def __init__(self,name,size):
        self.name = name
        self.size = size if size!=0 else 1
        self.estimate_on = True
        self.status_message = None
        self.steps = 0
        self.progress = 0
        self.start_time = None
        self.started = False
        self.is_done = False

    def start(self):
        if not self.started:
            self.start_time = time.time()
            self.started = True
        return self

    def done(self):
        self.steps = self.size
        self.ab = False
        self.display()
        self.is_done = True
        return self

    def step(self,size=1):
        if not self.started:
            self.start() 
        self.steps+=size
        return self

    def estimate(self,estimate_on):
        self.estimate_on = estimate_on
        return self

    def auto_display(self,rate=1):
        if rate>0:
            self.ad = True
            self.ad_rate = rate
            self.ad_next = time.time()
            self._auto_display()
        else:
            self.ad = False
        return self

    def _auto_display(self):
        if not self.is_done:
            if self.started:
                    self.display()
            if self.ad and self.steps<=self.size:
                self.ad_next = self.ad_next+self.ad_rate
                new_thread = threading.Timer(self.ad_next-time.time(),self._auto_display)
                new_thread.daemon = True
                new_thread.start()

    def display(self):

        curr_time = time.time()
        if not self.started: self.start_time = curr_time
        time_elapsed = curr_time-self.start_time

        self.progress = float(self.steps)/float(self.size)

        precentComplete = int((self.progress*100))
        tRemain = self._parseTime(int(time_elapsed/self.progress*(1-self.progress))) if self.progress!=0 else self._parseTime(float('inf'))

        write_string = "%s:" % self.name#"\033[F\x1b[2K%s:" % self.name
        write_string_size = len(self.name)+1
        write_string+= " "*(8*4-write_string_size)
        write_string_size = 8*4

        if self.steps<self.size:
            write_string += '\x1b[33m%s%s\x1b[0m' % (precentComplete, '%')
            write_string_size += len(str(precentComplete))+1
            if self.estimate_on:
                write_string+= " "*(8*5-write_string_size)
                write_string_size = 8*5
                rem = '(%s remaining)' % (tRemain)
                write_string+= rem
                write_string_size += len(rem)
            if self.status_message:
                write_string+= " "*(8*8-write_string_size)
                write_string_size = 8*8
                write_string+= '\x1b[34m[%s]\x1b[0m' % self.status_message
                write_string_size+=len(self.status_message)+2
        else:
            write_string += '\x1b[32mFinished\x1b[0m'

        safe_print(write_string,self)
        return self

    def _parseTime(self,seconds):
        if seconds < 60: return str(seconds//1)+"s"
        elif seconds == float('inf'): return "???"
        elif seconds < 3600: return str(seconds//60)+"m."+self._parseTime(seconds%60)
        elif seconds < 86400: return str(seconds//3600)+"h."+self._parseTime(seconds%3600)
        else: return str(seconds//86400)+"d."+self._parseTime(seconds%86400)

    def status(self, status_message=None):
        if not status_message: 
            status_message=None
        self.status_message = status_message
        self.display()
        return self

