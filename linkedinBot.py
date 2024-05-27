
import os
import time
from telegram import Update, Bot
from telegram.ext import Updater, CommandHandler, MessageHandler, filters, ContextTypes, Application, CallbackContext
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Telegram bot token
TELEGRAM_TOKEN = '6332330468:AAFz9Mj3Bl1d2ANf9ug4IuB2PcsTvH2yYUE'

# LinkedIn credentials
LINKEDIN_EMAIL = ''
LINKEDIN_PASSWORD = ''

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Hello! Send me a LinkedIn post link, and I will send a message to the author.')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Send a LinkedIn post link, and I will send a message to the author.')

async def message_handler(update: Update, context: CallbackContext) -> None:
    message_text = update.message.text
    print("Received message:", message_text)  # Debugging statement
    try:
        post_link = extract_link_from_message(message_text)
        print("Extracted post link:", post_link)  # Debugging statement
        send_message_on_linkedin(post_link)
        await update.message.reply_text(f'Message sent to the author of the post: {post_link}')
    except ValueError as ve:
        print("ValueError:", ve)
        await update.message.reply_text('Please send a valid LinkedIn post link.')
    except Exception as e:
        print("Error processing message:", e)
        await update.message.reply_text('An unexpected error occurred. Please try again later.')

def extract_link_from_message(message_text: str) -> str:
    # Split the message text into words
    words = message_text.split()
    # Iterate through each word to find a LinkedIn post link
    for word in words:
        # Check if the word contains 'linkedin.com/feed'
        if 'linkedin.com/feed' in word:
            # Return the word if it contains the LinkedIn post link
            return word
    # If no LinkedIn post link is found, raise a ValueError
    raise ValueError("No valid LinkedIn post link found in the message.")

def send_message_on_linkedin(post_link):
    # Set up Selenium WebDriver
    driver = webdriver.Chrome()  # Provide path to your WebDriver if necessary

    try:
        # Open LinkedIn login page
        print("Navigating to LinkedIn login page")
        driver.get("https://www.linkedin.com/login")

        # Log in to LinkedIn
        email_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        print("Email input field found")
        email_input.send_keys(LINKEDIN_EMAIL)
        
        password_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "password"))
        )
        print("Password input field found")
        password_input.send_keys(LINKEDIN_PASSWORD)
        password_input.send_keys(Keys.RETURN)

        # Wait for the home page to load
        WebDriverWait(driver, 60).until(EC.url_contains("linkedin.com/feed/"))
        print("Login successful")

        # Visit the provided LinkedIn post link
        print(f"Navigating to post link: {post_link}")
        driver.get(post_link)

        # Scroll down to make sure all elements are loaded
        SCROLL_PAUSE_TIME = 2
        last_height = driver.execute_script("return document.body.scrollHeight")

        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(SCROLL_PAUSE_TIME)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height

        # Extract profile URLs of all commenters
        commenters = []
        try:
            comments_section = WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CLASS_NAME, 'comments-comments-list'))
            )
            comments = comments_section.find_elements(By.CLASS_NAME, 'comments-comment-item')
            print(f"Found {len(comments)} comments")

            for comment in comments:
                try:
                    commenter_profile = comment.find_element(By.CSS_SELECTOR, '[aria-label*="profile"]')
                    profile_url = commenter_profile.get_attribute('href')
                    commenters.append(profile_url)
                    print(f"Commenter profile found: {profile_url}")
                except NoSuchElementException:
                    print("No profile link found in this comment")
                    continue

        except TimeoutException:
            print("Timeout: Comments section did not load in time.")
        except NoSuchElementException as e:
            print(f"Error: Unable to find an element: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

        # Send a message to each commenter
        for commenter in commenters:
            send_direct_message(driver, commenter, "Thank you for your comment on my post!")

    except TimeoutException as te:
        print("TimeoutException occurred:", te)
        driver.save_screenshot('timeout_error_screenshot.png')  # Save a screenshot for debugging
        print("Screenshot saved as 'timeout_error_screenshot.png'")
    except NoSuchElementException as nsee:
        print("NoSuchElementException occurred:", nsee)
        driver.save_screenshot('nosuchelement_error_screenshot.png')  # Save a screenshot for debugging
        print("Screenshot saved as 'nosuchelement_error_screenshot.png'")
    except WebDriverException as wde:
        print("WebDriverException occurred:", wde)
        driver.save_screenshot('webdriver_error_screenshot.png')  # Save a screenshot for debugging
        print("Screenshot saved as 'webdriver_error_screenshot.png'")
    except Exception as e:
        print("An unexpected error occurred:", e)
        driver.save_screenshot('error_screenshot.png')  # Save a screenshot for debugging
        print("Screenshot saved as 'error_screenshot.png'")
    finally:
        driver.quit()

def send_direct_message(driver, profile_url, message):
    print(f"Attempting to send a message to: {profile_url}")
    driver.get(profile_url)
    try:
        # Wait and click the message button
        print("Waiting for the message button to be clickable...")
        message_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'artdeco-button artdeco-button--2 artdeco-button--primary ember-view pvs-profile-actions__action')]"))
        )
        message_button.click()

        # Wait and send keys to the message box
        print("Waiting for the message box to appear...")
        message_box = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'msg-form__contenteditable'))
        )
        message_box.send_keys(message)

        # Click the send button
        send_button = WebDriverWait(driver, 30).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(@class, 'msg-form__send-button artdeco-button artdeco-button--1')]"))
        )
        send_button.click()
        print("Message sent successfully.")
    except TimeoutException as te:
        print(f"Timeout while trying to send message to {profile_url}: {te}")
        driver.save_screenshot('timeout_error_screenshot.png')
    except NoSuchElementException as nsee:
        print(f"Element not found while trying to send message to {profile_url}: {nsee}")
        driver.save_screenshot('nosuchelement_error_screenshot.png')
    except WebDriverException as wde:
        print(f"WebDriver exception while trying to send message to {profile_url}: {wde}")
        driver.save_screenshot('webdriver_error_screenshot.png')
    except Exception as e:
        print(f"An unexpected error occurred while trying to send message to {profile_url}: {e}")
        driver.save_screenshot('message_sending_error.png')
    finally:
        print("Completed attempt to send message")


def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')

if __name__ == '__main__':
    print('Starting bot...')
    
    # Initialize the Application
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Register handlers
    application.add_handler(CommandHandler('start', start_command))
    application.add_handler(CommandHandler('help', help_command))
    application.add_handler(MessageHandler(filters.TEXT, message_handler))
    application.add_error_handler(error_handler)

    # Start polling
    print('Polling...')
    application.run_polling()
