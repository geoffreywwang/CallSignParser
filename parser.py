import os
import re
import pickle
import functools
from datetime import date
from dateutil.relativedelta import relativedelta

class MorseUtils:
    """
    A class for morse code related functions.
    """

    # Letter to dot/dash represenation
    letter2code = { 'A':'.-', 'B':'-...',
                    'C':'-.-.', 'D':'-..', 'E':'.',
                    'F':'..-.', 'G':'--.', 'H':'....',
                    'I':'..', 'J':'.---', 'K':'-.-',
                    'L':'.-..', 'M':'--', 'N':'-.',
                    'O':'---', 'P':'.--.', 'Q':'--.-',
                    'R':'.-.', 'S':'...', 'T':'-',
                    'U':'..-', 'V':'...-', 'W':'.--',
                    'X':'-..-', 'Y':'-.--', 'Z':'--..',
                    '1':'.----', '2':'..---', '3':'...--',
                    '4':'....-', '5':'.....', '6':'-....',
                    '7':'--...', '8':'---..', '9':'----.',
                    '0':'-----', ', ':'--..--', '.':'.-.-.-',
                    '?':'..--..', '/':'-..-.', '-':'-....-',
                    '(':'-.--.', ')':'-.--.-'}
    
    # Letter to weight of a letter (1 for dots, 3 for dashes, and 1 between dots/dashes)
    letter2weight = { k : functools.reduce(lambda a, b: a + 3 + 1 if b == '-' else a + 1 + 1, v, -1) for k, v in letter2code.items()}

    @classmethod
    def str_to_morse_weight(cls, s: str) -> int:
        """
        Calculate morse code weight of a string
        """
        return functools.reduce(lambda a, b: a + cls.letter2weight[b] + 3, s, 0)

class CallSignParser:
    """
    A class to parse the FCC ULS database for available ameteur radio call signs
    """

    @staticmethod
    def db_str_to_date(s):
        """
        Convert string from database to date object
        """
        return date(int(s[6:10]), int(s[:2]), int(s[3:5]))

    @staticmethod
    def parse(path: str, print_freq=0):
        # Compile regex to parse each line
        parser = re.compile('^(?:[^|]*\|){4}(?P<call>[^|]*)\|(?:[^|]*\|){3}(?P<expire>[^|]*)\|(?P<cancel>[^|]*)')

        # Create output dictionary
        call_signs = {}

        # Create line counter
        line_count = 0

        # Open file and parse lines until end of file
        with open(path) as f:

            print(f'Parsing {path}')

            line = f.readline()
            while line:
                parsed = parser.match(line)

                # Check if line matches expected database format
                if parsed:

                    # Extract information
                    call_sign = parsed.group('call')
                    raw_expire = parsed.group('expire')
                    raw_cancel = parsed.group('cancel')

                    # Check if call sign has an expiration date
                    if raw_expire:
                        expire = CallSignParser.db_str_to_date(raw_expire)
                        
                        # Check if call sign has a canceled date
                        cancel = None
                        if raw_cancel:
                            cancel = CallSignParser.db_str_to_date(raw_cancel)

                        # If cancel date is before expire date, available date is 2 years and 1 day after cancel date
                        if cancel and cancel < expire:
                            available = cancel + relativedelta(days=1, years=2)

                        # Otherwise available date is 2 years and 1 day after expire date
                        else:
                            available = expire + relativedelta(days=1, years=2)

                        # Add information to output dictionary
                        if call_sign in call_signs.keys():
                            call_signs[call_sign] = max(available, call_signs[call_sign])   # Take the newest available date if record is updated
                        else:
                            call_signs[call_sign] = available

                # Print and update line count
                line_count += 1
                if print_freq != 0 and line_count % print_freq == 0:
                    print(f'Current line: {line_count}')
                line = f.readline()

            print('Finished parsing!')
            return call_signs


if __name__ == '__main__':
    # Parse database or load call signs from pickle
    if not os.path.exists('call_signs.pkl'):
        call_signs = CallSignParser.parse('HD.dat')
        pickle.dump(call_signs, open('call_signs.pkl', 'wb'))
        print('Dumped call_signs to pickle!')
    else:
        call_signs = pickle.load(open('call_signs.pkl', 'rb'))
        print('Loaded call_signs from pickle!')

    # Filter/collect call signs by available date
    available_dates = {}
    for call_sign in call_signs.keys():

        # Call sign filtering
        if call_signs[call_sign] >= date(2022, 4, 1) and len(call_sign) == 4:
            if str(call_signs[call_sign]) in available_dates.keys():
                available_dates[str(call_signs[call_sign])].append(call_sign)
            else:
                available_dates[str(call_signs[call_sign])] = [call_sign]

    # Print out next X batches of call signs
    for i, available_date in enumerate(sorted(available_dates.keys())):
        if i >= 20:
            break

        # Sort call sign by CW weight
        available_dates[available_date].sort(key=lambda a: MorseUtils.str_to_morse_weight(a))

        # Print call signs
        print(available_date, ' '.join(available_dates[available_date]))

        # Print corresponding CW weights
        print(' '*len(available_date), ' '.join(str(MorseUtils.str_to_morse_weight(call_sign)).rjust(len(call_sign), ' ') for call_sign in available_dates[available_date]))
