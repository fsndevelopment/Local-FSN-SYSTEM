import time
import logging
import argparse
import os
import json
import pandas as pd
from appium import webdriver
from appium.options.common import AppiumOptions
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# Suppress Appium and urllib3 HTTP logs
import logging
for noisy_logger in ["urllib3", "selenium.webdriver.remote.remote_connection", "httpcore", "httpx", "selenium.webdriver.remote.remote_connection.RemoteConnection"]:
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)

def load_devices(devices_file):
    with open(devices_file, 'r') as f:
        devices = json.load(f)
    # Normalize keys for all devices
    norm_devices = []
    for d in devices:
        if 'deviceName' in d:
            norm_devices.append(d)
        else:
            # Convert legacy keys
            norm_devices.append({
                'deviceName': d.get('Device Name', ''),
                'udid': d.get('UDID', ''),
                'appiumPort': int(d.get('Appium Port', 4723)),
                'wdaPort': int(d.get('WDA Port', 8100)),
                'bundleId': d.get('Bundle ID', '')
            })
    return norm_devices

def select_device(devices, name):
    for d in devices:
        if d['deviceName'].strip().lower() == name.strip().lower():
            return d
    raise ValueError(f"Device '{name}' not found in devices.json")

def load_usernames_from_xlsx(xlsx_path):
    df = pd.read_excel(xlsx_path)
    for col in df.columns:
        if col.lower() == 'username':
            return df[col].dropna().astype(str).tolist()
    return df.iloc[:, 0].dropna().astype(str).tolist()

class InstagramFollower:
    def __init__(self, driver, logger):
        self.driver = driver
        self.wait = WebDriverWait(driver, 10)
        self.logger = logger

    def debug_list_all_buttons(self):
        buttons = self.driver.find_elements(AppiumBy.XPATH, '//XCUIElementTypeButton')
        self.logger.info(f"[DEBUG] Found {len(buttons)} buttons on screen.")
        for i, btn in enumerate(buttons):
            try:
                self.logger.info(f"Button {i}: label={btn.get_attribute('label')}, name={btn.get_attribute('name')}, value={btn.get_attribute('value')}")
            except Exception as e:
                self.logger.info(f"Button {i}: Could not get attributes: {e}")

    def _navigate_to_explore(self):
        self.logger.debug("[STEP] Attempting to navigate to Explore tab...")
        self.logger.info("Navigating to Explore tab...")
        try:
            explore_button_xpath = '//XCUIElementTypeButton[@name="explore-tab"]'
            self.logger.debug(f"[XPATH] Looking for Explore button: {explore_button_xpath}")
            self.wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, explore_button_xpath))).click()
            self.logger.info("Successfully navigated to Explore tab.")
            time.sleep(2)
            return True
        except Exception as e:
            self.logger.error(f"[FAIL] Could not find/click Explore tab: {e}")
            self.logger.error(f"Failed to navigate to Explore tab: {e}")
            return False

    def _search_and_select_user(self, username):
        self.logger.debug(f"[STEP] Attempting to search for user: {username}")
        self.logger.info(f"Searching for user: '{username}'")
        try:
            search_bar_xpaths = [
                '//XCUIElementTypeSearchField[@name="Search"]',
                '//XCUIElementTypeSearchField[contains(@name, "search")]',
                '//XCUIElementTypeOther[@name="search-bar"]/XCUIElementTypeOther'
            ]
            search_bar = None
            for xpath in search_bar_xpaths:
                self.logger.debug(f"[XPATH] Looking for search bar: {xpath}")
                try:
                    search_bar = self.wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, xpath)))
                    if search_bar:
                        self.logger.info(f"Found search bar with XPath: {xpath}")
                        break
                except Exception as ex:
                    self.logger.debug(f"[FAIL] Search bar not found with {xpath}: {ex}")
            if not search_bar:
                self.logger.error("[FAIL] Could not find the search bar.")
                self.logger.error("Could not find the search bar.")
                return False
            search_bar.click(); time.sleep(1)
            search_bar.send_keys(username)
            self.logger.info(f"Typed '{username}' into search bar.")
            time.sleep(3)
            profile_link_xpath = f'//XCUIElementTypeStaticText[@name="{username}"]'
            self.logger.debug(f"[XPATH] Looking for profile link: {profile_link_xpath}")
            WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((AppiumBy.XPATH, profile_link_xpath)))
            results = self.driver.find_elements(AppiumBy.XPATH, profile_link_xpath)
            self.logger.info(f"Found {len(results)} potential profile links for '{username}'.")
            target_element = results[1] if len(results) > 1 else results[0]
            target_element.click()
            self.logger.info(f"Successfully clicked on '{username}' profile.")
            time.sleep(4)
            return True
        except Exception as e:
            self.logger.error(f"[FAIL] Could not search/select user {username}: {e}")
            self.logger.error(f"Failed during search and select user process: {e}")
            return False

    def _open_followers_list(self):
        self.logger.debug("[STEP] Attempting to open followers list...")
        self.logger.info("Opening followers list...")
        try:
            followers_button_xpath = '//XCUIElementTypeButton[@name="user-detail-header-followers"]'
            self.logger.debug(f"[XPATH] Looking for followers button: {followers_button_xpath}")
            self.wait.until(EC.element_to_be_clickable((AppiumBy.XPATH, followers_button_xpath))).click()
            self.logger.info("Successfully opened followers list.")
            time.sleep(3)
            return True
        except Exception as e:
            self.logger.error(f"[FAIL] Could not open followers list: {e}")
            self.logger.error(f"Failed to open followers list: {e}")
            return False

    def _follow_from_list(self, num_to_follow):
        self.logger.debug(f"[STEP] Attempting to follow {num_to_follow} users from list...")
        self.logger.info("[DEBUG] Listing all buttons before searching for follow buttons:")
        self.debug_list_all_buttons()
        follow_button_xpath = '//XCUIElementTypeButton[starts-with(@label, "Follow ")]'
        self.logger.info(f"[XPATH] Looking for follow buttons with: {follow_button_xpath}")
        self.logger.info(f"Starting to follow {num_to_follow} users...")
        followed_count = 0
        while followed_count < num_to_follow:
            if followed_count > 0 and followed_count % 8 == 0:
                self.logger.info("Followed 8 users, scrolling down to find more...")
                self._scroll_followers_list()
                time.sleep(2)
            try:
                available_buttons = self.driver.find_elements(AppiumBy.XPATH, follow_button_xpath)
                if not available_buttons:
                    self.logger.warning("[WARN] No 'Follow' buttons found on screen. Scrolling to search for more.")
                    self.logger.warning("No 'Follow' buttons found on screen. Scrolling to search for more.")
                    self._scroll_followers_list()
                    continue
                clicked_in_loop = False
                for button in available_buttons:
                    user_label = button.get_attribute("label")
                    if user_label and user_label.startswith("Follow "):
                        try:
                            button.click()
                            followed_count += 1
                            self.logger.debug(f"[CLICK] Clicked follow button for user. ({followed_count}/{num_to_follow})")
                            self.logger.info(f"Followed user. ({followed_count}/{num_to_follow}) - {user_label}")
                            clicked_in_loop = True
                            time.sleep(2)
                            break
                        except Exception as click_error:
                            self.logger.warning(f"[FAIL] Could not click button for {user_label}: {click_error}")
                            self.logger.warning(f"Could not click button for {user_label}: {click_error}")
                if not clicked_in_loop:
                    self.logger.info("[INFO] All visible buttons have been processed. Scrolling down.")
                    self.logger.info("All visible buttons have been processed. Scrolling down.")
                    self._scroll_followers_list()
            except Exception as e:
                self.logger.error(f"[FAIL] Error occurred during the follow loop: {e}")
                self.logger.error(f"An error occurred during the follow loop: {e}")
                break
        self.logger.info(f"Finished follow process. Total followed: {followed_count}")
        return followed_count >= num_to_follow

    def _scroll_followers_list(self):
        self.logger.debug("[STEP] Scrolling followers list...")
        try:
            window_size = self.driver.get_window_size()
            start_x = window_size['width'] // 2
            start_y = window_size['height'] * 0.8
            end_y = window_size['height'] * 0.2
            self.driver.swipe(start_x, start_y, start_x, end_y, duration=500)
            self.logger.debug("[SCROLL] Performed swipe to scroll followers list.")
        except Exception as e:
            self.logger.error(f"[FAIL] Error while scrolling followers list: {e}")
            self.logger.error(f"Error while scrolling followers list: {e}")

    def follow_from_usernames(self, usernames, num_to_follow=15):
        self.logger.debug(f"[STEP] Starting follow_from_usernames with {len(usernames)} usernames: {usernames}")
        for username in usernames:
            self.logger.info(f"--- Starting Follow Session: Searching for '{username}' to follow {num_to_follow} of their followers. ---")
            try:
                if not self._navigate_to_explore():
                    self.logger.error(f"[STOP] Could not navigate to Explore for {username}. Skipping.")
                    continue
                if not self._search_and_select_user(username):
                    self.logger.error(f"[STOP] Could not search/select user {username}. Skipping.")
                    continue
                if not self._open_followers_list():
                    self.logger.error(f"[STOP] Could not open followers list for {username}. Skipping.")
                    continue
                if not self._follow_from_list(num_to_follow):
                    self.logger.error(f"[STOP] Could not follow users from list for {username}. Skipping.")
                    continue
                self.logger.info(f"--- Follow Session Completed Successfully for {username} ---")
            except Exception as e:
                self.logger.error(f"[FAIL] Exception in follow session for {username}: {e}")
                self.logger.error(f"An error occurred during the follow session for {username}: {e}")
                continue

def main():
    parser = argparse.ArgumentParser(description="Instagram Follow-Only Bot")
    parser.add_argument('--device', required=True, help='Device name as in devices.json')
    parser.add_argument('--xlsx', default='/Users/jacqubsf/Desktop/Instwarm, following/Models.xlsx', help='Path to the XLSX file with usernames')
    parser.add_argument('--num', type=int, default=15, help='Number of users to follow per username')
    parser.add_argument('--devices-file', default='devices.json', help='Path to devices.json')
    args = parser.parse_args()

    # Logging setup
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('follow_only')

    devices = load_devices(args.devices_file)
    device = select_device(devices, args.device)

    appium_url = f"http://localhost:{device['appiumPort']}"
    caps = {
        "platformName": "iOS",
        "appium:deviceName": device['deviceName'],
        "appium:udid": device['udid'],
        "appium:automationName": "XCUITest",
        "appium:wdaLocalPort": int(device['wdaPort']),
        "appium:updatedWDABundleId": device['bundleId'],
        "appium:useNewWDA": False,
        "appium:skipServerInstallation": True,
        "appium:noReset": True
    }
    options = AppiumOptions().load_capabilities(caps)

    logger.info(f"Connecting to Appium at {appium_url} with device {device['deviceName']}")
    driver = webdriver.Remote(appium_url, options=options)
    logger.info("Appium driver initialized. Please manually open Instagram on your device now.")
    time.sleep(15)
    logger.info("Starting follow process...")

    follower = InstagramFollower(driver, logger)
    usernames = load_usernames_from_xlsx(args.xlsx)
    follower.follow_from_usernames(usernames, num_to_follow=args.num)

    logger.info("Follow process completed. Quitting driver.")
    driver.quit()

if __name__ == "__main__":
    main() 