#!/usr/bin/python
import time
import datetime as dt
import os
import sys
from multiprocessing import Process
import binascii, hashlib, base58
import pandas as pd
import numpy as np
import urllib.request

try:
    from fastecdsa import keys, curve
except ImportError:
    print(f'Failed to import fastecdsa, falling back to ecdsa...')
    import ecdsa


def reporthook(count, block_size, total_size):
    global start_time
    if count == 0:
        start_time = time.time()
        return
    duration = time.time() - start_time
    progress_size = int(count * block_size)
    speed = int(progress_size / (1024 * duration))
    percent = min(int(count * block_size * 100 / total_size), 100)
    print(f"Progress: {percent}%, {progress_size/(1024*1024):,.2f} MB, {speed:,.0f} KB/s, ({duration:,.2f}s)...", end='\r')


def ripemd160(x):
    d = hashlib.new('ripemd160')
    d.update(x)
    return d


def ecdsa_priv_key():
    return os.urandom(32)


def ecdsa_pub_key(private_key):
    sk = ecdsa.SigningKey.from_string(private_key, curve=ecdsa.SECP256k1)
    vk = sk.get_verifying_key()
    publ_key = '04' + binascii.hexlify(vk.to_string()).decode()
    return publ_key


def ecdsa_address(public_key):
    hash160 = ripemd160(hashlib.sha256(binascii.unhexlify(public_key)).digest()).digest()
    publ_addr_a = b"\x00" + hash160
    checksum = hashlib.sha256(hashlib.sha256(publ_addr_a).digest()).digest()[:4]
    publ_addr_b = base58.b58encode(publ_addr_a + checksum)
    return publ_addr_b.decode()


def ecdsa_wif(private_key):
    fullkey = '80' + binascii.hexlify(private_key).decode()
    sha256a = hashlib.sha256(binascii.unhexlify(fullkey)).hexdigest()
    sha256b = hashlib.sha256(binascii.unhexlify(sha256a)).hexdigest()
    WIF = base58.b58encode(binascii.unhexlify(fullkey+sha256b[:8]))
    return WIF.decode()


def fastecdsa_priv_key():
    return binascii.hexlify(os.urandom(32)).decode('utf-8').upper()


def fastecdsa_pub_key(private_key):
    """Accept a hex private key and convert it to its respective public key. Because converting a private key to
    a public key requires SECP256k1 ECDSA signing, this function is the most time consuming and is a bottleneck
    in the overall speed of the program.
    """
    # get the public key corresponding to the private key we just generated
    c = int('0x%s'%private_key,0)
    d = keys.get_public_key(c, curve.secp256k1)
    return '04%s%s'%('{0:064x}'.format(int(d.x)), '{0:064x}'.format(int(d.y)))


def fastecdsa_address(public_key):
    #Accept a public key and convert it to its resepective P2PKH wallet address.
    #print('Wanting to [%s] this to address'%public_key)
    output = []; alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
    var = hashlib.new('ripemd160')
    var.update(hashlib.sha256(binascii.unhexlify(public_key.encode())).digest())
    var = '00' + var.hexdigest() + hashlib.sha256(hashlib.sha256(binascii.unhexlify(('00' + var.hexdigest()).encode())).digest()).hexdigest()[0:8]
    count = [char != '0' for char in var].index(True) // 2
    n = int(var, 16)
    while n > 0:
        n, remainder = divmod(n, 58)
        output.append(alphabet[remainder])
    for i in range(count): output.append(alphabet[0])
    return ''.join(output[::-1])


def seek(process, df, isdataframe):
    global processes
    file_out = 'btc_keys'
    LOG_EVERY_N = 1000
    start_time = dt.datetime.today().timestamp()
    i = 0
    print(f"Process {process}: searching for keys...")

    while True:
        i += 1

        if use_fastecdsa:
            priv_key = fastecdsa_priv_key()
            pub_key = fastecdsa_pub_key(priv_key)
            address = fastecdsa_address(pub_key)
        else:
            priv_key = ecdsa_priv_key()
            pub_key = ecdsa_pub_key(priv_key)
            address = ecdsa_address(pub_key)

        time_diff = dt.datetime.today().timestamp() - start_time
        timestamp = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if (i % LOG_EVERY_N) == 0:
            print(f"{timestamp} - ~{(i/time_diff)*processes:,.2f} keys/sec, ~{i*processes:,.0f} keys tested", end='\r')

        if isdataframe:
            if address in df.index.values:
                if use_fastecdsa:
                    private_key = priv_key
                else:
                    private_key = ecdsa_wif(priv_key)

                balance = df.loc[address].balance
                print(f"\n{timestamp} - !!!!! Private key found for {address}: {private_key} [balance: {balance}] !!!!!\n")
                f = open(file_out, 'a')
                f.write(f"{address}: {private_key}")
                f.close()
        else:
            if address in df:
                if use_fastecdsa:
                    private_key = priv_key
                else:
                    private_key = ecdsa_wif(priv_key)

                print(f"\n{timestamp} - !!!!! Private key found for {address}: {private_key} !!!!!\n")
                f = open(file_out, 'a')
                f.write(f"{address}: {private_key}")
                f.close()


if __name__ == '__main__':
    global processes
    processes = 12
    file_url = 'http://addresses.loyce.club/blockchair_bitcoin_addresses_and_balance_LATEST.tsv.gz'
    known_wallets_gzip = 'btc_balance_sorted.tsv.gz'
    known_wallets = 'btc_balance_sorted.csv'
    known_wallets_txt = 'btc_addresses.txt'
    cleaned_wallets = 'btc_balance_sorted_clean.csv'
    min_balance = 100000000 # 100000000 = 1 BTC

    file_info = urllib.request.urlopen(file_url)
    download_list = input(f"Would you like to download the most recent list of known bitcoin addresses with a non-zero balance ({file_info.length/1024/1024:,.2f} MB)? [y/n] ")
    if download_list.lower() == 'yes' or download_list.lower() == 'y' or (not os.path.exists(known_wallets_gzip) and not os.path.exists(cleaned_wallets)):
        print(f"Downloading latest wallet list from {file_url}")
        urllib.request.urlretrieve(file_url, known_wallets_gzip, reporthook)
        print(f"\nCompleted, list saved as {known_wallets_gzip}")

    if os.path.exists(cleaned_wallets):
        if not os.path.exists(known_wallets_gzip):
            use_existing_data = 'yes'
        else:
            use_existing_data = input(f"Existing wallet file found, would you like to use it? [y/n] ")
    else:
        use_existing_data = 'no'

    print(f"Loading known wallet addresses...")
    if use_existing_data.lower() == 'yes' or use_existing_data.lower() == 'y':
        df = pd.read_csv(cleaned_wallets, sep=',', index_col='address')
    else:
        df = pd.read_csv(known_wallets_gzip, compression='gzip', sep='\t', index_col='address')

    # Filter out multisig and low balance wallets
    print(f"Cleaning up data, min. balance: {min_balance:,.0f} satoshi ({min_balance/100000000:,} BTC)...")
    df = df.filter(regex='^1', axis=0)
    df = df[df['balance'] >= min_balance]
    df.to_csv(cleaned_wallets)
    print(f"Found {df.size:,.0f} eligble addresses, starting up {processes} processes...")
    if all(x in sys.modules for x in ['fastecdsa.keys', 'fastecdsa.curve']):
        use_fastecdsa = True
    else:
        use_fastecdsa = False

    # Save addresses to known_wallets_txt
    np.savetxt(known_wallets_txt, df.index, fmt='%s')

    for process in range(processes):
        if os.path.exists(known_wallets_txt):
            addr_lines = open(known_wallets_txt).readlines()
            addr_lines.sort()
            addr_set = set(addr_lines)

            p = Process(target=seek, args=(process, addr_set, False))
            p.start()
        else:
            p = Process(target=seek, args=(process, df, True))
            p.start()
