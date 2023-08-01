from bs4 import BeautifulSoup
import requests
import os
import re
from datetime import datetime
import csv


def scrap_page(url, dir, truncate_file):
    # Initialization
    html_text = requests.get(url).text
    soup = BeautifulSoup(html_text, "lxml")

    # Scrap HTML content to extract discussion text
    title_text = soup.find("td", class_="navbar").text.strip()
    reply_divs = soup.find_all(is_reply_div)

    # Write discussion text to text file
    # Note: '/' and '\' in file name cause runtime errors
    modified_title = title_text.replace("/", "-").replace("\\", "-")
    with open(f"{dir}/{modified_title}.csv", "a") as new_file:
        if truncate_file:
            new_file.truncate(0)  # clear file content
        csv_writer = csv.writer(new_file)

        for reply_div in reply_divs:
            if reply_div:
                # Extract data corresponding to each response
                id = re.search(r"\d+", reply_div.get("id")).group()

                if reply_div.find("a", "bigusername"):
                    author = reply_div.find("a", "bigusername").text.strip()
                else:
                    author = "Guest"

                date_div = reply_div.find_all("div", class_="normal")[1]
                date_raw = date_div.text.strip()
                date = datetime.strptime(date_raw, "%m-%d-%Y, %I:%M %p")

                if not "n/a" in reply_div.find(is_num_posts).text:
                    num_posts = (
                        re.search(
                            r"\d{1,3}(?:,\d{3})*",
                            reply_div.find(is_num_posts).text.strip(),
                        )
                        .group()
                        .replace(",", "")
                        .replace("  ", "")
                    )
                else:
                    num_posts = 0

                reply_intermediate = (
                    reply_div.find(is_reply_message)
                    .get_text()
                    .strip()
                    .replace("\n", "")
                )
                reply = re.sub(r"\s+", " ", reply_intermediate)

                # Organize the extracted information into a CSV file
                csv_writer.writerow([id, author, date, num_posts, reply])

        page_ref = soup.find(is_page_reference)
        if page_ref:
            pages = re.findall(r"\d+", page_ref.text)
            # pages[0] -> first page, pages[1] -> last page
            if pages[0] < pages[1]:
                # next_anchor = soup.find("a", {"rel": "next"})
                new_page = str(int(pages[0]) + 1)
                if "&page=" in url:
                    new_url = re.sub(r"page=\d+", f"page={new_page}", url)
                else:
                    new_url = f"{url}&page={new_page}"

                scrap_page(new_url, dir, False)


def is_thread_title(tag):
    if tag.get("id"):
        return "thread_title" in tag.get("id")
    return False


def is_reply_div(tag):
    if tag.get("class") and tag.get("id"):
        return "tborder" in tag.get("class") and "post" in tag.get("id")
    return False


def is_num_posts(tag):
    if tag.text and tag.parent.get("class"):
        return tag.name == "div" and "Posts" in tag.text
    return False


def is_reply_message(tag):
    if tag.get("id"):
        return tag.name == "div" and "post_message" in tag.get("id")
    return False


def is_page_reference(tag):
    if tag.get("class") and tag.text:
        return "vbmenu_control" in tag.get("class") and "Page" in tag.text
    return False


def main():
    base_url = "https://www.walleyecentral.com/forums/forumdisplay.php?f=7&order=desc"

    html_text = requests.get(base_url, "lxml").text
    soup = BeautifulSoup(html_text, "lxml")

    # Obtain the maximum number of pages
    nav_buttons = soup.find_all("td", class_="alt1")
    first_last_button = [button for button in nav_buttons if "Last" in button.text][0]
    max_index = re.findall(r"\d+", first_last_button.a.get("href"))[-1]

    # Retrieve contents of all pages
    base_path = os.getcwd()
    for page_index in range(1, 6):  # max_index + 1
        # Create a new directory for each navigation page
        dir_name = f"forums-page-{page_index}"
        dir = os.path.join(base_path, f"content-wc", dir_name)
        if not os.path.exists(dir):
            os.makedirs(dir)

        # Retrieve all the forum names in the current navigation page
        url = f"{base_url}&page={60}"
        current_navigation_html_text = requests.get(url).text
        soup = BeautifulSoup(current_navigation_html_text, "lxml")

        anchors = soup.find_all(is_thread_title)
        for anchor in anchors:
            partial_link = anchor.get("href")
            link = f"https://www.walleyecentral.com/forums/{partial_link}"
            scrap_page(link, dir, True)


if __name__ == "__main__":
    main()
