import scrapy

class AmazonItem(scrapy.Item):
    category = scrapy.Field()  # Add this if you want dynamic filenames by category

    title = scrapy.Field()
    price = scrapy.Field()
    rating = scrapy.Field()
    link = scrapy.Field()
    Brand = scrapy.Field()
    Item_form = scrapy.Field()
    Hair_type = scrapy.Field()
    Scent = scrapy.Field()
    Age_range_description = scrapy.Field()
    Material_type_free = scrapy.Field()
    Special_features = scrapy.Field()
    Product_benefits = scrapy.Field()
    Liquid_volume = scrapy.Field()
    Recommended_uses_for_product = scrapy.Field()
