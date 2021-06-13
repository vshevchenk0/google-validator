import re
from typing import Optional, Union, Match
import initial_structures
from pydantic import BaseModel, validator, Field, ValidationError


class Item(BaseModel):
    id: Optional[str] = Field(alias="g:id")
    title: Optional[str] = Field(alias="g:title")
    google_product_category: Optional[str] = Field(alias="g:google_product_category")
    product_type: Optional[str] = Field(alias="g:product_type")
    description: Optional[str] = Field(alias="g:description")
    link: Optional[str] = Field(alias="g:link")
    image_link: Optional[str] = Field(alias="g:image_link")
    additional_image_link: Optional[Union[str, list[str]]] = Field(alias="g:additional_image_link")
    price: Optional[str] = Field(alias="g:price")
    sale_price: Optional[str] = Field(alias="g:sale_price")
    brand: Optional[str] = Field(alias="g:brand")

    class Config:
        allow_population_by_field_name = True


class BaseFeedDataField(BaseModel):
    count: int
    example: str


class ExtendedFeedDataField(BaseFeedDataField):
    error_count: int
    error_example: str


class Data(BaseModel):
    entries: int
    id: BaseFeedDataField
    title: BaseFeedDataField
    google_product_category: BaseFeedDataField
    product_type: BaseFeedDataField
    link: ExtendedFeedDataField
    price: ExtendedFeedDataField
    sale_price: ExtendedFeedDataField
    image_link: BaseFeedDataField
    additional_image_link: BaseFeedDataField
    brand: BaseFeedDataField
    description: BaseFeedDataField


class FeedInformation(BaseModel):
    data: Data
    errors: set

    """
    Method for pushing specific errors (e.g. URL-params or some price related errors - something
    we have to show to the user) which have some fields for them preserved in data
    """
    def push_error(self, tag: str, message: str, value: str):
        self.errors.add(message)
        self.data.__getattribute__(tag).error_count += 1
        if not self.data.__getattribute__(tag).error_example:
            self.data.__getattribute__(tag).error_example = value


class Feed(BaseModel):
    namespace: str
    items: list[Item]
    currency: Optional[str]  # TODO: method for extracting currency

    class Config:
        allow_population_by_field_name = True

    """
    Checks for namespace, if it's not a valid google one or it is empty - raises ValueError
    """
    @validator('namespace')
    def check_namespace(cls, v):
        namespace = re.search(r"(https?://base\.google\.com/c?ns/[0-9.0-9]+)", v)
        if not namespace:
            raise ValueError
        return v

    def validate_feed(self, feed_information: FeedInformation):
        for item in self.items:
            feed_information.data.entries += 1
            self._tag_exists(item, feed_information)
            self._check_link(item.link, feed_information)
            self._check_positivity(item.price, "price", feed_information)
            self._check_positivity(item.sale_price, "sale_price", feed_information)
            self._check_currency(item.price, "price", feed_information)
            self._check_currency(item.sale_price, "sale_price", feed_information)
            self._compare_price_with_sale_price(item.price, item.sale_price, feed_information)

    @staticmethod
    def _tag_exists(item: Item, feed_information: FeedInformation):
        for key, value in item.dict().items():
            if value is None:
                feed_information.errors.add(f"{key} is missing")
            else:
                feed_information.data.__getattribute__(key).count += 1
                if not feed_information.data.__getattribute__(key).example:
                    feed_information.data.__getattribute__(key).example = value

    @staticmethod
    def _check_link(link: str, feed_information: FeedInformation):
        # workaround for geniuses who have empty tags in their feeds which still initialize validator
        if link is not None:
            url = re.search(r".+\?(.+)", link)
            if url:
                feed_information.push_error("link", "Url contains GET-params", url.group(1))

    @staticmethod
    def _check_positivity(price: str, name: str, feed_information: FeedInformation):
        # same workaround as above
        if price is not None:
            _price = re.search(r"([0-9,.-]+)", price)
            if _price:
                _price = convert_price_to_float(_price)
                if _price <= 0:
                    feed_information.push_error(name, f"{name} should be greater than 0", price)

    @staticmethod
    def _check_currency(price: str, name: str, feed_information: FeedInformation):
        if price is not None:
            currency = re.search(r"[0-9,.-]+\s([A-Z]{3})$", price)
            if not currency:
                feed_information.push_error(name, "Currency is missing or wrong formatted", price)

    @staticmethod
    def _compare_price_with_sale_price(price: str, sale_price: str, feed_information: FeedInformation):
        if price is not None and sale_price is not None:
            _price = re.search(r"([0-9,.-]+)", price)
            if _price:
                _price = convert_price_to_float(_price)
                _sale_price = re.search(r"([0-9,.-]+)", sale_price)
                if _sale_price:
                    _sale_price = convert_price_to_float(_sale_price)
                    if _sale_price > _price:
                        feed_information.push_error("sale_price", "sale_price should be lower than price", sale_price)


"""
Function which creates Feed and FeedInformation instances and validates the feed. If there is no
namespace passed (empty string) or the namespace is not a valid google one - catches the error
raised in the namespace validator and adds a corresponding error to feed_information.errors
"""


def check_feed(feed: dict) -> FeedInformation:
    feed_information: FeedInformation = FeedInformation.parse_obj(initial_structures.data)
    # without next line there is a bug with new set of errors not being generated and the old one is being used
    feed_information.errors = set(feed_information.errors)
    try:
        feed_obj: Feed = Feed.parse_obj(feed)
        feed_obj.validate_feed(feed_information)
    except ValidationError:
        feed_information.errors.add("Ain't a google feed baby")
    return feed_information


def convert_price_to_float(price: Optional[Match[str]]) -> float:
    price: str = price.group(0)
    price_as_float: float = float(price.replace(".", "", price.count(".") - 1)
                                  .replace(",", "", price.count(",") - 1)
                                  .replace(",", "."))
    return price_as_float
