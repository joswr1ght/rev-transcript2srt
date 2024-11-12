#!/usr/bin/env python3
import sys
import os
import json
import nltk
from datetime import timedelta


def splitsentence(s: str, maxlen: int = 60) -> list:
    """
    Take a sentence and split it into multiple chunks of words, not exceeding maxlen.
    Splits on whitespace.

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
    """
    Split a paragraph into multiple sentences. Does not strip newlines.

    Args:
        text: Paragraph text.

    Returns:
        List of sentences.
    """
    return nltk.tokenize.sent_tokenize(text)


def sectosrttime(td: timedelta) -> str:
    """
    Take a <class 'datetime.timedelta'> and convert it to SRT-formatted time
    marker (e.g., "0:13:39,870").

    Args:
        td: class 'datetime.timedelta'

    Returns:
        String formatted for SRT time marker.

    """
    tdstr = str(td)
    if '.' not in tdstr:
        # Timedelta does not have microsecond precision
        srtmarker = tdstr + ',000'
    else:
        srtmarker = tdstr[0:-3].replace('.', ',')

    return srtmarker


if __name__ == '__main__':
    if (len(sys.argv) != 2):
        sys.stderr.write(f'Usage: {os.path.basename(sys.argv[0])} [Frost JSON file]\n')
        sys.exit(0)

    with open(sys.argv[1]) as f:
        frost = json.loads(f.read())
        frostappliedpmdoc = json.loads(frost['frostTranscript']['appliedPmDocJson'])
        fcontent = frostappliedpmdoc['content'][0]['content']

        # Track the last time end marker for each sentence to ensure
        # the next marker start does not happen happen before the last
        # marker stop.
        lastendtime = timedelta(seconds=0)

        linecount = 1
        for para in fcontent:

            try:
                ptranscript = para['content'][0]['text']
                ptimestamps = para['attrs']['timestamps']
            except KeyError:
                # Some Rev transcript JSON files don't include the whole text
                # in element 0; reproduce if missing by walking list
                ptranscript = ''
                ptimestamps = []
                # para['content'][0]['content'][0]['text']
                for p in para['content']:
                    ptranscript += p['content'][0]['text']
                    ptimestamps.append(p['attrs'])

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

                    # Rarely there will be no ending or start timestamp in the Rev
                    # JSON data. Use the last timestamp here instead, plus or minus
                    # a second, for subsequent manual review and correction.
                    try:
                        start = ptimestamps[captionindex]['s']
                    except IndexError:
                        ptimestamps[0]['s']+1
                    try:
                        end = ptimestamps[captionindex+(wordcount-1)]['e']
                    except IndexError:
                        ptimestamps[-1]['e']+1

                    # Instead of tracking start and stop timestamps, just use
                    # the last end timestamp as the start of the next
                    # timestamp. This will place a caption on every part of the
                    # video, but the results are more accurate with fewer
                    # problems. YMMV.

                    # if (lastendtime > timedelta(seconds=start)):
                    #     # The transcript has a bad timing marker, indicating
                    #     # that the previous partial ended after the start of
                    #     # the next. Use the previous end marker as the start
                    #     # instead.
                    #     starttimefmt = sectosrttime(lastendtime)
                    # else:
                    #     starttimefmt = sectosrttime(timedelta(seconds=start))

                    starttimefmt = sectosrttime(lastendtime)
                    endtimefmt = sectosrttime(timedelta(seconds=end))

                    # Record the end time for this partial for comparison to
                    # the next start time.
                    lastendtime = timedelta(seconds=end)

                    print(linecount)
                    print(f'{starttimefmt} --> {endtimefmt}')
                    print(f'{partial}\n')

                    captionindex += wordcount
                    linecount += 1
