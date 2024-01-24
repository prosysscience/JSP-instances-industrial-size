#!/usr/bin/python
import sys
import clingo

from clingo import ast
from clingo import Function, Number
from clingodl import ClingoDLTheory
import json
import logging
import time


NUM_OF_TIME_WINDOWS = 30
MAX_TIMEOUT = 21600

class Application(clingo.Application):
    '''
    Application class similar to clingo-dl (excluding optimization).
    '''
    def __init__(self, name):
        self.__theory = ClingoDLTheory()
        self.program_name = name
        self.version = ".".join(str(x) for x in self.__theory.version())

    def __on_model(self, model):
        self.__theory.on_model(model)

    def register_options(self, options):
        self.__theory.register_options(options)

    def validate_options(self):
        self.__theory.validate_options()
        return True

    '''
    def print_model(self, model, printer):
        # print model
        symbols = model.symbols(shown=True)
        sys.stdout.write(" ".join(str(symbol) for symbol in sorted(symbols) if not self.__hidden(symbol)))
        sys.stdout.write('\n')

        # print assignment
        sys.stdout.write('Assignment:\n')
        symbols = model.symbols(theory=True)
        assignment = []
        for symbol in sorted(symbols):
            if symbol.match("dl", 2):
                assignment.append("{}={}".format(*symbol.arguments))
        sys.stdout.write(" ".join(assignment))
        sys.stdout.write('\n')

        sys.stdout.flush()
    '''

    def __on_statistics(self, step, accu):
        self.__theory.on_statistics(step, accu)

    def __hidden(self, symbol):
        return symbol.type == clingo.SymbolType.Function and symbol.name.startswith("__")


    # get the Time out per Time Window
    def get_TimeOut(self):
        return MAX_TIMEOUT/NUM_OF_TIME_WINDOWS
    # ************************************************

    # get the assignment of the operations in a string format to be sent as facts for the next Time Window
    def get_total_facts(self, assignment, i):
        start_time = ''
        to_join = []
        for name, value in assignment:
            if str(name) != 'bound':
                facts_format = 'startTime({},{},{}).'.format(name, value, i)
                to_join.append(facts_format)
            else:
                bound = int(value)
        start_time = ' '.join(to_join)
        return start_time, bound
    # ****************************************************************************************************

    # get the part that should be grounded and solved
    def step_to_ground(self, control, step):
        #print('Start Time : {} '.format(step), start_time)

        string = 'solutionTimeWindow' + str(step)
        parts = []
        if step > 0:
            parts.append(("subproblem", [Number(step)]))
            if step > 1:
                parts.append((string, []))
                control.add(string, [], self.compressed_start_time)
        else:
            parts.append(('base', []))
        return parts
    # ***********************************************

    # add a new constraint to get lower value of bound (Optimization Part)
    def add_new_constraint(self, control, bound):
        control.cleanup()
        control.ground([("opt", [Number(bound-1)])])
        control.assign_external(Function("bound", [Number(bound-1)]), True)
    # ********************************************************************
    def write_facts(self, start_time):
        old_start = start_time.split(' ')
        new_start = self.compressed_start_time.split(' ')
        f = open('old.lp', 'a')
        for line in old_start:
            f.writelines(line)
            f.write("\n")
        f.close()
        
        f = open('new.lp', 'a')
        for line in new_start:
            f.writelines(line)
            f.write("\n")
        f.close()
        
    def post(self, model):
        list_atom =[]
        list_of_args = []
        atoms = model.symbols(terms = True)
        for atom in atoms:
            if atom.name == 'startTime':
                list_atom.append(str(atom) + '.')
        self.compressed_start_time = ' '.join(list_atom)

    def compression(self, start_time, overlapping_facts, i):
        list_files = [sys.argv[2], 'Compress_schedule.lp']
        compress = clingo.Control()
        for f in list_files:
            compress.load(f)
        compress.add('base', [], start_time + ' ' + overlapping_facts)
        compress.ground([('base', [])])
        compress.solve(on_model=self.post)
        

    def main(self, control, files):
        self.__theory.register(control)
        with ast.ProgramBuilder(control) as bld:
            ast.parse_files(files, lambda stm: self.__theory.rewrite_ast(stm, bld.add))

        time_out_for_window = self.get_TimeOut()
        i, ret = 0, None
        start_time = ''
        overlapping_facts = ''
        self.compressed_start_time = ''
        lastbound = 0
        interrupted_calls = 0
        non_interrupted_calls = 0
        makespan_time_window = []
        overlap_atoms = []
        while i <= NUM_OF_TIME_WINDOWS:
            time_used = 0
            control.configuration.solve.models = 0
            parts = self.step_to_ground(control, i)
            control.cleanup()
            control.ground(parts)
            self.__theory.prepare(control)
            bound = 0
            while True:
                control.assign_external(Function("bound", [Number(lastbound-1)]), False)
                lastbound = bound
                tic = time.time()
                if time_used >= time_out_for_window:
                    interrupted_calls += 1
                    break
                with control.solve(on_model=self.__on_model, on_statistics=self.__on_statistics, async_=True, yield_=True) as handle:
                    wait = handle.wait(time_out_for_window - time_used)
                    if not wait:
                        interrupted_calls += 1
                        break
                    for model in handle:
                        a = self.__theory.assignment(model.thread_id)
                        start_time, bound = self.get_total_facts(a, i)
                        overlap_atoms = [atom for atom in model.symbols(atoms=True) if atom.name == 'overlappedOperation']
                        break
                    else:
                        non_interrupted_calls += 1
                        # sys.stdout.write("Optimum Found\n")
                        break
                toc = time.time()
                time_used += (toc - tic)
                self.add_new_constraint(control, bound)
            else:
                ret = control.solve()
            if i != 0:
                makespan_time_window.append(lastbound)
                overlapping_facts = ' '.join([str(atom) + '.' for atom in overlap_atoms])
                self.compression(start_time, overlapping_facts, i)
                self.compressed_start_time = self.compressed_start_time + '\n'
            i = i + 1      # Go to the next Time Window
        for x in range(NUM_OF_TIME_WINDOWS):
            print('Completion Time for Window {} : {} '.format(x+1, makespan_time_window[x]))
        print('Number of Interrupted Calls : {} '.format(interrupted_calls))
        print('Number of UnInterrupted Calls : {} '.format(non_interrupted_calls-1))

sys.exit(int(clingo.clingo_main(Application('test'), sys.argv[1:])))
