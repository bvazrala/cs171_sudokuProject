import streamlit as st
import sys
import os
import time

# Add the solver source to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Sudoku_Python_Shell", "src"))

import SudokuBoard
import BTSolver
import Trail

st.set_page_config(page_title="Sudoku AI Solver", page_icon="🔢", layout="centered")

st.title("Sudoku AI Solver")
st.caption("CS 171 — Backtracking solver with CSP heuristics")

# --- Sidebar: algorithm config ---
st.sidebar.header("Algorithm Settings")

var_heuristic = st.sidebar.selectbox(
    "Variable Selection",
    options=["None", "MRV", "MAD"],
    help="MRV = Minimum Remaining Value; MAD = MRV with Degree tiebreaker",
)

val_heuristic = st.sidebar.selectbox(
    "Value Ordering",
    options=["None", "LCV"],
    help="LCV = Least Constraining Value",
)

consistency = st.sidebar.selectbox(
    "Consistency Check",
    options=["None", "Forward Checking", "Norvig Check"],
    help="Forward Checking propagates constraints; Norvig Check also assigns hidden singles",
)

VAR_MAP = {"None": "", "MRV": "MinimumRemainingValue", "MAD": "MRVwithTieBreaker"}
VAL_MAP = {"None": "", "LCV": "LeastConstrainingValue"}
CC_MAP  = {"None": "", "Forward Checking": "forwardChecking", "Norvig Check": "norvigCheck"}

var_sh = VAR_MAP[var_heuristic]
val_sh = VAL_MAP[val_heuristic]
cc     = CC_MAP[consistency]

# --- Board input ---
st.header("Puzzle Input")

input_mode = st.radio("Input mode", ["Generate random puzzle", "Enter puzzle manually"], horizontal=True)

def parse_grid(text):
    """Parse a 9x9 grid from user text input (0 = empty)."""
    rows = []
    for line in text.strip().splitlines():
        row = []
        for token in line.split():
            try:
                row.append(int(token))
            except ValueError:
                row.append(0)
        if row:
            rows.append(row)
    if len(rows) != 9 or any(len(r) != 9 for r in rows):
        return None
    return rows

def board_to_grid(sudoku_board):
    return [row[:] for row in sudoku_board.board]

def render_grid(grid, solution_grid=None, p=3, q=3):
    """Render a sudoku grid as an HTML table."""
    N = p * q
    cell_size = 52

    html = f"""
    <style>
      .sudoku-table {{
        border-collapse: collapse;
        margin: 0 auto;
        font-family: monospace;
        font-size: 20px;
      }}
      .sudoku-table td {{
        width: {cell_size}px;
        height: {cell_size}px;
        text-align: center;
        vertical-align: middle;
        border: 1px solid #aaa;
      }}
      .sudoku-table td.thick-right  {{ border-right:  3px solid #333; }}
      .sudoku-table td.thick-bottom {{ border-bottom: 3px solid #333; }}
      .sudoku-table td.thick-right.thick-bottom {{ border-right: 3px solid #333; border-bottom: 3px solid #333; }}
      .clue    {{ color: #111; font-weight: bold; }}
      .solved  {{ color: #1a73e8; }}
      .empty   {{ color: #ccc; }}
    </style>
    <table class="sudoku-table">
    """

    for i in range(N):
        html += "<tr>"
        for j in range(N):
            val = grid[i][j]
            sol_val = solution_grid[i][j] if solution_grid else None

            classes = []
            if (j + 1) % q == 0 and j != N - 1:
                classes.append("thick-right")
            if (i + 1) % p == 0 and i != N - 1:
                classes.append("thick-bottom")

            cls_str = " ".join(classes)

            if val != 0:
                display = f'<span class="clue">{val}</span>'
            elif sol_val and sol_val != 0:
                display = f'<span class="solved">{sol_val}</span>'
            else:
                display = '<span class="empty">·</span>'

            html += f'<td class="{cls_str}">{display}</td>'
        html += "</tr>"

    html += "</table>"
    return html

# --- Puzzle state ---
if "puzzle_grid" not in st.session_state:
    st.session_state.puzzle_grid = None
if "solution_grid" not in st.session_state:
    st.session_state.solution_grid = None
if "stats" not in st.session_state:
    st.session_state.stats = None

# --- Input section ---
if input_mode == "Generate random puzzle":
    num_clues = st.slider("Number of clues", min_value=5, max_value=30, value=17)
    if st.button("Generate Puzzle"):
        board = SudokuBoard.SudokuBoard(3, 3, num_clues)
        st.session_state.puzzle_grid = board_to_grid(board)
        st.session_state.solution_grid = None
        st.session_state.stats = None

else:
    example = (
        "0 0 3 0 2 0 6 0 0\n"
        "9 0 0 3 0 5 0 0 1\n"
        "0 0 1 8 0 6 4 0 0\n"
        "0 0 8 1 0 2 9 0 0\n"
        "7 0 0 0 0 0 0 0 8\n"
        "0 0 6 7 0 8 2 0 0\n"
        "0 0 2 6 0 9 5 0 0\n"
        "8 0 0 2 0 3 0 0 9\n"
        "0 0 5 0 1 0 3 0 0"
    )
    puzzle_text = st.text_area(
        "Enter 9×9 puzzle (0 = empty, space-separated rows)",
        value=example,
        height=200,
    )
    if st.button("Load Puzzle"):
        parsed = parse_grid(puzzle_text)
        if parsed is None:
            st.error("Invalid input — please enter exactly 9 rows of 9 numbers.")
        else:
            st.session_state.puzzle_grid = parsed
            st.session_state.solution_grid = None
            st.session_state.stats = None

# --- Display puzzle ---
if st.session_state.puzzle_grid:
    st.subheader("Puzzle")
    st.markdown(
        render_grid(st.session_state.puzzle_grid, st.session_state.solution_grid),
        unsafe_allow_html=True,
    )
    st.markdown("&nbsp;", unsafe_allow_html=True)

    # --- Solve button ---
    if st.button("Solve", type="primary"):
        grid = st.session_state.puzzle_grid
        board = SudokuBoard.SudokuBoard(p=3, q=3, board=[row[:] for row in grid])

        trail = Trail.Trail()
        solver = BTSolver.BTSolver(board, trail, val_sh, var_sh, cc)

        start = time.time()
        if cc in ["forwardChecking", "norvigCheck"]:
            solver.checkConsistency()
        result = solver.solve()
        elapsed = time.time() - start

        if solver.hassolution:
            sol_board = solver.getSolution()
            st.session_state.solution_grid = board_to_grid(sol_board)
            st.session_state.stats = {
                "time": elapsed,
                "pushes": trail.getPushCount(),
                "backtracks": trail.getUndoCount(),
            }
        else:
            st.error("No solution found. Try a different puzzle or heuristic.")
            st.session_state.solution_grid = None
            st.session_state.stats = None
        st.rerun()

# --- Solution display ---
if st.session_state.solution_grid:
    st.subheader("Solution")
    st.markdown(
        render_grid(st.session_state.puzzle_grid, st.session_state.solution_grid),
        unsafe_allow_html=True,
    )
    st.markdown("&nbsp;", unsafe_allow_html=True)

    stats = st.session_state.stats
    c1, c2, c3 = st.columns(3)
    c1.metric("Solve Time", f"{stats['time']*1000:.1f} ms")
    c2.metric("Trail Pushes", stats["pushes"])
    c3.metric("Backtracks", stats["backtracks"])
