If you want to create one video at a time, just provide the single set of conversation to the conversations.txt file, then run `python main.py`

If you need to create multiple videos in a single stretch, provide multiple set of conversation into the conversations.txt file, as per the reference file (sample-bulk-conversation.txt) and provide the conversations according to it, then run 
`python create_in_bulk.py` 

# TODO
* Make the conversation text size smaller
* ⁠Reduce the text appearance at a time
* Fix emotion of the depressed character - ISSUE: If he looks curious on one image, and on the following image he looks exhausted again. FIX: Instead, the same base template as before should be used.