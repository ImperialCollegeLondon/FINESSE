"""Tests for the NoiseProducer class."""

from decimal import Decimal
from itertools import product
from unittest.mock import MagicMock, Mock, patch

import pytest

from frog.hardware.noise_producer import NoiseProducer


@pytest.mark.parametrize("seed", (None, 0, 42))
@patch("frog.hardware.noise_producer.np.random.default_rng")
def test_init(rng_mock: Mock, seed: int | None) -> None:
    """Test providing different seeds to NoiseProducer."""
    NoiseProducer(seed=seed)
    rng_mock.assert_called_once_with(seed)


@patch("frog.hardware.noise_producer.np.random.default_rng")
def test_init_defaults(rng_mock: Mock) -> None:
    """Test the default values for NoiseProducer's constructor."""
    mock2 = MagicMock()
    rng_mock.return_value = mock2
    noise = NoiseProducer()
    assert noise.mean == 0.0
    assert noise.standard_deviation == 1.0
    assert noise.type is float
    rng_mock.assert_called_once_with(42)
    assert noise.rng is mock2


@pytest.mark.parametrize(
    "mean,standard_deviation,type", product(range(3), range(3), (float, int, Decimal))
)
def test_call(mean: int, standard_deviation: int, type: type) -> None:
    """Test calling NoiseProducers."""
    noise = NoiseProducer(float(mean), float(standard_deviation), type)
    with patch.object(noise, "rng") as rng_mock:
        rng_mock.normal.return_value = 0.0
        value = noise()

        # Check the RNG is called with the correct mean and SD
        rng_mock.normal.assert_called_once_with(float(mean), float(standard_deviation))

        # Check that returned type is correct
        assert isinstance(value, type)
