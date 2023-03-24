from trashbags.trashbag import Trashbag

__author__ = "Targeted Entropy"
__copyright__ = "Targeted Entropy"
__license__ = "MPL-2.0"


def test_trashbags_can_be_a_real_instance():
    # Call the trash with a None config
    trash = Trashbag(None)

    assert isinstance(trash, object)
