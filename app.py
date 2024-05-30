from difflib import SequenceMatcher
from flask import Flask, jsonify, redirect, render_template, request, url_for
import requests
from bs4 import BeautifulSoup


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
    return SequenceMatcher(None, a, b).ratio()

# Amazon product details
def fetch_amazon_product_details(user_product_name):
    amazon_url = f'https://www.amazon.in/s?k={user_product_name}&ref=nb_sb_noss'
    amazon_response = requests.get(
        url=amazon_url,
        headers={
            'authority': 'www.amazon.in',
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,'
                    'image/avif,image/webp,image/apng,*/*;q=0.8,'
                    'application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'device-memory': '8',
            'dnt': '1',
            'downlink': '10',
            'dpr': '1.5',
            'ect': '4g',
            'rtt': '50',
            'sec-ch-device-memory': '8',
            'sec-ch-dpr': '1.5',
            'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", '
                        '"Chromium";v="111"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-ch-ua-platform-version': '"10.0.0"',
            'sec-ch-viewport-width': '1152',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'sec-gpc': '1',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                        'AppleWebKit/537.36 (KHTML, like Gecko) '
                        'Chrome/111.0.0.0 Safari/537.36',
            'viewport-width': '1152'
        }
    )
    amazon_soup = BeautifulSoup(amazon_response.text, 'html.parser')

    amazon_products = amazon_soup.find_all('div', {'class': 's-result-item'})
    amazon_product_details = {'name': '', 'price': 0, 'productLink': '', 'imageLink': '', 'confidence': 0}
    for amazon_product in amazon_products:
        product_title = amazon_product.find(
            'div',
            {'class': 's-title-instructions-style'}
        )
        if product_title:
            product_name = product_title \
                .find('span', {'class': 'a-text-normal'}) \
                .text \
                .strip()
            confidence = match_confidence(user_product_name, product_name.lower())
            if amazon_product_details['confidence'] < confidence:
                amazon_product_details['confidence'] = confidence
                amazon_product_details['name'] = product_name
                amazon_product_details['productLink'] = \
                    'https://www.amazon.in' + \
                    amazon_product.find('a')['href']
                amazon_product_details['imageLink'] = amazon_product \
                    .find('img', {'class': 's-image'})['src']
                amazon_product_details['price'] = float(
                    amazon_product \
                        .find('div', {'class': 's-price-instructions-style'}) \
                        .find('span', {'class': 'a-offscreen'}) \
                        .text \
                        .strip()
                        .replace('₹', '')
                        .replace(',', '')
                )

    return amazon_product_details

# Flipkart product details
def fetch_flipkart_product_details(user_product_name):
    flipkart_url = f'https://www.flipkart.com/search?q={user_product_name}' + \
        '&otracker=search&otracker1=search&marketplace=FLIPKART&as-show=on&as=off'
    flipkart_response = requests.get(
        url=flipkart_url,
        headers={
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
    )
    flipkart_soup = BeautifulSoup(flipkart_response.text, 'html.parser')

    flipkart_products = flipkart_soup.find_all('div', {'class': '_1AtVbE'})
    flipkart_product_details = {'name': '', 'price': 0, 'productLink': '', 'imageLink': '', 'confidence': 0}

    for flipkart_product in flipkart_products:
        product_name_tag = flipkart_product.find('div', {'class': '_4rR01T'})  # Updated class for product name
        if product_name_tag:
            product_name = product_name_tag.text.strip()
            confidence = match_confidence(user_product_name, product_name.lower())
            if flipkart_product_details['confidence'] < confidence:
                flipkart_product_details['confidence'] = confidence
                flipkart_product_details['name'] = product_name
                product_link_tag = flipkart_product.find('a', {'class': '_1fQZEK'})
                flipkart_product_details['productLink'] = 'https://www.flipkart.com' + product_link_tag['href'] if product_link_tag else ''
                image_tag = flipkart_product.find('img', {'class': '_396cs4'})
                flipkart_product_details['imageLink'] = image_tag['src'] if image_tag else ''
                price_tag = flipkart_product.find('div', {'class': '_30jeq3 _1_WHN1'})  # Updated class for price
                if price_tag:
                    price_text = price_tag.text.strip().replace('₹', '').replace(',', '')
                    flipkart_product_details['price'] = float(price_text) if price_text else 0

    return flipkart_product_details

    flipkart_url = f'https://www.flipkart.com/search?q={user_product_name}' + \
        '&otracker=search&otracker1=search&marketplace=FLIPKART&as-show=on&as=off'
    flipkart_response = requests.get(
        url=flipkart_url,
        headers={
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
    )
    flipkart_soup = BeautifulSoup(flipkart_response.text, 'html.parser')

    flipkart_products = flipkart_soup.find_all('div', {'class': '_1AtVbE'})
    flipkart_product_details = {'name': '', 'price': 0, 'productLink': '', 'imageLink': '', 'confidence': 0}

    for flipkart_product in flipkart_products:
        product_name_tag = flipkart_product.find('div', {'class': '_4rR01T'})  # Adjusted class
        product_name = product_name_tag.text.strip() if product_name_tag else None

        if product_name:
            confidence = match_confidence(user_product_name, product_name.lower())
            if flipkart_product_details['confidence'] < confidence:
                flipkart_product_details['confidence'] = confidence
                flipkart_product_details['name'] = product_name
                product_link_tag = flipkart_product.find('a', {'class': '_1fQZEK'})
                flipkart_product_details['productLink'] = 'https://www.flipkart.com' + product_link_tag['href'] if product_link_tag else ''
                image_tag = flipkart_product.find('img', {'class': '_396cs4 _3exPp9'})
                flipkart_product_details['imageLink'] = image_tag['src'] if image_tag else ''
                price_tag = flipkart_product.find('div', {'class': '_30jeq3 _1_WHN1'})  # Adjusted class
                if price_tag:
                    flipkart_product_details['price'] = float(
                        price_tag.text.strip().replace('₹', '').replace(',', '')
                    )

    return flipkart_product_details

    flipkart_url = f'https://www.flipkart.com/search?q={user_product_name}' + \
        '&otracker=search&otracker1=search&marketplace=FLIPKART&as-show=on&as=off'
    flipkart_response = requests.get(
        url=flipkart_url,
        headers={
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
    )
    flipkart_soup = BeautifulSoup(flipkart_response.text, 'html.parser')

    flipkart_products = flipkart_soup.find_all('div', {'class': '_1AtVbE'})
    flipkart_product_details = {'name': '', 'price': 0, 'productLink': '', 'imageLink': '', 'confidence': 0}

    for flipkart_product in flipkart_products:
        product_name_tag = flipkart_product.find('a', {'class': 'IRpwTa'})
        product_name = product_name_tag.text.strip() if product_name_tag else None

        if product_name:
            confidence = match_confidence(user_product_name, product_name.lower())
            if flipkart_product_details['confidence'] < confidence:
                flipkart_product_details['confidence'] = confidence
                flipkart_product_details['name'] = product_name
                flipkart_product_details['productLink'] = 'https://www.flipkart.com' + product_name_tag['href']
                image_tag = flipkart_product.find('img', {'class': '_396cs4 _3exPp9'})
                flipkart_product_details['imageLink'] = image_tag['src'] if image_tag else ''
                price_tag = flipkart_product.find('div', {'class': '_30jeq3'})
                if price_tag:
                    flipkart_product_details['price'] = float(
                        price_tag.text.strip().replace('₹', '').replace(',', '')
                    )

    return flipkart_product_details

    flipkart_url = f'https://www.flipkart.com/search?q={user_product_name}' + \
        '&otracker=search&otracker1=search&marketplace=FLIPKART&as-show=on&as=off'
    flipkart_response = requests.get(
        url=flipkart_url,
        headers={
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
    )
    flipkart_soup = BeautifulSoup(flipkart_response.text, 'html.parser')

    flipkart_products = flipkart_soup.find_all('div', {'class': '_2kHMtA'})
    flipkart_product_details = {'name': '', 'price': 0, 'productLink': '', 'imageLink': '', 'confidence': 0}

    for flipkart_product in flipkart_products:
        product_name = flipkart_product \
            .find('div', {'class': '_4rR01T'}) \
            .text \
            .strip()
        
        confidence = match_confidence(user_product_name, product_name.lower())
        print(product_name,confidence)
        if flipkart_product_details['confidence'] < confidence:
            flipkart_product_details['confidence'] = confidence
            flipkart_product_details['name'] = product_name
            flipkart_product_details['productLink'] = 'https://www.flipkart.com' + flipkart_product\
                .find('a', {'class': '_1fQZEK'})['href']
            flipkart_product_details['imageLink'] = flipkart_product \
                .find('img', {'class': '_396cs4'})['src']
            flipkart_product_details['price'] = float(
                flipkart_product \
                    .find('div', {'class': '_30jeq3 _1_WHN1'}) \
                    .text \
                    .strip()
                    .replace('₹', '')
                    .replace(',', '')
            )

    return flipkart_product_details


@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        user_product_name = request.form['query']

        product_details = {
            'amazon': fetch_amazon_product_details(user_product_name),
            'flipkart': fetch_flipkart_product_details(user_product_name)
        }
        
        print(product_details)
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