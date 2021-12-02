# What is this?
This is an update to a BTC private key brute force script found [here](https://github.com/Xefrok/BitBruteForce-Wallet). This script tries to improve upon it by using an in-memory DataFrame.

# How does the script work?
It uses the same method of approach found in the [original script](https://github.com/Xefrok/BitBruteForce-Wallet), except instead of looping through a text file containing all the addresses, it uses a Pandas DataFrame where each individual address is the key.
To add to this, it also allows you to download the latest list of addresses from the [Bitcoin Address Database](https://bitkeys.work/) and use that as a starting point.

# Speed
This script was tested on a 5th gen Ryzen CPU, and when using 6 processes on a list containing ~147,000 addresses it reached ~850 keys per second, per process. Adding these 6 processes up, this amounts to approximately 5,100 keys/sec total => 18,360,000 keys/hour => 440,640,000 keys/day => ~160,833,600,000 keys/year. Be aware though that the amount of keys/sec is heavily dependant on both your CPU's power and the size of the address list being used and decreases as the list increases.

# Does it work?
Supposedly. However, chances of finding the private key belonging to an address on any list are **EXTREMELY** small. If you do however achieve the impossible and find one, please be mindful of it's actual owner and don't steal their money (unless you are **absolutely 100% certain** the wallet is dead).

# If you like it
**bc1qj49ruupswqg3ulc3jx4gfcydnwdvmy8lffhlqf**

# Requirements
- Python 3.x
- pip install ecdsa
- pip install base58
- pip install pandas
- 3,000,000,000 Years
