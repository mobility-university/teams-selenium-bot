#!/usr/bin/env python3
import time
import os
import sys

from selenium import webdriver
from selenium.common import exceptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import html


def launch_browser():
    config = {
        "email": os.environ["USER"],
        "password": os.environ["PASSWORD"],
        "headless": True,
    }
    browser = None

    def wait_until_found(sel, timeout):
        try:
            element_present = EC.visibility_of_element_located((By.CSS_SELECTOR, sel))
            WebDriverWait(browser, timeout).until(element_present)

            return browser.find_element("css selector", sel)
        except exceptions.TimeoutException:
            with open("failures/failure.html", "w") as file:
                file.write(browser.page_source)
            browser.save_screenshot("failures/failure.png")
            print(f"Timeout waiting for element: {sel}")
            return None

    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--use-fake-ui-for-media-stream")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--mute-audio")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-logging"])

    if "headless" in config and config["headless"]:
        chrome_options.add_argument("--headless")
        print("Enabled headless mode")

    browser = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)

    window_size = browser.get_window_size()
    if window_size["width"] < 950:
        browser.set_window_size(950, window_size["height"])

    def insert_into_field(field, content):
        element = wait_until_found(field, 30)
        assert element
        element.send_keys(content)
        time.sleep(1)

    browser.get("https://teams.microsoft.com")
    time.sleep(3)
    insert_into_field("input[type='email']", config["email"])
    # find the element again to avoid StaleElementReferenceException
    insert_into_field("input[type='email']", Keys.ENTER)
    if not wait_until_found("input[type='password']", 30):
        wait_until_found("a[id='idA_PWD_SwitchToPassword']", 5).click()
    insert_into_field("input[type='password']", config["password"])
    # find the element again to avoid StaleElementReferenceException
    insert_into_field("input[type='password']", Keys.ENTER)

    wait_until_found("input[id='idBtn_Back']", 30).click()
    wait_until_found(".use-app-lnk", 30).click()

    time.sleep(1)
    wait_until_found("button.app-bar-link > ng-include > svg.icons-chat", 30).click()

    time.sleep(10)
    return browser


def open_questions(browser, self_check_user=None):
    timeout = 5

    def send_message(text):
        for _ in range(20):
            try:
                while not browser.find_elements(By.CSS_SELECTOR, ".cke_textarea_inline"):
                    pass
                QUOTE = '"'
                RE = '\\"'
                browser.execute_script(
                    f'arguments[0].innerHTML = "{html.escape(text).replace(QUOTE, RE)}"',
                    browser.find_element(By.CSS_SELECTOR, ".cke_textarea_inline"),
                )
                time.sleep(1)
                browser.find_element(By.CSS_SELECTOR, 'button[data-tid="newMessageCommands-send"]').click()

                time.sleep(1)
                return
            except Exception as exception:
                with open("failures/failure.html", "w") as file:
                    file.write(browser.page_source)

                browser.save_screenshot("failures/failure.png")
                print(f"failed to send {text} cause {exception}")
        send_message("failed to send answer.")

    while True:
        try:
            for contact in browser.find_element(By.CSS_SELECTOR, 'div[data-tid="active-chat-list"]').find_elements(
                By.CSS_SELECTOR, ".cle-item"
            ):
                WebDriverWait(browser, timeout).until(EC.visibility_of_element_located((By.CSS_SELECTOR, "img")))
                qr_box = browser.find_elements(By.CSS_SELECTOR, "#ngdialog1")
                if qr_box:
                    qr_box[0].find_element(By.CSS_SELECTOR, ".icons-close").click()
                email = contact.find_element(By.CSS_SELECTOR, "img").get_attribute("data-upn")
                if self_check_user:
                    if email == self_check_user:
                        contact.click()
                        WebDriverWait(browser, timeout).until(
                            EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe"))
                        )
                        yield ("", send_message)
                        browser.switch_to.parent_frame()
                    continue
                contact.click()
                WebDriverWait(browser, timeout).until(
                    EC.frame_to_be_available_and_switch_to_it((By.CSS_SELECTOR, "iframe"))
                )
                WebDriverWait(browser, timeout).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, ".ui-chat__item__message"))
                )
                last_message = browser.find_elements(By.CSS_SELECTOR, ".ui-chat__item__message")[-1]
                if "MBB Mate" not in last_message.find_element(By.CSS_SELECTOR, "div.ui-chat__messageheader").text:
                    yield (last_message.find_element(By.CSS_SELECTOR, "div.ui-chat__messagecontent").text, send_message)
                browser.switch_to.parent_frame()
        except Exception as exception:
            browser.save_screenshot("failures/failure.png")
            raise exception


if __name__ == "__main__":
    assert len(sys.argv) in (1, 2)

    if sys.argv[-1] == "self-check":
        for _, answer_function in open_questions(launch_browser(), self_check_user=os.environ["SELF_CHECK_USER"]):
            answer_function(
                "self check message <3",
            )
            sys.exit(0)
        assert False, "cannot send test message"

    for question, answer_function in open_questions(launch_browser()):
        print(f"User asked: {question}")
        answer = f'dummy answer to {question}. Here should sit your answering logic'
        print(f"Bot Answered: {answer}")
        answer_function(answer)
