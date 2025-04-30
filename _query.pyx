cdef float calculate_word_score(str word, list title_words, int min_length, int longest_word):
    cdef float score = 0.0
    cdef str title_word
    cdef float match_percentage

    for title_word in title_words:
        if len(word) >= min_length:
            if word == title_word:
                return 1.0
        if word in title_word:
            match_percentage = len(word) / longest_word
            score += match_percentage
    return score


cpdef float calculate_match_score(str title, set query, int min_length=3):
    cdef float score = 0.0
    cdef list title_words = title.split()
    cdef str word
    cdef int longest_word

    longest_word = 0
    for word in title_words:
        if len(word) > longest_word:
            longest_word = len(word)

    for word in query:
        score += calculate_word_score(word, title_words, min_length, longest_word)
    return score
