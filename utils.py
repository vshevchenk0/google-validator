from defusedxml.ElementTree import fromstring
import re


def convert(errors):
    for key, value in errors['errors'].items():
        errors['errors'][key] = list(value)
    return errors


def parse(text):
    data = {
        "offer": {
            "entries": 0,
            "id_count": 0,
            "id_example": ""
        },
        "name": {
            "entries": 0,
            "example": "",
            "mandatory": True
        },
        "category": {
            "entries": 0,
            "example": "",
            "mandatory": True
        },
        "url": {
            "entries": 0,
            "example": "",
            "error_count": 0,
            "error_example": "",
            "mandatory": True
        },
        "price": {
            "entries": 0,
            "example": "",
            "error_count": 0,
            "error_example": "",
            "mandatory": True
        },
        "sale_price": {
            "entries": 0,
            "example": "",
            "error_count": 0,
            "error_example": "",
            "mandatory": False
        },
        "currency": {
            "entries": 0,
            "example": "",
            "error_count": 0,
            "error_example": "",
            "mandatory": True
        },
        "pictures": {
            "entries": 0,
            "example": "",
            "mandatory": True
        },
        "vendor": {
            "entries": 0,
            "example": "",
            "mandatory": True
        },
        "description": {
            "entries": 0,
            "example": "",
            "mandatory": False
        }
    }
    errors = {
        "errors": {
            "namespace": set(),
            "offer": set(),
            "name": set(),
            "category": set(),
            "url": set(),
            "price": set(),
            "sale_price": set(),
            "currency": set(),
            "pictures": set(),
            "vendor": set(),
            "description": set()
        }
    }
    namespace_pattern = r"(https?:\/\/base\.google\.com\/c?ns\/[0-9\.0-9]+)"
    namespace = re.search(namespace_pattern, text[:200])
    if not namespace:
        errors['errors']['namespace'].add("Ain't a google feed baby")
        errors = convert(errors)
        return data, errors
    else:
        namespace = namespace.group(0)
        xml = fromstring(text)
        url_pattern = r".+\?(.+)"
        price_pattern = r"([0-9\,\.-]+)"
        currency_pattern = r"[0-9\,\.-]+\s([A-Z]{3})$"
        items = xml[len(xml) - 1].findall('item')
        for item in items:
            data['offer']['entries'] += 1

            # check item id
            item_id = item.findtext(f"{{{namespace}}}id") or item.findtext("id")
            if not item_id:
                errors['errors']['offer'].add("No item id")
            else:
                data['offer']['id_count'] += 1
                if not data['offer']['id_example']:
                    data['offer']['id_example'] = item_id

            # check item name
            item_name = item.findtext(f"{{{namespace}}}title") or item.findtext("title")
            if not item_name:
                errors['errors']['name'].add("No item name")
            else:
                data['name']['entries'] += 1
                if not data['name']['example']:
                    data['name']['example'] = item_name

            # check item category
            item_category = item.findtext(f"{{{namespace}}}product_type") or item.findtext("product_type")
            if not item_category:
                errors['errors']['category'].add("No item category")
            else:
                data['category']['entries'] += 1
                if not data['category']['example']:
                    data['category']['example'] = item_category

            # check item url
            item_url = item.findtext(f"{{{namespace}}}link") or item.findtext("link")
            if not item_url:
                errors['errors']['url'].add("No item url")
            else:
                data['url']['entries'] += 1
                item_url_params = re.search(url_pattern, item_url)
                if item_url_params:
                    errors['errors']['url'].add("Url contains GET-params")
                    data['url']['error_count'] += 1
                    if not data['url']['error_example']:
                        data['url']['error_example'] = item_url
                elif not data['url']['example']:
                    data['url']['example'] = item_url

            # check item price
            item_price_with_currency = item.findtext(f"{{{namespace}}}price") or item.findtext("price")
            if not item_price_with_currency:
                errors['errors']['price'].add("No item price")
                item_price = None
            else:
                item_price = re.search(price_pattern, item_price_with_currency)
                item_price = item_price.group(0)
                item_price = item_price\
                    .replace(".", "", item_price.count(".")-1)\
                    .replace(",", "", item_price.count(",")-1)\
                    .replace(",", ".")
                data['price']['entries'] += 1
                if float(item_price) < 0:
                    errors['errors']['price'].add("Item price should be positive")
                    data['price']['error_count'] += 1
                    if not data['price']['error_example']:
                        data['price']['error_example'] = item_price
                elif not data['price']['example']:
                    data['price']['example'] = item_price

            # check item sale price
            item_sale_price_with_currency = item.findtext(f"{{{namespace}}}sale_price") or item.findtext("sale_price")
            if item_sale_price_with_currency:
                item_sale_price = re.search(price_pattern, item_sale_price_with_currency)
                item_sale_price = item_sale_price.group(0)
                item_sale_price = item_sale_price\
                    .replace(".", "", item_sale_price.count(".") - 1)\
                    .replace(",", "", item_sale_price.count(",") - 1)\
                    .replace(",", ".")
                data['sale_price']['entries'] += 1
                if item_price is None:
                    errors['errors']['sale_price'].add("Item sale_price is defined while price is not")
                elif float(item_sale_price) < 0:
                    errors['errors']['sale_price'].add("Item sale_price should be positive")
                    data['sale_price']['error_count'] += 1
                    if not data['sale_price']['error_example']:
                        data['sale_price']['error_example'] = item_sale_price
                elif item_price is not None and float(item_sale_price) >= float(item_price):
                    errors['errors']['sale_price'].add("Item sale_price should be lower than price")
                    data['sale_price']['error_count'] += 1
                    if not data['sale_price']['error_example']:
                        data['sale_price']['error_example'] = item_sale_price
                elif not data['sale_price']['example']:
                    data['sale_price']['example'] = item_sale_price

            # check currency
            try:
                item_price_currency = re.search(currency_pattern, item_price_with_currency).group(1)
                try:
                    item_sale_price_currency = re.search(currency_pattern, item_sale_price_with_currency).group(1)
                    # item_sale_price_currency = item_sale_price_currency.group(1)
                except (TypeError, AttributeError):
                    item_sale_price_currency = None

                # item_price_currency = item_price_currency.group(1)
                data['currency']['entries'] += 1
                # set feed currency on the first loop run
                if not data['currency']['example']:
                    data['currency']['example'] = item_price_currency
                if not item_price_currency == data['currency']['example']:
                    errors['errors']['currency'].add("Item price currency does not match feed currency")
                    data['currency']['error_count'] += 1
                    if not data['currency']['error_example']:
                        data['currency']['error_example'] = item_price_currency
                if item_sale_price_currency is not None and \
                        not item_sale_price_currency == data['currency']['example']:
                    errors['errors']['currency'].add("Item sale_price currency does not match feed currency")
                    data['currency']['error_count'] += 1
                    if not data['currency']['error_example']:
                        data['currency']['error_example'] = item_sale_price_currency
            except (TypeError, AttributeError):
                errors['errors']['currency'].add("Item price has no currency or wrong currency format")

            # check pictures
            item_picture = item.findtext(f"{{{namespace}}}image_link") or item.findtext("image_link")
            item_additional_pictures = item.findall(
                f"{{{namespace}}}additional_image_link") or item.findall("additional_image_link")
            if not item_picture and not item_additional_pictures:
                errors['errors']['pictures'].add("No item pictures")
            elif item_picture or item_additional_pictures:
                if item_picture:
                    data['pictures']['entries'] += 1
                    if not data['pictures']['example']:
                        data['pictures']['example'] = item_picture
                    if item_additional_pictures:
                        data['pictures']['entries'] += len(item_additional_pictures)
                else:
                    data['pictures']['entries'] += len(item_additional_pictures)
                    if not data['pictures']['example']:
                        data['pictures']['example'] = item_additional_pictures[0].text

            # check vendor
            item_vendor = item.findtext(f"{{{namespace}}}brand") or item.findtext("brand")
            if not item_vendor:
                errors['errors']['vendor'].add("No item vendor")
            else:
                data['vendor']['entries'] += 1
                if not data['vendor']['example']:
                    data['vendor']['example'] = item_vendor

            # check description
            item_description = item.findtext(f"{{{namespace}}}description") or item.findtext("description")
            if not item_description:
                errors['errors']['description'].add("No item description")
            else:
                data['description']['entries'] += 1
                if not data['description']['example']:
                    data['description']['example'] = item_description

    errors = convert(errors)
    return data, errors
