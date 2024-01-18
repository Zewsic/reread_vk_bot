import threading
import time
import logging

logging.getLogger('sqlalchemy.engine').setLevel('CRITICAL')
logging.getLogger('vkbottle').setLevel('INFO')

if __name__ == "__main__":
    import vk_bot
    import vk_admin_bot
    vk_bot.run()