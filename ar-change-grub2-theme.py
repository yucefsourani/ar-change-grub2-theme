#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
#  ar-change-grub2-theme.py
#  
#  Copyright 2017 youcef sourani <youssef.m.sourani@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
# 
import os.path
from os import listdir,makedirs,getcwd,chdir,walk,getuid
import subprocess
from collections import OrderedDict
import requests
import time
import tarfile
import zipfile
import shutil
import sys
import tempfile
import argparse

help_ = """
{}
-------------------------------------
Error:
    Set Grub2 Theme Link Or Location
Ex:
    sudo {} --link https://dl.opendesktop.org/api/files/downloadfile/id/1515426341/s/8192c84fbabf70f8713c84b1fcdc0c64/t/1523984154/u/444679/Atomic-GRUB-Theme.tar.gz
    sudo {} --link Downloads/megano-grub-fedora-install.tar.gz
    


REPORTING BUGS
    https://github.com/yucefsourani/ar-change-grub2-theme
""".format(__file__,__file__,__file__,__file__)

class Grub():
    def downlaod_theme(self,link,location=tempfile.gettempdir(),agent="Mozilla/5.0"):
        agent = agent={"User-Agent":agent}
        location = os.path.expanduser(os.path.join(location,"arfedora_grub_theme",str(int(time.time()))))
        makedirs(location, exist_ok=True)
        name = os.path.basename(link)
        saveas   = os.path.join(location,name)
        try:
            session = requests.session()
            opurl = session.get(link,headers=agent,stream=True,allow_redirects=True)
            opurl.raise_for_status()
            size = int(opurl.headers["Content-Length"])
            psize = 0
            print ("["+"-"*100+"]"+" "+str(size)+"b"+" "+"0%",end="\r",flush=True)
            with open(saveas, 'wb') as op:
                for chunk in opurl.iter_content(chunk_size=600):
                    count = int((psize*100)//size)
                    n = "#" * count
                    op.write(chunk)
                    psize += 600
                    print ("["+n+"-"*(100-count)+"]"+" "+str(size)+"b"+" "+str(round((psize*100)/size,2))+"%",end="\r",flush=True)
            
            print (" "*200,end="\r",flush=True)
            print ("["+"#"*100+"]"+" "+str(size)+"b"+" "+"100%")
        except requests.exceptions.MissingSchema:
            if  subprocess.call("cp {} {}".format(link,location),shell=True)!=0:
                return False
            if not os.path.isfile(saveas):
                return False
            return saveas
        except Exception as e:
            print(e)
            return False
        return saveas

    def unpack_theme_file(self,location):
        if location.endswith('.zip'):
            fun, mode = zipfile.ZipFile, 'r'
        elif location.endswith('.tar.gz') or location.endswith('.tgz'):
            fun, mode = tarfile.open, 'r:gz'
        elif location.endswith('.tar.bz2') or location.endswith('.tbz'):
            fun, mode = tarfile.open, 'r:bz2'
        elif location.endswith('.tar.xz') :
            fun, mode = tarfile.open, 'r:xz'
        else: 
            return False
        cwd = getcwd()
        chdir(os.path.dirname(location))
        try:
            file_ = fun(location, mode)
            try:
                file_.extractall()
            except Exception as e:
                print(e)
                os.chdir(cwd)
                return False
            finally:
                file_.close()
        except Exception as e:
            print(e)
            os.chdir(cwd)
            return False
        finally:
            os.chdir(cwd)
        
        for dirname,folders,files in walk(os.path.dirname(location)):
            for _file_ in files:
                if _file_ == "theme.txt":
                    return os.path.dirname(os.path.join(dirname,_file_))
        return False
            
        
    def change_grub_config(self,config,value,command,legacybios,efi):
        result = OrderedDict()
        with open("/etc/default/grub") as mf:
            for line in mf:
                line = line.strip()
                if line:
                    if "=" in line:
                        splitline = line.split("=",1)
                        k_ = splitline[0].strip()
                        v_ = splitline[1].strip()
                        if k_=="GRUB_TERMINAL_OUTPUT":
                            k_="#GRUB_TERMINAL_OUTPUT"
                        result.setdefault(k_,v_)
            
        if config not in result.keys():
            result.setdefault(config,value)
        else:
            result[config]=value
        try:
            with open("/etc/default/grub","w") as mf:
                for k,v in result.items():
                    mf.write(k+"="+v+"\n")
        except Exception as e:
            print(e)
            return False
        check  = self.update_grub(command,legacybios,efi)
        if check == 0:
            return True
        else:
            return False



    def change_grub_theme(self,theme_location,command,legacybios,efi):
        if os.path.isabs(theme_location) and os.path.isfile(theme_location) and os.path.basename(theme_location)=="theme.txt":
            if theme_location.startswith("/boot/grub2/themes") or theme_location.startswith("/boot/grub/themes"):
                return self.change_grub_config("GRUB_THEME","\""+theme_location+"\"",command,legacybios,efi)
            
        elif os.path.isabs(theme_location) and os.path.isdir(theme_location) :
            if theme_location.startswith("/boot/grub2/themes") or theme_location.startswith("/boot/grub/themes"):
                if "theme.txt" in listdir(theme_location) and os.path.isfile(theme_location+"/theme.txt"):
                    return self.change_grub_config("GRUB_THEME","\""+theme_location+"/theme.txt\"",command,legacybios,efi)

        return False

    def update_grub(self,command,legacybios,efi):
        if os.path.isdir("/sys/firmware/efi/efivars"):
            return  subprocess.call("{} -o {}".format(command,efi),shell=True)
        else:
            return subprocess.call("{} -o {}".format(command,legacybios),shell=True)

def main(link,system_theme_location,grub_mkconfig,legacy_boot_menu,efi_boot_menu):
    grub=Grub()
    themefile = grub.downlaod_theme(link,location=tempfile.gettempdir())
    if themefile:
        themefolder = grub.unpack_theme_file(themefile)
        if themefolder:
            check = subprocess.call("cp -r {} {}".format(themefolder,system_theme_location),shell=True)
            if check==0:
                check = grub.change_grub_theme(os.path.join(system_theme_location,os.path.basename(themefolder)),grub_mkconfig,legacy_boot_menu,efi_boot_menu)
                if check :
                    print("\nSuccess.")
                    return True
                else:
                    print("\nChange Theme To {} Fail.".format(os.path.join(system_theme_location,os.path.basename(themefolder))))
                    return False
            else:
                print("\nCopy  {} To {} Fail.".format(themefolder,system_theme_location))
        else:
            print("\nUnpack {} Fail.".format(themefolder))
            return False
    else:
        print("\nDownload {} Fail.".format(link))
        return False
    return True

if __name__ == "__main__":
    if getuid()!=0:
        print("\nRun Script With Root Permissions.\n")
        exit(1)
    parser = argparse.ArgumentParser(description = "Script To Change Grub2 Theme.")
    parser.version = "1.0"
    parser.add_argument("-v","--version",action="version")
    parser.add_argument("-l","--link",required=True,action="store",type=str,metavar="Link|zip|tar",help="(Link | Compressed File Location) For Grub2 Theme")
    parser.add_argument("-u","--ubuntu",action="store_true",help="Ubuntu Support (default is Fedora Linux)")
    parser.add_argument("-a","--archlinux",action="store_true",help="Archlinux Support (default is Fedora Linux)")
    args = parser.parse_args()
    link = args.link
    
    if args.ubuntu:
        system_theme_location = "/boot/grub/themes"
        grub_mkconfig         = "grub-mkconfig"
        legacy_boot_menu      = "/boot/grub/grub.cfg"
        efi_boot_menu         = "/boot/grub/grub.cfg"
    elif args.archlinux:
        system_theme_location = "/boot/grub/themes"
        grub_mkconfig         = "grub-mkconfig"
        legacy_boot_menu      = "/boot/grub/grub.cfg"
        efi_boot_menu         = "/boot/grub/grub.cfg"
    else: # default fedora
        system_theme_location = "/boot/grub2/themes"
        grub_mkconfig         = "grub2-mkconfig"
        legacy_boot_menu      = "/boot/grub2/grub.cfg"
        efi_boot_menu         = "/boot/efi/EFI/fedora/grub.cfg"
    
    if main(link,system_theme_location,grub_mkconfig,legacy_boot_menu,efi_boot_menu):
        exit(0)
    else:
        exit(1)
