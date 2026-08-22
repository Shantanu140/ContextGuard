"""
Day 2 -- ContextGuard project
------------------------------
Goal: read a .py file and report:
  1. total number of lines
  2. total number of words
  3. number of UNIQUE words
  4. the 5 most common words (a small taste of dictionaries doing real work)

New concepts today: lists, dictionaries, and sets -- and how each one is
suited to a different kind of question.
"""


def analyze_file(file_path):
    with open(file_path, "r") as f:
        lines = f.readlines()  # a LIST of strings, one per line (same as Day 1)
        
    total_lines = len(lines)  # len() works on lists just like it works on strings

    # ---- Building a list of every word in the file ----
    all_words = []  # start with an empty list
    for line in lines:
        # .split() breaks a line into words wherever there's whitespace,
        # and gives back a LIST of the pieces.
        # Example: "def add_numbers(a, b):" -> ["def", "add_numbers(a,", "b):"]
        words_in_line = line.split()

        # .extend() adds every item from one list onto the end of another.
        # (This is different from .append(), which would add the WHOLE
        # words_in_line list as a single item -- we don't want that here.)
        all_words.extend(words_in_line)

    total_words = len(all_words)

    # ---- Using a SET to find unique words ----
    # Passing a list into set(...) automatically throws away duplicates.
    # We also lowercase each word first, so "The" and "the" count as the same word.
    unique_words = set(word.lower() for word in all_words)
    total_unique_words = len(unique_words)

    # ---- Using a DICTIONARY to count how often each word appears ----
    word_counts = {}  # start with an empty dictionary
    for word in all_words:
        word = word.lower()
        if word in word_counts:
            # we've seen this word before -- add 1 to its existing count
            word_counts[word] = word_counts[word] + 1
        else:
            # first time seeing this word -- start its count at 1
            word_counts[word] = 1

    # ---- Finding the 5 most common words ----
    # word_counts.items() gives us (word, count) pairs.
    # sorted(..., key=..., reverse=True) sorts those pairs by count, highest first.
    # This one line is doing a lot -- if it looks unfamiliar, that's expected;
    # we'll unpack sorting and this "key=" pattern properly on a later day.
    most_common = sorted(word_counts.items(), key=lambda pair: pair[1], reverse=True)[:5]

    # ---- Print the report ----
    print(f"File: {file_path}")
    print(f"Total lines: {total_lines}")
    print(f"Total words: {total_words}")
    print(f"Unique words: {total_unique_words}")
    print("Top 5 most common words:")
    for word, count in most_common:
        print(f"  {word!r}: {count}")


if __name__ == "__main__":
    target_file = "day1_read_file.py"  # reuse yesterday's file, or point at any .py file
    analyze_file(target_file)
