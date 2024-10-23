from selenium import webdriver
from selenium.webdriver.firefox.webdriver import WebDriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
import time

#  using firefox, connect to host.docker.internal:4444
firefox_options = Options()
# firefox_options.add_argument("--headless")

analyzed_post_ids = set()


def read_analyzed_post_ids():
    with open("imgflip-memes-dataset-stage1.tsv", "r") as f:
        for line in f:
            analyzed_post_ids.add(line.split("\t")[0][len("imgflip-post-") :])


def append_to_file(line: str):
    with open("imgflip-memes-dataset-stage1.tsv", "a") as f:
        f.write(line + "\n")


read_analyzed_post_ids()


def analyze_post(category: str, post: WebElement):
    title_elem = post.find_element(By.CSS_SELECTOR, "h2 > a")
    id_str = title_elem.get_attribute("href").split("/i/")[-1]
    id = "imgflip-post-" + id_str

    if id_str in analyzed_post_ids:
        print(f"Already analyzed {id_str}")
        return

    title = title_elem.text

    img_elem = post.find_element(By.CSS_SELECTOR, ".base-img")

    image_url = "https:" + (
        img_elem.get_attribute("src") or img_elem.get_attribute("data-src")
    )

    base_view_count = post.find_element(By.CSS_SELECTOR, ".base-view-count").text
    # 382 views, 2 upvotes
    # 382 views, 2 comments
    # 16,386 views, 103 upvotes, 22 comments

    # extract upvote count
    split = base_view_count.split(" ")
    upvote = 0
    comment_count = 0
    # from first to last
    # if we find the word "comments", then read the number before it
    # if we find the word "upvotes", then read the number before it
    for i in range(len(split)):
        if "comments" in split[i]:
            comment_count = int(split[i - 1])
        if "upvotes" in split[i]:
            upvote = int(split[i - 1])

    line = f"{id}\t{category}\t{title}\t{image_url}\t{upvote}\t{comment_count}"
    append_to_file(line)


def analyze_page(category: str, page_number: int):
    print(f"Analyzing template {category} page {page_number}")
    driver.get(f"https://imgflip.com{category}?page={page_number}&sort=top-365d")
    elements = driver.find_elements(By.CSS_SELECTOR, "#page > #base-left > .base-unit")
    for element in elements:
        analyze_post(category, element)


def analyze_template_catalog(page_number: int):
    categories: list[str] = []
    driver.get(f"https://imgflip.com/memetemplates?page={page_number}")
    elements = driver.find_elements(
        By.CSS_SELECTOR, "#page > #mt-boxes-wrap > .mt-boxes > .mt-box"
    )
    for element in elements:
        h3_a = element.find_element(By.CSS_SELECTOR, "h3 > a")
        href = h3_a.get_attribute("href")
        # remove https://imgflip.com
        categories.append(href[len("https://imgflip.com") :])
    return categories


def main():
    # 3 * 40 * 10 * 14 = 16800
    for j in range(1):
        try:
            print(f"Analyzing template catalog page {j}")
            categories = analyze_template_catalog(j)  # 40 categories
            print(categories)

            for category in categories:
                try:
                    print(f"Analyzing template {category}")
                    for i in range(1, 11):
                        analyze_page(category, i)
                except KeyboardInterrupt:
                    raise
                except Exception as e:
                    print(e)
                time.sleep(10)
        except KeyboardInterrupt:
            return
        except Exception as e:
            print(e)

driver = webdriver.Remote(
    command_executor="http://host.docker.internal:4444/wd/hub",
    options=firefox_options,
)
# use local firefox
# driver = webdriver.Firefox(options=firefox_options)
# driver = webdriver.Firefox(options=firefox_options)

main()

driver.quit()
