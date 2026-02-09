from hashlib import sha256
from decimal import Decimal
from binascii import unhexlify, hexlify
import pprint
import unittest

from electrum.lnaddr import shorten_amount, unshorten_amount, LnAddr, lnencode, lndecode, u5_to_bitarray, bitarray_to_u5
from electrum.segwit_addr import bech32_encode, bech32_decode
from electrum import segwit_addr
from electrum.lnutil import UnknownEvenFeatureBits, derive_payment_secret_from_payment_preimage, LnFeatures, IncompatibleLightningFeatures
from electrum import constants

from . import ElectrumTestCase


RHASH=unhexlify('0001020304050607080900010203040506070809000102030405060708090102')
PAYMENT_SECRET=unhexlify('1111111111111111111111111111111111111111111111111111111111111111')
CONVERSION_RATE=1200
PRIVKEY=unhexlify('e126f68f7eafcc8b74f54d269fe206be715000f94dac067d1c04a8ca3b2db734')
PUBKEY=unhexlify('03e7156ae33b0a208d0744199163177e909e80176e55d97a2f221ede0f934dd9ad')


class TestBolt11(ElectrumTestCase):
    def test_shorten_amount(self):
        tests = {
            Decimal(10)/10**12: '10p',
            Decimal(1000)/10**12: '1n',
            Decimal(1200)/10**12: '1200p',
            Decimal(123)/10**6: '123u',
            Decimal(123)/1000: '123m',
            Decimal(3): '3',
            Decimal(1000): '1000',
        }

        for i, o in tests.items():
            self.assertEqual(shorten_amount(i), o)
            assert unshorten_amount(shorten_amount(i)) == i

    @staticmethod
    def compare(a, b):

        if len([t[1] for t in a.tags if t[0] == 'h']) == 1:
            h1 = sha256([t[1] for t in a.tags if t[0] == 'h'][0].encode('utf-8')).digest()
            h2 = [t[1] for t in b.tags if t[0] == 'h'][0]
            assert h1 == h2

        # Need to filter out these, since they are being modified during
        # encoding, i.e., hashed
        a.tags = [t for t in a.tags if t[0] != 'h' and t[0] != 'n']
        b.tags = [t for t in b.tags if t[0] != 'h' and t[0] != 'n']

        assert b.pubkey.serialize() == PUBKEY, (hexlify(b.pubkey.serialize()), hexlify(PUBKEY))
        assert b.signature is not None

        # Unset these, they are generated during encoding/decoding
        b.pubkey = None
        b.signature = None

        assert a.__dict__ == b.__dict__, (pprint.pformat([a.__dict__, b.__dict__]))

    def test_roundtrip(self):
        longdescription = ('One piece of chocolate cake, one icecream cone, one'
                          ' pickle, one slice of swiss cheese, one slice of salami,'
                          ' one lollypop, one piece of cherry pie, one sausage, one'
                          ' cupcake, and one slice of watermelon')

        timestamp = 1615922274
        tests = [
            (LnAddr(date=timestamp, paymenthash=RHASH, payment_secret=PAYMENT_SECRET, tags=[('d', ''), ('9', 33282)]),
             "lnyc1ps9zprzpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqsp5zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zygsdqq9qypqszvmpzfypnawsz97x93fe2dj92d6gq8fwdwye60s3em0dnnq30fdzq43h670f6xzwtcxsexhd6csmfjavvdrw76hkvk9rdgx0fmj8m9ucpk0cr9m"),
            (LnAddr(date=timestamp, paymenthash=RHASH, payment_secret=PAYMENT_SECRET, amount=Decimal('0.001'), tags=[('d', '1 cup coffee'), ('x', 60), ('9', 0x28200)]),
             "lnyc1m1ps9zprzpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqsp5zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zygsdq5xysxxatsyp3k7enxv4jsxqzpu9qy9qsqrvdnshzgcelnye3pqghtsp3etmhtljxanmnwpsnsg03hmwfxcvwkuam25a5r6vdvxz0na7w7p0320mt0k00p3gqp3uule734zqmw34sq0pj3ky"),
            (LnAddr(date=timestamp, paymenthash=RHASH, payment_secret=PAYMENT_SECRET, amount=Decimal('1'), tags=[('h', longdescription), ('9', 0x28200)]),
             "lnyc11ps9zprzpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqsp5zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zygshp58yjmdan79s6qqdhdzgynm4zwqd5d7xmw5fk98klysy043l2ahrqs9qy9qsq0dlwsu2t45xhxxwu9eelv5p2weusd4q7evjv02j4lx26d7yad4whdv9tlpy6dj6cd7jr7c2w9qedl3agctpczp4dz8f06jfve8z903sq6qlktz"),
            (LnAddr(date=timestamp, paymenthash=RHASH, payment_secret=PAYMENT_SECRET, net=constants.BitcoinTestnet, tags=[('f', 'mk2QpYatsKicvFVuTAQLBryyccRXMUaGHP'), ('h', longdescription), ('9', 0x28200)]),
             "lntc1ps9zprzpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqsp5zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zygsfpp3x9et2e20v6pu37c5d9vax37wxq72un98hp58yjmdan79s6qqdhdzgynm4zwqd5d7xmw5fk98klysy043l2ahrqs9qy9qsqygd2gl85serf6tsuas377pz3lz2xxdzap3vd35jkn03myc9el4d960m4lv277zh5caffjgu3ssu20ea57edn98zc0pe5t7mtynayhtsq3hxmz3"),
            (LnAddr(date=timestamp, paymenthash=RHASH, payment_secret=PAYMENT_SECRET, amount=24, tags=[
                ('r', [(unhexlify('029e03a901b85534ff1e92c43c74431f7ce72046060fcf7a95c37e148f78c77255'), unhexlify('0102030405060708'), 1, 20, 3),
                       (unhexlify('039e03a901b85534ff1e92c43c74431f7ce72046060fcf7a95c37e148f78c77255'), unhexlify('030405060708090a'), 2, 30, 4)]),
                ('f', 'YPnxgNDtu6wvVs7JSwoG6J9bRS7kZfEfVQ'),
                ('h', longdescription),
                ('9', 0x28200)]),
             "lnyc241ps9zprzpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqsp5zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zygsr9yq20q82gphp2nflc7jtzrcazrra7wwgzxqc8u7754cdlpfrmccae92qgzqvzq2ps8pqqqqqqpqqqqq9qqqvpeuqafqxu92d8lr6fvg0r5gv0heeeqgcrqlnm6jhphu9y00rrhy4grqszsvpcgpy9qqqqqqgqqqqq7qqzqfpp3qjmp7lwpagxun9pygexvgpjdc4jdj85fhp58yjmdan79s6qqdhdzgynm4zwqd5d7xmw5fk98klysy043l2ahrqs9qy9qsqzdaj50ssad5tyzczc7dgq5tqsy94xnqh8uv3zh6d0rmvyj5atnx5658vn6vpg7akzlsaw9wrpzl7zd9u9l98vvstydjlmzzelcc926cpe2vm3h"),
            (LnAddr(date=timestamp, paymenthash=RHASH, payment_secret=PAYMENT_SECRET,  amount=24, tags=[('f', 'xMNWkckEqEspBKKRb6zdjDNzdGSNcrBDmw'), ('h', longdescription), ('9', 0x28200)]),
             "lnyc241ps9zprzpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqsp5zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zygsfppj3a24vwu6r8ejrss3axul8rxldph2q7z9hp58yjmdan79s6qqdhdzgynm4zwqd5d7xmw5fk98klysy043l2ahrqs9qy9qsqfdlmxkjhmw9svxntaa8gpmjd695wrd8shn9ha3yc2ufq222787733jln4nqmyxwrnz8nj9q4fqjc0st4a3lyhm37z6a4fyl4k7500vcpcdu6fk"),
            (LnAddr(date=timestamp, paymenthash=RHASH, payment_secret=PAYMENT_SECRET,  amount=24, tags=[('f', 'yc1qw508d6qejxtdg4y5r3zarvary0c5xw7kau8qtd'), ('h', longdescription), ('9', 0x28200)]),
             "lnyc241ps9zprzpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqsp5zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zygsfppqw508d6qejxtdg4y5r3zarvary0c5xw7khp58yjmdan79s6qqdhdzgynm4zwqd5d7xmw5fk98klysy043l2ahrqs9qy9qsqddas3lalfw6esuu4r7jkgghcqwrgdwte04jap5h2nah8e9pvrs2jrr733cmeuzvxu3l5ssat4qafplkkfqdyaz5stjp9zzg8sd2zpvcqdcwvfv"),
            (LnAddr(date=timestamp, paymenthash=RHASH, payment_secret=PAYMENT_SECRET,  amount=24, tags=[('f', 'yc1qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3qrlzq2q'), ('h', longdescription), ('9', 0x28200)]),
             "lnyc241ps9zprzpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqsp5zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zygsfp4qrp33g0q5c5txsp9arysrx4k6zdkfs4nce4xj0gdcccefvpysxf3qhp58yjmdan79s6qqdhdzgynm4zwqd5d7xmw5fk98klysy043l2ahrqs9qy9qsqqvvwnlv02en5hpqh7xhyc3p5r2h0j4av6rdu2u4nr5faf6gvk4jrvafnu0x3uj3dsjju4az0yhngctfg92g7v2lcmrlhrlych8xqtasqnf3k8m"),
            (LnAddr(date=timestamp, paymenthash=RHASH, payment_secret=PAYMENT_SECRET,  amount=24, tags=[('n', PUBKEY), ('h', longdescription), ('9', 0x28200)]),
             "lnyc241ps9zprzpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqsp5zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zygsnp4q0n326hr8v9zprg8gsvezcch06gfaqqhde2aj730yg0durunfhv66hp58yjmdan79s6qqdhdzgynm4zwqd5d7xmw5fk98klysy043l2ahrqs9qy9qsqf7a76nwurvpwhe9jca5q3hyj040sfx92l0xr5q0fx459svtldkrs3w7va89uszf5246446s3m5hkxxm490llsg7e9564czpd68jlw2cppp4fly"),
            (LnAddr(date=timestamp, paymenthash=RHASH, payment_secret=PAYMENT_SECRET,  amount=24, tags=[('h', longdescription), ('9', 2 + (1 << 9) + (1 << 15))]),
             "lnyc241ps9zprzpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqsp5zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zygshp58yjmdan79s6qqdhdzgynm4zwqd5d7xmw5fk98klysy043l2ahrqs9qypqsz9wrhrfv5f9a73rwn8fxnrnj80l2e53uavtls0dnklkupsjrueyzheg7k9m9lr7xag9w7yt0rjmkp988k8yhz3h8wufc9gh7f4ju7rdgqqfysw0"),
            (LnAddr(date=timestamp, paymenthash=RHASH, payment_secret=PAYMENT_SECRET,  amount=24, tags=[('h', longdescription), ('9', 10 + (1 << 8) + (1 << 15))]),
             "lnyc241ps9zprzpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqsp5zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zygshp58yjmdan79s6qqdhdzgynm4zwqd5d7xmw5fk98klysy043l2ahrqs9qypqg2qatdk0rt7sqnlqnd4rjt5ywv79h5lejg24g8zywyvrsq2e8za95n5cvsk3la0kws2cd0ctdawweucxf2jakj3zlqg5tfy9758fjk7xgpyhw4ev"),
            (LnAddr(date=timestamp, paymenthash=RHASH, payment_secret=PAYMENT_SECRET,  amount=24, tags=[('h', longdescription), ('9', 10 + (1 << 9) + (1 << 15))]),
             "lnyc241ps9zprzpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqsp5zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zygshp58yjmdan79s6qqdhdzgynm4zwqd5d7xmw5fk98klysy043l2ahrqs9qypqs2z9tzrzagsffjwlql2334gza8h9e24dxjgg6mc5qysrgcnl3jzqhq8xnnz8ecepa23ey9qp7rk0wlzp3pyd89x9p0s3wv5wxm3pms8uqq0efhyg"),
            (LnAddr(date=timestamp, paymenthash=RHASH, payment_secret=PAYMENT_SECRET,  amount=24, tags=[('h', longdescription), ('9', 10 + (1 << 9) + (1 << 14))]),
             "lnyc241ps9zprzpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqsp5zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zygshp58yjmdan79s6qqdhdzgynm4zwqd5d7xmw5fk98klysy043l2ahrqs9qrss2d2747gsaxt85sfaw3sntvmga9rkjrd259mh605mxdyv7dfdqrsvntvedynhwyqcezht242djkzl333heyjkc7hvgdk9sqzqrslyshespmrne6n"),
        ]
        # Some old tests follow that do not have payment_secret. Note that if the parser raised due to the lack of features/payment_secret,
        # old wallets that have these invoices saved (as paid/expired), could not be opened (though we could do a db upgrade and delete them).
        tests.extend([
            (LnAddr(date=timestamp, paymenthash=RHASH, tags=[('d', '')]),
             "lnyc1ps9zprzpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqdqq0qkzeuc5f49j6qumnslnt6h3vrsx06llf0mm9a9xle2a958dm5vpxa6zmrje9ff260k23q5g2haf23z0x20g5tp0phdy2qeygjnal0sqt3tau5"),
            (LnAddr(date=timestamp, paymenthash=RHASH, amount=Decimal('0.001'), tags=[('d', '1 cup coffee'), ('x', 60)]),
             "lnyc1m1ps9zprzpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqdq5xysxxatsyp3k7enxv4jsxqzpu2aeduvrryugwa3tt8mlwvgsq8ygqt3rzgtnwq22y4jfcl2da95w9fgxu39tsrkmqk5wd50uy0qzakv8q5vm5lg50d39genrg5rkweuqqu2v5rj"),
            (LnAddr(date=timestamp, paymenthash=RHASH, amount=Decimal('1'), tags=[('h', longdescription)]),
             "lnyc11ps9zprzpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqhp58yjmdan79s6qqdhdzgynm4zwqd5d7xmw5fk98klysy043l2ahrqsfrhm0eqz2eq4ayqrheh2eea0lhjha0wvf9lp35kt4ljhk8kf3w0zgrkzwv7s2fv5209hykrd5rgz50wek3j4xk4jmap44qjferhms8qp35qyqg"),
            (LnAddr(date=timestamp, paymenthash=RHASH, net=constants.BitcoinTestnet, tags=[('f', 'mk2QpYatsKicvFVuTAQLBryyccRXMUaGHP'), ('h', longdescription)]),
             "lntc1ps9zprzpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqfpp3x9et2e20v6pu37c5d9vax37wxq72un98hp58yjmdan79s6qqdhdzgynm4zwqd5d7xmw5fk98klysy043l2ahrqstzxlmv2e97l824j6h2n7xz27ex8a6aynz2kj4lp86mhehnrcr5v8zjjhlvlmmm5pw2qlmsuq7c3q276mtllcj3aja3cp6zxfewvc7lspww8z9p"),

        ])

        # Roundtrip
        for lnaddr1, invoice_str1 in tests:
            invoice_str2 = lnencode(lnaddr1, PRIVKEY)
            self.assertEqual(invoice_str1, invoice_str2)
            lnaddr2 = lndecode(invoice_str2, net=lnaddr1.net)
            self.compare(lnaddr1, lnaddr2)

    def test_n_decoding(self):
        # We flip the signature recovery bit, which would normally give a different
        # pubkey.
        _, hrp, data = bech32_decode(
            lnencode(LnAddr(paymenthash=RHASH, payment_secret=PAYMENT_SECRET, amount=24, tags=[('d', ''), ('9', 33282)]), PRIVKEY),
            ignore_long_length=True)
        databits = u5_to_bitarray(data)
        databits.invert(-1)
        lnaddr = lndecode(bech32_encode(segwit_addr.Encoding.BECH32, hrp, bitarray_to_u5(databits)), verbose=True)
        assert lnaddr.pubkey.serialize() != PUBKEY

        # But not if we supply expliciy `n` specifier!
        _, hrp, data = bech32_decode(
            lnencode(LnAddr(paymenthash=RHASH, payment_secret=PAYMENT_SECRET, amount=24, tags=[('d', ''), ('n', PUBKEY), ('9', 33282)]), PRIVKEY),
            ignore_long_length=True)
        databits = u5_to_bitarray(data)
        databits.invert(-1)
        lnaddr = lndecode(bech32_encode(segwit_addr.Encoding.BECH32, hrp, bitarray_to_u5(databits)), verbose=True)
        assert lnaddr.pubkey.serialize() == PUBKEY

    def test_min_final_cltv_expiry_decoding(self):
        lnaddr = lndecode("lnyc500u1p5cjt8tpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqsp5qyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqsdqqcqzys9qypqsztgkaz3n5nr5ppcqaug6zvgxdj59877pdqq8suxp3aqk0al0sjerz6tdx6cr2h6npem4u4v3ptgdq3avkg44uhw3um0snxlr8h969ccqqz7s5vv")
        self.assertEqual(144, lnaddr.get_min_final_cltv_expiry())

        lnaddr = lndecode("lntc150u1p5cjt8tpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqsp5qyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqszqgpqyqsdqqcqp79qypqszpqa4w2rcgcdk7604z2tytarvkvl6za87stzkr0cgtpfm877axmg92x33tancf0fdwsaday6766uux7rd4dlk7nsslsppnmwjyfp80kgp9gwc5m",
                          net=constants.BitcoinTestnet)
        self.assertEqual(30, lnaddr.get_min_final_cltv_expiry())

    def test_min_final_cltv_expiry_roundtrip(self):
        for cltv in (1, 15, 16, 31, 32, 33, 150, 511, 512, 513, 1023, 1024, 1025):
            lnaddr = LnAddr(
                paymenthash=RHASH, payment_secret=b"\x01"*32, amount=Decimal('0.001'), tags=[('d', '1 cup coffee'), ('x', 60), ('c', cltv), ('9', 33282)])
            self.assertEqual(cltv, lnaddr.get_min_final_cltv_expiry())
            invoice = lnencode(lnaddr, PRIVKEY)
            self.assertEqual(cltv, lndecode(invoice).get_min_final_cltv_expiry())

    def test_features(self):
        lnaddr = lndecode("lnyc25m1p5cjtxhpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqsp5zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zygsdqq9qypqsz8yst7k0ywepazt7jerunv8qdqsx7k4yvpzmrpu3wqcuwzrejn5zzr7rpv9cuc3psj6pyf6jphdprtutcv92cgw35xsv2c0eegm34qvsqykmmkc")
        self.assertEqual(33282, lnaddr.get_tag('9'))
        self.assertEqual(LnFeatures(33282), lnaddr.get_features())

        with self.assertRaises(UnknownEvenFeatureBits):
            lndecode("lnyc25m1p5cjt68pp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqdqq9qygqqqy4vtmm6z27qp39l9qe5wuh8elu8g52xt7u0dlctwklm4yxczvccyjf4047w604eqp5z3pdjwvn4gr93p543u53q9medj7dauay3859cqc87f37")

    def test_payment_secret(self):
        lnaddr = lndecode("lnyc25m1p5cjtxhpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqsp5zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zygsdqq9q5sqqqqqqqqqqqqqqqpqsqtjzhmnu8xq5vndl5x95feth92yj4ett0fj3jpurv422ffzwx468z9lwe6fsngd8lg0h4fc4uqsnkv3c3888uanexa7xdfsgx03dt4nqqpxwak3")
        self.assertEqual((1 << 9) + (1 << 15) + (1 << 99), lnaddr.get_tag('9'))
        self.assertEqual(b"\x11" * 32, lnaddr.payment_secret)

    def test_derive_payment_secret_from_payment_preimage(self):
        preimage = bytes.fromhex("cc3fc000bdeff545acee53ada12ff96060834be263f77d645abbebc3a8d53b92")
        self.assertEqual("bfd660b559b3f452c6bb05b8d2906f520c151c107b733863ed0cc53fc77021a8",
                         derive_payment_secret_from_payment_preimage(preimage).hex())

    def test_validate_and_compare_features(self):
        lnaddr = lndecode("lnyc25m1p5cjtxhpp5qqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqqqsyqcyq5rqwzqfqypqsp5zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zyg3zygsdqq9q5sqqqqqqqqqqqqqqqpqsqtjzhmnu8xq5vndl5x95feth92yj4ett0fj3jpurv422ffzwx468z9lwe6fsngd8lg0h4fc4uqsnkv3c3888uanexa7xdfsgx03dt4nqqpxwak3")
        lnaddr.validate_and_compare_features(LnFeatures((1 << 8) + (1 << 14) + (1 << 15)))
        with self.assertRaises(IncompatibleLightningFeatures):
            lnaddr.validate_and_compare_features(LnFeatures((1 << 8) + (1 << 14) + (1 << 16)))
