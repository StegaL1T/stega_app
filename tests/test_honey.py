import pytest

from crypto_honey import HoneyFormatError, he_decrypt, he_encrypt, register_universe


@pytest.fixture(scope='module', autouse=True)
def setup_test_universe():
    messages = ['alpha', 'bravo', 'charlie', 'delta']
    probs = [0.4, 0.3, 0.2, 0.1]
    register_universe('test_demo', messages, probs)
    return messages


def test_roundtrip_text(setup_test_universe):
    blob = he_encrypt('bravo', 4242, 'test_demo')
    assert blob.startswith(b'HONEY1')
    assert he_decrypt(blob, 4242) == 'bravo'


def test_wrong_key_produces_decoys(setup_test_universe):
    blob = he_encrypt('alpha', 1111, 'test_demo')
    messages = set(setup_test_universe)
    decoys = {he_decrypt(blob, key) for key in range(2000, 2010)}
    assert decoys <= messages
    assert len(decoys) > 1
    assert any(decoy != 'alpha' for decoy in decoys)


def test_format_errors_trigger_exceptions():
    blob = he_encrypt('charlie', 5151, 'test_demo')
    # Corrupt magic
    corrupt = b'XXXXXX' + blob[6:]
    with pytest.raises(HoneyFormatError):
        he_decrypt(corrupt, 5151)
    # Unknown universe name
    modified = bytearray(blob)
    modified[6 + 4 + 8] = 4  # universe length
    modified[6 + 4 + 8 + 1:6 + 4 + 8 + 1 + 4] = b'fake'
    with pytest.raises(HoneyFormatError):
        he_decrypt(bytes(modified), 5151)
    # Truncation
    with pytest.raises(HoneyFormatError):
        he_decrypt(blob[:-3], 5151)


def test_register_universe_validates_probabilities():
    with pytest.raises(ValueError):
        register_universe('bad_probs', ['x', 'y'], [0.3, 0.3])
