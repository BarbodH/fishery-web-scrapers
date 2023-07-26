from bs4 import BeautifulSoup
import requests
import os


def scrap_page(url, dir):
    # Initialization
    html_text = requests.get(url).text
    soup = BeautifulSoup(html_text, "lxml")

    # Scrap HTML content to extract discussion text
    title_text = soup.find("h1", class_="page-title").text
    replies = soup.find_all("div", class_="bbp-reply-content entry-content is-magnific")

    # Write discussion text to text file
    # Note: '/' and '\' in file name cause runtime errors
    modified_title = title_text.replace("/", "-").replace("\\", "-")
    with open(f"{dir}/{modified_title}.txt", "a") as new_file:
        new_file.truncate(0)  # clear file content
        for reply in replies:
            if reply.find(is_immediate_p):
                reply_text = reply.find(is_immediate_p).text
                new_file.write(reply_text + "\n\n")


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
