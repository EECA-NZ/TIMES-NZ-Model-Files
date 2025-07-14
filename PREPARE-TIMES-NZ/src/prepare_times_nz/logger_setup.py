import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)  # Set to the lowest level you want to capture


class CustomFormatter(logging.Formatter):
    # Define colors and emojis for each log level
    COLORS = {
        logging.DEBUG: "\033[94m",  # Blue
        logging.INFO: "\033[92m",  # Green
        logging.WARNING: "\033[93m",  # Yellow
        logging.ERROR: "\033[91m",  # Red
        logging.CRITICAL: "\033[1;91m",  # Bright Red
    }

    EMOJIS = {
        logging.DEBUG: "🐞",
        logging.INFO: "",
        logging.WARNING: "⚠️",
        logging.ERROR: "❌",
        logging.CRITICAL: "🚨🚨🚨 CRITICAL 🚨🚨🚨",
    }

    RESET = "\033[0m"

    def format(self, record):
        color = self.COLORS.get(record.levelno, self.RESET)
        emoji = self.EMOJIS.get(record.levelno, "")
        msg = f"{color} {emoji}    {record.getMessage()}{self.RESET}"

        # regex some htmltags what's wrong with me
        # do my python logs need limited markup support?? I guess they do!
        # red
        msg = msg.replace("<red>", "\033[91m")
        msg = msg.replace("</red>", color)

        # blue
        msg = msg.replace("<blue>", "\033[94m")
        msg = msg.replace("</blue>", color)

        return msg


def setup_logging():
    handler = logging.StreamHandler()
    handler.setFormatter(CustomFormatter())
    logger = logging.getLogger()
    logger.handlers = [handler]


# Headers


def h1(text: str):
    line = "-" * (len(text) + 12)
    # logger.info("")
    logger.info(line)
    logger.info(f"----  {text}  ----")
    logger.info(line)


def h2(text: str):
    logger.info(f"----  {text}  ----")


# Colours


""""
Note: you must wrap the text in the markup for these, then define these in format()!
That's the only way to have the reset match whatever colour is in the log already!

Colour references:


black      \033[30m
red        \033[91m
green      \033[92m
yellow     \033[93m
blue       \033[94m
magenta    \033[95m
cyan       \033[96m
white      \033[97m
reset      \033[0m


Extra Extra
bold       \033[1m
dim        \033[2m
underline  \033[4m
blink      \033[5m (don’t use this unless u tryna give someone a seizure)

"""


def red_text(text):
    return f"<red>{text}</red>"


def blue_text(text):
    return f"<blue>{text}</blue>"


setup_logging()
