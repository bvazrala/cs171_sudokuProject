import SudokuBoard
import Variable
import Domain
import Trail
import Constraint
import ConstraintNetwork
import time
import random
import json
from collections import defaultdict

class BTSolver:

    # ==================================================================
    # Constructors
    # ==================================================================

    def __init__ ( self, gb, trail, val_sh, var_sh, cc ):
        self.network = ConstraintNetwork.ConstraintNetwork(gb)
        self.hassolution = False
        self.gameboard = gb
        self.trail = trail

        self.varHeuristics = var_sh
        self.valHeuristics = val_sh
        self.cChecks = cc

    # ==================================================================
    # Consistency Checks
    # ==================================================================

    # Basic consistency check, no propagation done
    def assignmentsCheck ( self ):
        for c in self.network.getConstraints():
            if not c.isConsistent():
                return False
        return True

    """
        Part 1 TODO: Implement the Forward Checking Heuristic

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        Note: remember to trail.push variables before you assign them
        Return: a tuple of a dictionary and a bool. The dictionary contains all MODIFIED variables, mapped to their MODIFIED domain.
                The bool is true if assignment is consistent, false otherwise.
    """
    def forwardChecking ( self ):
        modifiedVars = dict()

        # Look at all assigned variables
        for v in self.network.variables:
            if v.isAssigned():
                assignedVal = v.getAssignment()

                # Eliminate this value from all neighbors' domains
                for neighbor in self.network.getNeighborsOfVariable(v):
                    if neighbor.isAssigned():
                        # If a neighbor has the same assignment, inconsistency
                        if neighbor.getAssignment() == assignedVal:
                            return (modifiedVars, False)
                        continue

                    if neighbor.getDomain().contains(assignedVal):
                        self.trail.push(neighbor)
                        neighbor.removeValueFromDomain(assignedVal)
                        modifiedVars[neighbor] = neighbor.getDomain()

                        # If domain is empty after removal, inconsistency
                        if neighbor.getDomain().size() == 0:
                            return (modifiedVars, False)

                        # If domain is reduced to 1, assign it
                        if neighbor.getDomain().size() == 1:
                            neighbor.assignValue(neighbor.getDomain().values[0])

        return (modifiedVars, True)

    # =================================================================
    # Arc Consistency
    # =================================================================
    def arcConsistency( self ):
        assignedVars = []
        for c in self.network.constraints:
            for v in c.vars:
                if v.isAssigned():
                    assignedVars.append(v)
        while len(assignedVars) != 0:
            av = assignedVars.pop(0)
            for neighbor in self.network.getNeighborsOfVariable(av):
                if neighbor.isChangeable and not neighbor.isAssigned() and neighbor.getDomain().contains(av.getAssignment()):
                    neighbor.removeValueFromDomain(av.getAssignment())
                    if neighbor.domain.size() == 1:
                        neighbor.assignValue(neighbor.domain.values[0])
                        assignedVars.append(neighbor)

    
    """
        Part 2 TODO: Implement both of Norvig's Heuristics

        This function will do both Constraint Propagation and check
        the consistency of the network

        (1) If a variable is assigned then eliminate that value from
            the square's neighbors.

        (2) If a constraint has only one possible place for a value
            then put the value there.

        Note: remember to trail.push variables before you assign them
        Return: a pair of a dictionary and a bool. The dictionary contains all variables 
                that were ASSIGNED during the whole NorvigCheck propagation, and mapped to the values that they were assigned.
                The bool is true if assignment is consistent, false otherwise.
    """
    def norvigCheck ( self ):
        assignedVars = dict()

        # --- Part (1): Forward checking (eliminate from neighbors) ---
        for v in self.network.variables:
            if v.isAssigned():
                assignedVal = v.getAssignment()
                for neighbor in self.network.getNeighborsOfVariable(v):
                    if neighbor.isAssigned():
                        if neighbor.getAssignment() == assignedVal:
                            return (assignedVars, False)
                        continue

                    if neighbor.getDomain().contains(assignedVal):
                        self.trail.push(neighbor)
                        neighbor.removeValueFromDomain(assignedVal)

                        if neighbor.getDomain().size() == 0:
                            return (assignedVars, False)

                        if neighbor.getDomain().size() == 1:
                            neighbor.assignValue(neighbor.getDomain().values[0])
                            assignedVars[neighbor] = neighbor.getAssignment()

        # --- Part (2): If a constraint has only one place for a value, assign it ---
        for c in self.network.getConstraints():
            # For each possible value in the Sudoku
            for val in range(1, self.gameboard.N + 1):
                # Find all unassigned variables in this constraint that can hold this value
                possibleVars = []
                alreadyAssigned = False

                for var in c.vars:
                    if var.isAssigned() and var.getAssignment() == val:
                        alreadyAssigned = True
                        break
                    if not var.isAssigned() and var.getDomain().contains(val):
                        possibleVars.append(var)

                if alreadyAssigned:
                    continue

                # If no variable can hold this value, inconsistency
                if len(possibleVars) == 0:
                    return (assignedVars, False)

                # If exactly one variable can hold this value, assign it
                if len(possibleVars) == 1:
                    target = possibleVars[0]
                    if not target.isAssigned():
                        self.trail.push(target)
                        target.assignValue(val)
                        assignedVars[target] = val

        return (assignedVars, True)

    """
         Optional TODO: Implement your own advanced Constraint Propagation

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournCC ( self ):
        return False

    # ==================================================================
    # Variable Selectors
    # ==================================================================

    # Basic variable selector, returns first unassigned variable
    def getfirstUnassignedVariable ( self ):
        for v in self.network.variables:
            if not v.isAssigned():
                return v

        # Everything is assigned
        return None

    """
        Part 1 TODO: Implement the Minimum Remaining Value Heuristic

        Return: The unassigned variable with the smallest domain
    """
    def getMRV ( self ):
        bestVar = None
        minDomainSize = float('inf')

        for v in self.network.variables:
            if not v.isAssigned():
                if v.getDomain().size() < minDomainSize:
                    minDomainSize = v.getDomain().size()
                    bestVar = v

        return bestVar
    
    def getDegree ( self ):
        """
        Degree heuristic (DEG):
        Pick the unassigned variable that has the most unassigned neighbors.
        """
        bestVar = None
        bestDegree = -1

        for v in self.network.variables:
            if v.isAssigned():
                continue

            degree = 0
            for n in self.network.getNeighborsOfVariable(v):
                if not n.isAssigned():
                    degree += 1

            if degree > bestDegree:
                bestDegree = degree
                bestVar = v
            return bestVar

    """
        Part 2 TODO: Implement the Minimum Remaining Value Heuristic
                       with Degree Heuristic as a Tie Breaker

        Return: The unassigned variable with the smallest domain and affecting the  most unassigned neighbors.
                If there are multiple variables that have the same smallest domain with the same number of unassigned neighbors, add them to the list of Variables.
                If there is only one variable, return the list of size 1 containing that variable.
    """
    def MRVwithTieBreaker ( self ):
        # Step 1: Find the minimum domain size among unassigned variables
        minDomainSize = float('inf')
        for v in self.network.variables:
            if not v.isAssigned():
                if v.getDomain().size() < minDomainSize:
                    minDomainSize = v.getDomain().size()

        if minDomainSize == float('inf'):
            return [None]

        # Step 2: Collect all unassigned variables with that min domain size
        mrvVars = []
        for v in self.network.variables:
            if not v.isAssigned() and v.getDomain().size() == minDomainSize:
                mrvVars.append(v)

        if len(mrvVars) == 1:
            return mrvVars

        # Step 3: Among those, find the one(s) with the most unassigned neighbors (degree heuristic)
        maxDegree = -1
        for v in mrvVars:
            degree = 0
            for neighbor in self.network.getNeighborsOfVariable(v):
                if not neighbor.isAssigned():
                    degree += 1
            if degree > maxDegree:
                maxDegree = degree

        result = []
        for v in mrvVars:
            degree = 0
            for neighbor in self.network.getNeighborsOfVariable(v):
                if not neighbor.isAssigned():
                    degree += 1
            if degree == maxDegree:
                result.append(v)

        return result

    """
         Optional TODO: Implement your own advanced Variable Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVar ( self ):
        return None

    # ==================================================================
    # Value Selectors
    # ==================================================================

    # Default Value Ordering
    def getValuesInOrder ( self, v ):
        values = v.domain.values
        return sorted( values )

    """
        Part 1 TODO: Implement the Least Constraining Value Heuristic

        The Least constraining value is the one that will knock the least
        values out of it's neighbors domain.

        Return: A list of v's domain sorted by the LCV heuristic
                The LCV is first and the MCV is last
    """
    def getValuesLCVOrder ( self, v ):
        valScores = []

        for val in v.getDomain().values:
            count = 0
            # Count how many values this would eliminate from neighbors
            for neighbor in self.network.getNeighborsOfVariable(v):
                if not neighbor.isAssigned() and neighbor.getDomain().contains(val):
                    count += 1
            valScores.append((val, count))

        # Sort by count ascending (least constraining = eliminates fewest values first)
        valScores.sort(key=lambda x: x[1])
        return [pair[0] for pair in valScores]

    """
         Optional TODO: Implement your own advanced Value Heuristic

         Completing the three tourn heuristic will automatically enter
         your program into a tournament.
     """
    def getTournVal ( self, v ):
        return None

    # ==================================================================
    # Engine Functions
    # ==================================================================

    def solve ( self, time_left=600):
        if time_left <= 60:
            return -1

        start_time = time.time()
        if self.hassolution:
            return 0

        # Variable Selection
        v = self.selectNextVariable()

        # check if the assigment is complete
        if ( v == None ):
            # Success
            self.hassolution = True
            return 0

        # Attempt to assign a value
        for i in self.getNextValues( v ):

            # Store place in trail and push variable's state on trail
            self.trail.placeTrailMarker()
            self.trail.push( v )

            # Assign the value
            v.assignValue( i )

            # Propagate constraints, check consistency, recur
            if self.checkConsistency():
                elapsed_time = time.time() - start_time 
                new_start_time = time_left - elapsed_time
                if self.solve(time_left=new_start_time) == -1:
                    return -1
                
            # If this assignment succeeded, return
            if self.hassolution:
                return 0

            # Otherwise backtrack
            self.trail.undo()
        
        return 0

    def checkConsistency ( self ):
        if self.cChecks == "forwardChecking":
            return self.forwardChecking()[1]

        if self.cChecks == "norvigCheck":
            return self.norvigCheck()[1]

        if self.cChecks == "tournCC":
            return self.getTournCC()

        else:
            return self.assignmentsCheck()

    def selectNextVariable ( self ):
        if self.varHeuristics == "MinimumRemainingValue":
            return self.getMRV()

        if self.varHeuristics == "MRVwithTieBreaker":
            return self.MRVwithTieBreaker()[0]

        if self.varHeuristics == "Degree":
            return self.getDegree()

        if self.varHeuristics == "tournVar":
            return self.getTournVar()

        else:
            return self.getfirstUnassignedVariable()

    def getNextValues ( self, v ):
        if self.valHeuristics == "LeastConstrainingValue":
            return self.getValuesLCVOrder( v )

        if self.valHeuristics == "tournVal":
            return self.getTournVal( v )

        else:
            return self.getValuesInOrder( v )

    def getSolution ( self ):
        return self.network.toSudokuBoard(self.gameboard.p, self.gameboard.q)

    # ==================================================================
    # Testing Functions - Minimal AI Tests (Forward Checking Only)
    # ==================================================================

    @staticmethod
    def run_minimal_ai_tests():
        """
        Run 60 Minimal AI tests: 15 tests each for 9x9, 12x12, 16x16, 25x25
        All tests use Forward Checking (FC) only
        """
        print("\n" + "="*80)
        print("MINIMAL AI TESTS - Forward Checking Only")
        print("="*80)
        
        minimal_results = {
            '9x9': {'solved': 0, 'total_backtracks': 0, 'trials': 15},
            '12x12': {'solved': 0, 'total_backtracks': 0, 'trials': 15},
            '16x16': {'solved': 0, 'total_backtracks': 0, 'trials': 15},
            '25x25': {'solved': 0, 'total_backtracks': 0, 'trials': 15}
        }
        
        board_sizes = {
            '9x9': (3, 3),
            '12x12': (3, 4),
            '16x16': (4, 4),
            '25x25': (5, 5)
        }
        
        # Test each difficulty level
        for difficulty, (p, q) in board_sizes.items():
            print(f"\nTesting {difficulty} boards ({p}x{q})...")
            
            for test_num in range(15):
                # Reset Trail counters for each test
                Trail.Trail.numPush = 0
                Trail.Trail.numUndo = 0
                
                # Generate board
                board = SudokuBoard.SudokuBoard(p, q, 7)
                trail = Trail.Trail()
                
                # Create solver with FC only
                solver = BTSolver(board, trail, val_sh="", var_sh="", cc="forwardChecking")
                solver.checkConsistency()
                
                # Solve
                solver.solve()
                
                # Record results
                if solver.hassolution:
                    minimal_results[difficulty]['solved'] += 1
                    backtracks = trail.getUndoCount()
                    minimal_results[difficulty]['total_backtracks'] += backtracks
                    print(f"  Test {test_num+1}/15: SOLVED (backtracks: {backtracks})")
                else:
                    print(f"  Test {test_num+1}/15: FAILED")
        
        # Print summary table
        print("\n" + "="*80)
        print("MINIMAL AI TEST RESULTS")
        print("="*80)
        print(f"{'Board Size':<20} {'Sample Size (n)':<20} {'Boards Solved':<20} {'Avg # Backtracks':<20}")
        print("-"*80)
        
        total_solved = 0
        total_backtracks = 0
        total_trials = 0
        
        for difficulty in ['9x9', '12x12', '16x16', '25x25']:
            result = minimal_results[difficulty]
            solved = result['solved']
            trials = result['trials']
            avg_backtracks = result['total_backtracks'] / solved if solved > 0 else 0
            
            print(f"{difficulty:<20} {trials:<20} {solved:<20} {avg_backtracks:<20.2f}")
            
            total_solved += solved
            total_backtracks += result['total_backtracks']
            total_trials += trials
        
        avg_total_backtracks = total_backtracks / total_solved if total_solved > 0 else 0
        print("-"*80)
        print(f"{'Total Summary':<20} {total_trials:<20} {total_solved:<20} {avg_total_backtracks:<20.2f}")
        print("="*80)
        
        return minimal_results

    # ==================================================================
    # Testing Functions - Final AI Tests (Optimized Combinations)
    # ==================================================================

    @staticmethod
    def run_final_ai_tests():
        """
        Run 60 Final AI tests: 15 tests per difficulty level with optimized algorithm combinations
        """
        print("\n" + "="*80)
        print("FINAL AI TESTS - Optimized Algorithm Combinations")
        print("="*80)
        
        # Define algorithm combinations for each difficulty level
        # Format: (var_heuristic, val_heuristic, constraint_check)
        algorithm_combinations = {
            'easy': [
                ("", "", "forwardChecking"),           # 1-3: Basic FC
                ("", "", "forwardChecking"),
                ("", "", "forwardChecking"),
                ("MinimumRemainingValue", "", "forwardChecking"),  # 4-6: MRV + FC
                ("MinimumRemainingValue", "", "forwardChecking"),
                ("MinimumRemainingValue", "", "forwardChecking"),
                ("MRVwithTieBreaker", "LeastConstrainingValue", "forwardChecking"),  # 7-9: MRV+Degree + LCV + FC
                ("MRVwithTieBreaker", "LeastConstrainingValue", "forwardChecking"),
                ("MRVwithTieBreaker", "LeastConstrainingValue", "forwardChecking"),
                ("", "", "norvigCheck"),               # 10-12: Basic + Norvig
                ("", "", "norvigCheck"),
                ("", "", "norvigCheck"),
                ("MRVwithTieBreaker", "LeastConstrainingValue", "norvigCheck"),  # 13-15: MRV+Degree + LCV + Norvig
                ("MRVwithTieBreaker", "LeastConstrainingValue", "norvigCheck"),
                ("MRVwithTieBreaker", "LeastConstrainingValue", "norvigCheck"),
            ],
            'intermediate': [
                ("", "", "forwardChecking"),           # 1-3: Basic FC
                ("", "", "forwardChecking"),
                ("", "", "forwardChecking"),
                ("MinimumRemainingValue", "", "forwardChecking"),  # 4-6: MRV + FC
                ("MinimumRemainingValue", "", "forwardChecking"),
                ("MinimumRemainingValue", "", "forwardChecking"),
                ("MRVwithTieBreaker", "LeastConstrainingValue", "forwardChecking"),  # 7-9: MRV+Degree + LCV + FC
                ("MRVwithTieBreaker", "LeastConstrainingValue", "forwardChecking"),
                ("MRVwithTieBreaker", "LeastConstrainingValue", "forwardChecking"),
                ("MRVwithTieBreaker", "LeastConstrainingValue", "norvigCheck"),  # 10-12: MRV+Degree + LCV + Norvig
                ("MRVwithTieBreaker", "LeastConstrainingValue", "norvigCheck"),
                ("MRVwithTieBreaker", "LeastConstrainingValue", "norvigCheck"),
                ("", "", "norvigCheck"),               # 13-15: Basic + Norvig
                ("", "", "norvigCheck"),
                ("", "", "norvigCheck"),
            ],
            'hard': [
                ("MRVwithTieBreaker", "LeastConstrainingValue", "norvigCheck"),  # 1-3: MRV+Degree + LCV + Norvig
                ("MRVwithTieBreaker", "LeastConstrainingValue", "norvigCheck"),
                ("MRVwithTieBreaker", "LeastConstrainingValue", "norvigCheck"),
                ("MinimumRemainingValue", "", "norvigCheck"),  # 4-6: MRV + Norvig
                ("MinimumRemainingValue", "", "norvigCheck"),
                ("MinimumRemainingValue", "", "norvigCheck"),
                ("MRVwithTieBreaker", "LeastConstrainingValue", "forwardChecking"),  # 7-9: MRV+Degree + LCV + FC
                ("MRVwithTieBreaker", "LeastConstrainingValue", "forwardChecking"),
                ("MRVwithTieBreaker", "LeastConstrainingValue", "forwardChecking"),
                ("MRVwithTieBreaker", "", "norvigCheck"),  # 10-12: MRV+Degree + Norvig
                ("MRVwithTieBreaker", "", "norvigCheck"),
                ("MRVwithTieBreaker", "", "norvigCheck"),
                ("", "", "norvigCheck"),               # 13-15: Basic + Norvig
                ("", "", "norvigCheck"),
                ("", "", "norvigCheck"),
            ],
            'expert': [
                ("MRVwithTieBreaker", "LeastConstrainingValue", "norvigCheck"),  # 1-3: MRV+Degree + LCV + Norvig
                ("MRVwithTieBreaker", "LeastConstrainingValue", "norvigCheck"),
                ("MRVwithTieBreaker", "LeastConstrainingValue", "norvigCheck"),
                ("MRVwithTieBreaker", "", "norvigCheck"),  # 4-6: MRV+Degree + Norvig
                ("MRVwithTieBreaker", "", "norvigCheck"),
                ("MRVwithTieBreaker", "", "norvigCheck"),
                ("MRVwithTieBreaker", "LeastConstrainingValue", "forwardChecking"),  # 7-9: MRV+Degree + LCV + FC
                ("MRVwithTieBreaker", "LeastConstrainingValue", "forwardChecking"),
                ("MRVwithTieBreaker", "LeastConstrainingValue", "forwardChecking"),
                ("MinimumRemainingValue", "LeastConstrainingValue", "norvigCheck"),  # 10-12: MRV + LCV + Norvig
                ("MinimumRemainingValue", "LeastConstrainingValue", "norvigCheck"),
                ("MinimumRemainingValue", "LeastConstrainingValue", "norvigCheck"),
                ("MinimumRemainingValue", "", "norvigCheck"),  # 13-15: MRV + Norvig
                ("MinimumRemainingValue", "", "norvigCheck"),
                ("MinimumRemainingValue", "", "norvigCheck"),
            ]
        }
        
        board_sizes = {
            'easy': (3, 3),
            'intermediate': (3, 4),
            'hard': (4, 4),
            'expert': (5, 5)
        }
        
        final_results = {
            'easy': {'solved': 0, 'total_backtracks': 0, 'trials': 15},
            'intermediate': {'solved': 0, 'total_backtracks': 0, 'trials': 15},
            'hard': {'solved': 0, 'total_backtracks': 0, 'trials': 15},
            'expert': {'solved': 0, 'total_backtracks': 0, 'trials': 15}
        }
        
        # Test each difficulty level
        for difficulty in ['easy', 'intermediate', 'hard', 'expert']:
            p, q = board_sizes[difficulty]
            combos = algorithm_combinations[difficulty]
            
            print(f"\nTesting {difficulty} boards ({p}x{q})...")
            
            for test_num in range(15):
                # Reset Trail counters for each test
                Trail.Trail.numPush = 0
                Trail.Trail.numUndo = 0
                
                # Get algorithm combination for this test
                var_heur, val_heur, constraint = combos[test_num]
                
                # Generate board
                board = SudokuBoard.SudokuBoard(p, q, 7)
                trail = Trail.Trail()
                
                # Create solver with selected combination
                solver = BTSolver(board, trail, val_sh=val_heur, var_sh=var_heur, cc=constraint)
                solver.checkConsistency()
                
                # Solve
                solver.solve()
                
                # Determine combo name for display
                combo_name = f"{var_heur if var_heur else 'First'} + {val_heur if val_heur else 'InOrder'} + {constraint[:2].upper()}"
                
                # Record results
                if solver.hassolution:
                    final_results[difficulty]['solved'] += 1
                    backtracks = trail.getUndoCount()
                    final_results[difficulty]['total_backtracks'] += backtracks
                    print(f"  Test {test_num+1}/15 ({combo_name}): SOLVED (backtracks: {backtracks})")
                else:
                    print(f"  Test {test_num+1}/15 ({combo_name}): FAILED")
        
        # Print summary table
        print("\n" + "="*80)
        print("FINAL AI TEST RESULTS")
        print("="*80)
        print(f"{'Board Size':<20} {'Sample Size (n)':<20} {'Boards Solved':<20} {'Avg # Backtracks':<20}")
        print("-"*80)
        
        total_solved = 0
        total_backtracks = 0
        total_trials = 0
        
        for difficulty in ['easy', 'intermediate', 'hard', 'expert']:
            result = final_results[difficulty]
            solved = result['solved']
            trials = result['trials']
            avg_backtracks = result['total_backtracks'] / solved if solved > 0 else 0
            
            print(f"{difficulty:<20} {trials:<20} {solved:<20} {avg_backtracks:<20.2f}")
            
            total_solved += solved
            total_backtracks += result['total_backtracks']
            total_trials += trials
        
        avg_total_backtracks = total_backtracks / total_solved if total_solved > 0 else 0
        print("-"*80)
        print(f"{'Total Summary':<20} {total_trials:<20} {total_solved:<20} {avg_total_backtracks:<20.2f}")
        print("="*80)
        
        return final_results

    # ==================================================================
    # Main Testing Entry Point
    # ==================================================================

    @staticmethod
    def run_all_tests():
        """
        Run both Minimal AI and Final AI tests sequentially
        """
        print("\n\n")
        print("#"*80)
        print("# STARTING COMPREHENSIVE AI TESTING SUITE")
        print("#"*80)
        
        # Run Minimal Tests
        minimal_results = BTSolver.run_minimal_ai_tests()
        
        # Run Final Tests
        final_results = BTSolver.run_final_ai_tests()
        
        print("\n" + "#"*80)
        print("# ALL TESTING COMPLETE")
        print("#"*80 + "\n")
        
        return minimal_results, final_results
    