import asyncio
import json
import multiprocessing

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import csv
from config_reader import config
from groq_req import GroqClient


class TwitterAutomation:
    def __init__(self, email, password, new_password, name):
        self.driver = self.init_driver()
        self.email = email
        self.password = password
        self.new_password = new_password
        self.name = name

    def init_driver(self):
        """Инициализация драйвера"""
        driver = webdriver.Chrome()  # Путь к chromedriver
        driver.maximize_window()
        return driver

    def login_to_twitter(self):
        """Логин в Twitter"""
        self.driver.get('https://twitter.com/login')

        self.enter_email(self.email)

        time.sleep(2)

        security_type = self.check_security_message()
        if security_type:
            if security_type == "phone":
                self.enter_email(self.name)
            else:
                self.enter_email(self.email)

        time.sleep(2)
        self.enter_password(self.password)

    def enter_email(self, email):
        """Ввод email"""
        email_input = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.NAME, 'text')))
        email_input.send_keys(email)
        email_input.send_keys(Keys.RETURN)

    def enter_password(self, password):
        """Ввод пароля"""
        password_input = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.NAME, 'password')))
        password_input.send_keys(password)
        password_input.send_keys(Keys.RETURN)

    def check_security_message(self):
        """Проверка сообщения об необычных попытках входа"""
        try:
            warning_text_1 = "Мы заметили несколько необычных попыток входа в вашу учетную запись. В целях обеспечения ее безопасности просим вас ввести свой номер телефона (включая код страны, например +1) или адрес электронной почты, чтобы подтвердить, что это действительно вы."
            warning_text_2 = "Мы заметили несколько необычных попыток входа в вашу учетную запись. В целях обеспечения ее безопасности просим вас ввести свой номер телефона или имя пользователя, чтобы подтвердить, что это действительно вы."

            message_element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located(
                    (By.XPATH, f"//*[contains(text(), '{warning_text_1}') or contains(text(), '{warning_text_2}')]")
                )
            )

            if warning_text_2 in self.driver.page_source:
                return "phone"
            elif warning_text_1 in self.driver.page_source:
                return "email"
        except:
            print("Сообщение не найдено.")
            return False

    def change_password(self):
        """Изменение пароля"""
        time.sleep(2)
        try:
            self.driver.get('https://twitter.com/settings/password')
            time.sleep(4)

            current_password_input = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.NAME, 'current_password')))
            current_password_input.send_keys(self.password)

            time.sleep(2)

            new_password_input = self.driver.find_element(By.NAME, 'new_password')
            new_password_input.send_keys(self.new_password)

            time.sleep(2)

            confirm_password_input = self.driver.find_element(By.NAME, 'password_confirmation')
            confirm_password_input.send_keys(self.new_password)

            save_button = self.driver.find_element(By.XPATH, "//button[@data-testid='settingsDetailSave']")
            save_button.click()
        except Exception as e:
            print(f"Ошибка при изменении пароля: {e}")

    def save_to_csv(self):
        """Сохранение данных в CSV"""
        with open('twitter_account_data.csv', 'a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([self.email, self.new_password])

    def create_post(self, text):
        time.sleep(2)
        """Создание поста (твита)"""
        try:
            self.driver.get('https://twitter.com/compose/tweet')

            tweet_box = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//div[@aria-label='Post text']"))
            )
            tweet_box.send_keys(text)
            tweet_box.send_keys(" ")

            time.sleep(2)

            tweet_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[@data-testid='tweetButton'] | //button[@data-testid='tweetButtonInline']"))
            )

            tweet_button.click()
        except Exception as e:
            print(f"Ошибка при создании поста: {e}")

    def close_browser(self):
        """Закрытие браузера"""
        # input("Нажмите Enter, чтобы закрыть браузер...")
        self.driver.quit()


async def run_bot_async(email, password, new_password, name):
    bot = TwitterAutomation(email, password, new_password, name)
    groq_token = config.groq_token.get_secret_value()

    try:
        bot.login_to_twitter()
        post_text = await GroqClient.get_chat_completion(groq_token)
        bot.change_password()
        bot.save_to_csv()
        bot.create_post(post_text)
    finally:
        bot.close_browser()
        # input("Нажмите Enter, чтобы закрыть браузер...")


def run_bot(email, password, new_password, name):
    asyncio.run(run_bot_async(email, password, new_password, name))


def load_accounts_from_json(file_path):
    with open(file_path, 'r') as file:
        accounts = json.load(file)
    return [(account['email'], account['password'], account['new_password'], account['name']) for account in accounts]


if __name__ == "__main__":
    accounts = load_accounts_from_json('accounts.json')

    processes = []
    for account in accounts:
        p = multiprocessing.Process(target=run_bot, args=(account))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()
