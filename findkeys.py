#!/usr/bin/python
import time
import datetime as dt
import os
from multiprocessing import Process
import binascii, hashlib, base58, ecdsa
import pandas as pd
import urllib.request


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


def seek(process, df):
    global processes
    file_out = 'btc_keys'
    LOG_EVERY_N = 1000
    start_time = dt.datetime.today().timestamp()
    i = 0
    print(f"Process {process}: searching for keys...")

    while True:
        i += 1
        # generate private key , uncompressed WIF starts with "5"
        priv_key = os.urandom(32)
        fullkey = '80' + binascii.hexlify(priv_key).decode()
        sha256a = hashlib.sha256(binascii.unhexlify(fullkey)).hexdigest()
        sha256b = hashlib.sha256(binascii.unhexlify(sha256a)).hexdigest()
        WIF = base58.b58encode(binascii.unhexlify(fullkey+sha256b[:8]))

        # get public key , uncompressed address starts with "1"
        sk = ecdsa.SigningKey.from_string(priv_key, curve=ecdsa.SECP256k1)
        vk = sk.get_verifying_key()
        publ_key = '04' + binascii.hexlify(vk.to_string()).decode()
        hash160 = ripemd160(hashlib.sha256(binascii.unhexlify(publ_key)).digest()).digest()
        publ_addr_a = b"\x00" + hash160
        checksum = hashlib.sha256(hashlib.sha256(publ_addr_a).digest()).digest()[:4]
        publ_addr_b = base58.b58encode(publ_addr_a + checksum)
        priv = WIF.decode()
        pub = publ_addr_b.decode()

        time_diff = dt.datetime.today().timestamp() - start_time
        timestamp = dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        if (i % LOG_EVERY_N) == 0:
            print(f"{timestamp} - ~{(i/time_diff)*processes:,.2f} keys/sec, ~{i*processes:,.0f} keys tested", end='\r')
        #print(f"Worker {process}: {i} [ {pub} - {priv} ]")

        if pub in df.index.values:
            balance = df.loc[pub].balance
            print(f"\n{timestamp} - !!!!! Private key found for {pub}: {priv} [balance: {balance}] !!!!!\n")
            f = open(file_out, 'a')
            f.write(f"{pub}: {priv}")
            f.close()


if __name__ == '__main__':
    global processes
    processes = 12
    file_url = 'https://bitkeys.work/btc_balance_sorted.csv'
    known_wallets = 'btc_balance_sorted.csv'
    cleaned_wallets = 'btc_balance_sorted_clean.csv'
    min_balance = 100000000

    file_info = urllib.request.urlopen(file_url)
    download_list = input(f"Would you like to download the most recent list of known bitcoin addresses with a non-zero balance ({file_info.length/1024/1024:,.2f} MB)? [y/n] ")
    if download_list.lower() == 'yes' or download_list.lower() == 'y' or (not os.path.exists(known_wallets) and not os.path.exists(cleaned_wallets)):
        print(f"Downloading latest wallet list from https://bitkeys.work/")
        urllib.request.urlretrieve(file_url, known_wallets, reporthook)
        print(f"\nCompleted, list saved as {known_wallets}")

    if os.path.exists(cleaned_wallets):
        if not os.path.exists(known_wallets):
            use_existing_data = 'yes'
        else:
            use_existing_data = input(f"Existing wallet file found, would you like to use it? [y/n] ")
    else:
        use_existing_data = 'no'

    print(f"Loading known wallet addresses...")
    if use_existing_data.lower() == 'yes' or use_existing_data.lower() == 'y':
        df = pd.read_csv(cleaned_wallets, sep=',', index_col='address')
    else:
        df = pd.read_csv(known_wallets, sep=',', index_col='address')

    # Filter out multisig and low balance wallets
    print(f"Cleaning up data, min. balance: {min_balance:,.0f} satoshi ({min_balance/100000000:,} BTC)...")
    df = df.filter(regex='^1', axis=0)
    df = df[df['balance'] >= min_balance]
    df.to_csv(cleaned_wallets)
    print(f"Found {df.size:,.0f} eligble addresses, starting up {processes} processes...")

    for process in range(processes):
        p = Process(target=seek, args=(process, df))
        p.start()
