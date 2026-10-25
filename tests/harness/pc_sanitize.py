"""Skeleton for the runtime-built sanitizer (EVID-02). Replaced by the implementation commit."""
from __future__ import annotations

import collections

TOKENS = ()

Sources = collections.namedtuple("Sources", "homes login hostnames temp_dirs repo_root")


class SanitizerError(Exception):
    """The sanitizer refused or failed; messages are fixed text and never hold a value."""


def machine_sources():
    raise NotImplementedError


class Sanitizer(object):
    @classmethod
    def from_machine(cls, repo_root, extra_map=None, deny_file=None, sources=None):
        raise NotImplementedError
