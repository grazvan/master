# Korrector cleaner
# This script recovers files that have been encrypted with the Korrector Ransomware

import glob, os

# generate 9 test files file[i].txt
# each file will contain one char c, c =  [0..9]
def createFiles():
    for i in range(0, 9):
        fname = 'file'+str(i)+'.txt'
        print "writing ", fname
        f = open(fname, 'w')
        f.write(str(i)*500000)
        f.close()
        print "done."

# check the diff between the original file 
# and the infected one by XORing it with the initial value c, c = [0..9]
# print out the changed value and the postion 
def readFiles():
    for i in range(0, 9):
        fname = 'file'+str(i)+'.txt.korrektor'
        print "writing ", fname
        f = open(fname, 'rb')
        buffer = f.read()
        for j in range(0, len(buffer)):
            if ord(str(i)) ^ ord(buffer[j])  != 0:
                print 'Pos ',j, ', key:', ord(buffer[j])^ord(str(i))
        f.close()
        print "done."
        
# Result:
# ransome scheme uses a simple XOR with 0x5B every 2049 bytes for 11 times
# if (pos_file() mod 2049 == 0) and (counter <= 11):
#       b_new = b_old XOR 91
#       counter ++


# goes through the directories
# checks for files *.korrektor
# applies decryption scheme - removes damaged files

def cleanKorrektor():
    directory = 'C:\\'
    for root, dirs, f in os.walk(directory):
        for fname in f:
            if '.korrektor' in fname:
                print 'Cleaning ', fname,
                f = open(root+'\\'+fname, 'rb')
                c = open(root+'\\'+fname.replace('.korrektor',''), 'wb')
                data = f.read()
                cleanData = []
                counter = 0
                for i in range(0, len(data)):
                    if (i % 2049 == 0) and (counter<11):
                        counter = counter + 1
                        b =chr(ord(data[i]) ^ 91)
                        c.write(b)
                    else:
                        b = data[i]
                        c.write(b)
                f.close()
                c.close()
                os.remove(root+'\\'+fname)
                print ' done'

if __name__ == "__main__":
    cleanKorrektor()
