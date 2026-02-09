import shutil
import tempfile
import os

from electrum import constants, blockchain
from electrum.simple_config import SimpleConfig
from electrum.blockchain import Blockchain, deserialize_header, hash_header, InvalidHeader, HEADER_SIZE
from electrum.util import bfh, make_dir

from . import ElectrumTestCase


class TestBlockchain(ElectrumTestCase):

    # Headers with x16rv2 hashing; chain built with correct prev_block_hash links.
    HEADERS = {
        'A': deserialize_header(bfh("0100000000000000000000000000000000000000000000000000000000000000000000003b1259286da5c345c018612509c09ea0a80c13eba9be5564f5c4c9c1bcf47bd844e97b5bffff7f2002000000"), 0),
        'B': deserialize_header(bfh("01000000771442c0495d51748e69acba427d7de8685e2338499c0eccc6cd618c64d41ee87922c93efb5610c1191258ad36d3af4160e701092dd79d75b93949dcf962f59da8e97b5bffff7f2000000000"), 1),
        'C': deserialize_header(bfh("010000006a33c8eb1126b1e6ccd5650e955a7dfc8318183b8e50469b7d9e108b0de64e42b666a00d35149b246a4890eba0c3348da95779d2ef337d6b7797930066017f1e0cea7b5bffff7f2000000000"), 2),
        'D': deserialize_header(bfh("0100000028815a102b2dd8a9e3a50cd50169bb59f2af2a9a42de61853dca0485cde9903951185c003dd9c9f1e7106ec4f6d5e87c5471b56e576b69b8918195ef732f45b470ea7b5bffff7f2000000000"), 3),
        'E': deserialize_header(bfh("01000000942bc59fbde642e20dea2c74f63ce817e4cf047540f5f9ae596ec16330220a2f9e12e2d760d6e272bc169a0bd2a7dfa6f2bbba44b12c713d6ec928dc1733f49cd4ea7b5bffff7f2000000000"), 4),
        'F': deserialize_header(bfh("0100000095d9f7b600c202b121ae29da0e0a80dc7629197468f79ddec62673169c7deee14931eb68b7cdded97561f8107e3c7525367b66fcae25968c4c00ed07f5ca8eb738eb7b5bffff7f2000000000"), 5),
        'O': deserialize_header(bfh("01000000d17ef7f8f73e2d8dcea35524a1dd17d210963d6ce550742b51c35a971dc113369d08748452ea671b2e2a28041e0d97b29645e6f716c719e930d189a46c13ec919ceb7b5bffff7f2000000000"), 6),
        'P': deserialize_header(bfh("0100000022542d92ead692778f28e43beb9f28bccf06374e1fc22e387a53aff35791e695af3c10e1f99013c1e330b7e228e5a69c8bbb66fc82b8734b13ae8cd61db356bf00ec7b5bffff7f2000000000"), 7),
        'Q': deserialize_header(bfh("010000000dc43ae697387d094c22d531c53fb17647916341f5db452de7a85715f232c9fac41f6101ef57cdb0d6336e02d5c0a620ba3e6f2d97491192ac60e8de1e2db23f64ec7b5bffff7f2000000000"), 8),
        'R': deserialize_header(bfh("010000002fddb2b88ebb4cd35d438124153ef2ea9adfbf6025c250df4f42fc889348631ad9e88ce0c9c30281ad532d4277fdc6be4b942ddbe1e9d38ff41ea5685b4434bfc8ec7b5bffff7f2000000000"), 9),
        'S': deserialize_header(bfh("0100000002c44b8e53fb5b376224ffc8de2bf722e049f50ebe53d998569d2d8369ed0a331675b5465917dd51c0af64b945600b3b2083da8969c21be3c3d8ad5fe5db12a92ced7b5bffff7f2000000000"), 10),
        'T': deserialize_header(bfh("01000000d82f568456021ff46470ee9f5b477f4a4844e16544a126e5fd5e385dbafde19dca5f76820fe649438fe99986eb7ace2139503ca92476483e2a5a30c0698292f290ed7b5bffff7f2000000000"), 11),
        'U': deserialize_header(bfh("010000004d154d1e4d37d8afd4c5cbdb61eaf75de6daca11df7b00f3f1308c62cd1a37dd1df5bb2a586bb628945e3d21457d494f454b7ed3ac4ac315c1154428adc67312f4ed7b5bffff7f2000000000"), 12),
        'G': deserialize_header(bfh("01000000d17ef7f8f73e2d8dcea35524a1dd17d210963d6ce550742b51c35a971dc113362e96c3ea157ae11824636d7af414b19c177c1cab3b10ffcbdf4b4c8e14eeabf1a6eb7b5bffff7f2001000000"), 6),
        'H': deserialize_header(bfh("010000006028ac56031f2592164d6c7942ae6e0544c6e00959cb7eff31a56af5fcd0b6a80d231364dead99d7acf9831e550eb53072f1c9e465d7774d794aa388df95769b0aec7b5bffff7f2000000000"), 7),
        'I': deserialize_header(bfh("01000000227f09dbd1f9e9d396d708da1731c2542f25b2006860504262327c05a61cd02c34a5ae075e4c42d61aa890ab508ba58f96855f44f98111bc2ae506053ae0f37d6eec7b5bffff7f2000000000"), 8),
        'J': deserialize_header(bfh("0100000090f65c053bc18b6aa2c32445fa390a6141177d6e47fb1694acbc9a3ad63a150b1b4e813f0a5b6a2bc1d8fbbe13b14f705e34284d9187bfa254aed2cde0995319d2ec7b5bffff7f2000000000"), 9),
        'K': deserialize_header(bfh("010000009c9223f8d142df523dbefe7adaebb8689c84d700178fa558336204d6d9f1bf3e24361a369a8bdac27d2ba07b9de868981f0724e01eff77e125027f625c9ad18136ed7b5bffff7f2000000000"), 10),
        'L': deserialize_header(bfh("01000000a0acb1fb92449c1138a5b0de40e145564bb60b123d37efd2fe26e88eafaf9c7772b91d00355a1a4121684cb72de0a6a35b8dbd6518a372bc57350fd6ace9685e9aed7b5bffff7f2000000000"), 11),
        'M': deserialize_header(bfh("0100000090f65c053bc18b6aa2c32445fa390a6141177d6e47fb1694acbc9a3ad63a150bf5f4c40bc3ce3d39a5baa76c3d9f15564d5e556ee2d0b7e6981842e0672d6035dcec7b5bffff7f2001000000"), 9),
        'N': deserialize_header(bfh("01000000b12a8ce18ae0357598d8591c61ae7a2bdb40aa23f53ef249eb07ff5f5f54ebc29735924b906f1c192aee265d6765683e0ec8241a8ebf5784fbd23083c7a6aca940ed7b5bffff7f2000000000"), 10),
        'X': deserialize_header(bfh("01000000099354910267fa62431d925da2705d700a0ed180b30e49c9e86da5242d7f422b8604994f8d53dc51926ff060d8855f42a784925373fa12e6c4d714ff8adfb056a4ed7b5bffff7f2000000000"), 11),
        'Y': deserialize_header(bfh("010000004e2fbb763f7dd8175ebfc2d1993e111516b0c31beae590a593a5c935e223b93c0e0a337c243c7608c8f90f48939d9ab60ee65a4cecaeac66856efd22600bedf908ee7b5bffff7f2000000000"), 12),
        'Z': deserialize_header(bfh("01000000224afc3d259f8eca23c5da95ad213528b43e4b3126f4a7348f54f89728a9eb34a5c5fe437e1c579d905367371675a72c805ec318b3f29bfa365218c40eb95a8b6cee7b5bffff7f2000000000"), 13),
    }
    # tree of headers:
    #                                            - M <- N <- X <- Y <- Z
    #                                          /
    #                             - G <- H <- I <- J <- K <- L
    #                           /
    # A <- B <- C <- D <- E <- F <- O <- P <- Q <- R <- S <- T <- U

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        constants.set_regtest()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        constants.set_mainnet()

    def setUp(self):
        super().setUp()
        self.data_dir = self.electrum_path
        make_dir(os.path.join(self.data_dir, 'forks'))
        self.config = SimpleConfig({'electrum_path': self.data_dir})
        blockchain.blockchains = {}

    def _append_header(self, chain: Blockchain, header: dict):
        self.assertTrue(chain.can_connect(header))
        chain.save_header(header)

    def test_get_height_of_last_common_block_with_chain(self):
        blockchain.blockchains[constants.net.GENESIS] = chain_u = Blockchain(
            config=self.config, forkpoint=0, parent=None,
            forkpoint_hash=constants.net.GENESIS, prev_hash=None)
        open(chain_u.path(), 'w+').close()
        self._append_header(chain_u, self.HEADERS['A'])
        self._append_header(chain_u, self.HEADERS['B'])
        self._append_header(chain_u, self.HEADERS['C'])
        self._append_header(chain_u, self.HEADERS['D'])
        self._append_header(chain_u, self.HEADERS['E'])
        self._append_header(chain_u, self.HEADERS['F'])
        self._append_header(chain_u, self.HEADERS['O'])
        self._append_header(chain_u, self.HEADERS['P'])
        self._append_header(chain_u, self.HEADERS['Q'])

        chain_l = chain_u.fork(self.HEADERS['G'])
        self._append_header(chain_l, self.HEADERS['H'])
        self._append_header(chain_l, self.HEADERS['I'])
        self._append_header(chain_l, self.HEADERS['J'])
        self._append_header(chain_l, self.HEADERS['K'])
        self._append_header(chain_l, self.HEADERS['L'])

        self.assertEqual({chain_u:  8, chain_l: 5}, chain_u.get_parent_heights())
        self.assertEqual({chain_l: 11},             chain_l.get_parent_heights())

        chain_z = chain_l.fork(self.HEADERS['M'])
        self._append_header(chain_z, self.HEADERS['N'])
        self._append_header(chain_z, self.HEADERS['X'])
        self._append_header(chain_z, self.HEADERS['Y'])
        self._append_header(chain_z, self.HEADERS['Z'])

        self.assertEqual({chain_u:  8, chain_z: 5}, chain_u.get_parent_heights())
        self.assertEqual({chain_l: 11, chain_z: 8}, chain_l.get_parent_heights())
        self.assertEqual({chain_z: 13},             chain_z.get_parent_heights())
        self.assertEqual(5, chain_u.get_height_of_last_common_block_with_chain(chain_l))
        self.assertEqual(5, chain_l.get_height_of_last_common_block_with_chain(chain_u))
        self.assertEqual(5, chain_u.get_height_of_last_common_block_with_chain(chain_z))
        self.assertEqual(5, chain_z.get_height_of_last_common_block_with_chain(chain_u))
        self.assertEqual(8, chain_l.get_height_of_last_common_block_with_chain(chain_z))
        self.assertEqual(8, chain_z.get_height_of_last_common_block_with_chain(chain_l))

        self._append_header(chain_u, self.HEADERS['R'])
        self._append_header(chain_u, self.HEADERS['S'])
        self._append_header(chain_u, self.HEADERS['T'])
        self._append_header(chain_u, self.HEADERS['U'])

        self.assertEqual({chain_u: 12, chain_z: 5}, chain_u.get_parent_heights())
        self.assertEqual({chain_l: 11, chain_z: 8}, chain_l.get_parent_heights())
        self.assertEqual({chain_z: 13},             chain_z.get_parent_heights())
        self.assertEqual(5, chain_u.get_height_of_last_common_block_with_chain(chain_l))
        self.assertEqual(5, chain_l.get_height_of_last_common_block_with_chain(chain_u))
        self.assertEqual(5, chain_u.get_height_of_last_common_block_with_chain(chain_z))
        self.assertEqual(5, chain_z.get_height_of_last_common_block_with_chain(chain_u))
        self.assertEqual(8, chain_l.get_height_of_last_common_block_with_chain(chain_z))
        self.assertEqual(8, chain_z.get_height_of_last_common_block_with_chain(chain_l))

    def test_parents_after_forking(self):
        blockchain.blockchains[constants.net.GENESIS] = chain_u = Blockchain(
            config=self.config, forkpoint=0, parent=None,
            forkpoint_hash=constants.net.GENESIS, prev_hash=None)
        open(chain_u.path(), 'w+').close()
        self._append_header(chain_u, self.HEADERS['A'])
        self._append_header(chain_u, self.HEADERS['B'])
        self._append_header(chain_u, self.HEADERS['C'])
        self._append_header(chain_u, self.HEADERS['D'])
        self._append_header(chain_u, self.HEADERS['E'])
        self._append_header(chain_u, self.HEADERS['F'])
        self._append_header(chain_u, self.HEADERS['O'])
        self._append_header(chain_u, self.HEADERS['P'])
        self._append_header(chain_u, self.HEADERS['Q'])

        self.assertEqual(None, chain_u.parent)

        chain_l = chain_u.fork(self.HEADERS['G'])
        self._append_header(chain_l, self.HEADERS['H'])
        self._append_header(chain_l, self.HEADERS['I'])
        self._append_header(chain_l, self.HEADERS['J'])
        self._append_header(chain_l, self.HEADERS['K'])
        self._append_header(chain_l, self.HEADERS['L'])

        self.assertEqual(None,    chain_l.parent)
        self.assertEqual(chain_l, chain_u.parent)

        chain_z = chain_l.fork(self.HEADERS['M'])
        self._append_header(chain_z, self.HEADERS['N'])
        self._append_header(chain_z, self.HEADERS['X'])
        self._append_header(chain_z, self.HEADERS['Y'])
        self._append_header(chain_z, self.HEADERS['Z'])

        self.assertEqual(chain_z, chain_u.parent)
        self.assertEqual(chain_z, chain_l.parent)
        self.assertEqual(None,    chain_z.parent)

        self._append_header(chain_u, self.HEADERS['R'])
        self._append_header(chain_u, self.HEADERS['S'])
        self._append_header(chain_u, self.HEADERS['T'])
        self._append_header(chain_u, self.HEADERS['U'])

        self.assertEqual(chain_z, chain_u.parent)
        self.assertEqual(chain_z, chain_l.parent)
        self.assertEqual(None,    chain_z.parent)

    def test_forking_and_swapping(self):
        blockchain.blockchains[constants.net.GENESIS] = chain_u = Blockchain(
            config=self.config, forkpoint=0, parent=None,
            forkpoint_hash=constants.net.GENESIS, prev_hash=None)
        open(chain_u.path(), 'w+').close()

        self._append_header(chain_u, self.HEADERS['A'])
        self._append_header(chain_u, self.HEADERS['B'])
        self._append_header(chain_u, self.HEADERS['C'])
        self._append_header(chain_u, self.HEADERS['D'])
        self._append_header(chain_u, self.HEADERS['E'])
        self._append_header(chain_u, self.HEADERS['F'])
        self._append_header(chain_u, self.HEADERS['O'])
        self._append_header(chain_u, self.HEADERS['P'])
        self._append_header(chain_u, self.HEADERS['Q'])
        self._append_header(chain_u, self.HEADERS['R'])

        chain_l = chain_u.fork(self.HEADERS['G'])
        self._append_header(chain_l, self.HEADERS['H'])
        self._append_header(chain_l, self.HEADERS['I'])
        self._append_header(chain_l, self.HEADERS['J'])

        # do checks
        self.assertEqual(2, len(blockchain.blockchains))
        self.assertEqual(1, len(os.listdir(os.path.join(self.data_dir, "forks"))))
        self.assertEqual(0, chain_u.forkpoint)
        self.assertEqual(None, chain_u.parent)
        self.assertEqual(constants.net.GENESIS, chain_u._forkpoint_hash)
        self.assertEqual(None, chain_u._prev_hash)
        self.assertEqual(os.path.join(self.data_dir, "blockchain_headers"), chain_u.path())
        self.assertEqual(10 * HEADER_SIZE, os.stat(chain_u.path()).st_size)
        self.assertEqual(6, chain_l.forkpoint)
        self.assertEqual(chain_u, chain_l.parent)
        self.assertEqual(hash_header(self.HEADERS['G']), chain_l._forkpoint_hash)
        self.assertEqual(hash_header(self.HEADERS['F']), chain_l._prev_hash)
        self.assertEqual(os.path.join(self.data_dir, "forks", "fork2_6_%s_%s" % (hash_header(self.HEADERS['F']).lstrip('0'), hash_header(self.HEADERS['G']).lstrip('0'))), chain_l.path())
        self.assertEqual(4 * HEADER_SIZE, os.stat(chain_l.path()).st_size)

        self._append_header(chain_l, self.HEADERS['K'])

        # chains were swapped, do checks
        self.assertEqual(2, len(blockchain.blockchains))
        self.assertEqual(1, len(os.listdir(os.path.join(self.data_dir, "forks"))))
        self.assertEqual(6, chain_u.forkpoint)
        self.assertEqual(chain_l, chain_u.parent)
        self.assertEqual(hash_header(self.HEADERS['O']), chain_u._forkpoint_hash)
        self.assertEqual(hash_header(self.HEADERS['F']), chain_u._prev_hash)
        self.assertEqual(os.path.join(self.data_dir, "forks", "fork2_6_%s_%s" % (hash_header(self.HEADERS['F']).lstrip('0'), hash_header(self.HEADERS['O']).lstrip('0'))), chain_u.path())
        self.assertEqual(4 * HEADER_SIZE, os.stat(chain_u.path()).st_size)
        self.assertEqual(0, chain_l.forkpoint)
        self.assertEqual(None, chain_l.parent)
        self.assertEqual(constants.net.GENESIS, chain_l._forkpoint_hash)
        self.assertEqual(None, chain_l._prev_hash)
        self.assertEqual(os.path.join(self.data_dir, "blockchain_headers"), chain_l.path())
        self.assertEqual(11 * HEADER_SIZE, os.stat(chain_l.path()).st_size)
        for b in (chain_u, chain_l):
            self.assertTrue(all([b.can_connect(b.read_header(i), False) for i in range(b.height())]))

        self._append_header(chain_u, self.HEADERS['S'])
        self._append_header(chain_u, self.HEADERS['T'])
        self._append_header(chain_u, self.HEADERS['U'])
        self._append_header(chain_l, self.HEADERS['L'])

        chain_z = chain_l.fork(self.HEADERS['M'])
        self._append_header(chain_z, self.HEADERS['N'])
        self._append_header(chain_z, self.HEADERS['X'])
        self._append_header(chain_z, self.HEADERS['Y'])
        self._append_header(chain_z, self.HEADERS['Z'])

        # chain_z became best chain, do checks
        self.assertEqual(3, len(blockchain.blockchains))
        self.assertEqual(2, len(os.listdir(os.path.join(self.data_dir, "forks"))))
        self.assertEqual(0, chain_z.forkpoint)
        self.assertEqual(None, chain_z.parent)
        self.assertEqual(constants.net.GENESIS, chain_z._forkpoint_hash)
        self.assertEqual(None, chain_z._prev_hash)
        self.assertEqual(os.path.join(self.data_dir, "blockchain_headers"), chain_z.path())
        self.assertEqual(14 * HEADER_SIZE, os.stat(chain_z.path()).st_size)
        self.assertEqual(9, chain_l.forkpoint)
        self.assertEqual(chain_z, chain_l.parent)
        self.assertEqual(hash_header(self.HEADERS['J']), chain_l._forkpoint_hash)
        self.assertEqual(hash_header(self.HEADERS['I']), chain_l._prev_hash)
        self.assertEqual(os.path.join(self.data_dir, "forks", "fork2_9_%s_%s" % (hash_header(self.HEADERS['I']).lstrip('0'), hash_header(self.HEADERS['J']).lstrip('0'))), chain_l.path())
        self.assertEqual(3 * HEADER_SIZE, os.stat(chain_l.path()).st_size)
        self.assertEqual(6, chain_u.forkpoint)
        self.assertEqual(chain_z, chain_u.parent)
        self.assertEqual(hash_header(self.HEADERS['O']), chain_u._forkpoint_hash)
        self.assertEqual(hash_header(self.HEADERS['F']), chain_u._prev_hash)
        self.assertEqual(os.path.join(self.data_dir, "forks", "fork2_6_%s_%s" % (hash_header(self.HEADERS['F']).lstrip('0'), hash_header(self.HEADERS['O']).lstrip('0'))), chain_u.path())
        self.assertEqual(7 * HEADER_SIZE, os.stat(chain_u.path()).st_size)
        for b in (chain_u, chain_l, chain_z):
            self.assertTrue(all([b.can_connect(b.read_header(i), False) for i in range(b.height())]))

        self.assertEqual(constants.net.GENESIS, chain_z.get_hash(0))
        self.assertEqual(hash_header(self.HEADERS['F']), chain_z.get_hash(5))
        self.assertEqual(hash_header(self.HEADERS['G']), chain_z.get_hash(6))
        self.assertEqual(hash_header(self.HEADERS['I']), chain_z.get_hash(8))
        self.assertEqual(hash_header(self.HEADERS['M']), chain_z.get_hash(9))
        self.assertEqual(hash_header(self.HEADERS['Z']), chain_z.get_hash(13))

    def test_doing_multiple_swaps_after_single_new_header(self):
        blockchain.blockchains[constants.net.GENESIS] = chain_u = Blockchain(
            config=self.config, forkpoint=0, parent=None,
            forkpoint_hash=constants.net.GENESIS, prev_hash=None)
        open(chain_u.path(), 'w+').close()

        self._append_header(chain_u, self.HEADERS['A'])
        self._append_header(chain_u, self.HEADERS['B'])
        self._append_header(chain_u, self.HEADERS['C'])
        self._append_header(chain_u, self.HEADERS['D'])
        self._append_header(chain_u, self.HEADERS['E'])
        self._append_header(chain_u, self.HEADERS['F'])
        self._append_header(chain_u, self.HEADERS['O'])
        self._append_header(chain_u, self.HEADERS['P'])
        self._append_header(chain_u, self.HEADERS['Q'])
        self._append_header(chain_u, self.HEADERS['R'])
        self._append_header(chain_u, self.HEADERS['S'])

        self.assertEqual(1, len(blockchain.blockchains))
        self.assertEqual(0, len(os.listdir(os.path.join(self.data_dir, "forks"))))

        chain_l = chain_u.fork(self.HEADERS['G'])
        self._append_header(chain_l, self.HEADERS['H'])
        self._append_header(chain_l, self.HEADERS['I'])
        self._append_header(chain_l, self.HEADERS['J'])
        self._append_header(chain_l, self.HEADERS['K'])
        # now chain_u is best chain, but it's tied with chain_l

        self.assertEqual(2, len(blockchain.blockchains))
        self.assertEqual(1, len(os.listdir(os.path.join(self.data_dir, "forks"))))

        chain_z = chain_l.fork(self.HEADERS['M'])
        self._append_header(chain_z, self.HEADERS['N'])
        self._append_header(chain_z, self.HEADERS['X'])

        self.assertEqual(3, len(blockchain.blockchains))
        self.assertEqual(2, len(os.listdir(os.path.join(self.data_dir, "forks"))))

        # chain_z became best chain, do checks
        self.assertEqual(0, chain_z.forkpoint)
        self.assertEqual(None, chain_z.parent)
        self.assertEqual(constants.net.GENESIS, chain_z._forkpoint_hash)
        self.assertEqual(None, chain_z._prev_hash)
        self.assertEqual(os.path.join(self.data_dir, "blockchain_headers"), chain_z.path())
        self.assertEqual(12 * HEADER_SIZE, os.stat(chain_z.path()).st_size)
        self.assertEqual(9, chain_l.forkpoint)
        self.assertEqual(chain_z, chain_l.parent)
        self.assertEqual(hash_header(self.HEADERS['J']), chain_l._forkpoint_hash)
        self.assertEqual(hash_header(self.HEADERS['I']), chain_l._prev_hash)
        self.assertEqual(os.path.join(self.data_dir, "forks", "fork2_9_%s_%s" % (hash_header(self.HEADERS['I']).lstrip('0'), hash_header(self.HEADERS['J']).lstrip('0'))), chain_l.path())
        self.assertEqual(2 * HEADER_SIZE, os.stat(chain_l.path()).st_size)
        self.assertEqual(6, chain_u.forkpoint)
        self.assertEqual(chain_z, chain_u.parent)
        self.assertEqual(hash_header(self.HEADERS['O']), chain_u._forkpoint_hash)
        self.assertEqual(hash_header(self.HEADERS['F']), chain_u._prev_hash)
        self.assertEqual(os.path.join(self.data_dir, "forks", "fork2_6_%s_%s" % (hash_header(self.HEADERS['F']).lstrip('0'), hash_header(self.HEADERS['O']).lstrip('0'))), chain_u.path())
        self.assertEqual(5 * HEADER_SIZE, os.stat(chain_u.path()).st_size)

        self.assertEqual(constants.net.GENESIS, chain_z.get_hash(0))
        self.assertEqual(hash_header(self.HEADERS['F']), chain_z.get_hash(5))
        self.assertEqual(hash_header(self.HEADERS['G']), chain_z.get_hash(6))
        self.assertEqual(hash_header(self.HEADERS['I']), chain_z.get_hash(8))
        self.assertEqual(hash_header(self.HEADERS['M']), chain_z.get_hash(9))
        self.assertEqual(hash_header(self.HEADERS['X']), chain_z.get_hash(11))

        for b in (chain_u, chain_l, chain_z):
            self.assertTrue(all([b.can_connect(b.read_header(i), False) for i in range(b.height())]))

    def get_chains_that_contain_header_helper(self, header: dict):
        height = header['block_height']
        header_hash = hash_header(header)
        return blockchain.get_chains_that_contain_header(height, header_hash)

    def test_get_chains_that_contain_header(self):
        blockchain.blockchains[constants.net.GENESIS] = chain_u = Blockchain(
            config=self.config, forkpoint=0, parent=None,
            forkpoint_hash=constants.net.GENESIS, prev_hash=None)
        open(chain_u.path(), 'w+').close()
        self._append_header(chain_u, self.HEADERS['A'])
        self._append_header(chain_u, self.HEADERS['B'])
        self._append_header(chain_u, self.HEADERS['C'])
        self._append_header(chain_u, self.HEADERS['D'])
        self._append_header(chain_u, self.HEADERS['E'])
        self._append_header(chain_u, self.HEADERS['F'])
        self._append_header(chain_u, self.HEADERS['O'])
        self._append_header(chain_u, self.HEADERS['P'])
        self._append_header(chain_u, self.HEADERS['Q'])

        chain_l = chain_u.fork(self.HEADERS['G'])
        self._append_header(chain_l, self.HEADERS['H'])
        self._append_header(chain_l, self.HEADERS['I'])
        self._append_header(chain_l, self.HEADERS['J'])
        self._append_header(chain_l, self.HEADERS['K'])
        self._append_header(chain_l, self.HEADERS['L'])

        chain_z = chain_l.fork(self.HEADERS['M'])

        self.assertEqual([chain_l, chain_z, chain_u], self.get_chains_that_contain_header_helper(self.HEADERS['A']))
        self.assertEqual([chain_l, chain_z, chain_u], self.get_chains_that_contain_header_helper(self.HEADERS['C']))
        self.assertEqual([chain_l, chain_z, chain_u], self.get_chains_that_contain_header_helper(self.HEADERS['F']))
        self.assertEqual([chain_l, chain_z], self.get_chains_that_contain_header_helper(self.HEADERS['G']))
        self.assertEqual([chain_l, chain_z], self.get_chains_that_contain_header_helper(self.HEADERS['I']))
        self.assertEqual([chain_z], self.get_chains_that_contain_header_helper(self.HEADERS['M']))
        self.assertEqual([chain_l], self.get_chains_that_contain_header_helper(self.HEADERS['K']))

        self._append_header(chain_z, self.HEADERS['N'])
        self._append_header(chain_z, self.HEADERS['X'])
        self._append_header(chain_z, self.HEADERS['Y'])
        self._append_header(chain_z, self.HEADERS['Z'])

        self.assertEqual([chain_z, chain_l, chain_u], self.get_chains_that_contain_header_helper(self.HEADERS['A']))
        self.assertEqual([chain_z, chain_l, chain_u], self.get_chains_that_contain_header_helper(self.HEADERS['C']))
        self.assertEqual([chain_z, chain_l, chain_u], self.get_chains_that_contain_header_helper(self.HEADERS['F']))
        self.assertEqual([chain_u], self.get_chains_that_contain_header_helper(self.HEADERS['O']))
        self.assertEqual([chain_z, chain_l], self.get_chains_that_contain_header_helper(self.HEADERS['I']))

    def test_target_to_bits(self):
        # https://github.com/bitcoin/bitcoin/blob/7fcf53f7b4524572d1d0c9a5fdc388e87eb02416/src/arith_uint256.h#L269
        self.assertEqual(0x05123456, Blockchain.target_to_bits(0x1234560000))
        self.assertEqual(0x0600c0de, Blockchain.target_to_bits(0xc0de000000))

        # tests from https://github.com/bitcoin/bitcoin/blob/a7d17daa5cd8bf6398d5f8d7e77290009407d6ea/src/test/arith_uint256_tests.cpp#L411
        tuples = (
            (0, 0x0000000000000000000000000000000000000000000000000000000000000000, 0),
            (0x00123456, 0x0000000000000000000000000000000000000000000000000000000000000000, 0),
            (0x01003456, 0x0000000000000000000000000000000000000000000000000000000000000000, 0),
            (0x02000056, 0x0000000000000000000000000000000000000000000000000000000000000000, 0),
            (0x03000000, 0x0000000000000000000000000000000000000000000000000000000000000000, 0),
            (0x04000000, 0x0000000000000000000000000000000000000000000000000000000000000000, 0),
            (0x00923456, 0x0000000000000000000000000000000000000000000000000000000000000000, 0),
            (0x01803456, 0x0000000000000000000000000000000000000000000000000000000000000000, 0),
            (0x02800056, 0x0000000000000000000000000000000000000000000000000000000000000000, 0),
            (0x03800000, 0x0000000000000000000000000000000000000000000000000000000000000000, 0),
            (0x04800000, 0x0000000000000000000000000000000000000000000000000000000000000000, 0),
            (0x01123456, 0x0000000000000000000000000000000000000000000000000000000000000012, 0x01120000),
            (0x02123456, 0x0000000000000000000000000000000000000000000000000000000000001234, 0x02123400),
            (0x03123456, 0x0000000000000000000000000000000000000000000000000000000000123456, 0x03123456),
            (0x04123456, 0x0000000000000000000000000000000000000000000000000000000012345600, 0x04123456),
            (0x05009234, 0x0000000000000000000000000000000000000000000000000000000092340000, 0x05009234),
            (0x20123456, 0x1234560000000000000000000000000000000000000000000000000000000000, 0x20123456),
        )
        for nbits1, target, nbits2 in tuples:
            with self.subTest(original_compact_nbits=nbits1.to_bytes(length=4, byteorder="big").hex()):
                num = Blockchain.bits_to_target(nbits1)
                self.assertEqual(target, num)
                self.assertEqual(nbits2, Blockchain.target_to_bits(num))

        # Make sure that we don't generate compacts with the 0x00800000 bit set
        self.assertEqual(0x02008000, Blockchain.target_to_bits(0x80))

        with self.assertRaises(InvalidHeader):  # target cannot be negative
            Blockchain.bits_to_target(0x01fedcba)
        with self.assertRaises(InvalidHeader):  # target cannot be negative
            Blockchain.bits_to_target(0x04923456)
        with self.assertRaises(InvalidHeader):  # overflow
            Blockchain.bits_to_target(0xff123456)


class TestVerifyHeader(ElectrumTestCase):

    # Synthetic header at height 100 whose x16rv2 hash satisfies YAI's MAX_TARGET.
    # bits=0x2000ffff, nonce=33, same prev_hash/merkle_root structure.
    valid_header = "0100000095194b8567fe2e8bbda931afd01a7acd399b9325cb54683e64129bcd000000000802c98f18fd34fd16d61c63cf44474568370124ac5f3be626c2e1c3c9f0052d29ab5f49ffff002021000000"
    target = Blockchain.bits_to_target(0x2000ffff)
    prev_hash = "00000000cd9b12643e6854cb25939b39cd7a1ad0af31a9bd8b2efe67854b1995"

    def setUp(self):
        super().setUp()
        self.header = deserialize_header(bfh(self.valid_header), 100)

    def test_valid_header(self):
        Blockchain.verify_header(self.header, self.prev_hash, self.target)

    def test_expected_hash_mismatch(self):
        with self.assertRaises(InvalidHeader):
            Blockchain.verify_header(self.header, self.prev_hash, self.target,
                                     expected_header_hash="foo")

    def test_prev_hash_mismatch(self):
        with self.assertRaises(InvalidHeader):
            Blockchain.verify_header(self.header, "foo", self.target)

    def test_target_mismatch(self):
        with self.assertRaises(InvalidHeader):
            other_target = Blockchain.bits_to_target(0x1d00eeee)
            Blockchain.verify_header(self.header, self.prev_hash, other_target)

    def test_insufficient_pow(self):
        with self.assertRaises(InvalidHeader):
            self.header["nonce"] = 42
            Blockchain.verify_header(self.header, self.prev_hash, self.target)
