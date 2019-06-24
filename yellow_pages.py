#!/usr/bin/env python
# -*- coding: utf-8 -*-

import requests
from lxml import html
import unicodecsv as csv
import argparse
import datetime

def parameters():
	"""
	Function to set parameters for search on yellow pages. Set parameter to True to include in search. Must have
	at least one true for each parameter

	"""
	keyword_dict = {
		'restaurant': True
	}

	city_province_dict = {
		'toronto+ON': True
	}

	if sum(keyword_dict.values()) == 0 or sum(city_province_dict.values()) == 0:
		sys.exit("Ensure you have specified at least one keyword and city, province")
	else:
		return keyword_dict, city_province_dict

def parse_listing(keyword, place_city_province, pagination=1):
	"""
	
	Function to process yellowpage listing page 
	: param keyword: search query
    : param place_city : place city name
    : param place_province: place province name

	"""

	url = "https://www.yellowpages.ca/search/si/{2}/{0}/{1}".format(keyword, place_city_province, pagination)
	# /pagenumber/keyword/placecity+placeprovince

	print("retrieving ",url)

	headers = {'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
				'Accept-Encoding':'gzip, deflate, br',
				'Accept-Language':'en-GB,en;q=0.9,en-US;q=0.8,ml;q=0.7',
				'Cache-Control':'max-age=0',
				'Connection':'keep-alive',
				'Host':'www.yellowpages.ca',
				'Upgrade-Insecure-Requests':'1',
				'User-Agent':'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36'
			}

	# Adding retries
	for retry in range(10):
		try:
			response = requests.get(url,verify=False, headers = headers )

			if response.status_code==200:
				parser = html.fromstring(response.text)

				#making links absolute
				base_url = "https://www.yellowpages.ca"
				parser.make_links_absolute(base_url)

				XPATH_LISTINGS = "//div[contains(@class, 'listing listing--bottomcta placement')]" #listings
				listings = parser.xpath(XPATH_LISTINGS)
				scraped_results = []

				for results in listings:

					XPATH_BUSINESS_NAME = ".//a[contains(@class, 'listing__name--link')]//text()"
					XPATH_BUSINESS_PAGE = ".//a[contains(@class, 'listing__name--link')]//@href"
					XPATH_STREET = ".//div[contains(@class, 'listing__address')]//span[@itemprop='address']//span[@itemprop='streetAddress']//text()"
					XPATH_LOCALITY = ".//div[contains(@class, 'listing__address')]//span[@itemprop='address']//span[@itemprop='addressLocality']//text()"
					XPATH_REGION = ".//div[contains(@class, 'listing__address')]//span[@itemprop='address']//span[@itemprop='addressRegion']//text()"
					XPATH_ZIP_CODE = ".//div[contains(@class, 'listing__address')]//span[@itemprop='address']//span[@itemprop='postalCode']//text()"
					XPATH_WEBSITE = ".//div[contains(@class, 'listing__mlr__root')]//ul/li[4]//@href"

					raw_business_name = results.xpath(XPATH_BUSINESS_NAME)
					raw_business_page = results.xpath(XPATH_BUSINESS_PAGE)
					raw_website = results.xpath(XPATH_WEBSITE)
					raw_street = results.xpath(XPATH_STREET)
					raw_locality = results.xpath(XPATH_LOCALITY)
					raw_region = results.xpath(XPATH_REGION)
					raw_zip_code = results.xpath(XPATH_ZIP_CODE)
					
					business_name = ''.join(raw_business_name).strip() if raw_business_name else None
					business_page = ''.join(raw_business_page).strip() if raw_business_page else None
					street = ''.join(raw_street).strip() if raw_street else None
					website = ''.join(raw_website).strip() if raw_website else None
					locality = ''.join(raw_locality).replace(',\xa0','').strip() if raw_locality else None
					region = ''.join(raw_region).strip() if raw_region else None
					zipcode = ''.join(raw_zip_code).strip() if raw_zip_code else None

					business_details = {
										'business_name':business_name,
										'business_page':business_page,
										'street': street,
										'website':website,
										'street':street,
										'locality':locality,
										'region':region,
										'zipcode':zipcode,
										'search_category': keyword,
										'updated_at': datetime.datetime.now()
					}
					scraped_results.append(business_details)

				return scraped_results

			elif response.status_code==404:
				print("Could not find a location matching",place)
				#no need to retry for non existing page
				break
			else:
				print("Failed to process page")
				return []
				
		except:
			print("Failed to process page")
			return []

# Add pagination
# Add searched category
# Add recorded date


if __name__=="__main__":
	
	# argparser = argparse.ArgumentParser()
	# argparser.add_argument('keyword',help = 'Search Keyword')
	# argparser.add_argument('place_city',help = 'Place City Name')
	# argparser.add_argument('place_province', help = 'Place Province Name')
	
	# args = argparser.parse_args()
	# keyword = args.keyword
	# place_city = args.place_city
	# place_province = args.place_province

	keyword_dict, place_city_province_dict = parameters()

	keyword_list = [key for key, value in keyword_dict.items() if value]
	place_city_province_list = [key for key, value in place_city_province_dict.items() if value]

	for place_city_province in place_city_province_list:
		for keyword in keyword_list:
			scraped_data =  parse_listing(keyword,place_city_province)	
	
			if scraped_data:
		
				print("Writing scraped data to %s-%s-yellowpages-scraped-data.csv"%(keyword,place_city_province)) # update
		
				with open('%s-%s-yellowpages-scraped-data.csv'%(keyword,place_city_province),'wb') as csvfile: # update
					fieldnames = scraped_data[0].keys()
			
					writer = csv.DictWriter(csvfile,fieldnames = fieldnames,quoting=csv.QUOTE_ALL)
					writer.writeheader()
					for data in scraped_data:
						writer.writerow(data)
