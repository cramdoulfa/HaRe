from random import choice
from numpy import array
from sklearn.model_selection import train_test_split

#Generating the task

SEQUENCE_LENGTH = 10
NR_OF_INSTANCES_PER_GROUP = 100
DICTIONARY_SIZE = 20

#Generate sequences where casing is not important
word_instances_lexical = []
case_instances_lexical = []
target_lexical = []

for i in range(NR_OF_INSTANCES_PER_GROUP):
    word_instances_lexical.append([choice(range(DICTIONARY_SIZE-3)) for j in range(SEQUENCE_LENGTH)])
    case_instances_lexical.append([[choice([0,1])] for j in range(SEQUENCE_LENGTH)])
    target_lexical.append(0)

for i in range(NR_OF_INSTANCES_PER_GROUP):
    word_instances_lexical.append([choice(range(DICTIONARY_SIZE-3)) for j in range(SEQUENCE_LENGTH)])

    #Add predictor words
    word_instances_lexical[-1][choice(range(SEQUENCE_LENGTH))] = choice(range(DICTIONARY_SIZE-3,DICTIONARY_SIZE))

    case_instances_lexical.append([[choice([0,1])] for j in range(SEQUENCE_LENGTH)])
    target_lexical.append(1)

#Generate sequences where casing is the predictor
word_instances_casing = []
case_instances_casing = []
target_casing = []

for i in range(NR_OF_INSTANCES_PER_GROUP):
    word_instances_casing.append([choice(range(DICTIONARY_SIZE)) for j in range(SEQUENCE_LENGTH)])
    case_instances_casing.append([[0] for j in range(SEQUENCE_LENGTH)])
    target_casing.append(0)

for i in range(NR_OF_INSTANCES_PER_GROUP):
    word_instances_casing.append([choice(range(DICTIONARY_SIZE)) for j in range(SEQUENCE_LENGTH)])
    case_instances_casing.append([[choice([0,1])] for j in range(SEQUENCE_LENGTH)])
    target_casing.append(1)

#Generate sequences where a word is the predictor only when capitalized
word_instances_combined = []
case_instances_combined = []
target_combined = []

for i in range(NR_OF_INSTANCES_PER_GROUP):
    word_instances_combined.append([choice(range(DICTIONARY_SIZE-3)) for j in range(SEQUENCE_LENGTH)])
    case_instances_combined.append([[choice([0,1])] for j in range(SEQUENCE_LENGTH)])
    target_casing.append(0)

    #Add predictor words
    predictor_position = choice(range(SEQUENCE_LENGTH))
    word_instances_combined[-1][predictor_position] = choice(range(DICTIONARY_SIZE-3,DICTIONARY_SIZE))
    case_instances_combined[-1][predictor_position] = [0]

for i in range(NR_OF_INSTANCES_PER_GROUP):
    word_instances_combined.append([choice(range(DICTIONARY_SIZE-3)) for j in range(SEQUENCE_LENGTH)])
    case_instances_combined.append([[choice([0,1])] for j in range(SEQUENCE_LENGTH)])
    target_casing.append(1)

    # Add predictor words
    predictor_position = choice(range(SEQUENCE_LENGTH))
    word_instances_combined[-1][predictor_position] = choice(range(DICTIONARY_SIZE-3,DICTIONARY_SIZE))
    case_instances_combined[-1][predictor_position] = [1]

#Setting up the network
from tensorflow.keras.models import Model, Sequential
from tensorflow.keras.layers import Embedding, Bidirectional, GRU, GlobalMaxPool1D, Dense, Input, dot, concatenate
from tensorflow.keras.optimizers import Adam

word_input = Input(shape=(SEQUENCE_LENGTH,))
word_layer = Embedding(DICTIONARY_SIZE,SEQUENCE_LENGTH)(word_input)
word_model = Model(inputs=word_input, outputs=word_layer)

casing_input = Input(shape=(SEQUENCE_LENGTH,1))
casing_model = Model(inputs=casing_input, outputs=casing_input)

combined = concatenate([word_model.output, casing_model.output])

layers = Bidirectional(GRU(16, activation='tanh', return_sequences=True))(combined)
layers = Bidirectional(GRU(16, activation='tanh', return_sequences=True))(layers)
layers = GlobalMaxPool1D()(layers)

layers = Dense(256)(layers)
layers = Dense(256)(layers)
layers = Dense(1, activation='sigmoid')(layers)
model = Model([word_model.input, casing_model.input],layers)

# Compile the model
optimizer: Adam = Adam()
model.compile(optimizer=optimizer, loss='binary_crossentropy', metrics=['acc'])

#Give the data
model.fit([array(word_instances_combined),array(case_instances_combined)],target_lexical,validation_split=0.1,epochs=100)


