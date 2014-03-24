#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import sys
import subprocess as sub
import pickle
import argparse
from PIL import Image
import zlib
import hashlib
import tempfile
import shutil
from gi.repository import GExiv2
import time

VERSION="1.0"

# Calculates image hash for a single file. Just image data, ignore headers
def hashcalc(path,method="MD5"):
    if method=="identify":
        # Execute ImageMagick identify to get image signature
        p=sub.Popen(["identify",'-format','%#',path],stdout=sub.PIPE,stderr=sub.PIPE)
        output,errors=p.communicate()
        h=output[:-1]
    else:
        # All other methods involve opening the file using PIL
        try:
            im=Image.open(path)
            dat=im.tostring()
        except:
            sys.stderr.write("    *** Error opening file %s, file will be ignored\n" % path)
            return "ERR"
        # CRC should be faster than MD5 (al least in theory, actually it's about the same since the process is I/O bound)
        if method=="CRC":
            h=zlib.crc32(dat)
        else:
            # If unknown, use MD5
            md5=hashlib.new("MD5")
            md5.update(dat)
            h=md5.digest()
    return h

# Writes the specified dict to disk
def writecache(d):
    if not args.clean:
        cache=open(fsigs,'wb')
        pickle.dump(d,cache)
        cache.close()

# Deletes any temporary files
def rmtemps(dirlist):
    for d in dirlist:
        shutil.rmtree(d)

# Summarize image metadata in one line
def readmetadata(path):
    exif=GExiv2.Metadata(path)
    
    # Date
    date=[]
    if 'Exif.Photo.DateTimeOriginal' in exif:
        date.append(exif['Exif.Photo.DateTimeOriginal'])
    if 'Xmp.exif.DateTimeOriginal' in exif:
        date.append(exif['Xmp.exif.DateTimeOriginal'])
    #date.append(time.ctime(os.path.getmtime(path)))
    if len(date)>0:
        date=time.strftime("%d/%m/%Y %H:%M:%S",time.strptime(date[0],"%Y:%m:%d %H:%M:%S"))
    else:
        date=""
        
    # Orientation
    ori=exif.get('Exif.Image.Orientation',"?")
    
    # Tags
    tags=[]
    if 'Iptc.Application2.Keywords' in exif:
        tags.append(exif['Iptc.Application2.Keywords'])        
    if 'Xmp.dc.subject' in exif:
        tags+=exif['Xmp.dc.subject'].split(",")
    if 'Xmp.digiKam.TagsList' in exif:
        tags+=exif['Xmp.digiKam.TagsList'].split(",")
    if 'Xmp.MicrosoftPhoto.LastKeywordXMP' in exif:
        tags+=exif['Xmp.MicrosoftPhoto.LastKeywordXMP'].split(",")
    tags=[x.strip() for x in tags]
    tags=list(set(tags))
    tags.sort()
        
    # Title
    title=[]
    if 'Iptc.Application2.Caption' in exif:
        title.append(exif['Iptc.Application2.Caption'])
    if 'Xmp.dc.title' in exif:
        title.append(exif['Xmp.dc.title'])
    if 'Iptc.Application2.Headline' in exif:
        title.append(exif['Iptc.Application2.Headline'])
        
    # Software
    soft=""
    if 'Iptc.Application2.Program' in exif:
        soft=exif['Iptc.Application2.Program']
    
    sout="date: %s, orientation: %s" % (date,ori)
#    if soft!="":
#        sout+=", soft: %s" % soft
    if len(tags)>0:
        sout+=", tags:[%s]" % ",".join(tags)
        
    return sout

# The first, and only argument needs to be a directory
parser=argparse.ArgumentParser(description="Checks for duplicated images in a directory tree. Compares just image data, metadata is ignored, so physically different files may be reported as duplicates if they have different metadata (tags, titles, JPEG rotation, EXIF info...).")
parser.add_argument('directory',help="Base directory to check")
parser.add_argument('-1','--sameline',help="List each set of matches in a single line",action='store_true',required=False)
parser.add_argument('-d','--delete',help="Prompt user for files to preserve, deleting all others",action='store_true',required=False)
parser.add_argument('-c','--clean',help="Don't write to disk signatures cache",action='store_true',required=False)
parser.add_argument('-m','--method',help="Hash method to use. Default is MD5, but CRC might be faster on slower CPUs where process is not I/O bound. ImageMagick's utility identify can also be used if available",default="MD5",choices=["MD5","CRC","identify"],required=False)
parser.add_argument('--version', action='version', version='%(prog)s ' + VERSION)
args=parser.parse_args()

pwd=os.getcwd()

try:
    os.chdir(args.directory)
except:
    sys.stderr.write( "Directory %s doesn't exist\n" % args.directory)
    exit(1)

# Check if identify command is available
if args.method=="identify":
    try:
        sub.Popen("identify",stdout=sub.PIPE,stderr=sub.PIPE)
    except OSError:
        sys.stderr.write("identify command not found in path. Please install ImageMagick suite or use a different hashing method\n")
        exit(1)

# Extensiones admitidas (case insensitive)
extensiones=('jpg','jpeg')

# Diccionario con información sobre los ficheros
d={}
# Flag para saber si hay que volver a escribir la caché por cambios
modif=False

# Recuperar información de los ficheros generada previamente, si existe
rootDir='.'
fsigs='.signatures'
if os.path.isfile(fsigs):
    cache=open(fsigs,'rb')
    try:
        sys.stderr.write("Signatures cache detected, loading...\n")
        d=pickle.load(cache)
        cache.close()
	# Clean up non-existing entries
        sys.stderr.write("Cleaning up deleted files from cache...\n")
	d=dict(filter(lambda x:os.path.exists(x[0]),d.iteritems()))
    except (pickle.UnpicklingError,KeyError,EOFError,ImportError,IndexError):
        # Si el fichero no es válido, ignorarlo y marcar que hay que escribir cambios
        d={}
        modif=True
        cache.close()


count=0
for dirName, subdirList, fileList in os.walk(rootDir):
    sys.stderr.write('Exploring %s\n' % dirName)
    for fname in fileList:
        # Update signatures cache every 100 files
        if modif and ((count % 100)==0):
            writecache(d)
        if fname.lower().endswith(extensiones):
            ruta=os.path.join(dirName,fname)
            # Si el fichero no está en la caché, o está pero con tamaño diferente, añadirlo
            if (ruta not in d) or ((ruta in d) and (d[ruta]['size']!=os.path.getsize(ruta))):
                sys.stderr.write("   Calculating hash of %s...\n" % ruta)
                d[ruta]={
                        'name':fname,
                        'dir':dirName,
                        'hash':hashcalc(ruta,args.method),
                        'size':os.path.getsize(ruta)
                        }
                modif=True

# Write hash cache to disk
if modif: writecache(d)

# Check for duplicates

# Create a new dict indexed by hash
# Initialize dict with an empty list for every hash
hashes={}
for f in d:
    hashes[d[f]['hash']]=[]
# Group files with the same hash together
for f in d:
    hashes[d[f]['hash']].append(d[f])
# Discard hashes without duplicates
dupes={}
for h in hashes:
    if len(hashes[h])>1:
        dupes[h]=hashes[h]
# Cleanup. Not strictly necessary, but if there're a lot of files these can get quite big
del hashes
# Delete entries whose hash couldn't be generated, so they're not reported as duplicates
if 'ERR' in dupes: del dupes['ERR']

#TODO:Read tags, software used, title
nset=1
tmpdirs=[]
for h in dupes:
    print
    if args.delete:
        optselected=False
        while not optselected:
            # Prompt for which duplicated file to keep, delete the others
            #TODO: compare option to open in file manager (copy to temp, xdg-open it)
            for i in range(len(dupes[h])):
                aux=dupes[h][i]
                ruta=os.path.join(aux['dir'],aux['name'])
                sys.stderr.write( "[%d] %-40s %s\n" % (i+1,ruta,readmetadata(ruta)))
            answer=raw_input("Set %d of %d, preserve files [%d - %d, all, show, quit] (default: all): " % (nset,len(dupes),1,len(dupes[h])))
            if answer in ["quit","q"]:
                # If asked, write changes, delete temps and quit
                if modif: writecache(d)
                rmtemps(tmpdirs)
                exit(0)
            elif answer in ["show","s"]:
                # Create a temporary directory, copy duplicated files and open a file manager
                tmpdir=tempfile.mkdtemp()
                tmpdirs.append(tmpdir)
                for i in range(len(dupes[h])):
                    p=os.path.join(dupes[h][i]['dir'],dupes[h][i]['name'])
                    ntemp="%d_%s" % (i,dupes[h][i]['name'])
                    shutil.copyfile(p,os.path.join(tmpdir,ntemp))
                sub.Popen(["xdg-open",tmpdir],stdout=None,stderr=None)
            elif answer in ["all","a",""]:
                # Don't delete anything
                sys.stderr.write("Skipping deletion, all duplicates remain\n")
                optselected=True
            else:
                # If it's no option, assume it's a number and delete all movies except the chosen one
                answer=int(answer)-1 
                for i in range(len(dupes[h])):
                    if i!=answer:
                        p=os.path.join(dupes[h][i]['dir'],dupes[h][i]['name'])
                        os.remove(p)
                        del d[p]
                        modif=True
                optselected=True
        nset+=1
    else:
        # Just show duplicates
        for f in dupes[h]:
            print os.path.join(f['dir'],f['name']),
            if not args.sameline:
                print "\n",

# Final update of the cache in order to remove signatures of deleted files
if modif: writecache(d)

# Delete temps
rmtemps(tmpdirs)

# Restore directory
os.chdir(pwd)
