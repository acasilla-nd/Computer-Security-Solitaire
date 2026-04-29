import pymem
import pymem.process

# Decodes the identify of a card
def decode_card(raw_id):
    
    # Check the 15th bit for the face up flag
    is_face_down = (raw_id & 0x8000) == 0
    
    # Get the card ID (the lower byte)
    card_id = raw_id & 0xFF
    
    ranks = ["Ace", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Jack", "Queen", "King"]
    #suits = {"Clubs", "Diamonds", "Hearts", "Spades"} # Alphabetical order based on our observations
    suits = {0:2, 1:1, 2:0, 3:3} # Map the suits to the proper indexes for the solver
    
    try:
        # Our formula: ID / 4 = Rank, ID % 4 = Suit
        rank = card_id // 4
        suit = card_id % 4
        suit = suits[suit]
        
    except IndexError:
        print(f"Warning: Unknown card ID {hex(card_id)}")
        return None, None, None
        
    return suit, rank, is_face_down

def translate_card(suit, rank, is_face_down):
    return 16*suit+rank+64*(is_face_down)

def main():
    process_name = "sol.exe"
    
    try:
        pm = pymem.Pymem(process_name)
    except pymem.exception.ProcessNotFound:
        print(f"Error: {process_name} not found")
        return None, None

    # Get the base address
    module = pymem.process.module_from_name(pm.process_handle, process_name)
    base_address = module.lpBaseOfDll

    # The static game object pointer address
    static_pointer_addr = base_address + 0xD01C
    
    try:
        # Read the heap address stored at 0100D01C
        master_obj_addr = pm.read_int(static_pointer_addr)
        
        if master_obj_addr == 0:
            print("Error: Game object is NULL. Please start a new game and try again")
            return None, None
            
        # Stack array starts at +0x6C from the Master Object
        tableau_base = master_obj_addr + 0x6C

        deck = []
        foundations = [[] for _ in range(4)]
        tableaus = [[] for _ in range(7)]
        
        for i in range(13):
            # Read the pointer to the specific pile object
            pile_ptr = pm.read_int(tableau_base + (i * 4))
            
            # Determine the pile type based on the index
            match i:
                case 0:
                    pile = deck
                case 1:
                    pile = deck
                case 2 | 3 | 4 | 5:
                    pile = foundations[i-2]
                case _:
                    pile = tableaus[i-6]
            
            if pile_ptr == 0:
                continue

            # Offset +0x1C is the card count
            card_count = pm.read_int(pile_ptr + 0x1C)
                        
            # Offset +0x24 is the start of the card array
            cards_start = pile_ptr + 0x24
            
            for j in range(card_count):
                # Read the 4-byte ID at the start of the 12-byte card struct
                raw_card = pm.read_int(cards_start + (j * 12))
                suit, rank, is_face_down = decode_card(raw_card)
                if suit is None:
                    continue
                if pile is deck:
                    is_face_down = False
                translated_card = translate_card(suit, rank, is_face_down)
                pile.append(translated_card)
        
        # print("deck =", deck)
        # print("piles =", tableaus)


    except Exception as e:
        print(f"Critical error during memory read: {e}")
    
    return deck, tableaus


if __name__ == "__main__":
    main()
