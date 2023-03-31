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


def find_year(date_string):
    today = datetime.date.today()
    date_formats = [
        ('%m/%d/%Y', None),
        ('%B %d', '%Y')
    ]

    for date_format, year_format in date_formats:
        try:
            parsed_date = datetime.datetime.strptime(date_string, date_format)
            if year_format is None:
                return parsed_date.year, parsed_date.month, parsed_date.day
            else:
                if parsed_date.month > today.month or (parsed_date.month == today.month and parsed_date.day > today.day):
                    parsed_date = parsed_date.replace(year=today.year - 1)
                else:
                    parsed_date = parsed_date.replace(year=today.year)
                return parsed_date.year, parsed_date.month, parsed_date.day
        except ValueError:
            pass

    return None, None, None
    

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
    date_formats = [
        r'\d{1,2}[\/\\-]\d{1,2}[\/\\-]\d{2,4}',
        r'\d{1,2}[\/\\-]\d{1,2}',
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2}(?:,\s*\d{2,4})?'
    ]

    for date_format in date_formats:
        date_match = re.search(date_format, text)
        if date_match:
            return date_match.group()
    return None


def process_html(html_file, end_date=None):
    with open(html_file, 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    current_date = None
    for element in soup.descendants:
        if not isinstance(element, Tag) or isinstance(element, Comment):
            continue

        if element.name == 'span':
            text = element.get_text(strip=True)

            # Find the date in the text
            date_string = extract_date_from_text(text)
            if date_string:
                year, month, day = find_year(date_string)
                if year and month and day:
                    current_date = datetime.date(year, month, day)
                    if end_date and current_date <= end_date:
                        break
        elif current_date and element.name == 'img' and element.has_attr('src'):
            image_path = os.path.join(os.path.dirname(html_file), element['src'])
            update_image_date_taken(image_path, current_date)

if __name__ == "__main__":
    html_file = 'photos/evie/EviesDailyCommunicationlog.html'
    end_date_string = '2023-03-29'  # Format: YYYY-MM-DD
    end_date = datetime.date.fromisoformat(end_date_string)
    process_html(html_file)
