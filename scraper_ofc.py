from bs4 import BeautifulSoup
import requests
import os
import re
from datetime import datetime
import csv
import sys


def scrape_page(url, dir):
    # Initialization
    html_text = requests.get(url).text
    soup = BeautifulSoup(html_text, "lxml")

    # Scrap HTML content to extract discussion text
    try:
        title_text = soup.find(
            "h1", class_="ipsType_pageTitle ipsContained_container"
        ).text.strip()
    except:
        print(f"Forum unavailable at '{url}'")
        return
    reply_divs = soup.find_all("article", class_="cPost")

    # Write discussion text to text file
    # Note: '/' and '\' in file name cause runtime errors
    modified_title = title_text.replace("/", "-").replace("\\", "-")
    with open(f"{dir}/{modified_title}.csv", "a") as new_file:
        new_file.truncate(0)  # clear file content
        csv_writer = csv.writer(new_file)
        for reply_div in reply_divs:
            if reply_div:
                # Extract data corresponding to each response
                id = re.search(r"\d+", reply_div.get("id")).group()
                author = reply_div.find("h3", class_="cAuthorPane_author").text.strip()

                date_raw = reply_div.find("a", class_="ipsType_blendLinks").time.get(
                    "title"
                )
                date = datetime.strptime(date_raw, "%m/%d/%Y %I:%M %p")

                # For guest users, num_posts is not be available and should be wrapped with a try & except blocks
                author_panel = reply_div.find("ul", class_="cAuthorPane_info")
                try:
                    num_posts = (
                        re.search(
                            r"\d{1,3}(?:,\d{3})*",
                            author_panel.find("a", class_="ipsType_blendLinks").get(
                                "title"
                            ),
                        )
                        .group()
                        .replace(",", "")
                    )
                except:
                    num_posts = 0  # indicating guest user

                reply_paragraphs = reply_div.find(
                    "div", {"data-role": "commentContent"}
                ).find_all(is_reply_p)
                reply = " ".join(
                    [
                        paragraph.get_text().strip().replace("\n", " ")
                        for paragraph in reply_paragraphs
                    ]
                )

                # Organize the extracted information into a CSV file
                csv_writer.writerow([id, author, date, num_posts, reply])

        pagination_next_button = soup.find("li", class_="ipsPagination_next")
        if (
            pagination_next_button
            and not "ipsPagination_inactive" in pagination_next_button.get("class")
        ):
            scrape_page(pagination_next_button.a.get("href"), dir)


def is_reply_p(tag):
    return tag.name == "p" and tag.parent.parent.name != "blockquote"


def main():
    if len(sys.argv) >= 2:
        # General discussion
        if sys.argv[1] == "gd":
            base_url = "https://ontariofishingcommunity.com/forum/2-general-discussion/"
        # Fishing news
        elif sys.argv[1] == "fn":
            base_url = "https://ontariofishingcommunity.com/forum/39-fishing-news/"
        else:
            print("Error: Invalid string argument.")
            return
    # Default base url corresponds to fishing news since the dataset is smaller
    # in case of accidental execution of the script.
    else:
        base_url = "https://ontariofishingcommunity.com/forum/39-fishing-news/"

    html_text = requests.get(base_url, "lxml").text
    soup = BeautifulSoup(html_text, "lxml")

    # Obtain the maximum number of pages
    pagination_text = soup.find("li", class_="ipsPagination_pageJump").a.get_text()
    pagination_indices = re.findall(r"\d+", pagination_text)
    max_index = int(pagination_indices[1])

    # Retrieve contents of all pages
    base_path = os.getcwd()
    for page_index in range(1201, 1301):
        # Create a new directory for each navigation page
        dir_name = f"forums-page-{page_index}"
        dir = os.path.join(base_path, f"content-ofc-gd", dir_name)
        if not os.path.exists(dir):
            os.makedirs(dir)

        # Retrieve all the forum names in the current navigation page
        url = f"{base_url}/page/{page_index}"
        current_navigation_html_text = requests.get(url).text
        soup = BeautifulSoup(current_navigation_html_text, "lxml")

        link_spans = soup.find_all("span", class_="ipsType_break ipsContained")
        for span in link_spans:
            scrape_page(span.a.get("href"), dir)
            print(span.a.get("href"))


if __name__ == "__main__":
    main()
