import json
import re
import scrapy
from datetime import datetime
from scrapy import cmdline


class UserProductsSpider(scrapy.Spider):
    name = "user_products"
    start_urls = ["https://jiji.co.ke/sellerpage-4546841"]
    # start_urls = ["https://jiji.co.ke/shop/techsparkmachines"]

    def parse(self, response):
        
        
        # Extract any desired data here from the current response
        for product in response.css("div.b-seller-page__listing > div.b-seller-page__listing-items .masonry-item"):
            data = {
                'url': product.css('div.b-advert-listing-tile-item-wrapper a.b-list-advert-base--gallery::attr(href)').get(),
                'image': product.css('div.b-advert-listing-tile-item-wrapper a.b-list-advert-base--gallery img::attr(src)').get(),
                'title': product.css('div.b-advert-listing-tile-item-wrapper a.b-list-advert-base--gallery .b-list-advert-base__data__title div div::text').get(),
                'price': product.css('div.b-advert-listing-tile-item-wrapper a.b-list-advert-base--gallery .b-list-advert-base__data__price div div div::text').get(),
                'description': product.css('div.b-advert-listing-tile-item-wrapper a.b-list-advert-base--gallery div.b-list-advert-base__description-text::text').get(),
                'location': product.css('div.b-advert-listing-tile-item-wrapper a.b-list-advert-base--gallery span.b-list-advert__region__text::text').get(),
                'item-attrs': product.css('div.b-advert-listing-tile-item-wrapper a.b-list-advert-base--gallery div.b-list-advert-base__item-attr::text').getall(),
                'user_phone': None,
                'boost': None,
                'category': None,
            }
            
            if data['url'] is not None: data['url'] = response.urljoin(data['url'])
            if data['title'] is not None: data['title'] = data['title'].strip()
            if data['price'] is not None: data['price'] = self.currency_to_float(data['price'].lower().strip())
            if data['description'] is not None: data['description'] = data['description'].strip()
            if data['location'] is not None: data['location'] = data['location'].strip()
            if data['item-attrs'] is not None: data['item-attrs'] = [attr.strip() for attr in data['item-attrs'] if attr.strip()]
            
            yield data
        
        # Extract the script tag containing the nextUrl
        script_content = response.xpath('//script[contains(., "nextUrl")]/text()').get()

        if script_content:
            # Use regex to extract the nextUrl from the script content
            next_url_match = re.search(r'nextUrl:\s*"([^"]+)"', script_content)
            if next_url_match:
                next_url = next_url_match.group(1)
                # Fix any unicode escape sequences in the URL
                next_url = next_url.encode('utf-8').decode('unicode_escape')
                
                # Make a new request for the next page
                yield scrapy.Request(url=response.urljoin(next_url), callback=self.parse_next_pages)

    def parse_next_pages(self, response):
        
        print("Next page URL:", response.url)
        
        page_data = json.loads(response.text)
        
        ## Extract the products data
        products = page_data.get('adverts_list', {}).get('adverts', [])
        for product in products:
            data = {
                'url': product.get('url'),
                'image': product.get('image_obj', {}).get('url', None),
                'title': product.get('title'),
                'price': product.get('price_title'),
                'description': product.get('details'),
                'location': product.get('region_item_text'),
                'item-attrs': product.get('attrs', []),
                'user_phone': product.get('user_phone', None),
                'boost': product.get('is_boost', None),
                'category': product.get('category_name', None),
            }
            
            if data['url'] is not None: data['url'] = response.urljoin(data['url'])
            if data['title'] is not None: data['title'] = data['title'].strip()
            if data['price'] is not None: data['price'] = self.currency_to_float(data['price'].lower().strip())
            if data['description'] is not None: data['description'] = data['description'].strip()
            if data['location'] is not None: data['location'] = data['location'].strip()
            if data['item-attrs'] is not None: data['item-attrs'] = [f"{attr['name']}: {attr['value']}" for attr in data['item-attrs'] if attr]
            
            yield data
        
    
        # Get the next page url if any:
        next_page_url = page_data.get('next_url')
        if next_page_url:
            yield response.follow(next_page_url, callback=self.parse_next_pages)
        
    def currency_to_float(self, currency_string):
        # Remove any whitespace and convert to lowercase
        cleaned_string = currency_string.strip().lower()
        
        # Remove currency symbols and separators
        symbols = ['$', '€', '£', '¥', 'ksh', 'kes', 'ksh.', ',', ' ']
        for symbol in symbols:
            cleaned_string = cleaned_string.replace(symbol, '')
        
        try:
            # Convert to float
            return float(cleaned_string)
        except ValueError:
            # If conversion fails, return None
            return None
    
    

def crawl_products(): 
    cmdline.execute(f"scrapy runspider user_products.py -o products{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}_.csv".split()) 
    

crawl_products()