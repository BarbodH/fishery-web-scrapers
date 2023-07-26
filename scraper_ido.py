from bs4 import BeautifulSoup
import requests
import os
import re
from datetime import datetime


def scrap_page(url, dir):
    # Initialization
    html_text = requests.get(url).text
    soup = BeautifulSoup(html_text, "lxml")

    # Scrap HTML content to extract discussion text
    title_text = soup.find("h1", class_="page-title").text
    reply_divs = soup.find_all("article", class_="cf")

    # Write discussion text to text file
    # Note: '/' and '\' in file name cause runtime errors
    modified_title = title_text.replace("/", "-").replace("\\", "-")
    with open(f"{dir}/{modified_title}.txt", "a") as new_file:
        new_file.truncate(0)  # clear file content
        for reply_div in reply_divs:
            if reply_div:
                # Extract data corresponding to each response
                id = re.search(r"\d+", reply_div["id"]).group()
                author = reply_div.find("span", "bbp-author-name").text

                date_raw = reply_div.find("span", "bbp-reply-post-date").text
                date = datetime.strptime(date_raw, "%B %d, %Y at %I:%M %p")

                num_posts = re.search(
                    r"\d+", reply_div.find("div", "bbp-author-post-count").text
                ).group()

                reply_paragraphs = reply_div.find(
                    "div", class_="bbp-reply-content entry-content is-magnific"
                ).find_all(is_immediate_p)
                reply = " ".join(
                    [
                        paragraph.get_text().strip().replace("\n", " ")
                        for paragraph in reply_paragraphs
                    ]
                )

                new_file.write(f"{id}\n{author}\n{date}\n{num_posts}\n{reply}\n\n")


def is_immediate_p(tag):
    return tag.name == "p" and tag.parent.name != "blockquote"


def main():
    base_url = "https://www.in-depthoutdoors.com/community/forums/forum/fishing/canada/canadagen"

    html_text = requests.get(base_url, "lxml").text
    soup = BeautifulSoup(html_text, "lxml")

    # Obtain the maximum number of pages
    indices = soup.find_all("a", class_="page-numbers")
    max_index = int(indices[-2].text)

    # Retrieve contents of all pages
    base_path = os.getcwd()
    for page_index in range(1, max_index + 1):
        # Create a new directory for each navigation page
        dir_name = f"forums-page-{page_index}"
        dir = os.path.join(base_path, f"ido-content", dir_name)
        if not os.path.exists(dir):
            os.makedirs(dir)

        # Retrieve all the forum names in the current navigation page
        url = f"{base_url}/page/{page_index}"
        current_navigation_html_text = requests.get(url).text
        soup = BeautifulSoup(current_navigation_html_text, "lxml")

        links = soup.find_all("a", "bbp-topic-permalink")
        for link in links:
            scrap_page(link["href"], dir)


if __name__ == "__main__":
    main()
