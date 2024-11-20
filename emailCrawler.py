import os
import sys
import requests
import argparse
from colorama import init,Fore
from bs4 import BeautifulSoup
from collections import deque
from urllib.parse import urlparse
from email_scraper import scrape_emails

requests.packages.urllib3.disable_warnings()

cusomHeader={'user-agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36'}
checkedUrl = set()
results=set()

def banner():
    print(Fore.BLUE+'''
   __                _ _     ___                   _           
  /__\ __ ___   __ _(_) |   / __\ ____      ____ _| | ___ _ __ 
 /_\| '_ ` _ \ / _` | | |  / / | '__\ \ /\ / / _` | |/ _ \ '__|
//__| | | | | | (_| | | | / /__| |   \ V  V / (_| | |  __/ |   
\__/|_| |_| |_|\__,_|_|_| \____/_|    \_/\_/ \__,_|_|\___|_|   
                                                                                                                                                                                                
    ''')

def fix_url(url:str)->str:
    if not (url.startswith('https://') or url.startswith('http://')):
        url = 'https://' + url
        url = url.rstrip("/")
    return url

def checkResoureLink(link:str):
    if link.endswith(('.pdf','mp3','css','mp4','jpg','jpeg','gif','png','webp')):
        return False
    return True

#Warning: this crawl is very simple and not stable, if you need more accurate data, please use a mature framework.
def crawlLinks(urls:str,proxy=None,depth:int=1):
    if depth > 9 :
        depth = 9
    if depth <= 0:
        depth = 1
    urls = fix_url(urls)
    scheme = urlparse(urls).scheme+'://'
    host = urlparse(urls).netloc
    print(host)
    validLinks = set()
    tmpLinksContainer = set()
    validLinks.add(urls)
    while depth:
        try:
                if len(validLinks) == 0:
                    depth -= 1
                    validLinks=tmpLinksContainer.copy()
                    tmpLinksContainer.clear()
                if depth == 0:
                    for v in validLinks:
                        checkedUrl.add(v)
                    validLinks.clear()
                    break
                url = validLinks.pop()
                print(Fore.GREEN+'[+]'+f'crawing the host: {url}')
                if url in checkedUrl:
                    continue
                r = requests.get(url,headers=cusomHeader,proxies=proxy,timeout=10,verify=False)
                checkedUrl.add(url)
                if r.status_code == 200:
                    soup=BeautifulSoup(r.text,features="html.parser")
                    soup.encode('utf-8')
                    links = soup.find_all('a')
                    for link in links:
                        try:
                            link = link['href']
                        except:
                            continue
                        if len(urlparse(link).netloc)==0:
                            if checkResoureLink(link):
                                tmpLinksContainer.add(scheme+host+'/'+link)
                        if urlparse(link).netloc ==  host:
                            if checkResoureLink(link):
                                tmpLinksContainer.add(link)
                else:
                    print(r.status_code)
                    continue
        except KeyboardInterrupt:
            break
        except:
            print(Fore.RED+'[x] '+f'processed {url} email occurred exception, error message {sys.exc_info()[0]}')
            continue  
    #If the site crawl is completed, the email crawl will start.
    print(Fore.YELLOW+'-----------------------------------------------')
    print(Fore.YELLOW+'Crawling done. Now will be start scrape emails.')
    print(Fore.YELLOW+'-----------------------------------------------')
    crawlEmail(deque(checkedUrl))

def crawlEmail(urls:deque,proxy=None):
    tmp = []
    for url in urls:
        try:
            url = fix_url(url)
            print(f'processing:{url}')
            response = requests.get(url,headers=cusomHeader,proxies=proxy,timeout=10,verify=False)
            if response.status_code == 200:
                soup=BeautifulSoup(response.text,features="html.parser")
                soup.encode('utf-8')
                text = soup.get_text()
                emails = scrape_emails(text)
                for email in emails:
                    if email not in tmp:
                        tmp.append(email)
                        results.add(''+url+','+email+'')
        except KeyboardInterrupt:
            break
        except:
            print(Fore.RED+'[x] '+f'processed {url} email occurred exception, error message {sys.exc_info()[0]}')
            continue           
    tmp.clear()

def main():
    argp = argparse.ArgumentParser(prog='emailCrawler.py',description='''For crawling One Site All pages email, ATTENTION PLEASE! arguments deal order: file > list > site, 
    if you input these arguments in the meantime, the program will follow this order to deal with your input data.''')
    argp.add_argument('-d','--depth',default=1,help='crawl link function recursive depth, the default setting is 1, max depth 9.')
    argp.add_argument('-f','--file',default=False,help='read the site list from an existing site crawl result file.')
    argp.add_argument('-l','--list',default=False,help='input the sites list manually, separated by a comma. e.g:https://a.com/page1,https://a.com/page2')
    argp.add_argument('-o','--output',default=False,help='specify the output file name, the default format is .csv, while it just prints results on the screen if you ignore it.')
    argp.add_argument('-p','--proxy',default=False,help='custom proxies while sending requests to crawl links and emails.')
    argp.add_argument('-s','--site',default=False,help='''input the site you want to crawl, the program will automatically simply crawl the site all <a> tag href attribute links and check emails.
    This is not suggested, it will take a long time to crawl the site links and is not accurate, if you just want to crawl emails quickly, please use -f to deal with crawled site links files.
''')
    arg=argp.parse_args()
    proxy = None
    if arg.proxy is not False:
        proxy = {
                'http':arg.proxy,
                'https': arg.proxy
                }
    if arg.file is not False:
        if os.path.exists(arg.file):
            linksList = []
            with open(arg.file,'rb') as f:
                for link in f:
                    link = link.rstrip().decode('utf-8')
                    linksList.append(str(link))
            crawlEmail(deque(linksList),proxy)
    elif arg.list is not False:
        linksList = str(arg.list).strip(' ').split(',')
        crawlEmail(deque(linksList),proxy)
    elif arg.site is not False:
        crawlLinks(arg.site,proxy,arg.depth)
    else:
        argp.print_help()
    if arg.output is not False:
        with open(arg.output+'.csv','wb') as o:
            o.write('link,emailAddress')
            for result in results:
                o.write(result+'\n')
        print('All results have been write in'+arg.output+'.csv, please checked in current directory.')
    elif len (results) > 0:
        print(Fore.YELLOW+'-----------------------------------------------')
        print(Fore.YELLOW+'email crawl done.')
        print(Fore.YELLOW+'-----------------------------------------------')
        for r in results:
            print(r)
        
    

if __name__=='__main__':
    init(autoreset=True)
    banner()
    try:
        main()
    except KeyboardInterrupt:
        print(Fore.RED+'user aborted.')
        exit(-1)
