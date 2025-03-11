# pipelines.py
import json
import os
from datetime import datetime

class CategoryJsonWriterPipeline:
    def open_spider(self, spider):
        self.files = {}
        self.exporters = {}

    def close_spider(self, spider):
        # Close all open files at the end
        for f in self.files.values():
            f.write(']')
            f.close()

    def process_item(self, item, spider):
        # Determine the category
        cat = item.get("category", "default")

        # If we haven't opened a file for this category yet, create one
        if cat not in self.files:
            filename = f"{cat}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            f = open(filename, 'w', encoding='utf8')
            f.write('[')
            self.files[cat] = f
            self.first_item = {cat: True}  # track commas per category
        else:
            f = self.files[cat]

        # Write comma if not first item
        if not self.first_item[cat]:
            f.write(',')
        else:
            self.first_item[cat] = False

        # Dump the item JSON
        line = json.dumps(dict(item), ensure_ascii=False, indent=4)
        f.write('\n' + line + '\n')

        return item
