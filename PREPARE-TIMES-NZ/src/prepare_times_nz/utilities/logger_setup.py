"""
Logger Configuration and Utilities Module

This module configures and defines logging behavior for the entire application.
It provides a custom logging formatter that adds colored output to console logs,
making different log levels visually distinct.

Main Features:
- **CustomFormatter**: A logging formatter that applies ANSI color codes to log messages
  based on their severity (DEBUG, INFO, WARNING, ERROR, CRITICAL).
  This improves readability when scanning logs in the console.
- **HTML-like Color Markup**: Supports limited markup parsing for inline coloring
  within messages. For example, wrapping text in `<red>` or `<blue>` tags dynamically
  highlights parts of a log entry.
- **Convenience Functions**:
  - `h1(text)`: Emits a prominent heading in the logs to delineate sections.
  - `h2(text)`: Emits a secondary heading with less emphasis.
  - `red_text(text)`: Wraps a string with `<red>` tags for red highlighting.
    Good for drawing attention to key issues
  - `blue_text(text)`: Wraps a string with `<blue>` tags for blue highlighting.
    Good for highlighting field/address components of a message

Usage:
- Call `setup_logging()` once at application startup to initialize the logger.
- Use the `h1()` and `h2()` functions to visually separate major log sections.
- Use `red_text()` and `blue_text()` to inject colored text inline within log messages.

Color References:
- Debug: Blue
- Info: Green
- Warning: Yellow
- Error: Red
- Critical: Bright Red

Example:
    logger.info("This is an info message.")
    logger.warning(red_text"This warning contains red_text(red text!)")
    h1("Major Section Start")
    h2("Secondary section start)

Note:
The color codes rely on ANSI escape sequences and will work in most modern terminals.
Logs redirected to files will contain the raw escape codes unless handled separately.


"""

import logging

logger = logging.getLogger()


def setup_logging():
    """
    Runs all required commands to setup the logger handlers and set to
    required level (currently INFO)
    """
    handler = logging.StreamHandler()
    handler.setFormatter(CustomFormatter())
    logger.handlers = [handler]
    logger.setLevel(logging.INFO)


class CustomFormatter(logging.Formatter):
    """
    A custom logging formatter that adds ANSI color codes to log messages.

    This formatter applies color highlighting to log output based on the
    log level (DEBUG, INFO, WARNING, ERROR, CRITICAL), making logs easier
    to read in the console. In addition to coloring the entire message,
    it supports limited inline markup for selectively highlighting text
    within messages.
    """

    # Define colors for each log level
    COLORS = {
        logging.DEBUG: "\033[94m",  # Blue
        logging.INFO: "\033[92m",  # Green
        logging.WARNING: "\033[93m",  # Yellow
        logging.ERROR: "\033[91m",  # Red
        logging.CRITICAL: "\033[1;91m",  # Bright Red
    }

    RESET = "\033[0m"

    def format(self, record):
        """
        Format the specified log record as a string with color highlighting.

        This method applies ANSI color codes to the entire log message based
        on the record's log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        It also parses and replaces custom HTML-like tags (`<red>...</red>`,
        `<blue>...</blue>`) within the log message to allow inline color highlighting.

        Args:
            record (logging.LogRecord): The log record to be formatted.

        Returns:
            str: The formatted log message string with ANSI color codes applied.

        Notes:
            - If no matching color is found for a log level, the default terminal
              reset code is used.
            - Inline color tags are replaced only if they exactly match the predefined
              patterns (e.g., "<red>", "</red>").
            - The reset code applied to closing tags ensures that the inline color
              correctly blends with the outer log level color.

        Colour reference:

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
        blink      \033[5m

        """

        color = self.COLORS.get(record.levelno, self.RESET)
        msg = f"{color} {record.getMessage()}{self.RESET}"

        # We add limited parsing support for  html colour tags

        # red
        msg = msg.replace("<red>", "\033[91m")
        msg = msg.replace("</red>", color)

        # blue
        msg = msg.replace("<blue>", "\033[94m")
        msg = msg.replace("</blue>", color)

        return msg


# Headers
def h1(text: str):
    """
    takes the string input and returns a logging info formatted to make headings
    Allowing consistent log heading methods (h1)
    """
    line = "-" * (len(text) + 12)
    # logger.info("")
    logger.info(line)
    logger.info("----  {%s}  ----", text)
    logger.info(line)


def h2(text: str):
    """
    takes the string input and returns a log info formatted to make headings
    Allowing consistent log heading methods (h2)
    Less grandiose than h1
    """
    logger.info("----  {%s}  ----", text)


# Specific colours
def red_text(text):
    """
    Returns input text string with html tags for red
    """
    return f"<red>{text}</red>"


def blue_text(text):
    """
    Returns input text string with html tags for blue.
    """
    return f"<blue>{text}</blue>"


setup_logging()
