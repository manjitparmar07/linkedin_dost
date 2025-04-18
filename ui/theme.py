from PyQt6.QtGui import QHoverEvent


class Theme:
    sidebar = """
        background-color: #1E1E2F;
        color: white;
    """
    sidebar_title = """
        font-size: 18px;
        font-weight: bold;
        padding: 15px;
        color: #00ADB5;
    """
    nav_button = """
        background-color: #1E1E2F;
        color: white;
        padding: 10px;
        text-align: left;
        font-size: 14px;
        border: none;
    """
    nav_button: QHoverEvent = """
        background-color: #00ADB5;
        color: black;
    """
    header = """
        background-color: #393E46;
        padding: 8px;
    """
    header_title = """
        font-size: 16px;
        color: white;
    """
    header_button = """
        background-color: transparent;
        color: white;
        border: none;
        font-size: 16px;
    """
