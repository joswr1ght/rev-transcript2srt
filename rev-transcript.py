#!/usr/bin/env python3
import sys
import os
import json
import nltk
from datetime import timedelta
import pdb


def splitsentence(s: str, maxlen: int = 50) -> list:
    """
    Take a sentence

    Args:
        s: Sentence as a string
        maxlen: Maximum length of the chunk in chars

    Returns:
        list of sentence broken up into smaller chunks
    """
    chunks = []
    chunk = ''
    words = s.split(' ')
    for word in words:
        if len(chunk) + len(word) <= maxlen:
            chunk += word + ' '
        else:
            # Finish this chunk, add to chunks list
            chunks.append(chunk)
            chunk = word + ' '

    # Append the last chunk
    chunks.append(chunk)
    chunks = [x.strip(' ') for x in chunks]

    return chunks


# Take input text and return a list of sentences. Does not strip newlines.
def splitparagraph(text: str) -> list:
    return nltk.tokenize.sent_tokenize(text)


if __name__ == '__main__':
    if (len(sys.argv) != 2):
        sys.stderr.write(f'Usage: {os.path.basename(sys.argv[0])} [Frost JSON file]\n')
        sys.exit(0)

with open(sys.argv[1]) as f:
    frost = json.loads(f.read())
    fcontent = frost['content'][0]['content']

    linecount = 1
    for para in fcontent:
        ptranscript = para['content'][0]['text']
        ptimestamps = para['attrs']['timestamps']
        captionindex = 0  # Index for word and timing marker lists

        # Split the paragraph transcript content into sentences.
        psentences = splitparagraph(ptranscript)
        wordlist = ' '.join(psentences).split(' ')

        # Each sentence becomes a SRT transcript line with timing markers
        for psentence in psentences:

            # Some sentences are too long; split up longer sentences into
            # smaller chunks.
            if (len(psentence) < 50):
                partials = [psentence]
            else:
                partials = splitsentence(psentence)

            for partial in partials:
                wordcount = len(partial.split(' '))
                start = ptimestamps[captionindex]['s']
                end = ptimestamps[captionindex+(wordcount-1)]['e']

                starttimefmt = str(timedelta(seconds=start))[0:-3].replace('.', ',')
                endtimefmt = str(timedelta(seconds=end))[0:-3].replace('.', ',')

                print(linecount)
                print(f'{starttimefmt} --> {endtimefmt}')
                print(f'{partial}\n')

                captionindex += wordcount
                linecount += 1
