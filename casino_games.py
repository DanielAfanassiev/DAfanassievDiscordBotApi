import copy

face_cards = {1:"Ace", 11: "Jack", 12: "Queen", 13: "King", 14: "Ace"}

class Card:
    def __init__(self,  value, suit):
        self.name = str(face_cards.get(value, value))
        self.value = value
        self.suit = suit

    def __str__(self):
        return f"{self.name} of {self.suit}"

class Deck:
    def __init__(self):
        self.cards = []
        for value in range(1,14):
            for suit in ['Hearts','Spades','Diamonds', 'Clubs']:
                self.cards.append(Card(face_cards.get(value, value), str(value), suit))

# myDeck = Deck()
# for card in myDeck.cards:
#     print(str(card.name) + " " + str(card.value) + " " + str(card.suit))

hand_rankings = {"Royal Flush": 1,
                 "Straight Flush": 2,
                 "Four of a Kind": 3,
                 "Full House": 4,
                 "Flush": 5,
                 "Straight": 6,
                 "Three of a Kind": 7,
                 "Two Pair": 8,
                 "Pair": 9,
                 "High Card": 10}

def get_hand_type(hand):
    hand_type = ""
    # Royal Flush

def is_straight(cards, length = 5):
    cards = sort_by_value(list(cards))
    if(cards[0].name == "Ace"):
        cards.append(Card(14, cards[0].suit))
    max_sequence = 0
    cur_sequence = 1
    max_straight_card = None
    previous_card = cards[0]
    for card in cards:
        if(not card == previous_card):
            if(card.value == previous_card.value + 1):
                cur_sequence += 1
            else:
                cur_sequence = 1
            if(cur_sequence >= max_sequence):
                max_sequence = cur_sequence
                max_straight_card = card
        previous_card = card

    return max_sequence >= length, max_straight_card.value

def is_flush(cards, length = 5):
    cards = sort_by_value(list(cards))
    suits_dict = {"Hearts": [], "Spades": [], "Diamonds": [], "Clubs": []}
    max_suit_dict = {}
    for card in cards:
        suits_dict[card.suit].append(card)
        if(not card.suit in max_suit_dict):
            max_suit_dict[card.suit] = card
        else:
            if(max_suit_dict[card.suit].value < card.value and cards[0].value != 1):
                max_suit_dict[card.suit] = card

    flush_suit = max(suits_dict, key=lambda suit: len(suits_dict[suit]))
    flush_size = len(suits_dict[flush_suit])
    return  flush_size >= length, flush_size, suits_dict[flush_suit]

def is_straight_flush(cards, length = 5):
    are_cards_flush, size, flush_cards = is_flush(cards, length)
    if(not are_cards_flush):
        return False
    are_cards_straight, max_straight_card = is_straight(flush_cards, length)

    return are_cards_straight, max_straight_card.value

def is_royal_flush(cards, length = 5):
    are_cards_straight_flush, max_sf_card = is_straight_flush(cards, length)
    return are_cards_straight_flush and max_sf_card.value == 14

def is_quads(cards):
    cards = sort_by_value(cards, True)
    cards_dict = make_cards_dict(cards)

    quad_val = -1
    for card_value in cards_dict:
        if len(cards_dict[card_value]) >= 4 and (card_value > quad_val or card_value == 1):
            quad_val = card_value
            if(quad_val == 1):
                quad_val = 14
                cards_dict[14] = cards_dict[1]
                cards_dict.pop(1)
                break
    if(quad_val != -1):
        cards_dict_copy = copy.deepcopy(cards_dict)
        cards_dict_copy.pop(quad_val)
        new_card_list = []
        for card_value in cards_dict_copy:
            for cards in cards_dict_copy[card_value]:
                new_card_list.append(cards)
        new_sorted_cards = sort_by_value(cards_dict_copy, True)
        kicker = new_sorted_cards[0]
        return True, cards_dict[quad_val].append(kicker)
    return False, None

def is_trips(cards):
    cards = sort_by_value(cards, True)
    cards_dict = make_cards_dict(cards)

    trips_val = -1
    for card_value in cards_dict:
        if len(cards_dict[card_value]) >= 3 and (card_value > trips_val or card_value == 1):
            trips_val = card_value
            if (trips_val == 1):
                trips_val = 14
                cards_dict[14] = cards_dict[1]
                break
    if (trips_val != -1):
        return True, cards_dict[trips_val]
    return False, None

def is_pair(cards):
    cards = sort_by_value(cards, True)
    cards_dict = make_cards_dict(cards)

    pair_val = -1
    for card_value in cards_dict:
        if len(cards_dict[card_value]) >= 2 and (card_value > pair_val or card_value == 1):
            pair_val = card_value
            if (pair_val == 1):
                pair_val = 14
                cards_dict[14] = cards_dict[1]
                break
    if (pair_val != -1):
        return True, cards_dict[pair_val]
    return False, None

def is_full_house(cards):
    are_trips, trips_cards = is_trips(cards)
    if(are_trips):
        for card in trips_cards:
            cards.remove(card)
        are_pair, pair_cards = is_pair(cards)
        if(are_pair):
            if(trips_cards[0].value == 1):
                trips_cards[0].value = 14
            if(pair_cards[0].value == 1):
                pair_cards[0].value = 14
            return True, trips_cards, pair_cards

    return False, None, None

def make_cards_dict(cards):
    cards_dict = {}
    for card in cards:
        if(not card.value in cards_dict):
            cards_dict[card.value] = []
        cards_dict[card.value].append(card)
    return cards_dict

def sort_by_value(cards, inverse = False):
    return sorted(cards, key=lambda card: card.value, reverse=inverse)

def get_hand_rank(cards):
    if(is_royal_flush(cards)):
        return "Royal Flush", []

    is_sf, sf_max_cards = is_straight_flush(cards)
    if(is_sf):
        return "Straight Flush", sf_max_cards

    is_qds, qds_max_card = is_quads(cards)
    if(is_qds):
        return "Four of a Kind", qds_max_card

    is_fh, three, two = is_full_house(cards)
    if(is_fh):
        return "Full House", [three, two]

    is_str8, max_str8_card = is_straight(cards)
    if(is_str8):
        return "Straight", [max_str8_card]

    is_trps, trps_max_card = is_trips(cards)
    if(is_trps):
        return "Three of a Kind", [trps_max_card]

    is_pr, pr_max_card = is_pair(cards)
    if(is_pr):
        return "Pair", [pr_max_card]

    sorted_cards = sort_by_value(cards)
    if(sorted_cards[0].value == 1):
        return "High Card", [sorted_cards[len(sorted_cards) - 1].value]
    return

royal_flush = [Card(13, "Hearts"), Card(12, "Hearts"),Card(10, "Hearts"),Card(11, "Hearts"),Card(1, "Hearts")]
low_straight_flush = [Card(4,"Hearts"),Card(2,"Hearts"),Card(1,"Hearts"),Card(3,"Hearts"),Card(5,"Hearts")]
double_quads = [Card(2, "Hearts"),Card(2, "Hearts"),Card(2, "Hearts"),Card(2, "Hearts"),Card(5,"Hearts"),Card(5,"Hearts"),Card(5,"Hearts"),Card(5,"Hearts")]
low_full_house = [Card(2, "Hearts"),Card(2, "Hearts"),Card(3, "Hearts"),Card(3, "Hearts"),Card(3, "Hearts")]
high_full_house = [Card(1, "Hearts"),Card(1, "Hearts"),Card(1, "Hearts"),Card(3, "Hearts"),Card(3, "Hearts")]

hand_to_check = high_full_house

is_hand_straight, max_straight_card = is_straight(hand_to_check)
is_hand_flush, flush_size, flush_cards = is_flush(hand_to_check)
is_hand_straight_flush, max_sf_card = is_straight_flush(hand_to_check)
is_hand_royal_flush = is_royal_flush(hand_to_check)
is_hand_quads, quad_cards = is_quads(hand_to_check)
is_full_house, three, two = is_full_house(hand_to_check)

if is_hand_straight:
    print("Is straight")
    print(max_straight_card)
else:
    print("Is not straight")

print()
if is_hand_flush:
    print("Is flush")
    print(flush_size)
    printable_flush_cards = []
    for card in flush_cards:
        printable_flush_cards.append(str(card))
    print(printable_flush_cards)
else:
    print("Is not flush")

print()
if is_hand_straight_flush:
    print("Is straight flush")
    print(max_straight_card)
else:
    print("Is not straight flush")

print()
if is_hand_royal_flush:
    print("Is royal flush")
else:
    print("Is not royal flush")

print()
if is_hand_quads:
    print("Is quads")
    print(quad_cards[0])
else:
    print("Is not quads")

print()
if is_full_house:
    print("Is full house")
    print(three[0].name + "s full of " + two[0].name + "s")
else:
    print("Is not full house")