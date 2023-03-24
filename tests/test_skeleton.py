import pytest

from trashbags.skeleton import fib, main
from trashbags.trashbag import Trashbag

__author__ = "Targeted Entropy"
__copyright__ = "Targeted Entropy"
__license__ = "MPL-2.0"


def test_fib():
    """API Tests"""
    assert fib(1) == 1
    assert fib(2) == 1
    assert fib(7) == 13
    with pytest.raises(AssertionError):
        fib(-10)


def test_main(capsys):
    """CLI Tests"""
    # capsys is a pytest fixture that allows asserts against stdout/stderr
    # https://docs.pytest.org/en/stable/capture.html
    main(["7"])
    captured = capsys.readouterr()
    assert "The 7-th Fibonacci number is 13" in captured.out


def test_trashbags_can_be_a_real_instance():
    # Call the trash with a None config
    trash = Trashbag(None)

    assert isinstance(trash, object)
