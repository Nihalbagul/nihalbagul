import json
import os
import sys
import re

# File paths
STATE_FILE = "state.json"
README_FILE = "README.md"

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "board": [" ", " ", " ", " ", " ", " ", " ", " ", " "],
        "turn": "X",
        "winner": None
    }

def save_state(state):
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)

def check_winner(board):
    lines = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8], # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8], # Columns
        [0, 4, 8], [2, 4, 6]             # Diagonals
    ]
    for line in lines:
        if board[line[0]] == board[line[1]] == board[line[2]] != " ":
            return board[line[0]]
    if " " not in board:
        return "Draw"
    return None

def bot_move(board):
    # Simple AI: try to win, block opponent, or take center/corners
    lines = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8],
        [0, 3, 6], [1, 4, 7], [2, 5, 8],
        [0, 4, 8], [2, 4, 6]
    ]
    # 1. Try to win
    for line in lines:
        vals = [board[i] for i in line]
        if vals.count("O") == 2 and vals.count(" ") == 1:
            return line[vals.index(" ")]
    # 2. Block X
    for line in lines:
        vals = [board[i] for i in line]
        if vals.count("X") == 2 and vals.count(" ") == 1:
            return line[vals.index(" ")]
    # 3. Take center
    if board[4] == " ":
        return 4
    # 4. Take corners
    for corner in [0, 2, 6, 8]:
        if board[corner] == " ":
            return corner
    # 5. Take any empty cell
    for i in range(9):
        if board[i] == " ":
            return i
    return -1

def reset_game():
    return {
        "board": [" ", " ", " ", " ", " ", " ", " ", " ", " "],
        "turn": "X",
        "winner": None
    }

def update_readme(board, winner):
    with open(README_FILE, 'r', encoding='utf-8') as f:
        content = f.read()

    repo_url = "https://github.com/nihalbagul/nihalbagul"
    
    table = []
    table.append('<div align="center">')
    table.append('')
    table.append('<h3>🎮 Play Tic-Tac-Toe</h3>')
    
    if winner:
        if winner == "Draw":
            table.append("<h4>It's a Draw! 🤝</h4>")
        else:
            table.append(f"<h4>Winner: {winner == 'X' and 'You' or 'Antigravity Bot'}! {'🎉' if winner == 'X' else '🤖'}</h4>")
        table.append(f'<p><a href="{repo_url}/issues/new?title=ttt_reset&body=Click+Submit+New+Issue+to+restart+the+game!">🔄 <b>Play Again</b></a></p>')
    else:
        table.append("<h4>Your Turn (Play as X)</h4>")
        table.append("<p>Click any empty square below to make a move!</p>")
    
    table.append('<table style="border-collapse: collapse; text-align: center; font-size: 24px; font-weight: bold;">')
    for r in range(3):
        table.append('  <tr>')
        for c in range(3):
            idx = r * 3 + c
            val = board[idx]
            if val == "X":
                table.append('    <td width="60" height="60" style="border: 2px solid #414868; color: #f7768e; text-align: center;">❌</td>')
            elif val == "O":
                table.append('    <td width="60" height="60" style="border: 2px solid #414868; color: #7aa2f7; text-align: center;">⭕</td>')
            else:
                if winner:
                    table.append('    <td width="60" height="60" style="border: 2px solid #414868;">&nbsp;</td>')
                else:
                    move_url = f"{repo_url}/issues/new?title=ttt_move_{r}_{c}&body=Click+Submit+New+Issue+to+make+your+move+at+({r},{c})!"
                    table.append(f'    <td width="60" height="60" style="border: 2px solid #414868; text-align: center;"><a href="{move_url}">&nbsp;&nbsp;&nbsp;&nbsp;</a></td>')
        table.append('  </tr>')
    table.append('</table>')
    table.append('')
    table.append('</div>')
    
    board_str = "\n".join(table)
    
    pattern = r"<!--START_SECTION:tictactoe-->[\s\S]*<!--END_SECTION:tictactoe-->"
    replacement = f"<!--START_SECTION:tictactoe-->\n{board_str}\n<!--END_SECTION:tictactoe-->"
    
    new_content = re.sub(pattern, replacement, content)
    with open(README_FILE, 'w', encoding='utf-8') as f:
        f.write(new_content)

def main():
    if len(sys.argv) < 2:
        return
    
    issue_title = sys.argv[1].strip()
    
    state = load_state()
    
    if issue_title == "ttt_reset":
        state = reset_game()
        save_state(state)
        update_readme(state["board"], state["winner"])
        print("Game reset!")
        return

    match = re.match(r"ttt_move_(\d)_(\d)", issue_title)
    if not match:
        print("Invalid issue title")
        return
        
    r = int(match.group(1))
    c = int(match.group(2))
    idx = r * 3 + c
    
    if state["winner"] is not None:
        print("Game already ended")
        return
        
    if state["board"][idx] != " ":
        print("Cell already occupied")
        return
        
    # Player move
    state["board"][idx] = "X"
    winner = check_winner(state["board"])
    if winner:
        state["winner"] = winner
        save_state(state)
        update_readme(state["board"], state["winner"])
        print(f"Game over. Winner: {winner}")
        return
        
    # Bot move
    bot_idx = bot_move(state["board"])
    if bot_idx != -1:
        state["board"][bot_idx] = "O"
        winner = check_winner(state["board"])
        if winner:
            state["winner"] = winner
            
    save_state(state)
    update_readme(state["board"], state["winner"])
    print("Move processed!")

if __name__ == "__main__":
    main()
