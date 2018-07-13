#
# https://stackoverflow.com/a/47858268/1832058
#

import requests                # to get html from server
from bs4 import BeautifulSoup  # to search in html
import csv                     # to write in CSV
import webbrowser              # to open (downloaded) html file in web browser
import pymysql                  # to write in MySQL

#----------------------------------------------------------------------
# SCRAPER
#----------------------------------------------------------------------

def display(content, filename='output.html'):
    with open(filename, 'wb') as f:
        f.write(content)
        webbrowser.open(filename)

#----------------------------------------------------------------------

def get_soup(session, url, show=False):
    '''Read HTML from server and convert to Soup'''

    # GET request and response with HTML
    r = session.get(url)

    #print('TALanguage:', r.cookies.get('TALanguage')) # 'ALL' or 'es', 'pl', etc.
    #print('TASession:', r.cookies.get('TASession')) # see '*LF.ALL*' or '*LF.es*', '*LF.pl*', etc.

    # write html in file temp.html and open it in web browser.
    # it is useful to see/test what we get from server.
    if show:
        display(r.content, 'temp.html')

    # check if OK
    if r.status_code != 200: # not OK
        print('[get_soup] status code:', r.status_code)
        # (as default) it will returns None instead of Soup
    else:
        return BeautifulSoup(r.text, 'html.parser')

#----------------------------------------------------------------------

def post_soup(session, url, params, show=False):
    '''Read HTML from server and convert to Soup'''

    # POST request and response with HTML
    r = session.post(url, data=params) # POST request

    #print('TALanguage:', r.cookies.get('TALanguage')) # 'ALL' or 'es', 'pl', etc.
    #print('TASession:', r.cookies.get('TASession')) # see '*LF.ALL*' or '*LF.es*', '*LF.pl*', etc.

    # write html in file temp.html and open it in web browser.
    # it is useful to see/test what we get from server.
    if show:
        display(r.content, 'temp.html')

    # check if OK
    if r.status_code != 200: # not OK
        print('[post_soup] status code:', r.status_code)
        # (as default) it will returns None instead of Soup
    else:
        return BeautifulSoup(r.text, 'html.parser')

#----------------------------------------------------------------------

def scrape(url, lang='ALL'):

    # create session to keep all cookies (etc.) between requests
    session = requests.Session()

    session.headers.update({
        # some portals send correct HTML only if you have correct header 'user-agent'
        'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:57.0) Gecko/20100101 Firefox/57.0',
    })

    # add '?filterLang=ALL' to url to get all reviews (not only English)
    # add '?filterLang=es'  to url to get Spanish reviews
    # add '?filterLang=pl'  to url to get Polish reviews
    # etc.
    # ie. https://www.tripadvisor.com/Hotel_Review-g562819-d289642-Reviews-Hotel_Caserio-Playa_del_Ingles_Maspalomas_Gran_Canaria_Canary_Islands.html?filterLang=ALL'
    # for test - check language in cookies

    items = parse(session, url )

    return items

#----------------------------------------------------------------------

def parse(session, url):
    '''Get number of reviews and start getting subpages with reviews'''

 


    print('[parse] url:', url)

    soup = get_soup(session, url)

    if not soup:
        print('[parse] no soup:', url)
        return



    print('Hello World')

    # Get highlighted Amenity
    amenity_list = soup.findAll('div',class_="highlightedAmenity")

    print(amenity_list)

    for amenity in amenity_list:
        print(amenity.text )
  
    '''
    highliamenity_list
    
    for dom_elements in highlighted_amenity_dom:
        highlighted_amenity.append(dom_elements.text) 

    print(highlighted_amenity)
    '''

    # Getting Traveller Ratings under category Excellent,Very Good,Average ,Poor, Terrible

    traveller_rating_dict = dict()

    count = soup.findAll('span',class_="is-shown-at-tablet")

    traveller_rating_dict['Excellent'] = count[1].text
    traveller_rating_dict['Very good'] = count[3].text
    traveller_rating_dict['Average'] = count[5].text
    traveller_rating_dict['Poor'] = count[7].text
    traveller_rating_dict['Terrible'] = count[9].text

    print('Dictionary Printing')

    print('---------------------------')
    print(traveller_rating_dict)
    print('---------------------------')
    

    # get number of reviews in all languages
    num_reviews = soup.find('span', class_='reviews_header_count').text # get text
    num_reviews = num_reviews[1:-1] # remove `( )`
    num_reviews = num_reviews.replace(',', '') # remove `,` in number (ie. 1,234)
    num_reviews = int(num_reviews) # convert text into integer
    print('[parse] num_reviews ALL:', num_reviews)

    #~ num_reviews = soup.select_one('div[data-value="en"] span').text # get text
    #~ num_reviews = num_reviews[1:-1] # remove `( )`
    #~ num_reviews = num_reviews.replace(',', '') # remove `,` in number (ie. 1,234)
    #~ num_reviews = int(num_reviews) # convert text into integer
    #~ print('[parse] num_reviews ENGLISH:', num_reviews)

    # create template url to subpages with reviews
    # ie. https://www.tripadvisor.com/Hotel_Review-g562819-d289642-or{}.html
    url_template = url.replace('.html', '-or{}.html')
   # print('[parse] url_template:', url_template)




    # get subpages and parse reviews.
    # every subpage has 5 reviews
    # so it has url with -or0.html -or5.html -or10.html -or15.html etc.

    items = []

    offset = 0

    while(True):
        subpage_url = url_template.format(offset)

        subpage_items = parse_reviews(session, subpage_url)
        if not subpage_items:
            break

        items += subpage_items

        if len(subpage_items) < 5:
            break

        offset += 5

        #~ return items# for test only - to stop after first page

    return items

#----------------------------------------------------------------------

def get_reviews_ids(soup):

    items = soup.find_all('div', attrs={'data-reviewid': True})

    if items:
        reviews_ids = [x.attrs['data-reviewid'] for x in items][::2]
        print('[get_reviews_ids] data-reviewid:', reviews_ids)
        return reviews_ids

#----------------------------------------------------------------------

def get_more(session, reviews_ids):

    url = 'https://www.tripadvisor.com/OverlayWidgetAjax?Mode=EXPANDED_HOTEL_REVIEWS_RESP&metaReferer=Hotel_Review'

    payload = {
        'reviews': ','.join(reviews_ids), # ie. "577882734,577547902,577300887",
        #'contextChoice': 'DETAIL_HR', # ???
        'widgetChoice': 'EXPANDED_HOTEL_REVIEW_HSX', # ???
        'haveJses': 'earlyRequireDefine,amdearly,global_error,long_lived_global,apg-Hotel_Review,apg-Hotel_Review-in,bootstrap,desktop-rooms-guests-dust-en_US,responsive-calendar-templates-dust-en_US,taevents',
        'haveCsses': 'apg-Hotel_Review-in',
        'Action': 'install',
    }

    soup = post_soup(session, url, payload)

    return soup


#----------------------------------------------------------------------

def parse_reviews(session, url):
    '''Get all reviews from one page'''

    print('[parse_reviews] url:', url)

    soup =  get_soup(session, url)

    if not soup:
        print('[parse_reviews] no soup:', url)
        return

    hotel_name = soup.find('h1', id='HEADING').text

    reviews_ids = get_reviews_ids(soup)
    if not reviews_ids:
        return

    soup = get_more(session, reviews_ids)

    if not soup:
        print('[parse_reviews] no soup:', url)
        return

    items = []

    # find all reviews on page
    #for idx, review in enumerate(soup.find_all('div', class_='review-container')): # reviews on normal page
    for idx, review in enumerate(soup.find_all('div', class_='reviewSelector')):  # reviews on page after click "More"

        # it has to check if `badgets` (contributions/helpful_vote) exist on page
        badgets = review.find_all('span', class_='badgetext')
        if len(badgets) > 0:
            contributions = badgets[0].text
        else:
            contributions = '0'

        if len(badgets) > 1:
            helpful_vote = badgets[1].text
        else:
            helpful_vote = '0'

        # it has to check if `user_loc` exists on page
        #user_loc = review.find_all('div[@class="userLoc"]/strong/text()')
        user_loc = review.select_one('div.userLoc strong')
        
        if user_loc:
            user_loc = user_loc.text
        else:
            user_loc = ''

        # it has to find value in class name (ie. "bubble_40" => "40", "bubble_50" => "50")
        #bubble_rating = $xpath->query('.//span[contains(@class, "ui_bubble_rating")]', $review)[0]->getAttribute('class');
        bubble_rating = review.select_one('span.ui_bubble_rating')['class']
        bubble_rating = bubble_rating[1].split('_')[-1]

        item = {
            'hotel name': hotel_name,

            'review title': review.find('span', class_='noQuotes').text,
            'review_body': review.find('p', class_='partial_entry').text,
            # 'ratingDate' instead of 'relativeDate'
            'review date': review.find('span', class_='ratingDate')['title'],

            'contributions': contributions,  # former 'num_reviews_reviewer'
            'helpful vote': helpful_vote,  # new

            # former 'reviewer_name'
            'user name': review.find('div', class_='info_text').find('div').text,
            'user location': user_loc,  # new

            'rating': bubble_rating,
        }

        items.append(item)

        # display on screen
        print('\n--- review ---\n')
        for key,val in item.items():
            print(' ', key, ':', val)

        #~ return items # for test only - to stop after first review

    print() # empty line after last review

    return items
#----------------------------------------------------------------------
# CSV
#----------------------------------------------------------------------

def write_in_csv(items, filename='results.csv',
                  headers=['hotel name', 'review title', 'review body',
                           'review date', 'contributions', 'helpful vote',
                           'user name' , 'user location', 'rating'],
                  mode='w'):

    print('--- CSV ---')

    with open(filename, mode) as csvfile:
        csv_file = csv.DictWriter(csvfile, headers)

        if mode == 'w': # don't write headers if you append to existing file
            csv_file.writeheader()

        csv_file.writerows(items)

#----------------------------------------------------------------------
# DATABASE
# ---------------------------------------------------------------------

def connect():
    return pymysql.connect(
                host=DB_HOST,
                db=DB_DATABASE,
                user=DB_USER,
                password=DB_PASSWORD,
                port=DB_PORT,
                charset='utf8',
            )
    
def drop(conn):
    cur = conn.cursor()
    SQL = '''DROP TABLE ''' + DB_DATABASE + '''.''' + DB_TABLE + ''';'''
    cur.execute(SQL)
    conn.commit()
    cur.close()
    
def create(conn):
    cur = conn.cursor()
    query = '''CREATE TABLE {db}.{table} (
        id INT NOT NULL AUTO_INCREMENT,
        {column} LONG VARCHAR NOT NULL,
        PRIMARY KEY (id)
    )
    ENGINE=InnoDB
    DEFAULT CHARSET=utf8
    COLLATE=utf8_general_ci;'''.format(db=DB_DATABASE, table=DB_TABLE, column=DB_COLUMN)
    cur.execute(query)
    conn.commit()
    cur.close()

def insert(conn, item):
    cur = conn.cursor()
    query = 'INSERT INTO {table} ({column}) VALUE (%s);'.format(table=DB_TABLE, column=DB_COLUMN)
    cur.execute(query, item)
    conn.commit()
    cur.close()

def insert_many(conn, items):
    cur = conn.cursor()
    query = 'INSERT INTO {table} ({column}) VALUE (%s);'.format(table=DB_TABLE, column=DB_COLUMN)
    for item in items:
        cur.execute(query, item[DB_COLUMN])
    conn.commit()
    cur.close()
 
def display_all(conn):
    cur = conn.cursor()
    query = 'SELECT * FROM {table};'.format(table=DB_TABLE)
    cur.execute(query)
    for x in cur.fetchall():
        print(x)    
    cur.close()
    
# ---------------------------------------------------------------------

def write_in_mysql(items, headers):
        
    print('--- DATABASE ---')

    conn = connect()

    #drop(conn)   # drop old table 
    #create(conn) # create new table 

    insert_many(conn, items)

    display_all(conn)

    conn.close()

# ---------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------

DB_HOST     = 'localhost'
DB_DATABASE = 'tripadvisor'
DB_PORT     = 3306
DB_TABLE    = 'reviews'
DB_COLUMN   = 'review_body'

'''
DB_USER     = input('database login: ')
DB_PASSWORD = input('database password: ')
'''

# some URLs for testing
start_urls = [
    'https://www.tripadvisor.ca/Hotel_Review-g1480252-d316623-Reviews-Kuredu_Island_Resort_Spa-Kuredu.html',
    #'https://www.tripadvisor.com/Hotel_Review-g294229-d481832-Reviews-Pullman_Jakarta_Indonesia-Jakarta_Java.html',
    #'https://www.tripadvisor.com/Hotel_Review-g562819-d289642-Reviews-Hotel_Caserio-Playa_del_Ingles_Maspalomas_Gran_Canaria_Canary_Islands.html',
    #'https://www.tripadvisor.com/Hotel_Review-g60795-d102542-Reviews-Courtyard_Philadelphia_Airport-Philadelphia_Pennsylvania.html',
    #'https://www.tripadvisor.com/Hotel_Review-g60795-d122332-Reviews-The_Ritz_Carlton_Philadelphia-Philadelphia_Pennsylvania.html',
]

lang = 'in'

headers = [
    'hotel name', 
    'review title', 
     DB_COLUMN, #'review_body',
    'review date', 
    'contributions', 
    'helpful vote',
    'user name' , 
    'user location', 
    'rating',
]
           
for url in start_urls:

    # get all reviews for 'url' and 'lang'
    items = scrape(url, lang)

    if not items:
        print('No reviews')
    else:
        # write in CSV
        filename = url.split('Reviews-')[1][:-5] + '__' + lang
        print('filename:', filename)
        write_in_csv(items, filename + '.csv', headers, mode='w')
       
