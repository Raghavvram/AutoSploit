#!/usr/bin/env python3
# -*- coding: utf-8 -*-

class color:
    GREEN = '\033[32m'
    CYAN = '\033[36m'
    RED = '\033[31m'
    YELLOW = '\033[33m'
    GRAY = '\033[90m'
    BOLD = '\033[1m'
    RESET = '\033[0m'


def info(text):
    print(f"{color.BOLD}{color.GREEN}[+]{color.RESET} {text}")


def prompt(text, lowercase=True):
    question = input(f"{color.BOLD}{color.CYAN}[?]{color.RESET} {text}: ")
    if lowercase:
        return question.lower()
    return question


def error(text):
    print(f"{color.BOLD}{color.RED}[!]{color.RESET} {text}")


def warning(text):
    print(f"{color.BOLD}{color.YELLOW}[-]{color.RESET} {text}")


def misc_info(text):
    print(f"{color.GRAY}[i]{color.RESET} {text}")
