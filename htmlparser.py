from bs4 import BeautifulSoup
from PIL import Image
from PIL.ExifTags import TAGS
from PIL.ExifTags import GPSTAGS
import re
import datetime
import os    
from exif import Image
from bs4 import Comment
from bs4 import Tag
from dateutil.parser import parse as date_parse
from datetime import datetime

def update_image_date_taken(image_path, new_date, failed_images):
    # Convert date to EXIF format (YYYY:MM:DD HH:MM:SS)
    new_date_string = new_date.strftime('%Y:%m:%d %H:%M:%S')

    try:
        # Open the image and update the 'DateTimeOriginal' tag
        with open(image_path, 'rb') as image_file:
            image = Image(image_file)
            image.datetime_original = new_date_string

        # Save the image with updated EXIF data
        with open(image_path, 'wb') as image_file:
            image_file.write(image.get_file())

    except FileNotFoundError:
        print(f"Image not found: {image_path}")
    except KeyError:
        print(f"Unable to set 'DateTimeOriginal' for {image_path}")
    except Exception as e:
        print(f"Error processing image {image_path} with new date {new_date_string}: {e}")
        failed_images.append((image_path, new_date))

month_names = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*'
first_pattern = rf'\b({month_names})\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:,\s+(\d{{2,4}}))?\b'

def try_first_pattern(text, prev_date=None):
    date_match = re.search(first_pattern, text, flags=re.IGNORECASE)
    
    if not date_match:
        return None
    
    try:
        month_name, day, year = date_match.group(1,2,3)
    except IndexError:
        month_name, day = date_match.group(1,2)
        year = None

    # Match month
    month_match = re.search(month_names, month_name, flags=re.IGNORECASE)
    if month_match:
        month_name = month_match.group(0)
        month = datetime.strptime(month_name, '%B').month

    # Match day
    day = int(day)

    # Match year
    if year:
        year = int(year)
        if len(str(year)) <= 2:
            year += 2000

    # Set the year if missing
    if year is None:
        if prev_date:
            prev_year = prev_date.year
            test_date = datetime(prev_year, month, day)
            if test_date > prev_date:
                year = prev_year - 1
            else:
                year = prev_year
        else:
            year = 2023
            test_date = datetime(year, month, day)
            if test_date > datetime.now():
                year -= 1

    # Return the date as a datetime instance
    return datetime(year, month, day)

second_pattern = r'\b(\d{1,2})[-\/\\](\d{1,2})[-\/\\](?:(\d{2,4}))\b'

def try_second_pattern(text, prev_date=None):
    date_match = re.search(second_pattern, text, flags=re.IGNORECASE)
    
    if not date_match:
        return None
    try:
        month, day, year = date_match.group(1,2,3)
    except IndexError:
        month, day = date_match.group(1,2)
        year = None
    
    # Match month
    month = int(month)

    # Match day
    day = int(day)

    # Match year
    if year:
        year = int(year)
        if len(str(year)) <= 2:
            year += 2000

    # Set the year if missing
    if year is None:
        if prev_date:
            prev_year = prev_date.year
            test_date = datetime(prev_year, month, day)
            if test_date > prev_date:
                year = prev_year - 1
            else:
                year = prev_year
        else:
            year = 2023
            test_date = datetime(year, month, day)
            if test_date > datetime.now():
                year -= 1
    # Return the date as a datetime instance
    return datetime(year, month, day)


def parse_date_from_text(text, prev_date=None):
    if text is None:
        return None
    
    parsed_datetime = try_first_pattern(text, prev_date)
    if parsed_datetime:
        return parsed_datetime
    
    parsed_datetime = try_second_pattern(text, prev_date)

    if parsed_datetime:
        return parsed_datetime
    
    return None



def process_html(html_file, end_date=None, current_date=datetime.today()):
    with open(html_file, 'r') as file:
        content = file.read()

    soup = BeautifulSoup(content, 'html.parser')

    date = None
    previous_date_year = None

    datesParsed = 0
    imagesDated = 0

    failed_images = []

    for element in soup.descendants:
        if not isinstance(element, Tag):
            continue
        
        if element.name == 'span':
            possible_date = parse_date_from_text(element.string)
            if possible_date:
                date = possible_date
                # print(f"date parsed: {date} from date_string {element.string}")
                previous_date_year = date.year
                datesParsed += 1
                if end_date and current_date <= end_date:
                    print(f"end date reached: {end_date}" )
                    break

        if element.name == 'img':
            image_path = os.path.join(os.path.dirname(html_file), element['src'])
            if date:
                imagesDated += 1
                update_image_date_taken(image_path, date, failed_images)

    print(f"Dates parsed: {datesParsed}")
    print(f"Images dated: {imagesDated}")
    print(f"Failed images: {failed_images}")
    return soup


if __name__ == "__main__":
    html_file = 'photos/evie/EviesDailyCommunicationlog.html'
    end_date_string = '2023-03-29'  # Format: YYYY-MM-DD
    end_date = datetime.fromisoformat(end_date_string)

    soup = process_html(html_file)

