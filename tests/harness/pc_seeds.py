"""Run-time assembly of leak-shaped test strings (test support only).

The repository scans every commit for home paths, private addresses, internal host names,
e-mail addresses and credential shapes. A test that needs one of those shapes therefore
cannot hold it as a literal: each function here joins short fragments inside its body, so
no source line holds a whole leak-shaped value and the repository's own scan of this folder
stays clean. The functions return plain strings and touch nothing else.

This module is exempt from the no-delete static scan by name (the exemption set is asserted
to be exactly this module and pc_testutil), and it is the only place where seeds are built.
"""
from __future__ import annotations

_SLASH = "/"
_BACKSLASH = chr(92)


def home_path(user):
    """A macOS-style home folder path: slash, folder word, slash, name."""
    return _SLASH + "Users" + _SLASH + user


def home_path_linux(user):
    """A Linux-style home folder path."""
    return _SLASH + "home" + _SLASH + user


def dash_slug(user):
    """The dash-slug form of a macOS home folder, with its closing dash."""
    return "-" + "Users" + "-" + user + "-"


def mac_temp_root():
    """A macOS per-user temporary root prefix."""
    return _SLASH + "var" + _SLASH + "folders" + _SLASH + "zz" + _SLASH


def private_ipv4():
    """A private-range address (RFC 1918 shape)."""
    return ".".join(["192", "168", "7", "42"])


def cgnat_ipv4():
    """A carrier-grade NAT range address (the range overlay networks use)."""
    return ".".join(["100", "101", "7", "42"])


def internal_host(name):
    """A host name under a private suffix."""
    return name + "." + "local"


def email(local, domain):
    """An address assembled from its parts."""
    return local + "@" + domain


def aws_key():
    """An access-key-shaped string, built from three fragments."""
    first = "AK"
    second = "IA"
    third = "QYLPMN5HHHFPZAM7"
    return first + second + third


def github_token():
    """A personal-access-token-shaped string."""
    return "gh" + "p" + "_" + "a1B2c3D4e5F6g7H8i9J0" + "k1L2m3N4o5P6q7R8"


def anthropic_key():
    """An API-key-shaped string for the vendor's key prefix."""
    return "sk" + "-" + "ant" + "-" + "api03" + "-" + "Zk3Vq9Lm2Xw7Rt5Yp8Nc4Bd6Hf1Js0Ga"


def private_key_header():
    """The first line of a PEM private key block."""
    return "-----" + "BEGIN " + "RSA " + "PRIVATE " + "KEY" + "-----"


def bearer_token():
    """An authorization header value with a long opaque token."""
    return "Authorization: " + "Bear" + "er " + "abcdefghij" + "0123456789" + "ABCDEFGH"


def windows_home(user):
    """A Windows-style home folder path with a closing backslash."""
    return "C" + ":" + _BACKSLASH + "Users" + _BACKSLASH + user + _BACKSLASH


def root_home():
    """A path inside the superuser's home folder."""
    return _SLASH + "root" + _SLASH + "notes"
