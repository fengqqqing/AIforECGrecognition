import unittest

from PackUnpack import PackUnpack


class PackUnpackTest(unittest.TestCase):
    def _roundtrip(self, raw_packet):
        packer = PackUnpack()
        to_pack = list(raw_packet)
        self.assertTrue(packer.packData(to_pack))

        unpacker = PackUnpack()
        found = False
        for b in to_pack:
            found = unpacker.unpackData(b)
        self.assertTrue(found)
        return list(unpacker.getUnpackRslt())

    def test_roundtrip_ecg_packet(self):
        unpacked = self._roundtrip([0x10, 0x02, 0x07, 0xD0])
        self.assertEqual(unpacked[0], 0x10)
        self.assertEqual(unpacked[1], 0x02)
        self.assertEqual(unpacked[2], 0x07)
        self.assertEqual(unpacked[3], 0xD0)

    def test_checksum_rejects_tampered_packet(self):
        packer = PackUnpack()
        payload = [0x10, 0x04, 0x00, 0x64]
        self.assertTrue(packer.packData(payload))
        payload[5] ^= 0x01

        unpacker = PackUnpack()
        found = False
        for b in payload:
            found = unpacker.unpackData(b)
        self.assertFalse(found)


if __name__ == "__main__":
    unittest.main()
