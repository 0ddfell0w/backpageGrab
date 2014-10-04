import requests
import lxml.html
import pickle
import grequests
from collections import defaultdict, namedtuple

# Page = namedTuple("Page, ['url', 'location', 'ads'])
Ad = namedtuple("Ad", ['url', 'textbody', 'picture_urls'])

def get_all_backpages():
    r = requests.get("http://www.backpage.com/")
    html = lxml.html.fromstring(r.text)
    backpages = html.xpath("//a/@href")
    links = []
    for i in backpages:
          if "backpage" in i:
              if not "www" in i:
                  i = str(i)
                  links.append(i)

    with open("backpages","w") as f:
        pickle.dump(links,f)

def get_page_dict(index=2, as_list=False):
    """opens list of backpages stored in a file, generates links to relevant subdomains. returns either a dict mapping
    local backpage: links, or returns a long list of all the links generated."""
    backpages = pickle.load(open("backpages","rb"))
    link_dict = defaultdict(list)
    subdoms = ["FemaleEscorts/", "BodyRubs/", "Strippers/", "Domination/",
                            "TranssexualEscorts/", "MaleEscorts/", "Datelines/", "AdultJobs/"]
    page_suffix = lambda subdom, page: "{0}?page={1}".format(subdom, page) if page > 1 else subdom

    for page in backpages:
        for i in xrange(1,index):
            for subdom in subdoms:
                new_link = page + page_suffix(subdom, i)
                link_dict[subdom].append(new_link)
    if as_list:
        # set comprehension: for each list_of_links in values(): add each link in the list of links to the set
        return list( {link  for list_of_links in link_dict.values() for link in list_of_links} )
    return link_dict

def get_page_list(index=2):
    """ Generates a list of unique, relevant backpage urls on the second level. e.g. 'http://centraljersey.backpage.com/FemaleEscorts/' """
    return get_page_dict(index=index, as_list=True)

def get_ad_links_from_page(page):
    """ gets all the ads on a given subpage"""
    r = requests.get(page)
    html = lxml.html.fromstring(r.text)
    ads = html.xpath('//div[@class="cat"]/a/@href')
    return [str(ad) for ad in ads]

def get_page_to_ad_mapping(page_list, as_list=False):
    """Given a list of pages, return a dict of each page  """
    if not as_list:
        return {page : get_ad_links_from_page(page)   for page in page_list}
    else:
        return [link for page in page_list for link in get_ad_links_from_page(page)]

def get_ad_links_from_pages(page_list):
    return get_page_to_ad_mapping(page_list, as_list=True)

def extract_ad_info_from_response(response):
    """ Given a response to a request for an ad, extact the url, posting body, and links to the pictures"""
    html = lxml.html.fromstring(response.text)
    posting_body = html.xpath('//div[@class="postingBody"]')
    textbody = [i.text_content() for i in posting_body]

    # I don't think we're getting all images. Will need to revisit.
    picture_urls = list(set(html.xpath('//ul[@id="viewAdPhotoLayout"]/li/a/@href')))
    response.close()
    return Ad(url=response.url, textbody=textbody, picture_urls=picture_urls)

def extract_ad_info_from_url(url):
    """ wrapper around extract_ad_info_from_response"""
    return extract_ad_info_from_response(requests.get(url))

def extract_info_from_ads(url_list, asynchronous=False):
    if asynchronous:
        rs = (grequests.get(u,stream=False) for u in url_list)
        responses = grequests.map(rs)
        return [extract_ad_info_from_response(response) for response in responses]
    else:
        return [extract_ad_info_from_response(requests.get(url)) for url in url_list]


# def run_scraper(testing=False):
#     pages = get_page_link_list()
#     links = []
#     if testing:
#         page = pages[0]
#         # print page
#         links.append(grab_ads(page))
#         information = get_information_from_page(links[0][0])
#         return information
#     else:
#         for page in pages[:10]:
#             links += grab_ads(page)

#         # print "grabbing page data..."

#         #chunking requests because grequests can't handle that many at once
#         url_list = []
#         for i in xrange(0,len(links),10):
#             url_list.append(links[i-10:i])

#         data = get_information_from_page(url_list,asynchronous=True)
#         print data
#         data = []
#         for link in links:
#             data.append(get_information_from_page(link))
#         return data

# # data = run_scraper()
# ks:
#     data.append(get_information_from_page(link))
