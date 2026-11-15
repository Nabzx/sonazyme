"""The world model behaves, and a policy can be learned inside it quickly."""

import time

from sonazyme.loop.policy import act, observe, train
from sonazyme.loop.world import BASE_C, CEILING_C, Loop


def test_a_clean_loop_runs_cool_and_a_fouled_one_does_not():
    loop = Loop(seed=3)
    assert loop.temperature() < BASE_C + 2
    loop.film = [0.9] * loop.sections
    assert loop.temperature() > CEILING_C


def test_film_grows_and_a_dose_clears_it_where_it_lands():
    loop = Loop(seed=3)
    loop.film = [0.5] * loop.sections
    before = list(loop.film)
    loop.step(dose=2)
    assert loop.film[2] < before[2] * 0.4
    # Carried downstream, weaker as it goes, and untouched upstream.
    assert loop.film[3] < before[3]
    assert loop.film[1] > before[1]


def test_a_dose_must_name_a_section_of_this_loop():
    loop = Loop(seed=3)
    for bad in (-1, 99):
        try:
            loop.step(dose=bad)
        except ValueError:
            continue
        raise AssertionError(f"dose {bad} should have been refused")


def test_the_reading_is_coarse_and_comes_only_from_sensors():
    loop = Loop(seed=3)
    loop.film = [0.0] * loop.sections
    quiet = observe(loop)
    # A section with no sensor on it cannot move the reading.
    loop.film[7] = 0.95
    assert observe(loop) == quiet
    loop.film[4] = 0.95
    assert observe(loop) != quiet


def test_a_policy_is_learned_in_about_a_second_and_acts():
    started = time.perf_counter()
    table = train(episodes=400, hours=32, seed=5)
    assert time.perf_counter() - started < 10
    assert table, "the table should hold the states it visited"
    loop = Loop(seed=11)
    loop.film = [0.8] * loop.sections
    choice = act(table, loop)
    assert choice is None or 0 <= choice < loop.sections
