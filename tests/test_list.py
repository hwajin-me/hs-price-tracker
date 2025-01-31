from custom_components.price_tracker.utilities.list import Lu


def test_array_access():
    test = [
        {"entity": {"viewType": "ACCESS"}},
        {"entity": {"viewType": "ACCESS_TARGET"}},
    ]

    result = Lu.find(test, "entity.viewType", "ACCESS_TARGET")

    assert result == test[1]
