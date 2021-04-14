#!/usr/bin/env/python
# PDA-er interpreter
# Written by Jamie Large in March 2021
# Version 1.0
import sys
from queue import Queue


debug = False
PDA = dict()
starting_state = None

# A state in the PDA with:
# name - some nonnegative integer
# accepting - whether or not the state is accepting
# paths - the transitions from this state
class State:
	def __init__(self, name, accepting=False):
		self.name = name
		self.accepting = accepting
		self.paths = dict()

	def add_path(self, symbol, pop, push, destination):
		if (symbol, pop) not in self.paths:
			self.paths[(symbol, pop)] = []
		if (push, destination) not in self.paths[(symbol, pop)]:
			self.paths[(symbol, pop)].append( (push, destination) )

class Processing_Node:
	def __init__(self, state, output_str, stack, input_str):
		self.state = state
		self.output_str = output_str
		self.stack = stack
		self.input_str = input_str

def main():
	code = ""
	# Get the code, either as input from the user until they send EOF or from the specified file
	if (len(sys.argv) == 1):
		str_buf = []
		for line in sys.stdin:
			str_buf.append(line)
		code = ''.join(str_buf)
	else:
		try:
			with open(sys.argv[1], 'r') as f:
				code = f.read()
		except:
			print('Error reading file: ' + sys.argv[1])

	# Split the code between making the PDA and running the PDA
	parts = code.split('!', 1)
	if (len(parts) == 1):
		parts.append('')

	make_PDA(parts[0])
	if debug: print_PDA()
	run_PDA(parts[1])


# Construct the PDA from the string code
def make_PDA(code):
	c = 0
	current_state = None

	while (True):
		# If we've reached the end, stop
		if (c >= len(code)):
			return

		# If the current character is not . or -, just skip over it
		if (code[c] not in '.-'):
			c += 1
			continue

		# If we are creating a new state
		elif (code[c] == '.'):
			if (c == len(code) - 1):
				return
			c += 1

			# determine if accepting state
			accepting = False
			if (code[c] == '.'):
				accepting = True
				c += 1

			# gather the state's name
			name, offset = read_binary(code[c:], '.')
			if (name == -1):
				return
			c += offset

			# If the state already exists, get it, otherwise create it
			# Set the current state to be this state
			if (name in PDA):
				current_state = PDA[name]
				current_state.accepting = accepting
			else:
				current_state = State(name, accepting)
				if (len(PDA) == 0):
					global starting_state
					starting_state = current_state
				PDA[name] = current_state
			continue
		
		# If we are creating a new transition
		elif (code[c] == '-'):
			c += 1

			# If there are no states yet, create one
			if (current_state is None):
				current_state = State(0, accepting)
				PDA[0] = current_state
				starting_state = PDA[0]
			
			# gather the symbol the transition occurs on
			symbol, offset = read_binary(code[c:], '-')
			if (symbol == -1):
				return
			c += offset

			# gather the symbol to be popped from the stack
			pop, offset = read_binary(code[c:], '-')
			if (pop == -1):
				return
			c += offset

			# gather the symbol to be pushed from the stack
			push, offset = read_binary(code[c:], '-')
			if (push == -1):
				return
			c += offset

			# gather the name of the destination the transition goes to
			destination_name, offset = read_binary(code[c:], '-', 0)
			if (destination_name == -1):
				return
			c += offset
			
			# Find the actual state that is the destination, otherwise create it
			destination = None
			if (destination_name in PDA):
				destination = PDA[destination_name]
			else:
				destination = State(destination_name)
				PDA[destination_name] = destination

			current_state.add_path(symbol, pop, push, destination)
			continue

# Run the PDA in the manner specified by the string code
def run_PDA(code):
	if starting_state is None:
		return
	# Get the inputs to the DFA
	c = 0
	inputs = []
	while (True):
		# If we've reached the end, stop
		if (c >= len(code)):
			break

		# If the current character is not . or -, just skip over it
		if (code[c] not in '.-'):
			c += 1
			continue

		# If the code is manually passing input
		elif (code[c] == '.'):
			if (c == len(code) - 1):
				break
			c += 1
			# gather the input
			symbol, offset = read_binary(code[c:], '.', 0)
			if (symbol == -1):
				break
			c += offset

			inputs.append(symbol)
			continue

		# If the code is asking for user input, add it to the code to be read
		elif (code[c] == '-'):
			c += 1
			str_buf = []
			for line in sys.stdin:
				str_buf.append(line)
			ch_buf = []
			for ch in ''.join(str_buf):
				inputs.append(ord(ch))
			print()
			continue

	if (len(inputs) == 0):
		if (starting_state.accepting):
			output = chr(starting_state.name) if (starting_state.name <= 0x10FFFF and not debug) else str(starting_state.name)
			print(output)
		return

	# The first input specifies how many valid outputs to see before outputting
	n = inputs[0] if inputs[0] != 0 else 1

	# Set up the queue to process the possible paths
	processing_queue = Queue()
	processing_queue.put(Processing_Node(starting_state, [], [], inputs[1:]))

	possible_outputs = 0

	while (not processing_queue.empty()):
		# Get the current node and state
		current_node = processing_queue.get()
		current_state = current_node.state

		# Add to the output buffer
		output = chr(current_state.name) if (current_state.name <= 0x10FFFF and not debug) else str(current_state.name)
		current_node.output_str.append(output)

		if debug:
			print("New Node:")
			print("\t State: " + str(current_state.name))
			print("\t Output: " + str(current_node.output_str))
			print("\t Stack: " + str(current_node.stack))
			print("\t Inputs: " + str(current_node.input_str))


		# Figure out if this is the correct output
		if (len(current_node.input_str) == 0 and current_node.state.accepting):
			possible_outputs += 1
			if debug: print("Found correct ouput number " + str(possible_outputs))
			if (possible_outputs == n):
				print(''.join(current_node.output_str))
				return

		if debug: print

		### Get all the possible children nodes ###
		# The nodes that eat a symbol and pop from the stack
		if (len(current_node.input_str) > 0 and len(current_node.stack) > 0 and
			(current_node.input_str[0], current_node.stack[-1]) in current_state.paths):
			for path in current_state.paths[(current_node.input_str[0], current_node.stack[-1])]:
				new_stack = list(current_node.stack)
				new_stack.pop()
				if path[0] != '':
					new_stack.append(path[0])
				processing_queue.put(Processing_Node(path[1], 
													 list(current_node.output_str), 
													 new_stack,
													 current_node.input_str[1:]))

		# The nodes that eat a symbol and don't pop from the stack
		if (len(current_node.input_str) > 0 and (current_node.input_str[0], '') in current_state.paths):
			for path in current_state.paths[(current_node.input_str[0], '')]:
				new_stack = list(current_node.stack)
				if path[0] != '':
					new_stack.append(path[0])
				processing_queue.put(Processing_Node(path[1], 
													 list(current_node.output_str), 
													 new_stack,
													 current_node.input_str[1:]))


		# The nodes that don't eat a symbol and pop from the stack
		if (len(current_node.stack) > 0 and ('', current_node.stack[-1]) in current_state.paths):
			for path in current_state.paths[('', current_node.stack[-1])]:
				new_stack = list(current_node.stack)
				new_stack.pop()
				if path[0] != '':
					new_stack.append(path[0])
				processing_queue.put(Processing_Node(path[1], 
													 list(current_node.output_str), 
													 new_stack,
													 current_node.input_str))


		# The nodes that don't eat a symbol and don't pop from the stack
		if ('', '') in current_state.paths:
			for path in current_state.paths[('', '')]:
				new_stack = list(current_node.stack)
				if path[0] != '':
					new_stack.append(path[0])
				processing_queue.put(Processing_Node(path[1], 
													 list(current_node.output_str), 
													 new_stack,
													 current_node.input_str))

		

# Reads binary from code string until it encounters stop_char
# Returns -1 if it never encounters stop_char, otherwise converts binary to an int
# Returns default if it doesn't encounter any binary before stop_char
def read_binary(code, stop_char, default=''):
	c = 0
	binary_string = []
	while (True):
		if (c == len(code)):
			return -1

		if (code[c] == '0' or code[c] == '1'):
			binary_string.append(code[c])

		if (code[c] == stop_char):
			c += 1
			break
		c += 1

	result = int(''.join(binary_string), 2) if (len(binary_string) > 0) else default

	return result, c

# Prints the structure of the PDA (useful for debugging)
def print_PDA():
	for state in PDA:
		if (PDA[state] == starting_state):
			print("STARTING STATE")
		print ("state name: " + str(PDA[state].name))
		print ("accepting: " + str(PDA[state].accepting))
		print ("state paths: " )
		for path in PDA[state].paths:
			for multiple_path in PDA[state].paths[path]:
				print ("\t" + str(path) + ": (" + str(multiple_path[0]) + ", " + str(multiple_path[1].name) + ")")
		print()



main()