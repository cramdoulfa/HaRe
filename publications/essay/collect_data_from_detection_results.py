from hare import Hare, Conversation
from hare.conversation import import_conversations

from sklearn.metrics import fbeta_score

from os import mkdir
from os.path import isdir
from shutil import rmtree
from json import loads, dumps
from random import shuffle

def true_positives(true, predicted):

    result = 0

    for a,b in zip(true,predicted):
        if b == 1 and a == 1:
            result += 1

    return result


def false_positives(true, predicted):
    result = 0

    for a, b in zip(true, predicted):
        if b == 1 and a == 0:
            result += 1

    return result

#General settings
HARE_ROOT = '../../'
ESSAY_ROOT = HARE_ROOT+'publications/essay/'

CONV_HISTORY_FOLDER = ESSAY_ROOT+'results/full_results/'
CONVERSATION_HISTORY_FILES_WITH_THRESHOLDS = {'m04':[1,2,3,4,5,6,7,8,9,10],
                                              'm01':[0.001,0.0025,0.005,0.0075,0.01,0.025,0.05,0.075,0.1,0.25,0.5,0.75,1],
                                              'm02':[0.001,0.0025,0.005,0.0075,0.01,0.025,0.05,0.075,0.1,0.25,0.5,0.75,1],
                                              'm05': [0.001, 0.0025, 0.005, 0.0075, 0.01, 0.025, 0.05, 0.075, 0.1,
                                                          0.25, 0.5, 0.75, 1],
                                              'm06': [0.001, 0.0025, 0.005, 0.0075, 0.01, 0.025, 0.05, 0.075, 0.1,
                                                          0.25, 0.5, 0.75, 1]}

BETA_VALUES = [0.001,0.01,0.1,1,10,100,1000]

CONVERSATIONS_FILE = HARE_ROOT+'datasets/LoL/heldout_conversations_anon.txt'
CONVERSATION_LENGTH = 200
IDS_OF_CONVERSATIONS = [349,222,420,666,856,763,284,614,380,625]

OUTPUT_FOLDER = ESSAY_ROOT+'precalculated_data/'

#From all heldout conversations, load the first 10
all_conversations = import_conversations(CONVERSATIONS_FILE, cutoff_point=CONVERSATION_LENGTH)
conversations = [all_conversations[i] for i in IDS_OF_CONVERSATIONS]

#Cut away utterances by some speakers

# Come up with speakers aliases (artistic effect to have toxic players at random positions)
aliases_per_conversation = []
who_is_speaking_per_conversation = []

for conversation in conversations:

    speakers = list(conversation.all_speakers)
    activity_per_speaker = conversation.calculate_activity_per_speaker()
    shuffle(speakers)
    current_aliases = {speaker:speaker_index for speaker_index, speaker in enumerate(speakers)}
    current_who_is_speaking = []
    for utterance in conversation.utterances:

        speaker_alias = current_aliases[utterance.speaker]

        if speaker_alias > 9:
            speaker_alias -= 9

        current_who_is_speaking.append(speaker_alias)

    aliases_per_conversation.append(current_aliases)
    who_is_speaking_per_conversation.append(current_who_is_speaking)

    temp = 0

#Save the true target data
open(OUTPUT_FOLDER+'target.js','w').write('var target = '+dumps([aliases['TOXIC'] for aliases in aliases_per_conversation]))

#Save who is speaking
open(OUTPUT_FOLDER+'who_is_speaking.js','w').write('var who_is_speaking = '+dumps(who_is_speaking_per_conversation))

#Go through all detectors, with all thresholds
for conv_hist_file, thresholds in CONVERSATION_HISTORY_FILES_WITH_THRESHOLDS.items():

    #For each conversation, read the status at every point during the conversation
    status_per_conversation = []

    lines = open(CONV_HISTORY_FOLDER+conv_hist_file).readlines()
    for conv_index in IDS_OF_CONVERSATIONS:
        status_per_conversation.append(loads(lines[conv_index]))

    #Cut away utterances by some speakers

    # to do met conversation.remove_speaker()

    #Create a hare object for each threshold
    for threshold in thresholds:

        detector_name = conv_hist_file+'@'+str(threshold)
        folder_name = OUTPUT_FOLDER+detector_name+'/'

        if isdir(folder_name):
            print('skipping',folder_name)
            continue
        else:
            print('doing',folder_name)

        mkdir(folder_name)

        h = Hare(name=detector_name)
        h.status_per_conversation = status_per_conversation
        h.cut_off_value = threshold

        for conversation in conversations:
            h.add_conversation(conversation)

        per_player = []
        tp = []
        fp = []
        fbeta = {b:[] for b in BETA_VALUES}

        #Calculate metrics for this detector/threshold combi
        for utterance_index in range(CONVERSATION_LENGTH):

            state_per_player = {}

            for conversation_index in range(len(IDS_OF_CONVERSATIONS)):

                try:
                    current_status = h.status_per_conversation[conversation_index][utterance_index]
                except IndexError:
                    continue

                speakers = h.conversations[conversation_index].all_speakers

                for speaker in speakers:
                    speaker_alias = str(aliases_per_conversation[conversation_index][speaker])

                    if len(speaker_alias) < 2:
                        speaker_alias = '0' + speaker_alias

                    speaker_id = 'conv' + str(conversation_index) + '.' + speaker_alias
                    state_per_player[speaker_id] = current_status[speaker] >= threshold if speaker in current_status.keys() else False

            per_player.append(state_per_player)

            true, predicted = h.get_true_and_predicted_scores_at_utterance_index(utterance_index,categorize_predicted_scores=True)
            tp.append(true_positives(true,predicted))
            fp.append(false_positives(true,predicted))

            for b in BETA_VALUES:
                fbeta[b].append(fbeta_score(true,predicted,b))

        open(folder_name+'per_player.js','w').write('bool_per_player["'+conv_hist_file+'"]['+str(threshold)+'] = '+dumps(per_player))
        open(folder_name+'tp.js','w').write('tp["'+conv_hist_file+'"]['+str(threshold)+'] = '+dumps(tp))
        open(folder_name+'fp.js','w').write('fp["'+conv_hist_file+'"]['+str(threshold)+'] = '+dumps(fp))
        open(folder_name+'fbeta.js','w').write('fbeta["'+conv_hist_file+'"]['+str(threshold)+'] = '+dumps(fbeta))