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


def find_year(date_string, previous_date_year=None, current_date=datetime.date.today()):
    year_match = re.search(r'\b\d{4}\b', date_string)
    if year_match:
        return int(year_match.group())
    else:
        # Check for a two-digit year with different separators
        two_digit_year_match = re.search(r'\b\d{1,2}[\/\\-](\d{2})\b', date_string)
        if two_digit_year_match:
            two_digit_year = int(two_digit_year_match.group(1))
            # Assume 1900-2099 for two-digit years
            if 0 <= two_digit_year <= 99:
                return 2000 + two_digit_year if two_digit_year < 50 else 1900 + two_digit_year

        if previous_date_year:
            month_day_match = re.search(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}', date_string)
            if month_day_match:
                month_day = datetime.datetime.strptime(month_day_match.group(), '%B %d')
                if month_day.month == 12:
                    return previous_date_year - 1
                else:
                    return previous_date_year
        else:
            # Assume current year, but subtract 1 if the resulting date would be in the future
            inferred_year = current_date.year
            month_day_match = re.search(r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}', date_string)
            if month_day_match:
                month_day = datetime.datetime.strptime(month_day_match.group(), '%B %d')
                inferred_date = datetime.date(inferred_year, month_day.month, month_day.day)
                if inferred_date > current_date:
                    inferred_year -= 1
            return inferred_year

    return None


def update_image_date_taken(image_path, new_date):
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

def extract_date_from_text(text):
    if text is None:
        return None
    date_formats = [
        r'\d{1,2}[\/\\-]\d{1,2}[\/\\-]\d{2,4}',
        r'\d{1,2}[\/\\-]\d{1,2}',
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:,\s*\d{2,4})?'
    ]

    for date_format in date_formats:
        date_match = re.search(date_format, text)
        if date_match:
            print(f"date extracted {date_match}")
            return date_match.group()
    return None

def parse_date(date_string, previous_date_year=None, current_date=datetime.date.today()):
    year = find_year(date_string, previous_date_year, current_date)

    month_names = r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*'
    month_match = re.search(month_names, date_string)
    if month_match:
        month = datetime.datetime.strptime(month_match.group(), '%B').month
    else:
        month = int(re.search(r'\d+', date_string).group())

    day_match = re.search(r'\b\d{1,2}[\/\\\-](\d{1,2})', date_string)
    if day_match:
        day = int(day_match.group(1))
    else:
        day = int(re.search(r'\d+', re.sub(month_names, '', date_string)).group())

    if year:
        parsed_date = datetime.date(year, month, day)
    else:
        raise ValueError(f"Unable to parse date string: {date_string}")

    return parsed_date


def process_html(html_file, end_date=None, current_date=datetime.date.today()):
    with open(html_file, 'r') as file:
        content = file.read()

    soup = BeautifulSoup(content, 'html.parser')

    date = None
    previous_date_year = None

    datesParsed = 0
    imagesDated = 0

    for element in soup.descendants:
        if not isinstance(element, Tag):
            continue
        
        if element.name == 'span':
            date_string = extract_date_from_text(element.string)
            if date_string:
                date = parse_date(date_string, previous_date_year)
                print(f"date parsed: {date} from date_string {date_string}")
                previous_date_year = date.year
                datesParsed += 1
                if end_date and current_date <= end_date:
                    print(f"end date reached: {end_date}" )
                    break

        if element.name == 'img':
            image_path = os.path.join(os.path.dirname(html_file), element['src'])
            if date:
                imagesDated += 1
                update_image_date_taken(image_path, date)

    print(f"Dates parsed: {datesParsed}")
    print(f"Images dated: {imagesDated}")
    return soup


if __name__ == "__main__":
    html_file = 'photos/evie/EviesDailyCommunicationlog.html'
    end_date_string = '2023-03-29'  # Format: YYYY-MM-DD
    end_date = datetime.date.fromisoformat(end_date_string)
    process_html(html_file)
