# What is this?
This is an update to a BTC private key brute force script found [here](https://github.com/Xefrok/BitBruteForce-Wallet). This script tries to improve upon it by using an in-memory DataFrame.

# How does the script work?
It uses the same method of approach found in the [original script](https://github.com/Xefrok/BitBruteForce-Wallet), except instead of looping through a text file containing all the addresses, it uses a set of BTC addresses if possible and falls back to a Pandas DataFrame where each individual address is the key. If you OS supports it, it will also make use of fastecdsa.
To add to this, it also allows you to download the latest list of addresses from [Loyce Club](http://addresses.loyce.club/) and use that as a starting point.

# Speed
This script was tested on a 5th gen Ryzen CPU, and when using regular ecdsa with 6 processes on a list containing ~340,000 addresses it reached ~2,500 keys per second, per process. Adding these 6 processes up, this amounts to approximately 15,000 keys/sec total => 54,000,000 keys/hour => 1,296,000,000 keys/day => ~473,040,000,000 keys/year. Be aware though that the amount of keys/sec is heavily dependant on your CPU's power.

# Does it work?
Supposedly. However, chances of finding the private key belonging to an address on any list are **EXTREMELY** small. If you do however achieve the impossible and find one, please be mindful of it's actual owner and don't steal their money (unless you are **absolutely 100% certain** the wallet is dead).

# If you like it
**bc1qj49ruupswqg3ulc3jx4gfcydnwdvmy8lffhlqf**

# Requirements
- Python 3.x
- pip install fastecdsa (or pip install ecdsa if fastecdsa is not available)
- pip install base58
- pip install pandas
- pip install numpy
- 2,000,000,000 Years
