from datetime import timedelta


def test_compute_slowest_chain_no_dependencies(pipeline):
    time_taken = timedelta(days=1)
    # pylint: disable=protected-access
    result = pipeline._compute_slowest_chains(
        {"step1": []}, {"step1": (None, time_taken)}
    )

    assert result == {"step1": (["step1"], time_taken)}


def test_compute_slowest_chain_dependencies(pipeline):
    time_taken_step1 = timedelta(days=1)
    time_taken_step2 = timedelta(hours=1)
    # pylint: disable=protected-access
    result = pipeline._compute_slowest_chains(
        {"step1": ["step2"], "step2": []},
        {
            "step1": (None, time_taken_step1),
            "step2": (None, time_taken_step2),
        },
    )

    assert result == {
        "step1": (["step1", "step2"], time_taken_step1 + time_taken_step2),
        "step2": (["step2"], time_taken_step2),
    }
