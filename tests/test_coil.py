from unittest import TestCase

from construct import Int8ul

from nibe.coil import Coil, swapwords
from nibe.exceptions import DecodeException, EncodeException


class TestWordSwap(TestCase):
    def test_swapwords(self):
        self.assertEqual(swapwords(b"abcd"), b"cdab")
        self.assertEqual(swapwords(b"ab"), b"ab")


class TestCoil(TestCase):
    def test_create(self):
        coil = Coil(123, "test_name", "test_title", "u8", unknown="some other")

        self.assertEqual(coil.address, 123)
        self.assertEqual(coil.name, "test_name")
        self.assertEqual(coil.title, "test_title")
        self.assertEqual(coil.parser, Int8ul)
        self.assertEqual(coil.other["unknown"], "some other")


class TestCoilSigned8(TestCase):
    def setUp(self) -> None:
        self.coil = Coil(48739, "cool-offset-s1-48739", "Cool offset S1", "s8")

    def test_decode(self):
        self.coil.raw_value = b"\xfc\x00\x00\x00"
        self.assertEqual(-4, self.coil.value)
        self.coil.raw_value = b"\xfc\x00"
        self.assertEqual(-4, self.coil.value)
        self.coil.raw_value = b"\xfc"
        self.assertEqual(-4, self.coil.value)

    def test_encode(self):
        self.coil.value = -4
        self.assertEqual(b"\xfc\x00\x00\x00", self.coil.raw_value)

        with self.assertRaises(EncodeException):
            self.coil.value = 256
            _ = self.coil.raw_value


class TestCoilUnsigned8(TestCase):
    def setUp(self) -> None:
        self.coil = Coil(123, "test", "test", "u8")

    def test_decode(self):
        self.coil.raw_value = b"\x01\x00\x00\x00"
        self.assertEqual(1, self.coil.value)
        self.coil.raw_value = b"\x01\x00"
        self.assertEqual(1, self.coil.value)
        self.coil.raw_value = b"\x01"
        self.assertEqual(1, self.coil.value)

    def test_encode(self):
        self.coil.value = 1
        self.assertEqual(b"\x01\x00\x00\x00", self.coil.raw_value)
        self.coil.value = 255
        self.assertEqual(b"\xff\x00\x00\x00", self.coil.raw_value)

        with self.assertRaises(EncodeException):
            self.coil.value = 256
            _ = self.coil.raw_value


class TestCoilSigned16(TestCase):
    def setUp(self) -> None:
        self.coil = Coil(123, "test", "test", "s16", factor=10, min=50, max=300)

    def test_attributes(self):
        self.assertEqual(5.0, self.coil.min)
        self.assertEqual(30.0, self.coil.max)

        self.assertEqual(50, self.coil.raw_min)
        self.assertEqual(300, self.coil.raw_max)

        self.assertFalse(self.coil.is_boolean)
        self.assertFalse(self.coil.is_writable)

    def test_set_value_bounds(self):
        self.coil.value = 5.0
        self.coil.value = 30

        with self.assertRaises(AssertionError):
            self.coil.value = 4.9

        with self.assertRaises(AssertionError):
            self.coil.value = 30.1

    def test_decode(self):
        self.coil.raw_value = b"\x97\x00"

    def test_decode_out_of_bounds(self):
        with self.assertRaises(DecodeException):
            self.coil.raw_value = b"\x31\x00"

        with self.assertRaises(DecodeException):
            self.coil.raw_value = b"\x2d\x10"

    def test_encode(self):
        self.coil.value = 15.1
        self.assertEqual(b"\x97\x00\x00\x00", self.coil.raw_value)

    def test_encode_out_of_bounds(self):
        with self.assertRaises(AssertionError):
            self.coil.value = 4

        with self.assertRaises(AssertionError):
            self.coil.value = 30.1


class TestCoilUnsigned16(TestCase):
    def setUp(self) -> None:
        self.coil = Coil(
            123,
            "compressor-frequency-actual-43136",
            "Compressor Frequency, Actual",
            "u16",
            factor=10,
        )

    def test_decode(self):
        self.coil.raw_value = b"\x01\x00\x00\x00"
        self.assertEqual(0.1, self.coil.value)
        self.coil.raw_value = b"\x01\x00"
        self.assertEqual(0.1, self.coil.value)

    def test_encode(self):
        self.coil.value = 0.1
        self.assertEqual(b"\x01\x00\x00\x00", self.coil.raw_value)
        self.coil.value = 25.5
        self.assertEqual(b"\xff\x00\x00\x00", self.coil.raw_value)


class TestCoilSigned32(TestCase):
    def setUp(self) -> None:
        self.coil = Coil(
            43420,
            "tot-op-time-compr-eb100-ep14-43420",
            "Total compressorer operation time",
            "s32",
        )

    def test_decode(self):
        self.coil.raw_value = b"2T\x00\x00"
        self.assertEqual(21554, self.coil.value)

    def test_encode(self):
        self.coil.value = 21554
        self.assertEqual(b"2T\x00\x00", self.coil.raw_value)


class TestCoilSigned32WordSwap(TestCase):
    def setUp(self) -> None:
        self.coil = Coil(
            43420,
            "tot-op-time-compr-eb100-ep14-43420",
            "Total compressorer operation time",
            "s32",
            word_swap=False,
        )

    def test_decode(self):
        self.coil.raw_value = b"\x00\x00(\x06"
        self.assertEqual(1576, self.coil.value)

    def test_encode(self):
        self.coil.value = 1576
        self.assertEqual(b"\x00\x00(\x06", self.coil.raw_value)


class TestCoilWithMapping(TestCase):
    def setUp(self) -> None:
        self.coil = Coil(
            123,
            "prio-43086",
            "Prio",
            "u8",
            factor=1,
            mappings={
                "10": "Off",
                "20": "Hot Water",
                "30": "Heat",
                "40": "Pool",
                "41": "Pool 2",
                "50": "Transfer",
                "60": "Cooling",
            },
        )

    def test_set_valid_value(self):
        self.coil.value = "off"

        self.assertEqual("OFF", self.coil.value)

    def test_set_invalid_value(self):
        with self.assertRaises(AssertionError):
            self.coil.value = "Beer"

    def test_decode_mapping(self):
        self.coil.raw_value = b"\x0a"
        self.assertEqual("OFF", self.coil.value)

    def test_encode_mapping(self):
        self.coil.value = "off"
        self.assertEqual(b"\x0a\x00\x00\x00", self.coil.raw_value)

    def test_decode_mapping_failure(self):
        with self.assertRaises(DecodeException):
            self.coil.raw_value = b"\x00"

    def test_encode_mapping_failure(self):
        with self.assertRaises(AssertionError):
            self.coil.value = "Unknown"


class TestBooleanCoilWithMapping(TestCase):
    def setUp(self) -> None:
        self.coil = Coil(
            43024,
            "status-cooling-43024",
            "Status Cooling",
            "u8",
            factor=1,
            mappings={"0": "Off", "1": "On"},
        )

    def test_attributes(self):
        self.assertTrue(self.coil.is_boolean)

    def test_set_valid_value(self):
        self.coil.value = "On"
        assert self.coil.value == "ON"

        self.coil.value = "ofF"
        assert self.coil.value == "OFF"


class TestBooleanCoilWithBounds(TestCase):
    def setUp(self) -> None:
        self.coil = Coil(
            47050,
            "status-cooling-43024",
            "Periodic HW",
            "s8",
            factor=1,
            min=0,
            max=1,
            write=True,
        )

    def test_attributes(self):
        self.assertTrue(self.coil.is_boolean)

    def test_set_valid_value(self):
        self.coil.value = "ON"
        self.coil.value = "OFF"
