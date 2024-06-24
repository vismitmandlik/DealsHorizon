import aiohttp
from bs4 import BeautifulSoup
from flask import Flask, jsonify, redirect, render_template, request, url_for

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('homepage.html')

@app.route('/result')
def result():
    return render_template('result.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

def match_confidence(a, b):
    from difflib import SequenceMatcher
    return SequenceMatcher(None, a, b).ratio()

async def fetch(session, url, headers):
    try:
        async with session.get(url, headers=headers) as response:
            return await response.text()
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

async def fetch_amazon_product_details(user_product_name):
    amazon_url = f'https://www.amazon.in/s?k={user_product_name}&ref=nb_sb_noss'
    headers = {
        'authority': 'www.amazon.in',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'cache-control': 'max-age=0',
        'dnt': '1',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36',
    }

    async with aiohttp.ClientSession() as session:
        html = await fetch(session, amazon_url, headers)
        if html:
            amazon_soup = BeautifulSoup(html, 'html.parser')
            amazon_products = amazon_soup.find_all('div', {'class': 's-main-slot s-result-list s-search-results sg-row'})
            amazon_product_details = {'name': '', 'price': 0, 'productLink': '', 'imageLink': '', 'confidence': 0}
            for amazon_product in amazon_products:
                product_title = amazon_product.find('span', {'class': 'a-size-medium a-color-base a-text-normal'})
                if product_title:
                    product_name = product_title.text.strip()
                    confidence = match_confidence(user_product_name, product_name.lower())
                    if amazon_product_details['confidence'] < confidence:
                        amazon_product_details['confidence'] = confidence
                        amazon_product_details['name'] = product_name
                        amazon_product_details['productLink'] = 'https://www.amazon.in' + amazon_product.find('a')['href']
                        amazon_product_details['imageLink'] = amazon_product.find('img', {'class': 's-image'})['src']
                        price_whole = amazon_product.find('span', {'class': 'a-price-whole'})
                        if price_whole:
                            price = price_whole.text.strip().replace(',', '')
                            amazon_product_details['price'] = float(price)
            return amazon_product_details
        else:
            return {'error': 'Failed to fetch Amazon product details'}

async def fetch_flipkart_product_details(user_product_name):
    flipkart_url = f'https://www.flipkart.com/search?q={user_product_name}&otracker=search&otracker1=search&marketplace=FLIPKART&as-show=on&as=off'
    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36',
        'dnt': '1',
        'sec-ch-ua': '"Chromium";v="112", "Google Chrome";v="112", "Not:A-Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-gpc': '1'
    }

    async with aiohttp.ClientSession() as session:
        html = await fetch(session, flipkart_url, headers)
        if html:
            flipkart_soup = BeautifulSoup(html, 'html.parser')
            flipkart_products = flipkart_soup.find_all('div', {'class': '_1AtVbE'})
            flipkart_product_details = {'name': '', 'price': 0, 'productLink': '', 'imageLink': '', 'confidence': 0}
            for flipkart_product in flipkart_products:
                product_name_tag = flipkart_product.find('a', {'class': 'IRpwTa'})
                if product_name_tag:
                    product_name = product_name_tag.text.strip()
                    confidence = match_confidence(user_product_name, product_name.lower())
                    if flipkart_product_details['confidence'] < confidence:
                        flipkart_product_details['confidence'] = confidence
                        flipkart_product_details['name'] = product_name
                        flipkart_product_details['productLink'] = 'https://www.flipkart.com' + product_name_tag['href']
                        image_tag = flipkart_product.find('img', {'class': '_396cs4'})
                        flipkart_product_details['imageLink'] = image_tag['src'] if image_tag else ''
                        price_tag = flipkart_product.find('div', {'class': '_30jeq3'})
                        if price_tag:
                            price_text = price_tag.text.strip().replace('₹', '').replace(',', '')
                            flipkart_product_details['price'] = float(price_text) if price_text else 0
            return flipkart_product_details
        else:
            return {'error': 'Failed to fetch Flipkart product details'}

@app.route('/search', methods=['GET', 'POST'])
async def search():
    if request.method == 'POST':
        user_product_name = request.form['query']

        amazon_product_details = await fetch_amazon_product_details(user_product_name)
        flipkart_product_details = await fetch_flipkart_product_details(user_product_name)

        product_details = {
            'amazon': amazon_product_details,
            'flipkart': flipkart_product_details
        }

        return render_template(
            'result.html',
            amazon_product_details=product_details['amazon'],
            flipkart_product_details=product_details['flipkart'],
            query=user_product_name
        )
    else:
        return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
